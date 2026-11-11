---
title: 持久化——store 聚合 crate
module: core
platforms: [all]
sources: [core/crates/persistence/README.md, core/crates/persistence/store/src/lib.rs, core/crates/persistence/store/src/SqliteStore.rs, core/crates/persistence/store/src/CoreNodeIdentityStore.rs, core/crates/persistence/store/src/CoreNodeBindingStore.rs, core/crates/persistence/store/src/CoreSpaceStore.rs, core/crates/persistence/store/src/PreferencesDataStore.rs]
date: 2026-11-11
---

# 持久化——store 聚合 crate

## 概述

`store` 是当前聚合持久化 crate，包含 `database access`、`repositories`、`preferences`、`node identity stores`、`binding stores`、`space stores` 与 `sync stores`。`core/crates/persistence/README.md:9`

`Persistence` 域拥有 `durable state`、`repositories`、`identity data`、`bindings`、`space data` 与 `synchronization logs`。`core/crates/persistence/README.md:3`

`Persistence` 域不拥有 `realtime route selection`、`peer transport`、`business stream execution`、`provider execution` 与 `tool execution`。`core/crates/persistence/README.md:5`

`Target Split` 是目标布局计划：把聚合拆成 `core`、`preferences`、`chat`、`memory`、`workspace`、`node`、`sync` 七个 crate，不是已完成拆分。`core/crates/persistence/README.md:13`

本页只写存什么与入口；同步操作的执行与重放见 [[core-persistence-sync|持久化——同步存储]]。

## AI 速览

核心符号：

- `SqliteStore` — 共享 SQLite 连接包装器，连接由注册的 runtime host 提供。`core/crates/persistence/store/src/SqliteStore.rs:33`
- `SqliteTransaction` — 事务句柄，在事务内执行语句。`core/crates/persistence/store/src/SqliteStore.rs:202`
- `TransactionRollback` — 事务回滚也失败时同时携带 action 错误与 rollback 错误。`core/crates/persistence/store/src/SqliteStore.rs:184`
- `FromSqliteValue` — 把 host 的 SqliteValue 转成 Rust 强类型值。`core/crates/persistence/store/src/SqliteStore.rs:284`
- `ToSqliteValue` — 把 Rust 值转成 host 的 SqliteValue。`core/crates/persistence/store/src/SqliteStore.rs:337`
- `sqliteParams!` — 把值转成 SqliteValue 参数向量。`core/crates/persistence/store/src/SqliteStore.rs:407`
- `CoreNodeIdentity` — 只有一个字段 nodeId。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:18`
- `CoreNodeIdentityStore` — 节点身份存储，身份存在 RUNTIME_LINK_ACCESS_IDENTITY_PATH 的 CoreNodeStateStore，schema 版本为 2。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:130`
- `CoreNodeBindingRecord` — Binding 的持久化记录：key、nodeId、generation 三个字段。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:84`
- `CoreNodeBindingCommit` — 一次已提交的 Binding 变更：变更后的记录与持久化它的同步操作。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:92`
- `CoreNodeBindingStore` — Binding 记录由 RUNTIME_SYNC_DIR_PATH 上的 SyncOperationStore 持久化。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:113`
- `BINDING_SYNC_DOMAIN` — Binding 记录的同步域，值为 binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:17`
- `CoreSpace` — Space 的持久化记录：spaceId、spaceName、spaceRevision、members 四个字段。`core/crates/persistence/store/src/CoreSpaceStore.rs:25`
- `CoreSpaceStore` — new 创建的 store 记录同步操作。`core/crates/persistence/store/src/CoreSpaceStore.rs:160`
- `CoreSpaceDeviceProfile` — 设备档案，含 nodeId、displayName、userName、platform、model。`core/crates/persistence/store/src/CoreSpaceStore.rs:34`
- `CoreSpaceDevicePresence` — 设备在线状态，含 nodeId、active、baseUrl、version、updatedAt。`core/crates/persistence/store/src/CoreSpaceStore.rs:76`
- `CoreSpaceLinkAdvertisement` — 链路广告，含 targetNodeId、channelEpoch、sequence、measuredAt、expiresAt。`core/crates/persistence/store/src/CoreSpaceStore.rs:63`
- `CoreSpaceRoutePlan` — 选路计划，path 是从首跳到目标（含目标）的节点 id 列表。`core/crates/persistence/store/src/CoreSpaceStore.rs:97`
- `CORE_SPACE_RECORD_VERSION` — Space 记录的 schema 版本，值为 3。`core/crates/persistence/store/src/CoreSpaceStore.rs:18`
- `UNMEASURED_DIRECT_PEER_COST` — 无度量直连对端的选路代价，值为 1_000_000_000。`core/crates/persistence/store/src/CoreSpaceStore.rs:19`
- `COMPACT_TOPOLOGY_V1` — 拓扑紧凑编码名，值为 topologyV1。`core/crates/persistence/store/src/CoreSpaceStore.rs:127`
- `PreferencesDataStore` — 偏好存储，new 创建同步偏好 store。`core/crates/persistence/store/src/PreferencesDataStore.rs:2909`
- `Preferences` — 偏好快照，PartialEq 只比较持久化值。`core/crates/persistence/store/src/PreferencesDataStore.rs:1586`
- `CoreNodeStateStore` — typedEntry 只解码请求的记录，不展开无关 JSON。`core/crates/persistence/store/src/PreferencesDataStore.rs:1883`
- `CoreNodeSecretStore` — 存节点本地凭证与密钥，接受旧版加密文件。`core/crates/persistence/store/src/PreferencesDataStore.rs:2350`
- `PreferencesSyncDescriptor` — forStoragePath 由存储路径推导同步描述符。`core/crates/persistence/store/src/PreferencesDataStore.rs:2426`
- `PreferencesSyncedEntry` — fromOperation 要求同步操作的域为 preferences。`core/crates/persistence/store/src/PreferencesDataStore.rs:2573`
- `Flow` — collectWithCancellation 先发出当前值，再在 waitChanged 报告变化后发出新值。`core/crates/persistence/store/src/PreferencesDataStore.rs:352`
- `StateFlow` — set_value 在值不变时不通知订阅者。`core/crates/persistence/store/src/PreferencesDataStore.rs:752`
- `combine2` — 把两个 StateFlow 合并为一个派生 StateFlow。`core/crates/persistence/store/src/PreferencesDataStore.rs:913`
- `combine5` — 最多合并五个 StateFlow。`core/crates/persistence/store/src/PreferencesDataStore.rs:1220`
- `PREFERENCES_SCHEMA_VERSION_KEY_NAME` — 偏好 schema 版本键，值为 __operit_preferences_schema_version。`core/crates/persistence/store/src/PreferencesDataStore.rs:71`
- `PREFERENCES_REPLICATION_KEY` — 复制元数据键，值为 __operit_preferences_replication。`core/crates/persistence/store/src/PreferencesDataStore.rs:69`

