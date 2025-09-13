"""
OpenRouter API key validator.
"""

import json
import requests
from typing import List, Dict, Any

from .base import BaseValidator
from ..core import ValidationResult


class OpenRouterValidator(BaseValidator):
    """Validator for OpenRouter API keys."""
    
    @property
    def supported_key_types(self) -> List[str]:
        """Return list of supported key types."""
        return ['openrouter']
    
    def can_validate(self, key: str) -> bool:
        """Check if this validator can validate the given key."""
        return key.startswith('sk-or-v1-')
    
    def validate(self, key: str, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate an OpenRouter API key by making a test API call.
        
        Args:
            key: OpenRouter API key to validate
            context: Additional context (may contain proxy config)
            
        Returns:
            ValidationResult with validation status
        """
        if context is None:
            context = {}
        
        if not self.config.enabled:
            return self._create_error_result('disabled', 'OpenRouter validator is disabled')
        
        # Add delay to avoid rate limiting
        self._add_delay()
        
        try:
            # Prepare API request
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/apikey-king",  # Site URL for rankings
                "X-Title": "APIKEY-king Scanner",  # Site title for rankings
            }
            
            # Use minimal test request to avoid costs
            data = {
                "model": "deepseek/deepseek-chat-v3.1:free",  # Use free model
                "messages": [
                    {
                        "role": "user",
                        "content": "hi"  # Minimal content
                    }
                ],
                "max_tokens": 1,  # Minimal token usage
                "temperature": 0,
                "stream": False
            }
            
            # Get proxy config if available
            proxy_config = context.get('proxy_config')
            proxies = None
            if proxy_config and proxy_config.get('http'):
                proxies = {
                    'http': proxy_config.get('http'),
                    'https': proxy_config.get('https')
                }
            
            # Make API request
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(data),
                timeout=self.config.timeout,
                proxies=proxies
            )
            
            # Check response status
            if response.status_code == 200:
                # Parse response to get more info
                try:
                    response_data = response.json()
                    usage = response_data.get('usage', {})
                    model = response_data.get('model', 'unknown')
                    
                    return self._create_success_result({
                        'test_response': 'success',
                        'model_used': model,
                        'tokens_used': usage.get('total_tokens', 0),
                        'prompt_tokens': usage.get('prompt_tokens', 0),
                        'completion_tokens': usage.get('completion_tokens', 0),
                    })
                except json.JSONDecodeError:
                    # Response not JSON, but status is 200, so key works
                    return self._create_success_result({
                        'test_response': 'success',
                        'note': 'Valid response but non-JSON format'
                    })
            
            elif response.status_code == 401:
                # Unauthorized - invalid key
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Unauthorized')
                except:
                    error_message = 'Invalid API key'
                
                return self._create_error_result('unauthorized', f'API key unauthorized: {error_message}')
            
            elif response.status_code == 403:
                # Forbidden - might be rate limited or insufficient permissions
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Forbidden')
                except:
                    error_message = 'Access forbidden'
                
                return self._create_error_result('forbidden', f'Access forbidden: {error_message}')
            
            elif response.status_code == 429:
                # Rate limited
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Rate limited')
                except:
                    error_message = 'Rate limited'
                
                retry_after = response.headers.get('Retry-After', '60')
                return ValidationResult(
                    is_valid=False,
                    status='rate_limited',
                    error_message=f'Rate limited: {error_message}',
                    metadata={
                        'validator': self.name,
                        'retry_after': int(retry_after) if retry_after.isdigit() else 60,
                        'status_code': response.status_code
                    }
                )
            
            elif response.status_code == 400:
                # Bad request - might indicate key format is wrong or model unavailable
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Bad request')
                    error_type = error_data.get('error', {}).get('type', 'bad_request')
                    
                    # Some 400 errors might still indicate a valid key
                    if 'model' in error_message.lower() or 'not found' in error_message.lower():
                        return self._create_success_result({
                            'test_response': 'success',
                            'note': f'Key valid but model issue: {error_message}',
                            'warning': 'Model may not be available'
                        })
                    
                except:
                    error_message = 'Bad request'
                
                return self._create_error_result('bad_request', f'Bad request: {error_message}')
            
            else:
                # Other HTTP errors
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                except:
                    error_message = f'HTTP {response.status_code}'
                
                return self._create_error_result('http_error', f'HTTP error: {error_message}')
                
        except requests.exceptions.Timeout:
            return self._create_error_result('timeout', f'Request timeout after {self.config.timeout}s')
            
        except requests.exceptions.ConnectionError:
            return self._create_error_result('connection_error', 'Connection error - check network/proxy')
            
        except requests.exceptions.RequestException as e:
            return self._create_error_result('request_error', f'Request error: {type(e).__name__}: {e}')
            
        except Exception as e:
            return self._create_error_result('error', f'Validation error: {type(e).__name__}: {e}')