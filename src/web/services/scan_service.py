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
        self._scanner_thread = None
        self._stop_flag = False
        self._stats = {
            "total_files": 0,
            "total_keys": 0,
            "valid_keys": 0,
            "last_update": None
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
        
        from ..core.scanner_runner import ScannerRunner
        runner = ScannerRunner(config, self._stats, log_svc)
        self._scanner_thread = Thread(target=runner.run, args=(lambda: self._stop_flag,), daemon=True)
        self._scanner_thread.start()
        
        log_svc.add_log("success", "Scanner started", {"mode": config.get("scan_mode")})
        
        return {"status": "ok", "message": "Scanner started"}
    
    def stop_scan(self) -> Dict:
        """Stop scanning."""
        if not self._running:
            raise Exception("Scanner is not running")
        
        self._stop_flag = True
        log_svc = get_log_service()
        log_svc.add_log("warning", "Stop signal sent, waiting for scanner to finish current task...")
        
        return {"status": "ok", "message": "Stop signal sent"}
    
    def get_status(self) -> Dict:
        """Get scanner status."""
        return {
            "running": self._running,
            "stats": self._stats
        }
    
    def set_running(self, running: bool):
        """Set running status (called by runner)."""
        self._running = running

