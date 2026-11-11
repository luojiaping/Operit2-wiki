---
title: CoreNode
module: arch
platforms: [all]
sources: [docs/core-node-space-binding-architecture.md, core/CRATE_BOUNDARIES.md, core/crates/README.md, core/crates/application/core/src/lib.rs, core/crates/node/runtime/src/CoreNodeRouter.rs, core/crates/proxy/local/src/lib.rs, core/crates/tool/services/src/tools/ToolRegistration.rs, core/crates/node/runtime/src/SpacePersistenceSyncService.rs]
date: 2026-11-11
---

# CoreNode

## 概述

一个运行 Operit Core 的应用实例就是一个 `CoreNode`（`docs/core-node-space-binding-architecture.md:39`）。

`CoreNode` 由 `nodeId`、`OperitApplication`、`LocalCoreProxy`、`HostManager` 四部分组成（`docs/core-node-space-binding-architecture.md:42`）。

`Flutter` App、`CLI` 和其他平台 App 使用同一种 `CoreNode` 身份（`docs/core-node-space-binding-architecture.md:50`）。

执行模型只包含 `CoreNode` 和 `Binding` 两个概念（`docs/core-node-space-binding-architecture.md:21`）。

[[arch-space|Space]] 划定协作范围，[[arch-binding|Binding]] 决定一个聊天的下一步在哪个 `CoreNode` 执行（`docs/core-node-space-binding-architecture.md:143`）。

注意：代码中不存在名为 `CoreNode` 的 struct 类型；`CoreNode` 是架构文档的概念，代码侧的组装根是 `CoreApplication`（`core/crates/application/core/src/lib.rs:69`）。

## AI 速览

- `CoreNode` — 一个运行 Operit Core 的应用实例（`docs/core-node-space-binding-architecture.md:39`）
- `OperitApplication` — 单节点业务运行时（`core/crates/runtime/application/src/core/application/OperitApplication.rs:119`）
- `LocalCoreProxy` — 本机类型化代理，包起 OperitApplication（`core/crates/proxy/local/src/lib.rs:34`）
- `HostManager` — 本节点宿主能力集（`core/crates/foundation/host-api/src/HostManager.rs:139`）
- `CoreApplication` — 组装根，拥有一棵运行中的 Core 树（`core/crates/application/core/src/lib.rs:69`）
- `CoreApplicationConfig` — 启动一棵 Core 树所需的宿主输入（`core/crates/application/core/src/lib.rs:24`）
- `CoreNodeRouter` — 本机路由器，Binding 路由与 Space 路由的入口（`core/crates/node/runtime/src/CoreNodeRouter.rs:65`）
- `CoreNodeLocalRuntime` — 本地 Core 能力容器，供服务端 Space 路由器使用（`core/crates/node/runtime/src/CoreNodeRouter.rs:77`）
- `BindingRouteStatus` — 对话执行节点的状态提示（`core/crates/node/runtime/src/CoreNodeRouter.rs:41`）
- `SpacePersistenceSyncService` — CoreNode 启动后长期运行的持久化同步服务（`docs/core-node-space-binding-architecture.md:202`）
- `RoutedLink` — 经过 Peer Link 时附加的外层（`docs/core-node-space-binding-architecture.md:289`）

主入口（组装）：`CoreApplication::start`（`core/crates/application/core/src/lib.rs:81`）。

主入口（请求）：本机 `CoreNodeRouter`（`docs/core-node-space-binding-architecture.md:348`）。

数据流向：

本地 App → 本机 `CoreNodeRouter`（`docs/core-node-space-binding-architecture.md:348`）。

普通请求走 `LocalCoreProxy` 本地执行；标注 `Binding` 的请求按 `Binding(key)` 路由到目标 `CoreNode`（`docs/core-node-space-binding-architecture.md:355`）。

持久化数据由 `SpacePersistenceSyncService` 在获准存储的成员之间持续同步（`docs/core-node-space-binding-architecture.md:202`）。

## 核心机制

### 组成与唯一性

