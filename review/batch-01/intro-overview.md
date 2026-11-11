---
title: Operit2 是什么
module: intro
platforms: [all]
sources: [README.md, README-zh.md]
date: 2026-11-11
---

# Operit2 是什么

## 概述

Operit2 的一句话定位是 *An Agent core that connects your device space*（一个 Agent 核心，连接你的设备空间）[^1]。它是面向个人用户的开源跨设备 Agent 项目，让手机、桌面和云端设备各展所长，对话、任务与上下文在个人设备空间中延续[^2]。项目源于 Operit 的 Android Agent 实践，当前打磨多端同步、跨设备执行和恢复体验[^3]。

项目处于 Preview Release（预览）阶段[^4]。预览阶段底层结构、数据格式、插件契约和跨设备流程未冻结，破坏性更新在明确声明的预期内[^5]。完整章节见 [[outline|Operit2-wiki 大纲 v1]]。

[^1]: README.md:3
[^2]: README.md:10
[^3]: README.md:12
[^4]: README.md:4
[^5]: README.md:14

## AI 速览

核心符号：

- CoreNode — 运行 Core 的一个实例，Agent 工作流的执行单位（README.md:18）
- Host — 本机能力提供者，CoreNode 通过它使用文件、终端、浏览器（README.md:18）
- Space — 组织节点间协作与持久化同步的范围（README.md:18）
- Binding — 记录任务下一步由哪个节点继续（README.md:18）
- Link Access — 节点间认证连接的建立方式（README.md:43）
- PeerLink — 承载 Space 请求和同步流量的传输层（README.md:43）
- ToolPkg — 用 JavaScript/TypeScript 编写的插件包格式（README.md:59）
- Skill — 可导入、可见性可控的工作流和知识资源（README.md:61）
- MCP — 外部模型上下文协议服务器接入点（README.md:62）
- Web Access — 浏览器访问已运行 CoreNode 的入口（README.md:72）

主入口：`operit2`（无参数默认进入 TUI，README.md:175），命令参数以 `operit2 --help` 的实际输出为准（README.md:53）。

数据流向一句话：用户在发起设备开始任务 → 工具结果持久化后同步记录到达目标节点 → 目标节点继续执行 → 进展经异步同步回到其他设备（README.md:22）。

## 核心机制

### 设备如何协作

每个运行 Core 的实例称为 `CoreNode`，通过本机 `Host` 使用文件、终端、浏览器等能力。`Space` 组织节点之间的协作与持久化同步，`Binding` 记录任务下一步由哪个节点继续（README.md:18）。

Space 中的节点地位对等。Linux 云端设备可以因长期在线或具备合适能力而承担更多任务，但不会因此成为固定的主节点。加入 Space 也不会自动授予节点其他设备的系统权限（README.md:20）。

任务交接以工具结果已持久化、下一轮模型请求尚未开始为边界。目标节点取得必要的同步记录后，再继续后续工作。这种接续依赖保存的上下文和任务事实，不搬迁正在运行的模型请求、终端进程或浏览器会话（README.md:22）。

目标体验是在手机上发起任务，由合适的设备持续执行，在桌面上查看或批准，最后回到手机接收结果；主对话保留发起设备的交互归属，子任务在执行节点推进，其他设备通过异步同步了解进展。完整体验仍在完善中（README.md:24）。

### 单节点 Agent 的能力

每个 CoreNode 可以独立运行自己的 Agent 工作流，具体能力取决于平台 Host、模型 Provider 和本地配置（README.md:30）。当前仓库已经包含：

- 对话、会话分支、消息管理、附件、角色卡、角色群组和提示词配置（README.md:32）
- Provider 配置、模型参数、工具调用、请求队列和可下载的本地聊天模型，本地推理使用嵌入的 llama.cpp 与 MNN CPU 推理（README.md:33）
- 工作区、文件操作、项目模板、命令和备份/导入导出（README.md:34）
- 终端会话、PTY 输入和输出流（README.md:35）
- 网页访问、浏览器自动化、工作区浏览器和运行时 WebView 会话投影（README.md:36）
- 记忆、摘要、语音识别、语音合成以及其他内置工具（README.md:37）

