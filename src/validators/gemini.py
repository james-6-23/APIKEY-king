"""
Gemini API key validator.
"""

import os
import random
from typing import List, Dict, Any

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .base import BaseValidator
from ..core import ValidationResult


class GeminiValidator(BaseValidator):
    """Validator for Gemini API keys."""
    
    @property
    def supported_key_types(self) -> List[str]:
        """Return list of supported key types."""
        return ['gemini', 'google-ai']
    
    def can_validate(self, key: str) -> bool:
        """Check if this validator can validate the given key."""
        return key.startswith('AIzaSy') and len(key) == 39
    
    def validate(self, key: str, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate a Gemini API key by making a test API call.
        
        Args:
            key: Gemini API key to validate
            context: Additional context (may contain proxy config)
            
        Returns:
            ValidationResult with validation status
        """
        if context is None:
            context = {}
        
        if not self.config.enabled:
            return self._create_error_result('disabled', 'Gemini validator is disabled')
        
        # Add delay to avoid rate limiting
        self._add_delay()
        
        try:
            # Set up proxy if available
            proxy_config = context.get('proxy_config')
            if proxy_config and proxy_config.get('http'):
                os.environ['grpc_proxy'] = proxy_config.get('http')
            
            # Configure Gemini client
            client_options = {
                "api_endpoint": self.config.api_endpoint or "generativelanguage.googleapis.com"
            }
            
            genai.configure(
                api_key=key,
                client_options=client_options
            )
            
            # Make test API call
            model = genai.GenerativeModel(self.config.model_name or "gemini-2.5-flash")
            response = model.generate_content("hi")
            
            return self._create_success_result({
                'test_response': 'success',
                'model_used': self.config.model_name
            })
            
        except (google_exceptions.PermissionDenied, google_exceptions.Unauthenticated) as e:
            return self._create_error_result('unauthorized', 'API key not authorized or invalid')
        
        except google_exceptions.TooManyRequests as e:
            return ValidationResult(
                is_valid=False,
                status='rate_limited',
                error_message='Rate limited by API',
                metadata={'validator': self.name, 'retry_after': 60}
            )
        
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for rate limiting indicators
            if any(indicator in error_str for indicator in ['429', 'rate limit', 'quota']):
                return ValidationResult(
                    is_valid=False,
                    status='rate_limited',
                    error_message=f'Rate limited: {e}',
                    metadata={'validator': self.name, 'retry_after': 60}
                )
            
            # Check for service disabled
            elif any(indicator in error_str for indicator in ['403', 'service_disabled', 'api has not been used']):
                return self._create_error_result('service_disabled', f'Service disabled: {e}')
            
            else:
                return self._create_error_result('error', f'Validation error: {type(e).__name__}: {e}')