每个 `CoreNode` 只有当前应用实例已有的一套 `OperitApplication` + `LocalCoreProxy` + `HostManager`（`docs/core-node-space-binding-architecture.md:50`）。

文件系统、终端、浏览器、HTTP 和平台交互都来自该节点自己的 `HostManager`（`docs/core-node-space-binding-architecture.md:52`）。

一个 `CoreNode` 只有一个 `OperitApplication` 和一个 `HostManager`（`docs/core-node-space-binding-architecture.md:479`）。

`CoreNode` 之间地位对等；服务监听方、连接发起方和请求执行方只是一次连接或调用中的角色，不形成主节点和从节点（`docs/core-node-space-binding-architecture.md:57`）。

`CoreNode` 不持有环境注册表；需要使用另一台设备或另一套 Host 能力时，`Agent` 切换到另一个 `CoreNode`（`docs/core-node-space-binding-architecture.md:54`）。

### 用户身份

每个身份独立拥有设备身份、直接配对记录、设备空间成员关系、聊天、配置和工作区（`docs/core-node-space-binding-architecture.md:16`）。

身份不进入设备空间同步，也不通过 `Link` 传播（`docs/core-node-space-binding-architecture.md:17`）。

`Flutter` 在全局抽屉切换身份，`CLI` 在 Core 启动前通过 `identity` 命令选择身份；切换身份会重启应用并使用目标目录（`docs/core-node-space-binding-architecture.md:17`）。

浏览器端的 `Worker`、`OPFS`、`IndexedDB`、本机密钥、下载任务和跨标签运行时所有权全部按活动身份隔离（`docs/core-node-space-binding-architecture.md:18`）。

### Space 与 Binding 的关系

`Space` 是节点成员、路由和持久化同步的范围，它不是执行容器，不拥有 `Agent`、聊天或运行时（`docs/core-node-space-binding-architecture.md:28`）。

代码中的聊天运行模块只是 `CoreNode` 内部实现，不是可寻址的分布式实体，也不拥有独立身份、网络路由或绑定关系（`docs/core-node-space-binding-architecture.md:31`）。

架构不引入 `Chat Core`、`Agent Core`、`Env`、`Placement`、`Lease`、`Circuit`、`Capability` 或远程数据放置 `Ownership` 模型（`docs/core-node-space-binding-architecture.md:34`）。

`Space` 只负责三件事：确定协作范围成员、确定可承载 `Space` 流量的已配对连接、确定持续同步的成员范围（`docs/core-node-space-binding-architecture.md:69`）。

`Space` 不表达执行位置，也不表达数据归属；业务副本由具备 `storage.provide` 且实际提供 Core 存储服务的成员保存和同步（`docs/core-node-space-binding-architecture.md:76`）。

`Binding` 由 `key`、`nodeId`、`generation` 三个字段组成（`docs/core-node-space-binding-architecture.md:134`）。

`Binding` 只表达一句话：这个 `key` 对应的下一次路由执行由哪个 `CoreNode` 完成（`docs/core-node-space-binding-architecture.md:143`）。

`Binding` 层不知道 `key` 是否来自聊天、任务或其他业务对象；聊天路由直接使用现有 `chatId` 作为 `key`（`docs/core-node-space-binding-architecture.md:145`）。

`Binding` 不表示业务数据位于目标节点；`Agent`、聊天、消息、记忆、工具结果、配置和 `Binding` 本身都由 `Space` 持久化同步服务复制到获准参与业务存储的成员（`docs/core-node-space-binding-architecture.md:146`）。

同一个 `Agent` 的不同聊天可以绑定不同 `CoreNode`；切换 `Binding` 不会移动 `Agent`，也不会移动其对话（`docs/core-node-space-binding-architecture.md:150`）。

`Binding` 只决定 chat 的下一步执行节点；`Binding` 改变不移动数据（`docs/core-node-space-binding-architecture.md:481`）。

### 发现、配对与加入

配对完成后不会自动加入设备空间（`docs/core-node-space-binding-architecture.md:93`）。

