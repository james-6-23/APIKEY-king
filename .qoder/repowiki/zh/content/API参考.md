# API参考

<cite>
**本文档中引用的文件**   
- [config.py](file://src\models\config.py) - *重构后的配置模型*
- [main.py](file://src\main.py) - *更新的主应用入口*
- [core/__init__.py](file://src\core\__init__.py) - *新增扫描模式枚举*
</cite>

## 更新摘要
**已做更改**   
- 完全重构了“环境变量配置”部分，基于新的 `AppConfig` 数据模型
- 更新了“命令行参数”部分，新增三种扫描模式：`openrouter-only`、`gemini-only` 和 `compatible`
- 重写了“参数组合使用示例”，以匹配新的配置结构和 CLI 参数
- 移除了过时的内部函数接口描述，更新为基于新代码结构的说明
- 同步更新了所有源文件引用路径，反映项目重构后的实际位置

## 目录
1. [API参考](#api参考)
2. [环境变量配置](#环境变量配置)
3. [命令行参数](#命令行参数)
4. [参数组合使用示例](#参数组合使用示例)
5. [内部函数接口](#内部函数接口)

## 环境变量配置

本节详细列出 `config.py` 文件中定义的 `AppConfig` 模型所支持的所有配置项。新的配置系统采用结构化数据类，取代了旧的扁平化环境变量。

**Section sources**
- [config.py](file://src\models\config.py#L82-L111) - *重构后的主配置模型*

### GitHub 配置
| 配置项名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **github.tokens** | 字符串列表 | [] | 任意字符串列表 | 用于访问 GitHub API 的个人访问令牌列表。支持多个令牌轮换以避免速率限制。这是必填项。 |
| **github.api_url** | 字符串 | https://api.github.com/search/code | 有效的 URL | GitHub 搜索代码 API 的端点地址。 |

### 数据存储配置
| 配置项名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **data_path** | 字符串 | ./data | 任意有效路径 | 应用程序用于存储数据文件（如日志、检查点）的根目录路径。 |

### 搜索与过滤配置
| 配置项名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **scan.date_range_days** | 整数 | 730 | 大于 0 的整数 | 用于过滤仓库的年龄范围（天），只搜索在此天数内有更新的仓库。 |
| **scan.file_path_blacklist** | 字符串列表 | [] | 任意字符串列表 | 文件路径黑名单，包含这些关键词的文件路径将被跳过。 |
| **scan.queries_file** | 字符串 | queries.txt | 任意文件名 | 包含 GitHub 搜索查询语句的文件名（相对于 `data_path`）。 |

### 提取器通用配置 (ExtractorConfig)
所有密钥提取器共享以下配置结构，通过 `extractors` 字典进行配置。

| 配置项名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **name** | 字符串 | N/A | 任意字符串 | 提取器的唯一标识名称（如 `gemini`, `modelscope`, `openrouter`）。 |
| **enabled** | 布尔值 | true | true, false | 是否启用此提取器。 |
| **patterns** | 字典 | {} | 键值对 | 用于匹配密钥的正则表达式模式字典。 |
| **base_urls** | 字符串列表 | [] | 有效的 URL 列表 | 目标 API 的基础 URL 列表，用于上下文识别。 |
| **use_loose_pattern** | 布尔值 | false | true, false | 是否使用宽松的密钥模式进行匹配。 |
| **proximity_chars** | 整数 | 0 | 大于等于 0 的整数 | 密钥与 `base_urls` 在文本中的最大字符距离。 |
| **require_key_context** | 布尔值 | false | true, false | 是否要求密钥周围存在 "key", "token" 等上下文关键词。 |
| **extract_only** | 布尔值 | false | true, false | 是否仅提取密钥而不进行外部验证。 |

### 验证器通用配置 (ValidatorConfig)
所有密钥验证器共享以下配置结构，通过 `validators` 字典进行配置。

| 配置项名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **name** | 字符串 | N/A | 任意字符串 | 验证器的唯一标识名称（如 `gemini`, `modelscope`, `openrouter`）。 |
| **enabled** | 布尔值 | true | true, false | 是否启用此验证器。 |
| **api_endpoint** | 字符串（可选） | null | 有效的 URL | 验证 API 密钥的端点地址。 |
| **model_name** | 字符串（可选） | null | 任意模型名称 | 用于验证的模型名称（如 `gemini-2.5-flash`）。 |
| **timeout** | 浮点数 | 30.0 | 大于 0 的浮点数 | API 调用的超时时间（秒）。 |

### 代理配置
| 配置项名称 | 数据类型 | 默认值 | 取值范围 | 功能描述 |
| --- | --- | --- | --- | --- |
| **proxy_list** | 字符串列表 | [] | 有效的代理 URL 列表 | 用于访问外部 API 的代理服务器列表，支持 `http://` 和 `socks5://` 格式。 |

## 命令行参数

`main.py` 支持以下命令行选项，用于控制程序的运行模式和配置。

**Section sources**
- [main.py](file://src\main.py#L420-L445) - *命令行参数解析*

### --mode
*   **语法**: `--mode {modelscope-only,openrouter-only,gemini-only,compatible}`
*   **参数类型**: 字符串（枚举）
*   **使用场景**: 控制密钥扫描的核心模式。
    *   `modelscope-only`: 仅激活 ModelScope 相关的提取器和验证器，使用 `config/queries/modelscope.txt` 作为查询文件。
    *   `openrouter-only`: 仅激活 OpenRouter 相关的提取器和验证器，使用 `config/queries/openrouter.txt` 作为查询文件。
    *   `gemini-only`: 仅激活 Gemini 相关的提取器和验证器，使用 `config/queries/gemini.txt` 作为查询文件。
    *   `compatible`: 激活所有类型的提取器和验证器，提供向后兼容的完整扫描能力。
*   **依赖关系**: 此参数会覆盖配置文件中 `extractors` 和 `validators` 的 `enabled` 设置，并自动切换 `queries_file`。

### --config-preset
*   **语法**: `--config-preset <preset_name>`
*   **参数类型**: 字符串
*   **使用场景**: 从 `config/presets/` 目录加载预设的配置文件（如 `.env` 文件），用于快速切换不同的扫描环境。
*   **依赖关系**: 指定的预设文件必须存在于 `config/presets/` 目录下。

### --queries
*   **语法**: `--queries <file_path>`
*   **参数类型**: 字符串（文件路径）
*   **使用场景**: 覆盖配置中的 `queries_file`，指定一个自定义的查询文件路径。
*   **依赖关系**: 此参数优先级高于 `--mode` 参数对查询文件的设置。

## 参数组合使用示例

以下示例展示了如何组合使用配置和命令行参数。

### 示例 1：启用调试模式
虽然没有直接的 `DEBUG` 环境变量，但可以通过日志级别和启用所有验证来实现详细输出。
```bash
# 通过环境变量或预设文件启用所有提取器和验证器
python src/main.py --mode compatible
```

### 示例 2：指定自定义配置路径
通过设置 `data_path` 并使用 `--queries` 参数来完全控制数据和查询。
```bash
export data_path=/custom/data/path
python src/main.py --queries /custom/data/path/my_queries.txt
```

### 示例 3：仅提取并验证 OpenRouter 密钥
使用 `--mode openrouter-only` 参数来专注于 OpenRouter 密钥的发现和验证。
```bash
python src/main.py --mode openrouter-only
```

### 示例 4：使用预设配置
加载名为 `production` 的预设配置，该配置可能包含生产环境的代理和令牌。
```bash
python src/main.py --config-preset production --mode compatible
```

## 内部函数接口

本节提供关键内部函数的简要说明，为自动化脚本编写者和系统集成者提供技术参考。

**Section sources**
- [main.py](file://src\main.py#L50-L415) - *主应用逻辑*
- [core/__init__.py](file://src\core\__init__.py#L10-L15) - *扫描模式定义*

### Application._apply_scan_mode_config()
*   **方法签名**: `_apply_scan_mode_config(self) -> None`
*   **功能描述**: 根据 `self.scan_mode` 的值，动态修改 `self.config` 中提取器和验证器的启用状态，并切换查询文件。这是实现模式切换的核心逻辑。
*   **返回结构**: 无

### Application._create_extractors()
*   **方法签名**: `_create_extractors(self) -> List[KeyExtractor]`
*   **功能描述**: 遍历 `self.config` 中所有启用的提取器配置，根据其 `name` 创建相应的提取器实例（如 `GeminiExtractor`, `ModelScopeExtractor`）。
*   **返回结构**: 一个 `KeyExtractor` 实例列表。

### Application._create_validators()
*   **方法签名**: `_create_validators(self) -> List[KeyValidator]`
*   **功能描述**: 遍历 `self.config` 中所有启用的验证器配置，根据其 `name` 创建相应的验证器实例（如 `GeminiValidator`, `OpenRouterValidator`）。
*   **返回结构**: 一个 `KeyValidator` 实例列表。

### ScanMode 枚举
*   **类型**: `Enum`
*   **功能描述**: 定义了应用程序支持的四种扫描模式，确保模式参数的类型安全。
*   **取值范围**: `COMPATIBLE`, `MODELSCOPE_ONLY`, `OPENROUTER_ONLY`, `GEMINI_ONLY`

### AppConfig.get_enabled_extractors()
*   **方法签名**: `get_enabled_extractors(self) -> Dict[str, ExtractorConfig]`
*   **功能描述**: 从 `self.extractors` 字典中筛选出所有 `enabled=True` 的配置项。
*   **返回结构**: 一个包含启用的提取器配置的字典。

### AppConfig.get_enabled_validators()
*   **方法签名**: `get_enabled_validators(self) -> Dict[str, ValidatorConfig]`
*   **功能描述**: 从 `self.validators` 字典中筛选出所有 `enabled=True` 的配置项。
*   **返回结构**: 一个包含启用的验证器配置的字典。