import os
import random
import re
import argparse
import sys
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Union, Any, Tuple

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.Logger import logger
from common.config import Config
from utils.github_client import GitHubClient
from utils.file_manager import file_manager, Checkpoint, checkpoint
# sync_utils 已移除

# 创建GitHub工具实例和文件管理器
github_utils = GitHubClient.create_instance(Config.GITHUB_TOKENS)

# 统计信息
skip_stats = {
    "time_filter": 0,
    "sha_duplicate": 0,
    "age_filter": 0,
    "doc_filter": 0
}


def normalize_query(query: str) -> str:
    query = " ".join(query.split())

    parts = []
    i = 0
    while i < len(query):
        if query[i] == '"':
            end_quote = query.find('"', i + 1)
            if end_quote != -1:
                parts.append(query[i:end_quote + 1])
                i = end_quote + 1
            else:
                parts.append(query[i])
                i += 1
        elif query[i] == ' ':
            i += 1
        else:
            start = i
            while i < len(query) and query[i] != ' ':
                i += 1
            parts.append(query[start:i])

    quoted_strings = []
    language_parts = []
    filename_parts = []
    path_parts = []
    other_parts = []

    for part in parts:
        if part.startswith('"') and part.endswith('"'):
            quoted_strings.append(part)
        elif part.startswith('language:'):
            language_parts.append(part)
        elif part.startswith('filename:'):
            filename_parts.append(part)
        elif part.startswith('path:'):
            path_parts.append(part)
        elif part.strip():
            other_parts.append(part)

    normalized_parts = []
    normalized_parts.extend(sorted(quoted_strings))
    normalized_parts.extend(sorted(other_parts))
    normalized_parts.extend(sorted(language_parts))
    normalized_parts.extend(sorted(filename_parts))
    normalized_parts.extend(sorted(path_parts))

    return " ".join(normalized_parts)


def extract_keys_from_content(content: str) -> List[str]:
    pattern = r'(AIzaSy[A-Za-z0-9\-_]{33})'
    return re.findall(pattern, content)


def _contains_base_url(content: str, base_urls: List[str]) -> Tuple[bool, List[int]]:
    """检查内容中是否包含任意指定的base_url，并返回出现位置索引列表"""
    if not base_urls:
        return False, []
    lc = content.lower()
    positions: List[int] = []
    for url in base_urls:
        if not url:
            continue
        u = url.lower()
        start = 0
        while True:
            idx = lc.find(u, start)
            if idx == -1:
                break
            positions.append(idx)
            start = idx + 1
    return (len(positions) > 0), positions


def extract_ms_keys_for_modelscope(content: str) -> List[str]:
    """
    当同一文件中包含 Config.TARGET_BASE_URLS 任一值时，提取形态为 ms-UUID 的key。
    不做外部验证，仅基于形态与上下文（可选）筛选。
    受控于以下配置：
      - TARGET_BASE_URLS
      - MS_USE_LOOSE_PATTERN (bool)
      - MS_PROXIMITY_CHARS (int, 当使用宽松模式时建议>0)
      - MS_REQUIRE_KEY_CONTEXT (bool)
    """
    base_urls = Config.TARGET_BASE_URLS
    has_base, base_positions = _contains_base_url(content, base_urls)
    if not has_base:
        return []

    # 正则：严格UUID或宽松长度
    strict_pat = r'(?i)\bms-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'
    loose_pat = r'(?i)\bms-[0-9a-f-]{30,}\b'
    use_loose = Config.parse_bool(Config.MS_USE_LOOSE_PATTERN)
    pattern = loose_pat if use_loose else strict_pat

    proximity_chars = Config.MS_PROXIMITY_CHARS if use_loose else 0
    require_ctx = Config.parse_bool(Config.MS_REQUIRE_KEY_CONTEXT)
    ctx_re = re.compile(r"(key|token|secret|authorization|api[-_ ]?key)", re.IGNORECASE)

    results: List[str] = []
    for m in re.finditer(pattern, content):
        k = m.group(0)
        # 过滤明显占位符
        if k.lower() == "ms-00000000-0000-0000-0000-000000000000":
            continue

        if proximity_chars and base_positions:
            pos = m.start()
            near = any(abs(pos - bp) <= proximity_chars for bp in base_positions)
            if not near:
                continue

        if require_ctx:
            start = max(0, m.start() - 80)
            end = min(len(content), m.end() + 80)
            snippet = content[start:end]
            if not ctx_re.search(snippet):
                continue

        results.append(k)

    # 去重且保序
    seen = set()
    deduped = [x for x in results if not (x in seen or seen.add(x))]
    return deduped


