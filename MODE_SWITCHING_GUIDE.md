# 🎯 快速模式切换使用指南

现在你可以通过多种方式快速切换不同的扫描模式，专注于你需要的 API 密钥类型。

## 🚀 方式1: 命令行直接切换（推荐）

### OpenRouter 专扫模式
```bash
# 只扫描 OpenRouter API keys (sk-or-v1-格式)
python -m src.main --mode openrouter-only

# 使用预设配置文件
python -m src.main --mode openrouter-only --config-preset openrouter-only
```

### ModelScope 专扫模式
```bash
# 只扫描 ModelScope API keys (ms-UUID格式)
python -m src.main --mode modelscope-only

# 使用预设配置文件
python -m src.main --mode modelscope-only --config-preset modelscope-only
```

### Gemini 专扫模式
```bash
# 只扫描 Gemini API keys (AIzaSy格式) 并验证
python -m src.main --mode gemini-only

# 使用预设配置文件
python -m src.main --mode gemini-only --config-preset gemini-only
```

### 兼容模式（全扫描）
```bash
# 扫描所有类型的 API keys
python -m src.main --mode compatible
```

## 🎮 方式2: 快捷脚本（超简单）

### Python 快捷脚本
```bash
# OpenRouter 专扫
python scripts/quick_launch.py openrouter

# ModelScope 专扫  
python scripts/quick_launch.py modelscope

# Gemini 专扫
python scripts/quick_launch.py gemini

# 全类型扫描
python scripts/quick_launch.py all
```

### Shell 脚本 (Linux/Mac)
```bash
# 给脚本执行权限
chmod +x scripts/quick_scan.sh

# OpenRouter 专扫（支持短名）
./scripts/quick_scan.sh openrouter
./scripts/quick_scan.sh or

# ModelScope 专扫
./scripts/quick_scan.sh modelscope  
./scripts/quick_scan.sh ms

# Gemini 专扫
./scripts/quick_scan.sh gemini
./scripts/quick_scan.sh gm

# 全类型扫描
./scripts/quick_scan.sh all
```

### Windows 批处理 (Windows)
```cmd
REM OpenRouter 专扫
scripts\quick_scan.bat openrouter
scripts\quick_scan.bat or

REM ModelScope 专扫
scripts\quick_scan.bat modelscope
scripts\quick_scan.bat ms

REM Gemini 专扫  
scripts\quick_scan.bat gemini
scripts\quick_scan.bat gm

REM 全类型扫描
scripts\quick_scan.bat all
```

## 📋 方式3: 预设配置文件

如果你需要长期使用特定模式，可以直接复制预设配置：

```bash
# 复制 OpenRouter 专扫配置
cp config/presets/openrouter-only.env .env

# 复制 ModelScope 专扫配置  
cp config/presets/modelscope-only.env .env

# 复制 Gemini 专扫配置
cp config/presets/gemini-only.env .env
```

然后编辑 `.env` 文件，填入你的 `GITHUB_TOKENS`，直接运行：
```bash
python -m src.main
```

## 🔧 各模式特点对比

| 模式 | 提取类型 | 验证 | 查询文件 | 适用场景 |
|------|----------|------|----------|----------|
| `openrouter-only` | OpenRouter keys (sk-or-v1-*) | ✅ 实时验证 | openrouter_queries.txt | 专注 OpenRouter 平台 + 验证 |
| `modelscope-only` | ModelScope keys (ms-UUID) | ✅ 实时验证 | modelscope_queries.txt | 专注 ModelScope 平台 + 验证 |
| `gemini-only` | Gemini keys (AIzaSy*) | ✅ 实时验证 | gemini_queries.txt | 专注 Google AI 平台 + 验证 |
| `compatible` | 全部类型 | ✅ 全面验证 | queries.txt | 全面扫描 + 完整验证 |

## 🔥 验证功能亮点

### ✅ 现在支持的验证类型
- **Gemini** (AIzaSy*): 通过 Google AI API 验证
- **OpenRouter** (sk-or-v1-*): 通过 OpenRouter API 验证
- **ModelScope** (ms-*): 通过 ModelScope API 验证

### 🎯 验证优势
- **实时验证**: 发现密钥后立即验证有效性
- **智能判断**: 区分密钥无效、频率限制、网络问题等
- **成本优化**: 使用免费或低成本模型验证
- **详细报告**: 提供验证状态、使用模型、消耗代币等信息

## 💡 使用建议

### 🎯 针对性扫描（推荐）
如果你明确知道要找什么类型的密钥，使用专门模式效率更高：
```bash
# 我只关心 OpenRouter 的 keys
python -m src.main --mode openrouter-only

# 我只关心 ModelScope 的 keys  
python scripts/quick_launch.py modelscope
```

### 🌐 全面扫描
如果你不确定或想要全覆盖：
```bash
# 扫描所有类型
python -m src.main --mode compatible
```

### 📊 输出文件
不同模式的输出文件会自动按日期命名：
- `data/keys/keys_valid_20231201.txt` - 有效的密钥
- `data/logs/keys_valid_detail_20231201.log` - 详细日志

## 🔄 快速切换示例

```bash
# 早上先快速扫描 OpenRouter
./scripts/quick_scan.sh or

# 中午扫描 ModelScope  
python scripts/quick_launch.py ms

# 晚上全面扫描
python -m src.main --mode compatible
```

## 🆘 遇到问题？

1. **查看帮助**：
   ```bash
   python -m src.main --help
   python scripts/quick_launch.py help
   ./scripts/quick_scan.sh help
   ```

2. **检查配置**：确保 `.env` 文件中有正确的 `GITHUB_TOKENS`

3. **测试连接**：先用 `compatible` 模式测试系统是否正常

---

✨ **现在你可以灵活高效地切换不同扫描模式了！根据需要选择最合适的方式。**