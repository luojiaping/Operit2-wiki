---
title: Space
module: arch
platforms: [all]
sources: [docs/core-node-space-binding-architecture.md, docs/sync-architecture.md, docs/device-space-lan-discovery.md, core/crates/node/runtime/src/SpacePersistenceSyncService.rs]
date: 2026-11-11
---

# Space

## 概述

Space 是节点成员、路由和持久化同步的范围：它把多个已配对的 `CoreNode` 组成同一个持续同步网络。它不是执行容器，不拥有 Agent、聊天或运行时。`docs/core-node-space-binding-architecture.md:28`

Space 只负责三件事：确定哪些 `CoreNode` 属于同一个协作范围、确定哪些已配对连接可以承载 Space 流量、确定持久化数据应当在哪些 `CoreNode` 之间持续同步。`docs/core-node-space-binding-architecture.md:69`

Space 不表达执行位置，也不表达数据归属；业务副本由具备 `storage.provide` 且实际提供 Core 存储服务的成员保存和同步。执行位置的决定属于 [[arch-binding|Binding]]。`docs/core-node-space-binding-architecture.md:77`

一句话定位：Space 是协作范围，不是执行位置、不是数据归属、不是执行容器。`docs/core-node-space-binding-architecture.md:77`

## AI 速览

- `Space` — 节点成员、路由和持久化同步的范围；不是执行容器，不拥有 Agent、聊天或运行时。`docs/core-node-space-binding-architecture.md:28`
- `spaceId` — Space 的标识。`docs/core-node-space-binding-architecture.md:63`
- `members` — Space 的成员集合，元素为 `nodeId`。`docs/core-node-space-binding-architecture.md:65`
- `CoreNode` — 运行 Operit Core 的应用实例；Space 的成员。`docs/core-node-space-binding-architecture.md:42`
- `Binding` — 业务方法声明的不透明 key 与目标节点的对应关系。`docs/core-node-space-binding-architecture.md:134`
- `Peer Link` — 一个直接配对连接；多个 Peer Link 组成 Space 的实际网络拓扑。`docs/core-node-space-binding-architecture.md:118`
- `RouteTable` — 每个节点维护的内部路由表；是运行时实现，不是领域概念。`docs/core-node-space-binding-architecture.md:127`
- `SpacePersistenceSyncService` — 授权、交换、分页、Blob 与调度；CoreNode 启动后长期运行。`docs/sync-architecture.md:17` `docs/core-node-space-binding-architecture.md:202`
- `RuntimeRemoteLinkService` — 加入和退出走的普通 service call 宿主。`docs/core-node-space-binding-architecture.md:94`
- `node.space/reconcileSharedSpace` — 成员表分裂收敛的共享空间对账入口。`docs/core-node-space-binding-architecture.md:104`
- `storage.provide` — 参与业务副本同步所需的授权；内置 admin、user、relay 角色均具有该授权。`docs/core-node-space-binding-architecture.md:185`
- `syncClockDigest` — 常量大小探针，本机写出操作的时钟摘要；只有具备存储复制授权、处于正常变更门控状态的可达成员才用它判断是否需要完整交换。`docs/core-node-space-binding-architecture.md:218` `core/crates/node/runtime/src/SpacePersistenceSyncService.rs:734`

主入口：加入 Space 没有单独的协议入口，加入和退出是 `RuntimeRemoteLinkService` 上的普通 service call。`docs/core-node-space-binding-architecture.md:94`

成员表对账入口是 `node.space/reconcileSharedSpace`。`docs/core-node-space-binding-architecture.md:104`

发现入口是局域网 mDNS 查询 `_operit-link._tcp.local.`。`docs/device-space-lan-discovery.md:5`

数据流向：本地业务变更 → 数据集原子提交 → 持久 outbox → 操作日志 → Router / PeerSync → 对端解码与重放 → 原子提交 → 通知。`docs/sync-architecture.md:8`

## 核心机制

### Space 是什么，不是什么

执行模型只包含 `CoreNode` 和 `Binding` 两个概念。`docs/core-node-space-binding-architecture.md:21`

`Space` 是节点成员、路由和持久化同步的范围。`docs/core-node-space-binding-architecture.md:28`

