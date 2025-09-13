"""
OpenRouter API key extractor.
"""

from typing import List
from .base import BaseExtractor


class OpenRouterExtractor(BaseExtractor):
    """Extractor for OpenRouter API keys (sk-or-v1 format)."""
    
    @property
    def supported_services(self) -> List[str]:
        """Return list of supported service names."""
        return ['openrouter']
    
    def _is_valid_key(self, key: str, content: str, position: int) -> bool:
        """OpenRouter-specific key validation."""
        if not super()._is_valid_key(key, content, position):
            return False
        
        # Must start with sk-or-v1-
        if not key.lower().startswith('sk-or-v1-'):
            return False
        
        # Filter out placeholders with too many zeros
        if "0000000000000000" in key.lower():
            return False
        
        return True