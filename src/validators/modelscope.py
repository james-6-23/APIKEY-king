"""
ModelScope API key validator.
"""

import json
import requests
from typing import List, Dict, Any

from .base import BaseValidator
from ..core import ValidationResult


class ModelScopeValidator(BaseValidator):
    """Validator for ModelScope API keys."""
    
    @property
    def supported_key_types(self) -> List[str]:
        """Return list of supported key types."""
        return ['modelscope']
    
    def can_validate(self, key: str) -> bool:
        """Check if this validator can validate the given key."""
        # ModelScope keys start with 'ms-' and follow UUID pattern
        import re
        pattern = r'^ms-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, key, re.IGNORECASE))
    
    def validate(self, key: str, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate a ModelScope API key by making a test API call.
        
        Args:
            key: ModelScope API key to validate (ms-UUID format)
            context: Additional context (may contain proxy config)
            
        Returns:
            ValidationResult with validation status
        """
        if context is None:
            context = {}
        
        if not self.config.enabled:
            return self._create_error_result('disabled', 'ModelScope validator is disabled')
        
        # Add delay to avoid rate limiting
        self._add_delay()
        
        try:
            # ModelScope API endpoint (compatible with OpenAI format)
            url = "https://api-inference.modelscope.cn/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            
            # Use a lightweight model for testing (if available)
            # Using a simple model to minimize cost and latency
            test_model = self.config.model_name or "Qwen/Qwen2-1.5B-Instruct"
            
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
                "stream": False       # Simple response (not streaming)
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
                    model = response_data.get('model', test_model)
                    
                    return self._create_success_result({
                        'test_response': 'success',
                        'model_used': model,
                        'tokens_used': usage.get('total_tokens', 0),
                        'prompt_tokens': usage.get('prompt_tokens', 0),
                        'completion_tokens': usage.get('completion_tokens', 0),
                        'api_endpoint': 'ModelScope Inference API'
                    })
                except json.JSONDecodeError:
                    # Response not JSON, but status is 200, so key works
                    return self._create_success_result({
                        'test_response': 'success',
                        'note': 'Valid response but non-JSON format',
                        'api_endpoint': 'ModelScope Inference API'
                    })
            
            elif response.status_code == 401:
                # Unauthorized - invalid key
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Unauthorized')
                    if isinstance(error_message, dict):
                        error_message = str(error_message)
                except:
                    error_message = 'Invalid API key or unauthorized'
                
                return self._create_error_result('unauthorized', f'API key unauthorized: {error_message}')
            
            elif response.status_code == 403:
                # Forbidden - might be insufficient permissions or service not enabled
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Access forbidden')
                except:
                    error_message = 'Access forbidden - check service permissions'
                
                return self._create_error_result('forbidden', f'Access forbidden: {error_message}')
            
            elif response.status_code == 429:
                # Rate limited
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Rate limit exceeded')
                except:
                    error_message = 'Rate limit exceeded'
                
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
                # Bad request - might indicate model unavailable but key valid
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Bad request')
                    error_type = error_data.get('error', {}).get('type', 'bad_request')
                    
                    # Check if it's a model availability issue
                    if any(keyword in str(error_message).lower() for keyword in 
                           ['model', 'not found', 'not available', 'unavailable']):
                        return self._create_success_result({
                            'test_response': 'success',
                            'note': f'Key valid but model issue: {error_message}',
                            'warning': 'Test model may not be available',
                            'api_endpoint': 'ModelScope Inference API'
                        })
                    
                except:
                    error_message = 'Bad request'
                
                return self._create_error_result('bad_request', f'Bad request: {error_message}')
            
            elif response.status_code == 404:
                # Not found - might be model not available
                return self._create_success_result({
                    'test_response': 'success',
                    'note': f'Key appears valid but test model not found',
                    'warning': f'Model {test_model} not available',
                    'api_endpoint': 'ModelScope Inference API'
                })
            
            else:
                # Other HTTP errors
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                except:
                    error_message = f'HTTP {response.status_code}: {response.text[:200] if response.text else "Unknown error"}'
                
                return self._create_error_result('http_error', f'HTTP error: {error_message}')
                
        except requests.exceptions.Timeout:
            return self._create_error_result('timeout', f'Request timeout after {self.config.timeout}s')
            
        except requests.exceptions.ConnectionError:
            return self._create_error_result('connection_error', 'Connection error - check network/proxy or ModelScope service')
            
        except requests.exceptions.RequestException as e:
            return self._create_error_result('request_error', f'Request error: {type(e).__name__}: {e}')
            
        except Exception as e:
            return self._create_error_result('error', f'Validation error: {type(e).__name__}: {e}')