架构中不引入 Chat Core、Agent Core、Env、Placement、Lease、Circuit、Capability 或远程数据放置 Ownership 模型。`docs/core-node-space-binding-architecture.md:34`

`Binding` 只决定 chat 的下一步执行节点，`Binding` 改变不移动数据。`docs/core-node-space-binding-architecture.md:481`

### 身份在 Space 之上

每个身份独立拥有设备身份、直接配对记录、设备空间成员关系、聊天、配置和工作区。`docs/core-node-space-binding-architecture.md:16`

身份不进入设备空间同步，也不通过 Link 传播。`docs/core-node-space-binding-architecture.md:17`

每个身份首次启动时创建一个单设备空间，初始名称使用该设备的显示名称；用户可以独立重命名设备空间，退出共享空间后新建的单设备空间同样使用本机设备显示名称。`docs/core-node-space-binding-architecture.md:115`

### 发现、配对、加入

发现查询 `_operit-link._tcp.local.`，不枚举 IP 地址。`docs/device-space-lan-discovery.md:5`

设备只在已配置的网络监听器运行且 `discoveryEnabled` 启用时才广播；默认监听器是 HTTP 和 WebSocket，使用操作系统分配的端口，绑定 `0.0.0.0`。`docs/device-space-lan-discovery.md:7`

TXT 元数据必须包含 `nodeId`、`displayName` 和 `transports`；不完整广播会被拒绝并给出诊断，不会编造协议数据。`docs/device-space-lan-discovery.md:9`

添加设备对话框执行 5 秒主动扫描，刷新会重启共享查询并保留订阅句柄。`docs/device-space-lan-discovery.md:11`

本地设备和已配对设备有意排除在添加设备结果之外，包括当前离线的已配对设备；已解析的端点仍可供连接层使用。`docs/device-space-lan-discovery.md:14`

发现的宿主实现按平台划分：Windows、Linux、Android 和 OHOS 使用共享原生 mDNS 提供方，守护进程及其浏览器工作线程归 Host 所有；Android 在守护进程打开套接字前获取 Wi-Fi 组播锁，关闭后释放。`docs/device-space-lan-discovery.md:32`

iOS 和 macOS 使用系统 Bonjour DNS-SD 守护进程，不使用应用自有的 UDP 组播套接字；浏览、SRV/TXT 解析、地址监听、注册与取消都留在 Apple Host 内。`docs/device-space-lan-discovery.md:37`

两端都必须允许本地组播 DNS 流量（UDP 5353 到 `224.0.0.251` / `ff02::fb`）以及到广播监听端口的入站连接；AP 隔离、组播过滤和防火墙策略是网络配置问题，不由另一套发现协议绕过。`docs/device-space-lan-discovery.md:55`

发现、配对和加入设备空间按以下顺序进行：发现一个可连接的 Operit，使用现有配对握手建立直接信任，用户明确选择是否加入对方设备空间，双方通过普通 Link call 采用同一个 Space 投影，双方开始交换成员可达信息和持久化同步操作。`docs/core-node-space-binding-architecture.md:86`

配对完成后不会自动加入设备空间。`docs/core-node-space-binding-architecture.md:93`

加入和退出不是新的 Link 协议族，也没有 `space/join-request` 一类协议路径；它们是 `RuntimeRemoteLinkService` 上的普通 service call。配对只建立两个节点之间的直接可信连接。`docs/core-node-space-binding-architecture.md:94`

Space 成员关系使请求可以经过其他成员逐跳到达目标节点，但不会把中间节点与目标节点伪装成直接配对关系。`docs/core-node-space-binding-architecture.md:95`

加入申请只允许合并一个与目标不同的源空间。`docs/core-node-space-binding-architecture.md:97`

申请人发现目标与其本地 `spaceId` 相同时不再提交申请：成员一致说明已经是成员，成员不一致则是成员表分裂，走对账而不是全新的 `AdmitSpace` 审批。网关侧同样拒绝 `sourceSpaceId == targetSpaceId` 的提交，存量记录仍可取消。`docs/core-node-space-binding-architecture.md:97` `docs/core-node-space-binding-architecture.md:100`

### 成员表分裂与收敛

