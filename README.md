# 🔑 APIKEY-king

> **多平台 AI API 密钥发现与验证工具 - Web 可视化版本**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](docker-compose.yml)

APIKEY-king 是一个专业的 AI API 密钥安全扫描工具，支持 **4 大主流 AI 平台**的密钥发现和实时验证，配备完整的 **Web 可视化界面**和 **SQLite 数据库**持久化。

---

## ⚡ 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/your-username/APIKEY-king.git
cd APIKEY-king

# 2. 启动服务
docker-compose up -d

# 3. 访问 Web 界面
浏览器打开: http://localhost:8000
默认密码: kyx200328
```

---

## ✨ 核心特性

### 🌐 Web 可视化界面

- **🔐 密码认证**: 默认密码 `kyx200328`（可修改），密码保存在数据库
- **⚙️ 灵活配置**: 
  - 可视化配置 GitHub Token、代理
  - **每个渠道独立开关**
  - **每个渠道自定义验证模型**
  - 扫描模式选择（全部/单平台）
  - **性能调优**（并发、延迟、超时、重试）
- **📊 实时监控**: 扫描文件数、发现密钥数、有效密钥数实时更新
- **📝 实时日志**: WebSocket 推送，彩色分类显示
- **🔑 密钥管理**: SQLite 数据库存储，表格展示、一键复制、CSV 导出
- **💾 数据持久化**: 所有配置和密钥保存在 SQLite 数据库

### 🔍 支持的 AI 平台

1. **Gemini** (`AIzaSy...`) - Google AI 密钥
2. **OpenRouter** (`sk-or-v1-...`) - OpenRouter 平台密钥
3. **ModelScope** (`ms-...`) - ModelScope 平台密钥
4. **SiliconFlow** (`sk-...`) - SiliconFlow 平台密钥

---

## 📖 使用指南

### 1️⃣ 启动服务

```bash
docker-compose up -d
```

### 2️⃣ 登录系统

- 访问 `http://localhost:8000`
- 输入密码：`kyx200328`

### 3️⃣ 配置扫描

在"扫描配置"区域：

1. **GitHub Tokens**（必填）：每行一个
   ```
   ghp_xxxxxxxxxxxxxxxxxxxx
   ghp_yyyyyyyyyyyyyyyyyyyy
   ```
   > 获取地址：https://github.com/settings/tokens

2. **代理地址**（推荐）：避免 IP 被封
   ```
   http://localhost:1080
   ```

3. **扫描模式**：选择全部平台或单平台

4. **渠道验证配置**（灵活配置）：
   - **Gemini验证**：勾选启用，设置模型（如 `gemini-2.0-flash-exp`）
   - **OpenRouter验证**：勾选启用，设置模型（如 `deepseek/deepseek-chat-v3:free`）
   - **ModelScope验证**：勾选启用，设置模型（如 `Qwen/Qwen2-1.5B-Instruct`）
   - **SiliconFlow验证**：勾选启用，设置模型（如 `Qwen/Qwen2.5-7B-Instruct`）

5. **性能配置**（按需调优）：
   - **最大并发文件数**：1-20（默认5）
   - **请求间隔**：0-10秒（默认1秒）
   - **GitHub超时**：10-120秒（默认30秒）
   - **验证超时**：10-120秒（默认30秒）
   - **最大重试次数**：0-10次（默认3次）

6. 点击"保存配置"

### 4️⃣ 开始扫描

1. 点击"开始扫描"按钮
2. 观察实时日志和统计数据
3. 在"发现的密钥"区域查看结果

### 5️⃣ 管理密钥和系统

**密钥管理：**
- **查看记忆**：查看已处理的查询和文件数量
- **复制密钥**：点击"复制"按钮
- **导出数据**：点击"导出 CSV"下载所有密钥
- **刷新列表**：点击"刷新"更新数据
- **清除记忆**：点击"清除记忆"按钮（橙色），重新开始扫描

**系统设置：**
- **修改密码**：点击右上角"修改密码"，安全管理登录密码
- **退出登录**：点击右上角退出图标

---

## 🎯 灵活配置说明

