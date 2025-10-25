"""
Scan service.
"""

import os
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
        self._current_report_id = None  # 当前扫描报告ID
        self._scan_start_time = None  # 扫描开始时间
        self._stats = {
            "total_files": 0,
            "total_keys": 0,
            "valid_keys": 0,
            "last_update": None,
            "current_query": "",
            "current_query_index": 0,
            "total_queries": 0,
            "progress_percent": 0
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
        self._scan_start_time = datetime.now().isoformat()
        
        # 重置统计
        self._stats = {
            "total_files": 0,
            "total_keys": 0,
            "valid_keys": 0,
            "last_update": None,
            "current_query": "",
            "current_query_index": 0,
            "total_queries": 0,
            "progress_percent": 0
        }
        
        # 创建扫描报告
        from ..services.report_service import ReportService
        report_svc = ReportService()
        self._current_report_id = report_svc.create_report(self._stats, self._current_scan_mode)
        
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
            # 更新扫描报告
            if self._current_report_id:
                from ..services.report_service import ReportService
                from datetime import datetime
                report_svc = ReportService()
                report_svc.update_report(
                    self._current_report_id,
                    self._stats,
                    end_time=datetime.now().isoformat()
                )
                self._current_report_id = None
            
            self._current_scan_mode = None  # 清除扫描模式
    
    def is_paused(self) -> bool:
        """Check if scanner is paused."""
        return self._paused
    
    def update_progress(self, current_query_index: int, total_queries: int, current_query: str):
        """Update scan progress."""
        self._stats["current_query_index"] = current_query_index
        self._stats["total_queries"] = total_queries
        self._stats["current_query"] = current_query
        self._stats["progress_percent"] = int((current_query_index / total_queries) * 100) if total_queries > 0 else 0

