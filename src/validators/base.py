"""
Base validator class.
"""

import time
import random
from abc import ABC
from typing import Dict, Any

from ..core import KeyValidator, ValidationResult
from ..models.config import ValidatorConfig


class BaseValidator(KeyValidator):
    """Base implementation for key validators."""
    
    def __init__(self, config: ValidatorConfig):
        self.config = config
    
    @property
    def name(self) -> str:
        """Return the name of this validator."""
        return self.config.name
    
    def _add_delay(self) -> None:
        """Add random delay between validation requests."""
        delay = random.uniform(0.5, 1.5)
        time.sleep(delay)
    
    def _create_error_result(self, status: str, error_message: str) -> ValidationResult:
        """Create an error validation result."""
        return ValidationResult(
            is_valid=False,
            status=status,
            error_message=error_message,
            metadata={'validator': self.name}
        )
    
    def _create_success_result(self, metadata: Dict[str, Any] = None) -> ValidationResult:
        """Create a successful validation result."""
        if metadata is None:
            metadata = {}
        metadata['validator'] = self.name
        
        return ValidationResult(
            is_valid=True,
            status='valid',
            metadata=metadata
        )