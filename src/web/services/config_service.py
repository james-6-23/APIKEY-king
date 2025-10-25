"""
Configuration service.
"""

from typing import Dict, Optional
from ..database.database import db
from ..schemas.config import ConfigRequest, ValidatorConfig

log_service = None


def get_log_service():
    """Get log service instance (lazy loading to avoid circular import)."""
    global log_service
    if log_service is None:
        from .log_service import LogService
        log_service = LogService()
    return log_service


class ConfigService:
    """Configuration management service."""
    
    def __init__(self):
        self._cache = {}
    
    def save_config(self, request: ConfigRequest):
        """Save configuration to database."""
        # 准备验证器配置
        validators_config = request.validators or {
            "gemini": ValidatorConfig(enabled=True, model="gemini-2.0-flash-exp"),
            "openrouter": ValidatorConfig(enabled=True, model="deepseek/deepseek-chat-v3:free"),
            "modelscope": ValidatorConfig(enabled=True, model="Qwen/Qwen2-1.5B-Instruct"),
            "siliconflow": ValidatorConfig(enabled=True, model="Qwen/Qwen2.5-7B-Instruct"),
        }
        
        # 准备性能配置
        from ..schemas.config import PerformanceConfig
        performance_config = request.performance or PerformanceConfig()
        
        # Create config
        config = {
            "github_tokens": request.github_tokens,
            "proxy": request.proxy,
            "scan_mode": request.scan_mode,
            "date_range_days": request.date_range_days,
            "validators": {k: v.dict() if hasattr(v, 'dict') else v for k, v in validators_config.items()},
            "performance": performance_config.dict() if hasattr(performance_config, 'dict') else performance_config
        }
        
        # 保存到数据库
        db.save_config("github_tokens", request.github_tokens)
        db.save_config("proxy", request.proxy)
        db.save_config("scan_mode", request.scan_mode)
        db.save_config("date_range_days", request.date_range_days)
        db.save_config("validators", config["validators"])
        db.save_config("performance", config["performance"])
        
        # 更新缓存
        self._cache = config
        
        log_svc = get_log_service()
        log_svc.add_log("info", "Configuration updated", {
            "token_count": len(request.github_tokens),
            "scan_mode": request.scan_mode
        })
    
    def get_config(self) -> Optional[Dict]:
        """Get configuration from cache or database."""
        if not self._cache:
            db_config = db.get_all_configs()
            if db_config:
                self._cache = {
                    "github_tokens": db_config.get("github_tokens", []),
                    "proxy": db_config.get("proxy"),
                    "scan_mode": db_config.get("scan_mode", "compatible"),
                    "date_range_days": db_config.get("date_range_days", 730),
                    "validators": db_config.get("validators", {}),
                    "performance": db_config.get("performance", {
                        "max_concurrent_files": 5,
                        "request_delay": 1.0,
                        "github_timeout": 30,
                        "validation_timeout": 30,
                        "max_retries": 3
                    })
                }
        
        return self._cache.copy() if self._cache else None
    
    def clear_cache(self):
        """Clear configuration cache."""
        self._cache = {}

