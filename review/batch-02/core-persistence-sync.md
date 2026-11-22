---
title: 持久化——同步存储
module: core
platforms: [all]
sources: [core/crates/persistence/store/src/SyncOperationStore.rs, core/crates/persistence/store/src/SyncBlobIo.rs, core/crates/persistence/store/src/SyncAppliedChanges.rs, core/crates/persistence/store/src/MergeRules.rs, core/crates/persistence/store/src/PreferenceMerge.rs, core/crates/persistence/store/src/WorkspaceFileSyncStore.rs, core/crates/persistence/store/src/RuntimeFileSyncStore.rs, core/crates/persistence/store/src/FileSyncPolicy.rs, core/crates/persistence/store/src/transaction/Journal.rs]
date: 2026-11-11
---

## 概述

持久化同步存储是 Space 内多设备同步落到磁盘的那一层，以 `SyncOperationStore` 为存储入口（`core/crates/persistence/store/src/SyncOperationStore.rs:427`）。本页只写“存什么、怎么存”；操作如何执行与重放，写在 [[core-node-runtime|节点——节点运行时]]。

## AI 速览

- `SyncOperation` — 一条同步操作，11 个字段（`core/crates/persistence/store/src/SyncOperationStore.rs:245`）
- `SyncOperationStore` — 操作日志、时钟、实体版本与导出下限的存储入口（`core/crates/persistence/store/src/SyncOperationStore.rs:427`）
- `SyncClock` — 按设备记录已知最后序列号的向量时钟（`core/crates/persistence/store/src/SyncOperationStore.rs:45`）
- `SyncReceipt` — 按来源记录确切已收区间的回执（`core/crates/persistence/store/src/SyncOperationStore.rs:121`）
- `SyncOperationOrder` — 并发实体操作的确定性冲突顺序（`core/crates/persistence/store/src/SyncOperationStore.rs:316`）
- `RuntimeFileSyncReference` — 内容哈希加大小的 blob 引用（`core/crates/persistence/store/src/SyncBlobIo.rs:9`）
- `RuntimeFileSyncStore` — 运行时文件的快照、blob 与删除 tombstone 存储（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:33`）
- `WorkspaceFileSyncStore` — 托管工作区文件的清单、延迟与待完成写入存储（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:59`）
- `FileSyncPolicy` — 工作区与会话文件的用户可编辑同步策略（`core/crates/persistence/store/src/FileSyncPolicy.rs:17`）
- `PreferenceMergeSchema` — 偏好合并声明所属存储的集合（`core/crates/persistence/store/src/PreferenceMerge.rs:61`）
- SyncAppliedChanges — 提交后通知订阅者的 post-commit 通知（`core/crates/persistence/store/src/SyncAppliedChanges.rs:47`）
- 主入口：SyncOperationStore 的 `appendLocalOperation` 追加本地操作（`core/crates/persistence/store/src/SyncOperationStore.rs:1881`）；SyncOperationStore 的 `operationsSinceWithInventory` 导出同步页（`core/crates/persistence/store/src/SyncOperationStore.rs:826`）；RuntimeFileSyncStore 的 `recordSnapshot` 记录文件快照（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:120`）；WorkspaceFileSyncStore 的 `scan` 扫描工作区清单（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:110`）。
- 数据流向：本地写操作 → 追加操作日志并推进向量时钟 → 按导出下限与实体胜者裁剪同步页 → 内容寻址 blob 随页传输 → 对端落库为 pending 并记实体版本 → 偏好按声明合并、文件按清单与策略落盘。

## 核心机制

### 操作与操作日志