加入和退出不是新的 `Link` 协议族，也没有 `space/join-request` 一类协议路径；它们是 `RuntimeRemoteLinkService` 上的普通 service call（`docs/core-node-space-binding-architecture.md:94`）。

加入申请只允许合并一个与目标不同的源空间；目标 `spaceId` 与本地 `spaceId` 相同时不再提交申请（`docs/core-node-space-binding-architecture.md:98`）。

成员表分裂通过共享空间对账 `node.space/reconcileSharedSpace` 收敛；控制日志是唯一权威（`docs/core-node-space-binding-architecture.md:104`）。

退出设备空间只重写本机成员记录，保留完整业务数据和直接配对记录，并创建新的单设备空间（`docs/core-node-space-binding-architecture.md:111`）。

每个身份首次启动时都会创建一个单设备空间，初始名称使用该设备的显示名称（`docs/core-node-space-binding-architecture.md:115`）。

### 节点工具：查看与切换

`Agent` 通过 `list_core_nodes()` 获得节点列表，通过 `switch_core(nodeId)` 切换执行节点（`docs/core-node-space-binding-architecture.md:155`）。

list_core_nodes 返回 `{ currentNodeId, nodes }`（`core/crates/tool/services/src/tools/ToolRegistration.rs:179`）。

`nodes` 是对象数组，每项有 `nodeId`、`displayName`、`userName`、`platform`、`model`、`reachable`、`canExecute`（`core/crates/tool/services/src/tools/ToolRegistration.rs:185`）。

只有 `relayHops` 或 `relayPath` 有值时才出现在每项里（`core/crates/tool/services/src/tools/ToolRegistration.rs:190`）。

`list_core_nodes` 只读取本机已经同步的 `Space` 成员视图（`docs/core-node-space-binding-architecture.md:159`）。

`switch_core` 在调用时按同一份路由视图校验目标：目标不是 `Space` 成员或当前不可达时，工具直接返回失败（`docs/core-node-space-binding-architecture.md:164`）。

目标引用解析按精确 ID、精确名称、大小写不敏感名称、唯一前缀的顺序进行，重名或前缀歧义时返回候选列表而不猜测（`docs/core-node-space-binding-architecture.md:167`）。

`BindingRouteStatus` 表示对话的执行节点，不表示模型推理位置或请求是否需要联网（`docs/core-node-space-binding-architecture.md:175`）。

`Binding` 的冲突顺序复用持久化同步操作的设备序列和向量时钟；同步元数据不是 `Binding` 的业务字段（`docs/core-node-space-binding-architecture.md:178`）。

### 两条独立的数据路径

#### 持久化同步

内置 `admin`、`user` 和 `relay` 角色均具有 `storage.provide`（`docs/core-node-space-binding-architecture.md:184`）。

业务副本同步只在双方都具备 `storage.provide` 且实际提供 Core 存储服务时运行；后台任务和接收端均检查当前授权（`docs/core-node-space-binding-architecture.md:186`）。

授权变更通过独立的同空间控制交换传播，不依赖业务存储授权，也不推进业务同步时钟（`docs/core-node-space-binding-architecture.md:191`）。

`SpacePersistenceSyncService` 是 `CoreNode` 启动后长期运行的服务，经认证路由与可达成员持续交换本地操作日志和向量时钟（`docs/core-node-space-binding-architecture.md:202`）。

节点断开后保留自己的操作日志；重新连接时从双方时钟差异继续同步；同步不是由用户触发的一次事务，也不依赖当前 `Binding`（`docs/core-node-space-binding-architecture.md:214`）。

全量交换由变更门控调度，空闲设备不重复搬运未变化的状态（`docs/core-node-space-binding-architecture.md:217`）。

同步门控先检查 `backoffElapsed`：退避未到期时本周期不做完整交换；`pendingWork` 或 `consecutiveFailures` 大于 0 时直接安排完整交换（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:716`）。

未获存储复制授权的成员走 `authority_only` 分支，直接继续控制交换，不发摘要探针（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:728`）。