## 核心机制

### 聚合与 feature 门控

`lib.rs` 用 `pub use PreferencesDataStore::*` 把偏好存储的公开项重导出到 crate 根。`core/crates/persistence/store/src/lib.rs:53`

`lib.rs` 用 `pub use SqliteStore::*` 把该模块的公开项重导出到 crate 根。`core/crates/persistence/store/src/lib.rs:59`

`lib.rs` 的 `pub use SqliteStore::*;` 重导出本身也在 `#[cfg(feature = "full")]` 门控下。`core/crates/persistence/store/src/lib.rs:58`

`lib.rs` 的 `repository`、`dao`、`db`、`sync` 四个模块只在 `feature full` 下公开。`core/crates/persistence/store/src/lib.rs:66`

`SqliteStore` 模块只在 `feature full` 下公开。`core/crates/persistence/store/src/lib.rs:47`

`CoreNodeBindingStore` 模块只在 `feature full` 下公开。`core/crates/persistence/store/src/lib.rs:10`

`WorkspaceFileSyncStore` 与 `RuntimeFileSyncStore` 只在 `feature full` 下公开。`core/crates/persistence/store/src/lib.rs:40`

### SQLite 连接与事务

`SqliteStore` 是共享 SQLite 连接包装器，连接由注册的 runtime host 提供。`core/crates/persistence/store/src/SqliteStore.rs:33`

`SqliteStore::open` 用 `runtimeStoragePath` 解析逻辑路径后打开数据库。`core/crates/persistence/store/src/SqliteStore.rs:47`

`SqliteStore::openWithHost` 打开连接后执行 `PRAGMA foreign_keys = ON`。`core/crates/persistence/store/src/SqliteStore.rs:57`

`SqliteStore::executeBatch` 执行一段 SQL 批处理。`core/crates/persistence/store/src/SqliteStore.rs:76`

`SqliteStore::execute` 执行一条 SQL 语句并返回受影响行数。`core/crates/persistence/store/src/SqliteStore.rs:81`

`SqliteStore::queryRows` 运行查询并返回全部行。`core/crates/persistence/store/src/SqliteStore.rs:90`

`SqliteStore::queryOne` 运行查询并返回首行的 `Option`，不存在时为空。`core/crates/persistence/store/src/SqliteStore.rs:99`

`SqliteStore::queryScalar` 取首行首列并转换类型，无行时报错 `sqlite query returned no rows`。`core/crates/persistence/store/src/SqliteStore.rs:108`

`SqliteStore::getUserVersion` 读 `PRAGMA user_version`。`core/crates/persistence/store/src/SqliteStore.rs:121`

`SqliteStore::setUserVersion` 写 `PRAGMA user_version`。`core/crates/persistence/store/src/SqliteStore.rs:127`

`SqliteStore::tableExists` 查 `sqlite_master` 判断指定表是否存在。`core/crates/persistence/store/src/SqliteStore.rs:134`

`SqliteStore::addInvalidationObserver` 注册失效回调。`core/crates/persistence/store/src/SqliteStore.rs:143`

`SqliteStore::notifyInvalidated` 依次调用全部已注册失效回调。`core/crates/persistence/store/src/SqliteStore.rs:157`

`SqliteStore::transaction` 在 action 成功时提交，失败时显式回滚；回滚也失败时返回同时携带 action 错误与 rollback 错误的 `TransactionRollback`。`core/crates/persistence/store/src/SqliteStore.rs:184`

测试 `failed_action_rolls_back_explicitly_without_destructor_cleanup` 要求失败的 action 恰好显式回滚一次，不依赖析构清理。`core/crates/persistence/store/src/SqliteStore.rs:524`

