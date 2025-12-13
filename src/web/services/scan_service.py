"""
Scan service.
"""

import os
from datetime import datetime
from threading import Thread
from typing import Dict

log_service = None
config_service = None


def get_log_service():
    """Get log service instance."""
    global log_service
    if log_service is None:
        from .log_service import LogService
        log_service = LogService()
    return log_service


def get_config_service():
    """Get config service instance."""
    global config_service
    if config_service is None:
        from .config_service import ConfigService
        config_service = ConfigService()
    return config_service


class ScanService:
    """Scan management service."""
    
    def __init__(self):
        self._running = False
        self._paused = False
        self._scanner_thread = None
        self._stop_flag = False
        self._current_scan_mode = None  # 当前扫描使用的模式
        self._scan_start_time = None  # 扫描开始时间
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
            "remaining_queries": 0
        }
    
    def start_scan(self) -> Dict:
        """Start scanning."""
        if self._running:
            raise Exception("Scanner is already running")
        
        cfg_service = get_config_service()
        log_svc = get_log_service()
        
        config = cfg_service.get_config()
        if not config:
            raise Exception("Please configure GitHub tokens first")
        
        # Start scanner in background thread
        self._stop_flag = False
        self._running = True
        self._current_scan_mode = config.get("scan_mode", "compatible")  # 记录当前扫描模式
        self._scan_start_time = datetime.now()
        
        # 重置统计
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
            "remaining_queries": 0
        }
        
        from ..core.scanner_runner import ScannerRunner
        runner = ScannerRunner(config, self._stats, log_svc, self)
        self._scanner_thread = Thread(target=runner.run, args=(lambda: self._stop_flag,), daemon=True)
        self._scanner_thread.start()
        
        # 清除配置缓存，确保下次启动使用最新配置
        cfg_service.clear_cache()
        
        log_svc.add_log("success", f"Scanner started with mode: {self._current_scan_mode}")
        
        return {"status": "ok", "message": "Scanner started"}
    
    def stop_scan(self) -> Dict:
        """Stop scanning."""
        if not self._running:
            raise Exception("Scanner is not running")

        self._stop_flag = True
        self._running = False  # 立即标记为未运行状态
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
        log_svc = get_log_service()
        log_svc.add_log("warning", "Scanner paused")
        
        return {"status": "ok", "message": "Scanner paused"}
    
    def resume_scan(self) -> Dict:
        """Resume scanning."""
        if not self._running:
            raise Exception("Scanner is not running")
        
        if not self._paused:
            raise Exception("Scanner is not paused")
        
        self._paused = False
        log_svc = get_log_service()
        log_svc.add_log("success", "Scanner resumed")
        
        return {"status": "ok", "message": "Scanner resumed"}
    
    def get_status(self) -> Dict:
        """Get scanner status."""
        return {
            "running": self._running,
            "paused": self._paused,
            "scan_mode": self._current_scan_mode,  # 添加当前扫描模式
            "stats": self._stats
        }
    
    def set_running(self, running: bool):
        """Set running status (called by runner)."""
        self._running = running
        if not running:
            self._handle_scan_finished(False)

    def finish_scan(self, completed: bool):
        """Finalize scan state when runner exits."""
        self._handle_scan_finished(completed)

    def _handle_scan_finished(self, completed: bool):
        """Handle cleanup and optional report creation when scan stops."""
        # 只要是正常完成的扫描且有扫描模式，就生成报告
        if completed and self._current_scan_mode:
            # 只要处理过查询或扫描过文件，就生成报告
            has_activity = (
                self._stats.get("total_files", 0) > 0 or
                self._stats.get("queries_completed", 0) > 0 or
                self._stats.get("valid_keys", 0) > 0
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
                        end_time
                    )
                    log_svc = get_log_service()
                    log_svc.add_log("success", f"Scan report created: #{report.get('id')}", {
                        "total_files": self._stats.get("total_files", 0),
                        "valid_keys": self._stats.get("valid_keys", 0),
                        "duration": f"{int((end_time - start_time).total_seconds())}s"
                    })
                except Exception as e:
                    log_svc = get_log_service()
                    log_svc.add_log("error", f"Failed to create report: {str(e)}")

        if not completed:
            # 如果扫描被终止，保留已统计信息供下一次恢复
            pass

        # 重置运行状态，确保前端展示停止
        self._running = False
        self._paused = False
        self._stop_flag = False

        # 将进度标记为完成
        if completed and self._stats.get("total_queries"):
            self._stats["progress_percent"] = 100
            self._stats["current_query"] = ""

        # 重置运行状态
        self._current_scan_mode = None
        self._scan_start_time = None
    
    def is_paused(self) -> bool:
        """Check if scanner is paused."""
        return self._paused
    
    def update_progress(self, current_query_index: int, total_queries: int, current_query: str):
        """Update scan progress."""
        self._stats["current_query_index"] = current_query_index
        self._stats["total_queries"] = total_queries
        self._stats["current_query"] = current_query
        self._stats["progress_percent"] = int((current_query_index / total_queries) * 100) if total_queries > 0 else 0
