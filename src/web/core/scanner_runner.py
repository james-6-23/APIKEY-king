"""
Scanner runner for background execution.
"""

import os
import time
from datetime import datetime
from typing import Dict, Callable

from ...core import ScanMode, APIKeyScanner
from ...services import ConfigService as AppConfigService, GitHubService, FileService
from ...extractors import GeminiExtractor, ModelScopeExtractor, OpenRouterExtractor
from ...validators import GeminiValidator, OpenRouterValidator, ModelScopeValidator
from ...models import AppConfig
from ..database.database import db


class ScannerRunner:
    """Scanner runner that executes scans in background."""
    
    def __init__(self, config: Dict, stats: Dict, log_service, scan_service):
        self.config = config
        self.stats = stats
        self.log_service = log_service
        self.scan_service = scan_service
    
    def run(self, stop_flag: Callable[[], bool]):
        """Run the scanner."""
        try:
            # Set environment variables
            os.environ["GITHUB_TOKENS"] = ",".join(self.config["github_tokens"])
            if self.config.get("proxy"):
                os.environ["PROXY"] = self.config["proxy"]
            os.environ["DATE_RANGE_DAYS"] = str(self.config.get("date_range_days", 730))

            # Determine scan mode
            scan_mode = ScanMode(self.config.get("scan_mode", "compatible"))

            # Initialize services
            app_config_service = AppConfigService()
            app_config = app_config_service.load_config()

            # Apply scan mode overrides
            self._apply_scan_mode_config(app_config, scan_mode)

            # Create GitHub service with log callback
            performance_cfg = self.config.get("performance") if isinstance(self.config, dict) else None
            github_service = GitHubService(
                app_config,
                log_callback=self._create_log_callback(),
                performance_config=performance_cfg
            )
            file_service = FileService(app_config.data_path)

            # Create extractors and validators with custom config
            extractors = self._create_extractors(app_config)
            validators_config = self.config.get("validators", {})
            validators = self._create_validators_with_config(app_config, validators_config)

            scanner = APIKeyScanner(extractors, validators)

            # 从数据库加载扫描记忆
            memory_stats = db.get_scan_memory_stats()

            self.log_service.add_log("success", "Scanner initialized", {
                "extractors": len(extractors),
                "validators": len(validators),
                "processed_queries": memory_stats.get("processed_queries", 0),
                "scanned_files": memory_stats.get("scanned_files", 0)
            })

            # Load queries
            queries = file_service.load_queries(app_config.scan.queries_file)
            self.log_service.add_log("info", f"Loaded {len(queries)} queries")

            # Update total queries for progress
            self.stats["total_queries"] = len(queries)

            # Scan loop
            loop_count = 0
            while not stop_flag():
                loop_count += 1
                self.log_service.add_log("info", f"Starting scan loop #{loop_count}")

                # Check if all queries have been processed
                all_processed = True
                for query in queries:
                    normalized_query = " ".join(query.split())
                    if not db.is_query_processed(normalized_query):
                        all_processed = False
                        break
                
                if all_processed:
                    self.log_service.add_log("success", "All queries have been processed! Scan completed.")
                    break

                queries_processed_this_loop = 0
                for i, query in enumerate(queries, 1):
                    if stop_flag():
                        break

                    # 暂停检查
                    while self.scan_service.is_paused() and not stop_flag():
                        time.sleep(1)

                    if stop_flag():
                        break

                    # 更新进度
                    self.scan_service.update_progress(i, len(queries), query[:50])

                    normalized_query = " ".join(query.split())

                    # 从数据库检查是否已处理
                    if db.is_query_processed(normalized_query):
                        continue

                    queries_processed_this_loop += 1
                    self.log_service.add_log("info", f"Processing query {i}/{len(queries)}: {query[:50]}...")

                    try:
                        # Search GitHub
                        search_results = github_service.search_code(query)
                        items = search_results.get('items', [])

                        if not items:
                            db.add_processed_query(normalized_query)
                            continue

                        self.log_service.add_log("info", f"Found {len(items)} items for query {i}")

                        # Process items
                        for item_idx, item in enumerate(items, 1):
                            if stop_flag():
                                break

                            # 检查是否已扫描（从数据库）
                            sha = item.get("sha")
                            if sha and db.is_sha_scanned(sha):
                                continue

                            # Get file content
                            content = github_service.get_file_content(item)
                            if not content:
                                continue

                            # Scan content
                            context = {
                                'file_path': item.get('path', ''),
                                'repository': item.get('repository', {}),
                            }

                            scan_results = scanner.scan_content(content, context)

                            if scan_results['summary']['total_keys_found'] > 0:
                                self.log_service.add_log("success", f"Found {scan_results['summary']['total_keys_found']} keys", {
                                    "file": item.get('path', ''),
                                    "repo": item.get('repository', {}).get('full_name', '')
                                })

                                # Save keys
                                for key, validation_result in scan_results['validation_results'].items():
                                    if validation_result.is_valid:
                                        key_type = self._determine_key_type(key)

                                        # 保存到数据库
                                        db.save_key(
                                            key_value=key,
                                            key_type=key_type,
                                            source_repo=item.get('repository', {}).get('full_name', ''),
                                            source_file=item.get('path', ''),
                                            source_url=item.get('html_url', ''),
                                            is_valid=True,
                                            validation_status='valid',
                                            validation_message=None
                                        )

                                        self.stats["valid_keys"] += 1

                            # 保存到数据库记忆
                            db.add_scanned_sha(
                                item.get("sha"),
                                item.get('path', ''),
                                item.get('repository', {}).get('full_name', '')
                            )
                            self.stats["total_files"] += 1
                            self.stats["last_update"] = datetime.now().isoformat()

                        # 标记查询已处理
                        db.add_processed_query(normalized_query)

                    except Exception as e:
                        self.log_service.add_log("error", f"Error processing query: {str(e)}")

                # If no new queries were processed, check again in next loop
                if queries_processed_this_loop == 0 and not stop_flag():
                    # All queries already processed, will exit on next loop check
                    self.log_service.add_log("info", "No new queries to process, checking completion...")
                    continue
                
                if not stop_flag():
                    self.log_service.add_log("info", "Scan loop complete, sleeping 10 seconds...")
                    time.sleep(10)

            if stop_flag():
                self.log_service.add_log("warning", "Scanner stopped by user")
            else:
                self.log_service.add_log("success", "Scanner completed successfully")

        except Exception as e:
            self.log_service.add_log("error", f"Scanner error: {str(e)}")
        finally:
            # 确保扫描结束时重置运行状态
            self.scan_service.finish_scan(
                completed=(not stop_flag())
            )
            self.log_service.add_log("info", "Scanner thread terminated")
    
    def _apply_scan_mode_config(self, config: AppConfig, scan_mode: ScanMode):
        """Apply scan mode configuration."""
        if scan_mode == ScanMode.OPENROUTER_ONLY:
            for name, extractor_config in config.extractors.items():
                extractor_config.enabled = (name == 'openrouter')
            for name, validator_config in config.validators.items():
                validator_config.enabled = (name == 'openrouter')
            config.scan.queries_file = "config/queries/openrouter.txt"
        elif scan_mode == ScanMode.MODELSCOPE_ONLY:
            for name, extractor_config in config.extractors.items():
                extractor_config.enabled = (name == 'modelscope')
            for name, validator_config in config.validators.items():
                validator_config.enabled = (name == 'modelscope')
            config.scan.queries_file = "config/queries/modelscope.txt"
        elif scan_mode == ScanMode.GEMINI_ONLY:
            for name, extractor_config in config.extractors.items():
                extractor_config.enabled = (name == 'gemini')
            for name, validator_config in config.validators.items():
                validator_config.enabled = (name == 'gemini')
            config.scan.queries_file = "config/queries/gemini.txt"
        elif scan_mode == ScanMode.SILICONFLOW_ONLY:
            for name, extractor_config in config.extractors.items():
                extractor_config.enabled = (name == 'siliconflow')
            for name, validator_config in config.validators.items():
                validator_config.enabled = (name == 'siliconflow')
            config.scan.queries_file = "config/queries/siliconflow.txt"
    
    def _create_extractors(self, config: AppConfig):
        """Create extractor instances."""
        extractors = []
        for name, extractor_config in config.extractors.items():
            if not extractor_config.enabled:
                continue
            
            if name == 'gemini':
                extractors.append(GeminiExtractor(extractor_config))
            elif name == 'modelscope':
                extractors.append(ModelScopeExtractor(extractor_config))
            elif name == 'openrouter':
                extractors.append(OpenRouterExtractor(extractor_config))
            elif name == 'siliconflow':
                from ...extractors.siliconflow import SiliconFlowExtractor
                extractors.append(SiliconFlowExtractor(extractor_config))
        
        return extractors
    
    def _create_validators_with_config(self, config: AppConfig, custom_validators: dict):
        """Create validator instances with custom configuration."""
        validators = []
        
        for name, validator_config in config.validators.items():
            # 检查自定义配置
            if name in custom_validators:
                custom = custom_validators[name]
                if not custom.get('enabled', True):
                    continue
                # 更新模型配置
                if 'model' in custom:
                    validator_config.model = custom['model']
            elif not validator_config.enabled:
                continue
            
            try:
                if name == 'gemini':
                    validator = GeminiValidator(validator_config)
                    validators.append(validator)
                    self.log_service.add_log("info", f"Initialized {name} validator", {"model": validator_config.model})
                elif name == 'openrouter':
                    validator = OpenRouterValidator(validator_config)
                    validators.append(validator)
                    self.log_service.add_log("info", f"Initialized {name} validator", {"model": validator_config.model})
                elif name == 'modelscope':
                    validator = ModelScopeValidator(validator_config)
                    validators.append(validator)
                    self.log_service.add_log("info", f"Initialized {name} validator", {"model": validator_config.model})
                elif name == 'siliconflow':
                    from ...validators.siliconflow import SiliconFlowValidator
                    validator = SiliconFlowValidator(validator_config)
                    validators.append(validator)
                    self.log_service.add_log("info", f"Initialized {name} validator", {"model": validator_config.model})
            except Exception as e:
                self.log_service.add_log("error", f"Failed to create {name} validator: {str(e)}")
        
        return validators
    
    def _create_log_callback(self):
        """Create a log callback function for GitHub service."""
        def log_callback(message: str):
            """Callback to send GitHub service logs to log_service."""
            # Determine log type based on message content
            log_type = 'info'
            if '✅' in message or '🔍' in message or 'complete' in message.lower():
                log_type = 'success'
            elif '❌' in message or 'error' in message.lower() or 'failed' in message.lower():
                log_type = 'error'
            elif '⚠️' in message or 'warning' in message.lower():
                log_type = 'warning'
            elif '🌐 Fetching:' in message:
                # Don't log every individual file fetch to reduce noise
                return
            
            self.log_service.add_log(log_type, message)
        
        return log_callback
    
    def _determine_key_type(self, key: str) -> str:
        """Determine key type from key format."""
        if key.startswith('AIzaSy'):
            return 'gemini'
        elif key.startswith('sk-or-v1-'):
            return 'openrouter'
        elif key.startswith('ms-'):
            return 'modelscope'
        elif key.startswith('sk-'):
            return 'siliconflow'
        else:
            return 'unknown'
