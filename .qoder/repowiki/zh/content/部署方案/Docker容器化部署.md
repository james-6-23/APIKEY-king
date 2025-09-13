# Docker容器化部署

<cite>
**本文档引用的文件**   
- [Dockerfile](file://Dockerfile)
- [pyproject.toml](file://pyproject.toml)
- [app/hajimi_king.py](file://app/hajimi_king.py)
- [common/config.py](file://common/config.py)
- [common/Logger.py](file://common/Logger.py)
- [utils/github_client.py](file://utils/github_client.py)
- [utils/file_manager.py](file://utils/file_manager.py)
- [utils/sync_utils.py](file://utils/sync_utils.py)
- [README.md](file://README.md)
- [docker-compose.yml](file://docker-compose.yml)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构概述](#架构概述)
5. [详细组件分析](#详细组件分析)
6. [依赖分析](#依赖分析)
7. [性能考量](#性能考量)
8. [故障排除指南](#故障排除指南)
9. [结论](#结论)

## 简介
本项目是一个名为“Hajimi King”的自动化工具，旨在通过GitHub代码搜索发现并验证Google Gemini和ModelScope API密钥。系统采用模块化设计，支持Docker容器化部署，具备增量扫描、智能过滤、代理轮换和外部同步等高级功能。项目使用Python 3.11构建，通过uv包管理器安装依赖，利用GitHub API进行代码搜索，并通过可配置的同步机制将有效密钥发送至Gemini Balancer或GPT Load Balancer等外部服务。本技术文档将深入解析其Docker构建过程、系统架构和核心功能实现。

## 项目结构
项目采用清晰的分层目录结构，将不同功能模块分离，便于维护和扩展。

```mermaid
graph TD
A[项目根目录] --> B[app]
A --> C[common]
A --> D[scripts]
A --> E[utils]
A --> F[配置与文档]
B --> B1[hajimi_king.py]
C --> C1[Logger.py]
C --> C2[config.py]
D --> D1[dry_run.py]
E --> E1[file_manager.py]
E --> E2[github_client.py]
E --> E3[sync_utils.py]
F --> F1[Dockerfile]
F --> F2[pyproject.toml]
F --> F3[README.md]
F --> F4[docker-compose.yml]
F --> F5[CHANGELOG.md]
F --> F6[first_deploy.sh]
```

**Diagram sources**
- [Dockerfile](file://Dockerfile)
- [pyproject.toml](file://pyproject.toml)
- [README.md](file://README.md)

**本文档引用的文件**
- [Dockerfile](file://Dockerfile)
- [pyproject.toml](file://pyproject.toml)
- [README.md](file://README.md)

## 核心组件
项目的核心功能由多个协同工作的Python模块构成。主程序`hajimi_king.py`负责协调整个工作流，从`common`包中导入配置和日志工具，利用`utils`包中的`github_client`执行搜索，`file_manager`管理数据持久化，并通过`sync_utils`实现与外部服务的异步通信。系统采用命令行参数和环境变量双重配置机制，支持灵活的部署模式，如仅ModelScope模式或兼容模式。其核心逻辑包括查询规范化、密钥提取、验证和结果保存，形成了一个完整的闭环。

**本文档引用的文件**
- [app/hajimi_king.py](file://app/hajimi_king.py)
- [common/config.py](file://common/config.py)
- [common/Logger.py](file://common/Logger.py)
- [utils/github_client.py](file://utils/github_client.py)
- [utils/file_manager.py](file://utils/file_manager.py)
- [utils/sync_utils.py](file://utils/sync_utils.py)

## 架构概述
系统采用微内核架构，`hajimi_king.py`作为主控制器，协调各个独立的服务模块。配置管理、日志记录、GitHub API交互、文件系统操作和外部同步服务被设计为独立的、高内聚低耦合的组件。这种设计使得系统易于测试、维护和扩展。数据流始于配置加载和查询读取，经由GitHub搜索获取代码片段，再通过正则表达式提取潜在密钥，最后经过验证和分类，持久化到文件系统或异步发送到外部负载均衡器。

```mermaid
graph LR
A[配置文件 .env] --> B(hajimi_king.py)
C[查询文件 queries.txt] --> B
B --> D[github_client]
D --> E[GitHub API]
E --> D
D --> B
B --> F[file_manager]
B --> G[sync_utils]
F --> H[数据目录 /app/data]
G --> I[Gemini Balancer]
G --> J[GPT Load Balancer]
```

**Diagram sources**
- [app/hajimi_king.py](file://app/hajimi_king.py)
- [common/config.py](file://common/config.py)
- [utils/github_client.py](file://utils/github_client.py)
- [utils/file_manager.py](file://utils/file_manager.py)
- [utils/sync_utils.py](file://utils/sync_utils.py)

## 详细组件分析
### 主程序分析
`hajimi_king.py`是整个应用的入口点和控制中心。它首先解析命令行参数以确定运行模式，然后进行系统配置检查和文件管理器初始化。主循环按顺序处理每个搜索查询，对返回的代码片段进行过滤和处理。对于每个有效文件，它会提取密钥，进行验证，并将结果分类保存。

#### 主程序类图
```mermaid
classDiagram
class hajimi_king {
+main()
+process_item(item)
+validate_gemini_key(api_key)
+should_skip_item(item, checkpoint)
+print_skip_stats()
}
class github_client {
+search_for_keys(query)
+get_file_content(item)
}
class file_manager {
+save_valid_keys()
+save_rate_limited_keys()
+save_checkpoint()
+load_checkpoint()
}
class sync_utils {
+add_keys_to_queue(keys)
+shutdown()
}
class config {
+GITHUB_TOKENS
+DATA_PATH
+PROXY_LIST
+check()
}
hajimi_king --> github_client : "使用"
hajimi_king --> file_manager : "使用"
hajimi_king --> sync_utils : "使用"
hajimi_king --> config : "依赖"
file_manager --> config : "依赖"
sync_utils --> config : "依赖"
```

**Diagram sources**
- [app/hajimi_king.py](file://app/hajimi_king.py)
- [utils/github_client.py](file://utils/github_client.py)
- [utils/file_manager.py](file://utils/file_manager.py)
- [utils/sync_utils.py](file://utils/sync_utils.py)
- [common/config.py](file://common/config.py)

### 配置管理分析
`config.py`模块封装了所有应用配置，通过`os.getenv`从环境变量和`.env`文件中加载。它定义了GitHub令牌、代理设置、数据路径、同步服务端点等关键参数。`Config`类提供了`parse_bool`和`get_random_proxy`等实用方法，简化了配置的使用。该模块在启动时会进行完整性检查，确保必要配置项已设置，从而避免运行时错误。

**本文档引用的文件**
- [common/config.py](file://common/config.py)

### 文件管理分析
`file_manager.py`是系统的核心服务之一，负责所有持久化操作。它管理一个`Checkpoint`数据类，用于存储上次扫描时间、已处理的文件哈希（SHA）和查询，实现增量扫描。它还负责创建和管理日志文件、密钥文件，并根据日期动态更新文件名。`FileManager`类在初始化时会加载查询列表，并提供保存有效密钥、限流密钥和检查点的方法。

**本文档引用的文件**
- [utils/file_manager.py](file://utils/file_manager.py)

### 同步工具分析
`sync_utils.py`实现了与外部负载均衡器的异步通信。它使用`ThreadPoolExecutor`创建后台线程，通过定时器定期将待发送的密钥队列批量发送到Gemini Balancer或GPT Load Balancer。该模块实现了错误处理和重试逻辑，并将发送结果记录到日志文件中。`SyncUtils`实例在全局创建，确保在整个应用生命周期内可用。

**本文档引用的文件**
- [utils/sync_utils.py](file://utils/sync_utils.py)

## 依赖分析
项目依赖关系清晰，主程序依赖于所有工具模块，而工具模块又共同依赖于配置和日志模块。

```mermaid
graph TD
A[app/hajimi_king.py] --> B[common/config.py]
A --> C[common/Logger.py]
A --> D[utils/github_client.py]
A --> E[utils/file_manager.py]
A --> F[utils/sync_utils.py]
D --> B
D --> C
E --> B
E --> C
F --> B
F --> C
F --> E
```

**Diagram sources**
- [app/hajimi_king.py](file://app/hajimi_king.py)
- [common/config.py](file://common/config.py)
- [common/Logger.py](file://common/Logger.py)
- [utils/github_client.py](file://utils/github_client.py)
- [utils/file_manager.py](file://utils/file_manager.py)
- [utils/sync_utils.py](file://utils/sync_utils.py)

## 性能考量
系统的性能主要受GitHub API速率限制和网络延迟影响。通过多GitHub令牌轮换和代理支持，可以有效规避IP封禁，提高搜索成功率。`github_client`中的指数退避重试机制增强了网络请求的鲁棒性。`sync_utils`的异步批处理设计避免了主工作流因外部API调用而阻塞，保证了核心扫描任务的连续性。建议使用高性能代理和多个有效的GitHub令牌以获得最佳性能。

## 故障排除指南
常见问题及解决方案：
- **问题：** GitHub搜索返回403错误。
  **解决方案：** 检查`GITHUB_TOKENS`环境变量是否正确配置，确保令牌具有`public_repo`权限，并未过期。
- **问题：** 密钥验证总是失败。
  **解决方案：** 检查`HAJIMI_CHECK_MODEL`配置是否正确，或尝试更换代理。
- **问题：** Docker容器无法启动。
  **解决方案：** 确保`.env`文件存在且路径正确，数据卷`./data`有读写权限。
- **问题：** 未发现任何密钥。
  **解决方案：** 检查`queries.txt`中的查询表达式是否有效，可参考GitHub代码搜索语法进行优化。

**本文档引用的文件**
- [README.md](file://README.md)
- [common/Logger.py](file://common/Logger.py)

## 结论
Hajimi King是一个功能强大且设计良好的自动化密钥发现工具。其模块化架构和清晰的依赖关系使得代码易于理解和维护。Docker化部署简化了环境配置，而丰富的配置选项则提供了极大的灵活性。通过深入理解其Docker构建过程和内部组件，用户可以有效地部署、定制和优化此工具，以满足特定的密钥发现需求。