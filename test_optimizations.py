#!/usr/bin/env python3
"""
Test script to verify the optimizations made to APIKEY-king system.
This script tests the new logging and file saving mechanisms.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_logger_enhancements():
    """Test the new logger methods."""
    print("🧪 Testing Logger Enhancements...")
    
    try:
        from src.utils.logger import Logger
        
        logger = Logger()
        
        # Test new logging methods
        logger.key_extracted("siliconflow", 3, "user/repo", "config.py")
        logger.key_validating("sk-abcd1234", "siliconflow")
        logger.key_validation_success("sk-abcd1234", "siliconflow")
        logger.key_validation_failed("sk-efgh5678", "siliconflow", "401 Unauthorized")
        logger.key_saved_immediately("sk-abcd1234", "data/keys/keys_valid_siliconflow_20250915.txt")
        logger.progress_summary(10, 8, 5)
        
        output_files = {
            "有效密钥文件 Valid keys file": "data/keys/keys_valid_siliconflow_20250915.txt",
            "详细日志文件 Detail log file": "data/logs/keys_valid_detail_siliconflow_20250915.log",
            "限流密钥文件 Rate-limited keys file": "data/keys/key_429_siliconflow_20250915.txt"
        }
        logger.output_files_info("siliconflow", output_files)
        logger.key_rejection_reason("sk-invalid", "siliconflow", "placeholder detected")
        
        print("✅ Logger enhancements working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Logger test failed: {e}")
        return False

def test_file_service_enhancements():
    """Test the new file service methods."""
    print("🧪 Testing File Service Enhancements...")
    
    try:
        from src.services.file_service import FileService
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            file_service = FileService(temp_dir)
            
            # Test get_output_file_paths
            output_files = file_service.get_output_file_paths("siliconflow")
            expected_keys = [
                "有效密钥文件 Valid keys file",
                "详细日志文件 Detail log file", 
                "限流密钥文件 Rate-limited keys file"
            ]
            
            for key in expected_keys:
                if key not in output_files:
                    raise ValueError(f"Missing expected key: {key}")
                if "siliconflow" not in output_files[key]:
                    raise ValueError(f"Mode not in filename: {output_files[key]}")
            
            # Test immediate key saving
            test_key = "sk-abcd1234567890abcd1234567890abcd1234567890"
            validation_result = {'is_valid': True, 'status': 'valid'}
            
            saved_file = file_service.save_key_immediately(
                test_key, "siliconflow", "user/repo", "config.py", 
                "https://github.com/user/repo/blob/main/config.py", 
                validation_result
            )
            
            if not saved_file:
                raise ValueError("save_key_immediately returned None for valid key")
            
            # Check if file was created and contains the key
            if not Path(saved_file).exists():
                raise ValueError(f"Key file was not created: {saved_file}")
            
            with open(saved_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if test_key not in content:
                    raise ValueError("Key was not written to file")
            
            print("✅ File service enhancements working correctly!")
            return True
            
    except Exception as e:
        print(f"❌ File service test failed: {e}")
        return False

def test_key_type_detection():
    """Test the key type detection logic."""
    print("🧪 Testing Key Type Detection...")
    
    try:
        # We'll test this by importing and creating a minimal Application instance
        from src.main import Application
        from src.core import ScanMode
        
        app = Application(ScanMode.COMPATIBLE)
        
        # Test key type detection
        test_cases = [
            ("AIzaSyABC123DEF456GHI789JKL012MNO345PQR", "gemini"),
            ("sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef", "openrouter"),
            ("ms-12345678-1234-1234-1234-123456789012", "modelscope"),
            ("sk-abcd1234567890abcd1234567890abcd1234567890", "siliconflow"),
            ("invalid-key-format", "unknown")
        ]
        
        for key, expected_type in test_cases:
            detected_type = app._determine_key_type(key)
            if detected_type != expected_type:
                raise ValueError(f"Key type detection failed: {key} -> {detected_type}, expected {expected_type}")
        
        print("✅ Key type detection working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Key type detection test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting APIKEY-king Optimization Tests...")
    print("=" * 60)
    
    tests = [
        test_logger_enhancements,
        test_file_service_enhancements,
        test_key_type_detection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All optimizations are working correctly!")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
