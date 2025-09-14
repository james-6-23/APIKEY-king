"""
Enhanced logger for the new architecture with bilingual support.
带有双语支持的增强日志记录器
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import existing logger functionality
try:
    from ...common.Logger import Logger as OriginalLogger
    _original_logger_available = True
except ImportError:
    _original_logger_available = False


class Logger:
    """Enhanced logger with bilingual Chinese-English support."""
    
    def __init__(self, name: str = 'APIKEY-king', level: int = logging.INFO):
        if _original_logger_available:
            self._logger = OriginalLogger(name, level)
        else:
            self._setup_fallback_logger(name, level)
    
    def _setup_fallback_logger(self, name: str, level: int):
        """Setup fallback logger if original is not available."""
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def _safe_log(self, level_method, message: str, *args, **kwargs):
        """Safe logging that handles emoji encoding issues."""
        # Proactively clean the message before logging to prevent encoding errors
        safe_message = self._remove_emoji(message)
        try:
            level_method(safe_message, *args, **kwargs)
        except Exception:
            # Final fallback - remove all non-ASCII characters
            ascii_message = message.encode('ascii', 'ignore').decode('ascii')
            level_method(ascii_message, *args, **kwargs)
    
    def _remove_emoji(self, text: str) -> str:
        """Remove emoji characters from text for Windows compatibility."""
        # Simple emoji removal - replace common problematic characters
        replacements = {
            '✅': '[OK]',
            '❌': '[ERROR]', 
            '🎯': '[TARGET]',
            '🚀': '[START]',
            '🔍': '[SEARCH]',
            '📊': '[STATS]',
            '⏰': '[TIME]',
            '🔑': '[KEY]',
            '📅': '[DATE]',
            '🌐': '[NET]',
            '💾': '[SAVE]',
            '📁': '[FILE]',
            '⏱️': '[WAIT]',
            '🎮': '[RUN]',
            '🧠': '[AI]',
            '🇨🇳': '[CN]',
            '📝': '[LOG]',
            '🔧': '[CONFIG]',
            '🧭': '[MODE]',
            '🏁': '[FINISH]',
            '🔄': '[LOOP]',
            '⏭️': '[SKIP]',
            '📭': '[EMPTY]',
            '💤': '[SLEEP]',
            '⛔': '[STOP]',
            '🎯': '[TARGET]',
            '🧠': '[BRAIN]',
            '🔑': '[TOKENS]',
            '📝': '[LOG]',
            '🤖': '[BOT]',
            '🎮': '[GAME]',
            '🔧': '[TOOL]'
        }
        
        result = text
        for emoji, replacement in replacements.items():
            result = result.replace(emoji, replacement)
        return result
    
    def debug(self, message: str, *args, **kwargs):
        """Debug level logging."""
        if hasattr(self._logger, 'debug'):
            self._safe_log(self._logger.debug, message, *args, **kwargs)
        else:
            self._safe_log(self._logger.debug, str(message), *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Info level logging."""
        if hasattr(self._logger, 'info'):
            self._safe_log(self._logger.info, message, *args, **kwargs)
        else:
            self._safe_log(self._logger.info, str(message), *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Warning level logging."""
        if hasattr(self._logger, 'warning'):
            self._safe_log(self._logger.warning, message, *args, **kwargs)
        else:
            self._safe_log(self._logger.warning, str(message), *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Error level logging."""
        if hasattr(self._logger, 'error'):
            self._safe_log(self._logger.error, message, *args, **kwargs)
        else:
            self._safe_log(self._logger.error, str(message), *args, **kwargs)
    
    def success(self, message: str, *args, **kwargs):
        """Success message logging with bilingual support."""
        bilingual_msg = f"✅ 成功 Success: {message}"
        if hasattr(self._logger, 'success'):
            self._safe_log(self._logger.success, bilingual_msg, *args, **kwargs)
        else:
            self._safe_log(self._logger.info, bilingual_msg, *args, **kwargs)
    
    def init_success(self, component: str, details: str = ""):
        """Log successful initialization with bilingual support."""
        msg = f"✅ {component} 初始化成功 Initialized Successfully"
        if details:
            msg += f" - {details}"
        self.info(msg)
    
    def mode_activated(self, mode: str, validation: bool = True):
        """Log mode activation with bilingual support."""
        validation_text = "带验证 with validation" if validation else "仅提取 extract only"
        msg = f"🎯 {mode} 模式已激活 Mode Activated ({validation_text})"
        self.info(msg)
    
    def scan_progress(self, current: int, total: int, item_type: str = "items"):
        """Log scan progress with bilingual support."""
        percentage = (current / total * 100) if total > 0 else 0
        msg = f"📊 扫描进度 Scan Progress: {percentage:.1f}% ({current}/{total} {item_type})"
        self.info(msg)
    
    def key_found(self, key_type: str, count: int, status: str = ""):
        """Log key discovery with bilingual support."""
        status_text = f" - {status}" if status else ""
        msg = f"🔑 发现密钥 Keys Found: {count} {key_type} keys{status_text}"
        self.info(msg)
    
    def validation_result(self, key_type: str, valid: int, total: int):
        """Log validation results with bilingual support."""
        msg = f"🔍 验证结果 Validation Result: {valid}/{total} {key_type} keys valid"
        self.info(msg)
    
    def github_tokens(self, count: int):
        """Log GitHub token configuration with bilingual support."""
        msg = f"🔑 GitHub 令牌 Tokens: {count} 个已配置 configured"
        self.info(msg)
    
    def scan_mode_summary(self, extractors: list, validators: list):
        """Log scan mode summary with bilingual support."""
        msg = f"🔧 扫描配置 Scan Config: {len(extractors)} 提取器 extractors, {len(validators)} 验证器 validators"
        self.info(msg)
    
    def network_request(self, service: str, action: str):
        """Log network requests with bilingual support."""
        msg = f"🌐 网络请求 Network Request: {service} - {action}"
        self.info(msg)
    
    def rate_limit_warning(self, service: str, retry_after: int = 0):
        """Log rate limit warnings with bilingual support."""
        retry_text = f" 重试间隔 retry after {retry_after}s" if retry_after > 0 else ""
        msg = f"⏱️ 频率限制 Rate Limited: {service}{retry_text}"
        self.warning(msg)
    
    def file_operation(self, operation: str, path: str, status: str = "success"):
        """Log file operations with bilingual support."""
        status_map = {
            "success": "成功 success",
            "failed": "失败 failed", 
            "created": "已创建 created",
            "loaded": "已加载 loaded"
        }
        status_text = status_map.get(status, status)
        msg = f"📁 文件操作 File Operation: {operation} {path} - {status_text}"
        self.info(msg)
    
    def startup_banner(self):
        """Display startup banner with bilingual support."""
        self.separator("🚀 HAJIMI KING 启动中 STARTING 🚀")
        self.info(f"⏰ 启动时间 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def scan_complete(self, total_files: int, total_keys: int, valid_keys: int):
        """Log scan completion with bilingual support."""
        msg = f"🏁 扫描完成 Scan Complete: {total_files} 文件 files, {total_keys} 密钥 keys, {valid_keys} 有效 valid"
        self.info(msg)
    
    def progress(self, message: str, current: int, total: int, *args, **kwargs):
        """Progress logging."""
        if hasattr(self._logger, 'progress'):
            self._safe_log(self._logger.progress, message, current, total, *args, **kwargs)
        else:
            percentage = (current / total * 100) if total > 0 else 0
            msg = f"📈 进度 Progress {message} {percentage:.1f}% ({current}/{total})"
            self._safe_log(self._logger.info, msg, *args, **kwargs)

    def network(self, message: str, *args, **kwargs):
        """Network-related logging."""
        if hasattr(self._logger, 'network'):
            self._safe_log(self._logger.network, message, *args, **kwargs)
        else:
            msg = f"🌐 网络 Network {message}"
            self._safe_log(self._logger.info, msg, *args, **kwargs)

    def file_op(self, message: str, *args, **kwargs):
        """File operation logging."""
        if hasattr(self._logger, 'file_op'):
            self._safe_log(self._logger.file_op, message, *args, **kwargs)
        else:
            msg = f"📁 文件 File {message}"
            self._safe_log(self._logger.info, msg, *args, **kwargs)

    def key_extracted(self, key_type: str, count: int, repo: str, file_path: str):
        """Log immediate key extraction with source info."""
        msg = f"🔑 提取密钥 Extracted: {count} {key_type} keys from {repo}/{file_path}"
        self.info(msg)

    def key_validating(self, key_prefix: str, key_type: str):
        """Log key validation start."""
        msg = f"🔍 验证中 Validating: {key_prefix}... ({key_type})"
        self.info(msg)

    def key_validation_success(self, key_prefix: str, key_type: str):
        """Log successful key validation."""
        msg = f"✅ 验证成功 Valid: {key_prefix}... ({key_type})"
        self.success(msg)

    def key_validation_failed(self, key_prefix: str, key_type: str, reason: str):
        """Log failed key validation."""
        msg = f"❌ 验证失败 Invalid: {key_prefix}... ({key_type}) - {reason}"
        self.error(msg)

    def key_saved_immediately(self, key_prefix: str, file_path: str):
        """Log immediate key saving."""
        msg = f"💾 密钥已保存 Key Saved: {key_prefix}... → {file_path}"
        self.info(msg)

    def progress_summary(self, extracted: int, validated: int, valid: int):
        """Log current progress summary."""
        msg = f"📊 当前进度 Current Progress: 已提取 Extracted {extracted} keys, 已验证 Validated {validated} keys, 有效 Valid {valid} keys"
        self.info(msg)

    def output_files_info(self, mode: str, files: dict):
        """Log output file paths at startup."""
        self.separator(f"📁 {mode} 模式输出文件 Mode Output Files")
        for file_type, file_path in files.items():
            self.info(f"📄 {file_type}: {file_path}")

    def key_rejection_reason(self, key_prefix: str, key_type: str, reason: str):
        """Log specific reason for key rejection."""
        msg = f"🚫 密钥被拒 Key Rejected: {key_prefix}... ({key_type}) - {reason}"
        self.warning(msg)
    
    def rate_limit(self, message: str, *args, **kwargs):
        """Rate limit logging."""
        if hasattr(self._logger, 'rate_limit'):
            self._safe_log(self._logger.rate_limit, message, *args, **kwargs)
        else:
            msg = f"⏱️ 限制 Rate Limit {message}"
            self._safe_log(self._logger.warning, msg, *args, **kwargs)
    
    def separator(self, title: str = "", char: str = "=", width: int = 60):
        """Print separator line."""
        if hasattr(self._logger, 'separator'):
            try:
                self._logger.separator(title, char, width)
            except UnicodeEncodeError:
                # Fallback without emoji
                safe_title = self._remove_emoji(title)
                self._logger.separator(safe_title, char, width)
        else:
            safe_title = self._remove_emoji(title)
            if safe_title:
                title_formatted = f" {safe_title} "
                padding = (width - len(title_formatted)) // 2
                line = char * padding + title_formatted + char * padding
                if len(line) < width:
                    line += char
            else:
                line = char * width
            self._safe_log(self._logger.info, line)


# Create global logger instance
logger = Logger()