def extract_openrouter_keys(content: str) -> List[str]:
    """
    当同一文件中包含 Config.OPENROUTER_BASE_URLS 任一值时，提取 OpenRouter API keys。
    OpenRouter key 格式: sk-or-v1-[64位十六进制字符串]
    受控于以下配置：
      - OPENROUTER_BASE_URLS
      - OPENROUTER_USE_LOOSE_PATTERN (bool)
      - OPENROUTER_PROXIMITY_CHARS (int, 当使用宽松模式时建议>0)
      - OPENROUTER_REQUIRE_KEY_CONTEXT (bool)
    """
    base_urls = Config.OPENROUTER_BASE_URLS
    has_base, base_positions = _contains_base_url(content, base_urls)
    if not has_base:
        return []

    # OpenRouter key 正则模式
    # 严格模式：sk-or-v1-[64位十六进制]
    strict_pat = r'\bsk-or-v1-[0-9a-f]{64}\b'
    # 宽松模式：sk-or-v1-[至少40位字符]
    loose_pat = r'\bsk-or-v1-[0-9a-f]{40,}\b'
    
    use_loose = Config.parse_bool(Config.OPENROUTER_USE_LOOSE_PATTERN)
    pattern = loose_pat if use_loose else strict_pat

    proximity_chars = Config.OPENROUTER_PROXIMITY_CHARS if use_loose else 0
    require_ctx = Config.parse_bool(Config.OPENROUTER_REQUIRE_KEY_CONTEXT)
    ctx_re = re.compile(r"(key|token|secret|authorization|api[-_ ]?key|openrouter)", re.IGNORECASE)

    results: List[str] = []
    for m in re.finditer(pattern, content, re.IGNORECASE):
        k = m.group(0)
        
        # 过滤明显的占位符
        if "0000000000000000" in k.lower() or "your_key" in k.lower() or "example" in k.lower():
            continue

        # 邻近性检查（当使用宽松模式时）
        if proximity_chars and base_positions:
            pos = m.start()
            near = any(abs(pos - bp) <= proximity_chars for bp in base_positions)
            if not near:
                continue

        # 上下文检查（当启用时）
        if require_ctx:
            start = max(0, m.start() - 80)
            end = min(len(content), m.end() + 80)
            snippet = content[start:end]
            if not ctx_re.search(snippet):
                continue

        results.append(k)

    # 去重且保序
    seen = set()
    deduped = [x for x in results if not (x in seen or seen.add(x))]
    return deduped


def _parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hajimi King")
    parser.add_argument(
        "--mode",
        choices=["modelscope-only", "openrouter-only", "compatible"],
        help="modelscope-only: 仅提取 ms-key，不回退到 Gemini；openrouter-only: 仅提取 OpenRouter key；compatible: 未命中时回退到原有逻辑",
    )
    return parser.parse_args()


def should_skip_item(item: Dict[str, Any], checkpoint: Checkpoint) -> tuple[bool, str]:
    """
    检查是否应该跳过处理此item
    
    Returns:
        tuple: (should_skip, reason)
    """
    # 检查增量扫描时间
    if checkpoint.last_scan_time:
        try:
            last_scan_dt = datetime.fromisoformat(checkpoint.last_scan_time)
            repo_pushed_at = item["repository"].get("pushed_at")
            if repo_pushed_at:
                repo_pushed_dt = datetime.strptime(repo_pushed_at, "%Y-%m-%dT%H:%M:%SZ")
                if repo_pushed_dt <= last_scan_dt:
                    skip_stats["time_filter"] += 1
                    return True, "time_filter"
        except Exception as e:
            pass

    # 检查SHA是否已扫描
    if item.get("sha") in checkpoint.scanned_shas:
        skip_stats["sha_duplicate"] += 1
        return True, "sha_duplicate"

    # 检查仓库年龄
    repo_pushed_at = item["repository"].get("pushed_at")
    if repo_pushed_at:
        repo_pushed_dt = datetime.strptime(repo_pushed_at, "%Y-%m-%dT%H:%M:%SZ")
        if repo_pushed_dt < datetime.utcnow() - timedelta(days=Config.DATE_RANGE_DAYS):
            skip_stats["age_filter"] += 1
            return True, "age_filter"

    # 检查文档和示例文件
    lowercase_path = item["path"].lower()
    if any(token in lowercase_path for token in Config.FILE_PATH_BLACKLIST):
        skip_stats["doc_filter"] += 1
        return True, "doc_filter"

    return False, ""


