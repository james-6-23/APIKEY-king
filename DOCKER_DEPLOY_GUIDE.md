# 🐳 APIKEY-king Docker 部署指南

## 🚀 快速开始

### 1. 准备环境

```bash
# 克隆项目
git clone https://github.com/your-repo/APIKEY-king.git
cd APIKEY-king

# 创建环境变量文件
cp .env.template .env
nano .env  # 编辑配置
```

### 2. 配置 .env 文件

```bash
# 必填配置
GITHUB_TOKENS=ghp_your_token_1,ghp_your_token_2

# 可选：代理配置（推荐）
PROXY=http://localhost:1080

# 验证配置（可选，已有默认值）
GEMINI_VALIDATION_ENABLED=true
OPENROUTER_VALIDATION_ENABLED=true
MODELSCOPE_VALIDATION_ENABLED=true
```

### 3. 构建镜像

```bash
# 构建Docker镜像
docker build -t apikey-king:latest .

# 或使用Docker Compose构建
docker-compose build
```

## 🎯 三种部署模式

### 🌟 模式一：全面验证模式（推荐）

```bash
# 启动全面验证服务
docker-compose --profile full up -d

# 查看日志
docker-compose logs -f apikey-king-full

# 查看结果
ls data/full/keys/
tail -f data/full/logs/keys_valid_detail_*.log
```

**特点**：
- ✅ 同时扫描三种API密钥
- ✅ 完整的实时验证功能
- ✅ 最全面的安全检查
- 📊 数据存储在 `./data/full/` 目录

### 🧠 模式二：Gemini 专扫模式

```bash
# 启动Gemini专扫服务
docker-compose --profile gemini up -d

# 监控Gemini验证过程
docker logs -f apikey-king-gemini

# 查看Gemini密钥结果
cat data/gemini/keys/keys_valid_*.txt | grep "AIzaSy"
```

**特点**：
- 🎯 专注Google Gemini密钥
- ⚡ 使用gemini-2.5-flash快速验证
- 💰 成本控制的验证策略
- 📊 数据存储在 `./data/gemini/` 目录

### 🚀 模式三：OpenRouter 专扫模式

```bash
# 启动OpenRouter专扫服务
docker-compose --profile openrouter up -d

# 监控OpenRouter验证
docker logs -f apikey-king-openrouter

# 查看OpenRouter密钥结果
cat data/openrouter/keys/keys_valid_*.txt | grep "sk-or-v1-"
```

**特点**：
- 🎯 专注OpenRouter平台密钥
- 🆓 使用免费模型验证
- 🔄 低成本验证策略
- 📊 数据存储在 `./data/openrouter/` 目录

### 🇨🇳 模式四：ModelScope 专扫模式

```bash
# 启动ModelScope专扫服务
docker-compose --profile modelscope up -d

# 监控ModelScope验证
docker logs -f apikey-king-modelscope

# 查看ModelScope密钥结果
cat data/modelscope/keys/keys_valid_*.txt | grep "ms-"
```

**特点**：
- 🎯 专注ModelScope平台密钥
- 💫 使用轻量模型验证
- 🇨🇳 国内网络优化
- 📊 数据存储在 `./data/modelscope/` 目录

## 📊 多模式并行运行

### 同时运行所有专项模式

```bash
# 启动所有专项模式
docker-compose --profile modes up -d

# 查看所有服务状态
docker-compose ps

# 监控所有服务日志
docker-compose logs -f
```

### 启动监控服务

```bash
# 启动日志监控（可选）
docker-compose --profile monitor up -d

# 实时查看所有验证日志
docker logs -f apikey-king-monitor
```

## 🛠️ 高级配置

### 自定义查询文件

