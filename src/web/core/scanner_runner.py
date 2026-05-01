"""
Scanner runner for background execution.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Callable

from ...core import ScanMode, APIKeyScanner
from ...services import ConfigService as AppConfigService, GitHubService, FileService
from ...extractors import ModelScopeExtractor
from ...validators import ModelScopeValidator
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

            # Precompute normalized queries and load the processed set ONCE
            # (previously we issued one SQL round-trip per query per loop).
            normalized_queries = [" ".join(q.split()) for q in queries]
            processed_queries = db.get_processed_queries_set()
            # Ditto for scanned SHAs — the inner loop used to hit the DB once
            # per item which became the dominant latency at high item counts.
            scanned_shas = db.get_scanned_shas_set()

            # Concurrency for file fetches. The inner loop is IO-bound (one
            # HTTPS roundtrip per item) — serial was wasting the budget the
            # user already set in performance.max_concurrent.
            performance_cfg = self.config.get("performance") or {}
            try:
                max_concurrent = int(performance_cfg.get("max_concurrent", 5))
            except (TypeError, ValueError):
                max_concurrent = 5
            max_concurrent = max(1, min(max_concurrent, 20))

            # Scan loop
            loop_count = 0
            while not stop_flag():
                loop_count += 1
                self.log_service.add_log("info", f"Starting scan loop #{loop_count}")

                # Fast in-memory check — O(len(queries)) set lookups.
                if all(nq in processed_queries for nq in normalized_queries):
                    self.log_service.add_log("success", "All queries have been processed! Scan completed.")
                    break

                queries_processed_this_loop = 0
                for i, (query, normalized_query) in enumerate(zip(queries, normalized_queries), 1):
                    if stop_flag():
                        break

                    # 暂停检查 — interruptible wait: returns True immediately if stop fires
                    while self.scan_service.is_paused():
                        if self.scan_service.wait_or_stop(1.0):
                            break

                    if stop_flag():
                        break

                    # 更新进度
                    self.scan_service.update_progress(i, len(queries), query[:50])

                    if normalized_query in processed_queries:
                        continue

                    queries_processed_this_loop += 1
                    self.log_service.add_log("info", f"Processing query {i}/{len(queries)}: {query[:50]}...")

                    try:
                        # Search GitHub
                        search_results = github_service.search_code(query)
                        items = search_results.get('items', [])

                        if not items:
                            db.add_processed_query(normalized_query)
                            processed_queries.add(normalized_query)
                            continue

                        self.log_service.add_log("info", f"Found {len(items)} items for query {i}")

                        # Filter out SHAs we've already processed BEFORE submitting
                        # to the pool — saves on wasted GitHub roundtrips.
                        pending = [it for it in items if not (it.get("sha") and it.get("sha") in scanned_shas)]
                        skipped = len(items) - len(pending)
                        if skipped:
                            self.log_service.add_log("info", f"Skipped {skipped} already-scanned items")

                        # Concurrent fetch (IO-bound), serial scan/validate/save.
                        # Validation stays on the main thread to avoid any
                        # third-party SDK that mutates process-global state.
                        with ThreadPoolExecutor(
                            max_workers=max_concurrent,
                            thread_name_prefix="apikey-fetch",
                        ) as pool:
                            future_to_item = {
                                pool.submit(github_service.get_file_content, it): it
                                for it in pending
                            }
                            try:
                                for fut in as_completed(future_to_item):
                                    if stop_flag():
                                        # Cancel queued futures; in-flight ones
                                        # will finish and be discarded below.
                                        for f in future_to_item:
                                            f.cancel()
                                        break

                                    item = future_to_item[fut]
                                    try:
                                        content = fut.result()
                                    except Exception as e:
                                        self.log_service.add_log("error", f"Fetch failed: {type(e).__name__}: {e}")
                                        continue

                                    if not content:
                                        continue

                                    sha = item.get("sha")
                                    repo_full = item.get('repository', {}).get('full_name', '')
                                    file_path = item.get('path', '')

                                    context = {
                                        'file_path': file_path,
                                        'repository': item.get('repository', {}),
                                    }

                                    scan_results = scanner.scan_content(content, context)

                                    if scan_results['summary']['total_keys_found'] > 0:
                                        self.log_service.add_log("success", f"Found {scan_results['summary']['total_keys_found']} keys", {
                                            "file": file_path,
                                            "repo": repo_full,
                                        })

                                        for key, validation_result in scan_results['validation_results'].items():
                                            if validation_result.is_valid:
                                                key_type = self._determine_key_type(key)
                                                balance = None
                                                if validation_result.metadata:
                                                    total_balance = validation_result.metadata.get('total_balance')
                                                    if total_balance:
                                                        balance = total_balance

                                                db.save_key(
                                                    key_value=key,
                                                    key_type=key_type,
                                                    source_repo=repo_full,
                                                    source_file=file_path,
                                                    source_url=item.get('html_url', ''),
                                                    is_valid=True,
                                                    validation_status='valid',
                                                    validation_message=None,
                                                    balance=balance,
                                                )
                                                self.stats["valid_keys"] += 1

                                    if sha:
                                        db.add_scanned_sha(sha, file_path, repo_full)
                                        scanned_shas.add(sha)
                                    self.stats["total_files"] += 1
                                    self.stats["last_update"] = datetime.now().isoformat()
                            finally:
                                # Defensive: if we broke out on stop_flag, ensure
                                # in-flight fetches don't leak past the with-block.
                                # ThreadPoolExecutor.__exit__ already waits, but
                                # keeps the semantics explicit.
                                pass

                        if stop_flag():
                            break

                        # 标记查询已处理
                        db.add_processed_query(normalized_query)
                        processed_queries.add(normalized_query)
                        self.stats["queries_completed"] = self.stats.get("queries_completed", 0) + 1

                    except Exception as e:
                        self.log_service.add_log("error", f"Error processing query: {str(e)}")

                # If no new queries were processed, check again in next loop
                if queries_processed_this_loop == 0 and not stop_flag():
                    # All queries already processed, will exit on next loop check
                    self.log_service.add_log("info", "No new queries to process, checking completion...")
                    continue
                
                if not stop_flag():
                    self.log_service.add_log("info", "Scan loop complete, sleeping 10 seconds...")
                    # Interruptible sleep — stop fires break out immediately.
                    if self.scan_service.wait_or_stop(10.0):
                        break

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
        if scan_mode == ScanMode.MODELSCOPE_ONLY:
            for name, extractor_config in config.extractors.items():
                extractor_config.enabled = (name == 'modelscope')
            for name, validator_config in config.validators.items():
                validator_config.enabled = (name == 'modelscope')
            config.scan.queries_file = "config/queries/modelscope.txt"
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
            
            if name == 'modelscope':
                extractors.append(ModelScopeExtractor(extractor_config))
            elif name == 'siliconflow':
                from ...extractors.siliconflow import SiliconFlowExtractor
                extractors.append(SiliconFlowExtractor(extractor_config))
            elif name == 'deepseek':
                from ...extractors.deepseek import DeepSeekExtractor
                extractors.append(DeepSeekExtractor(extractor_config))

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
                if name == 'modelscope':
                    validator = ModelScopeValidator(validator_config)
                    validators.append(validator)
                    self.log_service.add_log("info", f"Initialized {name} validator", {"model": validator_config.model})
                elif name == 'siliconflow':
                    from ...validators.siliconflow import SiliconFlowValidator
                    validator = SiliconFlowValidator(validator_config)
                    validators.append(validator)
                    self.log_service.add_log("info", f"Initialized {name} validator", {"model": validator_config.model})
                elif name == 'deepseek':
                    from ...validators.deepseek import DeepSeekValidator
                    validator = DeepSeekValidator(validator_config)
                    validators.append(validator)
                    # DeepSeek validates via /user/balance — no model field is used.
                    self.log_service.add_log("info", f"Initialized {name} validator", {"endpoint": "api.deepseek.com/user/balance"})
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
        import re
        if key.startswith('ms-'):
            return 'modelscope'
        # DeepSeek keys are 'sk-' + 32 hex chars (length 35). Check before the
        # generic SiliconFlow fallback since both share the 'sk-' prefix.
        elif re.match(r'^sk-[a-f0-9]{32}$', key, re.IGNORECASE):
            return 'deepseek'
        elif key.startswith('sk-'):
            return 'siliconflow'
        else:
            return 'unknown'