### 渠道独立配置

每个 AI 平台渠道都可以**独立配置**：

- ✅ **启用/禁用**: 勾选框控制是否启用该渠道的验证
- ⚙️ **验证模型**: 为每个渠道指定不同的验证模型
- 🎯 **灵活组合**: 可以只启用某些渠道，节省 API 额度

### 推荐模型配置

| 平台 | 推荐模型 | 说明 |
|------|---------|------|
| Gemini | `gemini-2.0-flash-exp` | 最快的免费模型 |
| OpenRouter | `deepseek/deepseek-chat-v3:free` | 免费模型 |
| ModelScope | `Qwen/Qwen2-1.5B-Instruct` | 轻量级模型 |
| SiliconFlow | `Qwen/Qwen2.5-7B-Instruct` | 高效模型 |

### 配置示例

**场景一：只验证 Gemini**
- ✅ Gemini 验证
- ❌ OpenRouter 验证
- ❌ ModelScope 验证
- ❌ SiliconFlow 验证

**场景二：全部验证，自定义模型**
- ✅ Gemini → `gemini-1.5-flash`
- ✅ OpenRouter → `google/gemini-2.0-flash-exp:free`
- ✅ ModelScope → `Qwen/Qwen2.5-3B-Instruct`
- ✅ SiliconFlow → `deepseek-ai/DeepSeek-V3`

---

## 💾 数据库持久化

### 数据库表结构

所有数据保存在 **单个 SQLite 文件**（`data/apikey.db`）：

| 表名 | 说明 | 功能 |
|------|------|------|
| **system_settings** | 系统设置（密码哈希等） | 系统配置 |
| **config** | GitHub Token、代理、验证器、性能配置 | 用户配置 |
| **api_keys** | 发现的所有 API 密钥 | 密钥存储+去重 |
| **scan_logs** | 扫描日志 | 日志记录 |
| **scan_stats** | 扫描统计数据 | 统计分析 |
| **processed_queries** | 已处理的查询 | 🧠 记忆功能 |
| **scanned_shas** | 已扫描文件SHA | 🧠 去重功能 |

### 🧠 智能记忆功能

系统会自动记住扫描进度，避免重复工作：

**自动记忆：**
- ✅ 记住已处理的查询 → 不会重复搜索
- ✅ 记住已扫描的文件SHA → 不会重复下载和分析
- ✅ 断点续扫 → 重启后继续未完成的任务

**一键清除：**
- 点击 Web 界面的"清除记忆"按钮
- 清除所有已处理记录
- 下次扫描从头开始

**适用场景：**
- 长时间扫描可能中断 → 记忆功能避免重头开始
- 想要重新扫描所有内容 → 清除记忆重新开始
- 查询表达式更新 → 清除记忆使用新查询

### 数据库优势

- ✅ **单文件存储**：所有数据在一个 SQLite 文件中
- ✅ **零配置**：自动创建和初始化
- ✅ **轻量级**：无需额外数据库服务
- ✅ **持久化**：重启不丢失
- ✅ **可查询**：支持 SQL 查询和分析

---

## ❓ 常见问题

### Web 版本还需要 .env 文件吗？

**❌ 不需要！**

- 所有配置通过 **Web 界面**输入
- 配置保存在 **SQLite 数据库**中
- 无需任何配置文件即可启动

```bash
docker-compose up -d  # 直接启动，无需配置
```

### data 目录的作用？

**✅ 必需，但已精简**

**📂 精简的数据目录：**
```
data/
└── apikey.db     # 唯一的数据文件（存储所有数据）
```

**数据库包含 7 张表：**

| 表 | 说明 |
|---|------|
| `system_settings` | 系统设置（密码、配置） |
| `config` | 扫描配置（Token、代理、验证器、性能） |
| `api_keys` | 密钥（存储+去重） |
| `scan_logs` | 日志 |
| `scan_stats` | 统计 |
| `processed_queries` | 🧠 已处理查询（记忆） |
| `scanned_shas` | 🧠 已扫描文件（去重） |