成员表分裂通过共享空间对账（`node.space/reconcileSharedSpace`）收敛。`docs/core-node-space-binding-architecture.md:104`

控制日志是唯一权威：双方交换各自持有的该空间控制操作，只接受对方自源（`originDeviceId` 为对端）且属于该空间的操作，去重后并入本地日志，再各自重放合并日志得到一致的策略状态。`docs/core-node-space-binding-architecture.md:104`

收敛后每端把对端的成员记录改写到策略一致，本机自己的成员身份不因网络消息改写；发起方在策略排除自己时按显式退出处理，宿主侧只报告收敛结果。`docs/core-node-space-binding-architecture.md:107`

之后正常流程即可继续：策略仍承认该设备时无需任何新审批，策略已排除时设备以干净状态重新走标准加入流程。`docs/core-node-space-binding-architecture.md:108`

### 退出

退出设备空间只重写本机成员记录，保留完整业务数据和直接配对记录，并创建新的单设备空间。`docs/core-node-space-binding-architecture.md:111`

直接配对设备先双向交换设备空间投影；只有双方 `spaceId` 相同，才继续交换聊天、配置、`Binding` 和文件操作。因此退出状态可以传播，但退出后不会继续跨空间同步业务数据。`docs/core-node-space-binding-architecture.md:112`

### 同步：三件不同的事

成员资格、网络可达性和存储授权是三件不同的事。`docs/core-node-space-binding-architecture.md:185`

内置 `admin`（通过 `*`）、`user` 和 `relay` 角色均具有 `storage.provide`；新成员采用默认 `user` 角色后即可参与业务副本同步。`docs/core-node-space-binding-architecture.md:185`

业务副本同步（聊天、配置、Binding 日志、对象与文件）只在双方都具备 `storage.provide` 且实际提供 Core 存储服务时运行；后台任务和接收端均检查当前授权。中继同样保存业务副本，撤权后不能继续接收业务副本或 blob。`docs/core-node-space-binding-architecture.md:186`

授权变更通过独立的同空间控制交换传播，不依赖业务存储授权，也不推进业务同步时钟。`docs/core-node-space-binding-architecture.md:191`

`SpacePersistenceSyncService` 是 CoreNode 启动后长期运行的服务；它经认证路由与可达成员持续交换本地操作日志和向量时钟，交换的数据集包括 preferences、chat、object data、agents and memories、tool calls and tool results、Binding、execution completion records。`docs/core-node-space-binding-architecture.md:202`

节点断开后保留自己的操作日志；重新连接时从双方时钟差异继续同步。同步不是由用户触发的一次事务，也不依赖当前 Binding。`docs/core-node-space-binding-architecture.md:214`

同一 Space 内，具备 `storage.provide` 且提供 Core 存储服务的节点交换持久化操作与 Blob；配对、成员资格、路由可达性和存储授权分别校验。`docs/sync-architecture.md:3`

一次接收与一次业务应用是不同事实：操作可靠保存后才能推进接收凭据，业务提交完成后才能标记已应用；相同操作身份必须携带相同内容，重复投递幂等，内容冲突明确报错。`docs/sync-architecture.md:23`

下列数据保持节点本地，不进入 Space 持久化同步：CoreNode 身份私钥、两两配对密钥和 session、HostManager 平台状态、本机监听地址、应用界面缩放、本机平台能力和临时交互句柄。`docs/core-node-space-binding-architecture.md:255`

### Peer Link 与路由表

一个直接配对连接称为 Peer Link；多个 Peer Link 组成 Space 的实际网络拓扑。`docs/core-node-space-binding-architecture.md:118`

节点通过相邻 Peer Link 发布自己知道的 Space 成员和距离；每个节点据此维护内部 `RouteTable`。`docs/core-node-space-binding-architecture.md:126`

`RouteTable` 是运行时实现，不是领域概念。`docs/core-node-space-binding-architecture.md:127`

路由与转发的完整机制见 [[arch-routing|路由与转发]]；持久化同步的机制细节见 [[sync-overview|同步总览：Space 持久化同步]]；CoreNode 的组成见 [[arch-corenode|CoreNode]]。

## 关键符号

