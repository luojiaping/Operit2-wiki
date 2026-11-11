---
title: 设备间路由与实时分发
module: sync
platforms: [all]
sources: [2]
date: 2026-11-11
---

## 概述

- 文档定义多设备 Space 的路由与实时数据分发算法。`docs/device-net-routing-distribution.md:5`
- 本页覆盖由已认证 Peer Link 构成的应用层 overlay 上的路由与实时分发。`docs/device-net-routing-distribution.md:7`
- 本页的路由与分发规则来自设计文档 device-net-routing-distribution.md 的定义，PeerSync.rs 提供其上的对端同步调用面；调用路由与 Binding 由 [[arch-routing|路由与转发]] 讲，本页不展开。`docs/device-net-routing-distribution.md:7`
- 承载层（如 EasyTier）与 Operit 的路由是两层独立的决策：承载层选两个可达虚拟地址之间的物理包路径，Operit 选 Core 请求的下一个已认证 Peer Link，并决定一个实时源在哪里复制。`docs/device-net-routing-distribution.md:11`
- 文档不定义设备角色、执行位置、身份，以及 EasyTier 这类承载层使用的 NAT 穿越算法。`docs/device-net-routing-distribution.md:8`
- 路由目标是选择代价最小的活跃路由，而不只是 overlay 跳数最少的路由。`docs/device-net-routing-distribution.md:19`
- 分发目标是共享的实时状态源在一条边上只发一次，再在共同中间节点分发。`docs/device-net-routing-distribution.md:21`
- 分发目标还包括保持每个逻辑 Watch 的顺序、完成、取消与失败行为。`docs/device-net-routing-distribution.md:23`
- 分发目标还包括让过载可见，并隔离慢订阅者而不阻塞其他订阅者。`docs/device-net-routing-distribution.md:25`
- 路由只使用已认证的 Space 成员与活跃的直连 Peer Links。`docs/device-net-routing-distribution.md:26`

## AI 速览

- `LinkAdvertisement` — 每条活跃有向 Peer Link 发布的链路状态广告，含往返时延、丢失率与拥塞度。`docs/device-net-routing-distribution.md:37`
- `RouteDecision` — 一次路由决策的结果，含目的节点、下一跳、总代价与拓扑代系。`docs/device-net-routing-distribution.md:96`
- `SharedWatchHub` — 每个路由器拥有的共享 Watch 中枢，`SnapshotShared` 条目按源与路由键去重。`docs/device-net-routing-distribution.md:141`
- `SharedWatchEntry` — 一个共享 Watch 条目，恰好拥有一个上游 Watch，含最新快照与下游订阅者。`docs/device-net-routing-distribution.md:155`
- `RoutedCoreRequest.ttl` — 路由请求的硬循环上限，初始值为合格顶点数。`docs/device-net-routing-distribution.md:108`
- `NODE_SYNC_TARGET` — 对端同步调用的目标，值为 `$node.sync`。`core/crates/node/runtime/src/PeerSync.rs:5`
- `PeerSyncMethod` — 对端同步的完整远程调用面枚举，含 16 个方法变体。`core/crates/node/runtime/src/PeerSync.rs:18`
- `PeerSyncPushMethod` — 对端同步推送方法枚举，只有一个变体 `SyncReceiveBlob`。`core/crates/node/runtime/src/PeerSync.rs:103`
- 主入口函数：路由决策由路由器按新调用、Watch 打开或 Push 打开触发重算；对端同步调用由 PeerSyncMethod 的 `request` 构建。`core/crates/node/runtime/src/PeerSync.rs:44`
- 数据流向一句话：链路广告汇聚成链路状态图，Dijkstra 选出代价最小的下一跳，SnapshotShared 的 Watch 在共同中间节点分发，持久同步经路由图做向量时钟交换。`docs/device-net-routing-distribution.md:231`

## 核心机制

