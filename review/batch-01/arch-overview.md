---
title: 整体架构（总览）
module: arch
platforms: [all]
sources: [README.md, docs/core-node-space-binding-architecture.md, core/CRATE_BOUNDARIES.md, core/crates/node/peer-link/Cargo.toml, core/crates/node/runtime/Cargo.toml, core/crates/runtime/application/Cargo.toml, core/crates/application/core/Cargo.toml]
date: 2026-11-11
---

# 整体架构（总览）

## 概述

Operit2 的一句话定位是 An Agent core that connects your device space（`README.md:3`）。

它是一个跨设备 Agent 项目，让手机、桌面、云设备各自发挥所长，对话、任务与上下文在个人设备空间内延续（`README.md:10`）。

README 明确标注 Preview 阶段，底层结构、数据格式、插件契约与跨设备工作流有 breaking changes 的风险（`README.md:14`）。

每个运行 Core 的实例称为 CoreNode，通过本地 Host 使用文件、终端、浏览器等能力（`README.md:18`）。

Space 组织节点间的协作与持久化同步，Binding 记录哪个节点继续执行任务（`README.md:18`）。

数据走两条独立路径：持久化业务数据在获准成员间持续同步，实时调用经转发层送到目标节点。机制细节见 [[sync-overview|同步总览：Space 持久化同步]] 与 [[core-overview|Core 总览与 crate 边界]]，本页只写总览，不展开。

## AI 速览

- `CoreNode` — 运行 Operit Core 的应用实例（`docs/core-node-space-binding-architecture.md:42`）
- `Space` — 节点成员、路由与持久化同步的范围（`docs/core-node-space-binding-architecture.md:28`）
- `Binding` — key 对应的下一次路由执行由哪个 CoreNode 完成（`docs/core-node-space-binding-architecture.md:141`）
- `OperitApplication` — CoreNode 内的应用本体（`docs/core-node-space-binding-architecture.md:44`）
- `LocalCoreProxy` — CoreNode 内的本地代理（`docs/core-node-space-binding-architecture.md:45`）
- `HostManager` — 拥有活跃 host 能力集与生命周期侧 host 句柄（`core/CRATE_BOUNDARIES.md:140`）
- `CoreNodeRouter` — 本机请求路由入口（`docs/core-node-space-binding-architecture.md:348`）
- `SpacePersistenceSyncService` — CoreNode 启动后长期运行的持久化同步服务（`docs/core-node-space-binding-architecture.md:202`）
- `RoutedLink` — Peer Link 转发的外层封装（`docs/core-node-space-binding-architecture.md:289`）
- `operit-runtime` — 父编排 crate，拥有应用启动与服务装配（`core/CRATE_BOUNDARIES.md:41`）
- `operit-host-api` — host 能力 trait 与 HostManager 的边界（`core/CRATE_BOUNDARIES.md:9`）

主入口：本地 App 始终首先进入本机 CoreNodeRouter；CLI 提供配对、发现、连接、会话、传输方式与 Space 成员管理入口（`README.md:47`）。

数据流向一句话：持久化业务数据经 SpacePersistenceSyncService 在获准成员间持续同步（`docs/core-node-space-binding-architecture.md:202`），实时调用经 RoutedLink 转发到 Binding 指定的 CoreNode（`docs/core-node-space-binding-architecture.md:294`）。

## 核心机制

### 核心概念与执行模型

执行模型只包含 `CoreNode` 与 `Binding` 两个概念（`docs/core-node-space-binding-architecture.md:24`）。

`Space` 是节点成员、路由与持久化同步的范围，不是执行容器，不拥有 Agent、聊天或运行时（`docs/core-node-space-binding-architecture.md:28`）。

架构中不引入 Chat Core、Agent Core、`Env`、`Placement`、`Lease`、`Circuit`、`Capability` 或远程数据放置 `Ownership` 模型（`docs/core-node-space-binding-architecture.md:34`）。

`CoreNode` 由 `nodeId`、`OperitApplication`、`LocalCoreProxy`、`HostManager` 组成（`docs/core-node-space-binding-architecture.md:44`）。

每个 `CoreNode` 只有一个 `OperitApplication` 和一个 `HostManager`（`docs/core-node-space-binding-architecture.md:479`）。

`CoreNode` 之间地位对等，服务监听方、连接发起方与请求执行方只是一次连接或调用中的角色（`docs/core-node-space-binding-architecture.md:57`）。

