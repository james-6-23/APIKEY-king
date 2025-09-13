# 🎪 Hajimi King 🏆

[查看变更日志](CHANGELOG.md)

人人都是哈基米大王  👑  

注意： 本项目正处于beta期间，所以功能、结构、接口等等都有可能变化，不保证稳定性，请自行承担风险。

## ⚡ 快速开始（全面验证）

1) 配置 `.env`（不要提交到仓库）

```bash
# 复制配置模板
cp .env.template .env

# 编辑配置文件，填入你的 GitHub Token
# GITHUB_TOKENS=ghp_xxx1,ghp_xxx2
```

2) 准备查询 `data/queries.txt`

```bash
# 创建查询文件
cp queries.template data/queries.txt

# 或手动创建多种API密钥查询
mkdir -p data
echo 'AIzaSy in:file' > data/queries.txt
echo '"https://api-inference.modelscope.cn/v1/" in:file' >> data/queries.txt
echo '"https://openrouter.ai/api/v1" in:file' >> data/queries.txt
```

3) 运行（推荐使用全面验证模式）

```bash
# 全面扫描+验证模式（推荐）
python -m src.main --mode compatible

# 快捷脚本
python scripts/quick_launch.py all

# 专项模式
python -m src.main --mode modelscope-only
python -m src.main --mode openrouter-only  
python -m src.main --mode gemini-only
```

4) 查看输出

- 有效 Key 列表：`data/keys/keys_valid_YYYYMMDD.txt`
- 详细验证日志：`data/logs/keys_valid_detailYYYYMMDD.log`
- 验证统计：每个发现的密钥都会显示验证状态（✅有效/❌无效/⏱️限制）

## 🚀 核心功能

1. **GitHub搜索三种API Key** 🔍 - 基于自定义查询表达式搜索GitHub代码中的API密钥
   - **Gemini** keys (`AIzaSy...`) - Google AI 密钥
   - **OpenRouter** keys (`sk-or-v1-...`) - OpenRouter 平台密钥  
   - **ModelScope** keys (`ms-...`) - ModelScope 平台密钥
2. **🆕 实时验证功能** ✅ - 支持所有三种密钥类型的实时验证
   - **Gemini**: 通过 Google AI API 验证
   - **OpenRouter**: 通过 OpenRouter API 验证，使用免费模型
   - **ModelScope**: 通过 ModelScope Chat API 验证，使用轻量模型
3. **灵活模式切换** 🎛️ - 支持多种扫描模式快速切换
   - `--mode compatible`: 全面扫描+验证所有类型
   - `--mode gemini-only`: 专注 Gemini 密钥
   - `--mode openrouter-only`: 专注 OpenRouter 密钥
   - `--mode modelscope-only`: 专注 ModelScope 密钥
4. **代理支持** 🌐 - 支持多代理轮换，提高访问稳定性和成功率
5. **增量扫描** 📊 - 支持断点续传，避免重复扫描已处理的文件
6. **智能过滤** 🚫 - 自动过滤文档、示例、测试文件，专注有效代码

### 🔮 待开发功能 (TODO)

- [ ] **数据库支持保存key** 💾 - 支持将发现的API密钥持久化存储到数据库中
- [ ] **API、可视化展示抓取的key列表** 📊 - 提供API接口和可视化界面获取已抓取的密钥列表
- [ ] **付费key检测** 💰 - 额外check下付费key

## 📋 目录 🗂️

