# Docker 部署指南

<cite>
**本文档引用的文件**
- [Dockerfile](file://Dockerfile)
- [docker-compose.yml](file://docker-compose.yml)
- [.env.template](file://.env.template)
- [DOCKER_DEPLOY_GUIDE.md](file://DOCKER_DEPLOY_GUIDE.md)
- [README.md](file://README.md)
</cite>

## 目录
1. [简介](#简介)
2. [镜像构建](#镜像构建)
3. [容器运行模式](#容器运行模式)
4. [数据卷与持久化](#数据卷与持久化)
5. [环境变量配置](#环境变量配置)
6. [多模式并行部署](#多模式并行部署)
7. [运维管理](#运维管理)
8. [常见问题](#常见问题)
9. [最佳实践](#最佳实践)

## 简介

APIKEY-king 是一个用于扫描和验证 GitHub 上 API 密钥的工具，支持 Gemini、OpenRouter 和 ModelScope 三种平台密钥的发现与实时验证。本指南详细说明如何通过 Docker 和 Docker Compose 部署该项目，涵盖镜像构建、容器运行、数据挂载、环境配置等核心内容。

**Section sources**
- [README.md](file://README.md#L0-L50)
- [DOCKER_DEPLOY_GUIDE.md](file://DOCKER_DEPLOY_GUIDE.md#L0-L20)

## 镜像构建

### 基础镜像选择
项目使用 `python:3.11-slim` 作为基础镜像，确保轻量化且兼容 Python 3.11 运行环境。

### 构建流程
1. 安装系统依赖（git、curl）
2. 安装 uv 包管理器以提升依赖安装效率
3. 复制 `pyproject.toml` 并使用 uv 安装 Python 依赖
4. 复制项目源码、脚本和配置文件
5. 创建数据目录并设置权限
6. 生成默认查询文件，支持三种 API 密钥搜索
7. 设置 `/app/data` 为数据卷，便于外部挂载
8. 暴露端口 8080（预留用于未来 Web 界面）
9. 默认启动命令为全面验证模式：`python -m src.main --mode compatible`

```bash
# 构建镜像
docker build -t apikey-king:latest .

# 或使用 Docker Compose 构建
docker-compose build
```

**Diagram sources**
- [Dockerfile](file://Dockerfile#L1-L52)

**Section sources**
- [Dockerfile](file://Dockerfile#L1-L52)
- [DOCKER_DEPLOY_GUIDE.md](file://DOCKER_DEPLOY_GUIDE.md#L30-L50)

## 容器运行模式

项目通过 `docker-compose.yml` 提供四种预设运行模式，满足不同扫描需求。

### 全面验证模式（推荐）
同时扫描并验证三种 API 密钥，适用于全面安全检查。

```yaml
service: apikey-king-full
command: ["python", "-m", "src.main", "--mode", "compatible"]
volumes:
  - ./data/full:/app/data
  - ./config/queries:/app/config/queries:ro
```

### Gemini 专扫模式
专注 Google Gemini 密钥扫描与验证，使用 `gemini-2.5-flash` 模型进行快速验证。

```yaml
service: apikey-king-gemini
command: ["python", "-m", "src.main", "--mode", "gemini-only"]
volumes:
  - ./data/gemini:/app/data
  - ./config/queries/gemini.txt:/app/data/queries.txt:ro
```

### OpenRouter 专扫模式
专注于 OpenRouter 平台密钥，使用免费模型进行低成本验证。

```yaml
service: apikey-king-openrouter
command: ["python", "-m", "src.main", "--mode", "openrouter-only"]
volumes:
  - ./data/openrouter:/app/data
  - ./config/queries/openrouter.txt:/app/data/queries.txt:ro
```

### ModelScope 专扫模式
针对 ModelScope 平台密钥优化，支持国内网络环境。

```yaml
service: apikey-king-modelscope
command: ["python", "-m", "src.main", "--mode", "modelscope-only"]
volumes:
  - ./data/modelscope:/app/data
  - ./config/queries/modelscope.txt:/app/data/queries.txt:ro
```

**Diagram sources**
- [docker-compose.yml](file://docker-compose.yml#L5-L80)

**Section sources**
- [docker-compose.yml](file://docker-compose.yml#L5-L80)
- [DOCKER_DEPLOY_GUIDE.md](file://DOCKER_DEPLOY_GUIDE.md#L55-L150)

## 数据卷与持久化

### 数据目录结构
所有模式均挂载独立数据目录，结构如下：

```
data/
├── keys/           # 存储有效密钥文件
└── logs/           # 存储详细验证日志
```

### 挂载策略
- **写入目录**：`./data/{mode}/` 映射到 `/app/data`，用于持久化扫描结果
- **只读挂载**：配置文件（如查询规则）以 `:ro` 方式挂载，防止容器修改
- **日志监控**：可选服务 `apikey-king-monitor` 挂载整个 `data/` 目录只读，用于实时日志跟踪

```bash
# 创建数据目录
mkdir -p data/{full,gemini,openrouter,modelscope}/{keys,logs}
chmod -R 755 data/
```

**Section sources**
- [docker-compose.yml](file://docker-compose.yml#L20-L80)
- [DOCKER_DEPLOY_GUIDE.md](file://DOCKER_DEPLOY_GUIDE.md#L180-L200)

## 环境变量配置

### 必填配置
| 变量名 | 说明 |
|--------|------|
| `GITHUB_TOKENS` | GitHub 访问令牌，多个用逗号分隔 |

### 验证功能开关
| 变量名 | 说明 |
|--------|------|
| `GEMINI_VALIDATION_ENABLED` | 是否启用 Gemini 密钥验证 |
| `OPENROUTER_VALIDATION_ENABLED` | 是否启用 OpenRouter 密钥验证 |
| `MODELSCOPE_VALIDATION_ENABLED` | 是否启用 ModelScope 密钥验证 |

### 模型与代理配置
| 变量名 | 说明 |
|--------|------|
| `HAJIMI_CHECK_MODEL` | Gemini 验证模型 |
| `OPENROUTER_TEST_MODEL` | OpenRouter 测试模型 |
| `MODELSCOPE_TEST_MODEL` | ModelScope 测试模型 |
| `PROXY` | 代理地址，支持多代理轮换 |

配置示例：
```bash
GITHUB_TOKENS=ghp_xxx1,ghp_xxx2
PROXY=http://localhost:1080
HAJIMI_CHECK_MODEL=gemini-2.5-flash
```

**Section sources**
- [.env.template](file://.env.template#L1-L49)
- [README.md](file://README.md#L300-L350)

## 多模式并行部署

支持通过 Docker Compose Profile 实现多模式并行运行。

### 启动所有专项模式
```bash
docker-compose --profile modes up -d
```

### 启动监控服务
```bash
docker-compose --profile monitor up -d
docker logs -f apikey-king-monitor
```

### 查看服务状态
```bash
docker-compose ps
docker-compose logs -f
```

此策略适用于需要高并发、分场景扫描的生产环境。

**Section sources**
- [docker-compose.yml](file://docker-compose.yml#L5-L97)
- [DOCKER_DEPLOY_GUIDE.md](file://DOCKER_DEPLOY_GUIDE.md#L155-L175)

## 运维管理

### 服务控制
```bash
# 查看状态
docker-compose ps

# 重启服务
docker-compose restart apikey-king-gemini

# 停止服务
docker-compose down

# 清理数据卷
docker-compose down -v
```

### 日志管理
```bash
# 查看日志
docker-compose logs apikey-king-full

# 实时跟踪
docker-compose logs -f --tail=100

# 导出日志
docker-compose logs --no-color > apikey-king.log
```

### 资源监控
```bash
# 查看资源使用
docker stats

# 清理镜像
docker image prune
```

**Section sources**
- [DOCKER_DEPLOY_GUIDE.md](file://DOCKER_DEPLOY_GUIDE.md#L210-L240)

## 常见问题

### 服务无法启动
```bash
# 检查 Docker 状态
sudo systemctl status docker

# 查看错误日志
docker-compose logs apikey-king-full
```

### 权限问题
```bash
# 修复数据目录权限
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

### 网络连接失败
```bash
# 测试 GitHub 连接
docker run --rm apikey-king:latest curl -I https://api.github.com

# 测试代理
docker run --rm -e PROXY=http://localhost:1080 apikey-king:latest curl --proxy $PROXY -I https://api.github.com
```

**Section sources**
- [DOCKER_DEPLOY_GUIDE.md](file://DOCKER_DEPLOY_GUIDE.md#L280-L300)

## 最佳实践

### 生产环境建议
- 使用具体版本标签而非 `latest`
- 配置 `restart: unless-stopped` 实现自动恢复
- 设置日志轮转防止磁盘占满
- 使用专用网络进行服务隔离

### 安全配置
- 配置文件使用只读挂载
- GitHub Token 仅需 `public_repo` 权限
- 定期轮换 Token
- 不将敏感信息提交至版本控制

### 性能优化
- 限制容器内存与 CPU 资源
- 使用代理提升访问稳定性
- 合理设置并发参数（`MAX_WORKERS`, `BATCH_SIZE`）

**Section sources**
- [DOCKER_DEPLOY_GUIDE.md](file://DOCKER_DEPLOY_GUIDE.md#L305-L372)
- [README.md](file://README.md#L380-L405)