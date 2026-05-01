"""
Database module for APIKEY-king.
使用 SQLite 实现轻量级数据持久化。

Runtime-tuning notes:
- WAL mode so readers don't block the scanner's writers.
- busy_timeout avoids spurious "database is locked" errors under concurrency.
- Timestamps are stored as ISO-8601 strings everywhere so range queries hit indexes.
"""

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Set, Iterator
import json


def _now_iso() -> str:
    return datetime.now().isoformat()


def _to_iso(value: Any) -> Optional[str]:
    """Coerce datetime / str into ISO-8601 string for consistent sorting."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class Database:
    """SQLite database handler.

    The singleton instance (`db`) is shared across threads. Every method opens
    a fresh connection (sqlite3 connections aren't safe to share across threads
    by default); WAL + busy_timeout keep contention bounded.
    """

    def __init__(self, db_path: str = "data/apikey.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_lock = threading.Lock()
        self.init_database()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def get_connection(self):
        """Return a tuned connection. Kept as a public method for callers
        that construct their own contexts."""
        conn = sqlite3.connect(self.db_path, timeout=10.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        # PRAGMAs are per-connection; re-apply on every open.
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA temp_store=MEMORY")
        return conn

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        """Context manager replacing the `conn = ...; ... conn.close()` boilerplate.

        isolation_level=None puts sqlite3 in autocommit mode; we wrap multi-step
        writes with an explicit BEGIN via `_tx()` when we need atomicity.
        """
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        """Transactional variant: BEGIN IMMEDIATE + COMMIT/ROLLBACK."""
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def init_database(self):
        """Initialize database tables and indexes."""
        with self._init_lock, self._conn() as conn:
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_value TEXT NOT NULL,
                    key_type TEXT NOT NULL,
                    source_repo TEXT,
                    source_file TEXT,
                    source_url TEXT,
                    is_valid BOOLEAN DEFAULT 1,
                    validation_status TEXT,
                    validation_message TEXT,
                    balance TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(key_value, key_type)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS scan_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS scan_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_files INTEGER DEFAULT 0,
                    total_keys INTEGER DEFAULT 0,
                    valid_keys INTEGER DEFAULT 0,
                    scan_mode TEXT,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    status TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS processed_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT UNIQUE NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS scanned_shas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sha TEXT UNIQUE NOT NULL,
                    file_path TEXT,
                    repository TEXT,
                    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migration: add balance column on legacy DBs
            self._migrate_add_balance_column(cur)

            # Indexes — after tables so new installs and existing ones both get them.
            # IF NOT EXISTS keeps init_database idempotent.
            cur.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_type_created   ON api_keys (key_type, created_at DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_valid_created  ON api_keys (is_valid, created_at DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_created        ON api_keys (created_at DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_scan_logs_created       ON scan_logs (created_at DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_scan_stats_started      ON scan_stats (started_at DESC)")

    def _migrate_add_balance_column(self, cursor):
        """Add api_keys.balance on legacy DBs (idempotent)."""
        cursor.execute("PRAGMA table_info(api_keys)")
        columns = {col[1] for col in cursor.fetchall()}
        if 'balance' not in columns:
            try:
                cursor.execute("ALTER TABLE api_keys ADD COLUMN balance TEXT")
            except sqlite3.OperationalError:
                # Column may have been added by a concurrent init — safe to ignore.
                pass

    # ------------------------------------------------------------------
    # System settings
    # ------------------------------------------------------------------

    def save_system_setting(self, key: str, value: Any):
        value_json = json.dumps(value) if not isinstance(value, str) else value
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO system_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """, (key, value_json, _now_iso()))

    def get_system_setting(self, key: str) -> Optional[Any]:
        with self._conn() as conn:
            row = conn.execute("SELECT value FROM system_settings WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        try:
            return json.loads(row['value'])
        except (json.JSONDecodeError, TypeError):
            return row['value']

    def is_first_run(self) -> bool:
        return self.get_system_setting("password_hash") is None

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def save_config(self, key: str, value: Any):
        value_json = json.dumps(value) if not isinstance(value, str) else value
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """, (key, value_json, _now_iso()))

    def get_config(self, key: str) -> Optional[Any]:
        with self._conn() as conn:
            row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        try:
            return json.loads(row['value'])
        except (json.JSONDecodeError, TypeError):
            return row['value']

    def get_all_configs(self) -> Dict[str, Any]:
        with self._conn() as conn:
            rows = conn.execute("SELECT key, value FROM config").fetchall()
        configs: Dict[str, Any] = {}
        for row in rows:
            try:
                configs[row['key']] = json.loads(row['value'])
            except (json.JSONDecodeError, TypeError):
                configs[row['key']] = row['value']
        return configs

    # ------------------------------------------------------------------
    # API keys
    # ------------------------------------------------------------------

    def save_key(self, key_value: str, key_type: str, source_repo: str = None,
                 source_file: str = None, source_url: str = None,
                 is_valid: bool = True, validation_status: str = None,
                 validation_message: str = None, balance: str = None):
        now = _now_iso()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO api_keys
                (key_value, key_type, source_repo, source_file, source_url,
                 is_valid, validation_status, validation_message, balance, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key_value, key_type) DO UPDATE SET
                    is_valid = excluded.is_valid,
                    validation_status = excluded.validation_status,
                    validation_message = excluded.validation_message,
                    balance = excluded.balance,
                    updated_at = excluded.updated_at
            """, (key_value, key_type, source_repo, source_file, source_url,
                  is_valid, validation_status, validation_message, balance,
                  now, now))

    def get_all_keys(self, key_type: str = None, is_valid: bool = None) -> List[Dict]:
        query = "SELECT * FROM api_keys WHERE 1=1"
        params: list = []

        if key_type:
            query += " AND key_type = ?"
            params.append(key_type)

        if is_valid is not None:
            query += " AND is_valid = ?"
            params.append(is_valid)

        query += " ORDER BY created_at DESC"

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_keys_by_time_range(self, start_time: str, end_time: str, is_valid: bool = True) -> List[Dict]:
        """Range-scan keys by time window.

        We compare ISO strings directly so the query uses
        idx_api_keys_valid_created instead of wrapping the column in datetime()
        (which defeats the index).
        """
        start_iso = _to_iso(start_time)
        end_iso = _to_iso(end_time)
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT * FROM api_keys
                WHERE is_valid = ?
                  AND created_at >= ?
                  AND created_at <= ?
                ORDER BY created_at DESC
            """, (is_valid, start_iso, end_iso)).fetchall()
        return [dict(row) for row in rows]

    def get_key_count(self, key_type: str = None, is_valid: bool = None) -> int:
        query = "SELECT COUNT(*) AS count FROM api_keys WHERE 1=1"
        params: list = []

        if key_type:
            query += " AND key_type = ?"
            params.append(key_type)

        if is_valid is not None:
            query += " AND is_valid = ?"
            params.append(is_valid)

        with self._conn() as conn:
            result = conn.execute(query, params).fetchone()
        return result['count'] if result else 0

    def clear_keys(self):
        with self._conn() as conn:
            conn.execute("DELETE FROM api_keys")

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    def save_log(self, log_type: str, message: str, data: Dict = None):
        data_json = json.dumps(data) if data else None
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO scan_logs (log_type, message, data, created_at)
                VALUES (?, ?, ?, ?)
            """, (log_type, message, data_json, _now_iso()))

    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT * FROM scan_logs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()

        logs: List[Dict] = []
        for row in rows:
            log = dict(row)
            if log.get('data'):
                try:
                    log['data'] = json.loads(log['data'])
                except (json.JSONDecodeError, TypeError):
                    pass
            logs.append(log)
        return logs

    def clear_old_logs(self, days: int = 7):
        with self._conn() as conn:
            conn.execute("""
                DELETE FROM scan_logs
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """, (days,))

    # ------------------------------------------------------------------
    # Scan stats
    # ------------------------------------------------------------------

    def save_scan_stats(self, total_files: int, total_keys: int, valid_keys: int,
                        scan_mode: str, status: str = "running"):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO scan_stats
                (total_files, total_keys, valid_keys, scan_mode, started_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (total_files, total_keys, valid_keys, scan_mode, _now_iso(), status))

    def get_scan_stats(self) -> Dict:
        with self._conn() as conn:
            row = conn.execute("""
                SELECT * FROM scan_stats
                ORDER BY started_at DESC
                LIMIT 1
            """).fetchone()
        return dict(row) if row else {
            "total_files": 0,
            "total_keys": 0,
            "valid_keys": 0,
        }

    # ------------------------------------------------------------------
    # Scan memory (processed queries + scanned SHAs)
    # ------------------------------------------------------------------

    def add_processed_query(self, query_text: str):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO processed_queries (query_text, processed_at)
                VALUES (?, ?)
            """, (query_text, _now_iso()))

    def is_query_processed(self, query_text: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM processed_queries WHERE query_text = ? LIMIT 1",
                (query_text,),
            ).fetchone()
        return row is not None

    def get_processed_queries_set(self) -> Set[str]:
        """Load the full processed-queries set for in-memory filtering.

        Scanning loops previously did N round-trips checking one query at a
        time; callers should pull the set once and keep it local.
        """
        with self._conn() as conn:
            rows = conn.execute("SELECT query_text FROM processed_queries").fetchall()
        return {row['query_text'] for row in rows}

    def add_scanned_sha(self, sha: str, file_path: str = None, repository: str = None):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO scanned_shas (sha, file_path, repository, scanned_at)
                VALUES (?, ?, ?, ?)
            """, (sha, file_path, repository, _now_iso()))

    def is_sha_scanned(self, sha: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM scanned_shas WHERE sha = ? LIMIT 1",
                (sha,),
            ).fetchone()
        return row is not None

    def get_scanned_shas_set(self) -> Set[str]:
        with self._conn() as conn:
            rows = conn.execute("SELECT sha FROM scanned_shas").fetchall()
        return {row['sha'] for row in rows}

    def get_scan_memory_stats(self) -> Dict:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS count FROM processed_queries")
            queries_count = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) AS count FROM scanned_shas")
            shas_count = cur.fetchone()['count']
        return {
            "processed_queries": queries_count,
            "scanned_files": shas_count,
        }

    def clear_scan_memory(self):
        with self._tx() as conn:
            conn.execute("DELETE FROM processed_queries")
            conn.execute("DELETE FROM scanned_shas")

    # ------------------------------------------------------------------
    # Scan reports
    # ------------------------------------------------------------------

    def save_scan_report(self, report: Dict) -> int:
        status = report.get("status", "completed")
        with self._conn() as conn:
            cur = conn.execute("""
                INSERT INTO scan_stats (scan_mode, total_files, total_keys, valid_keys, started_at, ended_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report.get("scan_mode"),
                report.get("total_files", 0),
                report.get("total_keys", 0),
                report.get("valid_keys", 0),
                _to_iso(report.get("start_time")),
                _to_iso(report.get("end_time")),
                status,
            ))
            return cur.lastrowid

    def update_scan_report(self, report_id: int, data: Dict):
        with self._conn() as conn:
            conn.execute("""
                UPDATE scan_stats
                SET total_files = ?, total_keys = ?, valid_keys = ?, ended_at = ?, status = 'completed'
                WHERE id = ?
            """, (
                data.get("total_files", 0),
                data.get("total_keys", 0),
                data.get("valid_keys", 0),
                _to_iso(data.get("end_time")),
                report_id,
            ))

    def get_scan_reports(self, limit: int = 20) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT * FROM scan_stats
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
        return [dict(row) for row in rows]

    def get_scan_report(self, report_id: int) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM scan_stats WHERE id = ?", (report_id,)).fetchone()
        return dict(row) if row else None

    def delete_scan_report(self, report_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM scan_stats WHERE id = ?", (report_id,))

    def clear_scan_reports(self):
        with self._conn() as conn:
            conn.execute("DELETE FROM scan_stats")


# Global singleton — imported by services and routers.
db = Database()
