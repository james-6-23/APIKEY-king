"""
Configuration related schemas.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ValidatorConfig(BaseModel):
    """Validator configuration model."""
    enabled: bool = True
    model: str


class PerformanceConfig(BaseModel):
    """Performance configuration model."""
    max_concurrent_files: int = Field(default=5, ge=1, le=20, description="最大并发处理文件数")
    request_delay: float = Field(default=1.0, ge=0, le=10, description="请求间隔（秒）")
    github_timeout: int = Field(default=30, ge=10, le=120, description="GitHub请求超时（秒）")
    validation_timeout: int = Field(default=30, ge=10, le=120, description="验证超时（秒）")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")


class ConfigRequest(BaseModel):
    """Configuration request model."""
    github_tokens: List[str]
    proxy: Optional[str] = None
    scan_mode: str = "compatible"
    date_range_days: int = 730
    validators: Optional[Dict[str, ValidatorConfig]] = None
    performance: Optional[PerformanceConfig] = None


