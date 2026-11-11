---
title: 持久化同步（总览）
module: arch
platforms: [all]
sources: [docs/sync-architecture.md, docs/transaction-model.md, docs/transaction-sync-contract.md]
date: 2026-11-11
---

## 概述

持久化同步是同一 Space 内具备 `storage.provide` 且提供 Core 存储服务的节点之间交换持久化操作与 Blob 的机制（`docs/sync-architecture.md:3`）。配对、成员资格、路由可达性和存储授权分别校验（`docs/sync-architecture.md:3`）。

业务修改以事务为单位原子提交，由后来修改生效；最终同步后，两个文件一致（`docs/transaction-sync-contract.md:6`）。

本页是总览：只讲同步的职责分工、数据路径、事务模型与强制校正的判定条件。偏好重放、文件同步、发现配对、协议版本的机制细节见第 7 章多设备同步（[[sync-overview|同步总览]]、[[sync-transaction-model|事务模型与同步契约]]、[[sync-workspace-files|工作区文件同步与 .operit/sync.json]]、[[sync-protocol-version|协议版本与构建指纹]]）。

## AI 速览

`SpacePersistenceSyncService` — 授权、交换、分页、Blob 与调度（`docs/sync-architecture.md:17`）
`SyncOperationStore` — 原始操作、身份指纹、接收凭据与日志查询（`docs/sync-architecture.md:18`）
`PreferenceMerge` — 偏好 owner 声明与物化协调（`docs/sync-architecture.md:19`）
`PreferencesDataStore` — 单数据集工作副本与原子提交（`docs/sync-architecture.md:20`）
`Transaction::compaction` — 公共合并函数，Preference 同步用它选择有效事务（`docs/sync-architecture.md:127`）
`Transaction.rs` — 事务模型的实现入口（`docs/transaction-model.md:189`）

主入口：`SpacePersistenceSyncService`，负责授权、交换、分页、Blob 与调度（`docs/sync-architecture.md:17`）。

数据流向：本地业务变更 → 数据集原子提交 → 持久 outbox → 操作日志 → Router / PeerSync → 原始操作与接收凭据 → 数据集解码与重放计划 → 原子提交 → 通知（`docs/sync-architecture.md:8`、`docs/sync-architecture.md:12`）。

## 核心机制

### 谁参与、什么进同步

- 同一 Space 内具备 `storage.provide` 且提供 Core 存储服务的节点交换持久化操作与 Blob（`docs/sync-architecture.md:3`）。配对、成员资格、路由可达性和存储授权分别校验（`docs/sync-architecture.md:3`）。
- 同步目标分三类：`DataStore`、`SQL`、`File`（`docs/transaction-model.md:6`）。
- 每个偏好文件是独立数据集，一个数据集失败不能阻止独立数据集提交（`docs/sync-architecture.md:25`）。跨文件业务操作不具备单次原子性（`docs/sync-architecture.md:25`）。
- 布局状态只属于本节点，不参与 Space 同步，也不能由远端版本推进（`docs/sync-architecture.md:46`）。当前对话选择属于本机状态，各端独立保存（`docs/transaction-sync-contract.md:69`）。

### 接收与应用是两件事

- 一次接收与一次业务应用是不同事实：操作可靠保存后才能推进接收凭据，业务提交完成后才能标记已应用（`docs/sync-architecture.md:23`）。相同操作身份必须携带相同内容，重复投递幂等，内容冲突明确报错（`docs/sync-architecture.md:23`）。
- 远端保存原文后登记接收，业务原子提交后登记已应用（`docs/transaction-sync-contract.md:63`）。

### 偏好重放计划

- 偏好操作包含完整赋值、完整删除、整数增量和字段修改（`docs/sync-architecture.md:33`）。
- 完整赋值或删除重置同一根条目此前的效果（`docs/sync-architecture.md:35`）；随后的字段修改和整数增量继续生效，并满足实际依赖（`docs/sync-architecture.md:36`）。
- 原始操作身份、内容和归档记录完整保留，计算计划不改写历史（`docs/sync-architecture.md:38`）。有效操作依赖缺失时，整个数据集工作副本不提交（`docs/sync-architecture.md:41`）。
- 实体身份合并只执行已明确记录的决定，传输分页或分块结束不能授予业务合并许可（`docs/sync-architecture.md:42`）。

### 布局与迁移

- 偏好布局由节点本地的 `PreferenceLayout` 管理，迁移步骤必须可重入：先提交目标数据，再登记退役路径，最后由 DataStore 原子提交布局版本与退役声明（`docs/sync-architecture.md:44`）。
- 跨文件迁移不宣称具有跨文件原子性，失败时布局版本不推进，同步保留原待处理操作（`docs/sync-architecture.md:44`）。
- 迁移等价式要求同一规则作用于状态和事务的结果一致，存续事务保持原文（`docs/transaction-model.md:48`）。
- 收到未来格式时，原文进入待处理，升级就绪后应用（`docs/transaction-sync-contract.md:41`）。旧路径事务晚到时，按 layout 映射交给当前归属（`docs/transaction-sync-contract.md:42`）。

