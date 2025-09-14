"""
SiliconFlow API key extractor.
"""

import re
from typing import List, Dict, Any

from .base import BaseExtractor
from ..core import ExtractionResult
from ..models.config import ExtractorConfig


class SiliconFlowExtractor(BaseExtractor):
    """Extractor for SiliconFlow API keys."""
    
    def __init__(self, config: ExtractorConfig):
        super().__init__(config)

    @property
    def supported_services(self) -> List[str]:
        """Return list of supported service names."""
        return ['siliconflow']
    
    def extract(self, content: str, context: Dict[str, Any] = None) -> ExtractionResult:
        """Extract SiliconFlow API keys from content."""
        if context is None:
            context = {}
        if not self.should_process(content, context):
            return ExtractionResult(keys=[], metadata={})
        
        keys = []
        metadata = {
            'extractor': self.name,
            'pattern_used': 'strict',
            'context_required': self.config.require_key_context
        }
        
        # Use strict pattern by default
        pattern = self.config.patterns.get('strict', r'sk-[a-z]{40,64}')
        
        # If loose pattern is enabled and strict finds nothing
        if self.config.use_loose_pattern:
            strict_matches = re.findall(pattern, content, re.IGNORECASE)
            if not strict_matches:
                pattern = self.config.patterns.get('loose', r'sk-[a-z]{30,}')
                metadata['pattern_used'] = 'loose'
        
        # Find all matches
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        for match in matches:
            # Apply additional filtering if needed
            if self._is_valid_key_format(match):
                keys.append(match)
        
        metadata['keys_found'] = len(keys)
        metadata['total_matches'] = len(matches)
        
        return ExtractionResult(keys=keys, metadata=metadata)
    
    def should_process(self, content: str, context: Dict[str, Any]) -> bool:
        """Check if content should be processed for SiliconFlow keys."""
        if not self.config.enabled:
            return False

        # Check for required base URLs
        if self.config.base_urls:
            content_lower = content.lower()
            has_base_url = any(url.lower() in content_lower for url in self.config.base_urls)
            if not has_base_url:
                return False

        # Check for key context if required
        if self.config.require_key_context:
            context_keywords = ['siliconflow', 'api_key', 'openai', 'client']
            content_lower = content.lower()
            has_context = any(keyword in content_lower for keyword in context_keywords)
            if not has_context:
                return False

        return True
    
    def _is_valid_key_format(self, key: str) -> bool:
        """Validate SiliconFlow key format."""
        if not key.startswith('sk-'):
            return False
        
        # Check length (typical SiliconFlow keys are 40-64 characters)
        if len(key) < 30 or len(key) > 70:
            return False
        
        # Check if it's all lowercase letters after 'sk-'
        key_part = key[3:]  # Remove 'sk-' prefix
        if not key_part.islower() or not key_part.isalpha():
            return False
        
        return True