- `SyncOperation` 由 `opId`、`originDeviceId`、`sequence`、`domain`、`entityType`、`entityId`、`operation`、`semantics`、`payload`、`createdAt`、`schemaVersion` 共 11 个字段组成（`core/crates/persistence/store/src/SyncOperationStore.rs:245`）。
- `SyncOperationSemantics` 只有 `EntityState` 与 `Transaction` 两种语义：前者替换一个声明实体的状态，后者保留一条不可变的有序变更（`core/crates/persistence/store/src/SyncOperationStore.rs:211`）。
- `SyncOperationSemantics` 在 SQL 中的存储值是 `entity_state` 与 `transaction`（`core/crates/persistence/store/src/SyncOperationStore.rs:220`）。
- `verifySyncOperation` 用操作摘要比对同一 `opId` 的已有操作与传入操作，不一致即报错（`core/crates/persistence/store/src/SyncOperationStore.rs:273`）。
- 当前操作日志存在 `{root}/transactions.sqlite` 中，Journal 的 `open` 打开该库并建立 `originals` 等表（`core/crates/persistence/store/src/transaction/Journal.rs:20`）。
- `withJournal` 是当前 Journal 的打开入口，首次打开时经 `importLegacyJournal` 把已退休文件式 ledger 做一次原子导入（`core/crates/persistence/store/src/SyncOperationStore.rs:1720`）。
- `importLegacyJournal` 是当前 Journal 的一次性迁移入口，只做一次原子导入（`core/crates/persistence/store/src/SyncOperationStore.rs:1806`）。
- 已退休的文件式 ledger 按来源设备存在 {root}/operations/{safeId}.jsonl（`core/crates/persistence/store/src/SyncOperationStore.rs:1455`）。
- 遗留 JSONL 路径用的 `storageSafeId` 把设备标识中非字母数字且非连字符、下划线的字符替换为下划线（`core/crates/persistence/store/src/SyncOperationStore.rs:1596`）。
- `appendLocalOperation` 经 `withJournal` 把新操作写入当前 Journal（`core/crates/persistence/store/src/SyncOperationStore.rs:1885`）。
- `appendLocalOperation` 生成的 `opId` 是 `originDeviceId` 与序列号以冒号连接，序列号是本地时钟与日志最高值加一（`core/crates/persistence/store/src/SyncOperationStore.rs:1885`）。
- `appendLocalOperation` 生成的操作 `schemaVersion` 为 1，`createdAt` 取当前墙钟毫秒与 `highest_business_time` 加一的较大者（混合逻辑时钟下限）（`core/crates/persistence/store/src/SyncOperationStore.rs:1881``core/crates/persistence/store/src/SyncOperationStore.rs:1896`）。
- 本地设备标识格式是 core-{毫秒}-{UUID 简写}，首次生成后持久保存（`core/crates/persistence/store/src/SyncOperationStore.rs:783`）。
- 本地设备标识存在 {root}/local_device_id 文件中（`core/crates/persistence/store/src/SyncOperationStore.rs:1436`）。
- 已注册设备清单的 {root}/devices.json 是遗留文件，仅迁移导入时读取，导入提交后由 `cleanLegacyJournal` 删除（`core/crates/persistence/store/src/SyncOperationStore.rs:1431`）（`core/crates/persistence/store/src/SyncOperationStore.rs:1751`）。
- 加密偏好同步载荷的存储格式标识是 `operit.sync.encrypted_payload`（`core/crates/persistence/store/src/SyncOperationStore.rs:367`）。
- `encryptedPreferenceSyncOperation` 只在 `domain` 为 `preferences`、操作为 `set` 或 `transaction`、且 `payload` 的 `encrypted` 为 `true` 时成立（`core/crates/persistence/store/src/SyncOperationStore.rs:1611`）。
- `scanOperationLog` 逐行把遗留 JSONL 操作日志分类为可解码或损坏，损坏内容只记入 `findings`，不导致扫描失败（`core/crates/persistence/store/src/SyncOperationStore.rs:1306``core/crates/persistence/store/src/SyncOperationStore.rs:1331`）。
- `quarantineOperationLines` 只处理遗留 JSONL 日志，把损坏行移入隔离边车，不删除任何内容，每行保留原始偏移、哈希与隔离时间戳（`core/crates/persistence/store/src/SyncOperationStore.rs:1483`）。
- 遗留 JSONL 日志的隔离边车路径是 {root}/operations/{safeId}.jsonl.quarantine（`core/crates/persistence/store/src/SyncOperationStore.rs:1465`）。

### 时钟、回执与导出下限

- `SyncClock` 用 `BTreeMap<String, i64>` 按设备记录已知的最后序列号（`core/crates/persistence/store/src/SyncOperationStore.rs:45`）。
- SyncClock 的 `sequenceFor` 对未知设备返回 0（`core/crates/persistence/store/src/SyncOperationStore.rs:58`）。
- SyncClock 的 `includes` 要求本地时钟覆盖对方时钟的每一个设备序列（`core/crates/persistence/store/src/SyncOperationStore.rs:71`）。
- 向量时钟存在 {root}/clocks.json 文件中（`core/crates/persistence/store/src/SyncOperationStore.rs:1424`）。
- `SyncReceipt` 用 `BTreeMap<String, Vec<[i64; 2]>>` 按来源记录确切的已收区间（`core/crates/persistence/store/src/SyncOperationStore.rs:121`）。
- SyncReceipt 的 `validate` 拒绝空来源、超过 256 字符的来源、起始不大于 0、结束小于起始、起始不大于前一区间结束的区间（`core/crates/persistence/store/src/SyncOperationStore.rs:132`）。
- `localClock` 读本地时钟前先发布偏好 outbox（`core/crates/persistence/store/src/SyncOperationStore.rs:943`）。
- `currentLocalClock` 只读缓存的本地时钟，不发布偏好 outbox（`core/crates/persistence/store/src/SyncOperationStore.rs:952`）。
- `publishPreferenceOutboxes` 逐个发布已注册偏好数据集的 outbox（`core/crates/persistence/store/src/SyncOperationStore.rs:721`）。
- 单个数据集发布失败只记日志并记录错误，其余数据集继续发布（`core/crates/persistence/store/src/SyncOperationStore.rs:736`）。
- `observeOperations` 只在操作序列大于已知序列时推进本地时钟并写回（`core/crates/persistence/store/src/SyncOperationStore.rs:1182``core/crates/persistence/store/src/SyncOperationStore.rs:1193`）。
- `observeNetworkControlOperations` 只接受 `domain` 为 `network_control` 的操作（`core/crates/persistence/store/src/SyncOperationStore.rs:1211``core/crates/persistence/store/src/NetworkControlStore.rs:53`）。
- `observeNetworkControlOperations` 用 `{originDeviceId}:control` 作为独立时钟键确认，不推进业务序列（`core/crates/persistence/store/src/SyncOperationStore.rs:1211``core/crates/persistence/store/src/SyncOperationStore.rs:1712`）。
- `networkControlClockKey` 的格式是 `{originDeviceId}:control`（`core/crates/persistence/store/src/SyncOperationStore.rs:1711`）。
- 导出下限存在 {root}/export_floors.json 文件中（`core/crates/persistence/store/src/SyncOperationStore.rs:1448`）。
- `setExportFloor` 只提高导出下限不降低，已有值大于等于传入序列时直接返回（`core/crates/persistence/store/src/SyncOperationStore.rs:1014`）。
- `exportFloorFor` 未设下限的来源返回 0（`core/crates/persistence/store/src/SyncOperationStore.rs:1037`）。
- `markLocalOperationsUnexportable` 把本地设备及其 `preferences` 派生来源的当前序列设为导出下限（`core/crates/persistence/store/src/SyncOperationStore.rs:1003`）。
- `receiveOperations` 经 `storeOriginals` 把接收到的操作以 `pending` 状态存入当前 Journal（`core/crates/persistence/store/src/SyncOperationStore.rs:1958`）。
- `operationsSinceWithInventory` 在 `domains` 为空或包含 `preferences` 时先发布偏好 outbox 再读日志（`core/crates/persistence/store/src/SyncOperationStore.rs:826`）。
- 导出时跳过序列号不大于导出下限的记录（`core/crates/persistence/store/src/SyncOperationStore.rs:2081`）。
- `DEFAULT_SYNC_PAGE_BYTES` 是 4 MiB，单个同步交换页的序列化字节预算，超预算时截断但首条操作除外（见下）（`core/crates/persistence/store/src/SyncOperationStore.rs:42`）。
- `boundSyncOperationPage` 按序列化字节预算截断同步操作页（`core/crates/persistence/store/src/SyncOperationStore.rs:1647`）。
- 截断超预算页面时始终保留第一条操作，单个超大记录不阻塞导出（`core/crates/persistence/store/src/SyncOperationStore.rs:1658`）。

