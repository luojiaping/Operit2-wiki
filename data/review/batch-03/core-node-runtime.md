---
title: 节点——节点运行时
module: core
platforms: [all]
sources: [core/crates/node/README.md, core/crates/node/runtime/src/lib.rs, core/crates/node/runtime/src/CoreNodeRouter.rs, core/crates/node/runtime/src/SpaceRuntime.rs, core/crates/node/runtime/src/PeerSync.rs, core/crates/node/runtime/src/SpacePersistenceSyncService.rs, core/crates/node/runtime/src/NodeSpaceService.rs]
date: 2026-11-11
---

## 概述

节点运行时负责 Space 内调用的路由决策、本地执行与持久化同步，`CoreNodeRouter` 是路由决策的持有者（`core/crates/node/runtime/src/CoreNodeRouter.rs:65`）。
`SpaceRuntime` 持有 Space 侧运行时对象注册表与内嵌流池（`core/crates/node/runtime/src/SpaceRuntime.rs:11`）。
`SpacePersistenceSyncService` 经 Router 与可达的 Space 成员同步持久化数据，不拥有配对、发现或传输（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:152`）。
`NodeSpaceService` 是无应用执行运行时的设备的轻量组装（`core/crates/node/runtime/src/NodeSpaceService.rs:508`）。
Node 负责节点间通信、路由解析与执行（`core/crates/node/README.md:3`）。
节点身份、配对、会话准入与连接生命周期是 node 的职责，不设独立的 `access` 域（`core/crates/node/README.md:4`）。
README 把 `runtime/src/remote` 列为节点身份与会话持久化、配对、认证准入、连接监管及 HTTP 与 WebSocket 服务器与会话适配器的所在位置（`core/crates/node/README.md:12`）。
`runtime/src/remote` 目录在基线树中不存在，README 对它的描述是文档滞后，不得写成已实现（`core/crates/node/README.md:12`）。
本页只写路由、执行与同步；“存什么、怎么存”写在 [[core-persistence-sync|持久化——同步存储]]。
传输载体与路由宏写在 [[core-node-peer-link|节点——PeerLink 传输与路由宏]]。

## AI 速览

- `CoreNodeRouter` — 路由决策与跨节点调用的持有者（`core/crates/node/runtime/src/CoreNodeRouter.rs:65`）
- `CoreNodeLocalRuntime` — 本地执行上下文（`core/crates/node/runtime/src/CoreNodeRouter.rs:82`）
- `GeneratedSpaceRoute` — 生成的 Space 路由元数据（`core/crates/node/runtime/src/lib.rs:30`）
- `GeneratedCoreRoute` — Local 与 Binding 两种路由目标（`core/crates/node/runtime/src/lib.rs:8`）
- `GeneratedRoutePermissionSubject` — Caller 与 Target 两种权限主体（`core/crates/node/runtime/src/lib.rs:15`）
- `GeneratedRouteLifecycle` — Normal、BeforeChangeRoute 与 AfterChangeRoute 三种生命周期（`core/crates/node/runtime/src/lib.rs:22`）
- `SpaceRuntime` — Space 侧运行时对象注册表与内嵌流池（`core/crates/node/runtime/src/SpaceRuntime.rs:11`）
- `SpacePersistenceSyncService` — 可达成员间的持久化同步（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:152`）
- `PeerSyncMethod` — 16 种对端同步方法（`core/crates/node/runtime/src/PeerSync.rs:14`）
- `NodeSpaceService` — 无应用执行运行时的设备的轻量组装（`core/crates/node/runtime/src/NodeSpaceService.rs:508`）
- `SpaceJoinRequest` — 设备入群申请（`core/crates/node/runtime/src/NodeSpaceService.rs:315`）
- `SpaceJoinStatus` — Pending、Approving、Approved、Rejected、Cancelled、Expired 与 Joined 七种状态（`core/crates/node/runtime/src/NodeSpaceService.rs:310`）
- 主入口：`callSpaceWithOrigin` 解析路由并取绑定键（`core/crates/node/runtime/src/CoreNodeRouter.rs:978`）
- 主入口：CoreNodeRouter 的 `routedCall` 处理到达本节点的路由调用（`core/crates/node/runtime/src/CoreNodeRouter.rs:1924`）
- 主入口：SpacePersistenceSyncService 的 `synchronizeOnce` 执行一轮同步（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:362`）
- 主入口：NodeSpaceService 的 `dispatchPeerSpaceCall` 分发对端 Space 调用（`core/crates/node/runtime/src/NodeSpaceService.rs:362`）
- 数据流向：调用 → 路由解析 → 本地执行或跨节点转发 → 持久化操作经同步轮次在可达成员间对账与复制。

## 核心机制

### 路由决策：本地还是跨节点

- `CoreNodeRouter` 持有 `deviceToolService`、`peerServices`、`localCore`、`bindingStore`、`localNodeId`、`spaceStore` 与 `networkControlStore`（`core/crates/node/runtime/src/CoreNodeRouter.rs:69`）。
- `callSpaceWithOrigin` 经 `generated_space_call_route` 解析路由（`core/crates/node/runtime/src/CoreNodeRouter.rs:978`）。
- 路由解析后从请求参数取 `bindingKey`（`core/crates/node/runtime/src/CoreNodeRouter.rs:994`）。
- 路由流程在解析目标前先执行 `prepareCreationBinding`（`core/crates/node/runtime/src/CoreNodeRouter.rs:998`）。
- `routeNodeId` 对 Local 返回本节点，对 Binding 返回 `bindingRouteNodeId`（`core/crates/node/runtime/src/CoreNodeRouter.rs:433`）。
- `shouldRoute` 在 `coreForceLocal` 或目标为 Local 时不路由（`core/crates/node/runtime/src/CoreNodeRouter.rs:2352`）。
- 绑定不存在并返回 `CORE_BINDING_NOT_FOUND` 时不路由（`core/crates/node/runtime/src/CoreNodeRouter.rs:2371`）。
- `shouldRouteWatch` 按 `coreForceLocal`、本地目标、绑定缺失与可达性决定一次 watch 是否跨节点（`core/crates/node/runtime/src/CoreNodeRouter.rs:2384`）。
- `shouldUseLocalWatchSource` 在 `coreForceLocal` 时返回 false（`core/crates/node/runtime/src/CoreNodeRouter.rs:2417`）。
- shouldUseLocalWatchSource 在绑定目标 `targetNodeId` 为本节点时返回 true（`core/crates/node/runtime/src/CoreNodeRouter.rs:2438`）。
- shouldUseLocalWatchSource 在绑定目标 `targetNodeId` 不可达时返回 true（`core/crates/node/runtime/src/CoreNodeRouter.rs:2438`）。
- 成员可达当且仅当目标为本节点或路由计划 `plan` 存在（`core/crates/node/runtime/src/CoreNodeRouter.rs:1721`）。
- 只在路由计划多于一跳时填写 `relayHops` 与 `relayPath`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1722`）。
- `canExecute` 要求 `coreVersion` 存在且具备 `runtime.execute` 能力（`core/crates/node/runtime/src/CoreNodeRouter.rs:1734`）。
- `nodeIsReachable` 对本节点恒返回 true，其余节点走经活动对端的路由计划判断（`core/crates/node/runtime/src/CoreNodeRouter.rs:626`）。
- `nodeRoutePlan` 对本节点返回 None，策略断开、Space 外或不可达时也返回 None（`core/crates/node/runtime/src/CoreNodeRouter.rs:641`）。
- 应用目标走 `callApplication`，其余本地调用在 `withCoreForceLocal` 下执行（`core/crates/node/runtime/src/CoreNodeRouter.rs:1298`）。
- 共享客户端的 call 在目标为远端节点时要求 `requireCallPermission`（`core/crates/node/runtime/src/CoreNodeRouter.rs:2181`）。
- Binding 目标的 `watch` 经 `watchBindingFlow` 打开绑定流（`core/crates/node/runtime/src/CoreNodeRouter.rs:2305`）。
- 目标为本节点时返回 `localStream`（`core/crates/node/runtime/src/CoreNodeRouter.rs:2482`）。
- `coreNodeIsReachableThroughPeers` 经活动对端计算节点可达性（`core/crates/node/runtime/src/CoreNodeRouter.rs:1750`）。
- `coreNodeRoutePlanThroughPeers` 经活动对端计算节点路由计划（`core/crates/node/runtime/src/CoreNodeRouter.rs:1772`）。
- `CoreNodeRouter` 只在 feature `full` 下编译（`core/crates/node/runtime/src/lib.rs:83`）。
- `NodeSpaceService` 只在 feature `peer-runtime` 下编译（`core/crates/node/runtime/src/lib.rs:90`）。
- `SpacePersistenceSyncService` 只在 feature `full` 下编译（`core/crates/node/runtime/src/lib.rs:103`）。
- `SpaceRuntime` 只在 feature `full` 下编译（`core/crates/node/runtime/src/lib.rs:110`）。