- 每条活跃有向 Peer Link 发布一个 `LinkAdvertisement`，字段为 `sourceNodeId`、`targetNodeId`、`channelEpoch`、`sequence`、`measuredAt`、`expiresAt`、`smoothedRttMs`、`lossPermille`、`congestionPermille`。`docs/device-net-routing-distribution.md:37`
- `channelEpoch` 在 Peer Link 重建时变化，`sequence` 在该 epoch 内单调递增。`docs/device-net-routing-distribution.md:47`
- 接收方为每条有向边保留最新的 LinkAdvertisement，并在 `expiresAt` 丢弃广告。`docs/device-net-routing-distribution.md:48`
- 直连 Peer Link 用带序号的心跳请求与回显测量往返时间，保留有界的最近样本窗口，再发布指数加权移动平均值。`docs/device-net-routing-distribution.md:51`
- loss 是错过测量窗口的心跳序号占比，congestion 是帧被承载层接受前观测到的有界出站帧队列占用率。`docs/device-net-routing-distribution.md:53`
- 广告在实质变化时发出，并按固定刷新间隔发出，实质变化阈值、整数化与刷新周期防止遥测把持久同步日志变成心跳传输。`docs/device-net-routing-distribution.md:58`
- Space 拓扑控制面把最新广告带给每个成员。`docs/device-net-routing-distribution.md:61`
- 边合格的条件之一是两端都是当前 Space 成员。`docs/device-net-routing-distribution.md:66`
- 边合格的条件之一是广告未过期。`docs/device-net-routing-distribution.md:67`
- 边合格的条件之一是本地源端点是一条活跃的直连 Peer Link。`docs/device-net-routing-distribution.md:68`
- 边合格的条件之一是边有合法的 channel epoch 与 sequence。`docs/device-net-routing-distribution.md:69`
- 本地源端点的合格规则保护路由不受陈旧拓扑投影影响，每个远程中间节点在转发前执行同样的合格检查。`docs/device-net-routing-distribution.md:72`
- 路由器用 Dijkstra 算法计算有向最短路径树，图由合格的 LinkAdvertisement 构成。`docs/device-net-routing-distribution.md:78`
- 边代价是整数，对持有相同链路状态代系的所有节点保持稳定。`docs/device-net-routing-distribution.md:80`
- 边代价公式为 cost(u, v) = 1000 + 10 * smoothedRttMs(u, v) + 25 * lossPermille(u, v) + 10 * congestionPermille(u, v)。`docs/device-net-routing-distribution.md:84`
- 基础代价 1000 防止一串各自低延迟的链路靠累积舍入噪声取胜。`docs/device-net-routing-distribution.md:89`
- 代价系数是配置常量，不是协议字段。`docs/device-net-routing-distribution.md:91`
- 总代价相等时选择字典序最小的第一跳，使独立路由器收敛到同一路径并使测试确定。`docs/device-net-routing-distribution.md:103`
- 无合格路径的路由查找返回不可达错误，绝不凭成员关系或陈旧广告凭空造边。`docs/device-net-routing-distribution.md:105`
- `RoutedCoreRequest.ttl` 是硬循环上限，初始 TTL 为合格顶点数，每转发一跳减一。`docs/device-net-routing-distribution.md:108`
- 路由器为新调用、Watch 打开或 Push 打开重新计算路由，已打开的 Watch 与 Push 在其生命周期内保留既有物理路径。`docs/device-net-routing-distribution.md:111`
- Watch 路由在生成的 Core 路由元数据中声明一个分发类：`Unicast` 或 `SnapshotShared`。`docs/device-net-routing-distribution.md:119`
- `Unicast` 用于执行事件、工具流、增量、仅追加日志，以及任何后来订阅者必须看到完整历史的序列，且总是打开独立的上游流。`docs/device-net-routing-distribution.md:125`
- `SnapshotShared` 用于有完整当前快照及后续替换的状态投影，新接入的订阅者先收到最新缓存快照再收到后续变化。`docs/device-net-routing-distribution.md:129`
- 一条路由不能仅因两个序列化请求看起来相等就进入 `SnapshotShared` 类。`docs/device-net-routing-distribution.md:131`
- 生成的声明是分发分类的唯一权威，传输层不从对象 id、方法名、参数名或事件负载推断分类。`docs/device-net-routing-distribution.md:134`
- 每个路由器拥有一个 `SharedWatchHub`，`SnapshotShared` 条目以 (spaceId, targetNodeId, routeKind, target, propertyName, canonicalArguments, topologyGeneration) 为键。`docs/device-net-routing-distribution.md:141`
- `canonicalArguments` 是排除请求 id 后的结构化 Link 编解码表示，Core Value 映射已有确定键序，键使用其编码字节而非文本搜索或子串约定。`docs/device-net-routing-distribution.md:147`
- 第一个消费者沿加权路由打开上游 Watch，快照已存入后进入的消费者在其自己的逻辑订阅 id 上收到该快照。`docs/device-net-routing-distribution.md:162`
- changed 事件按源顺序复制给每个活跃消费者，完成事件关闭全部消费者并移除条目，最后一个消费者取消时关闭上游 Watch 并移除条目。`docs/device-net-routing-distribution.md:164`
- 每个下游订阅者有有界事件队列，触及上限时该逻辑订阅以 `PEER_WATCH_CONSUMER_SLOW` 关闭，不拖慢源端或其他消费者。`docs/device-net-routing-distribution.md:169`
- 队列占用计入链路拥塞度量，用于后续路由决策。`docs/device-net-routing-distribution.md:171`
- 共享 Watch 条目构成以源为根的反向最短路径树，C 与 D 经 B 订阅 A 的同一 SnapshotShared 源时只产生一条 A 到 B 的上游流与两条 B 到消费者的流，源事件只经过 A-B 一次。`docs/device-net-routing-distribution.md:179`
- 控制面保持个体化与已认证，包含 `CoreLinkWatchRequest::Open`、`CoreLinkWatchRequest::Close`、路由错误与 `LinkAdvertisement`。`docs/device-net-routing-distribution.md:190`
- 数据面只有在 `SnapshotShared` 声明核查通过后才可共享，共享内容为 `CoreEvent` 的 snapshot 与 changed 事件。`docs/device-net-routing-distribution.md:197`
- 每个下游事件按该消费者的逻辑请求 id 重写，每个消费者流内保留原始源顺序。`docs/device-net-routing-distribution.md:199`
- 文档的验证拓扑之一是直连高延迟边与两跳低延迟路径，Dijkstra 选择总代价更低的路径。`docs/device-net-routing-distribution.md:215`
- 文档的验证拓扑之一是过期的广告或不活跃的本地 Peer Link 导致路由不存在。`docs/device-net-routing-distribution.md:218`
- 文档的验证拓扑之一是 C 与 D 经 B 订阅 A 的同一 `SnapshotShared` 源时，B 持有一个上游 Watch 并在 A-B 上每个事件只发一次。`docs/device-net-routing-distribution.md:220`
- 文档的验证拓扑之一是慢速共享订阅者关闭时不拖慢健康消费者。`docs/device-net-routing-distribution.md:224`
- 文档的验证拓扑之一是承载层关闭结束受影响的树分支，不影响无关订阅。`docs/device-net-routing-distribution.md:226`
- 持久同步 worker 先通过直连配对交换已认证的 Space 投影，再枚举经加权路由图可达的每个当前 Space 成员并与之做常规向量时钟交换。`docs/device-net-routing-distribution.md:231`
- 多跳成员直接经既有路由 Core 调用路径参与反熵，不要求在源设备上有出站配对记录。`docs/device-net-routing-distribution.md:234`
- 直连对端拓扑与链路质量度量同属一个 Space 拥有的拓扑实体，移除直连 Peer Link 会移除其拓扑边与质量度量，没有当前拓扑边的度量不能产生合格路由。`docs/device-net-routing-distribution.md:240`
- 文档划分的模块职责表中，`operit-peer-link/connection` 负责心跳回显、本地度量、有界帧队列与逐消费者事件投递。`docs/device-net-routing-distribution.md:207`
- 文档划分的模块职责表中，`operit-store/CoreSpaceStore` 负责一条含直连对端与链路度量的持久化拓扑记录、过期过滤、有向 Dijkstra 与确定性路由决策。`docs/device-net-routing-distribution.md:208`
- 文档划分的模块职责表中，`operit-node-runtime/CoreNodeRouter` 为新操作选择路由并拥有 `SharedWatchHub`。`docs/device-net-routing-distribution.md:209`
- 文档划分的模块职责表中，`operit-link` 与路由代码生成负责为每个真实 Core Watch 路由声明 `Unicast` 或 `SnapshotShared`。`docs/device-net-routing-distribution.md:210`
- PeerSync.rs 实现类型化的对端同步协议，本地管理目标永不暴露。`core/crates/node/runtime/src/PeerSync.rs:1`
- PeerSyncMethod 枚举包含 `SyncReadSnapshot`、`SyncReadCoverage`、`SyncRepairSnapshot`、`SyncOperationsSince`、`SyncApplyOperations`、`SyncBlobExists`、`SyncReadBlobChunk`、`SyncApplyImmediateBindingOperation`。`core/crates/node/runtime/src/PeerSync.rs:26`
- 设备空间检查与即时执行绑定是控制面调用，不是复制持久业务数据的邀请。`core/crates/node/runtime/src/PeerSync.rs:35`
- `SyncApplyOperations` 要求操作数组，参数无效时以 `PEER_SYNC_INVALID_OPERATIONS` 失败。`core/crates/node/runtime/src/PeerSync.rs:67`
- `SyncReadSnapshot` 与 `SyncReadCoverage` 校验 `ReadSnapshot` 参数，`SyncRepairSnapshot` 校验 `RepairSnapshot` 参数，快照参数无效时以 `PEER_SYNC_INVALID_SNAPSHOT` 失败。`core/crates/node/runtime/src/PeerSync.rs:75`
- 测试断言 `PeerSyncMethod` 经 `request` 与 `fromRequest` 往返后相等，且请求目标为 `NODE_SYNC_TARGET`。`core/crates/node/runtime/src/PeerSync.rs:146`
- 测试断言 `startPairing` 不是对端同步操作，`PeerSyncMethod` 的 `fromRequest` 对其返回错误。`core/crates/node/runtime/src/PeerSync.rs:170`
- 测试断言 `SyncApplyOperations` 拒绝含 `complete`、`forceApply`、`spaceMerge`、`firstJoin` 的参数。`core/crates/node/runtime/src/PeerSync.rs:175`
- 测试断言对端同步推送只接受 `syncReceiveBlob`，`startListening` 被拒绝。`core/crates/node/runtime/src/PeerSync.rs:191`

