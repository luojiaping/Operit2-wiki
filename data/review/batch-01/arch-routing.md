---
title: 路由与转发
module: arch
platforms: [all]
sources: [docs/core-node-space-binding-architecture.md, docs/device-net-routing-distribution.md, docs/link-access-architecture.md, core/crates/node/runtime/src/CoreNodeRouter.rs, core/crates/node/runtime/src/RuntimeRemoteLinkService.rs, core/crates/tool/services/src/runtime_support.rs, core/crates/runtime/application/src/services/ChatServiceCore.rs, core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs, core/crates/foundation/link/src/protocol.rs, core/crates/node/runtime/src/peer/dispatch.rs]
date: 2026-11-11
---

# 路由与转发

## 概述

一个设备空间（Space）里有多个地位对等的 CoreNode。（docs/core-node-space-binding-architecture.md:57）
路由回答两个问题：一个聊天的下一步由哪个 CoreNode 执行，以及一条 Link 调用怎样逐跳到达那个节点。
分工是三层：[[arch-binding|Binding]] 决定执行节点，RouteTable 与加权路由决定下一跳，转发层只给现有 Link 消息加一个 `RoutedLink` 外层。
Space 是节点成员、路由和持久化同步的范围，它不是执行容器，不拥有 Agent、聊天或运行时。（docs/core-node-space-binding-architecture.md:28）
Space 只负责三件事：确定哪些 CoreNode 属于同一个协作范围、确定哪些已配对连接可以承载 Space 流量、确定持久化数据应当在哪些 CoreNode 之间持续同步。（docs/core-node-space-binding-architecture.md:69）

本页讲调用路由与 Binding。网络选路与实时分发的细节见 [[sync-routing|设备间路由与实时分发]]。

## AI 速览

- `RoutedLink` — 转发外层的四字段概念图示，省略了来源和路由种类
- `RoutedCoreRequest` — 实际序列化类型，六字段：spaceId、originNodeId、targetNodeId、ttl、routeKind、payload
- `CoreNodeRouter` — 本地请求入口，选 Binding 目标并逐跳转发
- `RouteTable` — 运行时内部路由表，不是领域概念
- `LinkAdvertisement` — 有向链路公告，含往返时延、丢包、拥塞
- `RouteDecision` — 路由结果：目标节点、下一跳、总代价、拓扑代际
- `SharedWatchHub` — 共享 Watch 树的所有者
- `SharedWatchEntry` — 一条共享上游 Watch 及其下游订阅者
- `Binding` — 决定一个 chat 下一步在哪个 CoreNode 执行的不透明 key
- `requiredClock` — 架构文档定义的持久化同步屏障概念，实际运输的上下文没有该参数
- `CoreRouteResumeContext` — 交接时实际运输的运行上下文，含 runtimeChatHistory 等字段
- `effectiveBinding` — 本次请求的有效 Binding 解析，目标不可达时取本机且不改归属
- `resumeFromRouteContext` — 目标节点接收交接上下文并取得本地执行 lease 的入口
- `PeerRouter` — 认证会话到执行后端的共同边界
- `PeerLink` / `PeerConnection` — 认证连接承载；对外提供 connect/listen 与 send/receive/close
- `#[operit_core_route(...)]` — 真实 Core 方法上的路由声明
- `list_core_nodes` — 读取本机已同步 Space 成员视图的工具
- `switch_core` — 切换 Binding 目标节点的工具

主入口：本地 App 始终首先进入本机 `CoreNodeRouter`。

数据流向：App → `CoreNodeRouter` → 普通请求走 `LocalCoreProxy`，Binding 请求经 `Binding(key)` 到目标 CoreNode；跨节点时逐跳经 `RoutedLink` 转发，响应沿原调用链返回。

## 核心机制

### 谁决定执行节点：Binding

`Binding` 只表达一句话：这个 key 对应的下一次路由执行由哪个 CoreNode 完成。（docs/core-node-space-binding-architecture.md:481）
`Binding` 只决定 chat 的下一步执行节点，`Binding` 改变不移动数据。（docs/core-node-space-binding-architecture.md:481）
每个需要路由的业务 key 必须有一条 `Binding`；`Binding` 缺失或指向非 Space 成员时，请求返回明确错误。（docs/core-node-space-binding-architecture.md:172）

