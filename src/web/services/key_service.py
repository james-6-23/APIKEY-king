"""
Key management service.
"""

from typing import List, Dict
from ..database.database import db

log_service = None


def get_log_service():
    """Get log service instance (lazy loading)."""
    global log_service
    if log_service is None:
        from .log_service import LogService
        log_service = LogService()
    return log_service


class KeyService:
    """API key management service."""

    def get_all_keys(self, key_type: str = None) -> List[Dict]:
        """Get all discovered keys."""
        keys_data = db.get_all_keys(is_valid=True, key_type=key_type)

        # 格式化数据
        formatted_keys = []
        for key in keys_data:
            key_info = {
                "key": key.get("key_value", ""),
                "type": key.get("key_type", ""),
                "source": key.get("source_repo", ""),
                "url": key.get("source_url", ""),
                "found_at": key.get("created_at", ""),
                "validation_status": key.get("validation_status", "")
            }
            # 只有当余额存在时才添加（目前只有 siliconflow 支持）
            if key.get("balance"):
                key_info["balance"] = key.get("balance")
            formatted_keys.append(key_info)

        return formatted_keys

    def save_key(self, key_value: str, key_type: str, source_repo: str = None,
                 source_file: str = None, source_url: str = None,
                 is_valid: bool = True, validation_status: str = None,
                 balance: str = None):
        """Save a discovered key."""
        db.save_key(
            key_value=key_value,
            key_type=key_type,
            source_repo=source_repo,
            source_file=source_file,
            source_url=source_url,
            is_valid=is_valid,
            validation_status=validation_status,
            balance=balance
        )

        log_svc = get_log_service()
        log_svc.add_log("success", f"Key saved: {key_type}", {
            "source": source_repo
        })
    
    def clear_all_keys(self):
        """Clear all discovered keys."""
        db.clear_keys()
        log_svc = get_log_service()
        log_svc.add_log("info", "All keys cleared from database")
    
    def get_key_count(self, key_type: str = None) -> int:
        """Get count of discovered keys."""
        return db.get_key_count(is_valid=True, key_type=key_type)