`Space` 由 `spaceId` 与 `members` 组成，members 是 nodeId 的集合（`docs/core-node-space-binding-architecture.md:64`）。

`Space` 只负责三件事：确定协作范围、确定哪些已配对连接可承载 Space 流量、确定持久化数据在哪些 `CoreNode` 间持续同步（`docs/core-node-space-binding-architecture.md:69`）。

`Space` 不表达执行位置，也不表达数据归属（`docs/core-node-space-binding-architecture.md:77`）。

配对完成后不会自动加入设备空间（`docs/core-node-space-binding-architecture.md:93`）。

`Binding` 由 `key`、`nodeId`、`generation` 组成，只表达 key 对应的下一次路由执行由哪个 `CoreNode` 完成（`docs/core-node-space-binding-architecture.md:141`）。

`Binding` 不表示业务数据位于目标节点；聊天路由直接使用现有 `chatId` 作为 key（`docs/core-node-space-binding-architecture.md:146`）。

每次比较写入成功后 `generation` 单调递增，同时标识目标节点即将执行的 continuation（`docs/core-node-space-binding-architecture.md:171`）。

`list_core_nodes` 只读取本机已经同步的 Space 成员视图（`docs/core-node-space-binding-architecture.md:159`）。

`switch_core` 在调用时按同一份路由视图校验目标，目标不是 Space 成员或当前不可达时工具直接返回失败（`docs/core-node-space-binding-architecture.md:164`）。

### 两条独立的数据路径

持久化同步与实时传输是两条独立路径。

`SpacePersistenceSyncService` 是 CoreNode 启动后长期运行的服务，经认证路由与可达成员持续交换本地操作日志和向量时钟（`docs/core-node-space-binding-architecture.md:202`）。

内置 `admin`、`user`、`relay` 角色均具有 `storage.provide`；业务副本同步只在双方具备 storage.provide 且实际提供 Core 存储服务时运行（`docs/core-node-space-binding-architecture.md:185`）。

每个同步周期对每个可达成员先发送一次常量大小的 `syncClockDigest` 探针（`docs/core-node-space-binding-architecture.md:218`）。

同步页单侧一页最多 `DEFAULT_SYNC_PAGE_BYTES`（4 MiB）（`docs/core-node-space-binding-architecture.md:233`）。

下列数据保持节点本地，不进入 Space 持久化同步：CoreNode 身份私钥、两两配对密钥和 session、`HostManager` 平台状态、本机监听地址、本机平台能力与临时交互句柄（`docs/core-node-space-binding-architecture.md:258`）。

实时传输承载 Core call、Core watch、Core push、stream event、Agent turn continuation、Host interaction response、Space 路由控制消息（`docs/core-node-space-binding-architecture.md:274`）。

实时传输不负责复制持久化业务数据；实时 continuation 要求的同步时钟只是交接屏障，不表示数据迁移（`docs/core-node-space-binding-architecture.md:280`）。

`requiredClock` 是持久化同步屏障；execution generation 来自 Binding 比较写入（`docs/core-node-space-binding-architecture.md:407`）。

### 路由与转发

`RoutedLink` 由 `spaceId`、`targetNodeId`、`ttl`、`payload` 组成（`docs/core-node-space-binding-architecture.md:294`）。

外层不携带 `chatId`、`Binding`、`envId`、文件路径或 Host 配置（`docs/core-node-space-binding-architecture.md:294`）。

每个 CoreNode 保存 Space 拓扑，第一跳必须是当前活跃且获准承载该 Space 流量的直接 Peer Link（`docs/core-node-space-binding-architecture.md:312`）。

`ttl` 每转发一次减一；无有效路径、TTL 用尽或目标不属于 Space 时属于路由失败（`docs/core-node-space-binding-architecture.md:321`）。

本地 App 始终首先进入本机 `CoreNodeRouter`（`docs/core-node-space-binding-architecture.md:348`）。

只有模型执行、工具循环、取消当前执行与实时执行状态进入 Binding 路由；聊天历史读取、配置编辑等持久化数据操作在本地 Core 执行（`docs/core-node-space-binding-architecture.md:362`）。

请求类型由真实 Core 方法上的 `operit_core_route` 注解声明，经 typed Core codegen 生成；未标注的方法始终留在本地 Core（`docs/core-node-space-binding-architecture.md:371`）。

### 工具边界切换 CoreNode