聊天路由使用现有 `chatId` 作为 key。（docs/core-node-space-binding-architecture.md:171）
切换工具只需要目标 `nodeId`：`switch_core(nodeId)` 切换目标。（docs/core-node-space-binding-architecture.md:156）
`list_core_nodes()` 返回本机已经同步的 Space 成员视图。（docs/core-node-space-binding-architecture.md:320）
`switch_core` 在调用时按同一份路由视图校验目标：目标不是 Space 成员或当前不可达时，工具直接返回失败，而不是让切换在回合结束后异步落空。（docs/core-node-space-binding-architecture.md:164）

按架构文档，`Binding` 比较写入成功后，它就是新的唯一执行位置。（docs/core-node-space-binding-architecture.md:410）
后续持久化同步屏障或 continuation 失败必须返回明确错误，不自动把 `Binding` 改回源节点。（docs/core-node-space-binding-architecture.md:410）

### 请求从哪里进入路由：CoreNodeRouter

本地 App 始终首先进入本机 `CoreNodeRouter`：普通请求走 `LocalCoreProxy`，标注 Binding 的请求经 `Binding(key)` 到目标 CoreNode，传输定向的 CoreNode 请求直达目标 CoreNode。（docs/core-node-space-binding-architecture.md:354）

只有模型执行、工具循环、取消当前执行和实时执行状态进入 Binding 路由。（docs/core-node-space-binding-architecture.md:363）
聊天历史读取、配置编辑和其他持久化数据操作在本地 Core 执行，由持续同步传播。（docs/core-node-space-binding-architecture.md:362）
整段会话删除属于本地持久化操作，不要求存在 `Binding`，也不要求执行节点在线。（docs/core-node-space-binding-architecture.md:365）

请求类型由真实 Core 方法上的 `#[operit_core_route(...)]` 声明，经 typed Core codegen 生成，不通过对象名、方法名或路径字符串猜测业务含义。（docs/core-node-space-binding-architecture.md:371）
请求显式携带 `Binding` key 时直接使用。（docs/core-node-space-binding-architecture.md:373）
未携带时，本机 `CoreNodeRouter` 调用注解声明的 resolver 读取当前 key，把 key 注入真实请求后再选择 `Binding` 目标。（docs/core-node-space-binding-architecture.md:373）
未标注的方法始终留在本地 Core。（docs/core-node-space-binding-architecture.md:373）

### 转发外层：RoutedLink

现有 `CoreCallRequest`、`CoreWatchRequest`、`CorePushRequest`、`CoreEvent` 和 `CorePushItem` 保持不变。（docs/core-node-space-binding-architecture.md:285）
架构文档用四字段图示说明经过 Peer Link 时增加的外层 `RoutedLink`，含 `spaceId`、`targetNodeId`、`ttl`、`payload`。（docs/core-node-space-binding-architecture.md:289）
四字段图示是概念示意，省略了来源和路由种类。（docs/core-node-space-binding-architecture.md:289）
实际序列化契约是六字段的 `RoutedCoreRequest<T>`，含 `spaceId`、`originNodeId`、`targetNodeId`、`ttl`、`routeKind`、`payload`。（core/crates/foundation/link/src/protocol.rs:984）
`peer/dispatch.rs` 的 `encodeRouted` 用完整的 `RoutedCoreRequest<T>` 编码请求。（core/crates/node/runtime/src/peer/dispatch.rs:20）
`payload` 是现有 Link 消息或 Space 控制消息，外层不携带 `chatId`、`Binding`、`envId`、文件路径或 Host 配置。（docs/core-node-space-binding-architecture.md:297）

请求路径是 `origin -> next peer -> ... -> target CoreNode`。（docs/core-node-space-binding-architecture.md:303）
响应沿正在等待的逐跳调用链返回。（docs/core-node-space-binding-architecture.md:307）
标准 Link 的 `requestId` 和 `pushId` 继续标识逻辑调用与流，不建立第二套流身份。（docs/core-node-space-binding-architecture.md:307）