### 实体版本与冲突顺序

- 已应用的实体版本存在 {root}/entity_versions.jsonl 文件中，每行一条 JSON（`core/crates/persistence/store/src/SyncOperationStore.rs:1442`）。
- `syncEntityVersionKey` 把操作身份编码为 `domain`、`entityType`、`entityId` 三元组的 JSON 字符串（`core/crates/persistence/store/src/SyncOperationStore.rs:1700`）。
- SyncOperationOrder 的 `fromOperation` 对 `contractVersion` 为 1 的 `preferences` 操作取 `payload` 的 `logicalTime`，对带 `initial` 标记的 `runtime_file` 操作取 1，其余操作取 `createdAt`（`core/crates/persistence/store/src/SyncOperationStore.rs:330``core/crates/persistence/store/src/SyncOperationStore.rs:339`）。
- `shouldApplyOperations` 比较新操作与已记录的实体版本（`core/crates/persistence/store/src/SyncOperationStore.rs:1100`）。
- 新操作只在顺序大于已记录版本时才应用，未知实体默认应用（`core/crates/persistence/store/src/SyncOperationStore.rs:1115`）。
- `recordAppliedOperations` 把已应用的操作批量记入实体版本日志（`core/crates/persistence/store/src/SyncOperationStore.rs:1136`）。
- 顺序不大于已记录版本的操作被跳过，不写入实体版本日志（`core/crates/persistence/store/src/SyncOperationStore.rs:1153`）。
- 导出时非 `preferences` 域的 `EntityState` 操作每实体只导出最新一条胜者（`core/crates/persistence/store/src/SyncOperationStore.rs:2100`）。
- `compactSyncOperations` 压缩同步操作页，保留 `preferences` 历史用于身份重放（`core/crates/persistence/store/src/SyncOperationStore.rs:1667``core/crates/persistence/store/src/SyncOperationStore.rs:1679`）。
- 压缩时保留全部 `preferences` 域操作与全部 `Transaction` 语义操作，`EntityState` 语义每实体只保留最新序列（`core/crates/persistence/store/src/SyncOperationStore.rs:1670``core/crates/persistence/store/src/SyncOperationStore.rs:1682`）。

### 内容寻址 blob

- `RuntimeFileSyncReference` 由 `contentHash` 与 `size` 两个字段组成（`core/crates/persistence/store/src/SyncBlobIo.rs:9`）。
- `validateContentHash` 要求内容哈希是 64 字符的小写十六进制 SHA-256（`core/crates/persistence/store/src/SyncBlobIo.rs:24`）。
- `verifyBlob` 校验引用声明的大小与内容的 SHA-256 哈希是否一致（`core/crates/persistence/store/src/SyncBlobIo.rs:32`）。
- `BUFFER_BYTES` 是 64 KiB，同步 blob 的流式读写按该大小分块（`core/crates/persistence/store/src/SyncBlobIo.rs:66`）。
- `write_json` 在引用大小不大于 64 KiB 时一次性原子写，否则走流式写入会话（`core/crates/persistence/store/src/SyncBlobIo.rs:90`）。
- `write_stream` 经写入会话流式写 blob，边写边算 SHA-256（`core/crates/persistence/store/src/SyncBlobIo.rs:100`）。
- 流式写入完成后校验总字节数与哈希，不符则报错且不提交写入会话（`core/crates/persistence/store/src/SyncBlobIo.rs:119`）。
- `read_json` 流式读取 blob 并在读完后校验哈希与大小（`core/crates/persistence/store/src/SyncBlobIo.rs:142`）。
- `transaction_reference` 从任意操作的 `payload` 的 `transactionBlob` 取引用，`payload` 非单键对象时报错（`core/crates/persistence/store/src/SyncBlobIo.rs:47`）。
- `verify_transaction` 在已下载事务 blob 的头部与信封不一致时报错，比较时把双方 `payload` 置空（`core/crates/persistence/store/src/SyncBlobIo.rs:56`）。

