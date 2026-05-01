"""
Main application entry point for APIKEY-king.
"""

import argparse
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

from .core import ScanMode, APIKeyScanner
from .services import ConfigService, GitHubService, FileService
from .extractors import ModelScopeExtractor
from .validators import ModelScopeValidator
from .models import Checkpoint, ScanResult, BatchScanResult
from .utils import logger


class Application:
    """Main application class."""
    
    def __init__(self, scan_mode: ScanMode = ScanMode.COMPATIBLE):
        self.config_service = ConfigService()
        self.config = None
        self.github_service = None
        self.file_service = None
        self.scanner = None
        self.checkpoint = None
        self.scan_mode = scan_mode
        
        # Statistics
        self.skip_stats = {
            "time_filter": 0,
            "sha_duplicate": 0,
            "age_filter": 0,
            "doc_filter": 0
        }

        # Running statistics for real-time progress
        self.running_stats = {"extracted": 0, "validated": 0, "valid": 0}
        self.last_progress_time = 0
    
    def initialize(self) -> bool:
        """Initialize application components."""
        try:
            # Load configuration
            self.config = self.config_service.load_config()
            
            # Apply scan mode overrides
            self._apply_scan_mode_config()
            
            logger.init_success("配置 Configuration")
            
            # Initialize services
            self.github_service = GitHubService(self.config)
            self.file_service = FileService(self.config.data_path)
            logger.init_success("服务 Services")
            
            # Create extractors based on configuration
            extractors = self._create_extractors()
            validators = self._create_validators()
            
            # Create scanner
            self.scanner = APIKeyScanner(extractors, validators)
            logger.scan_mode_summary(extractors, validators)
            
            # Load checkpoint
            self.checkpoint = self.file_service.load_checkpoint()
            logger.init_success("检查点 Checkpoint")
            
            return True
            
        except Exception as e:
            logger.error(f"初始化失败 Failed to initialize application: {e}")
            return False
    
    def _apply_scan_mode_config(self) -> None:
        """Apply scan mode specific configuration overrides."""
        if self.scan_mode == ScanMode.MODELSCOPE_ONLY:
            # Enable only ModelScope extractor
            for name, extractor_config in self.config.extractors.items():
                if name == 'modelscope':
                    extractor_config.enabled = True
                    extractor_config.extract_only = False  # Enable validation for ModelScope
                else:
                    extractor_config.enabled = False

            # Enable only ModelScope validator
            for name, validator_config in self.config.validators.items():
                if name == 'modelscope':
                    validator_config.enabled = True
                else:
                    validator_config.enabled = False

            # Use ModelScope queries
            self.config.scan.queries_file = "config/queries/modelscope.txt"
            logger.mode_activated("ModelScope", True)

        elif self.scan_mode == ScanMode.SILICONFLOW_ONLY:
            # Enable only SiliconFlow extractor
            for name, extractor_config in self.config.extractors.items():
                if name == 'siliconflow':
                    extractor_config.enabled = True
                    extractor_config.extract_only = False  # Enable validation
                else:
                    extractor_config.enabled = False

            # Enable only SiliconFlow validator
            for name, validator_config in self.config.validators.items():
                if name == 'siliconflow':
                    validator_config.enabled = True
                else:
                    validator_config.enabled = False

            # Use SiliconFlow queries
            self.config.scan.queries_file = "config/queries/siliconflow.txt"
            logger.mode_activated("SiliconFlow", True)

        elif self.scan_mode == ScanMode.DEEPSEEK_ONLY:
            # Enable only DeepSeek extractor
            for name, extractor_config in self.config.extractors.items():
                if name == 'deepseek':
                    extractor_config.enabled = True
                    extractor_config.extract_only = False
                else:
                    extractor_config.enabled = False

            # Enable only DeepSeek validator
            for name, validator_config in self.config.validators.items():
                if name == 'deepseek':
                    validator_config.enabled = True
                else:
                    validator_config.enabled = False

            # Use DeepSeek queries
            self.config.scan.queries_file = "config/queries/deepseek.txt"
            logger.mode_activated("DeepSeek", True)

        elif self.scan_mode == ScanMode.COMPATIBLE:
            # Enable all extractors with validation where supported
            for name, extractor_config in self.config.extractors.items():
                if name in ['modelscope', 'siliconflow', 'deepseek']:
                    extractor_config.extract_only = False

            # Enable all validators
            for name, validator_config in self.config.validators.items():
                validator_config.enabled = True

            logger.mode_activated("兼容 Compatible", True)
    
    def _create_extractors(self) -> List:
        """Create extractor instances based on configuration."""
        extractors = []
        
        enabled_extractors = self.config.get_enabled_extractors()
        
        for name, config in enabled_extractors.items():
            try:
                if name == 'modelscope':
                    extractor = ModelScopeExtractor(config)
                elif name == 'siliconflow':
                    from .extractors.siliconflow import SiliconFlowExtractor
                    extractor = SiliconFlowExtractor(config)
                elif name == 'deepseek':
                    from .extractors.deepseek import DeepSeekExtractor
                    extractor = DeepSeekExtractor(config)
                else:
                    logger.warning(f"Unknown extractor type: {name}")
                    continue

                extractors.append(extractor)
                logger.init_success(f"{name} 提取器 extractor")

            except Exception as e:
                logger.error(f"Failed to create {name} extractor: {e}")

        return extractors

    def _create_validators(self) -> List:
        """Create validator instances based on configuration."""
        validators = []

        enabled_validators = self.config.get_enabled_validators()

        for name, config in enabled_validators.items():
            try:
                if name == 'modelscope':
                    validator = ModelScopeValidator(config)
                    validators.append(validator)
                    logger.init_success(f"{name} 验证器 validator")
                elif name == 'siliconflow':
                    from .validators.siliconflow import SiliconFlowValidator
                    validator = SiliconFlowValidator(config)
                    validators.append(validator)
                    logger.init_success(f"{name} 验证器 validator")
                elif name == 'deepseek':
                    from .validators.deepseek import DeepSeekValidator
                    validator = DeepSeekValidator(config)
                    validators.append(validator)
                    logger.init_success(f"{name} 验证器 validator")
                else:
                    logger.warning(f"Unknown validator type: {name}")

            except Exception as e:
                logger.error(f"Failed to create {name} validator: {e}")

        return validators
    
    def run(self) -> None:
        """Run the main scanning loop."""
        if not self.initialize():
            logger.error("初始化失败 Failed to initialize application")
            sys.exit(1)
        
        # Print startup information
        self._print_startup_info()
        
        # Load queries
        queries = self.file_service.load_queries(self.config.scan.queries_file)
        if not queries:
            logger.error("未加载查询 No queries loaded - check queries file")
            sys.exit(1)
        
        logger.info(f"🔍 已加载 Loaded {len(queries)} 个查询 queries")
        
        # Main scanning loop
        total_valid_keys = 0
        loop_count = 0
        
        try:
            while True:
                loop_count += 1
                logger.separator(f"🔄 第 #{loop_count} 轮 LOOP - {datetime.now().strftime('%H:%M:%S')}")
                
                batch_result = BatchScanResult()
                self._reset_skip_stats()
                
                for i, query in enumerate(queries, 1):
                    normalized_query = self._normalize_query(query)
                    
                    # Skip if already processed
                    if normalized_query in self.checkpoint.processed_queries:
                        logger.info(f"⏭️ 跳过已处理查询 Skipping processed query #{i}: {query[:50]}...")
                        continue
                    
                    logger.info(f"🔍 处理查询 Processing query #{i}/{len(queries)}: {query}")
                    
                    # Search GitHub
                    search_results = self.github_service.search_code(query)
                    items = search_results.get('items', [])
                    
                    if not items:
                        logger.info(f"📭 未找到条目 No items found for query #{i}")
                        self.checkpoint.add_processed_query(normalized_query)
                        continue
                    
                    # Process items
                    for item_idx, item in enumerate(items, 1):
                        try:
                            if self._should_skip_item(item):
                                continue
                            
                            # Get file content
                            content = self.github_service.get_file_content(item)
                            if not content:
                                continue
                            
                            # Scan content
                            scan_results = self._scan_item(item, content)
                            if scan_results:
                                batch_result.add_result(scan_results)
                                total_valid_keys += len(scan_results.get_valid_keys())
                            
                            # Update checkpoint
                            self.checkpoint.add_scanned_sha(item.get("sha"))
                            
                            # Progress update every 20 items
                            if item_idx % 20 == 0:
                                logger.progress(f"Query {i} progress", item_idx, len(items))
                                self._save_checkpoint()
                        
                        except Exception as e:
                            logger.error(f"处理条目错误 Error processing item {item_idx}: {e}")
                            batch_result.add_error({
                                'item_index': item_idx,
                                'error': str(e),
                                'item_url': item.get('html_url', 'unknown')
                            })
                    
                    # Mark query as processed
                    self.checkpoint.add_processed_query(normalized_query)
                    self._save_checkpoint()
                    
                    logger.info(f"✅ 查询 #{i} 完成 Query complete - 发现 Found {len([r for r in batch_result.results if r.get_all_keys()])} 个文件包含密钥 files with keys")
                    self._print_skip_stats()
                
                # Save batch results
                batch_result.finalize()
                self.file_service.save_batch_result(batch_result)
                
                logger.separator(f"🏁 第 #{loop_count} 轮完成 LOOP COMPLETE")
                logger.success(f"已处理 Processed {batch_result.total_files_processed} 个文件 files")
                logger.success(f"发现 Found {batch_result.total_keys_found} 个密钥 total keys")  
                logger.success(f"验证 Validated {batch_result.total_valid_keys} 个有效密钥 valid keys")
                logger.info(f"累计有效密钥 Total valid keys so far: {total_valid_keys}")
                
                # Sleep between loops
                logger.info("💤 休眠 10 秒等待下一轮 Sleeping 10 seconds before next loop...")
                time.sleep(10)
        
        except KeyboardInterrupt:
            logger.info("⛔ 用户中断 Interrupted by user")

            # Save current batch results if any
            if 'batch_result' in locals() and batch_result.results:
                batch_result.finalize()
                self.file_service.save_batch_result(batch_result)
                logger.info(f"💾 已保存当前批次结果 Saved current batch results")

            # Display final file locations
            mode_name = self.scan_mode.value if hasattr(self.scan_mode, 'value') else str(self.scan_mode)
            output_files = self.file_service.get_output_file_paths(mode_name)
            logger.separator("📁 密钥文件位置 Key File Locations")

            from pathlib import Path
            for file_type, file_path in output_files.items():
                if Path(file_path).exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            key_count = sum(1 for line in f if line.strip())
                        logger.info(f"💾 {file_type}: {file_path} ({key_count} keys)")
                    except Exception:
                        logger.info(f"💾 {file_type}: {file_path} (file exists)")
                else:
                    logger.info(f"📄 {file_type}: {file_path} (not created)")

            self._save_checkpoint()
            logger.info(f"📊 最终统计 Final stats - 总共发现有效密钥 Total valid keys found: {total_valid_keys}")
    
    def _scan_item(self, item: Dict[str, Any], content: str) -> ScanResult:
        """Scan a single item with enhanced logging and immediate file saving."""
        context = {
            'file_path': item.get('path', ''),
            'repository': item.get('repository', {}),
            'proxy_config': None  # Could add proxy config here
        }

        repo_name = item.get('repository', {}).get('full_name', '')
        file_path = item.get('path', '')
        file_url = item.get('html_url', '')

        # Use scanner to process content
        scan_results = self.scanner.scan_content(content, context)

        if not scan_results['summary']['total_keys_found']:
            return None

        # Log extraction results immediately
        for extractor_name, extraction_result in scan_results['extracted_keys'].items():
            if extraction_result.keys:
                logger.key_extracted(extractor_name, len(extraction_result.keys), repo_name, file_path)

        # Process validation results with immediate logging and saving
        total_extracted = scan_results['summary']['total_keys_found']
        total_valid = 0

        for key, validation_result in scan_results['validation_results'].items():
            # Determine key type from key format
            key_type = self._determine_key_type(key)
            key_prefix = key[:12] + "..." if len(key) > 12 else key

            # Log validation start
            logger.key_validating(key_prefix, key_type)

            # Log validation result and save immediately
            if validation_result.is_valid:
                logger.key_validation_success(key_prefix, key_type)
                saved_file = self.file_service.save_key_immediately(
                    key, key_type, repo_name, file_path, file_url,
                    {'is_valid': True, 'status': 'valid'}
                )
                if saved_file:
                    logger.key_saved_immediately(key_prefix, saved_file)
                total_valid += 1
            else:
                reason = validation_result.error_message or validation_result.status or "Unknown"
                logger.key_validation_failed(key_prefix, key_type, reason)

                # Save rate-limited keys immediately
                if validation_result.status == 'rate_limited':
                    saved_file = self.file_service.save_key_immediately(
                        key, key_type, repo_name, file_path, file_url,
                        {'is_valid': False, 'status': 'rate_limited'}
                    )
                    if saved_file:
                        logger.key_saved_immediately(key_prefix, saved_file)

        # Update running totals and log progress
        self.running_stats['extracted'] += total_extracted
        self.running_stats['validated'] += len(scan_results['validation_results'])
        self.running_stats['valid'] += total_valid

        # Log progress summary every 10 keys or every 2 minutes
        import time
        if (self.running_stats['extracted'] % 10 == 0 or
            time.time() - self.last_progress_time > 120):
            logger.progress_summary(
                self.running_stats['extracted'],
                self.running_stats['validated'],
                self.running_stats['valid']
            )
            self.last_progress_time = time.time()

        # Create ScanResult object (for compatibility)
        result = ScanResult(
            file_url=file_url,
            repository_name=repo_name,
            file_path=file_path,
            extracted_keys={},
            validation_results={},
            scan_metadata=scan_results['summary']
        )

        # Process extraction results
        for extractor_name, extraction_result in scan_results['extracted_keys'].items():
            result.extracted_keys[extractor_name] = extraction_result.keys

        # Process validation results
        for key, validation_result in scan_results['validation_results'].items():
            result.validation_results[key] = {
                'is_valid': validation_result.is_valid,
                'status': validation_result.status,
                'error_message': validation_result.error_message,
                'metadata': validation_result.metadata
            }

        return result

    def _determine_key_type(self, key: str) -> str:
        """Determine key type from key format."""
        import re
        if key.startswith('ms-'):
            return 'modelscope'
        elif re.match(r'^sk-[a-f0-9]{32}$', key, re.IGNORECASE):
            return 'deepseek'
        elif key.startswith('sk-'):
            return 'siliconflow'
        else:
            return 'unknown'

    def _should_skip_item(self, item: Dict[str, Any]) -> bool:
        """Check if item should be skipped."""
        # Check if SHA already processed
        if item.get("sha") in self.checkpoint.scanned_shas:
            self.skip_stats["sha_duplicate"] += 1
            return True
        
        # Check file path blacklist
        file_path = item.get("path", "").lower()
        if any(blocked in file_path for blocked in self.config.scan.file_path_blacklist):
            self.skip_stats["doc_filter"] += 1
            return True
        
        return False
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query string for consistency."""
        return " ".join(query.split())
    
    def _save_checkpoint(self) -> None:
        """Save current checkpoint."""
        self.checkpoint.update_scan_time()
        self.file_service.save_checkpoint(self.checkpoint)
    
    def _reset_skip_stats(self) -> None:
        """Reset skip statistics."""
        self.skip_stats = {"time_filter": 0, "sha_duplicate": 0, "age_filter": 0, "doc_filter": 0}
    
    def _print_skip_stats(self) -> None:
        """Print skip statistics."""
        total_skipped = sum(self.skip_stats.values())
        if total_skipped > 0:
            logger.info(f"📊 已跳过 Skipped {total_skipped} 个条目 items - " + 
                       f"重复 Duplicate: {self.skip_stats['sha_duplicate']}, " +
                       f"文档 Docs: {self.skip_stats['doc_filter']}")
    
    def _print_startup_info(self) -> None:
        """Print enhanced startup information."""
        logger.startup_banner()
        logger.github_tokens(len(self.config.github.tokens))
        logger.info(f"📅 日期过滤 Date filter: {self.config.scan.date_range_days} 天 days")

        if self.config.get_proxy_configs():
            logger.info(f"🌐 代理配置 Proxies: {len(self.config.get_proxy_configs())} 个已配置 configured")

        # Display current scan mode
        mode_name = self.scan_mode.value if hasattr(self.scan_mode, 'value') else str(self.scan_mode)
        logger.mode_activated(mode_name, validation=True)

        # Display output file paths
        output_files = self.file_service.get_output_file_paths(mode_name)
        logger.output_files_info(mode_name, output_files)

        if self.checkpoint.last_scan_time:
            logger.info(f"💾 增量扫描模式 Incremental scan mode - 上次扫描 Last scan: {self.checkpoint.last_scan_time}")
            logger.info(f"📁 已扫描文件 Already scanned: {len(self.checkpoint.scanned_shas)} 个文件 files")
        else:
            logger.info("💾 完整扫描模式 Full scan mode")

        logger.success("系统就绪 System ready - 开始扫描 Starting scan")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="APIKEY-king - API Key Discovery Tool")
    parser.add_argument(
        "--mode",
        choices=["modelscope-only", "siliconflow-only", "deepseek-only", "compatible"],
        default="compatible",
        help="Scanning mode: modelscope-only, siliconflow-only, deepseek-only, or compatible (all types)"
    )
    parser.add_argument(
        "--config-preset",
        help="Load configuration preset from config/presets/ directory"
    )
    parser.add_argument(
        "--queries",
        help="Override queries file path"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Determine scan mode
    scan_mode = ScanMode.COMPATIBLE
    if args.mode:
        scan_mode = ScanMode(args.mode)
    
    app = Application(scan_mode)
    
    # Apply CLI overrides
    if args.mode:
        logger.info(f"🧭 CLI Mode: {args.mode}")
    
    if args.config_preset:
        # Load preset configuration
        import os
        preset_file = f"config/presets/{args.config_preset}.env"
        if os.path.exists(preset_file):
            from dotenv import load_dotenv
            load_dotenv(preset_file, override=True)
            logger.info(f"📋 Loaded preset: {args.config_preset}")
        else:
            logger.error(f"❌ Preset not found: {preset_file}")
            sys.exit(1)
    
    app.run()


if __name__ == "__main__":
    main()