这些能力并不在所有平台完全相同。真正能否执行某项操作，要看目标节点的 Host 描述、系统权限、已安装服务和当前用户批准（README.md:39）。

### 多节点连接与 Space

CLI 已提供配对、发现、连接、session、传输方式和 Space 成员管理入口。节点之间使用 Link Access 建立认证连接，再由 PeerLink 承载 Space 请求和同步流量，适合在本地或受控局域网环境中试验（README.md:43）。

```powershell
operit2 cli link serve --bind <address:port> --token <strong-token>
operit2 cli link discover
operit2 cli link connect <url> --token <token> --save <session-name>
operit2 cli link space join <session-name>
operit2 cli link space show
```

命令参数以 `operit2 --help` 和 `operit2 cli` 的实际输出为准。不要使用默认开发 token 对公网监听，也不要把 token、私钥或真实业务数据放入公开日志或截图（README.md:53）。

### 插件、Skill、ToolPkg 和 MCP

Operit2 的扩展面已经从“内置工具集合”逐步抽象为可管理的运行时与 SDK（README.md:57）：

- 使用 JavaScript/TypeScript 编写 Package 和 ToolPkg（README.md:59）
- 使用 JavaScript bridge、Wasm runtime 和 Compose DSL 构建工具与界面（README.md:60）
- 使用 Skill 提供可导入、可见性可控的工作流和知识资源（README.md:61）
- 连接 MCP server，管理 MCP 配置、工具和本地 MCP 进程（README.md:62）
- 使用插件市场和包管理命令安装、启用、停用、查看和执行扩展（README.md:63）
- 通过 Rust SDK、TypeScript 声明和 codegen 提供插件开发入口，接口仍在演进（README.md:64）

插件及其依赖须按目标平台验证，跨设备可移植性仍是重点建设方向（README.md:66）。

### Web Access

Web Access 让浏览器访问一个已运行的 CoreNode；打开页面不会自动让浏览器成为 Space 中的独立节点。浏览器 Host 与 WebAssembly 运行时是另一条工程路径，两者的能力和部署方式需要分别看待（README.md:72）。

Web Access 不是自动加入 Space 的浏览器节点，也不是中心化 Agent Server（README.md:99）。WebAssembly/browser Host 是浏览器运行时的本地能力边界，与 Web Access 访问面分开，具体能力取决于浏览器和当前 Web 构建模式（README.md:100）。

### 数据备份与迁移

Operit2 把迁移视为个人设备连续性的一部分。CLI 已提供身份、存储路径、快照导出/恢复、备份检查以及 Operit 一代快照检查入口（README.md:80）：

```powershell
operit2 cli identity list
operit2 cli storage paths
operit2 cli export snapshot <snapshot.zip>
operit2 cli backup inspect <snapshot.zip>
operit2 cli backup restore <snapshot.zip>
```

快照、配置和身份数据的具体范围以当前命令帮助和格式版本为准。活动中的进程和实时会话仍然属于原节点，不能把“有备份”理解成已经完成了所有运行时的无缝迁移（README.md:90）。

### 平台与访问面

| 入口或平台 | 在当前架构中的位置 | 当前边界 |
| --- | --- | --- |
| Flutter App | 移动端和桌面端的主要图形访问面，也可以承载一个 CoreNode | Android、Windows、Linux、macOS、iOS、OpenHarmony 和 Web 的 Host/构建条件不同（README.md:96） |
| Rust CLI/TUI | 本地 CoreNode 和运维/开发入口 | 当前 CLI Host 主要覆盖 Windows、Linux 和 macOS（README.md:97） |
| PB_SBC01_H3 | 运行完整 Core 的 Linux 硬件主控入口 | 使用 Linux Host 加板卡 Host 能力，应用入口位于 `edge/boards/pb_sbc01_h3`（README.md:98） |
| Web Access | 访问某个已运行 CoreNode 的浏览器入口 | 不是自动加入 Space 的浏览器节点，也不是中心化 Agent Server（README.md:99） |
| WebAssembly/browser Host | 浏览器运行时的本地能力边界 | 与 Web Access 访问面分开，具体能力取决于浏览器和当前 Web 构建模式（README.md:100） |
| Linux 云端设备 | Space 中的普通 CoreNode | 长期在线可以承担更多任务，但不因此拥有中心身份（README.md:101） |
| ESP32 Edge Node | 设备原生业务与 Edge Service 能力节点 | 保存身份、配对、空间控制及自身配置；支持有界独立运行和按需使用 Core，不保存完整业务副本（README.md:102） |
| Server | 未来的部署形态和 Host 方向 | 当前仓库还没有可以直接发布的完整 Server 产品（README.md:103） |

