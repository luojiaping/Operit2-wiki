---
title: 应用组装——CoreApplication 门面
module: core
platforms: [all]
sources: [core/crates/application/README.md, core/crates/application/core/src/lib.rs, core/crates/application/core/src/device_transport.rs]
date: 2026-11-11
---

## 概述

`CoreApplication` 是 Operit2 Core 树的组装根与生命周期所有者（`core/crates/application/README.md:9`）。
README 声明 application 域是 `runtime`、`proxy`、`node`、`access` 四类 crate 组装成一棵长期 Core 树的唯一位置（`core/crates/application/README.md:5`）；“唯一位置”是文档声明，本页未在全库核实，下列其余结论来自 `core` crate 的实现。
Host 侧使用本域提供的句柄与 Core 树打交道，`UI`、命令解析、平台适配器留在 Core 所有权图之外（`core/crates/application/README.md:5`）。
Core 整体的 crate 拆分见 [[core-overview|Core 总览与 crate 边界]]；Runtime 层面的组装细节见 [[core-runtime|Runtime 总览与 OperitApplication]]；节点运行时的细节见 [[core-node-runtime|节点——节点运行时]]；本地代理见 [[core-proxy|代理生成——扫描、发射器与本地代理运行时]]。

## AI 速览

- `CoreApplication` — 一棵 Core 树的门面与生命周期所有者（`core/crates/application/core/src/lib.rs:69`）
- `CoreApplicationConfig` — 启动一棵 Core 树所需的 Host 输入（`core/crates/application/core/src/lib.rs:24`）
- `LocalCoreProxy` — 本地 Core 客户端入口（`core/crates/application/core/src/lib.rs:70`）
- `CoreNodeRouter` — 拥有 Rust 路由分发的路由器（`core/crates/application/core/src/lib.rs:219`）
- `CoreNodeLocalRuntime` — 节点树拥有的本地运行时能力句柄（`core/crates/application/core/src/lib.rs:214`）
- `RuntimeRemoteLinkService` — Access 服务门面（`core/crates/application/core/src/lib.rs:234`）
- `NodeServices` — 应用、CLI 与 Router 共用的节点服务（`core/crates/application/core/src/lib.rs:45`）
- `OperitPluginSdkIpcBridge` — Plugin SDK IPC 桥，可为空（`core/crates/application/core/src/lib.rs:76`）
- `Channel` — 一条双工传输通道（`core/crates/application/core/src/device_transport.rs:12`）
- `ChannelRegistry` — 通道注册表（`core/crates/application/core/src/device_transport.rs:21`）
- `execute_transport` — 设备传输操作的入口（`core/crates/application/core/src/device_transport.rs:108`）

主入口：`CoreApplication::start`（`core/crates/application/core/src/lib.rs:81`）。
数据流向：Host 以 `HostManager` 与 `LinkDeviceInfo` 组装 `CoreApplicationConfig`（`core/crates/application/core/src/lib.rs:24`）→
`start` 由此建出 `LocalCoreProxy`（`core/crates/application/core/src/lib.rs:86`）→
再由它派生 `CoreNodeRouter`（`core/crates/application/core/src/lib.rs:132`）→
再创建 `RuntimeRemoteLinkService`（`core/crates/application/core/src/lib.rs:141`）→
Host 拿 `localClient()` 等句柄使用（`core/crates/application/core/src/lib.rs:209`）→
`shutdown()` 停整棵树（`core/crates/application/core/src/lib.rs:239`）。

## 核心机制

**组装件：四类 crate 在这里汇合**

- 组装件之一是 `OperitApplication`，即 runtime 应用入口（`core/crates/application/core/src/lib.rs:84`）。
- 组装件之二是 `LocalCoreProxy`，即 proxy 本地客户端（`core/crates/application/core/src/lib.rs:86`）。
- 组装件之三是 `CoreNodeRouter`，即 node 侧路由（`core/crates/application/core/src/lib.rs:132`）。
- 组装件之四是 `NodeServices`，即 node 侧共用服务（`core/crates/application/core/src/lib.rs:93`）。
- 组装件之五是 `RuntimeRemoteLinkService`，即 access 服务门面（`core/crates/application/core/src/lib.rs:141`）。