只有具备存储复制授权、处于正常变更门控状态的可达成员，才用 `syncClockDigest` 判断是否需要完整交换（`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:67`）。

失败按对端指数退避（2 秒起、60 秒封顶），成功后复位（`docs/core-node-space-binding-architecture.md:230`）。

同步页按字节与条数双重上限导出：单侧一页最多 `DEFAULT_SYNC_PAGE_BYTES`（4 MiB）（`docs/core-node-space-binding-architecture.md:233`）。

一个同步回合持续换页直到某次交换为空，历史完成标记只由这条空页携带；单回合页数有上限（`docs/core-node-space-binding-architecture.md:237`）。

单条操作自身超过上限时，本端直接以 `SYNC_OPERATION_TOO_LARGE` 报错；链路层把超限与鉴权失败分开报告为 `PEER_MESSAGE_TOO_LARGE`（`docs/core-node-space-binding-architecture.md:238`）。

`RuntimeStorageRepository` 读取这份结构化元数据决定写入是否记录同步 operation（`docs/core-node-space-binding-architecture.md:251`）。

`RuntimeFileSyncStore` 只处理已经声明为 `Space` 的文件，不维护 `Skill`、`ToolPkg` 配置、`USER.md`、浏览器数据或临时目录等业务路径清单（`docs/core-node-space-binding-architecture.md:252`）。

下列数据保持节点本地，不进入 `Space` 持久化同步：`CoreNode` 身份私钥、两两配对密钥和 session、HostManager 平台状态、本机监听地址、应用界面缩放、本机平台能力和临时交互句柄（`docs/core-node-space-binding-architecture.md:258`）。

每个需要路由的业务 `key` 必须有一条 `Binding`；创建可执行聊天时，Chat 仓库单独写入 `Binding(chatId)`（`docs/core-node-space-binding-architecture.md:170`）。

每次比较写入成功后 `generation` 单调递增，它同时标识目标节点即将执行的 `continuation`（`docs/core-node-space-binding-architecture.md:171`）。

`Binding` 缺失或指向非 `Space` 成员时，请求返回明确错误（`docs/core-node-space-binding-architecture.md:172`）。

#### 实时传输

实时传输承载 `Core call`、`Core watch`、`Core push`（`docs/core-node-space-binding-architecture.md:271`）。

实时传输还承载 stream event、`Agent` turn continuation、Host interaction response、`Space` 路由控制消息（`docs/core-node-space-binding-architecture.md:275`）。

实时传输不负责复制持久化业务数据；实时 continuation 可以要求目标节点先应用到指定同步时钟，该时钟只是交接屏障，不表示数据迁移（`docs/core-node-space-binding-architecture.md:280`）。

`requiredClock` 是持久化同步屏障；execution generation 来自 `Binding` 比较写入，不复用模型进程内部的 execution 或 round 身份（`docs/core-node-space-binding-architecture.md:407`）。

### 转发层

经过 Peer Link 时只增加一个外层 `RoutedLink`（`docs/core-node-space-binding-architecture.md:289`）。

转发外层（`payload`）是现有 `Link` 消息或 `Space` 控制消息；外层不携带 `chatId`、`Binding`、`envId`、文件路径或 Host 配置（`docs/core-node-space-binding-architecture.md:297`）。

每个 `CoreNode` 保存 `Space` 拓扑，第一跳必须是当前活跃且获准承载该 `Space` 流量的直接 Peer Link（`docs/core-node-space-binding-architecture.md:312`）。

心跳过期、连接关闭或策略断开时撤销对应连接与本机拓扑边；本机只发布自身连接事实，远端公告不能证明本机第一跳在线（`docs/core-node-space-binding-architecture.md:313`）。

路由结果随设备投影与 `list_core_nodes` 暴露给上层；非本机直连的状态标记为 `Announced`（`docs/core-node-space-binding-architecture.md:320`）。

`ttl` 每转发一次减一；无有效路径、TTL 用尽或目标不属于 `Space` 时属于路由失败（`docs/core-node-space-binding-architecture.md:321`）。

