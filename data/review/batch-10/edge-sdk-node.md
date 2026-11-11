---
title: Edge 节点 crate
module: edge
platforms: [all]
sources: 5
date: 2026-11-11
---

## 概述

- `operit-node-edge` 是设备侧 Edge Services 与 Link 适配器。`edge/sdk/node/README.md:3`
- 本 crate 拥有类型化设备服务、原生应用端点 hook 与 `EdgePeerRouter`。`edge/sdk/node/README.md:6`
- 本 crate 不组装 `OperitApplication`、Agent 运行时、providers、`ToolPkg` 引擎或完整业务副本。`edge/sdk/node/README.md:7`
- 设备应用在组合根注入共享节点身份、配对、Space 控制与存储服务，这些服务不在本 crate 内重复实现。`edge/sdk/node/README.md:9`
- `EdgeNode` 拥有一个 Edge 节点的轻量设备侧 Core 服务。`edge/sdk/node/src/lib.rs:69`
- 板级能力由服务经 `HostManager` 选择，不由传输决定。`edge/sdk/node/src/lib.rs:425`

## AI 速览

- `EdgeNode` — 一个 Edge 节点的轻量设备侧 Core 服务。`edge/sdk/node/src/lib.rs:69`
- `EdgePeerRouter` — 只接受本地 Target 路由与已定义共享 Space 控制调用的路由适配器。`edge/sdk/node/src/PeerRouter.rs:18`
- `createPeerService` — 用共享配对与会话引擎创建 Edge 接收端。`edge/sdk/node/src/peer.rs:17`
- `DeviceIoService` — 类型化设备 I/O 操作。`edge/sdk/node/src/service.rs:207`
- `RobotFaceService` — 类型化机器人表情操作。`edge/sdk/node/src/service.rs:222`
- `ScreenService` — 最小显示操作。`edge/sdk/node/src/lib.rs:33`
- `EdgeCallHandler` — 设备应用提供的原生调用分发。`edge/sdk/node/src/lib.rs:42`
- 主入口函数为 `EdgeNode` 的 `new`。`edge/sdk/node/src/lib.rs:82`
- `fromHostManager` 用一个 `HostManager` 的设备服务创建节点。`edge/sdk/node/src/lib.rs:112`
- 路由入口为 `EdgePeerRouter` 的 `new`。`edge/sdk/node/src/PeerRouter.rs:25`
- 数据流向一句话：本地调用先经 `dispatchAsyncCall` 问原生 `callHandler`，无应答时回落到 `dispatchCall`。`edge/sdk/node/src/lib.rs:369`

## 核心机制

### 路由：接受什么，不承担什么

- `EdgePeerRouter` 只提供本地设备服务执行，没有第二套配对协议。`edge/sdk/node/src/PeerRouter.rs:18`
- `EdgePeerRouter` 只接受本地 Target 路由与已定义的共享 Space 控制调用。`edge/sdk/node/README.md:13`
- `EdgePeerRouter` 不是完整 Core Binding 路由器，也不是中继实现。`edge/sdk/node/README.md:14`
- `check` 要求 `targetNodeId` 等于本节点 id，否则返回 `EDGE_ROUTE_TARGET_MISMATCH`。`edge/sdk/node/src/PeerRouter.rs:48`
- 只接受 `RoutedCoreRequestKind::Target` 路由，其他路由返回 `EDGE_ROUTE_UNSUPPORTED`。`edge/sdk/node/src/PeerRouter.rs:56`
- `EdgePeerRouter` 的 `new` 以 `nodeId` 创建路由。`edge/sdk/node/src/PeerRouter.rs:25`
- `install` 第二次安装返回 `Edge node already installed` 错误。`edge/sdk/node/src/PeerRouter.rs:32`
- `installSpace` 第二次安装返回 `Edge Space services already installed` 错误。`edge/sdk/node/src/PeerRouter.rs:37`
- `spaceChannelScope` 未安装 Space 服务时返回 `Ok(None)`。`edge/sdk/node/src/PeerRouter.rs:208`

### 原生服务注册