## 关键符号

- `LinkAdvertisement` — 每条活跃有向 Peer Link 发布的链路状态广告。`docs/device-net-routing-distribution.md:37`
- `RouteDecision` — 路由决策结果，含 `destinationNodeId`、`nextHopNodeId`、`totalCost`、`topologyGeneration`。`docs/device-net-routing-distribution.md:96`
- `SharedWatchHub` — 每个路由器拥有的共享 Watch 中枢。`docs/device-net-routing-distribution.md:141`
- `SharedWatchEntry` — 一个共享 Watch 条目，含 `latestSnapshot`、`upstreamSubscription`、`downstreamSubscribers`、`routeDecision`。`docs/device-net-routing-distribution.md:155`
- `RoutedCoreRequest.ttl` — 路由请求的硬循环上限。`docs/device-net-routing-distribution.md:108`
- `PEER_WATCH_CONSUMER_SLOW` — 下游订阅者队列触及上限时关闭该逻辑订阅的错误码。`docs/device-net-routing-distribution.md:169`
- `CoreLinkWatchRequest::Open` — 控制面的 Watch 打开请求。`docs/device-net-routing-distribution.md:190`
- `CoreLinkWatchRequest::Close` — 控制面的 Watch 关闭请求。`docs/device-net-routing-distribution.md:190`
- `NODE_SYNC_TARGET` — 对端同步调用的目标，值为 `$node.sync`。`core/crates/node/runtime/src/PeerSync.rs:5`
- `PeerSyncMethod` — 对端同步的完整远程调用面枚举。`core/crates/node/runtime/src/PeerSync.rs:18`
- `PeerSyncMethod` 的 `requiresStorageProvider` — 判断一个同步方法是否需要存储提供者。`core/crates/node/runtime/src/PeerSync.rs:38`
- PeerSyncMethod 的 `request` — 用目标与序列化方法名构建 `CoreCallRequest`。`core/crates/node/runtime/src/PeerSync.rs:44`
- PeerSyncMethod 的 `fromRequest` — 校验确切的对端方法与类型化操作信封。`core/crates/node/runtime/src/PeerSync.rs:56`
- `SyncRequest` — 同步请求的信封，字段为 `limit` 与 `force`。`core/crates/node/runtime/src/PeerSync.rs:9`
- `ReadSnapshot` — 快照读取参数，字段为 `owner` 与 `token`。`core/crates/node/runtime/src/PeerSync.rs:86`
- `RepairSnapshot` — 快照修复参数，字段为 `owner`、`expected` 与 `reference`。`core/crates/node/runtime/src/PeerSync.rs:92`
- `ApplyOperations` — 操作应用参数，字段 `operations` 的类型为 `Vec<SyncOperation>`。`core/crates/node/runtime/src/PeerSync.rs:97`
- `PeerSyncPushMethod` — 对端同步推送方法枚举，只有一个变体 `SyncReceiveBlob`。`core/crates/node/runtime/src/PeerSync.rs:103`
- `PeerSyncPushMethod` 的 `fromRequest` — 只接受 `syncReceiveBlob` 推送。`core/crates/node/runtime/src/PeerSync.rs:190`

