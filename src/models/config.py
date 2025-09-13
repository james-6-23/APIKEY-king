"""
Data models for configuration management.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import os


@dataclass
class ProxyConfig:
    """Proxy configuration."""
    http: Optional[str] = None
    https: Optional[str] = None
    
    @classmethod
    def from_string(cls, proxy_str: str) -> 'ProxyConfig':
        """Create ProxyConfig from proxy string."""
        if not proxy_str:
            return cls()
        return cls(http=proxy_str, https=proxy_str)


@dataclass
class ExtractorConfig:
    """Configuration for a key extractor."""
    name: str
    enabled: bool = True
    patterns: Dict[str, str] = field(default_factory=dict)
    base_urls: List[str] = field(default_factory=list)
    use_loose_pattern: bool = False
    proximity_chars: int = 0
    require_key_context: bool = False
    extract_only: bool = False
    
    def __post_init__(self):
        if not isinstance(self.patterns, dict):
            self.patterns = {}
        if not isinstance(self.base_urls, list):
            self.base_urls = []


@dataclass
class ValidatorConfig:
    """Configuration for a key validator."""
    name: str
    enabled: bool = True
    api_endpoint: Optional[str] = None
    model_name: Optional[str] = None
    timeout: float = 30.0
    
    def __post_init__(self):
        if self.timeout <= 0:
            self.timeout = 30.0


@dataclass
class GitHubConfig:
    """GitHub API configuration."""
    tokens: List[str] = field(default_factory=list)
    api_url: str = "https://api.github.com/search/code"
    
    def __post_init__(self):
        # Filter out empty tokens
        self.tokens = [token.strip() for token in self.tokens if token.strip()]


@dataclass
class ScanConfig:
    """Scanning configuration."""
    date_range_days: int = 730
    file_path_blacklist: List[str] = field(default_factory=list)
    queries_file: str = "queries.txt"
    
    def __post_init__(self):
        if self.date_range_days <= 0:
            self.date_range_days = 730
        if not isinstance(self.file_path_blacklist, list):
            self.file_path_blacklist = []


@dataclass
class AppConfig:
    """Main application configuration."""
    data_path: str = "./data"
    proxy_list: List[str] = field(default_factory=list)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    scan: ScanConfig = field(default_factory=ScanConfig)
    extractors: Dict[str, ExtractorConfig] = field(default_factory=dict)
    validators: Dict[str, ValidatorConfig] = field(default_factory=dict)
    
    def __post_init__(self):
        if not isinstance(self.github, GitHubConfig):
            self.github = GitHubConfig()
        if not isinstance(self.scan, ScanConfig):
            self.scan = ScanConfig()
        if not isinstance(self.extractors, dict):
            self.extractors = {}
        if not isinstance(self.validators, dict):
            self.validators = {}
    
    def get_proxy_configs(self) -> List[ProxyConfig]:
        """Get list of proxy configurations."""
        return [ProxyConfig.from_string(proxy) for proxy in self.proxy_list if proxy.strip()]
    
    def get_enabled_extractors(self) -> Dict[str, ExtractorConfig]:
        """Get only enabled extractors."""
        return {name: config for name, config in self.extractors.items() if config.enabled}
    
    def get_enabled_validators(self) -> Dict[str, ValidatorConfig]:
        """Get only enabled validators."""
        return {name: config for name, config in self.validators.items() if config.enabled}