`routeKind` 有三种：`Target` 使用目标节点的本地对象地址，`SpaceRoute` 使用注解生成的 Space 地址，`SpaceBinding` 由接入 Router 解析 `Binding` 后继续执行。（docs/link-access-architecture.md:140）
逐跳保留 `originNodeId`、最终 `targetNodeId` 和 `routeKind`，并处理 TTL、成员资格、撤销和中继权限。（docs/link-access-architecture.md:140）
路由元数据只在创建操作时提交；Watch Close 使用 `requestId`，Push Item/Close 使用 `pushId`，已打开的流保持所属会话和路由。（docs/link-access-architecture.md:137）

`target` 是稳定字符串地址。（docs/link-access-architecture.md:144）
本地 Proxy/SDK 使用 `core/<schema_key>`，Space route 使用 `space/<target_type>/<method>`；声明顺序不分配协议地址，改名是破坏性变更。（docs/link-access-architecture.md:144）

### 第一跳与路由失败

路由的第一跳必须是当前活跃且获准承载该 Space 流量的直接 Peer Link。（docs/core-node-space-binding-architecture.md:312）
心跳过期、连接关闭或策略断开时撤销对应连接与本机拓扑边。（docs/core-node-space-binding-architecture.md:313）
本机只发布自身连接事实，远端公告不能证明本机第一跳在线。（docs/core-node-space-binding-architecture.md:313）

`ttl` 每转发一次减一；无有效路径、TTL 用尽或目标不属于 Space 时属于路由失败。（docs/core-node-space-binding-architecture.md:321）
`RoutedCoreRequest.ttl` 是硬性循环上限，初始 TTL 是可用顶点数，每转发一跳减一。（docs/device-net-routing-distribution.md:107）
路由结果随设备投影与 `list_core_nodes` 暴露给上层，非本机直连的状态标记为 `Announced`，表示由其他成员宣告。（docs/core-node-space-binding-architecture.md:320）

转发期间先取得路由和连接句柄，释放互斥锁后再等待网络响应。（docs/core-node-space-binding-architecture.md:325）
路由和网络等待期间不持有全局 Core 互斥锁。（docs/core-node-space-binding-architecture.md:487）

### 加权路由：选代价最小的活跃路由

节点通过相邻 Peer Link 发布自己知道的 Space 成员和距离，每个节点据此维护内部 `RouteTable`。（docs/core-node-space-binding-architecture.md:126）
`RouteTable` 是运行时实现，不是领域概念。（docs/core-node-space-binding-architecture.md:127）
路由按有效边计算加权最短路径，等价路径使用确定的第一跳顺序。（docs/core-node-space-binding-architecture.md:316）

每条活跃有向 Peer Link 发布一条 `LinkAdvertisement`，含 `sourceNodeId`、`targetNodeId`、`channelEpoch`、`sequence`、`measuredAt`、`expiresAt`、`smoothedRttMs`、`lossPermille`、`congestionPermille`。（docs/device-net-routing-distribution.md:38）
`channelEpoch` 在 Peer Link 重建时变化，`sequence` 在该 epoch 内单调；接收方保留每条有向边的最新公告，并在 `expiresAt` 时丢弃。（docs/device-net-routing-distribution.md:46）

一条边可用当且仅当两端都是当前 Space 成员、公告未过期、本地源端是活跃直接 Peer Link、边有有效 channel epoch 与 sequence。（docs/device-net-routing-distribution.md:66）
路由器用 Dijkstra 算法计算有向最短路径树，图包含可用的公告。（docs/device-net-routing-distribution.md:78）
边代价是 `cost(u, v) = 1000 + 10 * smoothedRttMs + 25 * lossPermille + 10 * congestionPermille`。（docs/device-net-routing-distribution.md:83）
边代价的系数是配置常量，不是协议字段。（docs/device-net-routing-distribution.md:91）
等代价时选择字典序最小的第一跳，使独立路由器收敛到同一条路径。（docs/device-net-routing-distribution.md:102）
无可用路径的路由查找返回不可达错误，绝不凭成员关系或过期公告凭空造边。（docs/device-net-routing-distribution.md:102）

路由器为新的 call、Watch 打开或 Push 打开重新计算路由；已打开的 Watch 和 Push 在其生命周期内保留已有物理路径。（docs/device-net-routing-distribution.md:110）