`SqliteTransaction::execute` 在事务内执行语句。`core/crates/persistence/store/src/SqliteStore.rs:202`

`SqliteTransaction::lastInsertRowId` 返回事务内最后插入行的 id。`core/crates/persistence/store/src/SqliteStore.rs:235`

`FromSqliteValue` 把 host 的 `SqliteValue` 转成 Rust 强类型值。`core/crates/persistence/store/src/SqliteStore.rs:284`

`ToSqliteValue` 把 Rust 值转成 host 的 `SqliteValue`。`core/crates/persistence/store/src/SqliteStore.rs:337`

`sqliteParams!` 宏把值转成 `SqliteValue` 参数向量。`core/crates/persistence/store/src/SqliteStore.rs:407`

### 节点身份

`CoreNodeIdentity` 只有一个字段 `nodeId`。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:18`

身份记录的键是 `record`。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:14`

`IdentityRecord` 只从共享记录解码 `deviceId` 字段。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:24`

新身份的 `nodeId` 格式是 `core-{毫秒时间戳}-{uuid}`。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:92`

`CoreNodeIdentityStore::identity` 在身份未初始化时报错 `CoreNode identity is not initialized`。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:67`

`CoreNodeIdentityStore::localNodeId` 不初始化存储、不编造节点，直接读已持久化的本地身份。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:58`

`CoreNodeIdentityStore::writeNodeId` 先校验 `nodeId` 非空，再重写共享记录的 `deviceId`，同时保留 Link Access 展示元数据。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:105`

`CoreNodeIdentityStore::dataStore` 把身份存在 `RUNTIME_LINK_ACCESS_IDENTITY_PATH` 的 `CoreNodeStateStore`，schema 版本为 2。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:130`

身份 schema 的 v1 迁移接受 JSON 字符串与已解码对象两种旧记录形态。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:140`

`validateNodeId` 只要求 `nodeId` 去空白后非空。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:158`

### Binding

Binding 的同步域是 `binding`，实体类型是 `binding`。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:17`

`CoreNodeBindingRecord` 含 `key`、`nodeId`、`generation` 三个字段。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:84`

`CoreNodeBindingCommit` 含 `binding` 记录与持久化它的 `SyncOperation`。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:92`

`CoreNodeBindingStore::new` 先经 `CoreNodeIdentityStore` 初始化本地节点身份。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:108`

Binding 记录由 `RUNTIME_SYNC_DIR_PATH` 上的 `SyncOperationStore` 持久化。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:113`

`CoreNodeBindingStore::create` 为新 key 创建 `generation` 为 1 的初始 Binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:157`

`CoreNodeBindingStore::create` 在 key 已存在时报错 `Binding already exists`。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:152`

`CoreNodeBindingStore::createLocal` 以本地节点为初始目标创建 Binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:163`

`CoreNodeBindingStore::compareAndSet` 在当前节点与 `expectedNodeId` 不一致时返回 `Binding conflict` 错误。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:196`

`CoreNodeBindingStore::compareAndSet` 切换到不同目标并提交成功时 `generation` 加 1。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:209`

`CoreNodeBindingStore::compareAndSet` 在目标与当前相同时直接返回当前记录与最新操作，不写新记录。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:200`

`CoreNodeBindingStore::delete` 追加 `delete` 操作并清进程缓存，不要求目标执行节点在场。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:168`

`CoreNodeBindingStore::applySyncedOperation` 应用已同步的 Binding 操作，不产生新的本地操作。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:215`

`CoreNodeBindingStore::applyBootstrapOperation` 应用 Space 引导的 Binding 操作，跳过本地冲突过滤。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:221`

`CoreNodeBindingStore::applyImmediateOperation` 用 `appendUnobservedOperation` 追加直接传输的操作，不推进持久化时钟。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:271`

`materializeBindingRecords` 按 `bindingOperationOrder` 取每个实体的最新操作。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:303`

只有 `upsert` 操作能成为当前 Binding 记录，`delete` 操作不产生记录。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:312`

`validateBindingOperation` 要求域、实体类型、操作名与 `EntityState` 语义四者一致。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:441`

Binding 的 `delete` 操作载荷必须为 `null`。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:451`

Binding 的 `generation` 必须为正数。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:462`

同一 storage host 与同步根路径上的 Binding store 共享一份进程内缓存。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:61`

`coreNodeBindingMutationLock` 是进程内互斥锁，用于保持本地 compare-and-set 语义。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:55`

### Space 成员与投影

`CoreSpace` 含 `spaceId`、`spaceName`、`spaceRevision`、`members` 四个字段。`core/crates/persistence/store/src/CoreSpaceStore.rs:25`

Space 记录的 schema 版本是 3。`core/crates/persistence/store/src/CoreSpaceStore.rs:18`

`CoreSpaceStore::new` 创建的 store 记录同步操作。`core/crates/persistence/store/src/CoreSpaceStore.rs:160`

`CoreSpaceStore::newNodeLocal` 创建的端点 store 不记录同步操作、业务复制时钟与日志。`core/crates/persistence/store/src/CoreSpaceStore.rs:166`

新 Space 的初始显示名是 `Operit`。`core/crates/persistence/store/src/CoreSpaceStore.rs:1602`