### 运行时文件同步存储

- `RUNTIME_FILE_SYNC_DOMAIN` 的值是 `runtime_file`（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:15`）。
- `isCompleteState` 要求 `domain` 为 `runtime_file`、`entityType` 为 `file`、`semantics` 为 `EntityState`、操作为 `upsert` 或 `delete`（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:61``core/crates/persistence/store/src/RuntimeFileSyncStore.rs:15`）。
- `RuntimeFileSnapshot` 由扁平化的 blob 引用与可选的 `modifiedAt` 组成（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:23`）。
- `FileCoverage` 由 `owner` 与 `covered` 集合组成，失败方只提供覆盖证明而不重发业务内容（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:42`）。
- `FileCorrectionReference` 由 `source`、`superseded` 与 `skipped` 集合组成，`skipped` 只记录确切失败的原始文件（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:50`）。
- `recordSnapshot` 由文件内容直接算引用后以本地设备号追加本地操作，`initial` 时设备号加 `:initial` 后缀（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:120`）（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:130`）。
- `recordDeletion` 只追加 `payload` 为 null 的 `delete` 操作，不动本地文件（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:204``core/crates/persistence/store/src/RuntimeFileSyncStore.rs:216`）。
- `writeBlob` 先校验引用再写 blob（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:404`）。
- `readBlob` 读完 blob 后校验哈希与大小（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:454`）。
- `storeBlob` 计算内容的 SHA-256 并写入 blobs/{hash}，返回引用（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:423`）。
- `blobPath` 校验哈希后返回 {syncRoot}/blobs/{hash}（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:524`）。
- `hasBlob` 校验引用后查 blob 是否存在，不存在时再查 live 文件源是否能提供，不读内容也不哈希（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:391`）。
- `readBlobChunk` 在 `offset` 或 `length` 为负时报错（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:397`）。
- `requiredBlob` 对任意操作先取 `transaction_reference`，无引用时非 runtime_file 域或非 Space 所有权返回 `None`，`upsert` 从 `payload` 解析引用，`delete` 返回 `None`（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:318`）（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:336`）。
- 非 `file` 的 `entityType` 在取 blob 引用时报错（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:332`）。
- `prepareTransactionForTransport` 对无 `transaction_reference` 且序列化后大于 32 KiB 的操作，把载荷换成 `transactionBlob` 信封（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:345`）。
- 操作大小超过 32 KiB 时 `payload` 换成只含 `transactionBlob` 引用的小信封（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:352`）。
- `hydrateTransaction` 对无 `transaction_reference` 的操作原样返回，`initialize`/`initialization` 的 `chat` 与 `plugin_storage` 域不读 blob，其余带引用的操作从 blob 还原并校验头部（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:357`）。
- `requireSpaceFile` 拒绝未注册为 Space 同步的文件进入运行时文件同步（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:537`）。
- `upsert` 操作读 blob 写文件、恢复 `modifiedAt` 并 `flush` 文件（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:300`）。
- `delete` 操作只在文件存在时删除，其他操作报错（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:309`）。
- `writeSnapshot` 把显式变更与初始种子走同一文件同步路径（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:100`）。
- `writeSnapshot` 在 `initial` 且已有快照时直接返回，不重复写（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:102`）。
- 插件数据库文件拒绝进入文件同步，要求用记录级存储操作（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:110`）。
- `trackChanges` 在变更前后各抓一次文件快照（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:223`）。
- 变化的文件记录新快照，消失的文件记录删除（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:232`）。
- `resetTransactions` 重新发布当前字节与删除 `tombstone`（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:145`）。
- 重新发布后收回已被替换的文件历史（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:166`）。

### 工作区文件同步存储

- `MANAGED_ROOTS` 是 `workspaces`、聊天输出目录与旧版聊天附件目录三个托管根（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:22`）。
- WorkspaceFileSyncStore 的 `owns` 要求 `domain` 为 `runtime_file` 且路径被 `manages` 覆盖（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:92``core/crates/persistence/store/src/RuntimeFileSyncStore.rs:15`）。
- WorkspaceFileSyncStore 的 `manages` 要求路径以托管根加斜杠开头（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:98`）。
- `affectedBy` 覆盖托管路径及其祖先与后代路径（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:104`）。
- 工作区清单存在 {root}/workspace_inventory.json 文件中（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:188`）。
- `ScanState` 由 `files`、`references`、`deferred`、`pending` 四部分组成（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:49`）。
- `scan` 只遍历托管根，不查挂载的 VFS 目录（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:110`）。
- `prepareSpaceJoin` 在加入 Space 前恢复未完成写入（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:125`）。
- 加入 Space 时本地文件保留，只重新清点清单，避免本设备独有的文件被 `stranded`（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:124`）。
- 加入 Space 时工作区清单重置为 `ScanState::default()`（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:134`）。
- `trackPaths` 在变更前校验路径属于托管范围并提交重扫意图，不再在变更前后各扫描一次工作区（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:144`）。
- `applyOperation` 在落库后把操作追加到操作日志（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:486`）。
- `materializeOperations` 对非 `file` 实体或非本页拥有的操作报错（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:502`）。
- `materializeOperations` 在 `bootstrap` 时跳过 `shouldApplyOperation` 判断（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:499``core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:519`）。
- `applyUnlocked` 先标记恢复状态，再经 `applyToState` 把 `upsert` 解释为快照、`delete` 解释为空，其他操作报错（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:597` `core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:605`）。
- 策略拒绝或目标检查失败的传入状态存入 `deferred`，不丢弃（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:613`）。
- `wantsBlob` 按策略判断一个 `upsert` 操作是否需要其 blob（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:628`）。
- `deferredBlobs` 返回策略变化后重新符合条件的已延迟文件的引用（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:635`）。
- `recoverPending` 在任何扫描前先完成中断的传入写入（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:690`）。
- `finishPending` 先写已验证的字节，再提交清单（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:707`）。
- `writePending` 的 `upsert` 写字节、恢复 `modifiedAt` 并 `flush` 文件（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:608``core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:734`）。
- `writePending` 的 `delete` 只在文件存在时删除（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:729``core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:742`）。
- `checkDestination` 拒绝目标路径上的符号链接与文件/目录类型冲突（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:769`）。
- `managedDirectory` 取托管根下的第一段目录作为文件所属目录（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:810`）。
- `managedVfsPath` 把 `workspaces/` 映射为 `/operitapp/workspaces/`，聊天输出映射为 `/operitapp/outputs/`，`runtime/` 映射为 `/operitapp/data/`（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:821`）。
- `validatePath` 要求托管路径属于 Space 所有权（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:825`）。
- `captureReference` 为超限文件写 `.operit-ref.json` 边车保存 `FileReference`（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:427``core/crates/persistence/store/src/FileSyncPolicy.rs:12`）。
- 超限大文件只同步边车引用，原始大文件留在来源节点（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:294`）。