承载层与 Operit 路由是两个独立的决策：EasyTier 等承载层选择两个可达虚拟地址之间的物理包路径，Operit 选择下一个已认证 Peer Link 并决定一个实时源在哪里复制。（docs/device-net-routing-distribution.md:10）
`device-net-routing-distribution.md` 不定义设备角色、执行位置、身份或承载层使用的 NAT 穿透算法。（docs/device-net-routing-distribution.md:7）

### Call、Watch、Push 的转发规则

Call：每一跳向 `nextPeer` 发起一个下游 call 并等待结果，目标节点解开 `RoutedLink` 后把原始 `CoreCallRequest` 交给自己的 `LocalCoreProxy`，响应沿原调用栈逐跳返回。（docs/core-node-space-binding-architecture.md:329）

Watch：每一跳在 `nextPeer` 上打开同一个逻辑订阅，并把下游 `CoreEvent` 按顺序写给上游；上游关闭、下游完成或 Peer Link 断开时，该跳释放对应订阅。（docs/core-node-space-binding-architecture.md:334）
`Binding` 不参与普通 watch 转发；持久化聊天界面优先观察本地同步数据，明确观察某个 CoreNode 实时状态的 watch 才发送到该节点。（docs/core-node-space-binding-architecture.md:337）

Push：每一跳固定打开时解析出的 `nextPeer`，并保持同一 `pushId` 内的 sequence 顺序；关闭上游 push 时，该跳关闭下游 push。路由中断返回流错误，不把同一个 push 静默改送另一节点。（docs/core-node-space-binding-architecture.md:342）

### 分发类与共享 Watch 树

Watch 路由在生成的 Core 路由元数据中声明一个分发类：`Unicast` 或 `SnapshotShared`。（docs/device-net-routing-distribution.md:117）
`Unicast` 用于执行事件、工具流、增量、仅追加日志，以及后来订阅者必须观察完整历史的任何序列，始终打开独立的上游流。（docs/device-net-routing-distribution.md:124）
`SnapshotShared` 用于具有完整当前快照与后续替换的状态投影；新接入的订阅者先收到最新缓存快照，再收到后续变更。（docs/device-net-routing-distribution.md:128）
生成的声明是该分类的唯一权威；传输不从对象 id、方法名、参数名或事件负载推断。（docs/device-net-routing-distribution.md:133）

每个路由器拥有一个 `SharedWatchHub`。（docs/device-net-routing-distribution.md:139）
`SnapshotShared` 条目以 `(spaceId, targetNodeId, routeKind, target, propertyName, canonicalArguments, topologyGeneration)` 为键。（docs/device-net-routing-distribution.md:139）
`SharedWatchEntry` 拥有恰好一个上游 Watch，包含 `latestSnapshot`、`upstreamSubscription`、`downstreamSubscribers`、`routeDecision`。（docs/device-net-routing-distribution.md:150）
第一个消费者沿加权路由打开上游 Watch；快照已存储后进入的消费者在其自己的逻辑订阅 id 上收到该快照；变更事件按源顺序复制给每个活跃消费者。（docs/device-net-routing-distribution.md:161）
完成事件关闭每个消费者并移除条目；最后一个消费者取消时关闭上游 Watch 并移除条目。（docs/device-net-routing-distribution.md:161）

每个下游订阅者有有界事件队列；达到上限时以 `PEER_WATCH_CONSUMER_SLOW` 关闭该逻辑订阅，不拖延源或其他消费者。（docs/device-net-routing-distribution.md:168）
队列占用计入链路拥塞测量，用于后续路由决策。（docs/device-net-routing-distribution.md:168）

### 工具边界切换 CoreNode

切换 CoreNode 直接携带当前运行上下文续接，不触发会话总结或上下文压缩，也不以压缩成功作为切换前提。（docs/core-node-space-binding-architecture.md:379）
切换必须发生在工具调用已经完成、工具结果已经持久化、下一轮模型请求尚未发起的边界上。（docs/core-node-space-binding-architecture.md:387）

实际交接按提交调用链进行：先同步目标节点，再比较写入 `Binding`，安装 Binding operation，最后调用 `AfterChangeRoute`。