def process_item(item: Dict[str, Any]) -> tuple:
    """
    处理单个GitHub搜索结果item
    
    Returns:
        tuple: (valid_keys_count, rate_limited_keys_count)
    """
    delay = random.uniform(1, 4)
    file_url = item["html_url"]

    # 简化日志输出，只显示关键信息
    repo_name = item["repository"]["full_name"]
    file_path = item["path"]
    time.sleep(delay)

    content = github_utils.get_file_content(item)
    if not content:
        logger.warning(f"⚠️ Failed to fetch content for file: {file_url}")
        return 0, 0

    # 优先尝试ModelScope提取逻辑（当配置了目标base_url时）
    ms_keys: List[str] = []
    try:
        if Config.TARGET_BASE_URLS:
            ms_keys = extract_ms_keys_for_modelscope(content)
    except Exception as e:
        logger.error(f"ModelScope key extraction error: {e}")

    # 尝试OpenRouter密钥提取（当配置了OpenRouter base_url时）
    openrouter_keys: List[str] = []
    try:
        if Config.OPENROUTER_BASE_URLS:
            openrouter_keys = extract_openrouter_keys(content)
    except Exception as e:
        logger.error(f"OpenRouter key extraction error: {e}")

    # 如果找到了ModelScope或OpenRouter密钥，优先处理它们
    if ms_keys:
        logger.success(f"Found {len(ms_keys)} ModelScope key(s) (no validation)")
        file_manager.save_valid_keys(repo_name, file_path, file_url, ms_keys)
        logger.file_op(f"Saved {len(ms_keys)} ModelScope key(s)")
        return len(ms_keys), 0
    
    if openrouter_keys:
        logger.success(f"Found {len(openrouter_keys)} OpenRouter key(s) (no validation)")
        file_manager.save_valid_keys(repo_name, file_path, file_url, openrouter_keys)
        logger.file_op(f"Saved {len(openrouter_keys)} OpenRouter key(s)")
        return len(openrouter_keys), 0

    # 若启用仅提取模式（ModelScope 或 OpenRouter），则不回退到Gemini提取
    extract_only_mode = Config.parse_bool(Config.MODELSCOPE_EXTRACT_ONLY) or Config.parse_bool(Config.OPENROUTER_EXTRACT_ONLY)
    if extract_only_mode:
        logger.info("ℹ️ Extract-only mode enabled, no keys found, skipping Gemini extraction")
        return 0, 0

    # 默认回退到原有的Gemini密钥提取
    keys = extract_keys_from_content(content)

    # 过滤占位符密钥
    filtered_keys = []
    for key in keys:
        context_index = content.find(key)
        if context_index != -1:
            snippet = content[context_index:context_index + 45]
            if "..." in snippet or "YOUR_" in snippet.upper():
                continue
        filtered_keys.append(key)
    
    # 去重处理
    keys = list(set(filtered_keys))

    if not keys:
        return 0, 0

    logger.info(f"🔍 Found {len(keys)} suspected key(s), validating...")

    valid_keys = []
    rate_limited_keys = []

    # 验证每个密钥
    for key in keys:
        validation_result = validate_gemini_key(key)
        if validation_result and "ok" in validation_result:
            valid_keys.append(key)
            logger.success(f"VALID: {key}")
        elif validation_result == "rate_limited":
            rate_limited_keys.append(key)
            logger.rate_limit(f"RATE LIMITED: {key}, check result: {validation_result}")
        else:
            logger.info(f"❌ INVALID: {key}, check result: {validation_result}")

    # 保存结果
    if valid_keys:
        file_manager.save_valid_keys(repo_name, file_path, file_url, valid_keys)
        logger.file_op(f"Saved {len(valid_keys)} valid key(s)")
        # 同步功能已移除

    if rate_limited_keys:
        file_manager.save_rate_limited_keys(repo_name, file_path, file_url, rate_limited_keys)
        logger.file_op(f"Saved {len(rate_limited_keys)} rate limited key(s)")

    return len(valid_keys), len(rate_limited_keys)


