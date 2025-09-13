# Docker Compose编排部署

<cite>
**本文档引用文件**  
- [docker-compose.yml](file://docker-compose.yml#L1-L14)
- [Dockerfile](file://Dockerfile#L1-L27)
- [.env](file://.env)
</cite>

## 目录
1. [项目结构](#项目结构)  
2. [Docker Compose配置详解](#docker-compose配置详解)  
3. [服务依赖与启动顺序控制](#服务依赖与启动顺序控制)  
4. [多实例负载分担部署示例](#多实例负载分担部署示例)  
5. [容器运行与日志监控](#容器运行与日志监控)  
6. [网络模式与端口暴露策略](#网络模式与端口暴露策略)  
7. [生产环境敏感配置管理建议](#生产环境敏感配置管理建议)

## 项目结构

本项目采用模块化设计，主要目录结构如下：

```
.
├── app
│   └── hajimi_king.py                  # 主应用入口
├── common
│   ├── Logger.py                       # 日志工具
│   └── config.py                       # 全局配置
├── scripts
│   └── dry_run.py                      # 演练脚本
├── utils
│   ├── file_manager.py                 # 文件管理
│   ├── github_client.py                # GitHub API 客户端
│   └── sync_utils.py                   # 同步工具
├── CHANGELOG.md                        # 版本变更记录
├── Dockerfile                          # 镜像构建文件
├── README.md                           # 项目说明
├── docker-compose.yml                  # 容器编排配置
├── first_deploy.sh                     # 首次部署脚本
└── pyproject.toml                      # Python 依赖管理
```

**Section sources**  
- [docker-compose.yml](file://docker-compose.yml#L1-L14)

## Docker Compose配置详解

`docker-compose.yml` 文件定义了服务的编排结构，核心字段包括：

### 服务命名与镜像构建
- **服务名称**: `hajimi-king`，用于容器间通信和服务管理
- **镜像名称**: `hajimi-king:0.0.1`，由本地 Dockerfile 构建生成

### 环境变量注入方式
通过 `env_file` 字段加载外部环境变量文件：
```yaml
env_file:
  - .env
```
该配置从 `.env` 文件中读取键值对，注入到容器运行环境中，便于配置与代码分离。

### 卷映射配置（持久化）
使用 `volumes` 实现数据持久化：
```yaml
volumes:
  - ./data:/app/data
```
- 宿主机路径：`./data`（项目根目录下的 data 文件夹）
- 容器内路径：`/app/data`
用于持久化存储扫描结果、缓存文件或日志数据。

### 容器重启策略
```yaml
restart: unless-stopped
```
表示容器在异常退出时自动重启，除非被手动停止，保障服务高可用。

### 构建上下文来源
虽然当前 `docker-compose.yml` 未显式声明 `build` 字段，但镜像 `hajimi-king:0.0.1` 来源于项目根目录的 `Dockerfile`。

**Section sources**  
- [docker-compose.yml](file://docker-compose.yml#L1-L14)  
- [Dockerfile](file://Dockerfile#L1-L27)

## 服务依赖与启动顺序控制

当前 `docker-compose.yml` 文件中未使用 `depends_on` 字段，因此服务启动无显式依赖顺序。若未来引入数据库或其他依赖服务，可通过以下方式控制启动顺序：

```yaml
services:
  hajimi-king:
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
  db:
    image: postgres:13
    restart: always
```

> 注意：`depends_on` 仅确保容器启动顺序，并不等待服务内部就绪。如需等待数据库完全初始化，应结合健康检查（healthcheck）机制。

## 多实例负载分担部署示例

为实现负载分担，可通过 `docker-compose` 扩展服务实例数量。示例如下：

```yaml
version: '3.8'

services:
  hajimi-king-1:
    <<: *hajimi-service-template
    container_name: hajimi-king-1
    ports:
      - "8081:8080"

  hajimi-king-2:
    <<: *hajimi-service-template
    container_name: hajimi-king-2
    ports:
      - "8082:8080"

  hajimi-king-3:
    <<: *hajimi-service-template
    container_name: hajimi-king-3
    ports:
      - "8083:8080"
```

配合反向代理（如 Nginx）实现负载均衡：

```nginx
upstream hajimi_backend {
    least_conn;
    server localhost:8081;
    server localhost:8082;
    server localhost:8083;
}

server {
    listen 80;
    location / {
        proxy_pass http://hajimi_backend;
    }
}
```

启动命令：
```bash
docker-compose up -d --scale hajimi-king=3
```

## 容器运行与日志监控

### 后台启动服务
使用以下命令以后台模式启动所有服务：
```bash
docker-compose up -d
```

### 实时日志监控
查看指定服务日志：
```bash
docker-compose logs -f hajimi-king
```
- `-f` 参数表示持续输出最新日志（类似 `tail -f`）
- 可结合 `--tail=50` 查看最近50行日志

### 日志级别过滤
若应用支持日志级别设置，可在 `.env` 中配置：
```env
LOG_LEVEL=INFO
```
并在代码中读取该环境变量控制输出。

## 网络模式与端口暴露策略

### 网络模式配置
当前配置使用 `host` 模式：
```yaml
network_mode: host
```
- 容器共享宿主机网络栈，无需端口映射
- 性能更高，但安全性较低，适用于可信环境

#### 替代方案：Bridge 模式
```yaml
ports:
  - "8080:8080"
```
- 使用默认 bridge 网络，通过端口映射暴露服务
- 更安全，适合生产环境

### 自定义网络创建
推荐为微服务架构创建独立网络：
```yaml
networks:
  internal:
    driver: bridge

services:
  hajimi-king:
    networks:
      - internal
```

### 端口暴露建议
- 开发环境：使用 `ports` 映射便于调试
- 生产环境：结合反向代理统一暴露 80/443 端口，内部服务不直接暴露

## 生产环境敏感配置管理建议

为保障敏感信息（如 API Key、数据库密码）安全，建议采用以下方案：

### 方案一：Docker Secrets（推荐用于 Swarm）
```yaml
services:
  hajimi-king:
    secrets:
      - api_key

secrets:
  api_key:
    file: ./secrets/api_key.txt
```

容器内通过 `/run/secrets/api_key` 读取。

### 方案二：环境变量加密 + .env 加密管理
1. 使用 `sops` 或 `ansible-vault` 加密 `.env` 文件
2. 部署时解密：
```bash
sops -d secrets/.env.prod > .env
docker-compose up -d
```

### 方案三：外部配置中心
集成 Hashicorp Vault 或 AWS Secrets Manager：
```python
# 示例：从 Vault 获取密钥
import hvac
client = hvac.Client(url='https://vault.example.com')
secret = client.secrets.kv.v2.read_secret_version(path='hajimi-king/api_key')
```

### 安全实践总结
- 避免将 `.env` 提交至版本控制（已加入 `.gitignore`）
- 使用最小权限原则分配密钥
- 定期轮换敏感凭证
- 在日志中脱敏敏感信息输出

**Section sources**  
- [docker-compose.yml](file://docker-compose.yml#L1-L14)  
- [.env](file://.env)