## 调用链

1. 链路度量：直连 Peer Link 用带序号的心跳请求与回显测量往返时间，发布指数加权移动平均值、loss 与 congestion。`docs/device-net-routing-distribution.md:51`
2. 广告发布：每条活跃有向 Peer Link 发布 LinkAdvertisement，在实质变化时与固定刷新间隔发出。`docs/device-net-routing-distribution.md:58`
3. 广告汇聚：Space 拓扑控制面把最新 LinkAdvertisement 带给每个成员，接收方为每条有向边保留最新广告。`docs/device-net-routing-distribution.md:61`
4. 边过滤：只有两端是当前 Space 成员、广告未过期、本地源端点是活跃直连 Peer Link、且 channel epoch 与 sequence 合法，边才合格。`docs/device-net-routing-distribution.md:66`
5. 代价计算：边代价按 1000 + 10 * smoothedRttMs + 25 * lossPermille + 10 * congestionPermille 计算。`docs/device-net-routing-distribution.md:84`
6. 选路：路由器用 Dijkstra 算法在合格边构成的图上计算有向最短路径树，得到 `RouteDecision` 的下一跳。`docs/device-net-routing-distribution.md:96`
7. 平局处理：总代价相等时选择字典序最小的第一跳。`docs/device-net-routing-distribution.md:103`
8. 循环保护：`RoutedCoreRequest.ttl` 初始值为合格顶点数，每转发一跳减一。`docs/device-net-routing-distribution.md:108`
9. 分发分类：Watch 路由在生成的 Core 路由元数据中声明 `Unicast` 或 `SnapshotShared`，传输层不自行推断。`docs/device-net-routing-distribution.md:119`
10. 共享打开：第一个 `SnapshotShared` 消费者沿加权路由打开上游 Watch，条目以 (spaceId, targetNodeId, routeKind, target, propertyName, canonicalArguments, topologyGeneration) 为键登记。`docs/device-net-routing-distribution.md:141`
11. 快照分发：后进入的消费者先在其自己的逻辑订阅 id 上收到最新缓存快照，再收到后续 changed 事件。`docs/device-net-routing-distribution.md:162`
12. 事件复制：changed 事件按源顺序复制给每个活跃消费者，每个下游事件按该消费者的逻辑请求 id 重写。`docs/device-net-routing-distribution.md:199`
13. 慢消费者隔离：下游订阅者队列触及上限时以 `PEER_WATCH_CONSUMER_SLOW` 关闭该逻辑订阅，不拖慢源端或其他消费者。`docs/device-net-routing-distribution.md:169`
14. 结束：完成事件关闭全部消费者并移除条目，最后一个消费者取消时关闭上游 Watch 并移除条目。`docs/device-net-routing-distribution.md:164`
15. 持久同步：worker 先通过直连配对交换已认证的 Space 投影，再枚举经加权路由图可达的每个当前 Space 成员做向量时钟交换。`docs/device-net-routing-distribution.md:231`
16. 对端同步调用：PeerSyncMethod 的 `request` 用 `NODE_SYNC_TARGET` 与序列化后的方法名构建 `CoreCallRequest`。`core/crates/node/runtime/src/PeerSync.rs:44`
17. 对端同步校验：PeerSyncMethod 的 `fromRequest` 校验确切的对端方法与类型化操作信封，未知方法以 `PEER_SYNC_METHOD_DENIED` 失败。`core/crates/node/runtime/src/PeerSync.rs:56`
18. 对端同步推送：`PeerSyncPushMethod` 的 `fromRequest` 只接受 `syncReceiveBlob` 推送。`core/crates/node/runtime/src/PeerSync.rs:190`

