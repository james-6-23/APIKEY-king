"""
Checkpoint and scan result models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Set, List, Dict, Any, Optional

# Import config models
from .config import (
    AppConfig,
    ProxyConfig,
    ExtractorConfig,
    ValidatorConfig,
    GitHubConfig,
    ScanConfig
)

__all__ = [
    'Checkpoint',
    'ScanResult',
    'BatchScanResult',
    'AppConfig',
    'ProxyConfig',
    'ExtractorConfig',
    'ValidatorConfig',
    'GitHubConfig',
    'ScanConfig'
]


@dataclass
class Checkpoint:
    """Checkpoint for tracking scan progress."""
    last_scan_time: Optional[str] = None
    scanned_shas: Set[str] = field(default_factory=set)
    processed_queries: Set[str] = field(default_factory=set)
    
    def add_scanned_sha(self, sha: str) -> None:
        """Add a SHA to the scanned set."""
        if sha:
            self.scanned_shas.add(sha)
    
    def add_processed_query(self, query: str) -> None:
        """Add a query to the processed set."""
        if query:
            self.processed_queries.add(query)
    
    def update_scan_time(self) -> None:
        """Update the last scan time to now."""
        self.last_scan_time = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (excluding scanned_shas)."""
        return {
            "last_scan_time": self.last_scan_time,
            "processed_queries": list(self.processed_queries)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """Create from dictionary."""
        return cls(
            last_scan_time=data.get("last_scan_time"),
            scanned_shas=set(),  # Will be loaded separately
            processed_queries=set(data.get("processed_queries", []))
        )


@dataclass
class ScanResult:
    """Result of scanning a single file."""
    file_url: str
    repository_name: str
    file_path: str
    extracted_keys: Dict[str, List[str]] = field(default_factory=dict)
    validation_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    scan_metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def get_all_keys(self) -> Set[str]:
        """Get all unique keys found in this scan."""
        all_keys = set()
        for keys_list in self.extracted_keys.values():
            all_keys.update(keys_list)
        return all_keys
    
    def get_valid_keys(self) -> Set[str]:
        """Get all keys that passed validation."""
        valid_keys = set()
        for key, result in self.validation_results.items():
            if result.get('is_valid', False):
                valid_keys.add(key)
        return valid_keys
    
    def get_keys_by_extractor(self, extractor_name: str) -> List[str]:
        """Get keys found by a specific extractor."""
        return self.extracted_keys.get(extractor_name, [])


@dataclass
class BatchScanResult:
    """Result of scanning multiple files in a batch."""
    total_files_processed: int = 0
    total_keys_found: int = 0
    total_valid_keys: int = 0
    results: List[ScanResult] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    scan_start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    scan_end_time: Optional[str] = None
    
    def add_result(self, result: ScanResult) -> None:
        """Add a scan result to the batch."""
        self.results.append(result)
        self.total_files_processed += 1
        self.total_keys_found += len(result.get_all_keys())
        self.total_valid_keys += len(result.get_valid_keys())
    
    def add_error(self, error: Dict[str, Any]) -> None:
        """Add an error to the batch."""
        self.errors.append(error)
    
    def finalize(self) -> None:
        """Mark the batch scan as complete."""
        self.scan_end_time = datetime.utcnow().isoformat()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the batch scan results."""
        return {
            'total_files_processed': self.total_files_processed,
            'total_keys_found': self.total_keys_found,
            'total_valid_keys': self.total_valid_keys,
            'total_errors': len(self.errors),
            'scan_start_time': self.scan_start_time,
            'scan_end_time': self.scan_end_time,
            'success_rate': (self.total_files_processed / (self.total_files_processed + len(self.errors))) if (self.total_files_processed + len(self.errors)) > 0 else 0
        }