### 文件同步策略

- `POLICY_PATH` 是 `.operit/sync.json`（`core/crates/persistence/store/src/FileSyncPolicy.rs:11`）。
- `REFERENCE_SUFFIX` 是 `.operit-ref.json`（`core/crates/persistence/store/src/FileSyncPolicy.rs:12`）。
- `MAX_POLICY_BYTES` 是 256 KiB，策略文件与忽略文件读取不超过该上限（`core/crates/persistence/store/src/FileSyncPolicy.rs:13`）。
- 默认策略的 `exclude` 含 `.git/`、`node_modules/`、`target/`、`build/`、`dist/`、`.dart_tool/`、`.gradle/`、`__pycache__/`（`core/crates/persistence/store/src/FileSyncPolicy.rs:33`）。
- 默认策略的 `maxFileBytes` 与 `maxTotalBytes` 取布局默认值（`core/crates/persistence/store/src/FileSyncPolicy.rs:43`）。
- 策略文件不存在时 `load` 返回默认策略（`core/crates/persistence/store/src/FileSyncPolicy.rs:49`）。
- 策略 `version` 不是 1 时 `load` 报错（`core/crates/persistence/store/src/FileSyncPolicy.rs:49``core/crates/persistence/store/src/FileSyncPolicy.rs:62`）。
- `ensure` 只在策略文件不存在时写入默认策略，已存在不覆盖（`core/crates/persistence/store/src/FileSyncPolicy.rs:73`）。
- `readLimited` 分块读取并在超过上限时报错（`core/crates/persistence/store/src/FileSyncPolicy.rs:153`）。
- `validateRelative` 拒绝空路径、绝对路径、反斜杠、冒号、NUL、空段、单点与双点段（`core/crates/persistence/store/src/FileSyncPolicy.rs:183`）。
- `isControl` 把策略文件本身与 `.operit` 目录判定为控制路径，恒被包含（`core/crates/persistence/store/src/FileSyncPolicy.rs:229`）。
- `FileReference` 含 `nodeId`、`path`、`fileName`、`fileSize` 与可选的 `modifiedAt`（`core/crates/persistence/store/src/FileSyncPolicy.rs:240`）。
- `FileReference` 的 `format` 是 `operit_file_reference`，`version` 是 1（`core/crates/persistence/store/src/FileSyncPolicy.rs:235``core/crates/persistence/store/src/FileSyncPolicy.rs:266`）。
- FileReference 的 `validate` 要求路径以 `/app/`、`/operitapp/`、`/mnt/`、`/virtual/` 之一开头（`core/crates/persistence/store/src/FileSyncPolicy.rs:266`）。

### 偏好合并声明与规则

