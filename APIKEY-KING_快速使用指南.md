# 🎪 APIKEY-king 快速使用指南

> **一站式API密钥发现与验证工具**  
> 支持 Gemini、OpenRouter、ModelScope 三大AI平台

---

## 🚀 5分钟快速上手

### 第一步：获取GitHub Token
1. 访问 [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. 点击 "Generate new token (classic)"
3. 选择权限：只需勾选 `public_repo`
4. 复制生成的token（格式：`ghp_xxxxxxxxxxxx`）

### 第二步：配置环境
```bash
# 克隆项目
git clone <repository-url>
cd APIKEY-king

# 安装依赖
pip install uv
uv pip install -r pyproject.toml

# 配置Token
cp .env.template .env
echo "GITHUB_TOKENS=你的token1,你的token2" >> .env

# 准备查询文件
cp queries.template data/queries.txt
```

### 第三步：开始扫描
```bash
# 全面扫描模式（推荐新手）
python -m src.main --mode compatible

# 或使用快捷脚本
python scripts/quick_launch.py all
```

### 第四步：查看结果
```bash
# 查看发现的有效密钥
cat data/keys/keys_valid_*.txt

# 查看详细日志
tail -f data/logs/keys_valid_detail_*.log
```

---

## 📊 扫描模式选择

| 模式 | 命令 | 特点 | 适用场景 |
|------|------|------|----------|
| **兼容模式** | `--mode compatible` | 扫描所有平台+验证 | 全面安全检查 |
| **Gemini专项** | `--mode gemini-only` | 只扫描Google AI | 针对性检查 |
| **OpenRouter专项** | `--mode openrouter-only` | 只扫描OpenRouter | 特定平台审计 |
| **ModelScope专项** | `--mode modelscope-only` | 只扫描ModelScope | 国内平台检查 |

---

## ⚙️ 核心配置说明

### 必填配置
```bash
# .env 文件中必须配置
GITHUB_TOKENS=ghp_token1,ghp_token2,ghp_token3  # 多个token提高限额
```

### 推荐配置
```bash
# 代理设置（强烈推荐，避免IP被封）
PROXY=http://localhost:1080

# 扫描范围（天数，默认730天）
DATE_RANGE_DAYS=365

# 验证器开关
GEMINI_VALIDATION_ENABLED=true
OPENROUTER_VALIDATION_ENABLED=true
MODELSCOPE_VALIDATION_ENABLED=true
```

### 查询文件配置
```bash
# data/queries.txt - 自定义搜索规则
AIzaSy in:file                                    # 基础Gemini搜索
"https://openrouter.ai/api/v1" in:file           # OpenRouter API搜索
"https://api-inference.modelscope.cn/v1/" in:file # ModelScope API搜索
"AIzaSy" AND "google" in:file extension:py       # 精确Python文件搜索
```

---

## 🐳 Docker快速部署

### 方式一：Docker Compose（推荐）
```bash
# 1. 准备配置
cp .env.template .env
# 编辑 .env 文件，填入 GITHUB_TOKENS

# 2. 启动服务
docker-compose --profile full up -d

# 3. 查看日志
docker-compose logs -f apikey-king-full

# 4. 停止服务
docker-compose down
```

### 方式二：单容器运行
```bash
# 构建并运行
docker build -t apikey-king:latest .
docker run -d \
  --name apikey-king \
  -e GITHUB_TOKENS=your_tokens_here \
  -v ./data:/app/data \
  apikey-king:latest
```

---

## 📋 输出结果说明

### 文件结构
```
data/
├── keys/
│   ├── keys_valid_20250113.txt      # ✅ 有效密钥列表
│   └── key_429_20250113.txt         # ⏱️ 限流密钥列表
├── logs/
│   ├── keys_valid_detail_20250113.log   # 📝 详细验证日志
│   └── key_429_detail_20250113.log      # 📊 限流详细日志
├── checkpoint.json                   # 💾 断点续传数据
└── queries.txt                      # 🔍 搜索查询配置
```

### 日志格式解读
```bash
# 成功验证
[2025-01-13 10:30:15] ✅ VALID | AIzaSyABC123... | https://github.com/user/repo/blob/main/config.py | Gemini API验证成功

# 验证失败
[2025-01-13 10:30:16] ❌ INVALID | AIzaSyXYZ... | https://github.com/user/repo/blob/main/test.py | 401 Unauthorized

# 被限流
[2025-01-13 10:30:17] ⏱️ RATE_LIMITED | AIzaSyDEF... | https://github.com/user/repo/blob/main/app.py | 429 Too Many Requests
```

---

## 🔧 常见问题解决

### Q1: 扫描速度很慢？
**解决方案：**
- 添加更多GitHub Token：`GITHUB_TOKENS=token1,token2,token3`
- 配置代理服务器：`PROXY=http://localhost:1080`
- 缩小扫描范围：`DATE_RANGE_DAYS=180`

### Q2: 发现的密钥都无效？
**检查项目：**
- 网络连接是否正常
- 代理设置是否正确
- 验证器配置是否启用
- 是否扫描到测试/示例文件

### Q3: GitHub API限流？
**解决方案：**
- 使用多个GitHub Token
- 配置代理服务器轮换
- 降低扫描频率
- 等待限流重置

### Q4: 程序意外中断？
**恢复方法：**
- 直接重新运行，程序会从断点继续
- 检查 `data/checkpoint.json` 文件
- 如需重新开始：删除 `checkpoint.json` 和 `scanned_shas.txt`

---

## 💡 使用技巧

### 提高发现率
```bash
# 1. 优化查询语句
"AIzaSy" AND "config" in:file extension:py    # 针对配置文件
"api_key" AND "AIzaSy" in:file -path:test     # 排除测试文件

# 2. 扩大搜索范围
DATE_RANGE_DAYS=1095  # 扩大到3年

# 3. 使用多种查询模式
echo '"GOOGLE_API_KEY" in:file' >> data/queries.txt
echo '"GEMINI_API_KEY" in:file' >> data/queries.txt
```

### 性能优化
```bash
# 1. 使用SSD存储
DATA_PATH=/path/to/ssd/data

# 2. 定期清理日志
find data/logs -name "*.log" -mtime +7 -delete

# 3. 限制内存使用
export PYTHONHASHSEED=0
ulimit -m 2097152  # 限制2GB内存
```

### 安全建议
```bash
# 1. 定期轮换GitHub Token
# 2. 不要将真实密钥提交到版本控制
# 3. 对发现的有效密钥进行安全存储
# 4. 建立密钥泄露响应流程
```

---

## 🎯 高级用法

### 自定义提取规则
```yaml
# config/extractors/gemini.yaml
name: "gemini"
enabled: true
patterns:
  strict: "AIzaSy[A-Za-z0-9\\-_]{33}"
  loose: "AIzaSy[A-Za-z0-9\\-_]{30,40}"  # 宽松模式
use_loose_pattern: false  # 启用宽松模式
require_key_context: true  # 需要上下文验证
```

### 批量部署
```bash
# 使用预设配置
python -m src.main --config-preset gemini-only
python -m src.main --config-preset openrouter-only
python -m src.main --config-preset modelscope-only

# 并行运行多个实例
python -m src.main --mode gemini-only &
python -m src.main --mode openrouter-only &
python -m src.main --mode modelscope-only &
```

### 结果分析
```bash
# 统计各平台密钥数量
echo "Gemini: $(grep -c 'AIzaSy' data/keys/keys_valid_*.txt)"
echo "OpenRouter: $(grep -c 'sk-or-v1-' data/keys/keys_valid_*.txt)"
echo "ModelScope: $(grep -c 'ms-' data/keys/keys_valid_*.txt)"

# 按验证状态分类
grep "✅ VALID" data/logs/keys_valid_detail_*.log | wc -l
grep "❌ INVALID" data/logs/keys_valid_detail_*.log | wc -l
grep "⏱️ RATE_LIMITED" data/logs/keys_valid_detail_*.log | wc -l
```

---

## 📞 获取帮助

- **GitHub Issues**: 报告问题和功能请求
- **项目文档**: 查看完整的技术文档
- **社区讨论**: 参与使用经验分享

---

**🎉 开始你的API密钥发现之旅吧！**

> ⚠️ **重要提醒**: 本工具仅供安全研究和合法用途使用，请遵守相关法律法规。