新 Space 的 id 格式是 `space-{uuid}`。`core/crates/persistence/store/src/CoreSpaceStore.rs:1608`

`CoreSpaceStore::initializeNamed` 创建 `spaceRevision` 为 1 的成员记录。`core/crates/persistence/store/src/CoreSpaceStore.rs:193`

`mergedProjection` 把本地与对端成员合并，新 revision 取两者最大值加 1。`core/crates/persistence/store/src/CoreSpaceStore.rs:227`

`adoptAt` 拒绝 revision 更旧的加入投影。`core/crates/persistence/store/src/CoreSpaceStore.rs:246`

`adoptAt` 在同 revision 但 `spaceId` 或 `spaceName` 不同时报错。`core/crates/persistence/store/src/CoreSpaceStore.rs:252`

`CoreSpaceStore::rename` 把 Space 的 revision 加 1。`core/crates/persistence/store/src/CoreSpaceStore.rs:350`

`CoreSpaceStore::leave` 创建新单例 Space，成员只有本设备；损坏的对端记录与缺失的本地 profile 不阻止退出。`core/crates/persistence/store/src/CoreSpaceStore.rs:366`

`CoreSpaceStore::removeRemoteMember` 拒绝移除本设备，本设备退出须用 `leave`。`core/crates/persistence/store/src/CoreSpaceStore.rs:463`

`CoreSpaceStore::removeRemoteMember` 把被移除成员重写为 revision 为 1 的独立 Space。`core/crates/persistence/store/src/CoreSpaceStore.rs:497`

`CoreSpaceStore::removeRemoteMember` 把其余成员投影的 revision 加 1。`core/crates/persistence/store/src/CoreSpaceStore.rs:502`

`CoreSpaceStore::alignRemoteMemberRecord` 对本地设备拒绝，本地成员只能经 `leave` 退出。`core/crates/persistence/store/src/CoreSpaceStore.rs:529`

`CoreSpaceStore::admitRemoteMember` 先写设备 profile 再把成员加入投影，不要求对端提供业务存储。`core/crates/persistence/store/src/CoreSpaceStore.rs:568`

`CoreSpaceStore::writeLocalProtocol` 只刷新协议身份，不把软件版本当作兼容性变化。`core/crates/persistence/store/src/CoreSpaceStore.rs:614`

`CoreSpaceStore::writeLocalDeviceProfile` 在展示字段不变时直接返回已有 profile，不重写。`core/crates/persistence/store/src/CoreSpaceStore.rs:658`

`CoreSpaceStore::writeLocalDeviceProfile` 写本地设备档案时，若 Space 仍是 revision 1 的初始单成员 Space 且名仍为默认名，则把 Space 重命名为设备显示名。`core/crates/persistence/store/src/CoreSpaceStore.rs:641`

`CoreSpaceStore::importDeviceProfiles` 跳过 `updatedAt` 不比已有记录新的 profile。`core/crates/persistence/store/src/CoreSpaceStore.rs:756`

`CoreSpaceStore::deviceProfilesForCurrentSpace` 在成员缺少 profile 时报错。`core/crates/persistence/store/src/CoreSpaceStore.rs:722`

`readRecords` 读坏的非本地记录时只记警告并跳过，读坏的本地记录时返回错误。`core/crates/persistence/store/src/CoreSpaceStore.rs:1181`

`coreSpaceFromRecords` 的记录为空时报错 `Device space is not initialized`。`core/crates/persistence/store/src/CoreSpaceStore.rs:1461`

`coreSpaceFromRecords` 在本地身份无成员记录时报错。`core/crates/persistence/store/src/CoreSpaceStore.rs:1465`

`coreSpaceFromRecords` 只取与本地身份同一 `spaceId` 的记录作为成员。`core/crates/persistence/store/src/CoreSpaceStore.rs:1468`

`hasSameMembershipAs` 比较除 `updatedAt` 外的全部成员字段。`core/crates/persistence/store/src/CoreSpaceStore.rs:1448`

`writeSpaceProjectionAt` 拒绝 revision 小于等于 0 的投影。`core/crates/persistence/store/src/CoreSpaceStore.rs:1223`

`writeMemberRecord` 用 `replaceRecoverably` 写成员记录。`core/crates/persistence/store/src/CoreSpaceStore.rs:1203`

`importTopologyRecords` 跳过本地记录与 `updatedAt` 不比已有记录新的公告。`core/crates/persistence/store/src/CoreSpaceStore.rs:1257`

导入的拓扑记录不产生本地同步操作。`core/crates/persistence/store/src/CoreSpaceStore.rs:1266`

### 链路、拓扑与选路

`CoreSpaceDeviceProfile` 含 `nodeId`、`displayName`、`userName`、`platform`、`model`。`core/crates/persistence/store/src/CoreSpaceStore.rs:34`

`CoreSpaceDeviceProfile` 含 `coreVersion`、`protocolVersion`、`pairingIncarnation`、`updatedAt`。`core/crates/persistence/store/src/CoreSpaceStore.rs:46`

`pairingIncarnation` 标记设备加入时声明的配对代次，移除只撤销该代次的配对。`core/crates/persistence/store/src/CoreSpaceStore.rs:48`