- `isMergeMetadata` 要求 `domain` 为 `preferences`，且操作为 `alias`，或 `payload` 或 `entries` 中含合并声明键或插件偏好 schema 键（`core/crates/persistence/store/src/PreferenceMerge.rs:21`）。
- PreferenceMergeStore 的 `values` 声明 `version` 为 1，无 `catalog`、无 `references`、无 `projection`（`core/crates/persistence/store/src/PreferenceMerge.rs:45``core/crates/persistence/store/src/PreferenceMerge.rs:52`）。
- PreferenceMergeSchema 的 `owner` 先查原生注册，再查 `CoreSpaceStore`，再查插件偏好路径（`core/crates/persistence/store/src/PreferenceMerge.rs:72`）。
- `validateDeclaration` 要求声明 `version` 为 1，`references` 不超过 256 条（`core/crates/persistence/store/src/PreferenceMerge.rs:118`）。
- `catalog` 声明要求 `key_prefix`、`identity_field`、`name_field` 非空，`identity_field` 不等于 `name_field`，`ignored_fields` 不含 `name_field` 且不超过 64，`retired_keys` 不超过 64（`core/crates/persistence/store/src/PreferenceMerge.rs:127`）。
- `reference` 声明要求 `target` 以 `.preferences.json` 结尾、以 `runtime/` 开头，`path` 不超过 32 段（`core/crates/persistence/store/src/PreferenceMerge.rs:136`）。
- 偏好合并 `schema` 的聚合上限是 `catalogs` 不超过 64、`references` 不超过 256、`projectionCount` 不超过 64（`core/crates/persistence/store/src/PreferenceMerge.rs:188`）。
- 同一偏好合并 `schema` 中重复的存储路径被拒绝（`core/crates/persistence/store/src/PreferenceMerge.rs:178`）。
- `combineDeclarations` 只在版本、`catalog`、`projection` 相同且较长声明的 `references` 以较短声明开头时合并，取较长者（`core/crates/persistence/store/src/PreferenceMerge.rs:244`）。
- `applyIndependentOperations` 让每个数据集独立提交与独立失败，不共享提交或失败边界（`core/crates/persistence/store/src/PreferenceMerge.rs:269`）。
- `PreferenceMergeOutcome` 由 `paths`、`operations`、`skipped`、`result` 四个字段组成（`core/crates/persistence/store/src/PreferenceMerge.rs:260`）。
- `declaredAliases` 只解析已记录的别名决策，不从内容推断身份（`core/crates/persistence/store/src/PreferenceMerge.rs:436`）。
- `resolveIdentity` 沿别名链传递解析，遇到循环报错（`core/crates/persistence/store/src/PreferenceMerge.rs:852`）。
- `referenceKey` 的格式是路径加分隔符加身份（`core/crates/persistence/store/src/PreferenceMerge.rs:869`）。
- `rewriteReferenceValue` 按 `Field`、`ObjectValues`、`ArrayValues`、`Variant`、`Identity` 路径段逐级改写引用（`core/crates/persistence/store/src/PreferenceMerge.rs:793``core/crates/persistence/store/src/PreferenceMerge.rs:813``core/crates/persistence/store/src/PreferenceMerge.rs:823``core/crates/persistence/store/src/PreferenceMerge.rs:832`）。
- `Identity` 路径段必须在路径末尾（`core/crates/persistence/store/src/PreferenceMerge.rs:837`）。
- `keyMatches` 排除 `retired_keys`，要求身份非空（`core/crates/persistence/store/src/PreferenceMerge.rs:761`）。
- `nameRecords` 用 `uniqueNames` 分配确定性显示名，保留稳定的实体身份（`core/crates/persistence/store/src/PreferenceMerge.rs:723``core/crates/persistence/store/src/PreferenceMerge.rs:740`）。
- `currentRecords` 读取属于一个声明配置目录的当前记录（`core/crates/persistence/store/src/PreferenceMerge.rs:687`）。
- 记录的身份字段必须与键名一致（`core/crates/persistence/store/src/PreferenceMerge.rs:705`）。
- `writeRecords` 先删除旧记录与 `retired` 键，再写规范记录（`core/crates/persistence/store/src/PreferenceMerge.rs:771``core/crates/persistence/store/src/PreferenceMerge.rs:784`）。
- `canonicalContent` 排除身份字段与声明的忽略字段后比较完整的 JSON 内容（`core/crates/persistence/store/src/MergeRules.rs:6`）。
- `canonicalValue` 把对象键按 `BTreeMap` 排序，保留数组顺序作为业务数据（`core/crates/persistence/store/src/MergeRules.rs:18`）。
- `uniqueNames` 在名字冲突时加全角括号数字后缀，并跳过已被保留的名字（`core/crates/persistence/store/src/MergeRules.rs:33`）。

### 应用后通知

- SyncAppliedChanges 的订阅按存储 host 身份过滤，只接收同一 host 的变更（`core/crates/persistence/store/src/SyncAppliedChanges.rs:30`）。
- SyncAppliedChanges 的 `publish` 在变更为空时直接返回，且只在数据与同步时钟提交后、在 `store` 锁之外调用（`core/crates/persistence/store/src/SyncAppliedChanges.rs:47`）。
- 监听器 `panic` 被捕获并记日志，已提交的数据不受影响（`core/crates/persistence/store/src/SyncAppliedChanges.rs:58`）。

## 关键符号

