# 🔥 全面密钥验证功能

现在 APIKEY-king 支持**完整的密钥验证功能**！不仅能搜索各种 API 密钥，还能实时验证其有效性。

## ✨ 支持的验证类型

| 密钥类型 | 格式 | 验证方式 | 成本 |
|----------|------|----------|------|
| **Gemini** | `AIzaSy...` | Google AI API | 免费额度 |
| **OpenRouter** | `sk-or-v1-...` | OpenRouter API | 免费模型 |
| **ModelScope** | `ms-...` | ModelScope API | 免费模型 |

## 🎯 验证模式使用

### 1. Gemini 专验模式
```bash
# 搜索并验证 Gemini 密钥
python -m src.main --mode gemini-only

# 使用预设配置
python -m src.main --mode gemini-only --config-preset gemini-only

# 快捷脚本
python scripts/quick_launch.py gemini
./scripts/quick_scan.sh gm
```

### 2. OpenRouter 专验模式
```bash
# 搜索并验证 OpenRouter 密钥
python -m src.main --mode openrouter-only

# 快捷脚本
python scripts/quick_launch.py openrouter
./scripts/quick_scan.sh or
```

### 3. 全验证模式（推荐）
```bash
# 搜索并验证 Gemini + OpenRouter + ModelScope
python -m src.main --mode compatible

# 快捷启动
python scripts/quick_launch.py all
```

## ⚙️ 验证配置

### 全局配置
```bash
# Gemini 验证设置
GEMINI_VALIDATION_ENABLED=true
GEMINI_TIMEOUT=30.0
HAJIMI_CHECK_MODEL=gemini-2.5-flash

# OpenRouter 验证设置
OPENROUTER_VALIDATION_ENABLED=true
OPENROUTER_TIMEOUT=30.0
OPENROUTER_TEST_MODEL=deepseek/deepseek-chat-v3.1:free

# ModelScope 验证设置
MODELSCOPE_VALIDATION_ENABLED=true
MODELSCOPE_TIMEOUT=30.0
MODELSCOPE_TEST_MODEL=Qwen/Qwen2-1.5B-Instruct

# 代理设置（推荐，避免频率限制）
PROXY=http://localhost:1080
```

### 按需禁用验证
```bash
# 只想提取，不验证
GEMINI_VALIDATION_ENABLED=false
OPENROUTER_VALIDATION_ENABLED=false

# 或者设置提取模式
OPENROUTER_EXTRACT_ONLY=true
```

## 📊 验证输出示例

### Gemini 验证
```
🔍 Found 2 suspected key(s), validating...
✅ VALID: AIzaSyDaGmWKa4JsXMe5jdbtF0JhI... (Model: gemini-2.5-flash)
❌ INVALID: AIzaSyInvalidKey123... (Status: unauthorized)
```

### OpenRouter 验证
```
🔍 Found 1 suspected key(s), validating...
✅ VALID: sk-or-v1-1234567890abcdef... (Model: deepseek/deepseek-chat-v3.1:free, Tokens: 2)
```

### ModelScope 验证
```
🔍 Found 1 suspected key(s), validating...
✅ VALID: ms-12345678-1234-1234-1234-123456789abc... (Model: Qwen/Qwen2-1.5B-Instruct, Tokens: 1)
```

### 混合验证（兼容模式）
```
🔍 Found 4 suspected key(s), validating...
✅ VALID: AIzaSyDaGmWKa4JsXMe5jdbtF0JhI... (Gemini - gemini-2.5-flash)
✅ VALID: sk-or-v1-1234567890abcdef... (OpenRouter - deepseek/deepseek-chat-v3.1:free)
✅ VALID: ms-12345678-1234-1234-1234-123456789abc... (ModelScope - Qwen/Qwen2-1.5B-Instruct)
⏱️ RATE LIMITED: AIzaSyRateLimited... (Retry after: 60s)
```

## 🔧 验证详细状态

### Gemini 验证状态
- ✅ **Valid**: 密钥有效且可访问 Gemini API
- ❌ **Unauthorized**: 密钥无效或未授权
- ⏱️ **Rate Limited**: Google API 频率限制
- 🚫 **Service Disabled**: Gemini API 服务未启用
- 🌐 **Network Error**: 网络连接问题

