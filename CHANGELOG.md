# Changelog

## v0.0.2-modelscope (2025-09-11)

本次版本聚焦于 ModelScope Key 抓取能力与可运维性改进。

- 新增：ModelScope `ms-...` Key 抓取
  - 当同一文件包含 `TARGET_BASE_URLS`（默认含 `https://api-inference.modelscope.cn/v1/`）时，提取形态为 UUID 的 `ms-` key（严格匹配）。
  - 不做有效性验证，直接落盘到 `data/keys/keys_valid_YYYYMMDD.txt`，详细日志写入 `data/logs/keys_valid_detailYYYYMMDD.log`。
- 新增：命令行开关 `--mode`
  - `modelscope-only`: 仅提取 ms-key，不回退到 Gemini 提取与校验。
  - `compatible`: 若未命中 ms-key，则回退到原有的 Gemini 提取与校验。
  - CLI 参数优先级高于 `.env` 中的 `MODELSCOPE_EXTRACT_ONLY`。
- 新增：本地“干跑”脚本（无网络）
  - `python scripts/dry_run.py` 用本地内置样例验证提取与落盘链路是否正常。
- 新增：配置项（可在 `.env` 设置）
  - `TARGET_BASE_URLS`: 逗号分隔 base_url/域名，文件包含其一才会尝试提取（默认含 ModelScope v1）。
  - `MS_USE_LOOSE_PATTERN`: 是否使用宽松匹配（默认 false）。
  - `MS_PROXIMITY_CHARS`: 与 base_url 的最大字符距离（仅宽松模式下建议 300–1000）。
  - `MS_REQUIRE_KEY_CONTEXT`: 是否要求附近包含 key/token/secret/authorization 等上下文词（默认 false）。
  - `MODELSCOPE_EXTRACT_ONLY`: 仅提取不验证；在 `modelscope-only` 模式下生效（默认 true）。
- 文档：README 增补运行示例与配置说明；`queries.example` 增加 ModelScope 查询示例。

### 使用速览

1) 准备 `.env`（不要提交到仓库）

- 必填：`GITHUB_TOKENS=ghp_xxx1,ghp_xxx2`
- 建议：`DATA_PATH=./data`
- 可选（ModelScope）：
  - `TARGET_BASE_URLS=https://api-inference.modelscope.cn/v1/,api-inference.modelscope.cn`
  - `MS_USE_LOOSE_PATTERN=false`
  - `MS_PROXIMITY_CHARS=800`
  - `MS_REQUIRE_KEY_CONTEXT=false`
  - `MODELSCOPE_EXTRACT_ONLY=true`

2) 准备查询 `data/queries.txt`

- 示例：
  - `"https://api-inference.modelscope.cn/v1/" in:file`
  - `api-inference.modelscope.cn in:file`
- 可按需加语言/路径限制：`language:TypeScript path:src`

3) 运行

- 仅 ModelScope 模式：`python app/hajimi_king.py --mode modelscope-only`
- 兼容模式：`python app/hajimi_king.py --mode compatible`

4) 查看输出

- Key 列表：`data/keys/keys_valid_YYYYMMDD.txt`
- 详细日志：`data/logs/keys_valid_detailYYYYMMDD.log`

### 行为变化与兼容性

- 默认 `.env` 中 `MODELSCOPE_EXTRACT_ONLY=true`，意味着“仅提取不验证”。若需要回退到 Gemini 提取与校验，使用 `--mode compatible` 覆盖，或将该项设为 `false`。
- Search 上限仍受 GitHub Code Search API 限制（每查询最多 1000 条）。建议用更精确的表达式拆分查询以提升召回质量。

### 运行与部署

- 本地 Python：`pip install uv && uv pip install -r pyproject.toml`，然后按上述命令运行。
- Docker：准备 `.env`，`docker-compose up -d`，日志用 `docker-compose logs -f`。

### 故障排查

- 未提取到 key：
  - 确认 `data/queries.txt` 中的 base_url 查询是否命中代码（可在 GitHub 先手动检索）。
  - 若使用宽松匹配，建议设置 `MS_PROXIMITY_CHARS=300~1000` 并可开启 `MS_REQUIRE_KEY_CONTEXT=true`。
- 频繁限流：配置多个 `GITHUB_TOKENS` 并开启代理（`PROXY`）。
- 日志乱码（Windows 控制台）：建议使用 UTF-8 终端，或忽略彩色转义。

### 合规提示

- 仅在授权范围内使用。发现疑似泄露建议按组织流程负责披露与整改。不要验证、使用或传播非授权密钥。

---

## v0.0.1-beta

- 初始版本：
  - GitHub Code Search 搜索与分页抓取。
  - 基于正则的 Google/Gemini Key 提取与验证。
  - 文件管理与 checkpoint 增量机制。
  - 可选外部同步（Gemini Balancer / GPT Load）。

