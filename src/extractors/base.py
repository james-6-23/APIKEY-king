"""
Base classes for key extractors.
"""

import re
from abc import ABC
from typing import List, Dict, Any, Tuple

from ..core import KeyExtractor, ExtractionResult
from ..models.config import ExtractorConfig


class BaseExtractor(KeyExtractor):
    """Base implementation for key extractors."""
    
    def __init__(self, config: ExtractorConfig):
        self.config = config
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns from configuration."""
        self._patterns = {}
        for name, pattern in self.config.patterns.items():
            try:
                self._patterns[name] = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{name}': {e}")
    
    @property
    def name(self) -> str:
        """Return the name of this extractor."""
        return self.config.name
    
    def should_process(self, content: str, context: Dict[str, Any]) -> bool:
        """
        Base implementation checks if extractor is enabled and has required base URLs.
        Subclasses can override for more specific logic.
        """
        if not self.config.enabled:
            return False
        
        # If base URLs are configured, check that at least one is present
        if self.config.base_urls:
            return self._contains_base_url(content, self.config.base_urls)[0]
        
        return True
    
    def extract(self, content: str, context: Dict[str, Any]) -> ExtractionResult:
        """Extract keys using configured patterns."""
        all_keys = []
        metadata = {
            'extractor': self.name,
            'patterns_used': [],
            'base_urls_found': []
        }
        
        # Determine which pattern to use
        pattern_name = 'loose' if self.config.use_loose_pattern else 'strict'
        pattern = self._patterns.get(pattern_name)
        
        if not pattern:
            # Fallback to first available pattern
            if self._patterns:
                pattern_name = list(self._patterns.keys())[0]
                pattern = self._patterns[pattern_name]
            else:
                return ExtractionResult(keys=[], metadata=metadata)
        
        metadata['patterns_used'].append(pattern_name)
        
        # Find all matches
        matches = list(pattern.finditer(content))
        
        # Apply proximity filtering if configured
        if self.config.proximity_chars > 0 and self.config.base_urls:
            has_base, base_positions = self._contains_base_url(content, self.config.base_urls)
            if has_base:
                matches = self._filter_by_proximity(matches, base_positions, self.config.proximity_chars)
                metadata['base_urls_found'] = self.config.base_urls
        
        # Apply context filtering if configured
        if self.config.require_key_context:
            matches = self._filter_by_context(matches, content)
        
        # Extract keys and filter
        for match in matches:
            key = match.group(0)
            if self._is_valid_key(key, content, match.start()):
                all_keys.append(key)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keys = []
        for key in all_keys:
            if key not in seen:
                seen.add(key)
                unique_keys.append(key)
        
        metadata['total_matches'] = len(matches)
        metadata['unique_keys'] = len(unique_keys)
        
        return ExtractionResult(keys=unique_keys, metadata=metadata)
    
    def _contains_base_url(self, content: str, base_urls: List[str]) -> Tuple[bool, List[int]]:
        """Check if content contains any of the specified base URLs."""
        if not base_urls:
            return False, []
        
        content_lower = content.lower()
        positions = []
        
        for url in base_urls:
            if not url:
                continue
            url_lower = url.lower()
            start = 0
            while True:
                idx = content_lower.find(url_lower, start)
                if idx == -1:
                    break
                positions.append(idx)
                start = idx + 1
        
        return len(positions) > 0, positions
    
    def _filter_by_proximity(self, matches: List[re.Match], base_positions: List[int], max_distance: int) -> List[re.Match]:
        """Filter matches by proximity to base URL positions."""
        if not base_positions:
            return matches
        
        filtered = []
        for match in matches:
            match_pos = match.start()
            is_near = any(abs(match_pos - base_pos) <= max_distance for base_pos in base_positions)
            if is_near:
                filtered.append(match)
        
        return filtered
    
    def _filter_by_context(self, matches: List[re.Match], content: str) -> List[re.Match]:
        """Filter matches by context keywords."""
        context_pattern = re.compile(r"(key|token|secret|authorization|api[-_ ]?key)", re.IGNORECASE)
        
        filtered = []
        for match in matches:
            # Check surrounding context
            start = max(0, match.start() - 80)
            end = min(len(content), match.end() + 80)
            snippet = content[start:end]
            
            if context_pattern.search(snippet):
                filtered.append(match)
        
        return filtered
    
    def _is_valid_key(self, key: str, content: str, position: int) -> bool:
        """
        Check if a key is valid (not a placeholder or example).
        Subclasses can override for specific validation logic.
        """
        # Basic placeholder detection
        key_lower = key.lower()
        
        # Common placeholder patterns
        if any(placeholder in key_lower for placeholder in [
            'your_key', 'example', 'placeholder', 'test_key',
            'dummy', 'fake', 'sample', 'template'
        ]):
            return False
        
        # Check context for placeholder indicators
        context_start = max(0, position - 45)
        context_end = min(len(content), position + len(key) + 45)
        context = content[context_start:context_end]
        
        if "..." in context or "YOUR_" in context.upper():
            return False
        
        return True