- `SyncOperation` — 一条同步操作，11 个字段（`core/crates/persistence/store/src/SyncOperationStore.rs:245`）
- `SyncOperationSemantics` — `EntityState` 或 `Transaction` 两种操作语义（`core/crates/persistence/store/src/SyncOperationStore.rs:211`）
- `SyncOperationStore` — 操作日志、时钟、实体版本与导出下限的存储入口（`core/crates/persistence/store/src/SyncOperationStore.rs:427`）
- `SyncClock` — 按设备记录已知最后序列号的向量时钟（`core/crates/persistence/store/src/SyncOperationStore.rs:45`）
- `SyncReceipt` — 按来源记录确切已收区间的回执（`core/crates/persistence/store/src/SyncOperationStore.rs:121`）
- `SyncOperationOrder` — 并发实体操作的确定性冲突顺序（`core/crates/persistence/store/src/SyncOperationStore.rs:316`）
- `NewSyncOperation` — 新建本地操作时提交的域、实体与载荷（`core/crates/persistence/store/src/SyncOperationStore.rs:352`）
- SyncOperationStore 的 `appendLocalOperation` — 追加本地操作并分配序列号（`core/crates/persistence/store/src/SyncOperationStore.rs:1881`）
- SyncOperationStore 的 `operationsSinceWithInventory` — 按导出下限与实体胜者裁剪同步页（`core/crates/persistence/store/src/SyncOperationStore.rs:826`）
- SyncOperationStore 的 `receiveOperations` — 接收到的操作以 `pending` 状态存入日志（`core/crates/persistence/store/src/SyncOperationStore.rs:1958`）
- SyncOperationStore 的 `localDeviceId` — 生成或读取本地设备标识（`core/crates/persistence/store/src/SyncOperationStore.rs:783`）
- SyncOperationStore 的 `scanOperationLog` — 逐行分类遗留 JSONL 操作日志的可解码与损坏行（`core/crates/persistence/store/src/SyncOperationStore.rs:1306`）
- SyncOperationStore 的 `quarantineOperationLines` — 只处理遗留 JSONL 日志，把损坏行移入隔离边车（`core/crates/persistence/store/src/SyncOperationStore.rs:1483`）
- SyncOperationStore 的 `preferenceDatasets` — 列出已注册的偏好数据集（`core/crates/persistence/store/src/SyncOperationStore.rs:903`）
- SyncOperationStore 的 `preferenceMergeHistory` — 只读跨数据集的合并声明与身份决策（`core/crates/persistence/store/src/SyncOperationStore.rs:871`）
- SyncOperationStore 的 `preferenceHistory` — 返回偏好域的穷尽历史（`core/crates/persistence/store/src/SyncOperationStore.rs:855`）
- `RuntimeFileSyncReference` — 内容哈希加大小的 blob 引用（`core/crates/persistence/store/src/SyncBlobIo.rs:9`）
- SyncBlobIo 的 `validateContentHash` — 校验 64 字符小写十六进制 SHA-256（`core/crates/persistence/store/src/SyncBlobIo.rs:24`）
- SyncBlobIo 的 `verifyBlob` — 校验引用声明的大小与内容的 SHA-256（`core/crates/persistence/store/src/SyncBlobIo.rs:32`）
- SyncBlobIo 的 `write_json` — 小 blob 原子写、大 blob 流式写（`core/crates/persistence/store/src/SyncBlobIo.rs:90`）
- SyncBlobIo 的 `read_json` — 流式读取 blob 并校验哈希与大小（`core/crates/persistence/store/src/SyncBlobIo.rs:142`）
- SyncBlobIo 的 `transaction_reference` — 从任意操作的 `transactionBlob` 取引用（`core/crates/persistence/store/src/SyncBlobIo.rs:47`）。
- SyncBlobIo 的 `verify_transaction` — 校验已下载事务 blob 的头部与信封一致（`core/crates/persistence/store/src/SyncBlobIo.rs:56`）。
- SyncAppliedChanges 的 `subscribe` — 按存储 host 身份订阅提交后通知（`core/crates/persistence/store/src/SyncAppliedChanges.rs:30`）
- SyncAppliedChanges 的 `publish` — 数据与时钟提交后通知监听器（`core/crates/persistence/store/src/SyncAppliedChanges.rs:47`）
- MergeRules 的 `canonicalContent` — 排除身份与忽略字段后比较完整 JSON 内容（`core/crates/persistence/store/src/MergeRules.rs:6`）
- MergeRules 的 `canonicalValue` — 对象键排序、数组顺序保留的规范化 JSON（`core/crates/persistence/store/src/MergeRules.rs:18`）
- MergeRules 的 `uniqueNames` — 冲突时加全角括号数字后缀分配显示名（`core/crates/persistence/store/src/MergeRules.rs:33`）
- `RuntimeFileSyncStore` — 运行时文件的快照、blob 与删除 tombstone 存储（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:33`）
- `RuntimeFileSnapshot` — 扁平化 blob 引用加可选 `modifiedAt` 的文件快照（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:23`）
- `FileCoverage` — 失败方提供的覆盖证明（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:42`）
- `FileCorrectionReference` — 胜出文件与其取代的历史覆盖（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:50`）
- RuntimeFileSyncStore 的 `recordSnapshot` — 由内容算引用并以本地设备号追加本地操作（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:120`）。
- RuntimeFileSyncStore 的 `recordDeletion` — 追加 `payload` 为 null 的 `delete` 操作（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:204``core/crates/persistence/store/src/RuntimeFileSyncStore.rs:216`）
- RuntimeFileSyncStore 的 `storeBlob` — 计算 SHA-256 并写入 blobs/{hash}（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:423`）
- RuntimeFileSyncStore 的 `readBlob` — 读完 blob 后校验哈希与大小（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:454`）
- RuntimeFileSyncStore 的 `hasBlob` — 查 blob 是否存在，不存在时查 live 文件源（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:391`）。
- RuntimeFileSyncStore 的 `requiredBlob` — 取一个操作所需的 blob 引用（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:318`）
- RuntimeFileSyncStore 的 `prepareTransactionForTransport` — 大操作改走 blob 传输（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:345`）。
- RuntimeFileSyncStore 的 `hydrateTransaction` — 从 blob 还原带引用的操作（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:357`）。
- RuntimeFileSyncStore 的 `applySyncedOperation` — 落库一个已验证的运行时文件操作（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:280`）
- `WorkspaceFileSyncStore` — 托管工作区文件的清单、延迟与待完成写入存储（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:59`）
- WorkspaceFileSyncStore 的 `scan` — 只遍历托管根的清单扫描（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:110`）
- WorkspaceFileSyncStore 的 `prepareSpaceJoin` — 加入 Space 前恢复未完成写入并重置清单（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:125`）
- WorkspaceFileSyncStore 的 `materializeOperations` — 批量落库工作区文件操作（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:499`）
- WorkspaceFileSyncStore 的 `deferredBlobs` — 返回策略变化后重新符合条件的已延迟文件引用（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:635`）
- WorkspaceFileSyncStore 的 `managedDirectory` — 取托管根下的第一段目录（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:810`）
- WorkspaceFileSyncStore 的 `managedVfsPath` — 托管路径到 VFS 路径的映射（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:821`）
- `FileSyncPolicy` — 工作区与会话文件的用户可编辑同步策略（`core/crates/persistence/store/src/FileSyncPolicy.rs:17`）
- FileSyncPolicy 的 `load` — 读策略文件，不存在返回默认（`core/crates/persistence/store/src/FileSyncPolicy.rs:49`）
- FileSyncPolicy 的 `ensure` — 只在策略文件不存在时写入默认策略（`core/crates/persistence/store/src/FileSyncPolicy.rs:73`）
- `FileReference` — 超限大文件的定位引用（`core/crates/persistence/store/src/FileSyncPolicy.rs:240`）
- `PreferenceMergeStore` — 一个偏好数据集的合并声明持有者（`core/crates/persistence/store/src/PreferenceMerge.rs:31`）
- `PreferenceMergeSchema` — 偏好合并声明所属存储的集合（`core/crates/persistence/store/src/PreferenceMerge.rs:61`）
- PreferenceMergeSchema 的 `owner` — 解析一个偏好路径的归属声明（`core/crates/persistence/store/src/PreferenceMerge.rs:72`）
- PreferenceMerge 的 `applyIndependentOperations` — 每个数据集独立提交与独立失败（`core/crates/persistence/store/src/PreferenceMerge.rs:269`）
- `PreferenceMergeOutcome` — 一个数据集的合并结果（`core/crates/persistence/store/src/PreferenceMerge.rs:260`）
- PreferenceMerge 的 `declaredAliases` — 只解析已记录的别名决策（`core/crates/persistence/store/src/PreferenceMerge.rs:436`）
- PreferenceMerge 的 `resolveIdentity` — 沿别名链传递解析身份（`core/crates/persistence/store/src/PreferenceMerge.rs:852`）
- PreferenceMerge 的 `referenceKey` — 路径加分隔符加身份的命名空间键（`core/crates/persistence/store/src/PreferenceMerge.rs:869`）