### 提交、outbox 与锁

- 偏好业务值和内部 `__operit_preferences_replication` 字段经 Host 原子写入一起提交（`docs/sync-architecture.md:50`）。
- 业务提交后归档原始操作，归档可靠完成后清除 outbox；归档失败保留同一操作供后续发布，业务提交失败不能产生可导出的操作（`docs/sync-architecture.md:52`）。
- 数据集锁覆盖历史收集、归档与 outbox 合并、解码、重放和提交（`docs/sync-architecture.md:54`）。

### 会话删除是终态

- 整段会话删除使用保留的 SQL 事务操作，历史行删除、删除事实与接收凭据在同一事务提交（`docs/sync-architecture.md:56`）。
- 删除事实沿用 `sync_sql_deletions`，不依赖 Space 成员或 Binding；对同一会话 ID，删除是终态而非可被后续 upsert 撤销的普通字段（`docs/sync-architecture.md:57`）。
- 数据库 28 → 29 为删除事实建立查询索引，并在同一升级事务内清除旧链路已删除却又被恢复的会话行（`docs/sync-architecture.md:61`）。
- 退出后删除、重新加入也遵守删除规则（`docs/sync-architecture.md:59`）。

### 日志、待应用记录与内存边界

- 生产日志位于 `transactions.sqlite`，聊天和插件 SQL 通过同一 source 接口导出各自的业务日志（`docs/sync-architecture.md:68`）。
- 收据、domain、数据集和水位先筛选，偏好历史与事务不进行实体状态压缩（`docs/sync-architecture.md:70`）。
- 页面按精确序列化字节数与记录数限制；单条超限记录由传输层处理（`docs/sync-architecture.md:70`）。
- `receive_state.json` 的 `formatVersion: 2` 保存收据、指纹与轻量元数据，payload 位于 `pending/<sha256(opId)>.json`（`docs/sync-architecture.md:78`）。
- 接收时先原子发布记录文件，再提交引用与收据账本；应用完成时先提交移除引用的账本，再删除记录文件（`docs/sync-architecture.md:80`）。

### 一致性比较

- 一致性清单只使用 `digest` 判断内容是否相同，所有同步设备需一起更新到 `consistencyVersion: 7`，旧协议不能完成同步（`docs/sync-architecture.md:86`）。
- 聊天 owner 比较时排除 SQLite 本地分配的 `messages.messageId` 和 `message_variants.variantId`，插件 owner 排除对象存储的本地 CAS `version`（`docs/sync-architecture.md:88`）。
- 比较范围由各端自己的本轮导出收据确定，无需两端同时采样（`docs/transaction-sync-contract.md:69`）。

### 设备对调度与 Blob

- 同一对已授权存储节点仅由 CoreNode ID 字典序较小的一端协调完整双向交换（`docs/sync-architecture.md:92`）。
- 轻量探测和完整收据使用同一个本地创作时钟、投影计数及设备偏好修订摘要（`docs/sync-architecture.md:94`）。
- Blob 引用按内容哈希和大小去重，每页每端一次批量存在性调用；传输前后仍检查存储授权，落盘后仍验证完整哈希（`docs/sync-architecture.md:96`）。

### 诊断日志

- `sync_cycle.start` 记录本轮合并的唤醒来源，周期开始不表示执行了全量快照传输（`docs/sync-architecture.md:102`）。
- `sync_gate.required` 记录进入对端同步流程的条件（`docs/sync-architecture.md:103`）。
- `sync_pass.start/done/failed` 记录目标节点、调用来源、排队与执行耗时及失败后的重试时间（`docs/sync-architecture.md:104`）。
- `sync_consistency.correct mode=full_snapshot` 记录决定进行完整文件快照修复，reason 取 `content_digest_mismatch`、`local_file_missing` 或 `remote_file_missing`（`docs/sync-architecture.md:105`）。
- `sync_consistency.snapshot/applied/deferred/done` 记录快照或覆盖凭据大小、应用结果、并发修改导致的延后和最终一致性结果，`coverageOnly=true` 表示覆盖凭据（`docs/sync-architecture.md:106`）。
- 定位重复全量时先搜索 `mode=full_snapshot`，再按目标节点和时间对照 gate 与周期来源（`docs/sync-architecture.md:108`）。

### 事务模型与合并

