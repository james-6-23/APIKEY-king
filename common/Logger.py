import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        # 为不同级别添加颜色和图标
        level_icons = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
        
        # 获取颜色和图标
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        icon = level_icons.get(record.levelname, '📝')
        
        # 检查是否支持颜色输出（终端环境）
        if not self._supports_color():
            color = reset = ''
        
        # 格式化时间
        formatted_time = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # 构建日志消息
        if record.levelname == 'ERROR':
            # 错误日志特殊格式
            message = f"{color}{icon} [{formatted_time}] {record.levelname}{reset}\n{color}┌{'─' * 50}{reset}\n{color}│ {record.getMessage()}{reset}\n{color}└{'─' * 50}{reset}"
        else:
            # 普通日志格式
            message = f"{color}{icon} [{formatted_time}] {record.getMessage()}{reset}"
        
        return message
    
    def _supports_color(self) -> bool:
        """检查终端是否支持颜色输出"""
        # Windows环境检查
        if os.name == 'nt':
            # 启用Windows终端颜色支持
            try:
                import colorama
                colorama.init()
                return True
            except ImportError:
                # 检查是否是新版本Windows Terminal
                return 'WT_SESSION' in os.environ or 'TERM_PROGRAM' in os.environ
        
        # Unix/Linux环境检查
        return hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()


class Logger:
    """优化的日志记录器"""
    
    def __init__(self, name: str = 'APIKEY-king', level: int = logging.INFO):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        
        # 避免重复添加处理器
        if not self._logger.handlers:
            self._setup_logger()
    
    def _setup_logger(self):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        
        # 文件处理器（可选）
        log_dir = Path('data/logs')
        if log_dir.exists():
            log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
            )
            self._logger.addHandler(file_handler)
        
        self._logger.addHandler(console_handler)
        
        # 阻止日志传播到根记录器
        self._logger.propagate = False
    
    def debug(self, message: str, *args, **kwargs):
        """调试级别日志"""
        self._logger.debug(str(message), *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """信息级别日志"""
        self._logger.info(str(message), *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """警告级别日志"""
        self._logger.warning(str(message), *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """错误级别日志"""
        self._logger.error(str(message), *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """严重错误级别日志"""
        self._logger.critical(str(message), *args, **kwargs)
    
    def success(self, message: str, *args, **kwargs):
        """成功消息（使用INFO级别，但带特殊格式）"""
        self._logger.info(f"✅ {message}", *args, **kwargs)
    
    def progress(self, message: str, current: int, total: int, *args, **kwargs):
        """进度日志"""
        percentage = (current / total * 100) if total > 0 else 0
        progress_bar = self._create_progress_bar(current, total)
        self._logger.info(f"📈 {message} {progress_bar} {percentage:.1f}% ({current}/{total})", *args, **kwargs)
    
    def network(self, message: str, *args, **kwargs):
        """网络相关日志"""
        self._logger.info(f"🌐 {message}", *args, **kwargs)
    
    def file_op(self, message: str, *args, **kwargs):
        """文件操作日志"""
        self._logger.info(f"📁 {message}", *args, **kwargs)
    
    def security(self, message: str, *args, **kwargs):
        """安全相关日志"""
        self._logger.warning(f"🔒 {message}", *args, **kwargs)
    
    def rate_limit(self, message: str, *args, **kwargs):
        """频率限制日志"""
        self._logger.warning(f"⏱️ {message}", *args, **kwargs)
    
    def separator(self, title: str = "", char: str = "=", width: int = 60):
        """打印分隔线"""
        if title:
            title_formatted = f" {title} "
            padding = (width - len(title_formatted)) // 2
            line = char * padding + title_formatted + char * padding
            if len(line) < width:
                line += char
        else:
            line = char * width
        
        self._logger.info(line)
    
    def _create_progress_bar(self, current: int, total: int, width: int = 20) -> str:
        """创建进度条"""
        if total <= 0:
            return "[" + "?" * width + "]"
        
        filled = int(width * current / total)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
    
    def set_level(self, level: int):
        """设置日志级别"""
        self._logger.setLevel(level)
        for handler in self._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                handler.setLevel(level)


# 创建全局日志实例
logger = Logger()
