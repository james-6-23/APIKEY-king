"""
Unit tests for services.
"""

import pytest
import json
from unittest.mock import Mock, patch

from src.services import ConfigService, GitHubService, FileService
from src.models import Checkpoint


class TestConfigService:
    """Test configuration service."""
    
    def test_load_default_config(self, temp_dir):
        """Test loading default configuration."""
        # Create a test config file
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        default_config = {
            "data_path": "./test_data",
            "github_tokens": "token1,token2"
        }
        
        with open(config_dir / "default.yaml", "w") as f:
            import yaml
            yaml.dump(default_config, f)
        
        service = ConfigService(str(config_dir))
        config = service.load_config()
        
        assert config.data_path == "./test_data"
        assert len(config.github.tokens) == 2
    
    def test_env_override(self, temp_dir, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("GITHUB_TOKENS", "env_token1,env_token2")
        monkeypatch.setenv("DATA_PATH", "/env/data")
        
        service = ConfigService(str(temp_dir / "config"))
        config = service.load_config()
        
        assert len(config.github.tokens) == 2
        assert "env_token1" in config.github.tokens
        assert config.data_path == "/env/data"


class TestFileService:
    """Test file service."""
    
    def test_checkpoint_save_load(self, temp_dir):
        """Test saving and loading checkpoint."""
        service = FileService(str(temp_dir))
        
        # Create a checkpoint
        checkpoint = Checkpoint()
        checkpoint.add_scanned_sha("abc123")
        checkpoint.add_processed_query("test query")
        checkpoint.update_scan_time()
        
        # Save checkpoint
        service.save_checkpoint(checkpoint)
        
        # Load checkpoint
        loaded_checkpoint = service.load_checkpoint()
        
        assert loaded_checkpoint.last_scan_time is not None
        assert "abc123" in loaded_checkpoint.scanned_shas
        assert "test query" in loaded_checkpoint.processed_queries
    
    def test_queries_file_creation(self, temp_dir):
        """Test automatic queries file creation."""
        service = FileService(str(temp_dir))
        queries = service.load_queries("test_queries.txt")
        
        # Should create default queries file
        queries_file = temp_dir / "test_queries.txt"
        assert queries_file.exists()
        assert len(queries) > 0


class TestGitHubService:
    """Test GitHub service."""
    
    @pytest.fixture
    def github_service(self, sample_config):
        """Create GitHub service with test config."""
        return GitHubService(sample_config)
    
    def test_token_rotation(self, github_service):
        """Test token rotation logic."""
        token1 = github_service._get_next_token()
        token2 = github_service._get_next_token()
        
        assert token1 != token2
        assert token1 in github_service.tokens
        assert token2 in github_service.tokens
    
    @patch('requests.get')
    def test_search_code_success(self, mock_get, github_service):
        """Test successful GitHub code search."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "total_count": 1,
            "items": [{"path": "test.py", "sha": "abc123"}]
        }
        mock_response.headers = {"X-RateLimit-Remaining": "5000"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = github_service.search_code("test query")
        
        assert result["total_count"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["path"] == "test.py"
    
    @patch('requests.get')
    def test_get_file_content_success(self, mock_get, github_service, sample_github_items):
        """Test successful file content retrieval."""
        # Mock metadata response
        metadata_response = Mock()
        metadata_response.json.return_value = {
            "encoding": "base64",
            "content": "VGVzdCBjb250ZW50"  # "Test content" in base64
        }
        metadata_response.raise_for_status.return_value = None
        
        mock_get.return_value = metadata_response
        
        content = github_service.get_file_content(sample_github_items[0])
        
        assert content == "Test content"