**启动配置**

- `CoreApplicationConfig` 只公开 `hostManager` 与 `deviceInfo` 两个字段，其余三个字段私有（`core/crates/application/core/src/lib.rs:24`）。
- `new` 接受 `hostManager` 与 `deviceInfo`，并把 `startSpaceSync` 默认设为 `true`（`core/crates/application/core/src/lib.rs:34`）。
- `withNodeServices` 注入应用、`CLI` 与 `Router` 共用的 `NodeServices`（`core/crates/application/core/src/lib.rs:45`）。
- `withNodeServices` 接收 `mut self` 并返回 `Self`（`core/crates/application/core/src/lib.rs:45`）。
- `withSpaceSync` 选择 Core 应用是否拥有持久化 `Space` 同步器（`core/crates/application/core/src/lib.rs:52`）。
- `withSpaceSync` 接收 `mut self` 并返回 `Self`（`core/crates/application/core/src/lib.rs:52`）。
- `withLocalClientConfigurator` 在本地客户端被 Core 树共享前运行一次设置钩子（`core/crates/application/core/src/lib.rs:59`）。
- `withLocalClientConfigurator` 接收 `mut self` 并返回 `Self`（`core/crates/application/core/src/lib.rs:59`）。

**启动装配**

- `start` 是三个公开启动入口中唯一的 `async` 函数（`core/crates/application/core/src/lib.rs:81`）。
- `start` 从 `CoreApplicationConfig` 启动一棵 Core 树（`core/crates/application/core/src/lib.rs:81`）。
- `start` 先用 `hostManager` 创建 `OperitApplication` 并调用 `onCreate`，再用它创建 `LocalCoreProxy`（`core/crates/application/core/src/lib.rs:84`）。
- `localClientConfigurator` 若已设置，在本地客户端被共享前对 `LocalCoreProxy` 运行一次（`core/crates/application/core/src/lib.rs:87`）。
- `start` 未收到 `NodeServices` 时新建 `HostRuntimePeerService` 并包进 `NodeServices`（`core/crates/application/core/src/lib.rs:93`）。
- start 的最后一步是调 `installNodeServices` 安装节点服务（`core/crates/application/core/src/lib.rs:98`）。
- `startWithLocalClient` 接受调用方拥有的 `LocalCoreProxy` 启动 Core 树（`core/crates/application/core/src/lib.rs:104`）。
- `startWithSharedLocalClient` 接受共享的 `Arc` 包裹 `LocalCoreProxy` 启动 Core 树（`core/crates/application/core/src/lib.rs:113`）。
- `startWithSharedLocalClient` 以 `true` 为第三个参数调用 `startWithSharedLocalClientConfigured`（`core/crates/application/core/src/lib.rs:117`）。
- `startWithSharedLocalClient` 新建 `HostRuntimePeerService` 并包进 `NodeServices` 再安装（`core/crates/application/core/src/lib.rs:118`）。
- `startWithSharedLocalClientConfigured` 的第三个参数 `startSpaceSync` 决定持久化工作线程是否由本 Core 树拥有（`core/crates/application/core/src/lib.rs:129`）。
- `startWithSharedLocalClientConfigured` 是私有函数，只在 `start` 与 `startWithSharedLocalClient` 内部调用（`core/crates/application/core/src/lib.rs:126`）。
- 节点运行时取自 `localClient` 的 `coreNodeLocalRuntime` 方法（`core/crates/application/core/src/lib.rs:131`）。
- `CoreNodeRouter` 由 `nodeRuntime` 创建并包进 `Arc`（`core/crates/application/core/src/lib.rs:132`）。
- `nodeRuntime` 字段的类型是 `CoreNodeLocalRuntime`（`core/crates/application/core/src/lib.rs:71`）。
- `nodeRouter` 绑定 `localClient` 的 `deviceToolService` 作为设备工具服务（`core/crates/application/core/src/lib.rs:133`）。
- 代码注释写明，精简或测试 Host 省略任务调度时，设备调用明确失败，Core 启动与同步本地工具仍可用（`core/crates/application/core/src/lib.rs:134`）。
- 只有 `hostManager` 提供 `hostRuntimeTaskSchedulerHost` 时才绑定 `CoreDeviceToolRuntime`（`core/crates/application/core/src/lib.rs:136`）。
- `RuntimeRemoteLinkService` 由 `nodeRuntime` 与 `nodeRouter` 创建（`core/crates/application/core/src/lib.rs:141`）。
- `initializeDeviceInfo` 初始化设备资料，失败时只记日志并保留原 `deviceInfo`（`core/crates/application/core/src/lib.rs:144`）。
- `localClient` 绑定路由变更处理函数，把变更请求转发给 `accessServices` 的 `requestChangeRoute`（`core/crates/application/core/src/lib.rs:152`）。
- `pluginSdkIpcBridge` 只在 `hostManager` 提供 `pluginSdkIpcHost` 时创建（`core/crates/application/core/src/lib.rs:162`）。
- 创建 Plugin SDK IPC 桥要求 Host 任务调度器，缺失时返回 `"Plugin SDK IPC requires a Host task scheduler"` 错误（`core/crates/application/core/src/lib.rs:167`）。
- Plugin SDK IPC 桥的目标是 `nodeRouter`，类型为 `PluginSdkLinkTarget`（`core/crates/application/core/src/lib.rs:168`）。
- 桥使用 `operit_proxy_local` 的 `pluginSdkSurface` 作为插件表面（`core/crates/application/core/src/lib.rs:174`）。
- `pluginSdkIpcBridge` 创建后调用 `bridge.start`，失败时装配返回错误（`core/crates/application/core/src/lib.rs:177`）。
- `installNodeServices` 先把 `NodeServices` 装进 `nodeRouter`，再按 `startSpaceSync` 决定是否启动 Space 同步（`core/crates/application/core/src/lib.rs:193`）。
- `startSpaceSync` 失败时只记日志，不返回错误（`core/crates/application/core/src/lib.rs:196`）。

