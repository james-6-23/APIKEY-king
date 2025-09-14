"""
Configuration service for loading and managing application configuration.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from ..models.config import (
    AppConfig, GitHubConfig, ScanConfig, 
    ExtractorConfig, ValidatorConfig
)


class ConfigService:
    """Service for loading and managing configuration."""
    
    def __init__(self, config_dir: str = "config", env_file: str = ".env"):
        self.config_dir = Path(config_dir)
        self.env_file = env_file
        self._config: Optional[AppConfig] = None
        
        # Load environment variables
        if os.path.exists(env_file):
            load_dotenv(env_file, override=False)
    
    def load_config(self) -> AppConfig:
        """Load configuration from files and environment variables."""
        if self._config is None:
            self._config = self._build_config()
        return self._config
    
    def _build_config(self) -> AppConfig:
        """Build configuration from multiple sources."""
        # Start with default config
        config_data = self._load_default_config()
        
        # Override with environment variables
        self._apply_env_overrides(config_data)
        
        # Load extractor configurations
        extractors = self._load_extractor_configs()
        
        # Load validator configurations  
        validators = self._load_validator_configs()
        
        return AppConfig(
            data_path=config_data.get('data_path', './data'),
            proxy_list=self._parse_proxy_list(config_data.get('proxy', '')),
            github=GitHubConfig(
                tokens=self._parse_token_list(config_data.get('github_tokens', '')),
                api_url=config_data.get('github_api_url', 'https://api.github.com/search/code')
            ),
            scan=ScanConfig(
                date_range_days=int(config_data.get('date_range_days', 730)),
                file_path_blacklist=self._parse_blacklist(config_data.get('file_path_blacklist', '')),
                queries_file=config_data.get('queries_file', 'queries.txt')
            ),
            extractors=extractors,
            validators=validators
        )
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from YAML file."""
        default_config_file = self.config_dir / "default.yaml"
        if default_config_file.exists():
            try:
                with open(default_config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Could not load default config: {e}")
        
        return {}
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> None:
        """Apply environment variable overrides."""
        env_mappings = {
            'DATA_PATH': 'data_path',
            'PROXY': 'proxy',
            'GITHUB_TOKENS': 'github_tokens',
            'DATE_RANGE_DAYS': 'date_range_days',
            'FILE_PATH_BLACKLIST': 'file_path_blacklist',
            'QUERIES_FILE': 'queries_file'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                config_data[config_key] = env_value
    
    def _load_extractor_configs(self) -> Dict[str, ExtractorConfig]:
        """Load extractor configurations."""
        extractors = {}
        extractor_dir = self.config_dir / "extractors"
        
        if extractor_dir.exists():
            for config_file in extractor_dir.glob("*.yaml"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f) or {}
                    
                    name = config_file.stem
                    extractors[name] = ExtractorConfig(
                        name=name,
                        enabled=data.get('enabled', True),
                        patterns=data.get('patterns', {}),
                        base_urls=data.get('base_urls', []),
                        use_loose_pattern=data.get('use_loose_pattern', False),
                        proximity_chars=data.get('proximity_chars', 0),
                        require_key_context=data.get('require_key_context', False),
                        extract_only=data.get('extract_only', False)
                    )
                except Exception as e:
                    print(f"Warning: Could not load extractor config {config_file}: {e}")
        
        # Apply environment variable overrides for extractors
        self._apply_extractor_env_overrides(extractors)
        
        return extractors
    
    def _load_validator_configs(self) -> Dict[str, ValidatorConfig]:
        """Load validator configurations."""
        validators = {}
        
        # Create default Gemini validator
        validators['gemini'] = ValidatorConfig(
            name='gemini',
            enabled=self._parse_bool(os.getenv('GEMINI_VALIDATION_ENABLED', 'true')),
            api_endpoint='generativelanguage.googleapis.com',
            model_name=os.getenv('HAJIMI_CHECK_MODEL', 'gemini-2.5-flash'),
            timeout=float(os.getenv('GEMINI_TIMEOUT', '30.0'))
        )

        # Create default SiliconFlow validator
        validators['siliconflow'] = ValidatorConfig(
            name='siliconflow',
            enabled=self._parse_bool(os.getenv('SILICONFLOW_VALIDATION_ENABLED', 'true')),
            api_endpoint='api.siliconflow.cn',
            model_name=os.getenv('SILICONFLOW_TEST_MODEL', 'Qwen/Qwen2.5-72B-Instruct'),
            timeout=float(os.getenv('SILICONFLOW_TIMEOUT', '30.0'))
        )
        
        # Create default OpenRouter validator
        validators['openrouter'] = ValidatorConfig(
            name='openrouter',
            enabled=self._parse_bool(os.getenv('OPENROUTER_VALIDATION_ENABLED', 'true')),
            api_endpoint='https://openrouter.ai/api/v1/chat/completions',
            model_name=os.getenv('OPENROUTER_TEST_MODEL', 'deepseek/deepseek-chat-v3.1:free'),
            timeout=float(os.getenv('OPENROUTER_TIMEOUT', '30.0'))
        )

        # Create default ModelScope validator
        validators['modelscope'] = ValidatorConfig(
            name='modelscope',
            enabled=self._parse_bool(os.getenv('MODELSCOPE_VALIDATION_ENABLED', 'true')),
            api_endpoint='https://api-inference.modelscope.cn/v1/chat/completions',
            model_name=os.getenv('MODELSCOPE_TEST_MODEL', 'Qwen/Qwen2-1.5B-Instruct'),
            timeout=float(os.getenv('MODELSCOPE_TIMEOUT', '30.0'))
        )

        return validators
    
    def _apply_extractor_env_overrides(self, extractors: Dict[str, ExtractorConfig]) -> None:
        """Apply environment variable overrides for extractors."""
        # ModelScope extractor overrides
        if 'modelscope' in extractors:
            if os.getenv('TARGET_BASE_URLS'):
                extractors['modelscope'].base_urls = self._parse_list(os.getenv('TARGET_BASE_URLS'))
            if os.getenv('MS_USE_LOOSE_PATTERN'):
                extractors['modelscope'].use_loose_pattern = self._parse_bool(os.getenv('MS_USE_LOOSE_PATTERN'))
            if os.getenv('MS_PROXIMITY_CHARS'):
                extractors['modelscope'].proximity_chars = int(os.getenv('MS_PROXIMITY_CHARS', '0'))
            if os.getenv('MS_REQUIRE_KEY_CONTEXT'):
                extractors['modelscope'].require_key_context = self._parse_bool(os.getenv('MS_REQUIRE_KEY_CONTEXT'))
            if os.getenv('MODELSCOPE_EXTRACT_ONLY'):
                extractors['modelscope'].extract_only = self._parse_bool(os.getenv('MODELSCOPE_EXTRACT_ONLY'))
        
        # OpenRouter extractor overrides
        if 'openrouter' in extractors:
            if os.getenv('OPENROUTER_BASE_URLS'):
                extractors['openrouter'].base_urls = self._parse_list(os.getenv('OPENROUTER_BASE_URLS'))
            if os.getenv('OPENROUTER_USE_LOOSE_PATTERN'):
                extractors['openrouter'].use_loose_pattern = self._parse_bool(os.getenv('OPENROUTER_USE_LOOSE_PATTERN'))
            if os.getenv('OPENROUTER_PROXIMITY_CHARS'):
                extractors['openrouter'].proximity_chars = int(os.getenv('OPENROUTER_PROXIMITY_CHARS', '0'))
            if os.getenv('OPENROUTER_REQUIRE_KEY_CONTEXT'):
                extractors['openrouter'].require_key_context = self._parse_bool(os.getenv('OPENROUTER_REQUIRE_KEY_CONTEXT'))
            if os.getenv('OPENROUTER_EXTRACT_ONLY'):
                extractors['openrouter'].extract_only = self._parse_bool(os.getenv('OPENROUTER_EXTRACT_ONLY'))

        # SiliconFlow extractor overrides
        if 'siliconflow' in extractors:
            if os.getenv('SILICONFLOW_BASE_URLS'):
                extractors['siliconflow'].base_urls = self._parse_list(os.getenv('SILICONFLOW_BASE_URLS'))
            if os.getenv('SILICONFLOW_USE_LOOSE_PATTERN'):
                extractors['siliconflow'].use_loose_pattern = self._parse_bool(os.getenv('SILICONFLOW_USE_LOOSE_PATTERN'))
            if os.getenv('SILICONFLOW_PROXIMITY_CHARS'):
                extractors['siliconflow'].proximity_chars = int(os.getenv('SILICONFLOW_PROXIMITY_CHARS', '0'))
            if os.getenv('SILICONFLOW_REQUIRE_KEY_CONTEXT'):
                extractors['siliconflow'].require_key_context = self._parse_bool(os.getenv('SILICONFLOW_REQUIRE_KEY_CONTEXT'))
            if os.getenv('SILICONFLOW_EXTRACT_ONLY'):
                extractors['siliconflow'].extract_only = self._parse_bool(os.getenv('SILICONFLOW_EXTRACT_ONLY'))
    
    def _parse_token_list(self, tokens_str: str) -> list:
        """Parse comma-separated token list."""
        if not tokens_str:
            return []
        return [token.strip() for token in tokens_str.split(',') if token.strip()]
    
    def _parse_proxy_list(self, proxy_str: str) -> list:
        """Parse comma-separated proxy list."""
        if not proxy_str:
            return []
        return [proxy.strip() for proxy in proxy_str.split(',') if proxy.strip()]
    
    def _parse_blacklist(self, blacklist_str: str) -> list:
        """Parse comma-separated blacklist."""
        if not blacklist_str:
            return []
        return [item.strip().lower() for item in blacklist_str.split(',') if item.strip()]
    
    def _parse_list(self, list_str: str) -> list:
        """Parse comma-separated list."""
        if not list_str:
            return []
        return [item.strip() for item in list_str.split(',') if item.strip()]
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean value from string."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ('true', '1', 'yes', 'on', 'enabled')
        return False
    
    def get_config(self) -> AppConfig:
        """Get the loaded configuration."""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def reload_config(self) -> AppConfig:
        """Reload configuration from sources."""
        self._config = None
        return self.load_config()