- [本地部署](#-本地部署) 🏠
- [Docker部署](#-docker部署) 🐳
- [配置变量说明](#-配置变量说明) ⚙️

---

## 🖥️ 本地部署 🚀

### 1. 环境准备 🔧

```bash
# 确保已安装Python
python --version

# 安装uv包管理器（如果未安装）
pip install uv
```

### 2. 项目设置 📁

```bash
# 克隆项目
git clone <repository-url>
cd APIKEY-king

# 复制配置文件
cp .env.template .env

# 复制查询文件
cp queries.template data/queries.txt
```

### 3. 配置环境变量 🔑

编辑 `.env` 文件，**必须**配置GitHub Token：

```bash
# 必填：GitHub访问令牌
GITHUB_TOKENS=ghp1,ghp2,ghp3

# 可选：其他配置保持默认值即可
```

> 💡 **获取GitHub Token**：访问 [GitHub Settings > Tokens](https://github.com/settings/tokens)，创建具有 `public_repo` 权限的访问令牌 🎫

### 4. 安装依赖并运行 ⚡

```bash
# 安装项目依赖
uv pip install -r pyproject.toml

# 创建数据目录
mkdir -p data

# 🆕 全面扫描+验证模式（推荐）
python -m src.main --mode compatible

# 🆕 快捷启动脚本
python scripts/quick_launch.py all              # 全面模式
python scripts/quick_launch.py gemini           # 仅 Gemini
python scripts/quick_launch.py openrouter       # 仅 OpenRouter  
python scripts/quick_launch.py modelscope       # 仅 ModelScope

# 🆕 Shell 脚本快捷方式 (Linux/Mac)
./scripts/quick_scan.sh all                     # 全面模式
./scripts/quick_scan.sh gm                      # Gemini 简写
./scripts/quick_scan.sh or                      # OpenRouter 简写
./scripts/quick_scan.sh ms                      # ModelScope 简写

# 🆕 配置预设模式
python -m src.main --config-preset gemini-only
python -m src.main --config-preset openrouter-only
python -m src.main --config-preset modelscope-only
```

### 5. 本地运行管理 🎮

```bash
# 查看日志文件
tail -f data/keys/keys_valid_detail_*.log

# 查看找到的有效密钥
cat data/keys/keys_valid_*.txt

# 停止程序
Ctrl + C
```

---

## 🐳 Docker部署 🌊

### 方式一：使用环境变量

```yaml
version: '3.8'
services:
  hajimi-king:
    image: ghcr.io/gakkinoone/hajimi-king:latest
    container_name: hajimi-king
    restart: unless-stopped
    environment:
      # 必填：GitHub访问令牌
      - GITHUB_TOKENS=ghp_your_token_here_1,ghp_your_token_here_2
      # 可选配置
      - HAJIMI_CHECK_MODEL=gemini-2.5-flash
      - QUERIES_FILE=queries.txt
    volumes:
      - ./data:/app/data
    working_dir: /app
```

### 方式二：使用.env文件

```yaml
version: '3.8'
services:
  hajimi-king:
    image: ghcr.io/gakkinoone/hajimi-king:latest
    container_name: hajimi-king
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    working_dir: /app
```

创建 `.env` 文件（参考 `.env.template`）：
```bash
# 复制配置模板
cp .env.template .env
# 编辑配置文件，填入你的GitHub Token
```

### 启动服务

```bash
# 创建数据目录和查询文件
mkdir -p data
echo "AIzaSy in:file" > data/queries.txt

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### Docker 场景下的 .env 示例（支持 ModelScope 和 OpenRouter）

```bash
# GitHub 访问令牌（必填）
GITHUB_TOKENS=ghp_xxx1,ghp_xxx2

# 数据卷挂载到容器内路径（compose 已映射 /app/data）
DATA_PATH=/app/data

# ModelScope 提取配置
TARGET_BASE_URLS=https://api-inference.modelscope.cn/v1/,api-inference.modelscope.cn
MODELSCOPE_EXTRACT_ONLY=true

# OpenRouter 提取配置
OPENROUTER_BASE_URLS=https://openrouter.ai/api/v1,openrouter.ai
OPENROUTER_EXTRACT_ONLY=true

# 可选：宽松匹配与距离约束（召回不足时再开启）
# MS_USE_LOOSE_PATTERN=true
# MS_PROXIMITY_CHARS=800
# MS_REQUIRE_KEY_CONTEXT=true
# OPENROUTER_USE_LOOSE_PATTERN=true
# OPENROUTER_PROXIMITY_CHARS=800
```

### 代理配置

强烈建议使用！GITHUB、GEMINI 访问长时间高频都会BAN IP

如果需要使用代理访问GitHub或Gemini API，推荐使用本地WARP代理：

> 🌐 **代理方案**：[warp-docker](https://github.com/cmj2002/warp-docker) - 本地WARP代理解决方案

在 `.env` 文件中配置：
```bash
# 多个代理使用逗号分隔
PROXY=http://localhost:1080
```

---

## ⚙️ 配置变量说明 📖

以下是所有可配置的环境变量，在 `.env` 文件中设置：

### 🔴 必填配置 ⚠️

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `GITHUB_TOKENS` | GitHub API访问令牌，多个用逗号分隔 🎫 | `ghp_token1,ghp_token2` |

### 🟡 重要配置（建议了解）🤓

| 变量名 | 默认值                | 说明                                              |
|--------|--------------------|-------------------------------------------------|
| `PROXY` | 空 | 代理服务器地址，支持多个（逗号分隔）和账密认证，格式：`http://user:pass@proxy:port` 🌐 |
| `DATA_PATH` | `/app/data`        | 数据存储目录路径 📂                                     |
| `DATE_RANGE_DAYS` | `730`              | 仓库年龄过滤（天数），只扫描指定天数内的仓库 📅                       |
| `QUERIES_FILE` | `queries.txt`      | 搜索查询配置文件路径（表达式严重影响搜索的高效性) 🎯                    |

### 🆕 验证功能配置 ✅

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `GEMINI_VALIDATION_ENABLED` | `true` | 是否启用 Gemini 密钥验证 🧠 |
| `HAJIMI_CHECK_MODEL` | `gemini-2.5-flash` | Gemini 验证使用的模型（建议用最快的模型） 🤖 |
| `GEMINI_TIMEOUT` | `30.0` | Gemini 验证超时时间（秒）⏱️ |
| `OPENROUTER_VALIDATION_ENABLED` | `true` | 是否启用 OpenRouter 密钥验证 🚀 |
| `OPENROUTER_TEST_MODEL` | `deepseek/deepseek-chat-v3.1:free` | OpenRouter 验证使用的模型（建议用免费模型）🆓 |
| `OPENROUTER_TIMEOUT` | `30.0` | OpenRouter 验证超时时间（秒）⏱️ |
| `MODELSCOPE_VALIDATION_ENABLED` | `true` | 是否启用 ModelScope 密钥验证 🇨🇳 |
| `MODELSCOPE_TEST_MODEL` | `Qwen/Qwen2-1.5B-Instruct` | ModelScope 验证使用的模型（建议用轻量模型）💫 |
| `MODELSCOPE_TIMEOUT` | `30.0` | ModelScope 验证超时时间（秒）⏱️ |

### 🟢 可选配置（不懂就别动）😅

| 变量名                              | 默认值                                | 说明 |
|----------------------------------|------------------------------------|------|
| `VALID_KEY_PREFIX`               | `keys/keys_valid_`                 | 有效密钥文件名前缀 🗝️ |
| `RATE_LIMITED_KEY_PREFIX`        | `keys/key_429_`                    | 频率限制密钥文件名前缀 ⏰ |
| `VALID_KEY_DETAIL_PREFIX`        | `logs/keys_valid_detail_`          | 详细日志文件名前缀 📝 |
| `RATE_LIMITED_KEY_DETAIL_PREFIX` | `logs/key_429_detail_`             | 频率限制详细日志文件名前缀 📊 |
| `SCANNED_SHAS_FILE`              | `scanned_shas.txt`                 | 已扫描文件SHA记录文件名 📋 |
| `FILE_PATH_BLACKLIST`            | `readme,docs,doc/,.md,example,...` | 文件路径黑名单，逗号分隔 🚫 |

#### 🆕 API 密钥验证配置 ✅
现在支持三种密钥类型的实时验证：
- `GEMINI_VALIDATION_ENABLED`: 是否启用 Gemini 密钥验证（默认 true）
- `OPENROUTER_VALIDATION_ENABLED`: 是否启用 OpenRouter 密钥验证（默认 true）
- `MODELSCOPE_VALIDATION_ENABLED`: 是否启用 ModelScope 密钥验证（默认 true）
- `*_TIMEOUT`: 各验证器的超时时间配置
- `*_TEST_MODEL`: 验证时使用的测试模型（建议使用免费/轻量模型）

#### 传统提取配置（兼容性保留）
##### ModelScope 提取配置
- `TARGET_BASE_URLS`: 逗号分隔的 base_url 或域名，文件包含其一才会尝试提取（默认含 `https://api-inference.modelscope.cn/v1/`）。
- `MS_USE_LOOSE_PATTERN`: 是否使用宽松匹配（默认 false）。
- `MS_PROXIMITY_CHARS`: 与 base_url 的最大字符距离（仅宽松模式下建议设置 300–1000 以降噪）。
- `MS_REQUIRE_KEY_CONTEXT`: 是否要求附近包含 key/token/secret/authorization 等上下文词（默认 false）。

##### OpenRouter 提取配置
- `OPENROUTER_BASE_URLS`: 逗号分隔的 OpenRouter API 地址，文件包含其一才会尝试提取（默认含 `https://openrouter.ai/api/v1`）。
- `OPENROUTER_USE_LOOSE_PATTERN`: 是否使用宽松匹配模式（默认 false）。
- `OPENROUTER_PROXIMITY_CHARS`: 与 base_url 的最大字符距离（仅宽松模式下建议设置 300–1000 以降噪）。
- `OPENROUTER_REQUIRE_KEY_CONTEXT`: 是否要求附近包含 key/token/secret/authorization 等上下文词（默认 false）。

### 配置文件示例 💫

完整的 `.env` 文件示例（🆕 包含验证功能）：

```bash
# 必填配置
GITHUB_TOKENS=ghp_your_token_here_1,ghp_your_token_here_2

# 重要配置（可选修改）
DATA_PATH=/app/data
DATE_RANGE_DAYS=730
QUERIES_FILE=queries.txt
PROXY=

# 🆕 验证功能配置 ✅ 
# Gemini 验证
GEMINI_VALIDATION_ENABLED=true
HAJIMI_CHECK_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT=30.0

# OpenRouter 验证
OPENROUTER_VALIDATION_ENABLED=true
OPENROUTER_TEST_MODEL=deepseek/deepseek-chat-v3.1:free
OPENROUTER_TIMEOUT=30.0

# ModelScope 验证
MODELSCOPE_VALIDATION_ENABLED=true
MODELSCOPE_TEST_MODEL=Qwen/Qwen2-1.5B-Instruct
MODELSCOPE_TIMEOUT=30.0

# 高级配置（建议保持默认）
VALID_KEY_PREFIX=keys/keys_valid_
RATE_LIMITED_KEY_PREFIX=keys/key_429_
VALID_KEY_DETAIL_PREFIX=logs/keys_valid_detail_
RATE_LIMITED_KEY_DETAIL_PREFIX=logs/key_429_detail_
SCANNED_SHAS_FILE=scanned_shas.txt
FILE_PATH_BLACKLIST=readme,docs,doc/,.md,example,sample,tutorial,test,spec,demo,mock
```

### 查询配置文件 🔍

编辑 `queries.txt` 文件自定义搜索规则：

⚠️ **重要提醒**：query 是本项目的核心！好的表达式可以让搜索更高效，需要发挥自己的想象力！🧠💡

```bash
# GitHub搜索查询配置文件
# 每行一个查询语句，支持GitHub搜索语法
# 以#开头的行为注释，空行会被忽略

# 基础搜索
AIzaSy in:file
AizaSy in:file filename:.env
```

> 📖 **搜索语法参考**：[GitHub Code Search Syntax](https://docs.github.com/en/search-github/searching-on-github/searching-code) 📚  
> 🎯 **核心提示**：创造性的查询表达式是成功的关键，多尝试不同的组合！

---

## 🔒 安全注意事项 🛡️

- ✅ GitHub Token权限最小化（只需`public_repo`读取权限）🔐
- ✅ 定期轮换GitHub Token 🔄
- ✅ 不要将真实的API密钥提交到版本控制 🙈
- ✅ 定期检查和清理发现的密钥文件 🧹

💖 **享受使用 Hajimi King 的快乐时光！** 🎉✨🎊