切换 `CoreNode` 的边界是工具调用已完成、工具结果已持久化、下一轮模型请求尚未发起（`docs/core-node-space-binding-architecture.md:385`）。

任务交接的边界是工具结果已持久化且下一轮模型请求尚未开始；交接不移动进行中的模型请求、终端进程或浏览器会话（`README.md:22`）。

每轮模型请求开始前，CoreNode 必须确认 Binding(chatId) 指向自己；只有当前执行节点能够提交 Agent 发起的切换（`docs/core-node-space-binding-architecture.md:416`）。

每一跳只接受已配对 Peer 的签名流量（`docs/core-node-space-binding-architecture.md:460`）。

Space 把多个已配对 CoreNode 组成同一个持续同步网络；Binding 决定一个聊天的下一步在哪个 CoreNode 执行；实时转发层把现有 Link 调用和 Agent continuation 送到该节点（`docs/core-node-space-binding-architecture.md:493`）。

### 平台入口与能力边界

Flutter App 是移动与桌面主图形入口，也能托管 CoreNode；Host 与构建条件在 Android、Windows、Linux、macOS、iOS、OpenHarmony、Web 上不同（`README.md:96`）。

当前 CLI Host 主要覆盖 Windows、Linux、macOS（`README.md:97`）。

PB_SBC01_H3 是运行完整 Core 的 Linux 硬件控制入口，应用入口是 edge/boards/pb_sbc01_h3（`README.md:98`）。

Linux 云设备是 Space 内普通 CoreNode，始终在线可承担更多任务，但不因此获得中心身份（`README.md:101`）。

ESP32 Edge Node 拥有本地配置与有界操作，参与 Space 控制并可消费 Core 服务，没有完整业务副本（`README.md:102`）。

当前仓库没有可直接发布的完整 Server 产品（`README.md:103`）。

单节点 Agent 的能力在各平台不完全相同，能否执行取决于目标节点的 Host 描述、系统权限、已装服务与当前用户批准（`README.md:39`）。

Web Access 让浏览器访问正在运行的 CoreNode，打开页面不会自动使浏览器成为 Space 内独立节点（`README.md:72`）。

WebAssembly/browser Host 是浏览器运行时的本地能力边界，与 Web Access 是两条不同工程路径（`README.md:100`）。

能力模型从外到内分四层：App Runtime Sandbox 与 Host Authorization（`README.md:115`）。

AI Capability Limit（ReadOnly、WorkspaceWrite、Full）与 User Tool Approval（`README.md:118`）。

Space 成员资格不授予其他节点读取本机文件、使用本机终端或获得管理员/root 能力（`README.md:127`）。

API 密钥、设备私钥、配对密钥、会话与本地平台权限默认属于节点本地，加入 Space 不自动复制（`README.md:128`）。

`Full` 只表示放宽 AI 能力限制，不提升 Host 特权，也不创造操作系统没有的能力（`README.md:129`）。

不要用默认开发 token 对公网监听，也不要把 token、私钥或真实业务数据放进公开日志或截图（`README.md:53`）。

### 依赖方向与父级行为

依赖方向是 plugin-sdk/host-api → util → model → store → tools/local-models/providers/js-bridge → runtime → core-proxy/command-core（`core/CRATE_BOUNDARIES.md:63`）。

子 crate 不得依赖 operit-runtime；operit-runtime 可依赖全部子 crate（`core/CRATE_BOUNDARIES.md:66`）。

`operit-plugin-sdk` 只依赖公共生态 crate（`core/CRATE_BOUNDARIES.md:74`）。

`operit-plugin-theme` 只依赖公共生态 crate；runtime 与未来浏览器/审计适配器可消费它，绝不反向（`core/CRATE_BOUNDARIES.md:75`）。

子 crate 需要父级行为时定义 trait 并消费 trait 对象，由父级 runtime 实现并安装（`core/CRATE_BOUNDARIES.md:99`）。

`ToolRuntimeSupport` 由 operit-runtime 在 services/ToolRuntimeSupportService.rs 实现（`core/CRATE_BOUNDARIES.md:104`）。

`ProviderRuntimeSupport` 由 operit-runtime 在 services/ProviderRuntimeSupportService.rs 实现（`core/CRATE_BOUNDARIES.md:109`）。

`LocalModelRuntimeSupport` 定义本地模型侧请求；operit-runtime 拥有具体实现（`core/CRATE_BOUNDARIES.md:113`）。

