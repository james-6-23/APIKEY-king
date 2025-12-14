"""
Database module for APIKEY-king.
使用 SQLite 实现轻量级数据持久化
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class Database:
    """SQLite database handler."""
    
    def __init__(self, db_path: str = "data/apikey.db"):
        """Initialize database connection."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 系统设置表（包括密码等）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 密钥表
        cursor.execute("""
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
        
        # 扫描日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 扫描统计表
        cursor.execute("""
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
        
        # 已处理查询表（记忆功能）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT UNIQUE NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 已扫描文件SHA表（去重功能）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scanned_shas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sha TEXT UNIQUE NOT NULL,
                file_path TEXT,
                repository TEXT,
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 迁移：为旧数据库添加 balance 列
        self._migrate_add_balance_column(cursor)

        conn.commit()
        conn.close()

    def _migrate_add_balance_column(self, cursor):
        """迁移：为 api_keys 表添加 balance 列（如果不存在）."""
        try:
            cursor.execute("PRAGMA table_info(api_keys)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'balance' not in columns:
                cursor.execute("ALTER TABLE api_keys ADD COLUMN balance TEXT")
        except Exception:
            pass  # 忽略迁移错误
    
    # ===== 系统设置相关 =====
    
    def save_system_setting(self, key: str, value: Any):
        """保存系统设置."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        value_json = json.dumps(value) if not isinstance(value, str) else value
        
        cursor.execute("""
            INSERT INTO system_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET 
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (key, value_json, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_system_setting(self, key: str) -> Optional[Any]:
        """获取系统设置."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row['value'])
            except:
                return row['value']
        return None
    
    def is_first_run(self) -> bool:
        """检查是否首次运行."""
        return self.get_system_setting("password_hash") is None
    
    # ===== 配置相关 =====
    
    def save_config(self, key: str, value: Any):
        """保存配置."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        value_json = json.dumps(value) if not isinstance(value, str) else value
        
        cursor.execute("""
            INSERT INTO config (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET 
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (key, value_json, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_config(self, key: str) -> Optional[Any]:
        """获取配置."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row['value'])
            except:
                return row['value']
        return None
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM config")
        rows = cursor.fetchall()
        conn.close()
        
        configs = {}
        for row in rows:
            try:
                configs[row['key']] = json.loads(row['value'])
            except:
                configs[row['key']] = row['value']
        
        return configs
    
    # ===== 密钥相关 =====

    def save_key(self, key_value: str, key_type: str, source_repo: str = None,
                 source_file: str = None, source_url: str = None,
                 is_valid: bool = True, validation_status: str = None,
                 validation_message: str = None, balance: str = None):
        """保存密钥."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()

        cursor.execute("""
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

        conn.commit()
        conn.close()
    
    def get_all_keys(self, key_type: str = None, is_valid: bool = None) -> List[Dict]:
        """获取所有密钥."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM api_keys WHERE 1=1"
        params = []
        
        if key_type:
            query += " AND key_type = ?"
            params.append(key_type)
        
        if is_valid is not None:
            query += " AND is_valid = ?"
            params.append(is_valid)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_keys_by_time_range(self, start_time: str, end_time: str, is_valid: bool = True) -> List[Dict]:
        """根据时间范围获取密钥."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 使用 datetime 函数确保时间格式正确比较
        query = """
            SELECT * FROM api_keys
            WHERE datetime(created_at) >= datetime(?) 
              AND datetime(created_at) <= datetime(?) 
              AND is_valid = ?
            ORDER BY created_at DESC
        """

        cursor.execute(query, (start_time, end_time, is_valid))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_key_count(self, key_type: str = None, is_valid: bool = None) -> int:
        """获取密钥数量."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) as count FROM api_keys WHERE 1=1"
        params = []
        
        if key_type:
            query += " AND key_type = ?"
            params.append(key_type)
        
        if is_valid is not None:
            query += " AND is_valid = ?"
            params.append(is_valid)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] if result else 0
    
    def clear_keys(self):
        """清空所有密钥."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM api_keys")
        conn.commit()
        conn.close()
    
    # ===== 日志相关 =====
    
    def save_log(self, log_type: str, message: str, data: Dict = None):
        """保存日志."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        data_json = json.dumps(data) if data else None
        
        cursor.execute("""
            INSERT INTO scan_logs (log_type, message, data, created_at)
            VALUES (?, ?, ?, ?)
        """, (log_type, message, data_json, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """获取最近的日志."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM scan_logs 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            log = dict(row)
            if log.get('data'):
                try:
                    log['data'] = json.loads(log['data'])
                except:
                    pass
            logs.append(log)
        
        return logs
    
    def clear_old_logs(self, days: int = 7):
        """清理旧日志."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM scan_logs 
            WHERE created_at < datetime('now', '-' || ? || ' days')
        """, (days,))
        
        conn.commit()
        conn.close()
    
    # ===== 统计相关 =====
    
    def save_scan_stats(self, total_files: int, total_keys: int, valid_keys: int,
                       scan_mode: str, status: str = "running"):
        """保存扫描统计."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO scan_stats 
            (total_files, total_keys, valid_keys, scan_mode, started_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (total_files, total_keys, valid_keys, scan_mode, datetime.now(), status))
        
        conn.commit()
        conn.close()
    
    def get_scan_stats(self) -> Dict:
        """获取扫描统计."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取最新的统计
        cursor.execute("""
            SELECT * FROM scan_stats 
            ORDER BY started_at DESC 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else {
            "total_files": 0,
            "total_keys": 0,
            "valid_keys": 0
        }
    
    # ===== 扫描记忆相关 =====
    
    def add_processed_query(self, query_text: str):
        """添加已处理的查询."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO processed_queries (query_text, processed_at)
            VALUES (?, ?)
        """, (query_text, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def is_query_processed(self, query_text: str) -> bool:
        """检查查询是否已处理."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM processed_queries 
            WHERE query_text = ?
        """, (query_text,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] > 0 if result else False
    
    def add_scanned_sha(self, sha: str, file_path: str = None, repository: str = None):
        """添加已扫描的文件SHA."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO scanned_shas (sha, file_path, repository, scanned_at)
            VALUES (?, ?, ?, ?)
        """, (sha, file_path, repository, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def is_sha_scanned(self, sha: str) -> bool:
        """检查SHA是否已扫描."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM scanned_shas 
            WHERE sha = ?
        """, (sha,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] > 0 if result else False
    
    def get_scan_memory_stats(self) -> Dict:
        """获取扫描记忆统计."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM processed_queries")
        queries_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM scanned_shas")
        shas_count = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            "processed_queries": queries_count,
            "scanned_files": shas_count
        }
    
    def clear_scan_memory(self):
        """清除所有扫描记忆."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM processed_queries")
        cursor.execute("DELETE FROM scanned_shas")
        
        conn.commit()
        conn.close()
    
    def save_scan_report(self, report: Dict) -> int:
        """保存扫描报告."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 使用报告中的 status，默认为 completed（因为报告是在扫描完成后创建的）
        status = report.get("status", "completed")

        cursor.execute("""
            INSERT INTO scan_stats (scan_mode, total_files, total_keys, valid_keys, started_at, ended_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            report.get("scan_mode"),
            report.get("total_files", 0),
            report.get("total_keys", 0),
            report.get("valid_keys", 0),
            report.get("start_time"),
            report.get("end_time"),
            status
        ))

        report_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return report_id
    
    def update_scan_report(self, report_id: int, data: Dict):
        """更新扫描报告."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE scan_stats 
            SET total_files = ?, total_keys = ?, valid_keys = ?, ended_at = ?, status = 'completed'
            WHERE id = ?
        """, (
            data.get("total_files", 0),
            data.get("total_keys", 0),
            data.get("valid_keys", 0),
            data.get("end_time"),
            report_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_scan_reports(self, limit: int = 20) -> List[Dict]:
        """获取扫描报告列表."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM scan_stats 
            ORDER BY started_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_scan_report(self, report_id: int) -> Optional[Dict]:
        """获取单个扫描报告."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM scan_stats WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def delete_scan_report(self, report_id: int):
        """删除扫描报告."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM scan_stats WHERE id = ?", (report_id,))
        conn.commit()
        conn.close()
    
    def clear_scan_reports(self):
        """清除所有扫描报告."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM scan_stats")
        conn.commit()
        conn.close()


# 全局数据库实例
db = Database()