- 完整状态由归属与版本、值、业务修订、删除事实、身份映射、各修改范围的优先级、尚需保留的增量贡献构成；检查点另保存精确的历史覆盖集合 K（`docs/transaction-model.md:29`）。
- 普通文件以路径为原子边界，操作是带源修改时间的完整 upsert 或 delete；修改时间和大小决定文件判同（`docs/transaction-model.md:31`）。
- 字段范围独立比较优先级：父级删除 @30 后字段写入 @20 保持删除，字段写入 @50 只重建该字段需要的对象或 ID 记录容器（`docs/transaction-model.md:33`）。
- 同一归属、同一字段的绝对赋值按后来修改生效（`docs/transaction-model.md:116`）。
- 合并以整个原子事务为单位：旧事务同时修改 x、y，新事务仅覆盖 x 时，y 仍有效，旧事务整体保留（`docs/transaction-model.md:126`）。
- 两种迁移均须满足合并相容性，同时转换基线、事务和归属覆盖凭据（`docs/transaction-model.md:128`）。
- 离线端通过基线接续，已覆盖历史按空效果确认，其余修改继续按原顺序合并（`docs/transaction-model.md:135`）。
- 历史覆盖信息差异本身不触发全量（`docs/transaction-model.md:143`）。

### 强制校正

- 全量校正的前提为两端导出范围都未过期且最终内容仍不同（`docs/transaction-model.md:140`）。
- 权威内容按业务修订、节点优先序依次比较选出，直接复制权威方的完整同步文件，并在两端保存相同初始化事务（`docs/transaction-model.md:146`、`docs/transaction-model.md:150`）。
- 校正后的覆盖集合取双方已处理身份的并集，校正结果以事务合并封存（`docs/transaction-model.md:153`、`docs/transaction-model.md:160`）。
- 故障恢复是人为规定的权威替换，允许权威内容不同于损坏历史的重放结果（`docs/transaction-model.md:166`、`docs/transaction-model.md:173`）。
- 本轮完成蕴含两端迁移、事务处理及对应校验协议均就绪且内容相等；全量校正后两端具有同一条初始化事务（`docs/transaction-model.md:178`、`docs/transaction-model.md:184`）。
- 内容仍不一致说明事务链路已有损坏，直接复制较新方的完整同步文件及检查点，沿用源业务修订；缺失文件一并补齐（`docs/transaction-sync-contract.md:70`）。
- 校正落地时两端保存相同的整文件初始化事务，覆盖范围取双方已处理身份的并集，并删除已封存的旧载荷（`docs/transaction-sync-contract.md:71`）。

## 关键符号

- `SpacePersistenceSyncService` — 授权、交换、分页、Blob 与调度（`docs/sync-architecture.md:17`）
- `SyncOperationStore` — 原始操作、身份指纹、接收凭据与日志查询（`docs/sync-architecture.md:18`）
- `PreferenceMerge` — 偏好 owner 声明与物化协调（`docs/sync-architecture.md:19`）
- `PreferencesDataStore` — 单数据集工作副本与原子提交（`docs/sync-architecture.md:20`）
- `PreferenceLayout` — 节点本地的偏好布局管理，管文件的创建、设置所有权转移和旧路径退役（`docs/sync-architecture.md:44`）
- `Transaction::compaction` — 公共合并函数，Preference 同步用它选择有效事务（`docs/sync-architecture.md:127`）
- `Transaction.rs` — 事务模型的实现入口（`docs/transaction-model.md:189`）
- `receive_state.json` — formatVersion 2 的待应用记录账本，payload 按操作 ID 哈希分文件存放（`docs/sync-architecture.md:78`）
- `transactions.sqlite` — 生产日志数据库（`docs/sync-architecture.md:68`）
- `sync_sql_deletions` — 删除事实的沿用表（`docs/sync-architecture.md:57`）
- `__operit_preferences_replication` — 偏好内部复制字段，保存初始值导入标记、来源 epoch/序号、逻辑时间、已应用指纹及待归档 outbox（`docs/sync-architecture.md:50`）
- `consistencyVersion: 7` — 一致性协议版本，所有同步设备需一起更新到该版本（`docs/sync-architecture.md:86`）

## 调用链

1. 本地业务变更 → 数据集原子提交 → 持久 outbox → 操作日志（`docs/sync-architecture.md:8`）
2. 操作日志经 Router / PeerSync 到达对端（`docs/sync-architecture.md:8`）
3. 对端按原始操作与接收凭据解码并计算重放计划 → 原子提交 → 通知（`docs/sync-architecture.md:12`）
4. 接收时先原子发布记录文件，再提交引用与收据账本；应用完成时先提交移除引用的账本，再删除记录文件（`docs/sync-architecture.md:80`）
5. 业务提交后归档原始操作，归档可靠完成后清除 outbox（`docs/sync-architecture.md:52`）
6. 两端完成迁移和本轮增量交换后比较最终同步内容；内容仍有差异时以业务更新较新的一方为权威，强制校正并保存同一条初始化事务，再比较确认一致（`docs/transaction-sync-contract.md:8`）
7. 断开重连后，离线端通过基线接续，已覆盖历史按空效果确认，其余修改继续按原顺序合并（`docs/transaction-model.md:135`）

## 来源

- docs/sync-architecture.md（131 行，全文已读）
- docs/transaction-model.md（189 行，全文已读）
- docs/transaction-sync-contract.md（75 行，全文已读）

注：`docs/sync-architecture.md:3` 引用了 `docs/edge-architecture.md`，该文件在基线 364d1d594 上不存在，本页未采用其中关于 Edge 控制状态边界的说法。