`JsExecutionHost` 定义完整的 JavaScript 到应用的执行边界；operit-tools 以真实工具、包、资源与 IPC 逻辑实现它（`core/CRATE_BOUNDARIES.md:123`）。

`JsExecutionProvider` 定义引擎 provider 边界；operit-js-bridge 以 QuickJsExecutionProvider 实现，operit-runtime 把 provider 注入 operit-tools（`core/CRATE_BOUNDARIES.md:126`）。

`HostManager` 拥有活跃 host 能力集与生命周期侧 host 句柄；Host 集成位于 operit-host-api 之后（`core/CRATE_BOUNDARIES.md:140`）。

仓库与持久化数据结构属于 operit-store；可复用值模型属于 operit-model；runtime 服务可组合仓库，但仓库所有权留在 store（`core/CRATE_BOUNDARIES.md:150`）。

`operit-proxy-local` 是桌面投影层，扫描选定公共面并生成面向传输的 Rust 与 Dart 代理代码（`core/CRATE_BOUNDARIES.md:181`）。

`operit-proxy-edge` 是 Edge Service 的类型化投影；`operit-edge-contract` 只含稳定 Edge 地址，远端载体无需导入本地 Edge Node 即可使用同一契约（`core/CRATE_BOUNDARIES.md:184`）。

两个 proxy crate 都不拥有运行时行为、host 实现、provider 逻辑、工具逻辑或存储（`core/CRATE_BOUNDARIES.md:187`）。

架构文档 §8 的模块对照表使用目录式写法，本页按下表核对为当前 crate 名。

`node/peer-link` 对应当前 crate `operit-peer-link`（`core/crates/node/peer-link/Cargo.toml:2`）。

`node/runtime` 对应当前 crate `operit-node-runtime`（`core/crates/node/runtime/Cargo.toml:2`）。

`runtime/application` 对应当前 crate `operit-runtime`（`core/crates/runtime/application/Cargo.toml:2`）。

`application/core` 对应当前 crate `operit-core-application`（`core/crates/application/core/Cargo.toml:2`）。

| 模块（现名） | 职责 | 架构文档 §8 写法 |
| --- | --- | --- |
| operit-store | 操作日志、收据、`Binding` 与各存储 owner 的提交；拓扑记录与确定性路由计算（`docs/core-node-space-binding-architecture.md:442`） | `operit-store` |
| operit-link | `Call`、`Watch`、`Push`、事件、错误和流的协议契约（`docs/core-node-space-binding-architecture.md:443`） | `operit-link` |
| operit-peer-link | 认证连接承载、心跳、请求关联和连接生命周期（`docs/core-node-space-binding-architecture.md:444`） | `node/peer-link` |
| operit-node-runtime | 配对与成员策略、`CoreNodeRouter`、逐跳转发、共享 Watch 与同步调度（`docs/core-node-space-binding-architecture.md:445`） | `node/runtime` |
| operit-proxy-local | 本机类型化代理与业务分发（`docs/core-node-space-binding-architecture.md:446`） | `operit-proxy-local` |
| operit-runtime | 单节点业务运行时、模型工具循环与 handoff（`docs/core-node-space-binding-architecture.md:447`） | `runtime/application` |
| operit-core-application | 组装 Core、Proxy、Node 与 Host 的应用树（`docs/core-node-space-binding-architecture.md:448`） | `application/core` |

## 关键符号