先同步目标节点：`RuntimeRemoteLinkService` 在提交前调用 `synchronizeReachablePeerForReason` 同步目标节点。（core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1028）
比较写入 `Binding`：`bindingStore.compareAndSet` 比较写入，提交后校验新归属等于目标节点。（core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1044）
安装 Binding operation：`installRouteBindingOnTarget` 把 Binding operation 安装到目标节点。（core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1064）
调用 `AfterChangeRoute`：`callChatCoreLifecycle` 触发目标节点的 `AfterChangeRoute` 生命周期回调，传入交接上下文。（core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1083）
目标接收上下文：`resumeFromRouteContext` 接收 `CoreRouteResumeContext`。（core/crates/runtime/application/src/services/ChatServiceCore.rs:776）
取得本地执行 lease：目标节点打开聊天历史，并通过 `beginChatExecution` 取得本地执行 lease。（core/crates/runtime/application/src/services/ChatServiceCore.rs:805）
交给续接：`resumeFromRouteContext` 把执行 lease 和交接上下文交给 `sendRoutedContinuation` 续接。（core/crates/runtime/application/src/services/ChatServiceCore.rs:825）
续接使用上下文历史：目标节点续接时使用交接上下文中的 `runtimeChatHistory` 作为聊天历史发起下一轮。（core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:521）
续接前校验配置身份：目标节点续接前校验配置的 `extensionOwner` 与 `participantId` 与交接上下文快照身份一致，不一致时返回错误。（core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:496）

实际运输的上下文：`CoreRouteResumeContext` 包含 `runtimeChatHistory`、`workspacePath`、`promptFunctionType`、`participantId` 等字段，没有 `requiredClock` 或 execution generation 参数。（core/crates/tool/services/src/runtime_support.rs:22）

设计约束（架构文档定义，运行时实现尚未确认）：`requiredClock` 是持久化同步屏障，execution generation 来自 `Binding` 比较写入，不复用模型进程内部的 execution 或 round 身份。（docs/core-node-space-binding-architecture.md:407）
设计约束（架构文档定义，运行时实现尚未确认）：目标节点按 `(chatId, executionGeneration)` 识别 continuation，启动前读取 assistant 消息的 `completedExecutionGeneration`，已经完成相同或更高 generation 时直接返回，不重复调用模型或工具。（docs/core-node-space-binding-architecture.md:420）
设计约束（架构文档定义，运行时实现尚未确认）：每轮模型请求开始前，CoreNode 必须确认 `Binding(chatId)` 指向自己；`Binding` 更新使用当前值比较写入，只有当前执行节点能够提交 Agent 发起的切换。（docs/core-node-space-binding-architecture.md:416）
旧节点观察到 `Binding` 已改变后不得继续下一轮模型请求。（docs/core-node-space-binding-architecture.md:416）

响应流属于一次用户发起的 execution，不属于执行 CoreNode；最初接受请求的 `CoreNodeRouter` 保持上游流，当前执行节点只产生该 execution 的后续事件。（docs/core-node-space-binding-architecture.md:431）
发生切换时，当前执行节点把 handoff 结果返回给 origin router，origin router 根据新的 `Binding` 打开下一段 continuation，并把事件继续写入同一个上游 stream。（docs/core-node-space-binding-architecture.md:434）
多次切换不会形成 A -> B -> C 的永久转发链。（docs/core-node-space-binding-architecture.md:434）

当前行为：`Binding` 目标不可达时，`effectiveBinding` 只把本次请求所读记录副本的 `nodeId` 改为本机，不提交 CAS、不持久化新归属、不递增 generation，所有权仍在原目标节点。（core/crates/node/runtime/src/CoreNodeRouter.rs:451）
持久化归属 `ownerNodeId` 与本次有效执行节点 `activeNodeId` 是两个字段，目标不可达时 `activeNodeId` 为本机，`ownerNodeId` 仍为原目标。（core/crates/node/runtime/src/CoreNodeRouter.rs:469）
设计约束：目标不可达必须保持目标语义并明确报告错误，禁止静默改成本机执行。（docs/link-access-architecture.md:237）
架构文档另把“`Binding` 目标不可达时由发起设备原子接管，显式设备调用仍返回明确错误”列为必须保持的约束。（docs/core-node-space-binding-architecture.md:488）
当前行为与上述约束的偏差已列为待清理项，见“当前实现的待清理项”一节。（docs/link-access-architecture.md:247）