`CoreSpaceLinkAdvertisement` 含 `targetNodeId`、`channelEpoch`、`sequence`、`measuredAt`、`expiresAt`。`core/crates/persistence/store/src/CoreSpaceStore.rs:63`

`CoreSpaceLinkAdvertisement` 含 `smoothedRttMs`、`lossPermille`、`congestionPermille` 三个链路质量字段。`core/crates/persistence/store/src/CoreSpaceStore.rs:69`

`CoreSpaceDevicePresence` 含 `nodeId`、`active`、`baseUrl`、`version`、`updatedAt`。`core/crates/persistence/store/src/CoreSpaceStore.rs:76`

`CoreSpaceRoutePlan` 的 `path` 是从首跳到目标（含目标）的节点 id 列表。`core/crates/persistence/store/src/CoreSpaceStore.rs:97`

`CoreSpaceRoutePlan::firstHop` 返回计划的首跳。`core/crates/persistence/store/src/CoreSpaceStore.rs:105`

`CoreSpaceRoutePlan::hops` 返回路径的跳数。`core/crates/persistence/store/src/CoreSpaceStore.rs:111`

`CoreSpaceStore::setDirectPeers` 拒绝把本设备登记为直接对端。`core/crates/persistence/store/src/CoreSpaceStore.rs:807`

`CoreSpaceStore::publishLocalLinkAdvertisement` 拒绝向非活跃直接对端发布链路广告。`core/crates/persistence/store/src/CoreSpaceStore.rs:848`

`CoreSpaceStore::publishLocalAdjacency` 在对端集合与未过期链路都未变时返回 `false`，不写记录。`core/crates/persistence/store/src/CoreSpaceStore.rs:910`

新对端的初始链路广告 `sequence` 为 1，`channelEpoch` 为 `direct-adjacency`。`core/crates/persistence/store/src/CoreSpaceStore.rs:938`

`reachableNextHopThroughPeers` 用 Dijkstra 在未过期的有向链路度量上解析首跳。`core/crates/persistence/store/src/CoreSpaceStore.rs:1001`

无度量的直连对端在选路时代价为 `1_000_000_000`。`core/crates/persistence/store/src/CoreSpaceStore.rs:1061`

`UNMEASURED_DIRECT_PEER_COST` 的值是 `1_000_000_000`。`core/crates/persistence/store/src/CoreSpaceStore.rs:19`

`linkCost` 等于 1000 加 `smoothedRttMs` 乘 10、`lossPermille` 乘 25、`congestionPermille` 乘 10。`core/crates/persistence/store/src/CoreSpaceStore.rs:1686`

`routePlanThroughPeers` 拒绝以本设备为目标、拒绝非成员目标。`core/crates/persistence/store/src/CoreSpaceStore.rs:1029`

`deviceConnections` 只返回当前 Space 成员之间的有向直连。`core/crates/persistence/store/src/CoreSpaceStore.rs:961`

拓扑记录不允许重复对端。`core/crates/persistence/store/src/CoreSpaceStore.rs:1642`

拓扑记录不允许自环。`core/crates/persistence/store/src/CoreSpaceStore.rs:1647`

链路广告的目标必须是直接对端。`core/crates/persistence/store/src/CoreSpaceStore.rs:1657`

拓扑记录不允许重复有向链路。`core/crates/persistence/store/src/CoreSpaceStore.rs:1660`

链路广告要求 `sequence` 为正、`expiresAt` 大于 `measuredAt`、`loss` 与 `congestion` 各不超过 1000。`core/crates/persistence/store/src/CoreSpaceStore.rs:1675`

`migrateRecord` 把 schema 2 下以字符串存放的记录解码为对象。`core/crates/persistence/store/src/CoreSpaceStore.rs:1428`

`migrateRecord` 在记录版本已不低于 3 时返回 `SchemaVersionTooNew`。`core/crates/persistence/store/src/CoreSpaceStore.rs:1424`

节点本地端点在 `nodeLocalApplicationHistoryLimit` 存在时用 `topologyV1` 紧凑编码存拓扑。`core/crates/persistence/store/src/CoreSpaceStore.rs:1321`

`COMPACT_TOPOLOGY_V1` 的值是 `topologyV1`。`core/crates/persistence/store/src/CoreSpaceStore.rs:127`

### 校验规则

`validateSpaceName` 要求名非空、不超过 80 字符、不含控制字符。`core/crates/persistence/store/src/CoreSpaceStore.rs:1628`

`validateDeviceProfileField` 要求字段非空、不超过 160 字符、不含控制字符。`core/crates/persistence/store/src/CoreSpaceStore.rs:1585`

`validateDeviceUserName` 要求用户名不超过 80 字符、不含控制字符。`core/crates/persistence/store/src/CoreSpaceStore.rs:1570`

`validateDevicePresence` 只在 `active` 为 `true` 时要求 `baseUrl` 与 `version` 非空。`core/crates/persistence/store/src/CoreSpaceStore.rs:1533`

### 偏好存储的两种形态

`PreferencesDataStore` 的字段含 `path`、`storagePath`、`storageHost`、`encryption`、`syncOperationStore`、`syncDescriptor`。`core/crates/persistence/store/src/PreferencesDataStore.rs:1842`