- `Space` — 节点成员、路由和持久化同步的范围。`docs/core-node-space-binding-architecture.md:63`
- `spaceId` — Space 的标识。`docs/core-node-space-binding-architecture.md:63`
- `members` — Space 的成员集合，元素为 `nodeId`。`docs/core-node-space-binding-architecture.md:65`
- `CoreNode` — 运行 Operit Core 的应用实例。`docs/core-node-space-binding-architecture.md:42`
- `Binding` — 业务方法声明的不透明 key 与目标节点的对应关系。`docs/core-node-space-binding-architecture.md:134`
- `Peer Link` — 一个直接配对连接。`docs/core-node-space-binding-architecture.md:118`
- `RouteTable` — 每个节点维护的内部路由表；运行时实现，不是领域概念。`docs/core-node-space-binding-architecture.md:127`
- `SpacePersistenceSyncService` — 授权、交换、分页、Blob 与调度。`docs/sync-architecture.md:17`
- `SyncOperationStore` — 原始操作、身份指纹、接收凭据与日志查询。`docs/sync-architecture.md:18`
- `PreferenceMerge` — 偏好 owner 声明与物化协调。`docs/sync-architecture.md:19`
- `PreferencesDataStore` — 单数据集工作副本与原子提交。`docs/sync-architecture.md:20`
- `RuntimeRemoteLinkService` — 加入和退出走的普通 service call 宿主。`docs/core-node-space-binding-architecture.md:94`
- `node.space/reconcileSharedSpace` — 成员表分裂收敛的共享空间对账入口。`docs/core-node-space-binding-architecture.md:104`
- `syncClockDigest` — 常量大小探针，本机写出操作的时钟摘要；只有具备存储复制授权、处于正常变更门控状态的可达成员才用它判断是否需要完整交换。`docs/core-node-space-binding-architecture.md:218` `core/crates/node/runtime/src/SpacePersistenceSyncService.rs:734`
- `storage.provide` — 参与业务副本同步所需的授权。`docs/core-node-space-binding-architecture.md:185`

## 调用链

1. 发现：查询 `_operit-link._tcp.local.`；TXT 元数据必须包含 `nodeId`、`displayName` 和 `transports`。`docs/device-space-lan-discovery.md:5` `docs/device-space-lan-discovery.md:9`
2. 配对：使用现有配对握手建立直接信任。`docs/core-node-space-binding-architecture.md:87`
3. 加入：用户明确选择是否加入对方设备空间。`docs/core-node-space-binding-architecture.md:88`
4. 采用同一个 Space 投影：双方通过普通 Link call 采用同一个 Space 投影。`docs/core-node-space-binding-architecture.md:89`
5. 开始交换：双方开始交换成员可达信息和持久化同步操作。`docs/core-node-space-binding-architecture.md:90`
6. 同步门控：`backoffElapsed` 未到期时不执行完整同步；`pendingWork` 存在或 `consecutiveFailures` 大于 0 时直接判定需要完整同步，不经过摘要探针。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:716`
7. 摘要探针：只有正常存储复制门控分支才调用 `probeRemoteClockSummary` 探针判断是否需要完整交换；未获授权的成员走 `authority_only` 分支直接继续控制交换。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:734`
8. 同步业务数据：本地业务变更 → 数据集原子提交 → 持久 outbox → 操作日志 → Router / PeerSync → 对端解码与重放 → 原子提交 → 通知。`docs/sync-architecture.md:8`
9. 成员表分裂时：双方交换各自持有的该空间控制操作 → 只接受对方自源且属于该空间的操作 → 去重后并入本地日志 → 各自重放合并日志得到一致的策略状态。`docs/core-node-space-binding-architecture.md:104`
10. 退出时：只重写本机成员记录 → 保留完整业务数据和直接配对记录 → 创建新的单设备空间。`docs/core-node-space-binding-architecture.md:111`

## 来源

- `docs/core-node-space-binding-architecture.md`（494 行，100% 已读）
- `docs/sync-architecture.md`（131 行，100% 已读）
- `docs/device-space-lan-discovery.md`（139 行，100% 已读）
- `core/crates/node/runtime/src/SpacePersistenceSyncService.rs`（1907 行，门控与同步区段已读）
