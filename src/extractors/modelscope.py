"""
ModelScope API key extractor.
"""

from typing import List
from .base import BaseExtractor


class ModelScopeExtractor(BaseExtractor):
    """Extractor for ModelScope API keys (ms-UUID format)."""
    
    @property
    def supported_services(self) -> List[str]:
        """Return list of supported service names."""
        return ['modelscope']
    
    def _is_valid_key(self, key: str, content: str, position: int) -> bool:
        """ModelScope-specific key validation."""
        if not super()._is_valid_key(key, content, position):
            return False
        
        # Must start with ms-
        if not key.lower().startswith('ms-'):
            return False
        
        # Filter out obvious placeholder
        if key.lower() == "ms-00000000-0000-0000-0000-000000000000":
            return False
        
        return True