### 绑定与权限

- `effectiveBinding` 在属主不可达时把返回记录的 `nodeId` 改为本节点，且不改持久化属主（`core/crates/node/runtime/src/CoreNodeRouter.rs:454`）。
- 绑定路由状态的 `activeNodeId` 在属主可达时为属主，否则为本节点，同时返回 `activeIsLocal` 与 `ownerNodeId`（`core/crates/node/runtime/src/CoreNodeRouter.rs:470`）。
- 绑定路由状态返回 `ownerPlatform`、`ownerIsLocal`、`ownerReachable` 与 `generation`（`core/crates/node/runtime/src/CoreNodeRouter.rs:472`）。
- `bindingStillCurrent` 要求 `nodeId` 相同且 `generation` 相同（`core/crates/node/runtime/src/CoreNodeRouter.rs:1686`）。
- `prepareCreationBinding` 在 `createBindingCapability` 为空时不做绑定工作直接返回（`core/crates/node/runtime/src/CoreNodeRouter.rs:940`）。
- 已有绑定目标仍可用时用 `compareAndSet` 保持该绑定（`core/crates/node/runtime/src/CoreNodeRouter.rs:949`）。
- 已有绑定目标不能承载 Core 执行时返回 `ROUTE_UNAVAILABLE`（`core/crates/node/runtime/src/CoreNodeRouter.rs:947`）。
- 选新绑定属主时按成员 `sort_by_key` 排序，本节点优先（`core/crates/node/runtime/src/CoreNodeRouter.rs:952`）。
- 无可达且有执行能力的成员时返回 `ROUTE_UNAVAILABLE`（`core/crates/node/runtime/src/CoreNodeRouter.rs:961`）。
- 提交属主非本节点时经 `SyncApplyImmediateBindingOperation` 发往该节点安装绑定（`core/crates/node/runtime/src/CoreNodeRouter.rs:967`）。
- `requireRoutePermission` 在 `permissionCapability` 为空时直接放行（`core/crates/node/runtime/src/CoreNodeRouter.rs:522`）。
- 否则按 Caller 或 Target 主体校验 `nodeHasCapability`（`core/crates/node/runtime/src/CoreNodeRouter.rs:530`）。
- 路由权限拒绝时返回 `ROUTE_PERMISSION_DENIED`（`core/crates/node/runtime/src/CoreNodeRouter.rs:544`）。
- `requireCallPermission` 经 `generated_space_call_route` 解析路由，未知路由返回 `SPACE_ROUTE_NOT_FOUND`（`core/crates/node/runtime/src/CoreNodeRouter.rs:580`）。
- `requireWatchPermission` 对 `CORE_STREAM_TARGET` 走 `embeddedStreamSourceRoute`，其余走 `generated_space_watch_route`（`core/crates/node/runtime/src/CoreNodeRouter.rs:593`）。
- `requirePushPermission` 在没有生成的推送路由时直接放行，不做权限校验（`core/crates/node/runtime/src/CoreNodeRouter.rs:606`）。
- `bindingRouteStatusFlow` 订阅同步变更与对端变化，推送绑定路由状态更新（`core/crates/node/runtime/src/CoreNodeRouter.rs:481`）。
- `GeneratedSpaceRoute` 含 `routeId`、`methodName`、`bindingArgument` 与 `targetType` 四个字段（`core/crates/node/runtime/src/lib.rs:30`）。
- 路由元数据含 `permissionScope`、`permissionCapability`、`lifecycle` 与 `createBindingCapability` 四个字段（`core/crates/node/runtime/src/lib.rs:37`）。
- GeneratedSpaceRoute 的 `bindingKey` 从参数 map 中取绑定键（`core/crates/node/runtime/src/lib.rs:44`）。
- 该方法从参数 map 中取 `bindingArgument` 对应的值（`core/crates/node/runtime/src/lib.rs:53`）。
- 绑定键不是字符串时返回 `CORE_BINDING_KEY_INVALID`（`core/crates/node/runtime/src/lib.rs:62`）。
- 绑定键为空串时返回 `CORE_BINDING_KEY_REQUIRED`（`core/crates/node/runtime/src/lib.rs:68`）。