仓库包含多平台 Host 适配路径，但“能够构建”不等于“已经完成跨设备互操作验证”（README.md:105）。

### 用户控制与安全边界

Operit2 采用从外到内逐层收紧的能力模型（README.md:109）：

```text
0. App Runtime Sandbox
   虚拟机、容器、系统账号、Android 应用沙盒或服务器部署边界

1. Host Authorization
   操作系统真正授予本机 Host 的文件、终端、网络和系统能力

2. AI Capability Limit
   用户为 AI 选择的 ReadOnly、WorkspaceWrite 或 Full 能力模式

3. User Tool Approval
   用户对具体工具调用的允许、询问或禁止
```

必须保持的原则：

- Space 成员资格不会授予其他节点读取本机文件、使用本机终端或获得管理员/root 能力（README.md:127）
- API key、设备私钥、配对密钥、session 和本地平台权限默认属于节点本地，不会因为加入 Space 自动复制（README.md:128）
- `ModelConfigManager::new` 用 `preferenceStore` 创建模型配置存储（core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:136）
- `preferenceStore` 调用 `PreferencesDataStore::newWithStorage`（core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:108）
- `newWithStorage` 创建 Space 偏好存储（core/crates/persistence/store/src/PreferencesDataStore.rs:2924）
- 同步偏好存储创建时建立 `PreferencesSyncDescriptor`（core/crates/persistence/store/src/PreferencesDataStore.rs:2956）
- 同步偏好存储创建时建立 `SyncOperationStore` 同步操作存储（core/crates/persistence/store/src/PreferencesDataStore.rs:2962）
- `ModelConfigManager` 把完整 `ProviderProfile` 作为同步偏好值写入 `provider_<id>`（core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:1332）
- 该 `ProviderProfile` 包含 `apiKey` 和 `apiKeyPool`（core/crates/foundation/model/src/ModelConfigData.rs:604）
- 因此 Provider 凭证存在随配置同步的路径，不能把它与设备身份、配对密钥、OS 权限统称“不复制”（core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:1332）
- 该路径与 README.md:128 的“不复制”原则存在冲突（README.md:128）
- 本页未做真实双设备同步实验，上述路径是否实际触发同步未验证
- `Full` 只表示 AI 能力限制放宽，不表示 Host 提权，也不能创造操作系统没有的能力（README.md:129）
- 应用内部的 sandbox 字段和 UI 不能冒充真实的操作系统级隔离边界（README.md:130）
- 对外监听 Link 或 Web Access 前，应使用强 token、受限监听地址、TLS/防火墙和脱敏日志（README.md:131）
- 用户始终拥有是否同步敏感数据、是否批准具体动作以及是否让节点参与协作的决定权（README.md:132）

### 预览阶段与演进方向

Rust Core、平台 Host、节点连接、持久化同步和插件运行时已经形成工程基础。当前优先修复问题、打磨稳定性，尤其关注跨设备执行的取消、重连、资源释放和失败恢复（README.md:138）。

以下方向仍在设计、完善或验证中：结合节点健康状态（Health）、长期执行记录和用户偏好选择合适的设备；在适合的任务上引入备用节点、受控并行和子任务拆分；完善插件 SDK 的兼容声明与跨节点接续能力；改善新设备加入、数据恢复和长期在线部署的使用体验；验证节点数量增加后的发现、路由与同步成本（README.md:142）。