**Host 侧拿什么句柄**

- `CoreApplication` 持有 `localClient`、`nodeRuntime`、`nodeRouter`、`deviceInfo`、`startSpaceSync`、`accessServices`、`pluginSdkIpcBridge` 七个字段（`core/crates/application/core/src/lib.rs:72`）。
- `CoreApplication` 的七个字段均无 `pub` 修饰，外部只能通过访问器方法拿句柄（`core/crates/application/core/src/lib.rs:72`）。
- `localClient` 返回 `Arc` 包裹的 `LocalCoreProxy` 句柄（`core/crates/application/core/src/lib.rs:209`）。
- `nodeRuntime` 返回节点树拥有的 `CoreNodeLocalRuntime` 句柄（`core/crates/application/core/src/lib.rs:214`）。
- `nodeRouter` 返回拥有 Rust 路由分发的 `CoreNodeRouter`（`core/crates/application/core/src/lib.rs:219`）。
- `deviceInfo` 返回 `LinkDeviceInfo` 引用（`core/crates/application/core/src/lib.rs:224`）。
- `localNodeId` 取自 `nodeRouter` 的 `localNodeId`（`core/crates/application/core/src/lib.rs:226`）。
- `updateDeviceInfo` 经 `accessServices` 的 `updateDeviceInfo` 更新设备资料并写回（`core/crates/application/core/src/lib.rs:228`）。
- `accessServices` 返回 `RuntimeRemoteLinkService` 门面（`core/crates/application/core/src/lib.rs:234`）。
- `nodeServices` 在未装配时返回错误，不把缺失服务伪装成配对成功（`core/crates/application/core/src/lib.rs:204`）。