### TTL 与中继

- `routeTtl` 等于 Space 成员数转 u32，溢出时返回 `SPACE_TOO_LARGE`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1869`）。
- 初始路由在目标为本节点时返回 `CORE_NODE_TARGET_LOCAL`，并要求目标为 Space 成员，ttl 取 `routeTtl`（`core/crates/node/runtime/src/CoreNodeRouter.rs:695`）。
- 转发时 ttl 为 0 返回 `CORE_NODE_ROUTE_TTL_EXHAUSTED`（`core/crates/node/runtime/src/CoreNodeRouter.rs:732`）。
- 转发时每转发一跳把 `ttl` 减 1（`core/crates/node/runtime/src/CoreNodeRouter.rs:742`）。
- 无可用下一跳时返回 `CORE_NODE_UNREACHABLE`（`core/crates/node/runtime/src/CoreNodeRouter.rs:777`）。
- 入站路由校验要求 `Previous`、`Origin` 与 `Target` 均为 Space 成员（`core/crates/node/runtime/src/CoreNodeRouter.rs:806`）。
- `requireRouteSpace` 在 spaceId 不匹配时返回 `SPACE_ID_MISMATCH`（`core/crates/node/runtime/src/CoreNodeRouter.rs:788`）。
- `requireDirectPeer` 在无当前配对时返回 `PEER_NOT_AUTHORIZED`，被策略断开时返回 `CORE_NODE_REVOKED`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1913`）。
- 对 `NODE_SPACE_TARGET` 的调用要求当前直接配对，方向不限（`core/crates/node/runtime/src/CoreNodeRouter.rs:823`）。
- 节点调用经 `peers.call` 直发，ttl 为 0 且 routeKind 为 Target，不中继（`core/crates/node/runtime/src/CoreNodeRouter.rs:836`）。
- `callNodeSpace` 使用 SpaceRoute 路由类型（`core/crates/node/runtime/src/CoreNodeRouter.rs:852`）。
- 路由调用入口先校验 `requireRoutableTarget`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1932`）。
- 节点 Space 调用要求目标为本节点、origin 等于 previous、ttl 为 0 且类型为 Target，否则返回 `PEER_DIRECT_CALL_REQUIRED`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1943`）。
- 控制交换要求显式同 Space 的 Target 路由，否则返回 `CONTROL_ROUTE_INVALID`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1990`）。
- 审批要求显式同 Space 的路由，否则返回 `APPROVAL_ROUTE_INVALID`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1999`）。
- `routedWatchSnapshot` 是路由 watch 快照的入口（`core/crates/node/runtime/src/CoreNodeRouter.rs:2030`）。
- `routedWatch` 是路由 watch 流的入口（`core/crates/node/runtime/src/CoreNodeRouter.rs:2060`）。
- `routedOpenPush` 是路由推送会话的入口（`core/crates/node/runtime/src/CoreNodeRouter.rs:2111`）。

### SpaceRuntime 的本地执行

- Space 调用在路由未注册时返回 `SPACE_ROUTE_NOT_FOUND`（`core/crates/node/runtime/src/SpaceRuntime.rs:57`）。
- `callToolPkgRoute`、`watchToolPkgRoute` 与 `pushToolPkgRoute` 经 `ToolPkgRouteRuntime` 分发（`core/crates/node/runtime/src/SpaceRuntime.rs:65`）。
- 其余路由在 MAIN 槽位调用 `generated_space_call_on_chat_core`（`core/crates/node/runtime/src/SpaceRuntime.rs:74`）。
- Space watch 快照在路由未注册时返回 `SPACE_ROUTE_NOT_FOUND`（`core/crates/node/runtime/src/SpaceRuntime.rs:92`）。
- 对 `CORE_STREAM_TARGET` 的 watch 走 `openEmbeddedStream`（`core/crates/node/runtime/src/SpaceRuntime.rs:121`）。
- `openEmbeddedStream` 要求 `propertyName` 为 `openCoreStream`，否则返回 `watchNotFound`（`core/crates/node/runtime/src/SpaceRuntime.rs:158`）。
- SpaceStreamPool 的 `adopt` 只在 `streamId` 不存在时插入，不覆盖已有流（`core/crates/node/runtime/src/SpaceRuntime.rs:30`）。
- SpaceRuntime 的 `new` 接收 `ChatRuntimeHolder`（`core/crates/node/runtime/src/SpaceRuntime.rs:43`）。
- 推送路由解析后，非 `pushToolPkgRoute` 走 `generated_space_push_on_chat_core`，`pushToolPkgRoute` 先验 `requireSpacePackage`（`core/crates/node/runtime/src/SpaceRuntime.rs:216`）。
- `CoreLinkSharedClient` 的 `call` 委托给 SpaceRuntime 的 `call`（`core/crates/node/runtime/src/SpaceRuntime.rs:197`）。
- `executeLocalCall` 对 `DEVICE_TOOL_TARGET` 返回 `DEVICE_TOOL_MODE_INVALID`，设备工具要求可取消的 watch（`core/crates/node/runtime/src/CoreNodeRouter.rs:1284`）。
- 对 `NODE_SPACE_APPROVAL_TARGET` 的调用走 `RuntimeRemoteLinkService` 的 `acceptSpaceApprovalCall`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1290`）。
- 响应 `requestId` 与请求不一致时返回 `CORE_REQUEST_ID_MISMATCH`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1302`）。
- `watchBindingFlow` 为逻辑 watch 派生一个泵任务（`core/crates/node/runtime/src/CoreNodeRouter.rs:1375`）。
- 绑定流泵每段开始重新解析 `effectiveBinding`，路由或对端变化时重开底层流（`core/crates/node/runtime/src/CoreNodeRouter.rs:1433`）。
- 首个 `Snapshot` 已转发后把后续 `Snapshot` 转为 `Changed`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1610`）。
- 首个 Snapshot 到达时标记 `initialSnapshotForwarded`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1637`）。
- 内嵌流源路由按模式 call 走 `generated_space_call_route`，按模式 watch 走 `generated_space_watch_route`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1797`）。
- 内嵌流源路由在路由未知时返回 `SPACE_ROUTE_NOT_FOUND`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1812`）。
- `openPush` 在打开时固定推送路由，并在 `pushId` 下注册推送会话（`core/crates/node/runtime/src/CoreNodeRouter.rs:371`）。
- 推送项校验 `pushId` 与 `sequence`，不匹配分别返回 `PUSH_ID_MISMATCH` 与 `PUSH_SEQUENCE_MISMATCH`（`core/crates/node/runtime/src/CoreNodeRouter.rs:398`）。
- `closePush` 关闭推送会话，已关闭的会话返回 `PUSH_CLOSED`（`core/crates/node/runtime/src/CoreNodeRouter.rs:421`）。
- `installNodeServices` 只装配一次节点服务，第二次调用返回 Node services are already installed（`core/crates/node/runtime/src/CoreNodeRouter.rs:279`）。
- `nodeServices` 在未装配时返回 Node services are not installed（`core/crates/node/runtime/src/CoreNodeRouter.rs:285`）。
- `maxPeerMessageBytes` 在对端服务未装配时回落到 `DEFAULT_MAX_PEER_MESSAGE_BYTES`（`core/crates/node/runtime/src/CoreNodeRouter.rs:292`）。
- `localNodeId` 返回路由器的稳定节点身份（`core/crates/node/runtime/src/CoreNodeRouter.rs:344`）。

