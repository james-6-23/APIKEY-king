import os
import os
import random
from typing import Dict, Optional

from dotenv import load_dotenv

from common.Logger import logger

# 只在环境变量不存在时才从.env加载值
load_dotenv(override=False)


class Config:
    GITHUB_TOKENS_STR = os.getenv("GITHUB_TOKENS", "")

    # 获取GitHub tokens列表
    GITHUB_TOKENS = [token.strip() for token in GITHUB_TOKENS_STR.split(',') if token.strip()]
    DATA_PATH = os.getenv('DATA_PATH', '/app/data')
    PROXY_LIST_STR = os.getenv("PROXY", "")
    
    # 解析代理列表，支持格式：http://user:pass@host:port,http://host:port,socks5://user:pass@host:port
    PROXY_LIST = []
    if PROXY_LIST_STR:
        for proxy_str in PROXY_LIST_STR.split(','):
            proxy_str = proxy_str.strip()
            if proxy_str:
                PROXY_LIST.append(proxy_str)
    
    # 同步配置已移除

    # 文件前缀配置
    VALID_KEY_PREFIX = os.getenv("VALID_KEY_PREFIX", "keys/keys_valid_")
    RATE_LIMITED_KEY_PREFIX = os.getenv("RATE_LIMITED_KEY_PREFIX", "keys/key_429_")
    # KEYS_SEND_PREFIX 已移除，不再需要同步功能

    VALID_KEY_DETAIL_PREFIX = os.getenv("VALID_KEY_DETAIL_PREFIX", "logs/keys_valid_detail_")
    RATE_LIMITED_KEY_DETAIL_PREFIX = os.getenv("RATE_LIMITED_KEY_DETAIL_PREFIX", "logs/key_429_detail_")
    # KEYS_SEND_DETAIL_PREFIX 已移除，不再需要同步功能
    
    # 日期范围过滤器配置 (单位：天)
    DATE_RANGE_DAYS = int(os.getenv("DATE_RANGE_DAYS", "730"))  # 默认730天 (约2年)

    # 查询文件路径配置
    QUERIES_FILE = os.getenv("QUERIES_FILE", "queries.txt")

    # 已扫描SHA文件配置
    SCANNED_SHAS_FILE = os.getenv("SCANNED_SHAS_FILE", "scanned_shas.txt")

    # Gemini模型配置
    HAJIMI_CHECK_MODEL = os.getenv("HAJIMI_CHECK_MODEL", "gemini-2.5-flash")

    # 文件路径黑名单配置
    FILE_PATH_BLACKLIST_STR = os.getenv("FILE_PATH_BLACKLIST", "readme,docs,doc/,.md,sample,tutorial")
    FILE_PATH_BLACKLIST = [token.strip().lower() for token in FILE_PATH_BLACKLIST_STR.split(',') if token.strip()]

    # ModelScope key extraction (ms-uuid) configuration
    TARGET_BASE_URLS_STR = os.getenv(
        "TARGET_BASE_URLS",
        "https://api-inference.modelscope.cn/v1/"
    )
    TARGET_BASE_URLS = [u.strip() for u in TARGET_BASE_URLS_STR.split(',') if u.strip()]

    # Whether to use a loose key pattern (requires proximity filtering to avoid noise)
    MS_USE_LOOSE_PATTERN = os.getenv("MS_USE_LOOSE_PATTERN", "false")
    # Character distance threshold between base_url occurrence and key match (effective when using loose pattern)
    MS_PROXIMITY_CHARS = int(os.getenv("MS_PROXIMITY_CHARS", "0"))
    # Require key context words around the match, e.g., key/token/authorization
    MS_REQUIRE_KEY_CONTEXT = os.getenv("MS_REQUIRE_KEY_CONTEXT", "false")
    # If true, when extracting ModelScope keys, skip any validation and just save keys
    MODELSCOPE_EXTRACT_ONLY = os.getenv("MODELSCOPE_EXTRACT_ONLY", "true")

    # OpenRouter key extraction configuration
    OPENROUTER_BASE_URLS_STR = os.getenv(
        "OPENROUTER_BASE_URLS",
        "https://openrouter.ai/api/v1"
    )
    OPENROUTER_BASE_URLS = [u.strip() for u in OPENROUTER_BASE_URLS_STR.split(',') if u.strip()]
    
    # OpenRouter key extraction settings
    OPENROUTER_USE_LOOSE_PATTERN = os.getenv("OPENROUTER_USE_LOOSE_PATTERN", "false")
    OPENROUTER_PROXIMITY_CHARS = int(os.getenv("OPENROUTER_PROXIMITY_CHARS", "0"))
    OPENROUTER_REQUIRE_KEY_CONTEXT = os.getenv("OPENROUTER_REQUIRE_KEY_CONTEXT", "false")
    OPENROUTER_EXTRACT_ONLY = os.getenv("OPENROUTER_EXTRACT_ONLY", "true")

    @classmethod
    def parse_bool(cls, value: str) -> bool:
        """
        解析布尔值配置，支持多种格式
        
        Args:
            value: 配置值字符串
            
        Returns:
            bool: 解析后的布尔值
        """
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value = value.strip().lower()
            return value in ('true', '1', 'yes', 'on', 'enabled')
        
        if isinstance(value, int):
            return bool(value)
        
        return False

    @classmethod
    def get_random_proxy(cls) -> Optional[Dict[str, str]]:
        """
        随机获取一个代理配置
        
        Returns:
            Optional[Dict[str, str]]: requests格式的proxies字典，如果未配置则返回None
        """
        if not cls.PROXY_LIST:
            return None
        
        # 随机选择一个代理
        proxy_url = random.choice(cls.PROXY_LIST).strip()
        
        # 返回requests格式的proxies字典
        return {
            'http': proxy_url,
            'https': proxy_url
        }

    @classmethod
    def check(cls) -> bool:
        """
        检查必要的配置是否完整
        
        Returns:
            bool: 配置是否完整
        """
        logger.info("🔍 Checking required configurations...")
        
        errors = []
        
        # 检查GitHub tokens
        if not cls.GITHUB_TOKENS:
            errors.append("GitHub tokens not found. Please set GITHUB_TOKENS environment variable.")
            logger.error("❌ GitHub tokens: Missing")
        else:
            logger.info(f"✅ GitHub tokens: {len(cls.GITHUB_TOKENS)} configured")
        
        # 同步功能配置检查已移除
        logger.info("ℹ️ 同步功能已被移除")

        if errors:
            logger.error("❌ Configuration check failed:")
            logger.info("Please check your .env file and configuration.")
            return False
        
        logger.info("✅ All required configurations are valid")
        return True


