#!/usr/bin/env python3
"""
OpenRouter 专用启动脚本
只扫描和提取 OpenRouter API 密钥
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.Logger import logger

def main():
    """启动 OpenRouter 专用扫描"""
    logger.info("🔥 启动 OpenRouter 专用扫描模式")
    logger.info("📋 配置说明：")
    logger.info("   - 只扫描 OpenRouter API 密钥")
    logger.info("   - 不扫描 ModelScope 或 Gemini 密钥")
    logger.info("   - 不进行密钥验证，仅提取和保存")
    logger.separator()
    
    # 设置 OpenRouter 专用环境变量
    os.environ['OPENROUTER_EXTRACT_ONLY'] = 'true'
    os.environ['MODELSCOPE_EXTRACT_ONLY'] = 'false'
    os.environ['TARGET_BASE_URLS'] = ''  # 禁用 ModelScope
    
    # 确保有 OpenRouter 配置
    if not os.environ.get('OPENROUTER_BASE_URLS'):
        os.environ['OPENROUTER_BASE_URLS'] = 'https://openrouter.ai/api/v1,openrouter.ai'
        logger.info("✅ 自动设置 OpenRouter base URLs")
    
    # 导入并运行主程序
    try:
        from app.hajimi_king import main as hajimi_main
        # 通过 sys.argv 传递命令行参数
        sys.argv.extend(['--mode', 'openrouter-only'])
        hajimi_main()
    except ImportError as e:
        logger.error(f"❌ 导入错误: {e}")
        logger.info("请确保所有依赖已安装：pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"❌ 运行错误: {e}")

if __name__ == "__main__":
    main()