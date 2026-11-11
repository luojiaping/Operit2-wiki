---
title: 同步总览：Space 持久化同步
module: sync
platforms: [all]
sources: [2]
date: 2026-11-11
---

## 概述

- 同一 Space 内具备 `storage.provide` 且提供 Core 存储服务的节点交换持久化操作与 Blob。`docs/sync-architecture.md:3`
- 配对、成员资格、路由可达性和存储授权分别校验，配对见 [[sync-discovery-join|局域网发现、配对与加入 Space]]。`docs/sync-architecture.md:3`
- `SpacePersistenceSyncService` 通过 Router 与可达的 Space 成员同步持久化数据，不拥有配对、发现或传输。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:152`
- 本地业务变更经数据集原子提交、持久 outbox 进入操作日志。`docs/sync-architecture.md:8`
- 操作日志经 `Router` / `PeerSync` 到达对端。`docs/sync-architecture.md:10`
- 对端按原始操作与接收凭据经数据集解码与重放计划、原子提交后通知。`docs/sync-architecture.md:12`
- `SpacePersistenceSyncService` 管授权、交换、分页、Blob 与调度。`docs/sync-architecture.md:17`
- `SyncOperationStore` 管原始操作、身份指纹、接收凭据与日志查询。`docs/sync-architecture.md:18`
- `PreferenceMerge` 管偏好 owner 声明与物化协调。`docs/sync-architecture.md:19`
- `PreferencesDataStore` 管单数据集工作副本与原子提交。`docs/sync-architecture.md:20`
- 各业务 owner 管历史编码转换、业务验证与提交后运行时更新。`docs/sync-architecture.md:21`
- `SYNC_DOMAINS` 含 preferences、chat、binding、runtime_file、network_control、plugin_storage 六个域。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:28`
- 同步协议版本为 5，两端在交换前确认支持初始化事务。`docs/sync-architecture.md:131`
- 所有同步设备需一起更新到 `consistencyVersion: 7`，旧协议不能完成同步。`docs/sync-architecture.md:86`

## AI 速览

- `SpacePersistenceSyncService` — 通过 Router 与可达 Space 成员同步持久化数据的服务，不拥有配对、发现或传输。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:152`
- `SYNC_DOMAINS` — 六个同步域：preferences、chat、binding、runtime_file、network_control、plugin_storage。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:28`
- `SyncOperationStore` — 原始操作、身份指纹、接收凭据与日志查询。`docs/sync-architecture.md:18`
- `PreferenceMerge` — 偏好 owner 声明与物化协调。`docs/sync-architecture.md:19`
- `PreferencesDataStore` — 单数据集工作副本与原子提交。`docs/sync-architecture.md:20`
- `PeerSyncStatus` — 含 `local`、`remote`、`pending` 与 `progress` 四个字段。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:62`
- `storageReplicationAllowed` — 在 `requirePeerStorageProviders` 通过时返回 true，遇 `SPACE_STORAGE_PERMISSION_DENIED` 时返回 false。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:675`
- peerPassRequired — 退避未到期时不跑整轮同步，判定点为 `backoffElapsed`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:716`
- exchangePairedDeviceSpaceProjection — 远端快照交给 `observePeerSpaceSnapshot` 观察。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1123`
- `validateReachableDeviceSpace` — 业务复制前校验可达设备属于同一 Space。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:658`
- transferBlob — 按 `SYNC_BLOB_CHUNK_BYTES` 分块传输 Blob。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1270`
- `scheduleSynchronization` — 调度原因合并进 `synchronizationReasons` 集合。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1298`
- synchronizeDomains — 每轮先交换两端时钟，调用 `validateDomainClock` 校验域时钟并调用 `requireConsistencySupport` 校验一致性支持。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:905`
- `mergeSyncOperations` — 把两端操作按 `Transaction` 的 `ordered` 排成确定顺序。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1597`
- `syncPageChunks` — 按连接上限切分操作页。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1063`
- `blobPresence` — 每端一次分发批量查询存在性，逐项保留错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1241`
- 主入口函数：SpacePersistenceSyncService 的 `start`，先调用 `nodeServices` 与 spaceStore 的 `initialize`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:201`
- 数据流向一句话：本地业务变更经数据集原子提交、持久 outbox 进入操作日志。`docs/sync-architecture.md:8`
- 数据流向一句话（对端）：对端按原始操作与接收凭据经数据集解码与重放计划、原子提交后通知。`docs/sync-architecture.md:12`

## 核心机制

