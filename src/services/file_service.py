"""
File service for managing data persistence and file operations.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

from ..models import Checkpoint, ScanResult, BatchScanResult


class FileService:
    """Service for file operations and data persistence."""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.checkpoint_file = self.data_path / "checkpoint.json"
        self.scanned_shas_file = self.data_path / "scanned_shas.txt"
        
        # Ensure data directory exists
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.data_path / "keys").mkdir(exist_ok=True)
        (self.data_path / "logs").mkdir(exist_ok=True)
    
    def load_checkpoint(self) -> Checkpoint:
        """Load checkpoint from file."""
        checkpoint = Checkpoint()
        
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    checkpoint = Checkpoint.from_dict(data)
            except Exception as e:
                print(f"Warning: Could not load checkpoint: {e}")
        
        # Load scanned SHAs separately
        checkpoint.scanned_shas = self.load_scanned_shas()
        
        return checkpoint
    
    def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint to file."""
        try:
            # Save scanned SHAs separately
            self.save_scanned_shas(checkpoint.scanned_shas)
            
            # Save checkpoint data
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving checkpoint: {e}")
    
    def load_scanned_shas(self) -> Set[str]:
        """Load scanned SHAs from file."""
        scanned_shas = set()
        
        if self.scanned_shas_file.exists():
            try:
                with open(self.scanned_shas_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            scanned_shas.add(line)
            except Exception as e:
                print(f"Error loading scanned SHAs: {e}")
        
        return scanned_shas
    
    def save_scanned_shas(self, scanned_shas: Set[str]) -> None:
        """Save scanned SHAs to file."""
        try:
            with open(self.scanned_shas_file, 'w', encoding='utf-8') as f:
                f.write("# Scanned file SHAs\n")
                f.write("# One SHA per line\n")
                f.write(f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n")
                for sha in sorted(scanned_shas):
                    f.write(f"{sha}\n")
        except Exception as e:
            print(f"Error saving scanned SHAs: {e}")
    
    def load_queries(self, queries_file: str) -> List[str]:
        """Load search queries from file."""
        queries = []

        # Handle both absolute and relative paths
        if queries_file.startswith('config/') or queries_file.startswith('./config/'):
            # Config directory path - use as is
            queries_path = Path(queries_file)
        else:
            # Legacy path - use data_path
            queries_path = self.data_path / queries_file

        if not queries_path.exists():
            self._create_default_queries_file(queries_path)

        try:
            with open(queries_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        queries.append(line)
        except Exception as e:
            print(f"Error loading queries: {e}")

        return queries
    
    def save_scan_result(self, result: ScanResult) -> None:
        """Save a single scan result."""
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # Save valid keys
        valid_keys = result.get_valid_keys()
        if valid_keys:
            valid_keys_file = self.data_path / "keys" / f"keys_valid_{timestamp}.txt"
            self._append_keys_to_file(valid_keys_file, valid_keys)
            
            # Save detailed log
            detail_log_file = self.data_path / "logs" / f"keys_valid_detail_{timestamp}.log"
            self._append_detailed_log(detail_log_file, result)
        
        # Save rate-limited keys (if any)
        rate_limited_keys = self._get_rate_limited_keys(result)
        if rate_limited_keys:
            rate_limited_file = self.data_path / "keys" / f"key_429_{timestamp}.txt"
            self._append_keys_to_file(rate_limited_file, rate_limited_keys)
    
    def save_batch_result(self, batch_result: BatchScanResult) -> None:
        """Save batch scan results."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save summary
        summary_file = self.data_path / "logs" / f"batch_summary_{timestamp}.json"
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(batch_result.get_summary(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving batch summary: {e}")

        # Save individual results
        for result in batch_result.results:
            self.save_scan_result(result)

    def save_key_immediately(self, key: str, key_type: str, repo_name: str, file_path: str, file_url: str, validation_result: Dict[str, Any]) -> Optional[str]:
        """Save a single key immediately after validation."""
        timestamp = datetime.now().strftime('%Y%m%d')

        # Determine file names based on key type and mode
        if validation_result.get('is_valid', False):
            # Save to valid keys file
            valid_keys_file = self.data_path / "keys" / f"keys_valid_{key_type}_{timestamp}.txt"
            self._append_single_key_to_file(valid_keys_file, key)

            # Save to detailed log immediately
            detail_log_file = self.data_path / "logs" / f"keys_valid_detail_{key_type}_{timestamp}.log"
            self._append_single_key_log(detail_log_file, key, repo_name, file_path, file_url, validation_result)

            return str(valid_keys_file)

        elif validation_result.get('status') == 'rate_limited':
            # Save to rate-limited file
            rate_limited_file = self.data_path / "keys" / f"key_429_{key_type}_{timestamp}.txt"
            self._append_single_key_to_file(rate_limited_file, key)
            return str(rate_limited_file)

        return None

    def get_output_file_paths(self, mode: str) -> Dict[str, str]:
        """Get output file paths for current mode and date."""
        timestamp = datetime.now().strftime('%Y%m%d')

        return {
            "有效密钥文件 Valid keys file": str(self.data_path / "keys" / f"keys_valid_{mode}_{timestamp}.txt"),
            "详细日志文件 Detail log file": str(self.data_path / "logs" / f"keys_valid_detail_{mode}_{timestamp}.log"),
            "限流密钥文件 Rate-limited keys file": str(self.data_path / "keys" / f"key_429_{mode}_{timestamp}.txt")
        }
    
    def _create_default_queries_file(self, queries_path: Path) -> None:
        """Create default queries file."""
        try:
            # Ensure parent directory exists
            queries_path.parent.mkdir(parents=True, exist_ok=True)

            with open(queries_path, 'w', encoding='utf-8') as f:
                f.write("# GitHub search queries\n")
                f.write("# One query per line\n")
                f.write("# Lines starting with # are comments\n")
                f.write("\n")
                f.write("# Basic API key searches\n")
                f.write("AIzaSy in:file\n")
                f.write("AIzaSy in:file filename:.env\n")
                f.write("\n")
                f.write("# ModelScope API searches\n")
                f.write('"https://api-inference.modelscope.cn/v1/" in:file\n')
                f.write("api-inference.modelscope.cn in:file\n")
                f.write("\n")
                f.write("# SiliconFlow API searches\n")
                f.write('"https://api.siliconflow.cn/v1" in:file\n')
                f.write('"sk-" AND "siliconflow" in:file\n')
        except Exception as e:
            print(f"Error creating default queries file: {e}")
    
    def _append_keys_to_file(self, file_path: Path, keys: Set[str]) -> None:
        """Append keys to file."""
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                for key in sorted(keys):
                    f.write(f"{key}\n")
        except Exception as e:
            print(f"Error appending keys to {file_path}: {e}")
    
    def _append_detailed_log(self, file_path: Path, result: ScanResult) -> None:
        """Append detailed log entry."""
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"TIME: {result.timestamp}\n")
                f.write(f"URL: {result.file_url}\n")
                f.write(f"REPO: {result.repository_name}\n")
                f.write(f"PATH: {result.file_path}\n")
                
                for extractor, keys in result.extracted_keys.items():
                    f.write(f"EXTRACTOR: {extractor}\n")
                    for key in keys:
                        validation = result.validation_results.get(key, {})
                        status = "VALID" if validation.get('is_valid', False) else "INVALID"
                        f.write(f"KEY ({status}): {key}\n")
                
                f.write("-" * 80 + "\n")
        except Exception as e:
            print(f"Error appending detailed log: {e}")
    
    def _get_rate_limited_keys(self, result: ScanResult) -> Set[str]:
        """Get keys that were rate-limited during validation."""
        rate_limited = set()
        for key, validation in result.validation_results.items():
            if validation.get('status') == 'rate_limited':
                rate_limited.add(key)
        return rate_limited

    def _append_single_key_to_file(self, file_path: Path, key: str) -> None:
        """Append a single key to file immediately."""
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"{key}\n")
                f.flush()  # Ensure immediate write to disk
        except Exception as e:
            print(f"Error appending key to {file_path}: {e}")

    def _append_single_key_log(self, file_path: Path, key: str, repo_name: str, file_path_src: str, file_url: str, validation_result: Dict[str, Any]) -> None:
        """Append detailed log for a single key immediately."""
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"TIME: {datetime.now().isoformat()}\n")
                f.write(f"URL: {file_url}\n")
                f.write(f"REPO: {repo_name}\n")
                f.write(f"PATH: {file_path_src}\n")
                status = "VALID" if validation_result.get('is_valid', False) else "INVALID"
                f.write(f"KEY ({status}): {key}\n")
                if validation_result.get('error_message'):
                    f.write(f"ERROR: {validation_result['error_message']}\n")
                f.write("-" * 80 + "\n")
                f.flush()  # Ensure immediate write to disk
        except Exception as e:
            print(f"Error appending detailed log: {e}")
    
    def get_output_files(self) -> Dict[str, List[str]]:
        """Get list of output files by category."""
        files = {
            'valid_keys': [],
            'rate_limited': [],
            'logs': [],
            'summaries': []
        }
        
        keys_dir = self.data_path / "keys"
        logs_dir = self.data_path / "logs"
        
        if keys_dir.exists():
            files['valid_keys'] = [str(f) for f in keys_dir.glob("keys_valid_*.txt")]
            files['rate_limited'] = [str(f) for f in keys_dir.glob("key_429_*.txt")]
        
        if logs_dir.exists():
            files['logs'] = [str(f) for f in logs_dir.glob("*.log")]
            files['summaries'] = [str(f) for f in logs_dir.glob("batch_summary_*.json")]
        
        return files