转发期间先取得路由和连接句柄，释放互斥锁后再等待网络响应（`docs/core-node-space-binding-architecture.md:325`）。

每一跳向 `nextPeer` 发起一个下游 call 并等待结果；目标节点解开 `RoutedLink`，把原始 `CoreCallRequest` 交给自己的 `LocalCoreProxy`（`docs/core-node-space-binding-architecture.md:327`）。

每一跳在 `nextPeer` 上打开同一个逻辑订阅，并把下游 `CoreEvent` 按顺序写给上游；上游关闭、下游完成或 Peer Link 断开时，该跳释放对应订阅（`docs/core-node-space-binding-architecture.md:331`）。

`Binding` 不参与普通 watch 转发；持久化聊天界面优先观察本地同步数据，明确观察某个 `CoreNode` 实时状态的 watch 才发送到该节点（`docs/core-node-space-binding-architecture.md:333`）。

每一跳固定打开时解析出的 `nextPeer`，并保持同一 `pushId` 内的 sequence 顺序；关闭上游 push 时，该跳关闭下游 push；路由中断返回流错误，不把同一个 push 静默改送另一节点（`docs/core-node-space-binding-architecture.md:338`）。

### 请求路由

本地 App 始终首先进入本机 `CoreNodeRouter`（`docs/core-node-space-binding-architecture.md:348`）。

普通请求进入 `LocalCoreProxy`（`docs/core-node-space-binding-architecture.md:353`）。

标注了 `Binding` 的请求经 `Binding(key)` 路由到目标 `CoreNode`（`docs/core-node-space-binding-architecture.md:355`）。

传输定向的 `CoreNode` 请求直接发往目标 `CoreNode`（`docs/core-node-space-binding-architecture.md:358`）。

聊天历史读取、配置编辑和其他持久化数据操作在本地 Core 执行，由持续同步传播；只有模型执行、工具循环、取消当前执行和实时执行状态进入 `Binding` 路由（`docs/core-node-space-binding-architecture.md:362`）。

整段会话删除属于本地持久化操作，不要求存在 `Binding`，也不要求执行节点在线（`docs/core-node-space-binding-architecture.md:365`）。

会话 ID 的删除是终态，由 SQL owner 在同一事务内删除历史并记录删除事实；迟到的消息、快照或 `Binding` 不能重建该 ID，新建或恢复会话必须使用新 ID（`docs/core-node-space-binding-architecture.md:367`）。

请求类型由真实 Core 方法上的 `#[operit_core_route(...)]` 声明，经 typed Core codegen 生成，不通过对象名、方法名或路径字符串猜测业务含义（`docs/core-node-space-binding-architecture.md:371`）。

`Flutter`、`CLI` 和其他客户端仍调用普通 Core 方法，不创建 `Binding` 引用路径（`docs/core-node-space-binding-architecture.md:373`）。

请求显式携带 `Binding` key 时直接使用；未携带时，本机 `CoreNodeRouter` 调用注解声明的 `resolver` 读取当前 key，把 key 注入真实请求后再选择 `Binding` 目标；未标注的方法始终留在本地 Core（`docs/core-node-space-binding-architecture.md:374`）。

### 切换边界与单一执行者

切换 `CoreNode` 直接携带当前运行上下文续接，不触发会话总结或上下文压缩，也不以压缩成功作为切换前提；切换前的生命周期只检查执行所有权（`docs/core-node-space-binding-architecture.md:379`）。

`CoreNode` 切换的边界是：工具调用已经完成、工具结果已经持久化、下一轮模型请求尚未发起（`docs/core-node-space-binding-architecture.md:385`）。

Router 在比较写入前验证目标属于 `Space` 且 `Link` 路由可达（`docs/core-node-space-binding-architecture.md:409`）。

`Binding` 的比较写入成功后，它就是新的唯一执行位置；后续持久化同步屏障或 continuation 失败必须返回明确错误，不自动把 `Binding` 改回源节点（`docs/core-node-space-binding-architecture.md:411`）。