```bash
# 创建查询目录
mkdir -p config/queries

# Gemini专用查询
cat > config/queries/gemini.txt << EOF
AIzaSy in:file
"google.generativeai" AND "AIzaSy"
gemini filename:.env
"GOOGLE_API_KEY"
EOF

# OpenRouter专用查询  
cat > config/queries/openrouter.txt << EOF
"https://openrouter.ai/api/v1" in:file
"openrouter.ai" AND "sk-or-v1-"
openrouter filename:.env
"OPENROUTER_API_KEY"
EOF

# ModelScope专用查询
cat > config/queries/modelscope.txt << EOF
"https://api-inference.modelscope.cn/v1/" in:file
"api-inference.modelscope.cn" AND "ms-"
modelscope filename:.env
"MODELSCOPE_API_KEY"
EOF
```

### 代理配置

```bash
# 在.env文件中配置代理
echo "PROXY=http://localhost:1080" >> .env

# 或配置多个代理（轮换使用）
echo "PROXY=http://proxy1:1080,http://proxy2:1080" >> .env

# 带认证的代理
echo "PROXY=http://user:pass@proxy.example.com:1080" >> .env
```

### 数据卷管理

```bash
# 创建专用数据目录
mkdir -p data/{full,gemini,openrouter,modelscope}/{keys,logs}

# 设置权限
chmod -R 755 data/

# 清理旧数据（谨慎操作）
rm -rf data/*/keys/keys_valid_*.txt
rm -rf data/*/logs/*.log
```

## 🔧 运维操作

### 服务管理

```bash
# 查看运行状态
docker-compose ps

# 重启特定服务
docker-compose restart apikey-king-gemini

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 日志管理

```bash
# 查看特定服务日志
docker-compose logs apikey-king-full

# 实时跟踪日志
docker-compose logs -f --tail=100 apikey-king-openrouter

# 导出日志到文件
docker-compose logs --no-color > apikey-king.log
```

### 资源监控

```bash
# 查看容器资源使用
docker stats

# 查看镜像大小
docker images apikey-king

# 清理unused镜像
docker image prune
```

## 📈 性能优化

### 内存限制

```yaml
# 在docker-compose.yml中添加资源限制
services:
  apikey-king-full:
    # ... 其他配置
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### 并发控制

```bash
# 通过环境变量控制并发
docker-compose up -d \
  -e MAX_WORKERS=4 \
  -e BATCH_SIZE=50 \
  apikey-king-full
```

## 🔒 安全配置

### 网络隔离

```yaml
# 创建专用网络
networks:
  apikey-network:
    driver: bridge
    internal: true
```

### 只读挂载

```yaml
# 配置文件只读挂载
volumes:
  - ./config/queries/gemini.txt:/app/data/queries.txt:ro
  - /etc/localtime:/etc/localtime:ro
```

## 🚨 故障排查

### 常见问题

1. **服务无法启动**
```bash
# 检查Docker守护进程
sudo systemctl status docker

# 检查端口占用
netstat -tulpn | grep :8080

# 查看详细错误
docker-compose logs apikey-king-full
```

2. **权限问题**
```bash
# 修复数据目录权限
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

3. **网络问题**
```bash
# 测试GitHub连接
docker run --rm apikey-king:latest curl -I https://api.github.com

# 测试代理连接
docker run --rm -e PROXY=http://localhost:1080 apikey-king:latest curl --proxy $PROXY -I https://api.github.com
```

## 🎯 最佳实践

### 生产环境部署

```bash
# 1. 使用具体版本标签
docker-compose up -d apikey-king:v1.0.0

# 2. 配置自动重启
restart: unless-stopped

# 3. 设置健康检查
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s
  timeout: 10s
  retries: 3

# 4. 日志轮换
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 监控和告警

```bash
# 配置Prometheus监控端点（未来功能）
- METRICS_ENABLED=true
- METRICS_PORT=9090

# 配置钉钉/微信告警（未来功能）  
- ALERT_WEBHOOK_URL=https://your-webhook-url
```

---

🎉 **现在你已经掌握了 APIKEY-king 的完整 Docker 部署方案！**

可以根据需要选择合适的部署模式，灵活高效地进行 API 密钥发现和验证工作。