### 安全与审计

每一跳只接受已配对 Peer 的签名流量。（docs/core-node-space-binding-architecture.md:463）
收到 `RoutedLink` 后必须验证：当前节点属于 `spaceId`、上一跳属于 `spaceId`、`targetNodeId` 属于 `spaceId`、`payload` 类型允许在该 Peer Link 上转发。（docs/core-node-space-binding-architecture.md:463）

中间节点保留真实上一跳 session 作为审计来源；目标 CoreNode 获得 origin nodeId 和经过的相邻 session 审计记录，不能把所有多跳请求折叠成最后一个中继节点的控制者身份。（docs/core-node-space-binding-architecture.md:469）
设备身份、配对 secret 和 Host 授权保持节点本地。（docs/core-node-space-binding-architecture.md:472）
Space 成员资格不授予其他节点直接读取本机文件或终端的能力，只有在该 CoreNode 上执行的 Agent 工具通过本机 HostManager 访问这些能力。（docs/core-node-space-binding-architecture.md:472）

目标不可达必须保持目标语义并明确报告错误，禁止静默改成本机执行。（docs/link-access-architecture.md:237）
禁止未经明确要求增加失败后替换执行路径或重放请求的回退逻辑。（docs/link-access-architecture.md:238）

### 传输层：五种 transport 共用 Link 消息层

Link 的三个基础操作是 Call、Watch、Push。（docs/link-access-architecture.md:3）
五种 transport 是 HTTP、WebSocket、TCP、Serial、Bluetooth，共用 `FramedPeerConnection`；差别只在字节承载，不改变 Call、Watch、Push 的业务消息。（docs/link-access-architecture.md:153）
MessagePack 是产品 Link 的统一编码。（docs/link-access-architecture.md:161）
`PeerConnection` 对外提供 `send`、`receive`、`close`；`PeerLink` 提供 `connect`、`listen`。（docs/link-access-architecture.md:176）

Router 负责目标选择、Space 权限和转发；Peer runtime 负责身份、配对、会话、连接复用和响应关联；Transport 只负责连接、字节收发和 framing。（docs/link-access-architecture.md:37）
`PeerRouter` 是认证会话到执行后端的共同边界：完整 Core 使用 `CoreNodeRouter`，设备 Edge 使用 `EdgePeerRouter`，两者使用同一个 Peer runtime，不另建 Edge 配对流程。（docs/link-access-architecture.md:40）

`Binding` 和持久化同步使用 `$node.sync` 的标准 Call 或 Push，经 Router 校验并交给 `peer/sync_dispatch.rs`；同步要求相同 Space 的认证成员及相应 storage-provider 权限。（docs/link-access-architecture.md:209）
Space 回连准入由 `space_policy::spaceChannelScope` 集中判断。（docs/link-access-architecture.md:215）
`space_policy::RoutingPolicy` 从控制日志读取断开节点和中继权限。（docs/link-access-architecture.md:215）

监听能力由安装的 Host API 能力决定。（docs/link-access-architecture.md:165）
HTTP、WebSocket、TCP 使用同一个网络监听端口。（docs/link-access-architecture.md:167）

### 当前实现的待清理项

传输统一和路由行为合规是两个独立结论：当前五种 transport 已统一承载标准 Link 消息，共享客户端具备完整三个操作族；路由行为和 Host 边界仍有待清理项，见下表。（docs/link-access-architecture.md:4）
Transport 消息协议和共享 Link 客户端均已覆盖 Call、Watch、Push；Router 执行路径和 Host 边界仍需要上述代码层整改。（docs/link-access-architecture.md:251）

