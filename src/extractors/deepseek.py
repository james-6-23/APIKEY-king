"""
DeepSeek API key extractor.
"""

import re
from typing import List, Dict, Any

from .base import BaseExtractor
from ..core import ExtractionResult
from ..models.config import ExtractorConfig


class DeepSeekExtractor(BaseExtractor):
    """Extractor for DeepSeek API keys (sk-[a-f0-9]{32})."""

    def __init__(self, config: ExtractorConfig):
        super().__init__(config)

    @property
    def supported_services(self) -> List[str]:
        """Return list of supported service names."""
        return ['deepseek']

    def extract(self, content: str, context: Dict[str, Any] = None) -> ExtractionResult:
        """Extract DeepSeek API keys from content."""
        if context is None:
            context = {}
        if not self.should_process(content, context):
            return ExtractionResult(keys=[], metadata={})

        metadata = {
            'extractor': self.name,
            'pattern_used': 'strict',
            'context_required': self.config.require_key_context,
        }

        # DeepSeek keys are deterministic in shape: 'sk-' + 32 lowercase hex chars.
        # Keeping the regex strict is fine — loose mode isn't useful here because
        # the format is already narrow enough to avoid ambiguity with SiliconFlow
        # (whose keys are 40-64 pure-letter chars and never contain digits).
        pattern = self.config.patterns.get('strict', r'sk-[a-f0-9]{32}')

        matches = re.findall(pattern, content, re.IGNORECASE)

        # Dedupe while preserving order of first occurrence.
        seen = set()
        keys = []
        for match in matches:
            key = match.lower()
            if self._is_valid_key_format(key) and key not in seen:
                seen.add(key)
                keys.append(key)

        metadata['keys_found'] = len(keys)
        metadata['total_matches'] = len(matches)

        return ExtractionResult(keys=keys, metadata=metadata)

    def should_process(self, content: str, context: Dict[str, Any]) -> bool:
        """Check if content should be processed for DeepSeek keys."""
        if not self.config.enabled:
            return False

        if self.config.base_urls:
            content_lower = content.lower()
            has_base_url = any(url.lower() in content_lower for url in self.config.base_urls)
            if not has_base_url:
                return False

        if self.config.require_key_context:
            content_lower = content.lower()
            context_keywords = ['deepseek', 'api.deepseek.com', 'api_key', 'apikey']
            if not any(keyword in content_lower for keyword in context_keywords):
                return False

        return True

    def _is_valid_key_format(self, key: str) -> bool:
        """Validate the literal DeepSeek key shape.

        Required:
          - starts with 'sk-'
          - total length == 35 (3 prefix + 32 hex)
          - body is all hex characters
        """
        if not key.startswith('sk-'):
            return False
        if len(key) != 35:
            return False
        body = key[3:]
        try:
            int(body, 16)
        except ValueError:
            return False
        return True