logger.info(f"*" * 30 + " CONFIG START " + "*" * 30)
logger.info(f"GITHUB_TOKENS: {len(Config.GITHUB_TOKENS)} tokens")
logger.info(f"DATA_PATH: {Config.DATA_PATH}")
logger.info(f"PROXY_LIST: {len(Config.PROXY_LIST)} proxies configured")
# 同步相关配置日志已移除
logger.info(f"VALID_KEY_PREFIX: {Config.VALID_KEY_PREFIX}")
logger.info(f"RATE_LIMITED_KEY_PREFIX: {Config.RATE_LIMITED_KEY_PREFIX}")
logger.info(f"VALID_KEY_DETAIL_PREFIX: {Config.VALID_KEY_DETAIL_PREFIX}")
logger.info(f"RATE_LIMITED_KEY_DETAIL_PREFIX: {Config.RATE_LIMITED_KEY_DETAIL_PREFIX}")
logger.info(f"DATE_RANGE_DAYS: {Config.DATE_RANGE_DAYS} days")
logger.info(f"QUERIES_FILE: {Config.QUERIES_FILE}")
logger.info(f"SCANNED_SHAS_FILE: {Config.SCANNED_SHAS_FILE}")
logger.info(f"HAJIMI_CHECK_MODEL: {Config.HAJIMI_CHECK_MODEL}")
logger.info(f"FILE_PATH_BLACKLIST: {len(Config.FILE_PATH_BLACKLIST)} items")
logger.info(f"TARGET_BASE_URLS: {len(Config.TARGET_BASE_URLS)} configured")
logger.info(f"MS_USE_LOOSE_PATTERN: {Config.parse_bool(Config.MS_USE_LOOSE_PATTERN)}")
logger.info(f"MS_PROXIMITY_CHARS: {Config.MS_PROXIMITY_CHARS}")
logger.info(f"MS_REQUIRE_KEY_CONTEXT: {Config.parse_bool(Config.MS_REQUIRE_KEY_CONTEXT)}")
logger.info(f"MODELSCOPE_EXTRACT_ONLY: {Config.parse_bool(Config.MODELSCOPE_EXTRACT_ONLY)}")
logger.info(f"OPENROUTER_BASE_URLS: {len(Config.OPENROUTER_BASE_URLS)} configured")
logger.info(f"OPENROUTER_USE_LOOSE_PATTERN: {Config.parse_bool(Config.OPENROUTER_USE_LOOSE_PATTERN)}")
logger.info(f"OPENROUTER_PROXIMITY_CHARS: {Config.OPENROUTER_PROXIMITY_CHARS}")
logger.info(f"OPENROUTER_REQUIRE_KEY_CONTEXT: {Config.parse_bool(Config.OPENROUTER_REQUIRE_KEY_CONTEXT)}")
logger.info(f"OPENROUTER_EXTRACT_ONLY: {Config.parse_bool(Config.OPENROUTER_EXTRACT_ONLY)}")
logger.info(f"*" * 30 + " CONFIG END " + "*" * 30)

# 创建全局配置实例
config = Config()