每轮模型请求开始前，`CoreNode` 必须确认 `Binding(chatId)` 指向自己；`Binding` 更新使用当前值比较写入，只有当前执行节点能够提交 `Agent` 发起的切换（`docs/core-node-space-binding-architecture.md:416`）。

旧节点观察到 `Binding` 已改变后不得继续下一轮模型请求（`docs/core-node-space-binding-architecture.md:418`）。

目标节点按 `(chatId, executionGeneration)` 识别 continuation；进程内集合只记录正在执行的 generation（`docs/core-node-space-binding-architecture.md:420`）。

启动前读取 assistant 消息的 `completedExecutionGeneration`，已经完成相同或更高 generation 时直接返回，不重复调用模型或工具（`docs/core-node-space-binding-architecture.md:422`）。

正常完成时，`Binding` Store 以不透明 key、当前节点和 generation 建立本地执行门控；门控持有期间，最终 assistant message、结构化 parts、chat metadata、`completedExecutionGeneration` 和同步操作在同一个 `SQLite` 事务内提交（`docs/core-node-space-binding-architecture.md:425`）。

`Binding` Store 不读取任何 Chat 类型或表（`docs/core-node-space-binding-architecture.md:428`）。

响应流属于一次用户发起的 execution，不属于执行 `CoreNode`；最初接受请求的 `CoreNodeRouter` 保持上游流，当前执行节点只产生该 execution 的后续事件（`docs/core-node-space-binding-architecture.md:431`）。

发生切换时，当前执行节点把 handoff 结果返回给 origin router，origin router 根据新的 `Binding` 打开下一段 continuation，并把事件继续写入同一个上游 stream；多次切换不会形成 A -> B -> C 的永久转发链（`docs/core-node-space-binding-architecture.md:434`）。

### 安全与成员边界

每一跳只接受已配对 Peer 的签名流量；收到 `RoutedLink` 后必须验证：当前节点属于 `spaceId`、上一跳属于 `spaceId`、`targetNodeId` 属于 `spaceId`、`payload` 类型允许在该 Peer Link 上转发（`docs/core-node-space-binding-architecture.md:463`）。

中间节点保留真实上一跳 session 作为审计来源；目标 `CoreNode` 获得 origin `nodeId` 和经过的相邻 session 审计记录，不能把所有多跳请求折叠成最后一个中继节点的控制者身份（`docs/core-node-space-binding-architecture.md:469`）。

设备身份、配对 secret 和 Host 授权保持节点本地；`Space` 成员资格不授予其他节点直接读取本机文件或终端的能力，只有在该 `CoreNode` 上执行的 `Agent` 工具通过本机 `HostManager` 访问这些能力（`docs/core-node-space-binding-architecture.md:472`）。

### 必须保持的约束

一个 `CoreNode` 只有一个 `OperitApplication` 和一个 `HostManager`（`docs/core-node-space-binding-architecture.md:479`）。

`Binding` 只决定 chat 的下一步执行节点；`Binding` 改变不移动数据（`docs/core-node-space-binding-architecture.md:481`）。

工具结果持久化完成后才能交接下一轮模型调用（`docs/core-node-space-binding-architecture.md:483`）。

一个 chat 的同一执行轮次只有一个 `CoreNode` 可以推进（`docs/core-node-space-binding-architecture.md:484`）。

转发只复用已有 `Link` call/watch/push 身份（`docs/core-node-space-binding-architecture.md:485`）。

两两配对仍是所有直接网络信任的基础（`docs/core-node-space-binding-architecture.md:486`）。

路由和网络等待期间不持有全局 Core 互斥锁（`docs/core-node-space-binding-architecture.md:487`）。

`Binding` 目标不可达时由发起设备原子接管，显式设备调用仍返回明确错误（`docs/core-node-space-binding-architecture.md:488`）。

### 模块职责

