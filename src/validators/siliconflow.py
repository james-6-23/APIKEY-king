"""
SiliconFlow API key validator.
"""

import os
import time
import requests
from typing import Dict, Any, List

from .base import BaseValidator
from ..core import ValidationResult
from ..models.config import ValidatorConfig
from ..utils.logger import logger


class SiliconFlowValidator(BaseValidator):
    """Validator for SiliconFlow API keys."""
    
    def __init__(self, config: ValidatorConfig):
        super().__init__(config)
        self.base_url = "https://api.siliconflow.cn/v1"

    @property
    def supported_key_types(self) -> List[str]:
        """Return list of supported key types."""
        return ['siliconflow']

    def can_validate(self, key: str) -> bool:
        """Check if this validator can validate the given key."""
        # SiliconFlow keys start with 'sk-' and are 40-64 characters long
        import re
        pattern = r'^sk-[a-z]{40,64}$'
        return bool(re.match(pattern, key, re.IGNORECASE))
    
    def validate(self, key: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate SiliconFlow API key."""
        if not self.config.enabled:
            return self._create_skip_result("Validator disabled")
        
        # Add delay to avoid rate limiting
        self._add_delay()
        
        try:
            # Test the key with a simple chat completion request
            url = f"{self.base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            
            # Use a lightweight model for testing
            test_model = self.config.model_name or "Qwen/Qwen2.5-72B-Instruct"
            
            data = {
                "model": test_model,
                "messages": [
                    {
                        "role": "user",
                        "content": "hi"  # Minimal content
                    }
                ],
                "max_tokens": 1,      # Minimal token usage
                "temperature": 0,     # Deterministic output
                "stream": False       # Simple response
            }
            
            # Set up proxy if available
            proxies = None
            proxy_config = context.get('proxy_config') if context else None
            if proxy_config:
                proxies = {
                    'http': proxy_config.get('http'),
                    'https': proxy_config.get('https')
                }
            
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=self.config.timeout,
                proxies=proxies
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return self._create_success_result({
                    'test_response': 'success',
                    'model_used': test_model,
                    'usage': response_data.get('usage', {}),
                    'response_time': response.elapsed.total_seconds()
                })
            
            elif response.status_code == 401:
                return self._create_error_result("unauthorized", "Invalid API key")
            
            elif response.status_code == 429:
                return self._create_error_result("rate_limited", "Rate limit exceeded")
            
            elif response.status_code == 403:
                return self._create_error_result("forbidden", "Access forbidden")
            
            elif response.status_code == 400:
                # Check if it's a model issue
                error_data = response.json() if response.content else {}
                error_message = error_data.get('error', {}).get('message', 'Bad request')
                
                if 'model' in error_message.lower():
                    return self._create_error_result("model_issue", f"Model issue: {error_message}")
                else:
                    return self._create_error_result("bad_request", error_message)
            
            else:
                return self._create_error_result("unknown", f"HTTP {response.status_code}: {response.text}")
        
        except requests.exceptions.Timeout:
            return self._create_error_result("timeout", f"Request timeout after {self.config.timeout}s")
        
        except requests.exceptions.ConnectionError:
            return self._create_error_result("network_error", "Connection error")
        
        except requests.exceptions.RequestException as e:
            return self._create_error_result("network_error", f"Request error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error validating SiliconFlow key: {e}")
            return self._create_error_result("unknown", f"Unexpected error: {str(e)}")
    
    def can_validate(self, key: str) -> bool:
        """Check if this validator can handle the given key."""
        return key.startswith('sk-') and len(key) >= 30
