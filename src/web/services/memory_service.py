"""
Scan memory service.
"""

from typing import Dict
from ..database.database import db


def get_log_service():
    """Get log service instance (lazy loading)."""
    from .log_service import LogService
    return LogService()


class MemoryService:
    """Scan memory management service."""
    
    def get_stats(self) -> Dict:
        """Get scan memory statistics."""
        return db.get_scan_memory_stats()
    
    def clear_memory(self):
        """Clear all scan memory."""
        db.clear_scan_memory()
        
        log_svc = get_log_service()
        log_svc.add_log("warning", "Scan memory cleared", {
            "cleared": ["processed_queries", "scanned_files"]
        })
    
    def is_query_processed(self, query: str) -> bool:
        """Check if query has been processed."""
        return db.is_query_processed(query)
    
    def is_sha_scanned(self, sha: str) -> bool:
        """Check if SHA has been scanned."""
        return db.is_sha_scanned(sha)
    
    def add_processed_query(self, query: str):
        """Add processed query to memory."""
        db.add_processed_query(query)
    
    def add_scanned_sha(self, sha: str, file_path: str = None, repository: str = None):
        """Add scanned SHA to memory."""
        db.add_scanned_sha(sha, file_path, repository)