- `EdgeNode` 的 `new` 以 `Arc<dyn DeviceIoService>` 创建节点。`edge/sdk/node/src/lib.rs:82`
- `headless` 创建无 GPIO 与显示的节点，仍可加入 Space。`edge/sdk/node/src/lib.rs:87`
- `fromHostManager` 用一个 `HostManager` 的设备服务创建节点。`edge/sdk/node/src/lib.rs:112`
- `withRobotFaceService` 注册类型化机器人表情服务。`edge/sdk/node/src/lib.rs:117`
- `withScreenService` 注册可选通用显示能力。`edge/sdk/node/src/lib.rs:123`
- `withNodeServices` 注入同一个外层 `NodeServices` 接口，Edge 不自行实现配对或鉴权。`edge/sdk/node/src/lib.rs:100`
- `withCallHandler` 安装设备应用拥有的原生请求分发。`edge/sdk/node/src/lib.rs:129`
- `withStreamHandlers` 安装设备应用的通用 Stream 与 ReverseStream 端点。`edge/sdk/node/src/lib.rs:135`
- `EdgeCallHandler` 返回 `None` 时内置服务接管节点，没有插件注册表或清单。`edge/sdk/node/src/lib.rs:42`
- `createDeviceIoService` 从 `HostManager` 构建设备 I/O 服务。`edge/sdk/node/src/service.rs:329`
- `createRobotFaceService` 从 `HostManager` 构建机器人表情服务。`edge/sdk/node/src/service.rs:417`
- `HostDeviceIoService` 在 Host API 上实现类型化设备 I/O 操作。`edge/sdk/node/src/service.rs:232`
- `HostRobotFaceService` 在 Host API 上实现类型化机器人表情操作。`edge/sdk/node/src/service.rs:334`
- `DeviceIoService` 定义 `setDigitalOutput` 与 `getDigitalOutput`。`edge/sdk/node/src/service.rs:207`
- `watchDigitalOutput` 打开一个数字输出的类型化状态流。`edge/sdk/node/src/service.rs:213`
- `RobotFaceService` 定义 `setExpression` 与 `getExpression`。`edge/sdk/node/src/service.rs:222`
- `watchExpression` 打开一个机器人表情的类型化状态流。`edge/sdk/node/src/service.rs:228`
- `ScreenService` 定义 `getScreenSnapshot` 与 `sendScreenInput` 两个最小显示操作。`edge/sdk/node/src/lib.rs:33`
- `setDigitalOutput` 写入后向活跃订阅者发布已提交状态。`edge/sdk/node/src/service.rs:287`
- 未安装 device I/O Host API 时 `setDigitalOutput` 返回 `device I/O Host API is not installed` 错误。`edge/sdk/node/src/service.rs:287`
- `watchDigitalOutput` 先读当前状态作初始快照再注册订阅。`edge/sdk/node/src/service.rs:306`
- `DeviceIoStateStream` 释放时取消服务订阅。`edge/sdk/node/src/service.rs:108`
- `RobotFaceStateStream` 释放时取消服务订阅。`edge/sdk/node/src/service.rs:194`
- `EdgeServiceError` 携带一条类型化 Edge 服务操作失败的消息。`edge/sdk/node/src/service.rs:16`

### 配对与 Space 加入：两个独立步骤

- `peer::createPeerService` 使用共享的确认码配对与加密会话引擎。`edge/sdk/node/README.md:12`
- 配对与 Space 准入是两个独立步骤。`edge/sdk/node/README.md:13`
- Edge 启动使用共享确认码配对引擎，会话加密与 Space 授权留在共享运行时。`edge/sdk/node/src/peer.rs:1`
- `createPeerService` 复用已有配对与会话引擎，Core 与 Edge 共享确认码、加密与授权。`edge/sdk/node/src/peer.rs:9`
- `createPeerService` 用 `HostRuntimePeerService::newWithLimits` 创建 Edge 接收端。`edge/sdk/node/src/peer.rs:17`
- `installSpace` 安装 `NodeSpaceService`。`edge/sdk/node/src/PeerRouter.rs:37`
- Space 调用先分流到三个 Space 目标：`NODE_SPACE_TARGET`、`NODE_SPACE_APPROVAL_TARGET` 与 `NODE_SPACE_CONTROL_TARGET`。`edge/sdk/node/src/PeerRouter.rs:85`
- `checkSpaceOrigin` 要求 Space 调用直连来源、不可中继，`NODE_SPACE_TARGET` 调用 ttl 必须为 0。`edge/sdk/node/src/PeerRouter.rs:63`
- 准入前调用只允许零跳，同 Space 控制与评审调用在直连上可带正 TTL。`edge/sdk/node/src/PeerRouter.rs:90`
- 准入与控制目标的请求 `spaceId` 必须等于当前 Space 的 `spaceId`，否则返回 `SPACE_ID_MISMATCH`。`edge/sdk/node/src/PeerRouter.rs:113`
- 未安装 Space 服务时 Space 调用返回 `EDGE_SPACE_UNAVAILABLE`。`edge/sdk/node/src/PeerRouter.rs:99`
- `prepareRoutedCall` 只处理 `NODE_SPACE_TARGET` 的 `snapshot` 方法。`edge/sdk/node/src/PeerRouter.rs:141`
- `prepareEncodedCall` 只处理控制通道的 `exchange` 与 `exchangeBounded`、申请侧的 `requestJoin`、`cancelJoin` 与 `joinStatus`，以及 `observeSpaceSnapshot`。`edge/sdk/node/src/PeerRouter.rs:159`