| 问题 | 源码位置 | 影响 |
| --- | --- | --- |
| 不可达 Binding 改成本机 | `CoreNodeRouter.rs::effectiveBinding` | 本次请求的有效执行节点被静默替换；不符合禁止回退的约束（docs/link-access-architecture.md:247） |
| 部分路由失败后更换下一跳重发 | `route_forwarding.rs::forwardOperation` | 普通 target 可重提交；设备工具和硬件 target 被排除，仍需按禁止回退要求整改（docs/link-access-architecture.md:248） |
| 串口地址规范化包含平台判断 | `peer-link/src/transport/serial.rs::endpointKey` | Windows 端口规范化仍位于 transport，Host 边界未完全收敛（docs/link-access-architecture.md:249） |

## 关键符号

- `RoutedLink` — 转发外层的四字段概念图示，省略了来源和路由种类（docs/core-node-space-binding-architecture.md:289）
- `RoutedCoreRequest<T>` — 实际序列化类型，六字段：spaceId、originNodeId、targetNodeId、ttl、routeKind、payload（core/crates/foundation/link/src/protocol.rs:984）
- `CoreNodeRouter` — 本地请求入口与逐跳转发器（docs/core-node-space-binding-architecture.md:354）
- `RouteTable` — 运行时内部路由表，不是领域概念（docs/core-node-space-binding-architecture.md:127）
- `LinkAdvertisement` — 有向链路公告，含往返时延、丢包、拥塞（docs/device-net-routing-distribution.md:38）
- `RouteDecision` — 路由结果：`destinationNodeId`、`nextHopNodeId`、`totalCost`、`topologyGeneration`（docs/device-net-routing-distribution.md:91）
- `SharedWatchHub` — 共享 Watch 树的所有者（docs/device-net-routing-distribution.md:139）
- `SharedWatchEntry` — 一条共享上游 Watch 及其下游订阅者（docs/device-net-routing-distribution.md:150）
- `Binding` — 决定一个 chat 下一步在哪个 CoreNode 执行的不透明 key（docs/core-node-space-binding-architecture.md:481）
- `requiredClock` — 架构文档定义的持久化同步屏障概念，实际运输的上下文没有该参数（docs/core-node-space-binding-architecture.md:407）
- `CoreRouteResumeContext` — 交接时实际运输的运行上下文，含 runtimeChatHistory 等字段（core/crates/tool/services/src/runtime_support.rs:22）
- `effectiveBinding` — 本次请求的有效 Binding 解析，目标不可达时取本机且不改归属（core/crates/node/runtime/src/CoreNodeRouter.rs:451）
- `resumeFromRouteContext` — 目标节点接收交接上下文并取得本地执行 lease（core/crates/runtime/application/src/services/ChatServiceCore.rs:776）
- `PeerRouter` — 认证会话到执行后端的共同边界（docs/link-access-architecture.md:40）
- `PeerLink` / `PeerConnection` — 认证连接承载（docs/link-access-architecture.md:176）
- `#[operit_core_route(...)]` — 真实 Core 方法上的路由声明（docs/core-node-space-binding-architecture.md:371）
- `list_core_nodes` — 读取本机已同步 Space 成员视图的工具（docs/core-node-space-binding-architecture.md:320）
- `switch_core` — 切换 Binding 目标节点的工具（docs/core-node-space-binding-architecture.md:387）
- `operit-store` — 操作日志、收据、Binding 与各存储 owner 的提交；拓扑记录与确定性路由计算（docs/core-node-space-binding-architecture.md:442）
- `node/runtime` — 配对与成员策略、CoreNodeRouter、逐跳转发、共享 Watch 与同步调度（docs/core-node-space-binding-architecture.md:445）
- `space_policy::spaceChannelScope` — Space 回连准入的集中判断入口（docs/link-access-architecture.md:215）
- `space_policy::RoutingPolicy` — 从控制日志读取断开节点和中继权限（docs/link-access-architecture.md:215）
- `PEER_WATCH_CONSUMER_SLOW` — 下游订阅者事件队列达到上限时关闭该逻辑订阅的错误（docs/device-net-routing-distribution.md:168）

## 调用链

### 一次 Binding 路由的 Call