当前以个人设备空间为主要场景，尚未验证数千节点调度，也不以企业组织治理为产品目标。长期运行品质仍需持续测试，Rust 本身不构成无资源泄漏的保证（README.md:148）。

## 关键符号

- `CoreNode` — 运行 Core 的一个实例，Agent 工作流的执行单位（README.md:18）
- `Host` — 本机能力提供者，CoreNode 通过它使用文件、终端、浏览器（README.md:18）
- `Space` — 组织节点间协作与持久化同步的范围（README.md:18）
- `Binding` — 记录任务下一步由哪个节点继续（README.md:18）
- `Link Access` — 节点间认证连接的建立方式（README.md:43）
- `PeerLink` — 承载 Space 请求和同步流量的传输层（README.md:43）
- `ToolPkg` — 用 JavaScript/TypeScript 编写的插件包格式（README.md:59）
- `Skill` — 可导入、可见性可控的工作流和知识资源（README.md:61）
- `MCP` — 外部模型上下文协议服务器接入点（README.md:62）
- `Web Access` — 浏览器访问已运行 CoreNode 的入口（README.md:72）
- `ReadOnly` / `WorkspaceWrite` / `Full` — 用户为 AI 选择的三档能力模式（README.md:119）
- `operit2` — Rust CLI/TUI 可执行文件，无参数默认进入 TUI（README.md:170）

## 调用链

### 任务跨设备接续（当前已实现的边界）

1. 发起设备的 Agent 执行工具调用，工具结果持久化（README.md:22）
2. 下一轮模型请求尚未开始，交接窗口打开（README.md:22）
3. 目标节点取得必要的同步记录（README.md:22）
4. 目标节点依据保存的上下文和任务事实继续工作；正在运行的模型请求、终端进程、浏览器会话不搬迁（README.md:22）

### 节点加入 Space（CLI）

1. `operit2 cli link serve --bind <address:port> --token <strong-token>` 启动监听（README.md:46）
2. `operit2 cli link discover` 发现节点（README.md:46）
3. `operit2 cli link connect <url> --token <token> --save <session-name>` 建立认证连接并保存 session（README.md:46）
4. `operit2 cli link space join <session-name>` 加入 Space（README.md:46）
5. `operit2 cli link space show` 查看 Space 状态（README.md:46）

### Web Access 本地开发

1. 在 `apps/flutter/app` 目录运行（apps/flutter/app/web/README.md:23）
2. 运行命令是 `fvm flutter run -d web-server`（apps/flutter/app/web/README.md:30）
3. 浏览器打开 `http://127.0.0.1:4835`（apps/flutter/app/web/README.md:30）
4. Flutter 原生读取 `web_dev_config.yaml`，不需要单独的 Node 代理进程（apps/flutter/app/web/README.md:18）
5. 开发服务器地址由 `web_dev_config.yaml` 配置为 `127.0.0.1:4835`（apps/flutter/app/web_dev_config.yaml:4）
6. README.md:202 的双终端加 Node 代理流程引用的 `tools/dev_web_access_proxy.mjs` 在基线中不存在，照做会失败（README.md:202）

## 来源

- README.md（262 行，全文已读）
- README-zh.md（262 行，全文已读）
- core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs（核对 preferenceStore、writeProvider 相关行）
- core/crates/foundation/model/src/ModelConfigData.rs（核对 ProviderProfile 字段）
- core/crates/persistence/store/src/PreferencesDataStore.rs（核对 newWithStorage 与同步存储创建）
- apps/flutter/app/web/README.md（核对 Web 开发流程）
- apps/flutter/app/web_dev_config.yaml（核对开发服务器地址）
- edge/boards/pb_sbc01_h3/Cargo.toml（核对板卡入口）

两份白皮书 PDF（docs/Operit2-Technical-Whitepaper.pdf、docs/Operit2技术白皮书.pdf）只核存在，未读正文，本页不引用白皮书内容。

架构文档中标注为“目标”“计划”或“演进方向”的内容，不代表所有平台已经实现；判断当前实际行为时，以源码、命令帮助输出、构建结果和目标平台运行结果为准（README.md:246）。