### 持久化同步：SpacePersistenceSyncService

- `SYNC_DOMAINS` 含 preferences、chat、binding、runtime_file、network_control 与 plugin_storage 六个同步域（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:28`）。
- `SYNC_BLOB_CHUNK_BYTES` 为 64 KiB（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:33`）。
- `MAX_SYNC_PAGES_PER_PASS` 为 64 页（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:42`）。
- `PEER_FULL_SYNC_BACKOFF_BASE_MS` 为 2000 毫秒（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:44`）。
- `PEER_FULL_SYNC_BACKOFF_MAX_MS` 为 60000 毫秒（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:46`）。
- `WORKSPACE_SCAN_ACTIVE_INTERVAL_MS` 为 2000 毫秒（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:48`）。
- `WORKSPACE_SCAN_IDLE_INTERVAL_MS` 上限为 60000 毫秒（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:54`）。
- `peerFullSyncBackoffMs` 按失败次数翻倍退避，上限 60000 毫秒（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:106`）。
- 同步服务按 nodeId 在 `persistenceServices` 弱引用表中取单例（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:165`）。
- `start` 初始化 Space 存储、订阅同步变更并启动工作区扫描器与对端变化 watcher（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:199`）。
- 启动时经 `subscribeSyncMutations` 订阅同步变更（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:216`）。
- 启动时同时启动工作区扫描器 `startWorkspaceScanner` 与对端变化 watcher `startPeerChangeWatcher`（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:236`）。
- 启动末尾排队一次 `service_start` 同步（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:252`）。
- `stop` 停止工作区扫描器与对端变化 watcher，并丢弃变更订阅（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:267`）。
- 工作区扫描间隔 `intervalMs` 在有变更的轮次回到 2000 毫秒活动间隔，无变更的轮次逐轮翻倍直至 60000 毫秒空闲上限（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:311`）。
- `startPeerChangeWatcher` 只消费运行时连接变化，不订阅发现也不读写配对记录（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:331`）。
- `synchronizeOnce` 先检查被移除设备，再扫描工作区文件、发布本地拓扑并投递离场收据（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:362`）。
- 一轮同步发布本地拓扑时调用 `publishLocalTopology`（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:389`）。
- 一轮同步投递离场收据时调用 `space_departure::synchronize`（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:415`）。
- 一轮同步把各阶段错误 `errors` 用 " | " 连接后返回（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:478`）。
- `limit` 为 0 时报错（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:501`）。
- 执行互斥锁 `execution` 把同一对端的同步串行化（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:505`）。
- 目标不可达时返回 `CORE_NODE_UNREACHABLE`（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:570`）。
- 本节点 nodeId 大于目标时由本节点向对方请求 `SyncRequest` 状态（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:575`）。
- 权威更新送到非存储成员，包括 `grants` 与 `revocations`，且不推进业务复制时钟（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:604`）。
- 设备偏好 `preferences` 提供给每一个已准入成员，偏好时钟与载荷与业务副本时钟分离（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:630`）。
- 双端不均为存储提供方时，`storageReplicationAllowed` 不通过，返回 Ok(false)，不做业务复制（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:657`）。
- `storageReplicationAllowed` 在 `requirePeerStorageProviders` 通过时为 true，在 `SPACE_STORAGE_PERMISSION_DENIED` 时为 false，其余错误向上传播（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:674`）。
- `localStateSummary` 先发布偏好出箱，再发布 `synchronizationSummary` 摘要（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:688`）。
- `peerPassRequired` 决定一轮同步是否必需（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:694`）。
- 退避未过时返回 false，pendingWork 或连续失败时返回 true（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:719`）。
- 只有退避已过、无 pendingWork、无连续失败且 storageReplicationAllowed 为 true 时，才用 `probeRemoteClockSummary` 探针比对摘要决定是否需要一轮同步（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:734`）。
- 非存储成员走 `authority_only` 分支直接返回 true，不探针（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:727`）。
- `probeRemoteClockSummary` 经 `SyncClockDigest` 取对端时钟摘要，缺失时报错（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:778`）。
- `recordPeerPassCompleted` 重置失败计数，非业务复制的轮次清掉两端摘要（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:789`）。
- `synchronizeRequestedPeer` 在本节点 nodeId 大于等于目标时报错，称同步请求指向了错误的协调方（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:800`）。
- `recordPeerPassFailed` 记录一轮同步失败（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:815`）。
- `recordPeerFailure` 只对网络故障进指数退避，确定性失败记 failedState 且不退避（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:828`）。
- `recordPendingWork` 记录一轮内待处理的阶段与报告（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:849`）。
- `synchronizeDomains` 双向对账时钟并复制操作（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:878`）。
- 对账时经 `SyncClock` 与对端交换时钟（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:900`）。
- 时钟对账后做一致性校验 `requireConsistencySupport`（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:909`）。
- 一轮超过 `MAX_SYNC_PAGES_PER_PASS` 页时停止取页并记录剩余页数（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1004`）。
- 按 `syncPageChunks` 把操作拆页以适配对端消息上限（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1063`）。
- `exchangePairedDeviceSpaceProjection` 先协商 `projectionProtocol`，再取对端快照并观察其 Space 投影（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1093`）。
- 返回本地与对端 `spaceId` 是否一致（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1150`）。
- `validateReachableDeviceSpace` 经 DeviceSpace 调用核对双方成员表与 spaceId（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1155`）。
- `synchronizeRequiredBlobs` 同步缺失的 blob 引用（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1194`）。
- `synchronizeBlobReferences` 同步 blob 引用列表（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1212`）。
- `transferBlob` 按 64 KiB 分块传输 blob，完后校验持久化（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1250`）。
- `scheduleSynchronization` 合并触发原因后经 Host 调度器排队一轮异步同步任务（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1297`）。
- `callLocal` 经 application 目标调用本地应用方法（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1389`）。
- `serviceCallRequest` 对 `NODE_SPACE_TARGET` 与 `NODE_SPACE_CONTROL_TARGET` 直通，其余目标经 `targetForSchema` 解析（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1566`）。
- `syncOperationCeiling` 为对端消息上限减 4 KiB 信封余量（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1621`）。
- `syncPageBudget` 为对端消息上限的四分之三再减 64 KiB 余量（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1628`）。
- 单个操作超过上限时返回 `SYNC_OPERATION_TOO_LARGE`（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1657`）。
- `validateDomainClock` 要求时钟 `protocolVersion` 为 1（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1464`）。
- `clockStateSummary` 要求时钟含 `stateSummary` 字段，否则报错（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1477`）。
- `PeerSyncGate` 持有 `execution`、`lastRemoteClockSummary`、`lastLocalStateSummary` 与 `consecutiveFailures`（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:82`）。
- 还持有 `nextFullSyncAllowedAt`、`pendingWork` 与 `failedState`（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:89`）。