`PreferencesDataStore` 的字段含 `changeSignal`、`sharedState`、`schema`。`core/crates/persistence/store/src/PreferencesDataStore.rs:1847`

`PreferencesDataStore::new` 创建同步偏好 store。`core/crates/persistence/store/src/PreferencesDataStore.rs:2909`

`PreferencesDataStore::newEncrypted` 创建加密的同步偏好 store。`core/crates/persistence/store/src/PreferencesDataStore.rs:2917`

`PreferencesDataStore::newWithStorage` 创建同步偏好 store。`core/crates/persistence/store/src/PreferencesDataStore.rs:2925`

`PreferencesDataStore::newEncryptedWithStorage` 创建加密的同步偏好 store。`core/crates/persistence/store/src/PreferencesDataStore.rs:2936`

`PreferencesDataStore::newNodeLocalWithStorage` 创建节点本地 store。`core/crates/persistence/store/src/PreferencesDataStore.rs:2975`

同步 store 的 `syncOperationStore` 与 `syncDescriptor` 均存在。`core/crates/persistence/store/src/PreferencesDataStore.rs:2962`

节点本地 store 的 `syncOperationStore` 与 `syncDescriptor` 均为 `None`。`core/crates/persistence/store/src/PreferencesDataStore.rs:3001`

`PreferencesSyncDescriptor::forStoragePath` 由存储路径推导同步描述符。`core/crates/persistence/store/src/PreferencesDataStore.rs:2426`

同步描述符的域固定为 `preferences`，实体类型取自文件名去掉 `.preferences.json` 与 `.json` 后缀。`core/crates/persistence/store/src/PreferencesDataStore.rs:2437`

`preferenceSyncStore` 只认 `members`、`profiles`、`presence`、`topology` 四个目录下的 `.preferences.json` 记录。`core/crates/persistence/store/src/CoreSpaceStore.rs:1411`

`CoreNodeStateStore::typedEntry` 只解码请求的记录，不展开无关 JSON。`core/crates/persistence/store/src/PreferencesDataStore.rs:1883`

`CoreNodeStateStore::delete` 同时删除文件与共享快照，避免后续相同导入被缓存跳过。`core/crates/persistence/store/src/PreferencesDataStore.rs:2141`

`CoreNodeSecretStore` 存节点本地凭证与密钥，接受旧版加密文件。`core/crates/persistence/store/src/PreferencesDataStore.rs:2350`

`encodeStoredPreferences` 的 `bounded` 模式指无同步描述符且存储宿主不保留偏好缓存。`core/crates/persistence/store/src/PreferencesDataStore.rs:3524`

`encodeStoredPreferences` 在 `bounded` 模式下写紧凑 JSON，否则写 pretty JSON。`core/crates/persistence/store/src/PreferencesDataStore.rs:3530`

读取偏好文件不改写文件，不创建新解密密钥。`core/crates/persistence/store/src/PreferencesDataStore.rs:3238`

加密偏好文件以 `format` 字段 `operit.preferences.encrypted` 标识。`core/crates/persistence/store/src/PreferencesDataStore.rs:3602`

### 偏好条目与变更

`Preferences::set` 在值不变时直接返回，不记变更。`core/crates/persistence/store/src/PreferencesDataStore.rs:1635`

`Preferences::set` 把每次写记为一条 `set` 变更。`core/crates/persistence/store/src/PreferencesDataStore.rs:1641`

增量写记为 `increment` 操作，存增量而非绝对值。`core/crates/persistence/store/src/PreferencesDataStore.rs:1680`

`Preferences::setObjectField` 只改对象的一个字段。`core/crates/persistence/store/src/PreferencesDataStore.rs:1715`

对象字段的变更记为 `patch_object` 操作。`core/crates/persistence/store/src/PreferencesDataStore.rs:1751`

`Preferences` 的 `PartialEq` 只比较持久化值，不比较待提交变更。`core/crates/persistence/store/src/PreferencesDataStore.rs:1586`

### Schema 与迁移

偏好 schema 版本键是 `__operit_preferences_schema_version`，复制元数据键是 `__operit_preferences_replication`。`core/crates/persistence/store/src/PreferencesDataStore.rs:71`

`PreferencesDataStore::withSchema` 声明当前 schema 版本与逐版本迁移回调。`core/crates/persistence/store/src/PreferencesDataStore.rs:3011`

`readSchemaVersion` 把缺失的版本键当作 0。`core/crates/persistence/store/src/PreferencesDataStore.rs:3216`

`readSchemaVersion` 接受字符串与数字两种版本写法。`core/crates/persistence/store/src/PreferencesDataStore.rs:3220`

存储版本高于声明版本时迁移返回 `SchemaVersionTooNew`。`core/crates/persistence/store/src/PreferencesDataStore.rs:3196`

迁移按版本逐级应用，每级迁移一次，完成后把 schema 版本键写为当前版本。`core/crates/persistence/store/src/PreferencesDataStore.rs:3204`

### 偏好读写与观察

`data()` 在同步 store 或宿主保留偏好缓存的前提下，已缓存快照且 schema 已是最新时直接返回缓存。`core/crates/persistence/store/src/PreferencesDataStore.rs:3073`

`PreferencesDataStore::edit` 在内存中改偏好并持久化。`core/crates/persistence/store/src/PreferencesDataStore.rs:3328`