- 配对、成员资格、路由可达性和存储授权分别校验。`docs/sync-architecture.md:3`
- 同一对已授权存储节点仅由 CoreNode ID 字典序较小的一端协调完整双向交换。`docs/sync-architecture.md:92`
- 另一端通过已鉴权的 `syncRequest` 唤醒并等待协调端，排队请求取得设备对互斥锁后重新检查变更，显式请求仍可强制执行。`docs/sync-architecture.md:92`
- 等待端仅在长同步期间查询并镜像协调端的真实进度，结束响应携带最终进度。`docs/sync-architecture.md:92`
- 业务复制放行且本地 CoreNode ID 大于目标时，本端发 `SyncRequest` 唤醒协调端并等待。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:576`
- 等待端在长同步期间调用 `SyncProgress` 查询并 `mirror` 协调端的真实进度。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:590`
- 准入不是存储授权，业务复制要求两端都提供存储。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:656`
- `storageReplicationAllowed` 在 `requirePeerStorageProviders` 通过时返回 true，遇 `SPACE_STORAGE_PERMISSION_DENIED` 时返回 false。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:675`
- 未获存储授权时 `storageReplicationAllowed` 返回 false，不做业务复制。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:657`
- 授权更新仍到达非存储成员，不推进业务复制时钟。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:604`
- 业务复制前调用 `validateReachableDeviceSpace` 校验可达设备属于同一 Space。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:658`
- 远端 Space 的 `members` 含目标节点时才通过可达设备校验。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1167`
- 远端 Space 的 `members` 含本节点时才通过可达设备校验。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1177`
- 两端 `spaceId` 不同时返回空间不匹配错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1184`
- 以两端 `spaceId` 是否相同作为业务同步是否放行的返回值。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1150`
- 投影协议协商只针对 `activePeerNodeIds` 中且 `hasPairing` 的直连对端，否则返回 None。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1510`
- 中继路由上的普通控制与业务同步不依赖投影协议协商。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1508`
- `synchronizePeer` 先调用 `nodeIsReachable` 校验目标节点，不可达时返回 `CORE_NODE_UNREACHABLE` 错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:564`
- 对 Space 成员调用 `nodeIsReachable` 校验，不可达的目标被移除进度并跳过。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:455`
- 配对对端不在 `membershipBeforeExchange` 内时，投影交换就是其整轮同步，不做业务复制。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:442`
- `outboundPeerNodeIds` 列出的对端中，只有活跃且未被连接策略断开的节点才交换配对 Space 投影。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:421`
- 本地业务变更经数据集原子提交、持久 outbox 进入操作日志。`docs/sync-architecture.md:8`
- 操作日志经 `Router` / `PeerSync` 到达对端。`docs/sync-architecture.md:10`
- 对端按原始操作与接收凭据经数据集解码与重放计划、原子提交后通知。`docs/sync-architecture.md:12`
- 偏好业务值和内部 `__operit_preferences_replication` 字段经 Host 原子写入一起提交。`docs/sync-architecture.md:50`
- 内部字段保存初始值导入标记、来源 epoch/序号、逻辑时间、已应用指纹及待归档 outbox，对外业务序列化不暴露它。`docs/sync-architecture.md:50`
- 业务提交后归档原始操作，归档可靠完成后清除 outbox。`docs/sync-architecture.md:52`
- 归档失败保留同一操作供后续发布，业务提交失败不能产生可导出的操作。`docs/sync-architecture.md:52`
- `runtime/sync/preference_outboxes.json` 只登记位置与加密策略，登记记录不代表业务提交成功。`docs/sync-architecture.md:52`
- 数据集锁覆盖历史收集、归档与 outbox 合并、解码、重放和提交。`docs/sync-architecture.md:54`
- SQL 数据集使用其现有事务，具体同步应用记录与业务状态必须遵守该 owner 的提交边界。`docs/sync-architecture.md:54`
- 一次接收与一次业务应用是不同事实，操作可靠保存后才能推进接收凭据。`docs/sync-architecture.md:23`
- 业务提交完成后才能标记已应用。`docs/sync-architecture.md:23`
- 相同操作身份必须携带相同内容，重复投递幂等，内容冲突明确报错。`docs/sync-architecture.md:23`
- 每个偏好文件是独立数据集，一个数据集失败不能阻止独立数据集提交。`docs/sync-architecture.md:25`
- 普通稳定引用不组成跨文件事务，跨文件业务操作不具备单次原子性。`docs/sync-architecture.md:25`
- 本地存储 schema、逻辑操作契约版本和因果/来源顺序分别表达，互不替代。`docs/sync-architecture.md:31`
- 本地 schema 升级只转换存储表示，不能据此丢弃历史操作或生成覆盖全部业务历史的快照。`docs/sync-architecture.md:31`
- 已发布编码由对应 owner 显式解释，普通字符串保持原类型。`docs/sync-architecture.md:31`
- 偏好操作包含完整赋值、完整删除、整数增量和字段修改。`docs/sync-architecture.md:33`
- 完整赋值或删除重置同一根条目此前的效果。`docs/sync-architecture.md:35`
- 随后的字段修改和整数增量继续生效，并满足实际依赖。`docs/sync-architecture.md:36`
- 同一原始事务中的其他根条目独立计算，仍在同一次数据集提交中发布。`docs/sync-architecture.md:37`
- 原始操作身份、内容和归档记录完整保留，计算计划不改写历史。`docs/sync-architecture.md:38`
- 有效操作依赖缺失时，整个数据集工作副本不提交。`docs/sync-architecture.md:40`
- 实体身份合并只执行已明确记录的决定。`docs/sync-architecture.md:42`
- 引用投影使用目标数据集已经提交的身份决定，传输分页或分块结束不能授予业务合并许可。`docs/sync-architecture.md:42`
- 偏好布局由节点本地的 `PreferenceLayout` 管理，直接复用 DataStore 的 `withSchema` 执行逐版本迁移。`docs/sync-architecture.md:44`
- 单文件 schema 管理文件内表示，布局 schema 管理文件的创建、设置所有权转移和旧路径退役。`docs/sync-architecture.md:44`
- 跨文件迁移不宣称具有跨文件原子性，失败时布局版本不推进，同步保留原待处理操作。`docs/sync-architecture.md:44`
- 布局状态只属于本节点，不参与 Space 同步，也不能由远端版本推进。`docs/sync-architecture.md:46`
- 退役意味着旧来源不再拥有设置写入权，其迟到操作仅在原文归档成功后完成接收，不重建旧文件或覆盖当前实体。`docs/sync-architecture.md:46`
- 首次打开 SQL 事务账本时导入旧 JSONL 和接收索引。`docs/sync-architecture.md:27`
- 旧账本导入失败时原子清空该事务账本并标记旧格式已处理，业务文件和业务 SQL 保留。`docs/sync-architecture.md:27`
- 各 owner 复用现有初始化流程从当前业务数据重建基线。`docs/sync-architecture.md:27`
- 导入保留作者序号下界，避免复用其他节点已持有的事务身份。`docs/sync-architecture.md:27`
- 重启不再导入该旧账本，重置本身无法提交时仍返回错误。`docs/sync-architecture.md:27`
- 整段会话删除使用保留的 SQL 事务操作，历史行删除、删除事实与接收凭据在同一事务提交。`docs/sync-architecture.md:56`
- 删除事实沿用 `sync_sql_deletions`，不依赖 Space 成员或 Binding。`docs/sync-architecture.md:57`
- 对同一会话 ID，删除是终态而非可被后续 upsert 撤销的普通字段，迟到写入仍保留原始操作并推进接收凭据，但不重建会话或子记录。`docs/sync-architecture.md:58`
- 同步提交后通过 Host 调度器停止该会话的本地执行并清理界面，不另建删除 RPC。`docs/sync-architecture.md:60`
- 数据库 28 → 29 为删除事实建立查询索引，并在同一升级事务内清除旧链路已删除却又被恢复的会话行。`docs/sync-architecture.md:61`
- 启动恢复当前会话时，仅在选中的 ID 不存在时按该 ID 查询删除事实，确认已删除才清空持久化选择。`docs/sync-architecture.md:63`
- 生产日志位于 `transactions.sqlite`，聊天和插件 SQL 通过同一 source 接口导出各自的业务日志。`docs/sync-architecture.md:68`
- SQL 元数据索引先规划页面，再读取选中的载荷，旧 JSONL 与接收文件仅由兼容导入器读取。`docs/sync-architecture.md:68`
- 收据、domain、数据集和水位先筛选，调用者过滤先于实体状态压缩，偏好历史与事务不进行实体状态压缩。`docs/sync-architecture.md:70`
- 需要检查 payload 的记录逐条解码，页面按精确序列化字节数与记录数限制，单条超限记录由传输层处理。`docs/sync-architecture.md:70`
- 归档和待应用记录在同一查询规划器内去重、排序与分页，应用层不能在分页之后追加完整待应用队列。`docs/sync-architecture.md:72`
- 全局注册表持有弱引用，最后一个 Store owner 释放后，共享索引、账本和 Host 可以释放。`docs/sync-architecture.md:72`
- 锁顺序为接收账本在前、按设备顺序的日志锁在后。`docs/sync-architecture.md:72`
- `receive_state.json` 的 `formatVersion: 2` 保存收据、指纹与轻量元数据，payload 位于 `pending/<sha256(opId)>.json`。`docs/sync-architecture.md:78`
- 加密偏好继续按其加密编码持久化。`docs/sync-architecture.md:78`
- 接收时先原子发布记录文件，再提交引用与收据账本。`docs/sync-architecture.md:80`
- 应用完成时先提交移除引用的账本，再删除记录文件，加载时清理私有目录中未被引用的文件。`docs/sync-architecture.md:80`
- 旧内嵌格式逐条迁出并保留原始编码，所有记录文件落盘后才原子替换账本，升级中断时原账本和原始操作仍是重试依据。`docs/sync-architecture.md:82`
- SQL 完整快照仍携带所有表列和原始覆盖凭据，用于条件导出、修复与提交校验。`docs/sync-architecture.md:86`
- 一致性清单只使用 `digest` 判断内容是否相同，由数据所属模块排除本地辅助信息后计算，不设置旧摘要回退或兼容字段。`docs/sync-architecture.md:86`
- 聊天 owner 比较时排除 SQLite 本地分配的 `messages.messageId` 和 `message_variants.variantId`，按去掉本地列后的内容重新排序。`docs/sync-architecture.md:88`
- 消息正文、业务标识、消息部件、版本事实等仍参与比较。`docs/sync-architecture.md:88`
- 插件 owner 排除对象存储的本地 CAS `version`，身份映射忽略记录映射的来源及“自身到自身”的无效映射，相同有效映射去重，真正的别名决定和业务值仍参与比较。`docs/sync-architecture.md:88`
- 完整快照 token 不做这些投影，因此本地行号或 CAS token 改变仍会阻止使用过期快照覆盖。`docs/sync-architecture.md:88`
- 轻量探测和完整收据使用同一个本地创作时钟、投影计数及设备偏好修订摘要。`docs/sync-architecture.md:94`
- 完成基线只记录本轮空导出且内容校验通过的收据边界，不采纳轮前探测或轮后重新读取的状态，边界之后的写入仍会触发下一轮。`docs/sync-architecture.md:94`
- 待处理和失败重试不受去重影响。`docs/sync-architecture.md:94`
- Blob 引用按内容哈希和大小去重，每页每端一次批量存在性调用，逐项保留错误。`docs/sync-architecture.md:96`
- 传输前后仍检查存储授权，落盘后仍验证完整哈希。`docs/sync-architecture.md:96`
- 时钟日志仅输出来源数和摘要，页面日志仅汇总域、实体数量和时间范围，不重复格式化整个收据及操作身份列表。`docs/sync-architecture.md:96`
- Blob 引用按 `contentHash` 与 `size` 去重。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1217`
- 对两端各调用一次 `blobPresence` 做批量存在性查询。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1222`
- `blobPresence` 每端一次分发批量查询存在性，逐项保留错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1241`
- Blob 存在性响应长度与引用数不符时返回错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1246`
- 两端都没有的 Blob 返回含 `contentHash` 的缺失错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1232`
- 从操作中调用 `requiredBlob` 提取所需 Blob 引用。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1202`
- 按 `SYNC_BLOB_CHUNK_BYTES` 分块传输 Blob。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1270`
- 每块读写前后都重新调用 `requirePeerStorageProviders` 检查存储授权。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1276`
- 落盘后调用 `blobPresence` 验证 Blob 已持久化，未持久化时报错。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1284`
- 块为空时返回 `synchronization blob {} ended before its declared size` 错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1436`
- 块超出声明大小时返回 `synchronization blob {} exceeded its declared size` 错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1447`
- `sync_cycle.start triggers=...` 记录本轮合并的唤醒来源，包括服务启动、同步数据变更、连接变化、加入 Space、工作区扫描和上一轮运行期间的新变更。`docs/sync-architecture.md:102`
- 周期开始不表示执行了全量快照传输。`docs/sync-architecture.md:102`
- `sync_gate.required reasons=...` 记录进入对端同步流程的条件，包括首次建立基线、本地状态变化、远端时钟变化、待处理工作、失败重试或仅交换授权。`docs/sync-architecture.md:103`
- `sync_pass.start/done/failed` 记录目标节点、调用来源、排队与执行耗时、待处理状态及失败后的重试时间。`docs/sync-architecture.md:104`
- 路由切换的来源包含 `route_change` 和会话 ID。`docs/sync-architecture.md:104`
- `sync_consistency.correct mode=full_snapshot` 决定进行完整文件快照修复，INFO 级别记录 `reason=content_digest_mismatch/local_file_missing/remote_file_missing`、文件路径、两端内容摘要和逻辑版本、选定的数据来源。`docs/sync-architecture.md:105`
- 定位重复全量时先搜索 `mode=full_snapshot`，再按目标节点和时间对照 gate 与周期来源。`docs/sync-architecture.md:108`
- 关键快照决策及结果使用 INFO，空闲轮询来源保留在 V5 周期日志中。`docs/sync-architecture.md:108`
- 一轮同步记录 `sync_pass.start` 日志，含目标节点、触发原因、limit 与排队耗时。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:513`
- 一轮同步成功时记录 `sync_pass.done`，含业务复制是否放行、待处理状态与耗时。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:538`
- 一轮同步失败时记录 `sync_pass.failed`，含重试时间与错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:551`
- 同步任务开始时记录 `sync_cycle.start`，含本地节点、修订号与合并后的触发原因。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1329`
- 慢同步调用超过 250 毫秒时记 `sync_call.slow` 跟踪日志。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1552`
- 注册表明确声明消费域，偏好准备只处理偏好事务，不能将其他域误标为 skip。`docs/sync-architecture.md:119`
- 普通文件的完整 upsert/delete 可以直接重试历史 skip，按已有业务顺序只物化同文件的最终胜者，缺 Blob、权限或写入失败仍保留重试，成功后才完成对应原文。`docs/sync-architecture.md:119`
- 确定的能力／数据失败记录日志并封存为 skip，在本次任务的最终检查中强制复制完整快照。`docs/sync-architecture.md:121`
- 导出或应用曾失败时，即使当前内容相同也重建初始化基线。`docs/sync-architecture.md:121`
- SQL 结构异常、损坏初始化和无效偏好文件仍生成带损坏证据的版本凭据，受损端只作为覆盖目标。`docs/sync-architecture.md:121`
- 只有结构化通信错误启动退避重试，无法取得完整来源或无法落盘时明确失败，等待数据变化或显式请求，不能循环重试同一数据错误。`docs/sync-architecture.md:121`
- 矫正携带双方当次捕获的 skip ID，与文件覆盖范围一起写入初始化事务，然后清理对应旧原文。`docs/sync-architecture.md:123`
- 内容已经相同但仍有 skip 时也完成封存，导出后新到的事务保留到下一轮。`docs/sync-architecture.md:123`
- 未声明同步归属的文件记录 INFO 并退出同步，原文件保留，已知旧路径通过 layout 退休。`docs/sync-architecture.md:123`
- 缺 Blob 的 pending 与权限检查继续生效，并发写入在本次任务内重新交换，双方需支持一致性协议 7。`docs/sync-architecture.md:123`
- 退避未到期时不跑整轮同步，判定点为 `backoffElapsed`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:716`
- 有待处理工作时要求跑整轮同步，判定点为 `pendingWork`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:718`
- 上轮失败且退避已到期时要求重试，原因记为 `failure_retry`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:723`
- 非存储成员直接要求跑整轮同步，只交换授权，原因记为 `authority_only`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:731`
- 其余情况下调用 `probeRemoteClockSummary` 探测远端时钟摘要决定是否跑整轮同步。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:734`
- `probeRemoteClockSummary` 调用 `SyncClockDigest` 并取其中非空的 `digest` 字段。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:778`
- `recordPeerPassCompleted` 在完成时清零 `consecutiveFailures` 与 `failedState`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:793`
- 非业务复制的完成不保留本地与远端时钟基线，判定点为 `lastLocalStateSummary` 与 `lastRemoteClockSummary`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:792`
- 传输类失败调用 `recordPeerPassFailed` 计入重试退避。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:827`
- 确定性失败把失败时的本地与远端状态记入 `failedState`，`consecutiveFailures` 清零。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:832`
- `peerFullSyncBackoffMs` 按连续失败次数指数退避，倍增上限为 5 次。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:107`
- 退避延迟取基数乘以 2 的倍增次方与上限 60_000 毫秒中的较小值。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:109`
- 传输失败分类只认 `CORE_NODE_UNREACHABLE` 等传输错误码，应用错误不记为网络失败。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:131`
- `backoffElapsed` 在 `consecutiveFailures` 为 0 时返回 true。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:97`
- 本地 CoreNode ID 不小于目标时拒绝同步请求，错误为 `Synchronization request targets the wrong coordinator`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:802`
- 被唤醒的同步请求返回的 `PeerSyncStatus` 含本地与远端时钟摘要、待处理标志与进度。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:810`
- Preference 同步先按身份并集、定位并迁移到共同表示，再用公共 Transaction 的 `compaction` 选择有效事务，最后重放。`docs/sync-architecture.md:127`
- 合并结果中的删除 ID 随文件提交意图持久化，SQL 提交只执行这份清单，保留身份指纹和收据。`docs/sync-architecture.md:127`
- 本地编辑复用相同合并函数，只查询当前格式的普通历史，不读取初始化载荷。`docs/sync-architecture.md:127`
- 聊天和插件 SQL 继续在同库提交内维护范围索引。`docs/sync-architecture.md:127`
- 普通合并要求独立赋值及上下文无关的迁移，原子事务仍有部分效果有效时整笔保留，声明、增量、层级范围和业务 merge rule 保留原文。`docs/sync-architecture.md:127`
- 强制矫正时两端保存同一条完整初始化事务，删除该 owner 已封存的旧日志。`docs/sync-architecture.md:129`
- 初始化保留业务修订、范围版本、删除事实、别名和精确覆盖身份，接替旧独立基线。`docs/sync-architecture.md:129`
- 离线节点安装初始化后重放其未覆盖修改，空节点直接恢复完整文件。`docs/sync-architecture.md:129`
- 初始化事务参加正常分页、收据和转发，较大的内容使用现有校验 Blob 传输。`docs/sync-architecture.md:131`
- 收据、覆盖判断和导出规划只查询 SQL 元数据，普通写入不解析初始化快照。`docs/sync-architecture.md:131`
- `mergeSyncOperations` 把两端操作按 `Transaction` 的 `ordered` 排成确定顺序。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1597`
- 用 `mergeSyncOperations` 合并两端操作页。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:978`
- `new` 以 localRuntime、nodeRouter 与 spaceStore 创建一个持久化服务。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:160`
- 同节点已有服务状态在与新 localRuntime 共享应用时被复用，判定点为 `sharesApplicationWith`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:169`
- `start` 先调用 `nodeServices` 与 spaceStore 的 `initialize`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:201`
- `active` 已为 true 时直接返回。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:211`
- 同步变更订阅回调以 `sync_mutation` 为原因调度同步。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:221`
- 启动时同时启动工作区扫描器与对端变化监听器，任一启动失败只记警告。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:236`
- 启动完成时以 `service_start` 为原因调度一次同步。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:252`
- `stop` 把 `active` 置为 false 并停止工作区扫描。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:268`
- 停止时取走 `mutationSubscription`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:277`
- 停止时调用 `progress` 的 `clear` 清空进度。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:281`
- 工作区扫描器使用 Host 调度器，desktop、mobile 与 Web 共享同一生命周期与停止机制。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:286`
- 工作区扫描有变更时回到 `WORKSPACE_SCAN_ACTIVE_INTERVAL_MS` 快轮询，无变更时翻倍直至 `WORKSPACE_SCAN_IDLE_INTERVAL_MS` 空闲上限。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:312`
- 工作区扫描失败时不发布缺失文件删除，扫描见 [[sync-workspace-files|工作区文件同步与 .operit/sync.json]]。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:307`
- 对端变化监听器只消费 runtime 的连接变化，不订阅发现端点，不读取或修改配对记录。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:329`
- 对端连接变化时以 `peer_connection_changed` 为原因调度同步。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:350`
- 调度原因合并进 `synchronizationReasons` 集合。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1298`
- 已有待执行任务时直接返回，不重复排队，判定点为 `synchronizationScheduled`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1302`
- 同步任务走 Host 阻塞异步任务 `core-node-space-persistence-sync`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1309`
- 同步任务结束时若仍有新变更请求或修订号变化，以 `changes_during_pass` 为原因重新调度。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1368`
- 每轮先交换两端时钟，调用 `validateDomainClock` 校验域时钟并调用 `requireConsistencySupport` 校验一致性支持。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:905`
- `validateDomainClock` 要求收据的 `protocolVersion` 为 1，否则返回协议不匹配错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1466`
- `validateDomainClock` 把时钟解析为 `SyncReceipt` 并调用其 `validate`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1468`
- `clockStateSummary` 取收据的非空 `stateSummary` 作为状态摘要，缺失时报错。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1478`
- `localStateSummary` 先调用 `publishPreferenceOutboxes` 发布偏好 outbox，再取同步摘要。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:688`
- 交换操作前先调用 `synchronizeBlobReferences` 同步两端待处理 Blob 引用。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:937`
- 用 `SyncOperationsSince` 按时钟取两端操作。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:956`
- 操作页为空时仍以空批量调用 `applySynchronizedOperationBatch`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:984`
- 一致性未完成且无延期 owner 时继续下一页，直至 `MAX_SYNC_PAGES_PER_PASS` 上限。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:989`
- 达到 `MAX_SYNC_PAGES_PER_PASS` 上限时记录剩余页待处理并结束本轮。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1004`
- 应用批量前先调用 `synchronizeRequiredBlobs` 同步本批操作所需的 Blob。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1057`
- 用 `syncPageChunks` 按连接上限切分操作页。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1063`
- 切分时操作保持完整，事务不被切分。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1635`
- 单条操作超过上限时返回 `SYNC_OPERATION_TOO_LARGE` 错误而不是发送。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1657`
- 同一分块同时发给远端与本地的 `SyncApplyOperations` 应用。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1066`
- 应用报告中的 `pendingOwners` 被记为延期 owner。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1076`
- 支持快照分页时按 `snapshotHeader` 与 `snapshotControlPage` 分页拉取控制快照。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1105`
- 远端快照交给 `observePeerSpaceSnapshot` 观察。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1123`
- 引用条件满足时只回发 `observeSpaceProjection` 观察，否则回发完整 `observeSpaceSnapshot`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1136`
- `callLocal` 通过本进程 Core 调用 `application` 目标的方法。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1392`
- `callRemote` 通过 Router 向目标节点发 PeerSync 方法请求。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1483`

## 关键符号

- `SpacePersistenceSyncService` — 通过 Router 与可达的 Space 成员同步持久化数据，不拥有配对、发现或传输。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:152`
- SpacePersistenceSyncService 的 `new` — 以 localRuntime、nodeRouter 与 spaceStore 创建一个持久化服务。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:160`
- SpacePersistenceSyncService 的 `start` — 先调用 `nodeServices` 与 spaceStore 的 `initialize`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:201`
- SpacePersistenceSyncService 的 `stop` — 把 `active` 置为 false 并停止工作区扫描。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:268`
- SpacePersistenceSyncService 的 `synchronizeOnce` — 先初始化 spaceStore 并保留当前 Space 的成员进度。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:363`
- SpacePersistenceSyncService 的 synchronizeReachablePeerForReason — 同一对端的 `execution` 互斥锁把一轮同步串行化。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:505`
- SpacePersistenceSyncService 的 `synchronizePeer` — 先调用 `nodeIsReachable` 校验目标节点，不可达时返回 `CORE_NODE_UNREACHABLE` 错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:564`
- SpacePersistenceSyncService 的 `storageReplicationAllowed` — 在 `requirePeerStorageProviders` 通过时返回 true，遇 `SPACE_STORAGE_PERMISSION_DENIED` 时返回 false。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:675`
- SpacePersistenceSyncService 的 `localStateSummary` — 先调用 `publishPreferenceOutboxes` 发布偏好 outbox，再取同步摘要。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:688`
- SpacePersistenceSyncService 的 peerPassRequired — 退避未到期时不跑整轮同步，判定点为 `backoffElapsed`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:716`
- SpacePersistenceSyncService 的 `probeRemoteClockSummary` — 调用 `SyncClockDigest` 并取其中非空的 `digest` 字段。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:778`
- SpacePersistenceSyncService 的 `recordPeerPassCompleted` — 在完成时清零 `consecutiveFailures` 与 `failedState`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:793`
- SpacePersistenceSyncService 的 `synchronizeRequestedPeer` — 本地 CoreNode ID 不小于目标时拒绝同步请求，错误为 `Synchronization request targets the wrong coordinator`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:802`
- SpacePersistenceSyncService 的 synchronizeDomains — 每轮先交换两端时钟，调用 `validateDomainClock` 校验域时钟并调用 `requireConsistencySupport` 校验一致性支持。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:905`
- SpacePersistenceSyncService 的 applySynchronizedOperationBatch — 应用批量前先调用 `synchronizeRequiredBlobs` 同步本批操作所需的 Blob。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1057`
- SpacePersistenceSyncService 的 exchangePairedDeviceSpaceProjection — 远端快照交给 `observePeerSpaceSnapshot` 观察。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1123`
- SpacePersistenceSyncService 的 `validateReachableDeviceSpace` — 业务复制前校验可达设备属于同一 Space。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:658`
- SpacePersistenceSyncService 的 `synchronizeBlobReferences` — 交换操作前先调用它同步两端待处理 Blob 引用。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:937`
- SpacePersistenceSyncService 的 `blobPresence` — 每端一次分发批量查询存在性，逐项保留错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1241`
- SpacePersistenceSyncService 的 transferBlob — 按 `SYNC_BLOB_CHUNK_BYTES` 分块传输 Blob。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1270`
- SpacePersistenceSyncService 的 `scheduleSynchronization` — 调度原因合并进 `synchronizationReasons` 集合。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1298`
- `projectionProtocol` — 投影协议协商只针对 `activePeerNodeIds` 中且 `hasPairing` 的直连对端，否则返回 None。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1510`
- `mergeSyncOperations` — 把两端操作按 `Transaction` 的 `ordered` 排成确定顺序。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1597`
- `syncPageChunks` — 按连接上限切分操作页。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1063`
- `validateDomainClock` — 要求收据的 `protocolVersion` 为 1，否则返回协议不匹配错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1466`
- `clockStateSummary` — 取收据的非空 `stateSummary` 作为状态摘要，缺失时报错。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1478`
- `callLocal` — 通过本进程 Core 调用 `application` 目标的方法。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1392`
- `callRemote` — 通过 Router 向目标节点发 PeerSync 方法请求。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1483`
- `peerFullSyncBackoffMs` — 按连续失败次数指数退避，倍增上限为 5 次。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:107`
- `backoffElapsed` — 在 `consecutiveFailures` 为 0 时返回 true。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:97`
- `recordPeerPassFailed` — 传输类失败调用它计入重试退避。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:827`
- sendBlobChunk — 块为空时返回 `synchronization blob {} ended before its declared size` 错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1436`
- `PeerSyncStatus` — 含 `local`、`remote`、`pending` 与 `progress` 四个字段。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:62`
- `SYNC_DOMAINS` — 含 preferences、chat、binding、runtime_file、network_control、plugin_storage 六个域。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:28`
- `SYNC_BLOB_CHUNK_BYTES` — 为 64 * 1024。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:33`
- `SYNC_PAGE_ENVELOPE_BYTES` — 为 4 * 1024。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:36`
- `SYNC_PAGE_HEADROOM_BYTES` — 为 64 * 1024。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:39`
- `MAX_SYNC_PAGES_PER_PASS` — 为 64。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:42`
- `PEER_FULL_SYNC_BACKOFF_BASE_MS` — 为 2_000 毫秒。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:44`
- `PEER_FULL_SYNC_BACKOFF_MAX_MS` — 为 60_000 毫秒。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:46`
- `WORKSPACE_SCAN_ACTIVE_INTERVAL_MS` — 为 2_000 毫秒。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:50`
- `WORKSPACE_SCAN_IDLE_INTERVAL_MS` — 为 60_000 毫秒。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:54`
- `SyncOperationStore` — 原始操作、身份指纹、接收凭据与日志查询。`docs/sync-architecture.md:18`
- `PreferenceMerge` — 偏好 owner 声明与物化协调。`docs/sync-architecture.md:19`
- `PreferencesDataStore` — 单数据集工作副本与原子提交。`docs/sync-architecture.md:20`

## 调用链

1. `start` 先调用 `nodeServices` 与 spaceStore 的 `initialize`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:201`
2. 启动完成时以 `service_start` 为原因调度一次同步。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:252`
3. 调度原因合并进 `synchronizationReasons` 集合。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1298`
4. 已有待执行任务时直接返回，不重复排队，判定点为 `synchronizationScheduled`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1302`
5. 同步任务走 Host 阻塞异步任务 `core-node-space-persistence-sync`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1309`
6. 同步任务开始时记录 `sync_cycle.start`，含本地节点、修订号与合并后的触发原因。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1329`
7. `synchronizeOnce` 先初始化 spaceStore 并保留当前 Space 的成员进度。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:363`
8. 交换前调用 `retireRemovedDevice` 检查被移除设备并令其自行退役，重复投递同一命令是空操作。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:371`
9. 一轮同步先调用 `workspaceFiles` 的 `scan` 扫描工作区文件。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:379`
10. 随后调用 `activePeerNodeIds` 取活跃对端节点 ID。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:383`
11. `publishLocalTopology` 在快照交换前发布本设备实时直连邻接拓扑，通告不带实测质量，路由选择仍按跳数。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:389`
12. 拓扑发布失败时记录警告日志，日志文本含 `Local Space topology publish failed; multi-hop routing may degrade`。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:407`
13. 随后调用 `space_departure` 的 `synchronize` 交付 Space 离开信息。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:415`
14. `outboundPeerNodeIds` 列出的对端中，只有活跃且未被连接策略断开的节点才交换配对 Space 投影。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:421`
15. 配对对端不在 `membershipBeforeExchange` 内时，投影交换就是其整轮同步，不做业务复制。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:442`
16. 对 Space 成员调用 `nodeIsReachable` 校验，不可达的目标被移除进度并跳过。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:455`
17. 可达成员以 512 为 limit、`change_gate` 为原因执行同步。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:467`
18. 可达对端同步在 limit 为 0 时返回 `sync limit must be greater than 0` 错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:501`
19. 目标节点等于 `localNodeId` 时直接返回成功。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:502`
20. 同一对端的 `execution` 互斥锁把一轮同步串行化。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:505`
21. 取锁后对 `change_gate` / `peer_request` 触发重查 `peerPassRequired`，不通过直接返回。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:507`
22. 一轮同步记录 `sync_pass.start` 日志，含目标节点、触发原因、limit 与排队耗时。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:513`
23. `synchronizePeer` 先调用 `nodeIsReachable` 校验目标节点，不可达时返回 `CORE_NODE_UNREACHABLE` 错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:564`
24. 业务复制放行时先调用 `Protocol` 协商协议，再调用 `requireCompatible` 要求兼容。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:571`
25. 业务复制放行且本地 CoreNode ID 大于目标时，本端发 `SyncRequest` 唤醒协调端并等待。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:576`
26. 等待端在长同步期间调用 `SyncProgress` 查询并 `mirror` 协调端的真实进度。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:590`
27. 授权更新仍到达非存储成员，不推进业务复制时钟。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:604`
28. 偏好交换时每个成员都收到自己的配置，存储提供方之间还交换本设备的配置作备份。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:634`
29. 偏好响应作用域变化时返回 `Device preference response scope changed` 错误。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:652`
30. 未获存储授权时 `storageReplicationAllowed` 返回 false，不做业务复制。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:657`
31. 业务复制前调用 `validateReachableDeviceSpace` 校验可达设备属于同一 Space。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:658`
32. 每轮先交换两端时钟，调用 `validateDomainClock` 校验域时钟并调用 `requireConsistencySupport` 校验一致性支持。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:905`
33. 交换操作前先调用 `synchronizeBlobReferences` 同步两端待处理 Blob 引用。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:937`
34. 用 `SyncOperationsSince` 按时钟取两端操作。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:956`
35. 用 `mergeSyncOperations` 合并两端操作页。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:978`
36. 应用批量前先调用 `synchronizeRequiredBlobs` 同步本批操作所需的 Blob。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1057`
37. 用 `syncPageChunks` 按连接上限切分操作页。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1063`
38. 同一分块同时发给远端与本地的 `SyncApplyOperations` 应用。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1066`
39. 一致性未完成且无延期 owner 时继续下一页，直至 `MAX_SYNC_PAGES_PER_PASS` 上限。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:989`
40. 一轮同步结束时调用 `retain`，进度只保留当前成员。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:558`
41. 各对端错误汇总后以 ` | ` 连接返回。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:478`
42. 同步任务结束时若仍有新变更请求或修订号变化，以 `changes_during_pass` 为原因重新调度。`core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1368`

## 来源

- `docs/sync-architecture.md`
- `core/crates/node/runtime/src/SpacePersistenceSyncService.rs`