### 对端同步方法：PeerSync

- `NODE_SYNC_TARGET` 是 `$node.sync`（`core/crates/node/runtime/src/PeerSync.rs:5`）。
- `PeerSyncMethod` 定义 16 种对端同步方法（`core/crates/node/runtime/src/PeerSync.rs:14`）。
- `requiresStorageProvider` 要求 12 种方法具备存储提供方（`core/crates/node/runtime/src/PeerSync.rs:37`）。
- `CoreVersion`、`Protocol` 与 `DeviceSpace` 不要求存储提供方（`core/crates/node/runtime/src/PeerSync.rs:15`）。
- `SyncApplyImmediateBindingOperation` 不要求存储提供方（`core/crates/node/runtime/src/PeerSync.rs:30`）。
- 未知方法返回 `PEER_SYNC_METHOD_DENIED`（`core/crates/node/runtime/src/PeerSync.rs:60`）。
- `SyncApplyOperations` 要求携带 operations 数组（`core/crates/node/runtime/src/PeerSync.rs:64`）。
- 快照读取与修复校验类型化信封，否则返回 `PEER_SYNC_INVALID_SNAPSHOT`（`core/crates/node/runtime/src/PeerSync.rs:75`）。
- `PeerSyncPushMethod` 只允许 `SyncReceiveBlob` 一种推送方法（`core/crates/node/runtime/src/PeerSync.rs:102`）。
- `SyncRequest` 含 limit 与 force 两个字段，且拒绝未知字段（`core/crates/node/runtime/src/PeerSync.rs:9`）。
- `SyncProgress` 在本地经 `peerProgress` 应答（`core/crates/node/runtime/src/CoreNodeRouter.rs:1963`）。
- `SyncRequest` 经 `synchronizeRequestedPeer` 处理（`core/crates/node/runtime/src/CoreNodeRouter.rs:1969`）。
- 对 SpaceBinding 的路由调用走 `callSpaceWithOrigin`（`core/crates/node/runtime/src/CoreNodeRouter.rs:2007`）。
- 对 SpaceRoute 的路由调用先验权再走 `localCore.callSpace`（`core/crates/node/runtime/src/CoreNodeRouter.rs:2011`）。
- 其他路由类型的调用走 `executeLocalCall`，未到达目标时转发（`core/crates/node/runtime/src/CoreNodeRouter.rs:2018`）。
- 共享客户端的 `call` 解析生成的 Core 调用路由与目标节点（`core/crates/node/runtime/src/CoreNodeRouter.rs:2153`）。

### 节点身份、配对与会话准入：NodeSpaceService

