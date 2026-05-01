"""
Scan service.
"""

import threading
from datetime import datetime
from threading import Thread, Event, Lock
from typing import Dict

log_service = None
config_service = None
_service_lock = Lock()


def get_log_service():
    """Get log service instance (thread-safe lazy init)."""
    global log_service
    if log_service is None:
        with _service_lock:
            if log_service is None:
                from .log_service import LogService
                log_service = LogService()
    return log_service


def get_config_service():
    """Get config service instance (thread-safe lazy init)."""
    global config_service
    if config_service is None:
        with _service_lock:
            if config_service is None:
                from .config_service import ConfigService
                config_service = ConfigService()
    return config_service


class ScanService:
    """Scan management service.

    Lifecycle:
      - _stop_event is SET when the user asks to stop; runners poll
        ``is_set()`` and use ``wait(timeout)`` for interruptible sleeps.
      - _paused is a plain bool; the runner polls it in short intervals.
    """

    def __init__(self):
        self._running = False
        self._paused = False
        self._scanner_thread = None
        self._stop_event: Event = Event()
        self._current_scan_mode = None
        self._scan_start_time = None
        self._stats = {
            "total_files": 0,
            "total_keys": 0,
            "valid_keys": 0,
            "last_update": None,
            "current_query": "",
            "current_query_index": 0,
            "total_queries": 0,
            "progress_percent": 0,
            "queries_completed": 0,
            "initial_unprocessed_queries": 0,
            "remaining_queries": 0,
        }

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------

    def start_scan(self) -> Dict:
        """Start scanning."""
        if self._running:
            raise Exception("Scanner is already running")

        cfg_service = get_config_service()
        log_svc = get_log_service()

        config = cfg_service.get_config()
        if not config:
            raise Exception("Please configure GitHub tokens first")

        # Reset event on each run
        self._stop_event = Event()
        self._running = True
        self._paused = False
        self._current_scan_mode = config.get("scan_mode", "compatible")
        self._scan_start_time = datetime.now()

        self._stats = {
            "total_files": 0,
            "total_keys": 0,
            "valid_keys": 0,
            "last_update": None,
            "current_query": "",
            "current_query_index": 0,
            "total_queries": 0,
            "progress_percent": 0,
            "queries_completed": 0,
            "initial_unprocessed_queries": 0,
            "remaining_queries": 0,
        }

        from ..core.scanner_runner import ScannerRunner
        runner = ScannerRunner(config, self._stats, log_svc, self)
        # Preserve legacy callable signature — runners can also grab the Event
        # directly via ``scan_service._stop_event`` for ``wait(timeout)`` loops.
        self._scanner_thread = Thread(
            target=runner.run,
            args=(self._stop_event.is_set,),
            daemon=True,
        )
        self._scanner_thread.start()

        cfg_service.clear_cache()

        log_svc.add_log("success", f"Scanner started with mode: {self._current_scan_mode}")

        return {"status": "ok", "message": "Scanner started"}

    def stop_scan(self) -> Dict:
        """Signal the running scanner to stop."""
        if not self._running:
            raise Exception("Scanner is not running")

        self._stop_event.set()
        self._running = False  # surface the stop state to the UI immediately
        log_svc = get_log_service()
        log_svc.add_log("warning", "Stop signal sent, waiting for scanner to finish current task...")

        return {"status": "ok", "message": "Stop signal sent"}

    def pause_scan(self) -> Dict:
        """Pause scanning."""
        if not self._running:
            raise Exception("Scanner is not running")
        if self._paused:
            raise Exception("Scanner is already paused")

        self._paused = True
        get_log_service().add_log("warning", "Scanner paused")
        return {"status": "ok", "message": "Scanner paused"}

    def resume_scan(self) -> Dict:
        """Resume scanning."""
        if not self._running:
            raise Exception("Scanner is not running")
        if not self._paused:
            raise Exception("Scanner is not paused")

        self._paused = False
        get_log_service().add_log("success", "Scanner resumed")
        return {"status": "ok", "message": "Scanner resumed"}

    def restart_scan(self, wipe_memory: bool = True) -> Dict:
        """Stop (if running), optionally wipe scan memory, then start fresh.

        The "wipe memory" step clears processed-query and scanned-SHA state
        from the database so the new run rescans everything, which is what
        users expect when they hit "重新开始".
        """
        log_svc = get_log_service()

        # 1. Stop current scan if alive and wait for the runner thread to exit.
        if self._running:
            self._stop_event.set()
            self._running = False
            log_svc.add_log("warning", "Restart requested: waiting for scanner to stop...")
            thread = self._scanner_thread
            if thread is not None and thread.is_alive():
                thread.join(timeout=15.0)
                if thread.is_alive():
                    raise Exception("Scanner did not stop within timeout")

        # 2. Wipe memory so the next run re-processes everything.
        if wipe_memory:
            from ..database.database import db
            db.clear_scan_memory()
            log_svc.add_log("warning", "Scan memory cleared (processed queries & scanned SHAs)")

        # 3. Start a new scan using the current config.
        result = self.start_scan()
        return {"status": "ok", "message": "Scanner restarted", **result}

    def get_status(self) -> Dict:
        """Get scanner status."""
        return {
            "running": self._running,
            "paused": self._paused,
            "scan_mode": self._current_scan_mode,
            "stats": self._stats,
        }

    # ------------------------------------------------------------------
    # Runner callbacks
    # ------------------------------------------------------------------

    def set_running(self, running: bool):
        """Set running status (called by runner)."""
        self._running = running
        if not running:
            self._handle_scan_finished(False)

    def finish_scan(self, completed: bool):
        """Finalize scan state when runner exits."""
        self._handle_scan_finished(completed)

    def _handle_scan_finished(self, completed: bool):
        """Cleanup + optional report creation when scan stops."""
        if completed and self._current_scan_mode:
            has_activity = (
                self._stats.get("total_files", 0) > 0
                or self._stats.get("queries_completed", 0) > 0
                or self._stats.get("valid_keys", 0) > 0
            )

            if has_activity:
                try:
                    from ..services.report_service import ReportService

                    report_svc = ReportService()
                    start_time = self._scan_start_time or datetime.now()
                    end_time = datetime.now()
                    report = report_svc.create_report(
                        self._stats,
                        self._current_scan_mode,
                        start_time,
                        end_time,
                    )
                    log_svc = get_log_service()
                    log_svc.add_log("success", f"Scan report created: #{report.get('id')}", {
                        "total_files": self._stats.get("total_files", 0),
                        "valid_keys": self._stats.get("valid_keys", 0),
                        "duration": f"{int((end_time - start_time).total_seconds())}s",
                    })
                except Exception as e:
                    get_log_service().add_log("error", f"Failed to create report: {str(e)}")

        # Reset runtime state
        self._running = False
        self._paused = False
        self._stop_event.set()  # idempotent; ensures waiters exit

        if completed and self._stats.get("total_queries"):
            self._stats["progress_percent"] = 100
            self._stats["current_query"] = ""

        self._current_scan_mode = None
        self._scan_start_time = None

    # ------------------------------------------------------------------
    # Helpers exposed to the runner
    # ------------------------------------------------------------------

    def is_paused(self) -> bool:
        """Check if scanner is paused."""
        return self._paused

    def wait_or_stop(self, timeout: float) -> bool:
        """Sleep up to ``timeout`` seconds; return True if stop was requested
        during the wait. Callers should ``break`` on True.
        """
        return self._stop_event.wait(timeout)

    def update_progress(self, current_query_index: int, total_queries: int, current_query: str):
        """Update scan progress."""
        self._stats["current_query_index"] = current_query_index
        self._stats["total_queries"] = total_queries
        self._stats["current_query"] = current_query
        self._stats["progress_percent"] = int((current_query_index / total_queries) * 100) if total_queries > 0 else 0
