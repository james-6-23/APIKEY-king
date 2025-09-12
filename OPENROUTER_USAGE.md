# 🔥 OpenRouter 专用扫描模式使用指南

## 🚀 快速启动

### 方法一：使用专用启动脚本（推荐）

1. **配置环境**：
   ```bash
   # 复制 OpenRouter 专用配置
   cp .env.openrouter .env
   
   # 编辑配置文件，填入你的 GitHub token
   # GITHUB_TOKENS=你的github_token
   ```

2. **运行 OpenRouter 专用扫描**：
   ```bash
   python start_openrouter_only.py
   ```

### 方法二：使用命令行参数

```bash
# 使用命令行参数启动 OpenRouter 专用模式
python app/hajimi_king.py --mode openrouter-only
```

### 方法三：环境变量配置

在 `.env` 文件中配置：
```bash
# 启用 OpenRouter 提取
OPENROUTER_BASE_URLS=https://openrouter.ai/api/v1,openrouter.ai
OPENROUTER_EXTRACT_ONLY=true

# 禁用其他服务
TARGET_BASE_URLS=
MODELSCOPE_EXTRACT_ONLY=false

# 使用 OpenRouter 专用查询文件
QUERIES_FILE=queries.openrouter.txt
```

## 🔧 配置说明

### 核心配置项

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `OPENROUTER_BASE_URLS` | `https://openrouter.ai/api/v1,openrouter.ai` | OpenRouter API 地址 |
| `OPENROUTER_EXTRACT_ONLY` | `true` | 只提取，不验证 |
| `TARGET_BASE_URLS` | (空) | 禁用 ModelScope |
| `MODELSCOPE_EXTRACT_ONLY` | `false` | 禁用 ModelScope |

### 查询配置

OpenRouter 专用查询文件 `queries.openrouter.txt` 包含：
- `"https://openrouter.ai/api/v1" in:file`
- `sk-or-v1- in:file`
- `openrouter.ai in:file`
- 更多针对性查询...

## 📊 输出结果

扫描到的 OpenRouter 密钥会保存到：
- `data/keys/keys_valid_YYYYMMDD.txt` - 找到的密钥列表
- `data/logs/keys_valid_detail_YYYYMMDD.log` - 详细信息（包含来源文件）

## ✨ 特性

✅ **高效过滤**：只在包含 OpenRouter API 地址的文件中搜索  
✅ **智能识别**：精确匹配 `sk-or-v1-[64位十六进制]` 格式  
✅ **占位符过滤**：自动过滤示例和占位符密钥  
✅ **无验证模式**：纯提取，不进行 API 调用验证  
✅ **增量扫描**：避免重复扫描已处理的文件  

## 🎯 支持的密钥格式

- `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`
- `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`
- 所有 `sk-or-v1-` 开头的 64 位十六进制字符串

## 🛠️ 故障排除

### 常见问题

1. **没有找到密钥**
   - 检查 `OPENROUTER_BASE_URLS` 配置
   - 确认查询文件 `queries.openrouter.txt` 存在
   - 检查 GitHub token 是否有效

2. **扫描速度慢**
   - 配置代理：`PROXY=http://localhost:1080`
   - 减少查询数量或调整查询策略

3. **权限错误**
   - 确保 GitHub token 有 `public_repo` 权限
   - 检查 `data` 目录是否可写

### 日志输出示例

```
🔥 启动 OpenRouter 专用扫描模式
✅ Found 3 OpenRouter key(s) (no validation)
📁 Saved 3 OpenRouter key(s)
```

---

💡 **提示**：OpenRouter 专用模式会跳过 Gemini 验证，大大提高扫描速度！