- `NODE_SPACE_TARGET` 是 `node.space`（`core/crates/node/runtime/src/NodeSpaceService.rs:15`）。
- `NODE_SPACE_APPROVAL_TARGET` 是 `node.space.approval`（`core/crates/node/runtime/src/NodeSpaceService.rs:17`）。
- `NODE_SPACE_CONTROL_TARGET` 是 `node.space.control`（`core/crates/node/runtime/src/NodeSpaceService.rs:19`）。
- `spaceCallError` 把协议错误包成短消息，不带宿主回溯（`core/crates/node/runtime/src/NodeSpaceService.rs:24`）。
- `PeerSpaceSnapshot` 含 space、deviceProfiles、controlOperations、topology 与 departures（`core/crates/node/runtime/src/NodeSpaceService.rs:36`）。
- `NodeSpaceContext` 要求 storage、spaceStore、networkControlStore、peers 与 localNodeId，`isSpaceEndpoint` 默认返回 false（`core/crates/node/runtime/src/NodeSpaceService.rs:351`）。
- `NodeSpaceContext` 要求 `nodeIsReachable` 与 `callNode`，`afterJoined` 默认返回 Ok（`core/crates/node/runtime/src/NodeSpaceService.rs:352`）。
- NodeSpaceService 的 `new` 从 `CoreNodeIdentityStore` 取 localNodeId（`core/crates/node/runtime/src/NodeSpaceService.rs:516`）。
- NodeSpaceService 的 `initialize` 要求 profile.nodeId 等于本节点，否则报错，并把 protocolVersion 置为 `PeerProtocol::VERSION`（`core/crates/node/runtime/src/NodeSpaceService.rs:525`）。
- `requirePairedSpacePeer` 要求当前直接配对，方向不限，否则报错（`core/crates/node/runtime/src/NodeSpaceService.rs:548`）。
- `acceptPeerSpaceCall` 先要求当前直接配对，再分发到 `dispatchPeerSpaceCall`（`core/crates/node/runtime/src/NodeSpaceService.rs:556`）。
- `dispatchPeerSpaceCall` 按方法名分发对端 Space 调用（`core/crates/node/runtime/src/NodeSpaceService.rs:362`）。
- 分发 `projectionProtocol`、`snapshotHeader`、`snapshotControlPage` 与 `observeSpaceProjection`（`core/crates/node/runtime/src/NodeSpaceService.rs:369`）。
- 分发 `snapshot`、`deviceSpace` 与 `observeSpaceSnapshot`（`core/crates/node/runtime/src/NodeSpaceService.rs:375`）。
- 分发 `observePairedDeviceSpace`、`requestJoin`、`joinStatus`、`cancelJoin` 与 `reconcileSharedSpace`（`core/crates/node/runtime/src/NodeSpaceService.rs:383`）。
- 直接调用 join 返回 `SPACE_JOIN_APPROVAL_REQUIRED`，要求先提交入群申请等本地审批（`core/crates/node/runtime/src/NodeSpaceService.rs:385`）。
- `SpaceJoinStatus` 有 Pending、Approving、Approved、Rejected、Cancelled、Expired 与 Joined 七种状态（`core/crates/node/runtime/src/NodeSpaceService.rs:310`）。
- `SpaceJoinRequest` 含 requestId、targetDeviceId、applicantDeviceId、applicantName、spaceName、status、createdAt、expiresAt 与 canApprove（`core/crates/node/runtime/src/NodeSpaceService.rs:315`）。
- 入群申请含 `reviewerDeviceId`、`reviewerName`、`reviewerHops`、`assignmentVersion` 与 `decisionApprove`（`core/crates/node/runtime/src/NodeSpaceService.rs:325`）。
- 单成员且无入站申请 `hasInbound` 时直接返回空列表，不物化策略树（`core/crates/node/runtime/src/NodeSpaceService.rs:631`）。
- `decideDeviceSpaceJoin` 把审批决定包在轮询边界后的 future 里返回（`core/crates/node/runtime/src/NodeSpaceService.rs:638`）。
- `acceptSpaceApprovalCall` 委托给 `space_join::receiveApproval`（`core/crates/node/runtime/src/NodeSpaceService.rs:621`）。
- `leaveDeviceSpace` 退出 Space 但保留身份与配对（`core/crates/node/runtime/src/NodeSpaceService.rs:626`）。
- `requestDeviceSpaceJoin` 提交设备入群申请（`core/crates/node/runtime/src/NodeSpaceService.rs:627`）。
- `peerSpaceSnapshot` 返回当前 Space 的设备档案与拓扑（`core/crates/node/runtime/src/NodeSpaceService.rs:390`）。
- `peerSpaceSnapshotFor` 按当前 Space 成员过滤拓扑并校验设备档案（`core/crates/node/runtime/src/NodeSpaceService.rs:395`）。
- `peerSpaceSnapshotForPeer` 只给直接前邻居带上待处理的离场信息（`core/crates/node/runtime/src/NodeSpaceService.rs:413`）。
- `observePeerSpaceSnapshot` 校验对方档案与策略，未授权成员报错（`core/crates/node/runtime/src/NodeSpaceService.rs:421`）。
- 跨 Space 观察快照时做准入校验 `validateSpaceAdmission`（`core/crates/node/runtime/src/NodeSpaceService.rs:442`）。
- 同 Space 观察快照时做准入校验 `validateSpaceAdmission`（`core/crates/node/runtime/src/NodeSpaceService.rs:455`）。
- 观察快照时逐条应用引导控制操作 `applyBootstrapOperation`（`core/crates/node/runtime/src/NodeSpaceService.rs:490`）。
- `synchronizePreferences` 经 `NODE_SPACE_CONTROL_TARGET` 的 `exchangePreferences` 与活动对端交换设备偏好（`core/crates/node/runtime/src/NodeSpaceService.rs:650`）。
- 收到 `SPACE_ID_MISMATCH` 时取对方的离场收据（`core/crates/node/runtime/src/NodeSpaceService.rs:656`）。
- `spaceChannelScope` 委托给 `space_policy::spaceChannelScope`（`core/crates/node/runtime/src/NodeSpaceService.rs:670`）。
- 审批与控制目标带当前 `spaceId`，其余目标带空 `spaceId`，`ttl` 为 0 且 `routeKind` 为 `Target`（`core/crates/node/runtime/src/NodeSpaceService.rs:694`）。
- 经 `peers.call` 直发，不中继（`core/crates/node/runtime/src/NodeSpaceService.rs:693`）。
- `afterJoined` 经 `NODE_SPACE_CONTROL_TARGET` 发 `exchangeBounded` 交换当前控制操作，轻量端点不收业务副本也不推进复制时钟（`core/crates/node/runtime/src/NodeSpaceService.rs:700`）。
- `acceptSpaceControlCall` 处理 `exchangePreferences`（`core/crates/node/runtime/src/NodeSpaceService.rs:728`）。
- 同函数处理 `exchangeBounded`（`core/crates/node/runtime/src/NodeSpaceService.rs:736`）。
- 同函数处理 `exchange`（`core/crates/node/runtime/src/NodeSpaceService.rs:745`）。
- `exchangeBounded` 版本不符或消息上限过小时返回 `SPACE_PROTOCOL_INCOMPATIBLE`（`core/crates/node/runtime/src/NodeSpaceService.rs:735`）。
- 方法未知时返回 `Unknown Space control method`（`core/crates/node/runtime/src/NodeSpaceService.rs:745`）。
- `requireSpaceControlSource` 要求来源为 Space 成员、在 memberNodeIds 内且未被断开（`core/crates/node/runtime/src/NodeSpaceService.rs:752`）。
- `exchangeSpaceControl` 投影对方控制操作、退休被移除的本设备并应用移除成员的本地影响，返回当前控制操作（`core/crates/node/runtime/src/NodeSpaceService.rs:765`）。
- `spaceChannelScope` 委托给 `space_policy::spaceChannelScope`，传输授权只在双方成员资格均被当前 Space 控制日志准入后才可用，仅配对不足够（`core/crates/node/runtime/src/CoreNodeRouter.rs:618`）。

### 布局与未完成工作

- `runtime` 包含路由器、Space 运行时、发现、远程链接服务与同步（`core/crates/node/README.md:14`）。
- `route-macros` 提供注解生成的路由元数据（`core/crates/node/README.md:15`）。
- `edge-contract` 与 `edge` 提供紧凑的能力契约与设备运行时（`core/crates/node/README.md:16`）。
- `peer-link` 是轻量共享 PeerLink 引擎加 HTTP、WebSocket、TCP 与串口载体，依赖基础契约与 Host API，不依赖完整应用运行时或持久化存储（`core/crates/node/README.md:9`）。
- `proxy/edge` 是为固件体积限制保留的独立紧凑投影，不得再定义另一套对端身份或路由协议（`core/crates/node/README.md:18`）。
- `edge-transport` 仍含另一套配对权威与对端分发引擎，删除其剩余重复生命周期与会话模型是未完成工作（`core/crates/node/README.md:23`）。