def validate_gemini_key(api_key: str) -> Union[bool, str]:
    try:
        time.sleep(random.uniform(0.5, 1.5))

        # 获取随机代理配置
        proxy_config = Config.get_random_proxy()
        
        client_options = {
            "api_endpoint": "generativelanguage.googleapis.com"
        }
        
        # 如果有代理配置，添加到client_options中
        if proxy_config and proxy_config.get('http'):
            os.environ['grpc_proxy'] = proxy_config.get('http')

        genai.configure(
            api_key=api_key,
            client_options=client_options,
        )

        model = genai.GenerativeModel(Config.HAJIMI_CHECK_MODEL)
        response = model.generate_content("hi")
        return "ok"
    except (google_exceptions.PermissionDenied, google_exceptions.Unauthenticated) as e:
        return "not_authorized_key"
    except google_exceptions.TooManyRequests as e:
        return "rate_limited"
    except Exception as e:
        if "429" in str(e) or "rate limit" in str(e).lower() or "quota" in str(e).lower():
            return "rate_limited:429"
        elif "403" in str(e) or "SERVICE_DISABLED" in str(e) or "API has not been used" in str(e):
            return "disabled"
        else:
            return f"error:{e.__class__.__name__}"


def print_skip_stats():
    """打印跳过统计信息"""
    total_skipped = sum(skip_stats.values())
    if total_skipped > 0:
        logger.info(f"📊 Skipped {total_skipped} items - Time: {skip_stats['time_filter']}, Duplicate: {skip_stats['sha_duplicate']}, Age: {skip_stats['age_filter']}, Docs: {skip_stats['doc_filter']}")


def reset_skip_stats():
    """重置跳过统计"""
    global skip_stats
    skip_stats = {"time_filter": 0, "sha_duplicate": 0, "age_filter": 0, "doc_filter": 0}


