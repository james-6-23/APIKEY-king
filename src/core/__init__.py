"""
Core abstractions and interfaces for the APIKEY-king scanner.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class ScanMode(Enum):
    """Supported scanning modes."""
    COMPATIBLE = "compatible"
    MODELSCOPE_ONLY = "modelscope-only"
    OPENROUTER_ONLY = "openrouter-only"
    GEMINI_ONLY = "gemini-only"
    SILICONFLOW_ONLY = "siliconflow-only"


@dataclass
class ExtractionResult:
    """Result of key extraction from content."""
    keys: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not isinstance(self.keys, list):
            self.keys = []
        if not isinstance(self.metadata, dict):
            self.metadata = {}


@dataclass
class ValidationResult:
    """Result of key validation."""
    is_valid: bool
    status: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class KeyExtractor(ABC):
    """Abstract base class for key extractors."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this extractor."""
        pass
    
    @property
    @abstractmethod
    def supported_services(self) -> List[str]:
        """Return list of supported service names."""
        pass
    
    @abstractmethod
    def should_process(self, content: str, context: Dict[str, Any]) -> bool:
        """
        Determine if this extractor should process the given content.
        
        Args:
            content: File content to analyze
            context: Additional context (file path, repository info, etc.)
            
        Returns:
            True if this extractor should process the content
        """
        pass
    
    @abstractmethod
    def extract(self, content: str, context: Dict[str, Any]) -> ExtractionResult:
        """
        Extract API keys from the given content.
        
        Args:
            content: File content to analyze
            context: Additional context information
            
        Returns:
            ExtractionResult containing found keys and metadata
        """
        pass


class KeyValidator(ABC):
    """Abstract base class for key validators."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this validator."""
        pass
    
    @property
    @abstractmethod
    def supported_key_types(self) -> List[str]:
        """Return list of supported key types."""
        pass
    
    @abstractmethod
    def can_validate(self, key: str) -> bool:
        """
        Check if this validator can validate the given key.
        
        Args:
            key: API key to check
            
        Returns:
            True if this validator can handle the key
        """
        pass
    
    @abstractmethod
    def validate(self, key: str, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate an API key.
        
        Args:
            key: API key to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult with validation status
        """
        pass


class Scanner(ABC):
    """Abstract base class for scanners."""
    
    def __init__(self, extractors: List[KeyExtractor], validators: List[KeyValidator]):
        self.extractors = extractors
        self.validators = validators
    
    @abstractmethod
    def scan_content(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan content for API keys using configured extractors and validators.
        
        Args:
            content: Content to scan
            context: Context information (file path, repo info, etc.)
            
        Returns:
            Dictionary containing scan results
        """
        pass


# Export all important classes
__all__ = [
    'ScanMode',
    'ExtractionResult', 
    'ValidationResult',
    'KeyExtractor',
    'KeyValidator', 
    'Scanner',
    'APIKeyScanner'
]

# Import the main scanner implementation after defining base classes
from .scanner import APIKeyScanner