`PreferencesDataStore::migrate` 应用本地迁移或修复，不产生同步操作。`core/crates/persistence/store/src/PreferencesDataStore.rs:3356`

`PreferencesDataStore::replace` 整体替换快照并通知观察者。`core/crates/persistence/store/src/PreferencesDataStore.rs:3435`

`PreferencesDataStore::replace` 在内容不变且格式匹配时不写文件。`core/crates/persistence/store/src/PreferencesDataStore.rs:3474`

`PreferencesDataStore::replaceRecoverably` 与 `replace` 是同一替换路径。`core/crates/persistence/store/src/PreferencesDataStore.rs:3495`

`PreferencesDataStore::dataFlow` 返回带观察的 `Flow<Preferences>`。`core/crates/persistence/store/src/PreferencesDataStore.rs:3296`

### Flow 与 StateFlow

`Flow::collectWithCancellation` 先发出当前值，再在 `waitChanged` 报告变化后发出新值。`core/crates/persistence/store/src/PreferencesDataStore.rs:352`

`StateFlow::set_value` 在值不变时不通知订阅者。`core/crates/persistence/store/src/PreferencesDataStore.rs:752`

`StateFlow::compare_and_set` 只在当前值等于 `expect` 时替换。`core/crates/persistence/store/src/PreferencesDataStore.rs:785`

`combine2` 把两个 `StateFlow` 合并为一个派生 `StateFlow`。`core/crates/persistence/store/src/PreferencesDataStore.rs:913`

`combine5` 最多合并五个 `StateFlow`。`core/crates/persistence/store/src/PreferencesDataStore.rs:1220`

### 偏好同步载荷

`PreferencesSyncedEntry::fromOperation` 要求同步操作的域为 `preferences`。`core/crates/persistence/store/src/PreferencesDataStore.rs:2573`

偏好事务要求 `formatVersion` 为 2 且至少含 2 条。`core/crates/persistence/store/src/PreferencesDataStore.rs:2607`

偏好事务的条目键必须唯一。`core/crates/persistence/store/src/PreferencesDataStore.rs:2618`

偏好同步载荷的 `formatVersion` 只接受 1 与 2。`core/crates/persistence/store/src/PreferencesDataStore.rs:2661`

复制元数据键不许作为业务条目同步。`core/crates/persistence/store/src/PreferencesDataStore.rs:2592`

schema 元数据键不许作为业务条目同步。`core/crates/persistence/store/src/PreferencesDataStore.rs:2666`

`increment`、`patch_object`、`alias` 操作要求 `Transaction` 语义。`core/crates/persistence/store/src/PreferencesDataStore.rs:2693`

`PreferencesSyncedEntry::requireSchemaVersion` 在远端 schema 版本高于本地时返回 `SchemaVersionTooNew`。`core/crates/persistence/store/src/PreferencesDataStore.rs:2752`

`prepareSync`、`isSyncPrepared`、`syncSnapshot`、`repairSyncedSnapshot` 四个同步入口委托给 `Transaction::preference`。`core/crates/persistence/store/src/PreferencesDataStore.rs:3904`

同步的插件偏好路径必须以 `.preferences.json` 结尾。`core/crates/persistence/store/src/PreferencesDataStore.rs:3712`

同步的插件偏好路径必须归 Space 所有，节点本地与临时存储不许同步偏好。`core/crates/persistence/store/src/PreferencesDataStore.rs:3717`

同一 storage host 与路径的偏好 store 共享同一份 shared state。`core/crates/persistence/store/src/PreferencesDataStore.rs:3778`

同一 storage host 与路径的偏好 store 共享同一个 change signal。`core/crates/persistence/store/src/PreferencesDataStore.rs:3806`

`notifyChanged` 递增版本号、唤醒等待者并调度订阅者回调。`core/crates/persistence/store/src/PreferencesDataStore.rs:3584`

## 关键符号

`SqliteStore` — 共享 SQLite 连接包装器。`core/crates/persistence/store/src/SqliteStore.rs:33`

`SqliteTransaction` — 事务内执行语句。`core/crates/persistence/store/src/SqliteStore.rs:202`

`SqliteStoreError` — 含 `TransactionRollback`，回滚失败时同时保留 action 错误与 rollback 错误。`core/crates/persistence/store/src/SqliteStore.rs:184`

`FromSqliteValue` — host 值转 Rust 强类型。`core/crates/persistence/store/src/SqliteStore.rs:284`

`ToSqliteValue` — Rust 值转 host 值。`core/crates/persistence/store/src/SqliteStore.rs:337`

`sqliteParams!` — 值转 `SqliteValue` 参数向量。`core/crates/persistence/store/src/SqliteStore.rs:407`

`CoreNodeIdentity` — 只有一个字段 `nodeId`。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:18`

`CoreNodeIdentityStore` — 节点身份存储，schema 版本为 2。`core/crates/persistence/store/src/CoreNodeIdentityStore.rs:130`

`CoreNodeBindingRecord` — Binding 的持久化记录。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:84`

`CoreNodeBindingCommit` — 已提交的 Binding 变更。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:92`

`CoreNodeBindingStore` — Binding 记录的持久化存储。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:113`