def main():
    start_time = datetime.now()

    # 解析命令行参数，配置提取模式
    try:
        args = _parse_cli_args()
        if getattr(args, "mode", None):
            # CLI 覆盖环境变量：仅本进程生效
            if args.mode == "modelscope-only":
                Config.MODELSCOPE_EXTRACT_ONLY = "true"
                Config.OPENROUTER_EXTRACT_ONLY = "false"
                # 可选：清空 OpenRouter URLs 以确保不提取
                Config.OPENROUTER_BASE_URLS = []
                logger.info(f"🧭 CLI 模式: ModelScope-only mode activated")
            elif args.mode == "openrouter-only":
                Config.OPENROUTER_EXTRACT_ONLY = "true"
                Config.MODELSCOPE_EXTRACT_ONLY = "false"
                # 可选：清空 ModelScope URLs 以确保不提取
                Config.TARGET_BASE_URLS = []
                logger.info(f"🧭 CLI 模式: OpenRouter-only mode activated")
            elif args.mode == "compatible":
                Config.MODELSCOPE_EXTRACT_ONLY = "false"
                Config.OPENROUTER_EXTRACT_ONLY = "false"
                logger.info(f"🧭 CLI 模式: Compatible mode activated (will fallback to Gemini)")
    except SystemExit:
        return

    # 打印系统启动信息
    logger.separator("🚀 HAJIMI KING STARTING 🚀")
    logger.info(f"⏰ Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 检查配置
    if not Config.check():
        logger.error("Config check failed. Exiting...")
        sys.exit(1)
    # 2. 检查文件管理器
    if not file_manager.check():
        logger.error("FileManager check failed. Exiting...")
        sys.exit(1)

    # 同步功能相关代码已移除

    # 3. 显示系统信息
    search_queries = file_manager.get_search_queries()
    logger.separator("📋 SYSTEM INFORMATION")
    logger.info(f"🔑 GitHub tokens: {len(Config.GITHUB_TOKENS)} configured")
    logger.info(f"🔍 Search queries: {len(search_queries)} loaded")
    logger.info(f"📅 Date filter: {Config.DATE_RANGE_DAYS} days")
    if Config.PROXY_LIST:
        logger.network(f"Proxy: {len(Config.PROXY_LIST)} proxies configured")

    if checkpoint.last_scan_time:
        logger.info(f"💾 Checkpoint found - Incremental scan mode")
        logger.info(f"   Last scan: {checkpoint.last_scan_time}")
        logger.info(f"   Scanned files: {len(checkpoint.scanned_shas)}")
        logger.info(f"   Processed queries: {len(checkpoint.processed_queries)}")
    else:
        logger.info(f"💾 No checkpoint - Full scan mode")


    logger.success("System ready - Starting scan")
    logger.separator()

    total_keys_found = 0
    total_rate_limited_keys = 0
    loop_count = 0

    while True:
        try:
            loop_count += 1
            logger.info(f"🔄 Loop #{loop_count} - {datetime.now().strftime('%H:%M:%S')}")

            query_count = 0
            loop_processed_files = 0
            reset_skip_stats()

            for i, q in enumerate(search_queries, 1):
                normalized_q = normalize_query(q)
                if normalized_q in checkpoint.processed_queries:
                    logger.info(f"🔍 Skipping already processed query: [{q}],index:#{i}")
                    continue

                res = github_utils.search_for_keys(q)

                if res and "items" in res:
                    items = res["items"]
                    if items:
                        query_valid_keys = 0
                        query_rate_limited_keys = 0
                        query_processed = 0

                        for item_index, item in enumerate(items, 1):

                            # 每20个item保存checkpoint并显示进度
                            if item_index % 20 == 0:
                                logger.progress(
                                    f"Processing query: {q[:30]}...", 
                                    item_index, len(items)
                                )
                                logger.info(f"Current valid: {query_valid_keys} | Rate limited: {query_rate_limited_keys} | Total valid: {total_keys_found}")
                                file_manager.save_checkpoint(checkpoint)
                                file_manager.update_dynamic_filenames()

                            # 检查是否应该跳过此item
                            should_skip, skip_reason = should_skip_item(item, checkpoint)
                            if should_skip:
                                logger.info(f"🚫 Skipping item,name: {item.get('path','').lower()},index:{item_index} - reason: {skip_reason}")
                                continue

                            # 处理单个item
                            valid_count, rate_limited_count = process_item(item)

                            query_valid_keys += valid_count
                            query_rate_limited_keys += rate_limited_count
                            query_processed += 1

                            # 记录已扫描的SHA
                            checkpoint.add_scanned_sha(item.get("sha"))

                            loop_processed_files += 1



                        total_keys_found += query_valid_keys
                        total_rate_limited_keys += query_rate_limited_keys

                        if query_processed > 0:
                            logger.info(f"✅ Query {i}/{len(search_queries)} complete - Processed: {query_processed}, Valid: +{query_valid_keys}, Rate limited: +{query_rate_limited_keys}")
                        else:
                            logger.info(f"⏭️ Query {i}/{len(search_queries)} complete - All items skipped")

                        print_skip_stats()
                    else:
                        logger.info(f"📭 Query {i}/{len(search_queries)} - No items found")
                else:
                    logger.warning(f"❌ Query {i}/{len(search_queries)} failed")

                checkpoint.add_processed_query(normalized_q)
                query_count += 1

                checkpoint.update_scan_time()
                file_manager.save_checkpoint(checkpoint)
                file_manager.update_dynamic_filenames()

                if query_count % 5 == 0:
                    logger.info(f"⏸️ Processed {query_count} queries, taking a break...")
                    time.sleep(1)

            logger.info(f"🏁 Loop #{loop_count} complete - Processed {loop_processed_files} files | Total valid: {total_keys_found} | Total rate limited: {total_rate_limited_keys}")

            logger.info(f"💤 Sleeping for 10 seconds...")
            time.sleep(10)

        except KeyboardInterrupt:
            logger.info("⛔ Interrupted by user")
            checkpoint.update_scan_time()
            file_manager.save_checkpoint(checkpoint)
            logger.info(f"📊 Final stats - Valid keys: {total_keys_found}, Rate limited: {total_rate_limited_keys}")
            # 同步功能已移除
            break
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            traceback.print_exc()
            logger.info("🔄 Continuing...")
            continue


if __name__ == "__main__":
    main()