| 模块 | 职责 |
| --- | --- |
| `operit-store` | 操作日志、收据、`Binding` 与各存储 owner 的提交；拓扑记录与确定性路由计算（`docs/core-node-space-binding-architecture.md:442`） |
| `operit-link` | Call、Watch、Push、事件、错误和流的协议契约（`docs/core-node-space-binding-architecture.md:443`） |
| `node/peer-link` | 认证连接承载、心跳、请求关联和连接生命周期（`docs/core-node-space-binding-architecture.md:444`） |
| `node/runtime` | 配对与成员策略、`CoreNodeRouter`、逐跳转发、共享 Watch 与同步调度（`docs/core-node-space-binding-architecture.md:445`） |
| `operit-proxy-local` | 本机类型化代理与业务分发（`docs/core-node-space-binding-architecture.md:446`） |
| `runtime/application` | 单节点业务运行时、模型工具循环与 handoff（`docs/core-node-space-binding-architecture.md:447`） |
| `application/core` | 组装 Core、Proxy、Node 与 Host 的应用树（`docs/core-node-space-binding-architecture.md:448`） |

### Crate 边界

`operit-runtime` 是父编排 crate，拥有应用启动、服务装配、插件资产、偏好、工作区服务、聊天服务生命周期、Provider 支持实现和工具支持实现（`core/CRATE_BOUNDARIES.md:41`）。

子 crate 不得依赖 `operit-runtime`；`operit-runtime` 可以依赖全部子 crate（`core/CRATE_BOUNDARIES.md:66`）。

`operit-node-edge` 是轻量设备侧 Edge Core 节点，它不是架构文档定义的完整 `CoreNode` 组合（`core/CRATE_BOUNDARIES.md:51`）。

`HostManager` 拥有活动的宿主能力集和面向生命周期的宿主句柄；平台 crate 提供实现，运行时代码只看到显式 trait 与环境描述符（`core/CRATE_BOUNDARIES.md:140`）。

依赖方向是 `plugin-sdk/host-api` → `util` → `model` → `store` → `tools/local-models/providers/js-bridge` → `runtime` → `core-proxy/command-core`（`core/CRATE_BOUNDARIES.md:61`）。

`node` 域覆盖节点身份、配对、认证 peer link 及其传输、路由宏、节点路由、空间运行时与同步（`core/crates/README.md:15`）。

`application` 域是组装根，把 runtime、proxy、node 组装成一棵 Core 树（`core/crates/README.md:21`）。

## 关键符号

| 符号 | 职责 | 引用 |
| --- | --- | --- |
| `CoreNode` | 一个运行 Operit Core 的应用实例（架构概念，代码中无同名 struct） | `docs/core-node-space-binding-architecture.md:39` |
| `OperitApplication` | 单节点业务运行时 | `core/crates/runtime/application/src/core/application/OperitApplication.rs:119` |
| `LocalCoreProxy` | 本机类型化代理，包起 OperitApplication | `core/crates/proxy/local/src/lib.rs:34` |
| `HostManager` | 本节点宿主能力集 | `core/crates/foundation/host-api/src/HostManager.rs:139` |
| `CoreApplication` | 组装根，拥有一棵运行中的 Core 树 | `core/crates/application/core/src/lib.rs:69` |
| `CoreApplicationConfig` | 启动一棵 Core 树所需的宿主输入 | `core/crates/application/core/src/lib.rs:24` |
| `CoreNodeRouter` | 本机路由器，Binding 路由与 Space 路由的入口 | `core/crates/node/runtime/src/CoreNodeRouter.rs:65` |
| `CoreNodeLocalRuntime` | 本地 Core 能力容器，供服务端 Space 路由器使用 | `core/crates/node/runtime/src/CoreNodeRouter.rs:77` |
| `BindingRouteStatus` | 对话执行节点的状态提示 | `core/crates/node/runtime/src/CoreNodeRouter.rs:41` |
| `Binding` | 只决定一个业务 key 的下一次路由执行由哪个 CoreNode 完成 | `docs/core-node-space-binding-architecture.md:134` |
| `SpacePersistenceSyncService` | CoreNode 启动后长期运行的持久化同步服务 | `docs/core-node-space-binding-architecture.md:202` |
| `RoutedLink` | 经过 Peer Link 时附加的外层 | `docs/core-node-space-binding-architecture.md:289` |
| `RuntimeRemoteLinkService` | 加入与退出 Space 的普通 service call 所在服务 | `docs/core-node-space-binding-architecture.md:94` |

