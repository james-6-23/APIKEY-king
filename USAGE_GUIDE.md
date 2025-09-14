# 📖 APIKEY-king 使用指南

## 🚀 快速上手

### 第一次使用（推荐）

```bash
# 1. 运行配置向导
python scripts/quick_setup.py

# 2. 按提示配置 GitHub Token 和代理
# 3. 选择扫描范围
# 4. 自动生成配置文件

# 5. 开始扫描
python -m src.main --mode compatible
```

### 手动配置

```bash
# 1. 复制配置模板
cp .env.simple .env

# 2. 编辑配置文件
# 必填：GITHUB_TOKENS=your_token_here
# 推荐：PROXY=http://localhost:1080

# 3. 开始扫描
python -m src.main --mode compatible
```

## 🎯 扫描模式详解

### 1. Compatible 模式（推荐）
```bash
python -m src.main --mode compatible
```
- **功能**: 扫描所有4种平台的密钥
- **验证**: 启用所有验证器
- **适用**: 全面安全审计
- **时间**: 30-60分钟
- **成本**: 中等（$0.01-0.10）

### 2. 单平台专项模式

#### Gemini 专项模式
```bash
python -m src.main --mode gemini-only
```
- **功能**: 仅扫描 Google AI 密钥
- **验证**: 使用 gemini-2.5-flash 模型
- **适用**: Google AI 平台专项检查
- **时间**: 10-20分钟
- **成本**: 低（$0.001-0.01）

#### OpenRouter 专项模式
```bash
python -m src.main --mode openrouter-only
```
- **功能**: 仅扫描 OpenRouter 密钥
- **验证**: 使用免费模型验证
- **适用**: 成本敏感的扫描
- **时间**: 10-20分钟
- **成本**: 零（使用免费模型）

#### ModelScope 专项模式
```bash
python -m src.main --mode modelscope-only
```
- **功能**: 仅扫描 ModelScope 密钥
- **验证**: 使用轻量模型验证
- **适用**: 国内 AI 平台检查
- **时间**: 10-20分钟
- **成本**: 低（轻量模型）

#### SiliconFlow 专项模式
```bash
python -m src.main --mode siliconflow-only
```
- **功能**: 仅扫描 SiliconFlow 密钥
- **验证**: 使用高效模型验证
- **适用**: SiliconFlow 平台专项检查
- **时间**: 10-20分钟
- **成本**: 低（高效模型）

## 📊 结果文件说明

### 输出目录结构
```
data/
├── keys/
│   ├── keys_valid_20241201.txt      # 有效密钥列表
│   └── key_429_20241201.txt         # 频率限制的密钥
├── logs/
│   ├── keys_valid_detail_20241201.log  # 详细验证日志
│   └── batch_summary_20241201.json     # 批次扫描摘要
└── checkpoint.json                   # 扫描进度检查点
```

### 验证状态说明
- ✅ **Valid**: 密钥有效且可正常使用
- ❌ **Invalid**: 密钥无效或已失效
- ⏱️ **Rate Limited**: API 频率限制
- 🌐 **Network Error**: 网络连接错误
- ⚠️ **Model Issue**: 密钥有效但测试模型不可用

## 🔧 高级配置

### 成本控制
```bash
# 仅提取不验证（零成本）
export GEMINI_VALIDATION_ENABLED=false
export OPENROUTER_VALIDATION_ENABLED=false
export MODELSCOPE_VALIDATION_ENABLED=false
export SILICONFLOW_VALIDATION_ENABLED=false

python -m src.main --mode compatible
```

### 性能优化
```bash
# 缩短扫描范围
export DATE_RANGE_DAYS=30

# 缩短超时时间
export GEMINI_TIMEOUT=15.0
export OPENROUTER_TIMEOUT=15.0

python -m src.main --mode compatible
```

### 自定义查询
```bash
# 使用自定义查询文件
export QUERIES_FILE=my_custom_queries.txt
python -m src.main --mode compatible
```

## 🛠️ 故障排除

### 常见问题

**Q: GitHub API 限制？**
```bash
# 使用多个 GitHub Token
GITHUB_TOKENS=token1,token2,token3
```

**Q: 网络连接问题？**
```bash
# 配置代理
PROXY=http://localhost:1080
```

**Q: 验证超时？**
```bash
# 增加超时时间
GEMINI_TIMEOUT=60.0
OPENROUTER_TIMEOUT=60.0
```

**Q: 发现密钥数量少？**
```bash
# 增加扫描范围
DATE_RANGE_DAYS=1095  # 3年

# 启用调试日志
LOG_LEVEL=DEBUG
```

### 调试模式
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python -m src.main --mode compatible

# 查看详细日志
tail -f data/logs/keys_valid_detail_*.log
```

## 📈 最佳实践

### 1. 安全使用
- 定期轮换 GitHub Token
- 不要将配置文件提交到版本控制
- 及时清理发现的密钥文件

### 2. 性能优化
- 使用代理避免 IP 被封
- 合理设置扫描范围
- 根据需求选择验证策略

### 3. 成本控制
- 优先使用免费验证模型
- 根据预算调整验证器开关
- 定期监控 API 使用量

### 4. 结果分析
- 定期检查扫描日志
- 分析密钥泄露模式
- 建立密钥管理规范

---

🎯 **更多帮助请查看项目文档或提交 Issue！**