## 调用链

1. 本地写操作：`appendLocalOperation` 分配序列号并把操作追加到当前 Journal，`opId` 是 `originDeviceId` 与序列号以冒号连接（`core/crates/persistence/store/src/SyncOperationStore.rs:1885`）。
2. 时钟推进：`observeOperations` 只在操作序列大于已知序列时推进本地时钟并写回 `clocks.json`（`core/crates/persistence/store/src/SyncOperationStore.rs:1182``core/crates/persistence/store/src/SyncOperationStore.rs:1193``core/crates/persistence/store/src/SyncOperationStore.rs:1424`）。
3. 导出裁剪：`operationsSinceWithInventory` 在 `domains` 为空或包含 `preferences` 时先发布偏好 outbox 再读日志（`core/crates/persistence/store/src/SyncOperationStore.rs:826`）。
4. 导出裁剪：导出时跳过序列号不大于导出下限的记录（`core/crates/persistence/store/src/SyncOperationStore.rs:2081`）。
5. 导出裁剪：非 `preferences` 域的 `EntityState` 操作每实体只导出最新一条胜者（`core/crates/persistence/store/src/SyncOperationStore.rs:2100`）。
6. 大操作传输：操作大小超过 32 KiB 时 `payload` 换成只含 `transactionBlob` 引用的小信封（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:352`）。
7. 接收落库：`receiveOperations` 把接收到的操作以 `pending` 状态存入当前 Journal（`core/crates/persistence/store/src/SyncOperationStore.rs:1958`）。
8. 实体版本记录：`recordAppliedOperations` 把已应用的操作批量记入实体版本日志（`core/crates/persistence/store/src/SyncOperationStore.rs:1136`）。
9. 文件快照：`recordSnapshot` 由文件内容直接算引用后以本地设备号追加本地操作，`initial` 时设备号加 `:initial` 后缀（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:120`）（`core/crates/persistence/store/src/RuntimeFileSyncStore.rs:130`）。
10. 工作区扫描：`scan` 只遍历托管根，不查挂载的 VFS 目录（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:110`）。
11. 工作区落库：`finishPending` 先写已验证的字节，再提交清单（`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:707`）。
12. 提交后通知：SyncAppliedChanges 的 `publish` 在变更为空时直接返回，且只在数据与同步时钟提交后、在 `store` 锁之外调用（`core/crates/persistence/store/src/SyncAppliedChanges.rs:47`）。

## 来源

- `core/crates/persistence/store/src/SyncOperationStore.rs`
- `core/crates/persistence/store/src/SyncBlobIo.rs`
- `core/crates/persistence/store/src/SyncAppliedChanges.rs`
- `core/crates/persistence/store/src/MergeRules.rs`
- `core/crates/persistence/store/src/PreferenceMerge.rs`
- `core/crates/persistence/store/src/WorkspaceFileSyncStore.rs`
- `core/crates/persistence/store/src/RuntimeFileSyncStore.rs`
- `core/crates/persistence/store/src/FileSyncPolicy.rs`
- `core/crates/persistence/store/src/transaction/Journal.rs`