### 没有 storage.provide 时：能保存什么，不能参与什么

- Edge 不用 `storage.provide` 也能持久化自身配置与资源。`edge/sdk/node/README.md:22`
- 有界设备偏好在共享 Space 控制通道上交换，带成员与撤销检查。`edge/sdk/node/README.md:23`
- 完整业务副本要求两端都具备存储能力与真实 Core 存储服务。`edge/sdk/node/README.md:24`
- 控制通道的 `exchangeBounded` 是 `prepareEncodedCall` 处理的有界交换入口之一。`edge/sdk/node/src/PeerRouter.rs:159`
- Host API traits 提供硬件、I/O 与存储，设备应用拥有行为。`edge/sdk/node/README.md:20`
- 配置 `ToolPkg` 在有能力的宿主上运行，设备配置保存后不必保持安装或运行。`edge/sdk/node/README.md:29`
- 当前 ESP32 应用支持原生设备服务、有界独立 HTTP 聊天与可选远程 Core 聊天。`edge/sdk/node/README.md:27`

### 调用分发：缺失端点怎么办

- `dispatchCall` 把 `setDigitalOutput` 与 `getDigitalOutput` 分发到设备 I/O 服务。`edge/sdk/node/src/lib.rs:150`
- `setExpression` 与 `getExpression` 分发到机器人表情服务。`edge/sdk/node/src/lib.rs:155`
- `getScreenSnapshot` 与 `sendScreenInput` 分发到显示服务。`edge/sdk/node/src/lib.rs:160`
- 未知目标或方法返回 `methodNotFound` 方法错误。`edge/sdk/node/src/lib.rs:165`
- 屏幕目标的 watch 快照返回 `watchNotFound`。`edge/sdk/node/src/lib.rs:210`
- `dispatchAsyncCall` 先问 `callHandler`，无应答时回落到 `dispatchCall`。`edge/sdk/node/src/lib.rs:367`
- `watch` 只把 device-io、robot-face、screen 之外目标的请求交给 `watchHandler`。`edge/sdk/node/src/lib.rs:397`
- `openPush` 无 `pushHandler` 时返回 `methodNotFound`。`edge/sdk/node/src/lib.rs:413`
- 应用用 `withCallHandler` 注册原生调用，用 `withStreamHandlers` 注册可选输出与输入端点。`edge/sdk/node/README.md:17`
- 原生端点使用 Call、Watch / Stream 与 Push / ReverseStream，缺失端点返回标准方法错误。`edge/sdk/node/README.md:18`

## 关键符号