## 来源

- `docs/device-net-routing-distribution.md`（241 行，设计文档：定义多设备 Space 的路由与实时数据分发算法、链路状态、加权选路、分发类、共享 Watch 树、控制面与数据面、模块职责划分、验证拓扑与持久同步扇出；正文的路由与分发规则均为该文档的定义，不是逐行代码实现）
- `core/crates/node/runtime/src/PeerSync.rs`（196 行，对端同步的类型化调用面：`PeerSyncMethod` 与 `PeerSyncPushMethod`、存储提供者判定、请求构建与校验、测试）
- 否定性结论核验方法：本页对 `SharedWatchHub`、`RouteDecision`、`LinkAdvertisement` 的表述均限定为设计文档 `device-net-routing-distribution.md` 内的定义，不写成已实现的 Rust 符号。核验命令为 `grep -rn 'SharedWatchHub\|RouteDecision\|LinkAdvertisement' --include='*.rs' ~/workspace/Operit2`（2026-11-11，对基线 364d1d594）：`SharedWatchHub` 与 `RouteDecision` 在 Rust 源码中零命中；`LinkAdvertisement` 的 20 处命中全部是 `CoreSpaceLinkAdvertisement` 结构体、`publishLocalLinkAdvertisement` 与 `validateLinkAdvertisement` 函数名中的子串，没有名为 `LinkAdvertisement` 的独立 Rust 类型；另仅 `core/crates/persistence/store/src/CoreSpaceStore.rs:1001` 的注释提及 Dijkstra。
