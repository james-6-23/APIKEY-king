#!/usr/bin/env python3
"""
Demo script to showcase the optimized APIKEY-king system.
This script demonstrates the new real-time logging and file saving features.
"""

import sys
import os
import time
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def demo_startup_info():
    """Demonstrate the enhanced startup information."""
    print("🎯 Demo: Enhanced Startup Information")
    print("=" * 50)
    
    try:
        from src.utils.logger import Logger
        from src.services.file_service import FileService
        
        logger = Logger()
        
        # Simulate startup banner
        logger.startup_banner()
        logger.github_tokens(3)
        logger.info("📅 日期过滤 Date filter: 730 天 days")
        logger.info("🌐 代理配置 Proxies: 2 个已配置 configured")
        
        # Show mode activation
        logger.mode_activated("siliconflow", validation=True)
        
        # Show output file paths
        file_service = FileService("./data")
        output_files = file_service.get_output_file_paths("siliconflow")
        logger.output_files_info("siliconflow", output_files)
        
        logger.info("💾 完整扫描模式 Full scan mode")
        logger.success("系统就绪 System ready - 开始扫描 Starting scan")
        
        print("\n✅ Enhanced startup information displayed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def demo_real_time_key_processing():
    """Demonstrate real-time key extraction, validation, and saving."""
    print("\n🎯 Demo: Real-time Key Processing")
    print("=" * 50)
    
    try:
        from src.utils.logger import Logger
        from src.services.file_service import FileService
        import tempfile
        
        logger = Logger()
        
        # Create temporary file service for demo
        with tempfile.TemporaryDirectory() as temp_dir:
            file_service = FileService(temp_dir)
            
            # Simulate processing a file with keys
            repo_name = "user/awesome-project"
            file_path = "src/config.py"
            file_url = "https://github.com/user/awesome-project/blob/main/src/config.py"
            
            print("📁 Processing file: user/awesome-project/src/config.py")
            time.sleep(0.5)
            
            # Simulate key extraction
            logger.key_extracted("siliconflow", 2, repo_name, file_path)
            time.sleep(0.3)
            
            # Simulate validation process for first key
            test_key1 = "sk-abcd1234567890abcd1234567890abcd1234567890"
            key_prefix1 = "sk-abcd1234"
            
            logger.key_validating(key_prefix1, "siliconflow")
            time.sleep(0.8)  # Simulate API call time
            logger.key_validation_success(key_prefix1, "siliconflow")
            
            # Save immediately
            saved_file = file_service.save_key_immediately(
                test_key1, "siliconflow", repo_name, file_path, file_url,
                {'is_valid': True, 'status': 'valid'}
            )
            logger.key_saved_immediately(key_prefix1, saved_file)
            time.sleep(0.2)
            
            # Simulate validation process for second key
            test_key2 = "sk-efgh5678901234efgh5678901234efgh5678901234"
            key_prefix2 = "sk-efgh5678"
            
            logger.key_validating(key_prefix2, "siliconflow")
            time.sleep(0.6)  # Simulate API call time
            logger.key_validation_failed(key_prefix2, "siliconflow", "401 Unauthorized")
            time.sleep(0.2)
            
            # Show progress summary
            logger.progress_summary(15, 12, 8)
            
            print("\n✅ Real-time key processing demonstrated!")
            print(f"📄 Valid key saved to: {saved_file}")
            
            # Show file contents
            if os.path.exists(saved_file):
                with open(saved_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    print(f"📝 File contents: {content}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def demo_progress_tracking():
    """Demonstrate enhanced progress tracking."""
    print("\n🎯 Demo: Enhanced Progress Tracking")
    print("=" * 50)
    
    try:
        from src.utils.logger import Logger
        
        logger = Logger()
        
        # Simulate processing multiple files
        for i in range(1, 6):
            print(f"\n📁 Processing query #{i}/5...")
            
            # Simulate finding keys
            if i % 2 == 1:  # Odd queries find keys
                logger.key_extracted("siliconflow", i, f"repo{i}/project", "config.py")
                time.sleep(0.2)
                
                # Simulate validation
                for j in range(i):
                    key_prefix = f"sk-key{i}{j}"
                    logger.key_validating(key_prefix, "siliconflow")
                    time.sleep(0.1)
                    
                    if j % 2 == 0:  # Even keys are valid
                        logger.key_validation_success(key_prefix, "siliconflow")
                        logger.key_saved_immediately(key_prefix, f"data/keys/keys_valid_siliconflow_20250915.txt")
                    else:
                        logger.key_validation_failed(key_prefix, "siliconflow", "Invalid format")
                    
                    time.sleep(0.1)
            
            # Show progress every few queries
            if i % 2 == 0:
                extracted = i * 2
                validated = i * 2
                valid = i
                logger.progress_summary(extracted, validated, valid)
            
            time.sleep(0.3)
        
        print("\n✅ Enhanced progress tracking demonstrated!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def demo_interrupt_handling():
    """Demonstrate enhanced interrupt handling."""
    print("\n🎯 Demo: Enhanced Interrupt Handling")
    print("=" * 50)
    
    try:
        from src.utils.logger import Logger
        from src.services.file_service import FileService
        from pathlib import Path
        import tempfile
        
        logger = Logger()
        
        print("🔄 Simulating user interrupt (Ctrl+C)...")
        time.sleep(0.5)
        
        logger.info("⛔ 用户中断 Interrupted by user")
        logger.info("💾 已保存当前批次结果 Saved current batch results")
        
        # Show final file locations
        logger.separator("📁 密钥文件位置 Key File Locations")
        
        # Simulate file existence check
        sample_files = {
            "有效密钥文件 Valid keys file": "data/keys/keys_valid_siliconflow_20250915.txt",
            "详细日志文件 Detail log file": "data/logs/keys_valid_detail_siliconflow_20250915.log",
            "限流密钥文件 Rate-limited keys file": "data/keys/key_429_siliconflow_20250915.txt"
        }
        
        for file_type, file_path in sample_files.items():
            if "valid" in file_path:  # Simulate that valid keys file exists
                logger.info(f"💾 {file_type}: {file_path} (5 keys)")
            else:
                logger.info(f"📄 {file_type}: {file_path} (not created)")
        
        logger.info("📊 最终统计 Final stats - 总共发现有效密钥 Total valid keys found: 5")
        
        print("\n✅ Enhanced interrupt handling demonstrated!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def main():
    """Run all demonstrations."""
    print("🚀 APIKEY-king Optimization Demonstrations")
    print("=" * 60)
    print("This demo showcases the new real-time logging and file saving features.")
    print()
    
    demos = [
        demo_startup_info,
        demo_real_time_key_processing,
        demo_progress_tracking,
        demo_interrupt_handling
    ]
    
    for demo in demos:
        try:
            demo()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n⛔ Demo interrupted by user")
            break
        except Exception as e:
            print(f"❌ Demo failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 All demonstrations completed!")
    print("\n📋 Key Improvements Demonstrated:")
    print("   ✅ Real-time key extraction logging")
    print("   ✅ Immediate validation status display")
    print("   ✅ Instant file saving (no data loss on interrupt)")
    print("   ✅ Enhanced startup information with file paths")
    print("   ✅ Detailed progress summaries")
    print("   ✅ Improved interrupt handling with file location display")
    print("   ✅ Mode-specific file naming (siliconflow, gemini, etc.)")

if __name__ == "__main__":
    main()
