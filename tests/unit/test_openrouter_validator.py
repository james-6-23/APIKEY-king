"""
Unit tests for OpenRouter validator.
"""

import pytest
from unittest.mock import Mock, patch
import requests

from src.validators import OpenRouterValidator
from src.models.config import ValidatorConfig
from src.core import ValidationResult


class TestOpenRouterValidator:
    """Test OpenRouter key validator."""
    
    @pytest.fixture
    def openrouter_validator(self):
        config = ValidatorConfig(
            name="openrouter",
            enabled=True,
            api_endpoint="https://openrouter.ai/api/v1/chat/completions",
            model_name="deepseek/deepseek-chat-v3.1:free",
            timeout=30.0
        )
        return OpenRouterValidator(config)
    
    def test_can_validate_valid_key(self, openrouter_validator):
        """Test validation of valid OpenRouter key format."""
        valid_key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        assert openrouter_validator.can_validate(valid_key) == True
    
    def test_cannot_validate_invalid_key_format(self, openrouter_validator):
        """Test rejection of invalid key formats."""
        invalid_keys = [
            "AIzaSyDaGmWKa4JsXMe5jdbtF0JhIxNOL2D4EKs",  # Gemini key
            "sk-1234567890abcdef",  # OpenAI key
            "ms-12345678-1234-1234-1234-123456789abc",  # ModelScope key
            "sk-or-v2-1234567890abcdef",  # Wrong version
            "random-string"
        ]
        
        for key in invalid_keys:
            assert openrouter_validator.can_validate(key) == False
    
    def test_supported_key_types(self, openrouter_validator):
        """Test supported key types."""
        types = openrouter_validator.supported_key_types
        assert "openrouter" in types
    
    @patch('requests.post')
    def test_validate_success(self, mock_post, openrouter_validator):
        """Test successful key validation."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello"}}],
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2
            },
            "model": "deepseek/deepseek-chat-v3.1:free"
        }
        mock_post.return_value = mock_response
        
        # Test validation
        key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        result = openrouter_validator.validate(key)
        
        assert result.is_valid == True
        assert result.status == "valid"
        assert result.metadata["test_response"] == "success"
        assert result.metadata["model_used"] == "deepseek/deepseek-chat-v3.1:free"
        
        # Verify API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["headers"]["Authorization"] == f"Bearer {key}"
        assert "deepseek/deepseek-chat-v3.1:free" in call_args[1]["data"]
    
    @patch('requests.post')
    def test_validate_unauthorized(self, mock_post, openrouter_validator):
        """Test validation with unauthorized key."""
        # Mock unauthorized response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key",
                "type": "invalid_request_error"
            }
        }
        mock_post.return_value = mock_response
        
        key = "sk-or-v1-invalid-key"
        result = openrouter_validator.validate(key)
        
        assert result.is_valid == False
        assert result.status == "unauthorized"
        assert "Invalid API key" in result.error_message
    
    @patch('requests.post')
    def test_validate_rate_limited(self, mock_post, openrouter_validator):
        """Test validation with rate limiting."""
        # Mock rate limited response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {
            "error": {
                "message": "Rate limit exceeded",
                "type": "rate_limit_error"
            }
        }
        mock_post.return_value = mock_response
        
        key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        result = openrouter_validator.validate(key)
        
        assert result.is_valid == False
        assert result.status == "rate_limited"
        assert result.metadata["retry_after"] == 60
    
    @patch('requests.post')
    def test_validate_model_not_available(self, mock_post, openrouter_validator):
        """Test validation when model is not available (400 error but key valid)."""
        # Mock model not available response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "message": "Model deepseek/deepseek-chat-v3.1:free not found",
                "type": "invalid_request_error"
            }
        }
        mock_post.return_value = mock_response
        
        key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        result = openrouter_validator.validate(key)
        
        # Should be considered valid since the key works but model has issues
        assert result.is_valid == True
        assert result.status == "valid"
        assert "Model may not be available" in result.metadata["warning"]
    
    @patch('requests.post')
    def test_validate_timeout(self, mock_post, openrouter_validator):
        """Test validation timeout."""
        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout()
        
        key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        result = openrouter_validator.validate(key)
        
        assert result.is_valid == False
        assert result.status == "timeout"
        assert "timeout" in result.error_message.lower()
    
    @patch('requests.post')
    def test_validate_connection_error(self, mock_post, openrouter_validator):
        """Test validation connection error."""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        result = openrouter_validator.validate(key)
        
        assert result.is_valid == False
        assert result.status == "connection_error"
        assert "connection error" in result.error_message.lower()
    
    def test_validate_disabled_validator(self, openrouter_validator):
        """Test validation when validator is disabled."""
        openrouter_validator.config.enabled = False
        
        key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        result = openrouter_validator.validate(key)
        
        assert result.is_valid == False
        assert result.status == "disabled"