# 🚀 SiliconFlow 集成指南

## 📋 概述

APIKEY-king 现已支持 **SiliconFlow** 平台的 API 密钥发现和验证！SiliconFlow 是一个高性能的 AI 推理平台，提供多种优质模型服务。

## 🎯 SiliconFlow 支持特性

### ✅ 密钥发现
- **密钥格式**: `sk-` 开头的小写字母密钥
- **上下文识别**: 自动识别 SiliconFlow API 相关代码
- **智能过滤**: 排除测试和示例代码中的假密钥

### ✅ 实时验证
- **API 验证**: 通过 SiliconFlow Chat Completions API 验证
- **高效模型**: 使用 `Qwen/Qwen2.5-72B-Instruct` 等高效模型
- **成本控制**: 最小 token 消耗策略
- **详细报告**: 提供验证状态和元数据

## 🚀 快速开始

### 1. 基础配置

```bash
# 复制简化配置模板
cp .env.simple .env

# 编辑配置文件
nano .env
```

**最小配置示例：**
```bash
# 必填：GitHub Token
GITHUB_TOKENS=your_github_token_here

# 推荐：代理设置
PROXY=http://localhost:1080

# 可选：扫描范围
DATE_RANGE_DAYS=365
```

### 2. 运行 SiliconFlow 专项扫描

```bash
# 仅扫描 SiliconFlow 密钥
python -m src.main --mode siliconflow-only

# 使用预设配置
python -m src.main --mode siliconflow-only --config-preset siliconflow-only

# 全面扫描（包含 SiliconFlow）
python -m src.main --mode compatible
```

### 3. 快速配置向导

```bash
# 运行配置向导（推荐新手使用）
python scripts/quick_setup.py
```

## 🔍 SiliconFlow 查询策略

### 预置查询模式
项目内置了针对 SiliconFlow 优化的查询策略：

```bash
# API URL 搜索
"https://api.siliconflow.cn/v1" in:file
"api.siliconflow.cn" in:file

# 上下文搜索
"sk-" AND "siliconflow" in:file
"OpenAI" AND "siliconflow" in:file

# 代码模式搜索
"client = OpenAI" AND "siliconflow" in:file
"base_url" AND "api.siliconflow.cn" in:file
```

### 自定义查询
您可以在 `config/queries/siliconflow.txt` 中添加自定义查询：

```bash
# 添加您的自定义查询
echo '"YOUR_API_KEY_FROM_CLOUD_SILICONFLOW_CN" in:file' >> config/queries/siliconflow.txt
```

## ⚙️ 高级配置

### SiliconFlow 专项配置

```bash
# 验证器配置
SILICONFLOW_VALIDATION_ENABLED=true
SILICONFLOW_TEST_MODEL=Qwen/Qwen2.5-72B-Instruct
SILICONFLOW_TIMEOUT=30.0

# 提取器配置
SILICONFLOW_BASE_URLS=https://api.siliconflow.cn/v1,api.siliconflow.cn,siliconflow.cn
SILICONFLOW_EXTRACT_ONLY=false
SILICONFLOW_USE_LOOSE_PATTERN=false
```

### 成本优化配置

```bash
# 仅提取不验证（零成本）
SILICONFLOW_EXTRACT_ONLY=true

# 缩短超时时间
SILICONFLOW_TIMEOUT=15.0

# 使用更轻量的模型（如果可用）
SILICONFLOW_TEST_MODEL=Qwen/Qwen2-1.5B-Instruct
```

## 📊 输出结果

### 扫描结果文件
```bash
data/
├── keys/
│   └── keys_valid_20241201.txt      # 有效的 SiliconFlow 密钥
├── logs/
│   └── keys_valid_detail_20241201.log  # 详细验证日志
└── checkpoint.json                   # 扫描进度
```

### 验证状态说明
- ✅ **Valid**: 密钥有效且可访问 SiliconFlow API
- ❌ **Unauthorized**: 密钥无效或未授权
- ⏱️ **Rate Limited**: API 频率限制
- ⚠️ **Model Issue**: 密钥有效但测试模型不可用
- 🌐 **Network Error**: 网络连接错误

## 🎯 使用场景

### 1. 安全审计
```bash
# 全面扫描所有平台（包括 SiliconFlow）
python -m src.main --mode compatible
```

### 2. SiliconFlow 专项检查
```bash
# 仅检查 SiliconFlow 密钥泄露
python -m src.main --mode siliconflow-only
```

### 3. 成本控制扫描
```bash
# 仅提取不验证（零成本）
export SILICONFLOW_EXTRACT_ONLY=true
python -m src.main --mode siliconflow-only
```

## 🔧 故障排除

### 常见问题

**Q: SiliconFlow 验证失败？**
A: 检查网络连接和代理设置，确保可以访问 `api.siliconflow.cn`

**Q: 发现的密钥数量少？**
A: 尝试启用宽松模式：`SILICONFLOW_USE_LOOSE_PATTERN=true`

**Q: 验证超时？**
A: 调整超时时间：`SILICONFLOW_TIMEOUT=60.0`

### 调试模式
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python -m src.main --mode siliconflow-only
```

## 🚀 最佳实践

1. **使用代理**: 避免 IP 被封禁
2. **合理配置超时**: 平衡速度和成功率
3. **定期扫描**: 及时发现新的密钥泄露
4. **成本控制**: 根据需求选择验证策略
5. **结果分析**: 定期检查扫描日志和结果

---

🎉 **SiliconFlow 集成让 APIKEY-king 支持更多 AI 平台，提供更全面的密钥安全检查！**