**Host 侧不碰什么**

- `UI`、命令解析、平台适配器留在 Core 所有权图之外（`core/crates/application/README.md:5`）。
- `CoreApplication` 的内部字段不对外公开，Host 侧不直接读写 `localClient`、`nodeRouter`、`accessServices` 等字段（`core/crates/application/core/src/lib.rs:72`）。

**停止**

- `shutdown` 先停 Space 同步，再停 `peers`，最后调 `shutdownNow`（`core/crates/application/core/src/lib.rs:239`）。
- `shutdownNow` 停桥、停 Space 同步、关 ToolPkg 执行引擎、清 Core 路由运行时（`core/crates/application/core/src/lib.rs:251`）。
- `CoreApplication` 被 `drop` 时停桥、停 Space 同步、关 ToolPkg 执行引擎（`core/crates/application/core/src/lib.rs:262`）。

**ToolPkg 双工传输门面**

- 文件头注释说明，本文件是 `ToolPkg` 之上的双工门面，复用已认证的 `Watch` 与 `Push` 路由（`core/crates/application/core/src/device_transport.rs:1`）。
- `Channel` 记录 `owner`、`node`、`send`、`receive`、`cancel` 五个字段（`core/crates/application/core/src/device_transport.rs:12`）。
- `ChannelRegistry` 是 `Mutex` 保护的 `HashMap`，键为 `String`，值为 `Channel`（`core/crates/application/core/src/device_transport.rs:21`）。
- `ChannelRegistry` 被 `drop` 时向全部通道发送取消信号（`core/crates/application/core/src/device_transport.rs:24`）。
- `decode` 按 `kind` 标签把 `Value` 译为 `CoreValue`（`core/crates/application/core/src/device_transport.rs:29`）。
- `kind` 标签的取值含 `null`、`bytes`、`list`、`map`、`bool`、`number`、`string` 七种（`core/crates/application/core/src/device_transport.rs:36`）。
- `encode` 把 `CoreValue` 编码为带 `kind` 标签的值（`core/crates/application/core/src/device_transport.rs:43`）。
- `ChannelGuard` 被 `drop` 时把通道从注册表移除（`core/crates/application/core/src/device_transport.rs:57`）。
- 通道任务用 `tokio::select` 等待取消信号、发送块、接收块三者之一完成（`core/crates/application/core/src/device_transport.rs:91`）。
- 发送块把值发进输入会话，收到 `None` 时关闭输入（`core/crates/application/core/src/device_transport.rs:70`）。
- 接收块把远端事件编码后回传，`Completed` 事件后只返回 `done` 为 `true` 的结果（`core/crates/application/core/src/device_transport.rs:83`）。
- `close_transport_handle` 按 `handle` 关闭单个通道并发送取消信号（`core/crates/application/core/src/device_transport.rs:99`）。
- `close_transport_owner` 关闭指定 `owner` 的全部通道（`core/crates/application/core/src/device_transport.rs:102`）。
- `execute_transport` 接收 `JsToolCallRequest` 与 `JsDeviceToolCall`，返回 `JsToolCallResult`（`core/crates/application/core/src/device_transport.rs:108`）。
- `execute_transport` 要求参数含 `op`，缺失时报 `Missing transport operation` 错误（`core/crates/application/core/src/device_transport.rs:110`）。
- `execute_transport` 要求参数含 `__transport_owner`，缺失时报 `Missing transport owner` 错误（`core/crates/application/core/src/device_transport.rs:111`）。
- `call` 与 `open` 共用一个分支（`core/crates/application/core/src/device_transport.rs:113`）。
- `send`、`finish`、`next`、`close` 共用一个分支（`core/crates/application/core/src/device_transport.rs:143`）。
- `call` 与 `open` 分支先取 `router`，运行时已释放时报 `Owning Core runtime is no longer available` 错误（`core/crates/application/core/src/device_transport.rs:114`）。
- 传输 `target` 须非空且不超过 256 字符（`core/crates/application/core/src/device_transport.rs:115`）。
- 传输 `method` 须非空且不超过 128 字符（`core/crates/application/core/src/device_transport.rs:117`）。
- `call` 经 `router` 的 `callNode` 发起单次节点调用并编码结果（`core/crates/application/core/src/device_transport.rs:119`）。
- 打开通道前已有 8 个通道时报 `Too many open device channels` 错误（`core/crates/application/core/src/device_transport.rs:122`）。
- 通道插入注册表时再次检查 8 通道上限（`core/crates/application/core/src/device_transport.rs:132`）。
- `open` 用 `router` 的 `watchNode` 建立输出流（`core/crates/application/core/src/device_transport.rs:124`）。
- `open` 用 `router` 的 `openPushNode` 建立输入会话（`core/crates/application/core/src/device_transport.rs:125`）。
- 双工通道任务以 `device-duplex-channel` 为名交给 Host 任务调度器（`core/crates/application/core/src/device_transport.rs:136`）。
- open 成功返回带 `handle` 的值（`core/crates/application/core/src/device_transport.rs:140`）。
- `send`、`finish`、`next`、`close` 分支要求参数含 `handle`（`core/crates/application/core/src/device_transport.rs:144`）。
- `close` 一个已不存在的通道返回成功结果，不报错（`core/crates/application/core/src/device_transport.rs:148`）。
- 通道 `owner` 或 `node` 与请求不符时报 `Device channel owner mismatch` 错误（`core/crates/application/core/src/device_transport.rs:151`）。
- `close` 从注册表移除通道并发送取消信号（`core/crates/application/core/src/device_transport.rs:154`）。
- `finish` 不带值，只发关闭信号；`send` 带值（`core/crates/application/core/src/device_transport.rs:157`）。
- 未知 `op` 返回 `Unknown transport operation` 错误（`core/crates/application/core/src/device_transport.rs:163`）。
- 成功时返回 `success` 为 `true` 的 `JsToolCallResult`（`core/crates/application/core/src/device_transport.rs:165`）。