**已删除的冗余文件：**
- ❌ `data/keys/` 目录
- ❌ `data/logs/` 目录
- ❌ `checkpoint.json`
- ❌ `scanned_shas.txt`

### 🧠 智能记忆功能

**自动记忆避免重复：**
- ✅ 记住已处理的查询 → 不重复搜索
- ✅ 记住已扫描的文件 → 通过SHA去重
- ✅ 断点续扫 → 重启后继续任务

**一键清除记忆：**

在 Web 界面点击"清除记忆"按钮（橙色），适用于：
- 💡 想要重新扫描所有内容
- 💡 更新了查询表达式
- 💡 清理数据库释放空间

---

## 🔧 高级配置

### 密码管理

**默认密码：** `kyx200328`

**首次启动：**
- 系统自动使用默认密码 `kyx200328`
- 密码哈希保存在数据库中

**修改密码：**
1. 登录后，点击右上角"修改密码"按钮
2. 输入当前密码和新密码
3. 确认修改（需重新登录）

**密码存储：**
- 密码以 SHA256 哈希存储在数据库（`system_settings` 表）
- 不存储明文密码
- 重启后密码不会重置

### 性能配置

在"扫描配置"中的"性能配置"区域：

| 配置项 | 默认值 | 说明 | 建议 |
|--------|--------|------|------|
| 最大并发文件数 | 5 | 同时处理的文件数量 | 5-10（避免限流） |
| 请求间隔 | 1.0秒 | 每个请求之间的延迟 | 网络好可减少到0.5秒 |
| GitHub超时 | 30秒 | GitHub API 请求超时 | 网络慢时增加到60秒 |
| 验证超时 | 30秒 | 密钥验证请求超时 | API慢时增加到60秒 |
| 最大重试次数 | 3次 | 失败后重试次数 | 网络不稳定时增加 |

**调优建议：**
- 🚀 **高速模式**：并发10 + 间隔0.5秒（需要好的代理）
- ⚖️ **平衡模式**：并发5 + 间隔1秒（推荐）
- 🐌 **保守模式**：并发2 + 间隔2秒（避免被限流）

### 自定义端口

修改 `docker-compose.yml`：
```yaml
ports:
  - "8080:8000"  # 将 8000 改为你想要的端口
```

### 数据库备份

```bash
# 备份数据库
cp data/apikey.db data/apikey.db.backup

# 恢复数据库
cp data/apikey.db.backup data/apikey.db
```

### 重新构建镜像

修改配置或更新代码后：

```bash
# 重新构建并启动
docker-compose up -d --build

# 强制重建（清理缓存）
docker-compose build --no-cache
docker-compose up -d
```

---

## 🐳 Docker 命令

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建
docker-compose up -d --build

# 查看状态
docker-compose ps
```

---

## 📊 数据管理

### 数据库表结构

SQLite 数据库（`data/apikey.db`）包含 7 张表：

| 表名 | 说明 | 操作 |
|------|------|------|
| `system_settings` | 系统设置（密码等） | Web 界面设置 |
| `config` | 配置数据（Token、性能等） | Web 界面配置 |
| `api_keys` | 发现的密钥 | 自动保存 |
| `scan_logs` | 扫描日志 | 自动记录 |
| `scan_stats` | 统计数据 | 自动更新 |
| `processed_queries` | 已处理查询（记忆） | 自动记录 |
| `scanned_shas` | 已扫描文件（去重） | 自动记录 |

### 查看数据库

```bash
# 进入容器
docker exec -it apikey-king sh

# 查询密钥数量
sqlite3 /app/data/apikey.db "SELECT COUNT(*) FROM api_keys;"

# 查看扫描记忆
sqlite3 /app/data/apikey.db "SELECT COUNT(*) FROM processed_queries;"
sqlite3 /app/data/apikey.db "SELECT COUNT(*) FROM scanned_shas;"

# 查看配置
sqlite3 /app/data/apikey.db "SELECT * FROM config;"
```

### 清理数据

**在 Web 界面操作：**
- 清除密钥：点击"发现的密钥"区域的操作按钮
- **清除记忆**：点击"清除记忆"按钮（橙色）

**或使用 API：**
```bash
# 清除所有密钥
curl -X DELETE http://localhost:8000/api/keys/clear \
  -H "Authorization: Bearer YOUR_TOKEN"

