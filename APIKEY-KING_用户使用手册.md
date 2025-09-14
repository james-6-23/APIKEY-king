# 🎪 APIKEY-king 用户详细使用手册

> **版本**: 1.0.0  
> **更新时间**: 2025-01-13  
> **适用人群**: 安全研究人员、开发者、运维工程师

## 📋 目录

1. [项目简介](#项目简介)
2. [快速开始](#快速开始)
3. [安装部署](#安装部署)
4. [配置详解](#配置详解)
5. [使用方法](#使用方法)
6. [输出结果](#输出结果)
7. [高级功能](#高级功能)
8. [故障排除](#故障排除)
9. [最佳实践](#最佳实践)
10. [常见问题](#常见问题)

---

## 🎯 项目简介

**APIKEY-king** 是一个专业的API密钥发现与验证工具，能够自动从GitHub公开代码中搜索、提取和验证API密钥。

### 核心功能
- 🔍 **智能搜索**: 基于GitHub搜索API，支持自定义查询语法
- 🎯 **多平台支持**: 支持Gemini、OpenRouter、ModelScope三大AI平台
- ✅ **实时验证**: 自动验证密钥有效性，区分有效/无效/限流状态
- 📊 **智能过滤**: 自动过滤文档、示例、测试文件，专注有效代码
- 🔄 **断点续传**: 支持增量扫描，避免重复工作
- 🌐 **代理支持**: 内置代理轮换，提高访问稳定性

### 支持的密钥类型
| 平台 | 密钥格式 | 示例 | 验证方式 |
|------|---------|------|----------|
| **Google Gemini** | `AIzaSy` + 33位字符 | `AIzaSyABC123...` | Google AI API |
| **OpenRouter** | `sk-or-v1-` + 64位十六进制 | `sk-or-v1-abc123...` | OpenRouter API |
| **ModelScope** | `ms-` + UUID格式 | `ms-12345678-1234...` | ModelScope API |

---

## ⚡ 快速开始

### 最简启动（5分钟上手）

1. **获取GitHub Token**
   ```bash
   # 访问 https://github.com/settings/tokens
   # 创建具有 public_repo 权限的 Personal Access Token
   ```

2. **配置环境变量**
   ```bash
   # 复制配置模板
   cp .env.template .env
   
   # 编辑 .env 文件，填入你的GitHub Token
   echo "GITHUB_TOKENS=ghp_your_token_here" >> .env
   ```

3. **准备查询文件**
   ```bash
   # 使用默认查询模板
   cp queries.template data/queries.txt
   ```

4. **运行扫描**
   ```bash
   # 全面扫描模式（推荐）
   python -m src.main --mode compatible
   
   # 或使用快捷脚本
   python scripts/quick_launch.py all
   ```

5. **查看结果**
   ```bash
   # 查看有效密钥
   cat data/keys/keys_valid_*.txt
   
   # 查看详细日志
   tail -f data/logs/keys_valid_detail_*.log
   ```

---

## 🛠 安装部署

### 环境要求
- **Python**: 3.11 或更高版本
- **系统**: Windows/Linux/macOS
- **内存**: 建议 2GB 以上
- **网络**: 需要访问 GitHub API 和各平台验证API

### 方式一：本地部署

#### 1. 克隆项目
```bash
git clone <repository-url>
cd APIKEY-king
```

#### 2. 安装依赖
```bash
# 安装 uv 包管理器（推荐）
pip install uv

# 安装项目依赖
uv pip install -r pyproject.toml

# 或使用传统方式
pip install -r requirements.txt
```

#### 3. 创建数据目录
```bash
mkdir -p data/{keys,logs}
```

#### 4. 配置环境
```bash
# 复制配置文件
cp .env.template .env
cp queries.template data/queries.txt

# 编辑 .env 文件（必须配置 GITHUB_TOKENS）
nano .env
```

### 方式二：Docker部署

#### 1. 使用 Docker Compose（推荐）
```bash
# 创建配置文件
cp .env.template .env
# 编辑 .env 文件，填入 GITHUB_TOKENS

# 启动全面验证模式
docker-compose --profile full up -d

# 查看日志
docker-compose logs -f apikey-king-full
```

#### 2. 单容器运行
```bash
# 构建镜像
docker build -t apikey-king:latest .

# 运行容器
docker run -d \
  --name apikey-king \
  -e GITHUB_TOKENS=your_tokens_here \
  -v ./data:/app/data \
  apikey-king:latest
```

---

## ⚙️ 配置详解

### 配置文件层次结构
```
config/
├── default.yaml          # 默认配置
├── extractors/           # 提取器配置
│   ├── gemini.yaml
│   ├── modelscope.yaml
│   └── openrouter.yaml
├── presets/             # 预设配置
│   ├── gemini-only.env
│   ├── modelscope-only.env
│   └── openrouter-only.env
└── queries/             # 查询文件
    ├── gemini.txt
    ├── modelscope.txt
    └── openrouter.txt
```

### 核心配置项

#### 必填配置 ⚠️
```bash
# GitHub API访问令牌（必填）
GITHUB_TOKENS=ghp_token1,ghp_token2,ghp_token3
```

#### 基础配置
```bash
# 数据存储路径
DATA_PATH=./data

# 代理设置（可选，但强烈推荐）
PROXY=http://localhost:1080

# 扫描范围（天数）
DATE_RANGE_DAYS=730

# 查询文件路径
QUERIES_FILE=queries.txt

# 文件路径黑名单
FILE_PATH_BLACKLIST=readme,docs,doc/,.md,example,sample,tutorial,test,spec,demo,mock
```

#### 验证器配置
```bash
# Gemini 验证器
GEMINI_VALIDATION_ENABLED=true
HAJIMI_CHECK_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT=30.0

# OpenRouter 验证器
OPENROUTER_VALIDATION_ENABLED=true
OPENROUTER_TEST_MODEL=deepseek/deepseek-chat-v3.1:free
OPENROUTER_TIMEOUT=30.0

# ModelScope 验证器
MODELSCOPE_VALIDATION_ENABLED=true
MODELSCOPE_TEST_MODEL=Qwen/Qwen2-1.5B-Instruct
MODELSCOPE_TIMEOUT=30.0
```

### 查询语法配置

#### 基础查询示例
```bash
# data/queries.txt 文件内容
AIzaSy in:file
"https://openrouter.ai/api/v1" in:file
"https://api-inference.modelscope.cn/v1/" in:file
"openrouter.ai" AND "sk-or-v1-"
"api-inference.modelscope.cn" AND "ms-"
```

#### 高级查询技巧
```bash
# 针对特定文件类型
AIzaSy in:file extension:py
AIzaSy in:file extension:js

# 排除特定路径
AIzaSy in:file -path:test -path:example

# 组合查询
"AIzaSy" AND "google" AND "api" in:file

# 时间范围限制
AIzaSy in:file created:>2024-01-01
```

---

## 🚀 使用方法

### 扫描模式详解

#### 1. 兼容模式（推荐）
```bash
# 扫描所有三种平台的密钥并进行验证
python -m src.main --mode compatible

# 特点：
# ✅ 全面覆盖三种平台
# ✅ 实时验证密钥有效性
# ✅ 智能结果分类
# ⚠️ 扫描时间较长
```

#### 2. 单平台专项模式
```bash
# 仅扫描 Gemini 密钥
python -m src.main --mode gemini-only

# 仅扫描 OpenRouter 密钥
python -m src.main --mode openrouter-only

# 仅扫描 ModelScope 密钥
python -m src.main --mode modelscope-only

# 特点：
# ✅ 扫描速度快
# ✅ 资源消耗少
# ✅ 专注特定平台
```

#### 3. 预设配置模式
```bash
# 使用预设配置文件
python -m src.main --config-preset gemini-only
python -m src.main --config-preset openrouter-only
python -m src.main --config-preset modelscope-only

# 特点：
# ✅ 配置标准化
# ✅ 便于批量部署
# ✅ 减少配置错误
```

### 快捷启动脚本

#### Python 脚本
```bash
# 全面模式
python scripts/quick_launch.py all

# 单平台模式
python scripts/quick_launch.py gemini
python scripts/quick_launch.py openrouter
python scripts/quick_launch.py modelscope
```

#### Shell 脚本（Linux/Mac）
```bash
# 全面模式
./scripts/quick_scan.sh all

# 简写模式
./scripts/quick_scan.sh gm    # Gemini
./scripts/quick_scan.sh or    # OpenRouter
./scripts/quick_scan.sh ms    # ModelScope
```

#### 批处理脚本（Windows）
```cmd
# 运行快速扫描
scripts\quick_scan.bat
```

### Docker 运行模式

#### 多服务模式
```bash
# 启动全面验证服务
docker-compose --profile full up -d

# 启动单平台服务
docker-compose --profile gemini up -d
docker-compose --profile openrouter up -d
docker-compose --profile modelscope up -d

# 启动所有模式服务
docker-compose --profile all up -d

# 启动监控服务
docker-compose --profile monitor up -d
```

#### 服务管理
```bash
# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

---

## 📊 输出结果

### 文件结构
```
data/
├── keys/                    # 密钥文件
│   ├── keys_valid_20250113.txt      # 有效密钥
│   └── key_429_20250113.txt         # 限流密钥
├── logs/                    # 日志文件
│   ├── keys_valid_detail_20250113.log   # 详细日志
│   └── key_429_detail_20250113.log      # 限流详细日志
├── checkpoint.json          # 检查点文件
├── scanned_shas.txt        # 已扫描文件记录
└── queries.txt             # 查询配置
```

### 结果文件格式

#### 有效密钥文件 (keys_valid_*.txt)
```
AIzaSyABC123DEF456GHI789JKL012MNO345PQR678
sk-or-v1-abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
ms-12345678-1234-5678-9012-123456789012
```

#### 详细日志文件 (keys_valid_detail_*.log)
```
[2025-01-13 10:30:15] ✅ VALID | AIzaSyABC123... | https://github.com/user/repo/blob/main/config.py | Gemini API验证成功
[2025-01-13 10:30:16] ✅ VALID | sk-or-v1-abc... | https://github.com/user/repo/blob/main/api.js | OpenRouter API验证成功
[2025-01-13 10:30:17] ❌ INVALID | ms-invalid... | https://github.com/user/repo/blob/main/test.py | ModelScope API验证失败: 401 Unauthorized
[2025-01-13 10:30:18] ⏱️ RATE_LIMITED | AIzaSyXYZ... | https://github.com/user/repo/blob/main/app.py | Gemini API限流: 429 Too Many Requests
```

### 实时输出解读

#### 启动信息
```
🎪 Hajimi King 🏆 - API Key Discovery Tool
🧭 CLI Mode: compatible
📋 Loaded preset: compatible
✅ 配置 Configuration
✅ 服务 Services
✅ gemini 提取器 extractor
✅ modelscope 提取器 extractor
✅ openrouter 提取器 extractor
✅ gemini 验证器 validator
✅ openrouter 验证器 validator
✅ modelscope 验证器 validator
✅ 检查点 Checkpoint
```

#### 扫描进度
```
🔄 第 #1 轮 LOOP - 10:30:15
🔍 已加载 Loaded 5 个查询 queries
🔍 处理查询 Processing query #1/5: AIzaSy in:file
📊 已跳过 Skipped 15 个条目 items - 重复 Duplicate: 10, 文档 Docs: 5
✅ 查询 #1 完成 Query complete - 发现 Found 3 个文件包含密钥 files with keys
```

#### 结果统计
```
🏁 第 #1 轮完成 LOOP COMPLETE
✅ 已处理 Processed 150 个文件 files
✅ 发现 Found 25 个密钥 total keys
✅ 验证 Validated 18 个有效密钥 valid keys
📊 累计有效密钥 Total valid keys so far: 18
💤 休眠 10 秒等待下一轮 Sleeping 10 seconds before next loop...
```

---

## 🔧 高级功能

### 增量扫描与断点续传

#### 工作原理
- 系统自动记录已扫描的文件SHA值
- 支持程序中断后从断点恢复
- 避免重复扫描，提高效率

#### 检查点管理
```bash
# 查看检查点状态
cat data/checkpoint.json

# 清除检查点（重新开始扫描）
rm data/checkpoint.json data/scanned_shas.txt

# 手动保存检查点
# 程序会在以下情况自动保存：
# - 每处理20个文件
# - 每完成一个查询
# - 程序中断时
```

### 代理配置与轮换

#### 单代理配置
```bash
# HTTP代理
PROXY=http://localhost:1080

# SOCKS5代理
PROXY=socks5://localhost:1080

# 带认证的代理
PROXY=http://username:password@proxy.example.com:8080
```

#### 多代理轮换
```bash
# 多个代理用逗号分隔
PROXY=http://proxy1:1080,http://proxy2:1080,socks5://proxy3:1080

# 系统会自动轮换使用，提高成功率
```

### 自定义提取规则

#### 修改提取器配置
```yaml
# config/extractors/gemini.yaml
name: "gemini"
enabled: true

patterns:
  strict: "AIzaSy[A-Za-z0-9\\-_]{33}"
  loose: "AIzaSy[A-Za-z0-9\\-_]{30,40}"  # 宽松模式

# 启用宽松模式
use_loose_pattern: true

# 上下文验证
require_key_context: true
proximity_chars: 500
```

#### 添加新的查询规则
```bash
# 编辑 data/queries.txt
echo 'AIzaSy AND "google" AND "api_key" in:file' >> data/queries.txt
echo '"gemini" AND "AIzaSy" in:file extension:py' >> data/queries.txt
echo 'AIzaSy in:file -path:test -path:example' >> data/queries.txt
```

### 结果过滤与分析

#### 按状态分类查看
```bash
# 查看所有有效密钥
grep "✅ VALID" data/logs/keys_valid_detail_*.log

# 查看限流密钥
grep "⏱️ RATE_LIMITED" data/logs/keys_valid_detail_*.log

# 查看无效密钥
grep "❌ INVALID" data/logs/keys_valid_detail_*.log
```

#### 按平台分类统计
```bash
# 统计各平台密钥数量
echo "Gemini密钥数量: $(grep -c "AIzaSy" data/keys/keys_valid_*.txt)"
echo "OpenRouter密钥数量: $(grep -c "sk-or-v1-" data/keys/keys_valid_*.txt)"
echo "ModelScope密钥数量: $(grep -c "ms-" data/keys/keys_valid_*.txt)"
```

---

## 🔍 故障排除

### 常见错误及解决方案

#### 1. GitHub API限流
```
错误信息: API rate limit exceeded
解决方案:
- 添加更多GitHub Token
- 配置代理服务器
- 降低扫描频率
```

#### 2. 网络连接问题
```
错误信息: Connection timeout / Network unreachable
解决方案:
- 检查网络连接
- 配置代理服务器
- 检查防火墙设置
```

#### 3. 配置文件错误
```
错误信息: Configuration validation failed
解决方案:
- 检查 .env 文件格式
- 验证 GITHUB_TOKENS 有效性
- 确认配置文件路径正确
```

#### 4. 权限问题
```
错误信息: Permission denied
解决方案:
- 检查数据目录写权限
- 确认GitHub Token权限
- 检查文件系统权限
```

### 调试技巧

#### 启用详细日志
```bash
# 设置日志级别
export LOG_LEVEL=DEBUG

# 查看详细输出
python -m src.main --mode compatible 2>&1 | tee debug.log
```

#### 测试配置
```bash
# 测试GitHub Token
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# 测试代理连接
curl --proxy http://localhost:1080 https://api.github.com

# 验证配置文件
python -c "from src.services import ConfigService; print(ConfigService().load_config())"
```

#### 单步调试
```bash
# 使用单个查询测试
echo "AIzaSy in:file" > data/test_queries.txt
python -m src.main --mode gemini-only --queries data/test_queries.txt
```

---

## 💡 最佳实践

### 安全建议

#### 1. Token管理
- 使用最小权限原则，只授予 `public_repo` 权限
- 定期轮换GitHub Token
- 不要将Token提交到版本控制系统
- 使用环境变量或配置文件管理Token

#### 2. 结果处理
- 定期清理发现的密钥文件
- 对有效密钥进行安全存储
- 建立密钥泄露响应流程
- 记录和审计所有操作

#### 3. 网络安全
- 使用HTTPS代理
- 避免在公共网络运行
- 配置防火墙规则
- 监控网络流量

### 性能优化

#### 1. 扫描效率
```bash
# 使用多个GitHub Token提高API限额
GITHUB_TOKENS=token1,token2,token3,token4,token5

# 配置合适的扫描范围
DATE_RANGE_DAYS=365  # 减少扫描范围

# 优化查询语句
# 好的查询：AIzaSy in:file extension:py
# 差的查询：AIzaSy  # 过于宽泛
```

#### 2. 资源管理
```bash
# 限制内存使用
export PYTHONHASHSEED=0
ulimit -m 2097152  # 限制2GB内存

# 使用SSD存储提高I/O性能
DATA_PATH=/path/to/ssd/storage

# 定期清理日志文件
find data/logs -name "*.log" -mtime +7 -delete
```

#### 3. 并发优化
```bash
# Docker环境下限制资源
docker run --memory=2g --cpus=2 apikey-king:latest

# 使用多实例并行扫描（不同查询）
# 实例1: 扫描Gemini
# 实例2: 扫描OpenRouter
# 实例3: 扫描ModelScope
```

### 部署建议

#### 1. 生产环境
```bash
# 使用Docker Compose部署
# 配置健康检查
# 设置自动重启策略
# 配置日志轮转
# 监控资源使用
```

#### 2. 监控告警
```bash
# 监控指标
# - 扫描进度
# - 发现密钥数量
# - API调用成功率
# - 系统资源使用

# 告警条件
# - API限流超过阈值
# - 长时间无新发现
# - 系统资源不足
# - 网络连接异常
```

#### 3. 数据备份
```bash
# 定期备份重要数据
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# 同步到云存储
# rsync -av data/ user@backup-server:/backup/apikey-king/

# 版本控制配置文件
git add config/ .env.template
git commit -m "Update configuration"
```

---

## ❓ 常见问题

### Q1: 为什么扫描速度很慢？
**A**: 可能的原因和解决方案：
- GitHub API限流 → 添加更多Token
- 网络延迟 → 配置代理服务器
- 查询范围过大 → 优化查询语句
- 验证超时 → 调整超时设置

### Q2: 如何提高密钥发现率？
**A**: 优化策略：
- 使用更精准的查询语句
- 扩大扫描时间范围
- 添加更多查询模式
- 启用宽松匹配模式

### Q3: 发现的密钥都是无效的怎么办？
**A**: 检查以下方面：
- 验证器配置是否正确
- 网络连接是否正常
- 代理设置是否有效
- 密钥是否为测试/示例密钥

### Q4: 如何在企业环境中部署？
**A**: 企业部署建议：
- 使用内网代理服务器
- 配置企业防火墙规则
- 建立密钥管理流程
- 集成现有监控系统

### Q5: 程序占用内存过多怎么办？
**A**: 内存优化方案：
- 减少扫描范围
- 清理历史日志
- 使用Docker限制资源
- 定期重启程序

### Q6: 如何扩展支持新的API平台？
**A**: 扩展步骤：
1. 创建新的提取器类继承 `BaseExtractor`
2. 创建新的验证器类继承 `BaseValidator`
3. 添加配置文件到 `config/extractors/`
4. 更新查询文件添加新的搜索模式

---

## 📞 技术支持

### 获取帮助
- **GitHub Issues**: 报告Bug和功能请求
- **文档**: 查看项目README和技术文档
- **社区**: 参与讨论和经验分享

### 贡献代码
- Fork项目仓库
- 创建功能分支
- 提交Pull Request
- 参与代码审查

---

## 📚 附录

### A. 完整配置文件示例

#### .env 完整配置示例

```bash
# ================================
# APIKEY-king 完整配置文件示例
# ================================

# 必填配置 - GitHub访问令牌
GITHUB_TOKENS=ghp_token1,ghp_token2,ghp_token3

# 基础配置
DATA_PATH=./data
DATE_RANGE_DAYS=730
QUERIES_FILE=queries.txt

# 代理配置（强烈推荐）
PROXY=http://localhost:1080,socks5://localhost:1081

# 验证器配置
GEMINI_VALIDATION_ENABLED=true
HAJIMI_CHECK_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT=30.0

OPENROUTER_VALIDATION_ENABLED=true
OPENROUTER_TEST_MODEL=deepseek/deepseek-chat-v3.1:free
OPENROUTER_TIMEOUT=30.0

MODELSCOPE_VALIDATION_ENABLED=true
MODELSCOPE_TEST_MODEL=Qwen/Qwen2-1.5B-Instruct
MODELSCOPE_TIMEOUT=30.0

# 高级配置
FILE_PATH_BLACKLIST=readme,docs,doc/,.md,example,sample,tutorial,test,spec,demo,mock
VALID_KEY_PREFIX=keys/keys_valid_
RATE_LIMITED_KEY_PREFIX=keys/key_429_
VALID_KEY_DETAIL_PREFIX=logs/keys_valid_detail_
RATE_LIMITED_KEY_DETAIL_PREFIX=logs/key_429_detail_
SCANNED_SHAS_FILE=scanned_shas.txt

# ModelScope 提取配置（高级用户）
TARGET_BASE_URLS=https://api-inference.modelscope.cn/v1/,api-inference.modelscope.cn
MODELSCOPE_EXTRACT_ONLY=false
MS_USE_LOOSE_PATTERN=false
MS_PROXIMITY_CHARS=800
MS_REQUIRE_KEY_CONTEXT=false

# OpenRouter 提取配置（高级用户）
OPENROUTER_BASE_URLS=https://openrouter.ai/api/v1,openrouter.ai
OPENROUTER_EXTRACT_ONLY=false
OPENROUTER_USE_LOOSE_PATTERN=false
OPENROUTER_PROXIMITY_CHARS=800
OPENROUTER_REQUIRE_KEY_CONTEXT=false
```

#### docker-compose.yml 完整示例

```yaml
version: '3.8'

services:
  # 全面验证模式
  apikey-king-full:
    image: apikey-king:latest
    container_name: apikey-king-full
    restart: unless-stopped
    environment:
      - GITHUB_TOKENS=${GITHUB_TOKENS}
      - GEMINI_VALIDATION_ENABLED=true
      - OPENROUTER_VALIDATION_ENABLED=true
      - MODELSCOPE_VALIDATION_ENABLED=true
      - PROXY=${PROXY:-}
    volumes:
      - ./data/full:/app/data
      - ./config/queries:/app/config/queries:ro
    command: ["python", "-m", "src.main", "--mode", "compatible"]
    profiles: ["full", "all"]
    healthcheck:
      test: ["CMD", "python", "-c", "import os; exit(0 if os.path.exists('/app/data/checkpoint.json') else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 监控服务
  apikey-king-monitor:
    image: apikey-king:latest
    container_name: apikey-king-monitor
    restart: unless-stopped
    volumes:
      - ./data:/app/data:ro
    command: ["tail", "-f", "/app/data/*/logs/keys_valid_detail_*.log"]
    profiles: ["monitor"]

networks:
  default:
    driver: bridge

volumes:
  data:
    driver: local
```

### B. 查询语法参考

#### GitHub搜索语法完整参考
```bash
# 基础搜索
AIzaSy in:file                    # 在文件内容中搜索
AIzaSy in:path                    # 在文件路径中搜索

# 文件类型限制
AIzaSy in:file extension:py       # 只搜索Python文件
AIzaSy in:file extension:js       # 只搜索JavaScript文件
AIzaSy in:file extension:json     # 只搜索JSON文件

# 路径过滤
AIzaSy in:file path:config        # 只搜索config目录
AIzaSy in:file -path:test         # 排除test目录
AIzaSy in:file -path:example      # 排除example目录

# 仓库属性
AIzaSy in:file stars:>100         # 只搜索星标数>100的仓库
AIzaSy in:file size:>1000         # 只搜索大小>1000KB的仓库
AIzaSy in:file pushed:>2024-01-01 # 只搜索2024年后更新的仓库

# 组合查询
"AIzaSy" AND "google" in:file     # 同时包含两个关键词
"AIzaSy" OR "GOOGLE_API_KEY" in:file  # 包含任一关键词
"AIzaSy" NOT "example" in:file    # 包含AIzaSy但不包含example

# 高级模式
/AIzaSy[A-Za-z0-9_-]{33}/ in:file  # 使用正则表达式
"api_key" AND "AIzaSy" in:file language:python  # 指定编程语言
```

#### 平台特定查询示例
```bash
# Gemini 密钥查询
AIzaSy in:file
"AIzaSy" AND "google" in:file
"AIzaSy" AND "generative" in:file
"GOOGLE_API_KEY" in:file
"gemini" AND "api_key" in:file

# OpenRouter 密钥查询
"sk-or-v1-" in:file
"openrouter.ai" AND "sk-or-v1-" in:file
"https://openrouter.ai/api/v1" in:file
"OPENROUTER_API_KEY" in:file

# ModelScope 密钥查询
"ms-" in:file
"api-inference.modelscope.cn" AND "ms-" in:file
"https://api-inference.modelscope.cn/v1/" in:file
"MODELSCOPE_API_KEY" in:file
```

### C. 错误代码参考

#### HTTP状态码含义
| 状态码 | 含义 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | 正常处理 |
| 401 | 未授权 | 检查API密钥有效性 |
| 403 | 禁止访问 | 检查权限或IP限制 |
| 404 | 未找到 | 检查API端点URL |
| 429 | 请求过多 | 等待或使用代理 |
| 500 | 服务器错误 | 稍后重试 |
| 502 | 网关错误 | 检查网络连接 |
| 503 | 服务不可用 | 等待服务恢复 |

#### 验证器错误类型
```bash
# Gemini验证器错误
PERMISSION_DENIED: API未启用或密钥无权限
RESOURCE_EXHAUSTED: 配额耗尽
INVALID_ARGUMENT: 密钥格式错误
UNAUTHENTICATED: 密钥无效

# OpenRouter验证器错误
UNAUTHORIZED: 密钥无效
INSUFFICIENT_QUOTA: 余额不足
MODEL_NOT_FOUND: 模型不存在
RATE_LIMITED: 请求频率过高

# ModelScope验证器错误
INVALID_API_KEY: 密钥无效
MODEL_NOT_AVAILABLE: 模型不可用
QUOTA_EXCEEDED: 配额超限
SERVICE_UNAVAILABLE: 服务不可用
```

### D. 性能调优指南

#### 系统资源优化
```bash
# CPU优化
# 1. 使用多核处理器
# 2. 避免CPU密集型操作
# 3. 合理设置并发数

# 内存优化
# 1. 定期清理缓存
# 2. 限制批处理大小
# 3. 使用流式处理

# 磁盘I/O优化
# 1. 使用SSD存储
# 2. 定期清理日志
# 3. 压缩历史数据

# 网络优化
# 1. 使用CDN加速
# 2. 配置连接池
# 3. 启用HTTP/2
```

#### 扫描策略优化
```bash
# 查询优化
# 1. 使用精确的搜索词
# 2. 添加文件类型限制
# 3. 排除无关目录

# 时间范围优化
# 1. 根据需求调整扫描范围
# 2. 使用增量扫描
# 3. 定期清理检查点

# 验证优化
# 1. 合理设置超时时间
# 2. 使用轻量级测试模型
# 3. 启用结果缓存
```

### E. 安全最佳实践

#### 密钥管理安全
```bash
# 1. 访问控制
# - 限制文件访问权限
# - 使用专用用户账户
# - 配置防火墙规则

# 2. 数据加密
# - 加密存储敏感数据
# - 使用HTTPS传输
# - 定期更新加密密钥

# 3. 审计日志
# - 记录所有操作
# - 监控异常访问
# - 定期审查日志

# 4. 应急响应
# - 建立泄露响应流程
# - 准备密钥撤销机制
# - 制定恢复计划
```

#### 合规性考虑
```bash
# 1. 法律合规
# - 遵守当地法律法规
# - 尊重知识产权
# - 获得必要授权

# 2. 道德准则
# - 负责任的披露
# - 保护用户隐私
# - 避免恶意使用

# 3. 行业标准
# - 遵循安全标准
# - 实施最佳实践
# - 定期安全评估
```

---

## 📖 版本历史

### v1.0.0 (2025-01-13)
- ✅ 初始版本发布
- ✅ 支持三种AI平台密钥扫描
- ✅ 实现实时验证功能
- ✅ 添加Docker容器化支持
- ✅ 完善文档和使用指南

### 未来版本规划
- 🔄 Web界面开发
- 🔄 数据库后端支持
- 🔄 更多平台密钥支持
- 🔄 机器学习增强
- 🔄 分布式扫描支持

---

## 🤝 社区与支持

### 参与贡献
- **代码贡献**: 提交Pull Request
- **问题报告**: 创建GitHub Issue
- **文档改进**: 完善使用文档
- **功能建议**: 提出新功能想法

### 获取支持
- **技术问题**: GitHub Issues
- **使用咨询**: 社区讨论
- **商业支持**: 联系开发团队

---

**🎉 感谢使用 APIKEY-king！**

> 本工具仅供安全研究和合法用途使用。请遵守相关法律法规，负责任地使用本工具。

**最后更新**: 2025-01-13
**文档版本**: v1.0.0
