"""
Regular expression patterns for key extraction.
"""

import re
from typing import Dict

# Compiled regex patterns for different key types
PATTERNS = {
    'gemini': {
        'strict': re.compile(r'AIzaSy[A-Za-z0-9\-_]{33}', re.IGNORECASE),
        'description': 'Gemini API keys (AIzaSy + 33 characters)'
    },
    'modelscope': {
        'strict': re.compile(r'ms-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE),
        'loose': re.compile(r'ms-[0-9a-f-]{30,}', re.IGNORECASE),
        'description': 'ModelScope API keys (ms-UUID format)'
    },
    'openrouter': {
        'strict': re.compile(r'sk-or-v1-[0-9a-f]{64}', re.IGNORECASE),
        'loose': re.compile(r'sk-or-v1-[0-9a-f]{40,}', re.IGNORECASE),
        'description': 'OpenRouter API keys (sk-or-v1 format)'
    }
}

# Context patterns for key detection
CONTEXT_PATTERNS = {
    'key_context': re.compile(r'(key|token|secret|authorization|api[-_ ]?key)', re.IGNORECASE),
    'placeholder': re.compile(r'(your_key|example|placeholder|test_key|dummy|fake|sample|template)', re.IGNORECASE)
}


def get_pattern(key_type: str, pattern_type: str = 'strict') -> re.Pattern:
    """
    Get compiled regex pattern for a specific key type.
    
    Args:
        key_type: Type of key (gemini, modelscope, openrouter)
        pattern_type: Pattern strictness (strict, loose)
        
    Returns:
        Compiled regex pattern or None if not found
    """
    return PATTERNS.get(key_type, {}).get(pattern_type)


def get_context_pattern(pattern_name: str) -> re.Pattern:
    """
    Get compiled context pattern.
    
    Args:
        pattern_name: Name of the context pattern
        
    Returns:
        Compiled regex pattern or None if not found
    """
    return CONTEXT_PATTERNS.get(pattern_name)


def is_placeholder_key(key: str) -> bool:
    """
    Check if a key appears to be a placeholder.
    
    Args:
        key: API key to check
        
    Returns:
        True if the key appears to be a placeholder
    """
    placeholder_pattern = CONTEXT_PATTERNS['placeholder']
    return bool(placeholder_pattern.search(key))