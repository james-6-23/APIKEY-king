"""
Scan report service.
"""

from datetime import datetime
from typing import Dict, List, Optional
from ..database.database import db


class ReportService:
    """Scan report management service - Singleton."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
    
    def create_report(self, stats: Dict, scan_mode: str) -> Dict:
        """Create a scan report."""
        report = {
            "scan_mode": scan_mode,
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_files": stats.get("total_files", 0),
            "total_keys": stats.get("total_keys", 0),
            "valid_keys": stats.get("valid_keys", 0),
            "queries_processed": stats.get("total_queries", 0),
            "duration_seconds": 0  # 将在扫描结束时更新
        }
        
        # 保存到数据库
        report_id = db.save_scan_report(report)
        report["id"] = report_id
        
        return report
    
    def update_report(self, report_id: int, stats: Dict, end_time: str = None):
        """Update a scan report when scan completes."""
        update_data = {
            "end_time": end_time or datetime.now().isoformat(),
            "total_files": stats.get("total_files", 0),
            "total_keys": stats.get("total_keys", 0),
            "valid_keys": stats.get("valid_keys", 0)
        }
        
        db.update_scan_report(report_id, update_data)
    
    def get_all_reports(self, limit: int = 20) -> List[Dict]:
        """Get all scan reports."""
        return db.get_scan_reports(limit)
    
    def get_report(self, report_id: int) -> Optional[Dict]:
        """Get a specific report."""
        return db.get_scan_report(report_id)
    
    def delete_report(self, report_id: int):
        """Delete a scan report."""
        db.delete_scan_report(report_id)
    
    def clear_all_reports(self):
        """Clear all scan reports."""
        db.clear_scan_reports()

