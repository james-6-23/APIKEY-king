"""
Integration tests for the complete scanning workflow.
"""

import pytest
from unittest.mock import Mock, patch

from src.main import Application
from src.core import APIKeyScanner
from src.extractors import GeminiExtractor
from src.validators import GeminiValidator


class TestScanningWorkflow:
    """Test complete scanning workflow."""
    
    @pytest.fixture
    def mock_github_response(self, sample_github_items, sample_file_content):
        """Mock GitHub API responses."""
        with patch('src.services.github_service.requests.get') as mock_get:
            # Mock search response
            search_response = Mock()
            search_response.json.return_value = {
                "total_count": 1,
                "items": sample_github_items[:1]
            }
            search_response.headers = {"X-RateLimit-Remaining": "5000"}
            search_response.raise_for_status.return_value = None
            
            # Mock file content response
            content_response = Mock()
            content_response.json.return_value = {
                "encoding": "base64",
                "content": "R0VNSU5JX0FQSV9LRVk9QUl6YVN5RGFHbVdLYTRKc1hNZTVqZGJ0RjBKaEl4Tk9MMkQ0RUtzCk9QRU5BSV9BUElfS0VZPXNrLTEyMzQ1Njc4OTA="  # base64 of sample content
            }
            content_response.raise_for_status.return_value = None
            
            mock_get.side_effect = [search_response, content_response]
            yield mock_get
    
    @patch.dict('os.environ', {'GITHUB_TOKENS': 'test_token'})
    def test_full_scanning_workflow(self, temp_dir, mock_github_response, sample_file_content):
        """Test complete scanning workflow from start to finish."""
        # Create temporary config directory
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        # Create extractors config
        extractors_dir = config_dir / "extractors"
        extractors_dir.mkdir()
        
        with open(extractors_dir / "gemini.yaml", "w") as f:
            f.write("""
name: gemini
enabled: true
patterns:
  strict: "AIzaSy[A-Za-z0-9\\\\-_]{33}"
extract_only: false
""")
        
        # Create default config
        with open(config_dir / "default.yaml", "w") as f:
            f.write(f"""
data_path: "{temp_dir}"
queries_file: "test_queries.txt"
""")
        
        # Create test queries file
        with open(temp_dir / "test_queries.txt", "w") as f:
            f.write("AIzaSy in:file\n")
        
        # Initialize application
        app = Application()
        app.config_service.config_dir = config_dir
        
        # Mock validator to avoid actual API calls
        with patch('src.validators.gemini.genai.configure'), \
             patch('src.validators.gemini.genai.GenerativeModel') as mock_model:
            
            mock_instance = Mock()
            mock_instance.generate_content.return_value = "test response"
            mock_model.return_value = mock_instance
            
            assert app.initialize() == True
            
            # Check that components were created
            assert app.scanner is not None
            assert len(app.scanner.extractors) > 0
            assert len(app.scanner.validators) > 0


class TestAPIKeyScanner:
    """Test the core scanner functionality."""
    
    @pytest.fixture
    def scanner_with_mocks(self):
        """Create scanner with mock extractors and validators."""
        # Mock extractor
        mock_extractor = Mock()
        mock_extractor.name = "test_extractor"
        mock_extractor.should_process.return_value = True
        
        from src.core import ExtractionResult
        mock_extractor.extract.return_value = ExtractionResult(
            keys=["test_key_123"],
            metadata={"extractor": "test_extractor"}
        )
        
        # Mock validator
        mock_validator = Mock()
        mock_validator.name = "test_validator"
        mock_validator.can_validate.return_value = True
        
        from src.core import ValidationResult
        mock_validator.validate.return_value = ValidationResult(
            is_valid=True,
            status="valid",
            metadata={"validator": "test_validator"}
        )
        
        return APIKeyScanner([mock_extractor], [mock_validator])
    
    def test_scan_content_with_keys(self, scanner_with_mocks):
        """Test scanning content that contains keys."""
        content = "Some content with test_key_123"
        context = {"file_path": "test.py"}
        
        results = scanner_with_mocks.scan_content(content, context)
        
        assert results['summary']['total_keys_found'] == 1
        assert results['summary']['total_valid_keys'] == 1
        assert len(results['extracted_keys']) == 1
        assert len(results['validation_results']) == 1
        
        # Check that extraction was called
        scanner_with_mocks.extractors[0].should_process.assert_called_once_with(content, context)
        scanner_with_mocks.extractors[0].extract.assert_called_once_with(content, context)
        
        # Check that validation was called
        scanner_with_mocks.validators[0].can_validate.assert_called_once_with("test_key_123")
        scanner_with_mocks.validators[0].validate.assert_called_once_with("test_key_123", context)
    
    def test_scan_content_no_keys(self, scanner_with_mocks):
        """Test scanning content with no keys."""
        # Configure mock to return no keys
        from src.core import ExtractionResult
        scanner_with_mocks.extractors[0].extract.return_value = ExtractionResult(
            keys=[],
            metadata={"extractor": "test_extractor"}
        )
        
        content = "Some content with no keys"
        context = {"file_path": "test.py"}
        
        results = scanner_with_mocks.scan_content(content, context)
        
        assert results['summary']['total_keys_found'] == 0
        assert results['summary']['total_valid_keys'] == 0
        assert len(results['extracted_keys']) == 0
        assert len(results['validation_results']) == 0