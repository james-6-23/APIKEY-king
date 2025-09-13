# API参考

<cite>
**本文档中引用的文件**   
- [config.py](file://common/config.py)
- [hajimi_king.py](file://app/hajimi_king.py)
- [github_client.py](file://utils/github_client.py)
- [file_manager.py](file://utils/file_manager.py)
- [Logger.py](file://common/Logger.py) - *在最近的提交中更新*
</cite>

## 更新摘要
**已做更改**   
- 更新了“内部函数接口”部分，新增了 `Logger` 类的多个方法说明
- 添加了对 `Logger.py` 文件的引用，以反映日志模块的重构
- 修正了文档中未提及的 `Logger` 新增方法，确保与代码实现一致
- 维护并更新了文档级和章节级的源文件引用系统

## 目录
1. [API参考](#api参考)
2. [环境变量配置](#环境变量配置)
3. [命令行参数](#命令行参数)
4. [参数组合使用示例](#参数组合使用示例)
5. [内部函数接口](#内部函数接口)

## 环境变量配置

本节详细列出 `config.py` 文件中定义的所有可配置环境变量，包括其名称、数据类型、默认值、取值范围和功能描述。

**Section sources**
- [config.py](file://common/config.py#L12-L169)

### GitHub 配置
| 环境变量名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **GITHUB_TOKENS** | 字符串（逗号分隔） | "" | 任意字符串 | 用于访问 GitHub API 的个人访问令牌列表，多个令牌用逗号分隔。这是必填项。 |
| **PROXY** | 字符串（逗号分隔） | "" | 任意字符串 | 用于访问 GitHub API 的代理服务器列表，支持 `http://` 和 `socks5://` 格式，多个代理用逗号分隔。 |

### 数据存储配置
| 环境变量名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **DATA_PATH** | 字符串 | /app/data | 任意有效路径 | 应用程序用于存储数据文件（如日志、检查点）的根目录路径。 |

### 文件路径与前缀配置
| 环境变量名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **VALID_KEY_PREFIX** | 字符串 | keys/keys_valid_ | 任意字符串 | 存储有效 API 密钥的文件路径前缀。 |
| **RATE_LIMITED_KEY_PREFIX** | 字符串 | keys/key_429_ | 任意字符串 | 存储被限流 API 密钥的文件路径前缀。 |
| **VALID_KEY_DETAIL_PREFIX** | 字符串 | logs/keys_valid_detail_ | 任意字符串 | 存储有效密钥详细信息（含 URL）的日志文件路径前缀。 |
| **RATE_LIMITED_KEY_DETAIL_PREFIX** | 字符串 | logs/key_429_detail_ | 任意字符串 | 存储被限流密钥详细信息的日志文件路径前缀。 |
| **QUERIES_FILE** | 字符串 | queries.txt | 任意文件名 | 包含 GitHub 搜索查询语句的文件名（相对于 `DATA_PATH`）。 |
| **SCANNED_SHAS_FILE** | 字符串 | scanned_shas.txt | 任意文件名 | 用于记录已扫描文件 SHA 值的文件名（相对于 `DATA_PATH`）。 |

### 搜索与过滤配置
| 环境变量名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **DATE_RANGE_DAYS** | 整数 | 730 | 大于 0 的整数 | 用于过滤仓库的年龄范围（天），只搜索在此天数内有更新的仓库。 |
| **FILE_PATH_BLACKLIST** | 字符串（逗号分隔） | readme,docs,doc/,.md,sample,tutorial | 任意字符串 | 文件路径黑名单，包含这些关键词的文件路径将被跳过。 |
| **HAJIMI_CHECK_MODEL** | 字符串 | gemini-2.5-flash | 任意模型名称 | 用于验证 Google API 密钥的 Gemini 模型名称。 |

### ModelScope 密钥提取配置
| 环境变量名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **TARGET_BASE_URLS** | 字符串（逗号分隔） | https://api-inference.modelscope.cn/v1/ | 有效的 URL | 目标 API 基础 URL 列表，用于识别包含 ModelScope 密钥的文件。 |
| **MS_USE_LOOSE_PATTERN** | 字符串（布尔值） | false | true, false | 是否使用宽松的密钥模式（`ms-`后跟长字符串）进行匹配。 |
| **MS_PROXIMITY_CHARS** | 整数 | 0 | 大于等于 0 的整数 | 当使用宽松模式时，密钥与 `TARGET_BASE_URLS` 在文本中的最大字符距离。 |
| **MS_REQUIRE_KEY_CONTEXT** | 字符串（布尔值） | false | true, false | 是否要求密钥周围存在 "key", "token" 等上下文关键词。 |
| **MODELSCOPE_EXTRACT_ONLY** | 字符串（布尔值） | true | true, false | 是否仅提取 ModelScope 密钥，不进行外部验证。 |

### OpenRouter 密钥提取配置
| 环境变量名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **OPENROUTER_BASE_URLS** | 字符串（逗号分隔） | https://openrouter.ai/api/v1 | 有效的 URL | OpenRouter API 基础 URL 列表，用于识别包含 OpenRouter 密钥的文件。 |
| **OPENROUTER_USE_LOOSE_PATTERN** | 字符串（布尔值） | false | true, false | 是否使用宽松模式匹配 OpenRouter 密钥。 |
| **OPENROUTER_PROXIMITY_CHARS** | 整数 | 0 | 大于等于 0 的整数 | 密钥与 `OPENROUTER_BASE_URLS` 在文本中的最大字符距离。 |
| **OPENROUTER_REQUIRE_KEY_CONTEXT** | 字符串（布尔值） | false | true, false | 是否要求密钥周围存在上下文关键词。 |
| **OPENROUTER_EXTRACT_ONLY** | 字符串（布尔值） | true | true, false | 是否仅提取 OpenRouter 密钥，不进行外部验证。 |

## 命令行参数

`hajimi_king.py` 支持以下命令行选项，用于控制程序的运行模式。

**Section sources**
- [hajimi_king.py](file://app/hajimi_king.py#L24-L30)

### --mode
*   **语法**: `--mode {modelscope-only,compatible}`
*   **参数类型**: 字符串（枚举）
*   **使用场景**: 控制密钥提取的模式。
    *   `modelscope-only`: 仅提取符合 `ms-UUID` 模式的 ModelScope 密钥，不进行任何外部验证，并且不会回退到原有的 Google API 密钥提取逻辑。
    *   `compatible`: 首先尝试提取 ModelScope 密钥，如果未找到，则回退到原有的 Google API 密钥提取和验证逻辑。
*   **依赖关系**: 此参数会覆盖环境变量 `MODELSCOPE_EXTRACT_ONLY` 的值，但仅在当前进程运行期间有效。

## 参数组合使用示例

以下示例展示了如何组合使用环境变量和命令行参数。

### 示例 1：启用调试模式
通过设置 `DEBUG` 环境变量（虽然代码中未直接使用，但可通过日志级别控制）和 `MODELSCOPE_EXTRACT_ONLY=false` 来启用更详细的日志输出和完整的验证流程。
```bash
export MODELSCOPE_EXTRACT_ONLY=false
python app/hajimi_king.py --mode compatible
```

### 示例 2：指定自定义配置路径
通过设置 `DATA_PATH` 环境变量来指定数据文件的存储位置。
```bash
export DATA_PATH=/custom/data/path
export QUERIES_FILE=my_queries.txt
python app/hajimi_king.py
```

### 示例 3：仅提取 ModelScope 密钥
使用 `--mode modelscope-only` 参数来仅提取 ModelScope 密钥，忽略所有其他密钥。
```bash
python app/hajimi_king.py --mode modelscope-only
```

## 内部函数接口

本节提供关键内部函数的简要说明，为自动化脚本编写者和系统集成者提供技术参考。

**Section sources**
- [github_client.py](file://utils/github_client.py#L30-L150)
- [Logger.py](file://common/Logger.py#L10-L180) - *新增日志方法*

### github_client.GitHubClient.search_for_keys()
*   **方法签名**: `search_for_keys(self, query: str, max_retries: int = 5) -> Dict[str, Any]`
*   **功能描述**: 使用配置的 GitHub 令牌在 GitHub 代码中执行搜索查询。它会自动轮换令牌以避免速率限制，并处理分页，最多返回 1000 个结果。
*   **返回结构**: 一个字典，包含 `total_count` (总结果数), `incomplete_results` (布尔值，表示结果是否不完整), 和 `items` (包含搜索结果的列表)。

### github_client.GitHubClient.get_file_content()
*   **方法签名**: `get_file_content(self, item: Dict[str, Any]) -> Optional[str]`
*   **功能描述**: 根据 GitHub 搜索结果项获取文件的完整内容。它会处理 base64 编码的内容，并在必要时通过 `download_url` 获取。
*   **返回结构**: 成功时返回文件内容的字符串，失败时返回 `None`。

### common.Logger.Logger.success()
*   **方法签名**: `success(self, message: str, *args, **kwargs)`
*   **功能描述**: 记录成功消息，使用特殊图标 ✅ 和 INFO 级别，用于标识操作成功。
*   **返回结构**: 无

### common.Logger.Logger.progress()
*   **方法签名**: `progress(self, message: str, current: int, total: int, *args, **kwargs)`
*   **功能描述**: 记录进度信息，显示进度条、百分比和当前/总数，用于长时间运行任务的可视化进度。
*   **返回结构**: 无

### common.Logger.Logger.network()
*   **方法签名**: `network(self, message: str, *args, **kwargs)`
*   **功能描述**: 记录网络相关操作，使用 🌐 图标，用于标识网络请求或连接事件。
*   **返回结构**: 无

### common.Logger.Logger.file_op()
*   **方法签名**: `file_op(self, message: str, *args, **kwargs)`
*   **功能描述**: 记录文件操作，使用 📁 图标，用于标识文件读写、创建或删除等操作。
*   **返回结构**: 无

### common.Logger.Logger.security()
*   **方法签名**: `security(self, message: str, *args, **kwargs)`
*   **功能描述**: 记录安全相关事件，使用 🔒 图标和 WARNING 级别，用于标识潜在的安全风险或敏感操作。
*   **返回结构**: 无

### common.Logger.Logger.rate_limit()
*   **方法签名**: `rate_limit(self, message: str, *args, **kwargs)`
*   **功能描述**: 记录频率限制事件，使用 ⏱️ 图标和 WARNING 级别，用于标识 API 调用被限流的情况。
*   **返回结构**: 无

### common.Logger.Logger.separator()
*   **方法签名**: `separator(self, title: str = "", char: str = "=", width: int = 60)`
*   **功能描述**: 打印分隔线，可带标题，用于在日志中划分不同逻辑块，提高可读性。
*   **返回结构**: 无