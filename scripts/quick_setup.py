#!/usr/bin/env python3
"""
APIKEY-king 快速配置向导
简化用户配置流程，只需要配置核心选项
"""

import os
import sys
import shutil
from pathlib import Path


def print_banner():
    """打印欢迎横幅"""
    print("🎯 APIKEY-king 快速配置向导")
    print("=" * 50)
    print("让我们快速配置您的 APIKEY-king 环境！")
    print()


def get_github_tokens():
    """获取 GitHub tokens"""
    print("📝 GitHub Token 配置")
    print("获取地址: https://github.com/settings/tokens")
    print("需要权限: public_repo")
    print()
    
    tokens = input("请输入您的 GitHub Token(s)，多个用逗号分隔: ").strip()
    if not tokens:
        print("❌ GitHub Token 是必需的！")
        return get_github_tokens()
    
    return tokens


def get_proxy_config():
    """获取代理配置"""
    print("\n🌐 代理配置（强烈推荐）")
    print("代理可以避免 IP 被 GitHub 封禁，提高扫描成功率")
    
    use_proxy = input("是否使用代理？[Y/n]: ").strip().lower()
    if use_proxy in ['', 'y', 'yes']:
        proxy = input("请输入代理地址 (如 http://localhost:1080): ").strip()
        return proxy if proxy else ""
    
    return ""


def get_scan_range():
    """获取扫描范围配置"""
    print("\n📊 扫描范围配置")
    print("选择扫描时间范围：")
    print("[1] 快速扫描 (30天) - 适合测试")
    print("[2] 平衡扫描 (365天) - 推荐")
    print("[3] 全面扫描 (730天) - 最全面")
    
    choice = input("请选择 [1-3]: ").strip()
    
    range_map = {
        '1': 30,
        '2': 365,
        '3': 730
    }
    
    return range_map.get(choice, 365)


def create_config_file(tokens, proxy, date_range):
    """创建配置文件"""
    config_content = f"""# APIKEY-king 配置文件
# 由快速配置向导自动生成

# ==== 必填配置 ====
GITHUB_TOKENS={tokens}

# ==== 网络配置 ====
PROXY={proxy}

# ==== 扫描配置 ====
DATE_RANGE_DAYS={date_range}
DATA_PATH=./data

# ==== 验证器配置（默认全部启用）====
GEMINI_VALIDATION_ENABLED=true
OPENROUTER_VALIDATION_ENABLED=true
MODELSCOPE_VALIDATION_ENABLED=true
SILICONFLOW_VALIDATION_ENABLED=true

# ==== 高级配置 ====
GEMINI_TIMEOUT=30.0
OPENROUTER_TIMEOUT=30.0
MODELSCOPE_TIMEOUT=30.0
SILICONFLOW_TIMEOUT=30.0
FILE_PATH_BLACKLIST=readme,docs,doc/,.md,example,sample,tutorial,test,spec,demo,mock
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(config_content)


def show_usage_guide():
    """显示使用指南"""
    print("\n✅ 配置完成！")
    print("=" * 50)
    print("🚀 快速启动命令：")
    print()
    print("# 全面扫描（推荐）")
    print("python -m src.main --mode compatible")
    print()
    print("# 单平台扫描")
    print("python -m src.main --mode gemini-only")
    print("python -m src.main --mode openrouter-only")
    print("python -m src.main --mode modelscope-only")
    print("python -m src.main --mode siliconflow-only")
    print()
    print("📊 扫描结果将保存在 data/ 目录下")
    print("📝 详细日志请查看 data/logs/ 目录")
    print()
    print("🆘 需要帮助？运行: python -m src.main --help")


def main():
    """主函数"""
    print_banner()
    
    # 检查是否已有配置文件
    if os.path.exists('.env'):
        overwrite = input("检测到已有 .env 配置文件，是否覆盖？[y/N]: ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print("配置已取消")
            return
    
    # 收集配置信息
    tokens = get_github_tokens()
    proxy = get_proxy_config()
    date_range = get_scan_range()
    
    # 创建配置文件
    create_config_file(tokens, proxy, date_range)
    
    # 显示使用指南
    show_usage_guide()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n配置已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 配置过程中出现错误: {e}")
        sys.exit(1)
