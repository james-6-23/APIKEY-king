"""
Test configuration and fixtures.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.models.config import AppConfig, ExtractorConfig, ValidatorConfig, GitHubConfig, ScanConfig
from src.services import ConfigService


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_config():
    """Create sample configuration for testing."""
    return AppConfig(
        data_path="./test_data",
        github=GitHubConfig(
            tokens=["test_token_1", "test_token_2"]
        ),
        scan=ScanConfig(
            date_range_days=365,
            file_path_blacklist=["test", "example"],
            queries_file="test_queries.txt"
        ),
        extractors={
            "gemini": ExtractorConfig(
                name="gemini",
                enabled=True,
                patterns={"strict": "AIzaSy[A-Za-z0-9\\-_]{33}"}
            ),
            "modelscope": ExtractorConfig(
                name="modelscope",
                enabled=True,
                patterns={"strict": "ms-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"},
                base_urls=["api-inference.modelscope.cn"],
                extract_only=True
            )
        },
        validators={
            "gemini": ValidatorConfig(
                name="gemini",
                enabled=True,
                model_name="gemini-2.5-flash"
            )
        }
    )


@pytest.fixture  
def sample_github_items():
    """Sample GitHub search result items."""
    return [
        {
            "html_url": "https://github.com/test/repo/blob/main/config.py",
            "path": "config.py",
            "sha": "abc123",
            "repository": {
                "full_name": "test/repo",
                "pushed_at": "2023-01-01T00:00:00Z"
            }
        },
        {
            "html_url": "https://github.com/test/repo2/blob/main/.env",
            "path": ".env", 
            "sha": "def456",
            "repository": {
                "full_name": "test/repo2",
                "pushed_at": "2023-02-01T00:00:00Z"
            }
        }
    ]


@pytest.fixture
def sample_file_content():
    """Sample file content with API keys."""
    return {
        "gemini_key": """
# Configuration file
GEMINI_API_KEY=AIzaSyDaGmWKa4JsXMe5jdbtF0JhIxNOL2D4EKs
OPENAI_API_KEY=sk-1234567890
""",
        "modelscope_key": """
import requests

# ModelScope API configuration
BASE_URL = "https://api-inference.modelscope.cn/v1/"
API_KEY = "ms-12345678-1234-1234-1234-123456789abc"

def call_api():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(BASE_URL + "chat/completions", headers=headers)
""",
        "mixed_keys": """
# Mixed API keys
GEMINI_KEY=AIzaSyBaGmWKa4JsXMe5jdbtF0JhIxNOL2D4EKt
MODELSCOPE_KEY=ms-87654321-4321-4321-4321-abcdef123456
BASE_URL=https://api-inference.modelscope.cn/v1/
""",
        "no_keys": """
# Just some regular code
def hello_world():
    print("Hello, World!")
    return 42
"""
    }