"""
Unit tests for extractors.
"""

import pytest
from src.extractors import GeminiExtractor, ModelScopeExtractor, OpenRouterExtractor
from src.models.config import ExtractorConfig


class TestGeminiExtractor:
    """Test Gemini key extractor."""
    
    @pytest.fixture
    def gemini_extractor(self):
        config = ExtractorConfig(
            name="gemini",
            enabled=True,
            patterns={"strict": "AIzaSy[A-Za-z0-9\\-_]{33}"}
        )
        return GeminiExtractor(config)
    
    def test_extract_valid_key(self, gemini_extractor, sample_file_content):
        """Test extraction of valid Gemini key."""
        content = sample_file_content["gemini_key"]
        result = gemini_extractor.extract(content, {})
        
        assert len(result.keys) == 1
        assert result.keys[0] == "AIzaSyDaGmWKa4JsXMe5jdbtF0JhIxNOL2D4EKs"
        assert result.metadata["extractor"] == "gemini"
    
    def test_no_keys_found(self, gemini_extractor, sample_file_content):
        """Test when no keys are found."""
        content = sample_file_content["no_keys"]
        result = gemini_extractor.extract(content, {})
        
        assert len(result.keys) == 0
    
    def test_should_process_always_true(self, gemini_extractor):
        """Test that Gemini extractor always processes content."""
        assert gemini_extractor.should_process("any content", {}) == True
    
    def test_supported_services(self, gemini_extractor):
        """Test supported services list."""
        services = gemini_extractor.supported_services
        assert "gemini" in services
        assert "google-ai" in services


class TestModelScopeExtractor:
    """Test ModelScope key extractor."""
    
    @pytest.fixture
    def modelscope_extractor(self):
        config = ExtractorConfig(
            name="modelscope",
            enabled=True,
            patterns={"strict": "ms-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"},
            base_urls=["api-inference.modelscope.cn"]
        )
        return ModelScopeExtractor(config)
    
    def test_extract_valid_key(self, modelscope_extractor, sample_file_content):
        """Test extraction of valid ModelScope key."""
        content = sample_file_content["modelscope_key"]
        result = modelscope_extractor.extract(content, {})
        
        assert len(result.keys) == 1
        assert result.keys[0] == "ms-12345678-1234-1234-1234-123456789abc"
    
    def test_should_process_with_base_url(self, modelscope_extractor, sample_file_content):
        """Test processing when base URL is present."""
        content = sample_file_content["modelscope_key"]
        assert modelscope_extractor.should_process(content, {}) == True
    
    def test_should_not_process_without_base_url(self, modelscope_extractor, sample_file_content):
        """Test not processing when base URL is absent."""
        content = sample_file_content["no_keys"]
        assert modelscope_extractor.should_process(content, {}) == False
    
    def test_supported_services(self, modelscope_extractor):
        """Test supported services list."""
        services = modelscope_extractor.supported_services
        assert "modelscope" in services


class TestOpenRouterExtractor:
    """Test OpenRouter key extractor."""
    
    @pytest.fixture
    def openrouter_extractor(self):
        config = ExtractorConfig(
            name="openrouter",
            enabled=True,
            patterns={"strict": "sk-or-v1-[0-9a-f]{64}"},
            base_urls=["openrouter.ai"]
        )
        return OpenRouterExtractor(config)
    
    def test_should_process_with_base_url(self, openrouter_extractor):
        """Test processing when base URL is present."""
        content = "Using openrouter.ai API with key sk-or-v1-1234567890abcdef"
        assert openrouter_extractor.should_process(content, {}) == True
    
    def test_should_not_process_without_base_url(self, openrouter_extractor):
        """Test not processing when base URL is absent."""
        content = "Just some random content"
        assert openrouter_extractor.should_process(content, {}) == False
    
    def test_supported_services(self, openrouter_extractor):
        """Test supported services list."""
        services = openrouter_extractor.supported_services
        assert "openrouter" in services