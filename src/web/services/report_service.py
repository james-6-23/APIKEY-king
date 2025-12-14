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
    
    def create_report(self, stats: Dict, scan_mode: str,
                       start_time: datetime = None, end_time: datetime = None) -> Dict:
        """Create a scan report."""
        now = datetime.now()
        start = start_time or now
        end = end_time or now

        # 计算持续时间
        duration_seconds = int((end - start).total_seconds()) if start and end else 0

        report = {
            "scan_mode": scan_mode,
            "start_time": start.isoformat() if isinstance(start, datetime) else start,
            "end_time": end.isoformat() if isinstance(end, datetime) else end,
            "total_files": stats.get("total_files", 0),
            "total_keys": stats.get("total_keys", 0),
            "valid_keys": stats.get("valid_keys", 0),
            "queries_processed": stats.get("queries_completed", 0) or stats.get("total_queries", 0),
            "duration_seconds": duration_seconds
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

    def get_report_keys(self, report_id: int) -> List[str]:
        """获取报告关联的密钥列表."""
        report = db.get_scan_report(report_id)
        if not report:
            return []

        start_time = report.get('started_at')
        end_time = report.get('ended_at')

        # 如果没有时间范围，尝试直接获取所有有效密钥
        if not start_time or not end_time:
            # 回退方案：获取所有有效密钥
            all_keys = db.get_all_keys(is_valid=True)
            return [key.get('key_value') for key in all_keys if key.get('key_value')]

        # 根据时间范围获取密钥
        keys = db.get_keys_by_time_range(start_time, end_time, is_valid=True)
        
        # 如果时间范围查询没有结果，但报告显示有有效密钥，回退获取所有有效密钥
        if not keys and report.get('valid_keys', 0) > 0:
            all_keys = db.get_all_keys(is_valid=True)
            return [key.get('key_value') for key in all_keys if key.get('key_value')]
        
        return [key.get('key_value') for key in keys if key.get('key_value')]

    def delete_report(self, report_id: int):
        """Delete a scan report."""
        db.delete_scan_report(report_id)
    
    def clear_all_reports(self):
        """Clear all scan reports."""
        db.clear_scan_reports()