- `EdgeNode` — 一个 Edge 节点的轻量设备侧 Core 服务。`edge/sdk/node/src/lib.rs:69`
- `EdgePeerRouter` — 只接受本地 Target 路由与已定义共享 Space 控制调用的路由适配器。`edge/sdk/node/src/PeerRouter.rs:18`
- `createPeerService` — 用共享配对与会话引擎创建 Edge 接收端。`edge/sdk/node/src/peer.rs:17`
- `DeviceIoService` — 类型化设备 I/O 操作。`edge/sdk/node/src/service.rs:207`
- `RobotFaceService` — 类型化机器人表情操作。`edge/sdk/node/src/service.rs:222`
- `ScreenService` — 最小显示操作。`edge/sdk/node/src/lib.rs:33`
- `HostDeviceIoService` — 在 Host API 上实现类型化设备 I/O 操作。`edge/sdk/node/src/service.rs:232`
- `HostRobotFaceService` — 在 Host API 上实现类型化机器人表情操作。`edge/sdk/node/src/service.rs:334`
- `EdgeCallHandler` — 设备应用提供的原生调用分发。`edge/sdk/node/src/lib.rs:42`
- `EdgeWatchHandler` — 设备应用提供的原生输出流类型。`edge/sdk/node/src/lib.rs:50`
- `EdgePushHandler` — 设备应用提供的原生输入流类型。`edge/sdk/node/src/lib.rs:57`
- `EdgeServiceError` — 类型化 Edge 服务操作失败。`edge/sdk/node/src/service.rs:16`
- `DeviceIoStateStream` — 类型化数字输出状态流。`edge/sdk/node/src/service.rs:30`
- `RobotFaceStateStream` — 类型化机器人表情状态流。`edge/sdk/node/src/service.rs:116`
- `NodeSpaceService` — Space 服务，经 `installSpace` 安装。`edge/sdk/node/src/PeerRouter.rs:37`

## 调用链

1. 设备应用用 `EdgeNode` 的 `new` 创建节点。`edge/sdk/node/src/lib.rs:82`
2. `fromHostManager` 用一个 `HostManager` 的设备服务创建节点。`edge/sdk/node/src/lib.rs:112`
3. 设备应用用 `withCallHandler` 注册原生调用，用 `withStreamHandlers` 注册流端点。`edge/sdk/node/README.md:17`
4. `createPeerService` 用共享配对引擎建立加密会话，配对与 Space 准入分开进行。`edge/sdk/node/src/peer.rs:9`
5. `EdgePeerRouter` 的 `new` 以 `nodeId` 创建路由。`edge/sdk/node/src/PeerRouter.rs:25`
6. `install` 安装 `EdgeNode`，`installSpace` 安装 `NodeSpaceService`。`edge/sdk/node/src/PeerRouter.rs:32`
7. `routedCall` 的第一步是执行 `check`。`edge/sdk/node/src/PeerRouter.rs:80`
8. Space 调用再过 `checkSpaceOrigin`：直连来源、不可中继。`edge/sdk/node/src/PeerRouter.rs:63`
9. 本地调用经 `dispatchAsyncCall` 分发到类型化设备服务。`edge/sdk/node/src/lib.rs:367`
10. Space 目标调用交给 Space 服务的 `acceptPeerSpaceCall` 处理。`edge/sdk/node/src/PeerRouter.rs:121`

## 来源

- `edge/sdk/node/README.md`：crate 说明，全文 30 行。
- `edge/sdk/node/src/lib.rs`：`EdgeNode` 与原生端点分发，全文 1040 行。
- `edge/sdk/node/src/PeerRouter.rs`：`EdgePeerRouter` 路由与 Space 分流，全文 214 行。
- `edge/sdk/node/src/peer.rs`：`createPeerService` 配对接收端，全文 20 行。
- `edge/sdk/node/src/service.rs`：类型化设备 I/O 与机器人表情服务，全文 521 行。

否定性核验方法：2026-11-12 对基线 AAswordman/Operit2 @ 364d1d594 的本地 checkout 执行 `grep -rn "storage.provide" edge/sdk/node/README.md edge/sdk/node/src/lib.rs edge/sdk/node/src/PeerRouter.rs edge/sdk/node/src/peer.rs edge/sdk/node/src/service.rs`，唯一命中为 `edge/sdk/node/README.md:23`，4 个 Rust 源文件零命中；因此本页只转述 README 关于持久化与完整业务副本的断言，不写任何 `storage.provide` 实现细节。

范围说明：`platforms: [all]` 指本 crate 的 Rust 代码本身不区分 Host，板级能力由服务经 `HostManager` 选择。`edge/sdk/node/src/lib.rs:425`

范围说明：ESP32 相关断言只适用于 ESP32 应用。`edge/sdk/node/README.md:27`

未读文件：本页只读 5 个 seed 文件；`edge/sdk/node/Cargo.toml` 与引用的共享运行时（`operit_node_runtime`、`operit_link`、`operit_host_api`、`operit_edge_contract`）未读未引。