- `operit-host-api` — host 能力 trait 与 HostManager；平台 host 实现该边界，core crate 通过 trait 消费 host 行为（`core/CRATE_BOUNDARIES.md:9`）
- `operit-util` — 共享工具代码、流 helper、日志 helper、序列化、路径布局常量与媒体/文档 helper（`core/CRATE_BOUNDARIES.md:11`）
- `operit-model` — runtime、store、tools、providers、proxy 生成与 host-facing DTO 共用的数据结构（`core/CRATE_BOUNDARIES.md:13`）
- `operit-store` — 持久化层，含 DAO/repository 代码、偏好存储、SQLite/ObjectBox 风格 helper、同步存储与存储 host 注册（`core/CRATE_BOUNDARIES.md:15`）
- `operit-plugin-sdk` — 可发布的插件契约、独立 JavaScript 包解析与管理、固定 JavaScript 工具 API、Compose DSL、`ToolPkg` 归档解析/加载、完整包查询、hook 分发与 JavaScript 执行契约（`core/CRATE_BOUNDARIES.md:17`）
- `operit-plugin-theme` — 只含运行时无关的 theme v1 schema；只依赖公共生态 crate；不做 I/O、Host 调用、运行时启动、插件执行、持久化或主题应用（`core/CRATE_BOUNDARIES.md:20`）
- `operit-tools` — 工具系统，含内置工具、`ToolPkg`、`MCP`、skill 包、权限感知工具注册、包生命周期管理、工具执行元数据与工具侧运行时支持 trait（`core/CRATE_BOUNDARIES.md:27`）
- `operit-local-models` — 本地模型清单、已装模型注册表契约、存储路径 helper 与本地 STT/TTS/聊天会话接口；运行时侧操作经 `LocalModelRuntimeSupport` 暴露（`core/CRATE_BOUNDARIES.md:31`）
- `operit-providers` — provider 契约与内置实现，含 `AIService`、provider 请求/结果/流类型、`ProviderRuntimeSupport`、LLM 适配器、对话编排、TTS/STT/market 服务（`core/CRATE_BOUNDARIES.md:34`）
- `operit-js-bridge` — JavaScript 引擎集成与 JS 侧 ToolPkg 执行面，实现 operit-plugin-sdk 暴露的 JS 执行 trait（`core/CRATE_BOUNDARIES.md:38`）
- `operit-runtime` — 父编排 crate，拥有应用启动、服务装配、插件资产、偏好、工作区服务、聊天服务生命周期、provider 支持实现与 tool 支持实现（`core/CRATE_BOUNDARIES.md:41`）
- `operit-proxy-local` — 构建时代理生成与本地分发，扫描选定公共面并生成 Rust 与 Dart 代理代码（`core/CRATE_BOUNDARIES.md:44`）
- `operit-link` — 传输协议与 client/server 原语（`core/CRATE_BOUNDARIES.md:48`）
- `operit-edge-contract` — 只含共享 Edge Service 地址与属性名，不含 Host 实现或 Link 分发（`core/CRATE_BOUNDARIES.md:49`）
- `operit-node-edge` — 轻量设备侧 Edge Core 节点，是设备能力节点，不是 Space 架构定义的完整 CoreNode 组合（`core/CRATE_BOUNDARIES.md:51`）
- `operit-command-core` — 面向 CLI 的命令层，构建于 runtime 与拆分后的 core crate 之上（`core/CRATE_BOUNDARIES.md:56`）

## 调用链

1. 本地 App 发起请求，始终首先进入本机 `CoreNodeRouter`（`docs/core-node-space-binding-architecture.md:348`）。
2. 普通请求进入 `LocalCoreProxy`；带注解的 Binding 请求经 `Binding(key)` 路由到目标 CoreNode（`docs/core-node-space-binding-architecture.md:354`）。
3. 模型工具循环在工具调用边界切换 CoreNode：模型产生 `switch_core`，源节点验证目标是可达的 Space 成员，在一个事务内持久化 assistant 工具调用、工具结果、chat metadata 与同步操作，Router 比较写入 `Binding(chatId)`，把 Binding record 与 operation 放入 Link route context 发送到目标节点（`docs/core-node-space-binding-architecture.md:395`）。
4. 目标节点的 Router 在调用业务恢复方法前应用并校验 Binding operation，响应业务等待 `requiredClock`，加载已同步 assistant 消息并使用 switch_core 的工具结果发起下一轮模型请求（`docs/core-node-space-binding-architecture.md:407`）。
5. 响应流属于一次用户发起的 execution，不属于执行 CoreNode；最初接受请求的 `CoreNodeRouter` 保持上游流，当前执行节点只产生该 execution 的后续事件（`docs/core-node-space-binding-architecture.md:432`）。
6. `SpacePersistenceSyncService` 经认证路由与可达成员持续交换本地操作日志和向量时钟，同步不依赖当前 Binding（`docs/core-node-space-binding-architecture.md:202`）。
7. CLI 入口：`operit2 cli link serve`、`operit2 cli link discover`、`operit2 cli link connect`、`operit2 cli link space join`、`operit2 cli link space show`（`README.md:47`）。

## 来源

- README.md
- docs/core-node-space-binding-architecture.md
- core/CRATE_BOUNDARIES.md
- core/crates/node/peer-link/Cargo.toml（§8 名称核对用）
- core/crates/node/runtime/Cargo.toml（§8 名称核对用）
- core/crates/runtime/application/Cargo.toml（§8 名称核对用）
- core/crates/application/core/Cargo.toml（§8 名称核对用）