# 清除扫描记忆
curl -X DELETE http://localhost:8000/api/memory/clear \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🛠️ 故障排除

### 端口被占用
```bash
# 修改 docker-compose.yml 中的端口
ports:
  - "8080:8000"
```

### 数据库锁定
```bash
# 重启服务
docker-compose restart
```

### 配置未生效
- 检查是否点击了"保存配置"
- 查看浏览器控制台是否有错误
- 重新登录尝试

---

## 🤖 GitHub Actions 自动构建

项目已配置 GitHub Actions，推送代码时自动构建 Docker 镜像。

**构建配置：**
- 架构：仅 linux/amd64
- Dockerfile：单一 `Dockerfile`
- 优化：多层缓存，快速构建

**使用方式：**

```bash
# 推送触发自动构建
git push origin main

# 发布版本（自动构建标签）
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# 拉取并使用镜像
docker pull ghcr.io/your-username/apikey-king:latest
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data ghcr.io/your-username/apikey-king:latest
```

---

## 📐 技术架构

### 分层架构

```
前端层 (Vanilla JS + Tailwind CSS)
    ↓ HTTP/WebSocket
────────────────────────────────────
API 路由层 (routers/)
    ↓
业务逻辑层 (services/)
    ↓
数据访问层 (database/)
────────────────────────────────────
核心扫描引擎
    ├─ GitHub Service
    ├─ Extractors (4种)
    └─ Validators (4种，灵活配置)
```

### 后端目录结构（分层架构）

```
src/web/
├── api.py                  # FastAPI 主入口 (60行) ✨
│
├── schemas/                # 📋 数据模型层 (Pydantic)
│   ├── auth.py            # 认证模型
│   ├── config.py          # 配置模型（含性能配置）
│   └── scan.py            # 扫描模型
│
├── routers/                # 🚏 路由层 (HTTP 处理)
│   ├── auth.py            # POST /api/auth/login
│   ├── config.py          # GET/POST /api/config
│   ├── scan.py            # POST /api/scan/control
│   ├── keys.py            # GET/DELETE /api/keys
│   ├── logs.py            # GET /api/logs
│   ├── memory.py          # GET/DELETE /api/memory
│   └── settings.py        # POST /api/settings/change-password
│
├── services/               # 🔧 业务逻辑层
│   ├── auth_service.py    # 认证、密码管理、JWT
│   ├── config_service.py  # 配置管理（含性能配置）
│   ├── scan_service.py    # 扫描控制、线程管理
│   ├── key_service.py     # 密钥 CRUD
│   ├── log_service.py     # 日志管理、WebSocket
│   └── memory_service.py  # 记忆管理
│
├── database/               # 💾 数据访问层
│   └── database.py        # SQLite 封装 (7张表)
│
├── core/                   # ⚙️ 核心功能
│   └── scanner_runner.py  # 后台扫描任务执行器
│
└── websocket/              # 🔌 实时通信
    └── logs.py            # WS /ws/logs
```

**架构优势：**
- ✅ 主文件从 638 行精简到 60 行（减少 91%）
- ✅ 清晰的分层架构，职责明确
- ✅ 高内聚低耦合，易于维护
- ✅ 支持单元测试，质量可控
- ✅ 易于扩展新功能


### 技术栈

- **后端**: FastAPI + Uvicorn + WebSocket + SQLite
- **前端**: Vanilla JS + Tailwind CSS
- **数据库**: SQLite（轻量级，零配置，7张表）
- **认证**: JWT Token（24小时有效）+ 密码数据库存储
- **架构**: 分层架构 + 依赖注入 + 模块化
- **部署**: Docker（单文件）+ Docker Compose

---

## 🔒 安全注意事项

- ✅ 修改默认密码
- ✅ 定期备份数据库
- ✅ 使用代理避免 IP 封禁
- ✅ 定期清理密钥数据
- ✅ 不要暴露到公网

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

**享受使用 APIKEY-king！** 🎉✨