## 关键符号

- `CoreNodeRouter` — 路由决策与跨节点调用的持有者（`core/crates/node/runtime/src/CoreNodeRouter.rs:65`）
- `CoreNodeLocalRuntime` — 本地执行上下文（`core/crates/node/runtime/src/CoreNodeRouter.rs:82`）
- CoreNodeRouter 的 `installNodeServices` — 只装配一次节点服务（`core/crates/node/runtime/src/CoreNodeRouter.rs:279`）
- CoreNodeRouter 的 `nodeServices` — 取已装配的节点服务，未装配报错（`core/crates/node/runtime/src/CoreNodeRouter.rs:285`）
- CoreNodeRouter 的 `localNodeId` — 返回路由器的稳定节点身份（`core/crates/node/runtime/src/CoreNodeRouter.rs:344`）
- CoreNodeRouter 的 `routeNodeId` — 解析 Local 或 Binding 的目标节点（`core/crates/node/runtime/src/CoreNodeRouter.rs:433`）
- CoreNodeRouter 的 `effectiveBinding` — 属主不可达时返回指向本节点的绑定副本（`core/crates/node/runtime/src/CoreNodeRouter.rs:454`）
- CoreNodeRouter 的 `bindingRouteStatus` — 返回绑定路由的属主与活动节点状态（`core/crates/node/runtime/src/CoreNodeRouter.rs:461`）
- CoreNodeRouter 的 `requireRoutePermission` — 按 Caller 或 Target 主体校验路由权限（`core/crates/node/runtime/src/CoreNodeRouter.rs:522`）
- CoreNodeRouter 的 `callSpaceWithOrigin` — 解析路由、取绑定键并决定本地或跨节点执行（`core/crates/node/runtime/src/CoreNodeRouter.rs:976`）
- CoreNodeRouter 的 `prepareCreationBinding` — 创建或保持执行绑定（`core/crates/node/runtime/src/CoreNodeRouter.rs:938`）
- CoreNodeRouter 的 `callNode` — 直发节点调用，`NODE_SPACE_TARGET` 不中继（`core/crates/node/runtime/src/CoreNodeRouter.rs:816`）
- CoreNodeRouter 的 `routedCall` — 处理到达本节点的路由调用（`core/crates/node/runtime/src/CoreNodeRouter.rs:1924`）
- CoreNodeRouter 的 `routedWatchSnapshot` — 路由 watch 快照的入口（`core/crates/node/runtime/src/CoreNodeRouter.rs:2030`）
- CoreNodeRouter 的 `routedWatch` — 路由 watch 流的入口（`core/crates/node/runtime/src/CoreNodeRouter.rs:2060`）
- CoreNodeRouter 的 `routedOpenPush` — 路由推送会话的入口（`core/crates/node/runtime/src/CoreNodeRouter.rs:2111`）
- CoreNodeRouter 的 `watchBindingFlow` — 为逻辑 watch 派生泵任务（`core/crates/node/runtime/src/CoreNodeRouter.rs:1375`）
- CoreNodeRouter 的 `pumpBindingFlow` — 每段重解析绑定并泵送事件流（`core/crates/node/runtime/src/CoreNodeRouter.rs:1413`）
- CoreNodeRouter 的 `shouldRoute` — 决定一次调用是否跨节点（`core/crates/node/runtime/src/CoreNodeRouter.rs:2352`）
- CoreNodeRouter 的 `shouldUseLocalWatchSource` — 决定一次 watch 是否用本地源（`core/crates/node/runtime/src/CoreNodeRouter.rs:2417`）
- CoreNodeRouter 的 `nodeIsReachable` — 判断节点可达性（`core/crates/node/runtime/src/CoreNodeRouter.rs:626`）
- CoreNodeRouter 的 `nodeRoutePlan` — 计算到目标节点的中继计划（`core/crates/node/runtime/src/CoreNodeRouter.rs:641`）
- CoreNodeRouter 的 `routeTtl` — ttl 等于 Space 成员数（`core/crates/node/runtime/src/CoreNodeRouter.rs:1869`）
- CoreNodeRouter 的 `requireDirectPeer` — 要求当前直接配对（`core/crates/node/runtime/src/CoreNodeRouter.rs:1913`）
- `GeneratedSpaceRoute` — 生成的 Space 路由元数据（`core/crates/node/runtime/src/lib.rs:30`）
- `GeneratedCoreRoute` — Local 与 Binding 两种路由目标（`core/crates/node/runtime/src/lib.rs:8`）
- `GeneratedRoutePermissionSubject` — Caller 与 Target 两种权限主体（`core/crates/node/runtime/src/lib.rs:15`）
- `GeneratedRouteLifecycle` — Normal、BeforeChangeRoute 与 AfterChangeRoute 三种生命周期（`core/crates/node/runtime/src/lib.rs:22`）
- GeneratedSpaceRoute 的 `bindingKey` — 从参数 map 取绑定键（`core/crates/node/runtime/src/lib.rs:44`）
- `SpaceRuntime` — Space 侧运行时对象注册表与内嵌流池（`core/crates/node/runtime/src/SpaceRuntime.rs:11`）
- SpaceRuntime 的 `call` — 本地执行 Space 调用（`core/crates/node/runtime/src/SpaceRuntime.rs:51`）
- SpaceRuntime 的 `watch` — 本地打开 Space 监听流（`core/crates/node/runtime/src/SpaceRuntime.rs:121`）
- SpaceRuntime 的 `openPush` — 本地打开 Space 推送会话（`core/crates/node/runtime/src/SpaceRuntime.rs:210`）
- SpaceStreamPool 的 `adopt` — 只在流不存在时登记内嵌流（`core/crates/node/runtime/src/SpaceRuntime.rs:30`）
- `PeerSyncMethod` — 16 种对端同步方法（`core/crates/node/runtime/src/PeerSync.rs:14`）
- PeerSyncMethod 的 `requiresStorageProvider` — 判断方法是否要求存储提供方（`core/crates/node/runtime/src/PeerSync.rs:37`）
- PeerSyncMethod 的 `fromRequest` — 解析同步请求并校验参数信封（`core/crates/node/runtime/src/PeerSync.rs:54`）
- `SpacePersistenceSyncService` — 可达成员间的持久化同步（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:152`）
- SpacePersistenceSyncService 的 `synchronizeOnce` — 执行一轮同步（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:362`）
- SpacePersistenceSyncService 的 `synchronizePeer` — 与一个对端同步（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:563`）
- SpacePersistenceSyncService 的 `synchronizeDomains` — 双向对账时钟并复制操作（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:878`）
- SpacePersistenceSyncService 的 `exchangePairedDeviceSpaceProjection` — 交换对端 Space 投影（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1093`）
- SpacePersistenceSyncService 的 `transferBlob` — 按 64 KiB 分块传输 blob（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1250`）
- SpacePersistenceSyncService 的 `scheduleSynchronization` — 合并触发原因后排队同步任务（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1297`）
- `NodeSpaceService` — 无应用执行运行时的设备的轻量组装（`core/crates/node/runtime/src/NodeSpaceService.rs:508`）
- NodeSpaceService 的 `initialize` — 校验本地身份并置协议版本（`core/crates/node/runtime/src/NodeSpaceService.rs:525`）
- NodeSpaceService 的 `dispatchPeerSpaceCall` — 分发对端 Space 调用（`core/crates/node/runtime/src/NodeSpaceService.rs:362`）
- NodeSpaceService 的 `observePeerSpaceSnapshot` — 观察并校验对端 Space 快照（`core/crates/node/runtime/src/NodeSpaceService.rs:421`）
- NodeSpaceService 的 `acceptSpaceControlCall` — 处理控制交换（`core/crates/node/runtime/src/NodeSpaceService.rs:723`）
- `NodeSpaceContext` — NodeSpaceService 的存储与对端访问契约（`core/crates/node/runtime/src/NodeSpaceService.rs:351`）
- `SpaceJoinRequest` — 设备入群申请（`core/crates/node/runtime/src/NodeSpaceService.rs:315`）
- `SpaceJoinStatus` — 七种入群状态（`core/crates/node/runtime/src/NodeSpaceService.rs:310`）

## 调用链

1. 调用方发起 Space 调用：`callSpaceWithOrigin` 经 `generated_space_call_route` 解析路由（`core/crates/node/runtime/src/CoreNodeRouter.rs:978`）。
2. 取绑定键：路由解析后从请求参数取 `bindingKey`（`core/crates/node/runtime/src/CoreNodeRouter.rs:994`）。
3. 创建绑定：路由流程在解析目标前先执行 `prepareCreationBinding`（`core/crates/node/runtime/src/CoreNodeRouter.rs:998`）。
4. 解析目标：`routeNodeId` 对 Local 返回本节点，对 Binding 返回 `bindingRouteNodeId`（`core/crates/node/runtime/src/CoreNodeRouter.rs:433`）。
5. 验权：`requireRoutePermission` 在 `permissionCapability` 为空时直接放行（`core/crates/node/runtime/src/CoreNodeRouter.rs:522`）。
6. 验权：否则按 Caller 或 Target 主体校验 `nodeHasCapability`（`core/crates/node/runtime/src/CoreNodeRouter.rs:530`）。
7. 本地执行：目标为本节点时走 `localCore.callSpace`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1015`）。
8. 跨节点执行：目标为远端时经 `callNodeWithKindAndOrigin` 以 SpaceRoute 类型发往目标节点（`core/crates/node/runtime/src/CoreNodeRouter.rs:1017`）。
9. 中继：ttl 为 0 时返回 `CORE_NODE_ROUTE_TTL_EXHAUSTED`（`core/crates/node/runtime/src/CoreNodeRouter.rs:732`）。
10. 中继：每转发一跳把 `ttl` 减 1（`core/crates/node/runtime/src/CoreNodeRouter.rs:742`）。
11. 到达目标：路由调用入口先校验 `requireRoutableTarget`（`core/crates/node/runtime/src/CoreNodeRouter.rs:1932`）。
12. 目标执行：对 SpaceBinding 的路由调用走 `callSpaceWithOrigin`，对 SpaceRoute 先验权再走 `localCore.callSpace`（`core/crates/node/runtime/src/CoreNodeRouter.rs:2011`）。
13. 目标执行：其他路由类型的调用走 `executeLocalCall`，未到达目标时转发（`core/crates/node/runtime/src/CoreNodeRouter.rs:2018`）。
14. 逻辑监听：Binding 目标的 `watch` 经 `watchBindingFlow` 打开绑定流（`core/crates/node/runtime/src/CoreNodeRouter.rs:2305`）。
15. 泵送：绑定流泵每段开始重新解析 `effectiveBinding`，路由或对端变化时重开底层流（`core/crates/node/runtime/src/CoreNodeRouter.rs:1433`）。
16. 同步启动：`start` 初始化 Space 存储、订阅同步变更并启动工作区扫描器与对端变化 watcher（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:199`）。
17. 同步一轮：`synchronizeOnce` 先检查被移除设备，再扫描工作区文件、发布本地拓扑并投递离场收据（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:362`）。
18. 对端同步：目标不可达时返回 `CORE_NODE_UNREACHABLE`（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:570`）。
19. 权威：权威更新送到非存储成员，包括 `grants` 与 `revocations`，且不推进业务复制时钟（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:604`）。
20. 偏好：设备偏好 `preferences` 提供给每一个已准入成员，偏好时钟与载荷与业务副本时钟分离（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:630`）。
21. 业务复制：双端不均为存储提供方时，`storageReplicationAllowed` 不通过，返回 Ok(false)，不做业务复制（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:657`）。
22. 域同步：`synchronizeDomains` 双向对账时钟并复制操作（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:878`）。
23. 入群审批：直接调用 join 返回 `SPACE_JOIN_APPROVAL_REQUIRED`，要求先提交入群申请等本地审批（`core/crates/node/runtime/src/NodeSpaceService.rs:385`）。
24. 准入：`observePeerSpaceSnapshot` 校验对方档案与策略，未授权成员报错（`core/crates/node/runtime/src/NodeSpaceService.rs:421`）。
25. 控制交换：`acceptSpaceControlCall` 按方法名分发三种控制方法（`core/crates/node/runtime/src/NodeSpaceService.rs:723`）。

## 来源

- `core/crates/node/README.md`
- `core/crates/node/runtime/src/lib.rs`
- `core/crates/node/runtime/src/CoreNodeRouter.rs`
- `core/crates/node/runtime/src/SpaceRuntime.rs`
- `core/crates/node/runtime/src/PeerSync.rs`
- `core/crates/node/runtime/src/SpacePersistenceSyncService.rs`
- `core/crates/node/runtime/src/NodeSpaceService.rs`