### OpenRouter 验证状态
- ✅ **Valid**: 密钥有效且可访问 OpenRouter
- ❌ **Unauthorized**: 密钥无效
- ⏱️ **Rate Limited**: OpenRouter 频率限制
- ⚠️ **Model Issue**: 密钥有效但测试模型不可用
- 🔧 **Bad Request**: 请求格式问题
- 🌐 **Network Error**: 连接错误

### ModelScope 验证状态
- ✅ **Valid**: 密钥有效且可访问 ModelScope API
- ❌ **Unauthorized**: 密钥无效或未授权
- ⏱️ **Rate Limited**: ModelScope API 频率限制
- 🚫 **Forbidden**: 访问被禁止，权限不足
- ⚠️ **Model Issue**: 密钥有效但测试模型不可用
- 🔧 **Bad Request**: 请求格式或参数问题
- 🌐 **Network Error**: 连接错误

## 💡 验证优化技巧

### 1. 成本控制
```bash
# 使用最便宜的验证设置
HAJIMI_CHECK_MODEL=gemini-2.5-flash          # Gemini 最快模型
OPENROUTER_TEST_MODEL=deepseek/deepseek-chat-v3.1:free  # 免费模型
```

### 2. 速度优化
```bash
# 降低超时时间
GEMINI_TIMEOUT=15.0
OPENROUTER_TIMEOUT=15.0
MODELSCOPE_TIMEOUT=15.0

# 使用代理避免频率限制
PROXY=http://localhost:1080
```

### 3. 选择性验证
```bash
# 只验证 Gemini 和 ModelScope，OpenRouter 仅提取
GEMINI_VALIDATION_ENABLED=true
OPENROUTER_VALIDATION_ENABLED=false
MODELSCOPE_VALIDATION_ENABLED=true
OPENROUTER_EXTRACT_ONLY=true
```

## 📈 性能对比

| 模式 | 扫描速度 | 验证准确性 | 网络消耗 | 推荐场景 |
|------|----------|------------|----------|----------|
| **仅提取** | 很快 | N/A | 最低 | 快速扫描 |
| **Gemini验证** | 中等 | 高 | 中等 | 安全审计 |
| **OpenRouter验证** | 中等 | 高 | 低（免费模型） | 成本敏感 |
| **ModelScope验证** | 中等 | 高 | 低（轻量模型） | 国内优化 |
| **全验证** | 较慢 | 最高 | 较高 | 完整安全检查 |

## 🎮 实战使用案例

### 案例1: 快速安全审计
```bash
# 全面扫描并验证所有发现的密钥
export GITHUB_TOKENS="your_tokens_here"
python -m src.main --mode compatible

# 查看验证结果
cat data/keys/keys_valid_*.txt        # 已验证的有效密钥
cat data/logs/keys_valid_detail_*.log # 详细验证日志
```

### 案例2: 专项 OpenRouter 检查
```bash
# 专门查找并验证 OpenRouter 密钥
python scripts/quick_launch.py openrouter

# 检查验证统计
grep "OpenRouter" data/logs/keys_valid_detail_*.log
```

### 案例3: 专项 ModelScope 检查
```bash
# 专门查找并验证 ModelScope 密钥
python scripts/quick_launch.py modelscope

# 检查验证统计
grep "ModelScope" data/logs/keys_valid_detail_*.log
```

### 案例4: 成本控制扫描
```bash
# 提取所有类型，只验证 ModelScope 和 OpenRouter（免费模型）
export GEMINI_VALIDATION_ENABLED=false
export MODELSCOPE_VALIDATION_ENABLED=true
export OPENROUTER_VALIDATION_ENABLED=true
python -m src.main --mode compatible
```

## 🔒 安全考虑

### 1. 验证安全
- 验证过程使用最小权限请求
- 不会存储或泄露密钥内容
- 支持代理隐藏验证来源

### 2. 频率限制
- 内置随机延迟机制
- 智能重试策略
- 支持多代理轮换

### 3. 错误处理
- 区分临时错误和永久失效
- 详细的错误分类和记录
- 优雅的网络异常处理

---

🎉 **现在你拥有了业界最完整的 API 密钥发现和验证系统！**

无论是快速扫描还是深度安全审计，都能满足你的需求。