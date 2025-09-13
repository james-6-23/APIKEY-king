"""
Gemini API key extractor.
"""

from typing import List
from .base import BaseExtractor


class GeminiExtractor(BaseExtractor):
    """Extractor for Gemini API keys (AIzaSy format)."""
    
    @property
    def supported_services(self) -> List[str]:
        """Return list of supported service names."""
        return ['gemini', 'google-ai']
    
    def _is_valid_key(self, key: str, content: str, position: int) -> bool:
        """Gemini-specific key validation."""
        if not super()._is_valid_key(key, content, position):
            return False
        
        # Gemini keys should be exactly 39 characters (AIzaSy + 33 chars)
        if len(key) != 39:
            return False
        
        # Must start with AIzaSy
        if not key.startswith('AIzaSy'):
            return False
        
        return True