## 关键符号

- `CoreApplication` — 一棵 Core 树的门面与生命周期所有者（`core/crates/application/core/src/lib.rs:69`）
- `CoreApplicationConfig` — 启动一棵 Core 树所需的 Host 输入（`core/crates/application/core/src/lib.rs:24`）
- `LocalClientConfigurator` — 在共享本地客户端前对 `LocalCoreProxy` 做设置的 `FnOnce` 闭包类型（`core/crates/application/core/src/lib.rs:22`）
- `LocalCoreProxy` — 本地 Core 客户端入口（`core/crates/application/core/src/lib.rs:70`）
- `CoreNodeRouter` — Rust 路由分发所有者（`core/crates/application/core/src/lib.rs:219`）
- `CoreNodeLocalRuntime` — 节点树拥有的本地运行时能力句柄（`core/crates/application/core/src/lib.rs:214`）
- `RuntimeRemoteLinkService` — Access 服务门面（`core/crates/application/core/src/lib.rs:234`）
- `NodeServices` — 应用、CLI 与 Router 共用的节点服务（`core/crates/application/core/src/lib.rs:45`）
- `HostRuntimePeerService` — 未提供 `NodeServices` 时新建的节点对等服务（`core/crates/application/core/src/lib.rs:95`）
- `OperitApplication` — Runtime 应用入口，`start` 先建它并调 `onCreate`（`core/crates/application/core/src/lib.rs:84`）
- `OperitPluginSdkIpcBridge` — Plugin SDK IPC 桥（`core/crates/application/core/src/lib.rs:76`）
- `Channel` — 一条双工传输通道（`core/crates/application/core/src/device_transport.rs:12`）
- `ChannelRegistry` — 通道注册表（`core/crates/application/core/src/device_transport.rs:21`）
- `ChannelGuard` — 通道析构时从注册表移除的守卫（`core/crates/application/core/src/device_transport.rs:57`）
- `execute_transport` — 设备传输操作的入口（`core/crates/application/core/src/device_transport.rs:108`）
- `decode` — 按 `kind` 标签把 `Value` 译为 `CoreValue`（`core/crates/application/core/src/device_transport.rs:29`）
- `encode` — 把 `CoreValue` 编码为带 `kind` 标签的值（`core/crates/application/core/src/device_transport.rs:43`）