1. 本地 App 把请求交给本机 `CoreNodeRouter`。（docs/core-node-space-binding-architecture.md:354）
2. `CoreNodeRouter` 按 `#[operit_core_route(...)]` 声明判断请求类型：普通请求走 `LocalCoreProxy`；标注 Binding 的请求读取 `Binding(key)` 得到目标 CoreNode。（docs/core-node-space-binding-architecture.md:371）
3. `CoreNodeRouter` 用加权路由（Dijkstra + `LinkAdvertisement`）选出第一跳 `nextPeer`。（docs/device-net-routing-distribution.md:78）
4. `CoreNodeRouter` 把请求包进 `RoutedLink` 外层发往第一跳。（docs/core-node-space-binding-architecture.md:289）
5. 每一跳验证 `spaceId` 成员资格与 `payload` 类型。（docs/core-node-space-binding-architecture.md:463）
6. 每一跳向下一跳发起下游 call 并等待结果。（docs/core-node-space-binding-architecture.md:329）
7. 目标节点解开 `RoutedLink`，把原始 `CoreCallRequest` 交给自己的 `LocalCoreProxy` 执行。（docs/core-node-space-binding-architecture.md:329）
8. 响应沿正在等待的逐跳调用链返回，`requestId` 全程标识这次逻辑调用。（docs/core-node-space-binding-architecture.md:307）

### 一次工具边界切换（switch_core）

1. node-A 的模型产生 `switch_core(node-D)`。（docs/core-node-space-binding-architecture.md:395）
2. node-A 验证 node-D 是可达的 Space 成员。（docs/core-node-space-binding-architecture.md:396）
3. node-A 在一个事务内持久化 assistant 工具调用、工具结果、chat metadata 和同步操作。（docs/core-node-space-binding-architecture.md:397）
4. 响应业务向 Router 返回只包含目标和不透明 payload 的 route transition。（docs/core-node-space-binding-architecture.md:398）
5. Router 先同步目标节点，为提交做准备。（core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1028）
6. Router 比较写入 `Binding(chat-1) = node-D`，提交成功后得到新的 generation 和 operation。（core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1044）
7. Router 把 Binding operation 安装到 node-D。（core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1064）
8. Router 调用 `AfterChangeRoute`，把交接上下文交给 node-D。（core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1083）
9. node-D 的 `resumeFromRouteContext` 接收 `CoreRouteResumeContext`。（core/crates/runtime/application/src/services/ChatServiceCore.rs:776）
10. node-D 打开聊天历史，并通过 `beginChatExecution` 取得本地执行 lease。（core/crates/runtime/application/src/services/ChatServiceCore.rs:805）
11. node-D 把执行 lease 和交接上下文交给 `sendRoutedContinuation` 续接。（core/crates/runtime/application/src/services/ChatServiceCore.rs:825）
12. `sendRoutedContinuation` 用交接上下文中的 `runtimeChatHistory` 作为聊天历史发起下一轮模型请求。（core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:521）
13. node-D 的输出事件继续写入原来的逻辑响应流。（docs/core-node-space-binding-architecture.md:404）

### 一次共享 Watch 的打开

1. 路由器按生成的 Core 路由元数据确认该 Watch 属于 `SnapshotShared` 类。（docs/device-net-routing-distribution.md:118）
2. 第一个消费者沿加权路由打开上游 Watch，`SharedWatchHub` 创建 `SharedWatchEntry`。（docs/device-net-routing-distribution.md:139）
3. 后进入的消费者在自己的逻辑订阅 id 上先收到最新缓存快照，再收到后续变更事件。（docs/device-net-routing-distribution.md:161）
4. 变更事件按源顺序复制给每个活跃消费者；完成事件关闭每个消费者并移除条目。（docs/device-net-routing-distribution.md:161）
5. 最后一个消费者取消时关闭上游 Watch 并移除条目；任一下游订阅者队列达到上限时只关闭该订阅，不拖延源或其他消费者。（docs/device-net-routing-distribution.md:168）

## 来源

- docs/core-node-space-binding-architecture.md
- docs/device-net-routing-distribution.md
- docs/link-access-architecture.md
- core/crates/node/runtime/src/CoreNodeRouter.rs
- core/crates/node/runtime/src/RuntimeRemoteLinkService.rs
- core/crates/tool/services/src/runtime_support.rs
- core/crates/runtime/application/src/services/ChatServiceCore.rs
- core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs
- core/crates/foundation/link/src/protocol.rs
- core/crates/node/runtime/src/peer/dispatch.rs