## 调用链

### 组装一棵 Core 树

1. `CoreApplication::start` 从 `CoreApplicationConfig` 启动一棵 Core 树（`core/crates/application/core/src/lib.rs:81`）。
2. 先用 `config.hostManager` 创建 `OperitApplication` 并调用 `onCreate`，再由 `LocalCoreProxy::new` 包起它（`core/crates/application/core/src/lib.rs:84`）。
3. 从 `localClient` 取出 `coreNodeLocalRuntime`，据此新建 `CoreNodeRouter`，并把 `deviceToolService` 绑定到 `CoreNodeRouter`（`core/crates/application/core/src/lib.rs:131`）。
4. 用 `nodeRuntime` 与 `nodeRouter` 创建 `RuntimeRemoteLinkService` 作为访问服务（`core/crates/application/core/src/lib.rs:141`）。

### 请求进入 CoreNode

1. 本地 App 始终首先进入本机 `CoreNodeRouter`（`docs/core-node-space-binding-architecture.md:348`）。
2. 普通请求进入 `LocalCoreProxy`（`docs/core-node-space-binding-architecture.md:353`）。
3. 标注了 `Binding` 的请求经 `Binding(key)` 路由到目标 `CoreNode`（`docs/core-node-space-binding-architecture.md:355`）。
4. 传输定向的 `CoreNode` 请求直接发往目标 `CoreNode`（`docs/core-node-space-binding-architecture.md:358`）。

### 切换执行节点（10 步）

1. node-A 的模型产生 `switch_core(node-D)`（`docs/core-node-space-binding-architecture.md:395`）。
2. node-A 验证 node-D 是可达的 Space 成员（`docs/core-node-space-binding-architecture.md:396`）。
3. node-A 在一个事务内持久化 assistant 工具调用、工具结果、chat metadata 和同步操作（`docs/core-node-space-binding-architecture.md:397`）。
4. 响应业务向 Router 返回只包含目标和不透明 payload 的 route transition（`docs/core-node-space-binding-architecture.md:398`）。
5. Router 比较写入 `Binding(chat-1) = node-D`，得到新的 `generation` 和 operation（`docs/core-node-space-binding-architecture.md:399`）。
6. Router 把 `Binding` record 和 operation 放入 `Link` route context，把不透明 transition 作为业务参数发送到 node-D（`docs/core-node-space-binding-architecture.md:400`）。
7. node-D 的 Router 在调用业务恢复方法前应用并校验 `Binding` operation，但不提前推进持久化同步 clock（`docs/core-node-space-binding-architecture.md:401`）。
8. node-D 的响应业务只接收 `Link` 定义的 route key/generation，等待 `requiredClock`（`docs/core-node-space-binding-architecture.md:402`）。
9. node-D 加载已同步 assistant 消息并使用 `switch_core` 的工具结果发起下一轮模型请求（`docs/core-node-space-binding-architecture.md:403`）。
10. node-D 的输出事件继续写入原来的逻辑响应流（`docs/core-node-space-binding-architecture.md:404`）。

## 来源

- docs/core-node-space-binding-architecture.md（494 行，seed）
- core/CRATE_BOUNDARIES.md（188 行，seed）
- core/crates/README.md（26 行，seed）
- core/crates/application/core/src/lib.rs（组装位置核实）
- core/crates/node/runtime/src/CoreNodeRouter.rs（组装位置核实）
- core/crates/proxy/local/src/lib.rs（组装位置核实）
- core/crates/foundation/host-api/src/HostManager.rs（组装位置核实）
- core/crates/runtime/application/src/core/application/OperitApplication.rs（组装位置核实）
- core/crates/tool/services/src/tools/ToolRegistration.rs（list_core_nodes 工具实现核实）
- core/crates/node/runtime/src/SpacePersistenceSyncService.rs（同步门控核实）