## 调用链

1. Host 以 `HostManager` 与 `LinkDeviceInfo` 组装 `CoreApplicationConfig`（`core/crates/application/core/src/lib.rs:24`）。
2. 可选：`withNodeServices` 注入应用、CLI 与 Router 共用的 `NodeServices`（`core/crates/application/core/src/lib.rs:45`）。
3. 可选：`withSpaceSync` 选择 Core 应用是否拥有持久化 Space 同步器（`core/crates/application/core/src/lib.rs:52`）。
4. 可选：`withLocalClientConfigurator` 在本地客户端被 Core 树共享前运行一次设置钩子（`core/crates/application/core/src/lib.rs:59`）。
5. `start` 先用 `hostManager` 创建 `OperitApplication` 并调用 `onCreate`，再用它创建 `LocalCoreProxy`（`core/crates/application/core/src/lib.rs:84`）。
6. `startWithSharedLocalClientConfigured` 从 `localClient` 取 `coreNodeLocalRuntime`，建 `CoreNodeRouter` 并绑定 `deviceToolService`（`core/crates/application/core/src/lib.rs:131`）。
7. 有 `hostRuntimeTaskSchedulerHost` 时绑定 `CoreDeviceToolRuntime`，否则跳过（`core/crates/application/core/src/lib.rs:136`）。
8. 创建 `RuntimeRemoteLinkService`，初始化设备资料（失败只记日志）（`core/crates/application/core/src/lib.rs:141`）。
9. 绑定路由变更处理函数，变更请求转发给 `requestChangeRoute`（`core/crates/application/core/src/lib.rs:152`）。
10. `pluginSdkIpcBridge` 只在提供 `pluginSdkIpcHost` 时创建（`core/crates/application/core/src/lib.rs:162`）。
11. `pluginSdkIpcBridge` 创建后调用 `bridge.start`（`core/crates/application/core/src/lib.rs:177`）。
12. `installNodeServices` 把 `NodeServices` 装进 `nodeRouter`，再按 `startSpaceSync` 启动 Space 同步（`core/crates/application/core/src/lib.rs:193`）。
13. 使用阶段：Host 经 `localClient()` 拿本地 Core 客户端句柄（`core/crates/application/core/src/lib.rs:209`）。
14. 使用阶段：Host 经 `nodeRouter()` 拿路由分发句柄（`core/crates/application/core/src/lib.rs:219`）。
15. 使用阶段：Host 经 `accessServices()` 拿 Access 服务门面（`core/crates/application/core/src/lib.rs:234`）。
16. 停止：`shutdown()` 先停 Space 同步，再停 `peers`，最后调 `shutdownNow()`（`core/crates/application/core/src/lib.rs:239`）。
17. `shutdownNow()` 停桥、停 Space 同步、关 ToolPkg 执行引擎、清 Core 路由运行时（`core/crates/application/core/src/lib.rs:251`）。
18. `open` 分支建 `watchNode` 输出流与 `openPushNode` 输入会话（`core/crates/application/core/src/device_transport.rs:124`）。
19. open 成功返回带 `handle` 的值（`core/crates/application/core/src/device_transport.rs:140`）。

## 来源

- `core/crates/application/README.md`
- `core/crates/application/core/src/lib.rs`
- `core/crates/application/core/src/device_transport.rs`

基线：AAswordman/Operit2 @ 364d1d594。