`BINDING_SYNC_DOMAIN` — Binding 的同步域，值为 `binding`。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:17`

`CoreSpace` — Space 的持久化记录。`core/crates/persistence/store/src/CoreSpaceStore.rs:25`

`CoreSpaceStore` — Space 成员、profile、presence、拓扑与链路的存储。`core/crates/persistence/store/src/CoreSpaceStore.rs:160`

`CoreSpaceDeviceProfile` — 设备档案。`core/crates/persistence/store/src/CoreSpaceStore.rs:34`

`CoreSpaceDevicePresence` — 设备在线状态。`core/crates/persistence/store/src/CoreSpaceStore.rs:76`

`CoreSpaceLinkAdvertisement` — 链路广告。`core/crates/persistence/store/src/CoreSpaceStore.rs:63`

`CoreSpaceRoutePlan` — 选路计划。`core/crates/persistence/store/src/CoreSpaceStore.rs:97`

`CORE_SPACE_RECORD_VERSION` — Space 记录的 schema 版本，值为 3。`core/crates/persistence/store/src/CoreSpaceStore.rs:18`

`UNMEASURED_DIRECT_PEER_COST` — 无度量直连对端的选路代价。`core/crates/persistence/store/src/CoreSpaceStore.rs:19`

`COMPACT_TOPOLOGY_V1` — 拓扑紧凑编码名。`core/crates/persistence/store/src/CoreSpaceStore.rs:127`

`PreferencesDataStore` — 偏好存储，同步与节点本地两种形态。`core/crates/persistence/store/src/PreferencesDataStore.rs:2909`

`Preferences` — 偏好快照。`core/crates/persistence/store/src/PreferencesDataStore.rs:1586`

`CoreNodeStateStore` — 节点本地状态存储。`core/crates/persistence/store/src/PreferencesDataStore.rs:1883`

`CoreNodeSecretStore` — 节点本地凭证与密钥存储。`core/crates/persistence/store/src/PreferencesDataStore.rs:2350`

`PreferencesSyncDescriptor` — 偏好同步描述符。`core/crates/persistence/store/src/PreferencesDataStore.rs:2426`

`PreferencesSyncedEntry` — 已同步的偏好条目。`core/crates/persistence/store/src/PreferencesDataStore.rs:2573`

`Flow` — 可观察的值流。`core/crates/persistence/store/src/PreferencesDataStore.rs:352`

`StateFlow` — 带当前值的可观察状态。`core/crates/persistence/store/src/PreferencesDataStore.rs:752`

`combine2` — 合并两个 `StateFlow`。`core/crates/persistence/store/src/PreferencesDataStore.rs:913`

`combine5` — 合并五个 `StateFlow`。`core/crates/persistence/store/src/PreferencesDataStore.rs:1220`

## 调用链

`CoreNodeBindingStore::new` 先经 `CoreNodeIdentityStore` 初始化本地节点身份。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:108`

Binding 记录由 `RUNTIME_SYNC_DIR_PATH` 上的 `SyncOperationStore` 持久化。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:113`

`CoreNodeBindingStore::create` 为新 key 创建 `generation` 为 1 的初始 Binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:157`

`CoreNodeBindingStore::compareAndSet` 切换到不同目标并提交成功时 `generation` 加 1。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:209`

`CoreSpaceStore::initializeNamed` 创建 `spaceRevision` 为 1 的成员记录。`core/crates/persistence/store/src/CoreSpaceStore.rs:193`

`merge` 经 `mergedProjection` 合并本地与对端成员，新 revision 取两者最大值加 1。`core/crates/persistence/store/src/CoreSpaceStore.rs:227`

`adoptAt` 拒绝 revision 更旧的加入投影。`core/crates/persistence/store/src/CoreSpaceStore.rs:246`

`writeMemberRecord` 用 `replaceRecoverably` 写成员记录。`core/crates/persistence/store/src/CoreSpaceStore.rs:1203`

`PreferencesDataStore::edit` 在内存中改偏好并持久化。`core/crates/persistence/store/src/PreferencesDataStore.rs:3328`

`data()` 在同步 store 或宿主保留偏好缓存的前提下，已缓存快照且 schema 已是最新时直接返回缓存。`core/crates/persistence/store/src/PreferencesDataStore.rs:3073`

`prepareSync`、`isSyncPrepared`、`syncSnapshot`、`repairSyncedSnapshot` 四个同步入口委托给 `Transaction::preference`。`core/crates/persistence/store/src/PreferencesDataStore.rs:3904`

`notifyChanged` 递增版本号、唤醒等待者并调度订阅者回调。`core/crates/persistence/store/src/PreferencesDataStore.rs:3584`

## 来源

- `core/crates/persistence/README.md`（13 行，100% 已读）
- `core/crates/persistence/store/src/lib.rs`（92 行，100% 已读）
- `core/crates/persistence/store/src/SqliteStore.rs`（568 行，100% 已读）
- `core/crates/persistence/store/src/CoreNodeIdentityStore.rs`（163 行，100% 已读）
- `core/crates/persistence/store/src/CoreNodeBindingStore.rs`（481 行，100% 已读）
- `core/crates/persistence/store/src/CoreSpaceStore.rs`（2972 行，100% 已读）
- `core/crates/persistence/store/src/PreferencesDataStore.rs`（3972 行，100% 已读）
