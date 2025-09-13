"""
Integration test for validation functionality across all modes.
"""

import pytest
from unittest.mock import Mock, patch
import os

from src.main import Application
from src.core import ScanMode


class TestValidationModes:
    """Test validation functionality across different scanning modes."""
    
    def setup_method(self):
        """Setup test environment variables."""
        os.environ.update({
            'GITHUB_TOKENS': 'test_token_123',
            'DATA_PATH': './test_data',
            'GEMINI_VALIDATION_ENABLED': 'true',
            'OPENROUTER_VALIDATION_ENABLED': 'true',
        })
    
    def test_openrouter_only_mode_validation(self):
        """Test that OpenRouter-only mode enables validation."""
        app = Application(ScanMode.OPENROUTER_ONLY)
        
        # Mock config loading
        with patch.object(app.config_service, 'load_config') as mock_config:
            mock_config.return_value = self._create_mock_config()
            
            # Initialize app
            with patch.object(app, '_create_extractors') as mock_extractors, \
                 patch.object(app, '_create_validators') as mock_validators, \
                 patch('src.main.GitHubService'), \
                 patch('src.main.FileService'):
                
                mock_extractors.return_value = []
                mock_validators.return_value = []
                
                app.initialize()
                
                # Check that OpenRouter extractor validation is enabled
                openrouter_config = app.config.extractors.get('openrouter')
                assert openrouter_config is not None
                assert openrouter_config.enabled == True
                assert openrouter_config.extract_only == False  # Validation enabled
                
                # Check that OpenRouter validator is enabled
                openrouter_validator = app.config.validators.get('openrouter')
                assert openrouter_validator is not None
                assert openrouter_validator.enabled == True
    
    def test_gemini_only_mode_validation(self):
        """Test that Gemini-only mode enables validation."""
        app = Application(ScanMode.GEMINI_ONLY)
        
        with patch.object(app.config_service, 'load_config') as mock_config:
            mock_config.return_value = self._create_mock_config()
            
            with patch.object(app, '_create_extractors') as mock_extractors, \
                 patch.object(app, '_create_validators') as mock_validators, \
                 patch('src.main.GitHubService'), \
                 patch('src.main.FileService'):
                
                mock_extractors.return_value = []
                mock_validators.return_value = []
                
                app.initialize()
                
                # Check that Gemini extractor validation is enabled
                gemini_config = app.config.extractors.get('gemini')
                assert gemini_config is not None
                assert gemini_config.enabled == True
                assert gemini_config.extract_only == False  # Validation enabled
                
                # Check that Gemini validator is enabled
                gemini_validator = app.config.validators.get('gemini')
                assert gemini_validator is not None
                assert gemini_validator.enabled == True
    
    def test_compatible_mode_all_validation(self):
        """Test that compatible mode enables all validations."""
        app = Application(ScanMode.COMPATIBLE)
        
        with patch.object(app.config_service, 'load_config') as mock_config:
            mock_config.return_value = self._create_mock_config()
            
            with patch.object(app, '_create_extractors') as mock_extractors, \
                 patch.object(app, '_create_validators') as mock_validators, \
                 patch('src.main.GitHubService'), \
                 patch('src.main.FileService'):
                
                mock_extractors.return_value = []
                mock_validators.return_value = []
                
                app.initialize()
                
                # Check that both Gemini and OpenRouter have validation enabled
                gemini_config = app.config.extractors.get('gemini')
                openrouter_config = app.config.extractors.get('openrouter')
                
                assert gemini_config.extract_only == False  # Validation enabled
                assert openrouter_config.extract_only == False  # Validation enabled
                
                # Check that all validators are enabled
                gemini_validator = app.config.validators.get('gemini')
                openrouter_validator = app.config.validators.get('openrouter')
                
                assert gemini_validator.enabled == True
                assert openrouter_validator.enabled == True
    
    def test_modelscope_only_mode_no_validation(self):
        """Test that ModelScope-only mode doesn't enable validation (not supported)."""
        app = Application(ScanMode.MODELSCOPE_ONLY)
        
        with patch.object(app.config_service, 'load_config') as mock_config:
            mock_config.return_value = self._create_mock_config()
            
            with patch.object(app, '_create_extractors') as mock_extractors, \
                 patch.object(app, '_create_validators') as mock_validators, \
                 patch('src.main.GitHubService'), \
                 patch('src.main.FileService'):
                
                mock_extractors.return_value = []
                mock_validators.return_value = []
                
                app.initialize()
                
                # Check that ModelScope extractor has validation disabled
                modelscope_config = app.config.extractors.get('modelscope')
                assert modelscope_config is not None
                assert modelscope_config.enabled == True
                assert modelscope_config.extract_only == True  # No validation available
    
    def _create_mock_config(self):
        """Create mock configuration."""
        from src.models.config import AppConfig, ExtractorConfig, ValidatorConfig
        
        mock_config = Mock(spec=AppConfig)
        mock_config.data_path = './test_data'
        
        # Mock extractors
        mock_config.extractors = {
            'gemini': ExtractorConfig(name='gemini', enabled=True),
            'modelscope': ExtractorConfig(name='modelscope', enabled=True),
            'openrouter': ExtractorConfig(name='openrouter', enabled=True)
        }
        
        # Mock validators
        mock_config.validators = {
            'gemini': ValidatorConfig(name='gemini', enabled=True),
            'openrouter': ValidatorConfig(name='openrouter', enabled=True)
        }
        
        mock_config.get_enabled_extractors.return_value = mock_config.extractors
        mock_config.get_enabled_validators.return_value = mock_config.validators
        mock_config.github = Mock()
        mock_config.github.tokens = ['test_token']
        mock_config.scan = Mock()
        mock_config.scan.queries_file = 'test_queries.txt'
        mock_config.get_proxy_configs.return_value = []
        
        return mock_config


class TestValidationConfiguration:
    """Test validation configuration from environment variables."""
    
    def test_gemini_validation_can_be_disabled(self):
        """Test that Gemini validation can be disabled via env var."""
        with patch.dict(os.environ, {'GEMINI_VALIDATION_ENABLED': 'false'}):
            from src.services.config_service import ConfigService
            
            service = ConfigService()
            validators = service._load_validator_configs()
            
            gemini_validator = validators.get('gemini')
            assert gemini_validator.enabled == False
    
    def test_openrouter_validation_can_be_disabled(self):
        """Test that OpenRouter validation can be disabled via env var."""
        with patch.dict(os.environ, {'OPENROUTER_VALIDATION_ENABLED': 'false'}):
            from src.services.config_service import ConfigService
            
            service = ConfigService()
            validators = service._load_validator_configs()
            
            openrouter_validator = validators.get('openrouter')
            assert openrouter_validator.enabled == False
    
    def test_validation_timeout_configuration(self):
        """Test that validation timeout can be configured."""
        with patch.dict(os.environ, {
            'GEMINI_TIMEOUT': '60.0',
            'OPENROUTER_TIMEOUT': '45.0'
        }):
            from src.services.config_service import ConfigService
            
            service = ConfigService()
            validators = service._load_validator_configs()
            
            gemini_validator = validators.get('gemini')
            openrouter_validator = validators.get('openrouter')
            
            assert gemini_validator.timeout == 60.0
            assert openrouter_validator.timeout == 45.0