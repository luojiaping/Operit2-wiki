---
title: 事务模型与同步契约
module: sync
platforms: [all]
sources: [3]
date: 2026-11-11
---

## 概述

- 业务修改以事务为单位原子提交，由后来修改生效，最终同步后两个文件一致。`docs/transaction-sync-contract.md:6`
- 文档将 f 定义为 DataStore、SQL 与 File 三类载体的带类型标记并集。`docs/transaction-model.md:6`
- 代码的 `Backend` 只有 `DataStore` 与 `Sql` 两项，未含 File。`core/crates/persistence/store/src/Transaction.rs:88`
- `Transaction` 的字段为 `id`、`revision`、`target` 与 `edits`。`core/crates/persistence/store/src/Transaction.rs:329`
- `Transaction` 的 `backend` 恒返回 `Sql`，事务自身始终是 SQL 数据。`core/crates/persistence/store/src/Transaction.rs:338`
- `merge` 将两端事务按统一顺序和规则计算为一致的业务状态。`docs/transaction-sync-contract.md:20`
- 同步总览与参与节点见 [[sync-overview|同步总览：Space 持久化同步]]。`docs/transaction-model.md:189`

## AI 速览

- `Transaction` — 一条带固定身份、顺序、目标与操作的原子修改。`core/crates/persistence/store/src/Transaction.rs:329`
- `History` — 保存事务原文的集合，同身份事务须与已存原文一致。`core/crates/persistence/store/src/Transaction.rs:1046`
- `Data` — 完整业务状态，含 `owner` 与 `values`。`core/crates/persistence/store/src/Transaction.rs:351`
- `Migrations` — 格式与 layout 迁移表，含 `owners`、`layouts` 与 `formats`。`core/crates/persistence/store/src/Transaction.rs:977`
- `Rule` — 含 `RenameKey` 与 `RenameField` 两种重命名规则。`core/crates/persistence/store/src/Transaction.rs:632`
- Rule — 含 `SplitObject`、`DropKey` 与 `SplitRecords` 三种结构规则。`core/crates/persistence/store/src/Transaction.rs:647`
- `Snapshot` — 快照，字段为 `node`、`data`、`covered` 与 `generation`。`core/crates/persistence/store/src/Transaction.rs:1198`
- `Manifest` — 有线比较视图，字段为 `owner`、`node`、`revision`、`token` 与 `digest`。`core/crates/persistence/store/src/Transaction.rs:1267`
- `Correction` — 合并两端 `covered` 的校正结果。`core/crates/persistence/store/src/Transaction.rs:1339`
- `Replay` — 重放结果，含 `data`、`applied` 与 `pending` 三个字段。`core/crates/persistence/store/src/Transaction.rs:1170`
- `Edit` 的 `Set` — 按 `key` 与 `path` 写入值。`core/crates/persistence/store/src/Transaction.rs:127`
- Edit 的 `Delete` — 按 `key` 与 `path` 删除。`core/crates/persistence/store/src/Transaction.rs:132`
- Edit 的 `Increment` — 按 `key`、`path` 与 `delta` 做增量。`core/crates/persistence/store/src/Transaction.rs:136`
- Edit 的 `Patch` — 一次批量设置与删除同一 `key` 的多个字段。`core/crates/persistence/store/src/Transaction.rs:141`
- Edit 的 `ReplaceRecords` — 原子替换一个记录命名空间。`core/crates/persistence/store/src/Transaction.rs:147`
- `Owner` — 归属，字段为 `backend`、`path`、`format` 与 `layout`。`core/crates/persistence/store/src/Transaction.rs:94`
- `Revision` — `SyncOperationOrder` 的公开类型别名。`core/crates/persistence/store/src/Transaction.rs:12`
- 主入口函数：History 的 `materialize`。`core/crates/persistence/store/src/Transaction.rs:1115`
- 数据流向一句话：事务原文经 `materialize` 迁移基线并重放为 `Data`。`core/crates/persistence/store/src/Transaction.rs:1115`

## 核心机制

- 文档定义 A、B 为两端完整业务状态，`C(A)` 是确定序列化的文件值或同步 SQL 表结构及记录。`docs/transaction-model.md:14`
- 文档定义 `T_a` 是单个事务，`T_A` 是 A 端的一组事务且序列可以为空，`\rho(T_a)` 是业务修改顺序。`docs/transaction-model.md:15`
- 文档定义 `\operatorname{Apply}_\mu(A,\mathcal T)` 按序列逐个原子应用事务，`μ` 是目标数据所属模块的 `merge rule`。`docs/transaction-model.md:16`
- 文档定义 `[]` 为空序列，`‖` 为序列拼接，`π` 为任意到达顺序的排列。`docs/transaction-model.md:17`
- 文档定义 `\cup_{\mathrm{id}}` 按身份合并历史，`N(\mathcal H)` 对历史按身份去重并按 `ρ` 排序，同身份同原文计入一次，同身份不同原文判错。`docs/transaction-model.md:18`
- 文档定义 `\mathsf M_{\mu,b}(\mathcal H)` 将基线 b 和历史改写为等价基线 `b_c` 及更小的历史 `H_c`。`docs/transaction-model.md:19`
- 文档定义 `\operatorname{Eff}_{\mu_T}(\mathcal H)` 校验原文身份后按目标依赖及事务规则求有效的一阶历史，仅有一阶事务时等于原历史。`docs/transaction-model.md:20`
- 文档定义 `m_F` 为格式迁移，`m_L` 为 layout 迁移，组合 `m=m_F\circ m_L` 表示先确定当前归属再转换为对应格式。`docs/transaction-model.md:21`
- 文档定义 `m(A)` 以同一规则迁移完整状态，`m_A(\mathcal T)` 以 A 为上下文转换事务序列。`docs/transaction-model.md:22`
- 文档定义 P 与 E 是按身份识别的待处理与已应用事务集合，`\operatorname{ready}(T)` 表示事务有效且所需格式、归属、上下文和依赖均已就绪。`docs/transaction-model.md:23`
- 文档定义 `X[k]=(x,r)` 表示位置 k 的值为 x、业务修订为 r，`†` 表示保留删除事实。`docs/transaction-model.md:24`
- 文档定义 `α` 是记录 ID 到规范 ID 的持久映射，`\nu_X` 是 X 的快照版本，`↝` 表示经处理后到达的状态。`docs/transaction-model.md:25`
- 文档将完整状态写为 `A=(O,V,\rho,D,\alpha,\sigma,\Delta)`，检查点另保存精确的历史覆盖集合 K。`docs/transaction-model.md:29`
- 文档将 `Transaction.rs` 列为事务模型的实现入口。`docs/transaction-model.md:189`
- 契约定义数据接口 f 为 DataStore 和 SQL 共有的逻辑访问与变换接口，暴露路径、归属、字段和值以及设置、删除、增量操作语义。`docs/transaction-sync-contract.md:14`
- 契约定义事务为以 SQL 记录承载的一组原子修改，含固定身份、顺序、目标和操作。`docs/transaction-sync-contract.md:15`
- 契约定义修改顺序为因果上后发生的修改排在后面，并发修改按统一逻辑时间和稳定身份排序。`docs/transaction-sync-contract.md:16`
- 契约定义 `merge rule` 为数据所属模块声明的合并策略，包括冲突、删除、内容判同和引用处理。`docs/transaction-sync-contract.md:22`
- 契约定义事务合并为用等价的较新事务或完整基线替代已覆盖历史，持久保存覆盖身份后删除旧 payload。`docs/transaction-sync-contract.md:21`
- `newer` 在同一来源设备内比较 `sequence`，否则按 `Revision` 的全序比较。`core/crates/persistence/store/src/Transaction.rs:21`
- `verify_original` 在同身份原文不一致时返回 `Conflicting immutable transaction` 错误。`core/crates/persistence/store/src/Transaction.rs:29`
- `ordered` 按身份去重并按业务顺序排序，返回统一顺序的事务序列。`core/crates/persistence/store/src/Transaction.rs:46`
- ordered 在同一来源同一 `sequence` 出现两条事务时返回错误。`core/crates/persistence/store/src/Transaction.rs:69`
- `History` 的 `insert` 拒绝空身份，同身份事务须与已存原文一致。`core/crates/persistence/store/src/Transaction.rs:1046`
- History 的 `materialize` 先对基线做 `migrate_data` 再重放事务。`core/crates/persistence/store/src/Transaction.rs:1115`
- 目标为 `Target` 的 `Data` 但 `owner` 与当前数据不一致的事务被当作独立数据集跳过。`core/crates/persistence/store/src/Transaction.rs:1139`
- 求有效视图或迁移失败的事务记入 `pending`。`core/crates/persistence/store/src/Transaction.rs:1141`
- 应用失败的事务记入 `pending`。`core/crates/persistence/store/src/Transaction.rs:1157`
- `Data` 的 `apply` 要求事务目标等于当前 `owner`，否则返回 `Transaction owner/version is not ready` 错误。`core/crates/persistence/store/src/Transaction.rs:424`
- `Data` 的 `apply` 先在副本上应用全部 `edits`，全部成功后才整体提交。`core/crates/persistence/store/src/Transaction.rs:424`
- 整体 `revision` 只在新事务的 `revision` 更新时才推进。`core/crates/persistence/store/src/Transaction.rs:457`
- Data 的 apply_edit 对 ReplaceRecords，较旧的整组替换直接跳过。`core/crates/persistence/store/src/Transaction.rs:473`
- Data 的 apply_edit 对 ReplaceRecords 按整组命名空间保存范围版本。`core/crates/persistence/store/src/Transaction.rs:507`
- 已有更新的祖先范围版本时，较旧的写入被跳过。`core/crates/persistence/store/src/Transaction.rs:530`
- Increment 要求整数且不溢出，否则返回错误。`core/crates/persistence/store/src/Transaction.rs:227`
- 契约要求乱序、重复到达或离线修改按统一顺序合并，每个事务效果计入一次。`docs/transaction-sync-contract.md:32`
- 契约要求同一字段先赋值 A 再赋值 AB 时保留 AB 的原身份和顺序，删除被覆盖的 A。`docs/transaction-sync-contract.md:34`
- 契约要求旧事务同时修改 x、y 而新事务仅覆盖 x 时，y 仍有效，旧事务整体保留。`docs/transaction-sync-contract.md:35`
- Data 含 `revision`，记录文件最后业务修改的顺序。`core/crates/persistence/store/src/Transaction.rs:357`
- Data 含 `deleted` 与 `aliases`，`deleted` 记录删除事实，`aliases` 记录身份映射。`core/crates/persistence/store/src/Transaction.rs:358`
- Data 含 `versions` 与 `additions`，`versions` 记录各修改范围的优先级，`additions` 记录尚需保留的增量贡献。`core/crates/persistence/store/src/Transaction.rs:361`
- 契约定义 preference 迁移为格式迁移，转换同一数据集内部的字段、类型和编码，例如 `name → displayName`。`docs/transaction-sync-contract.md:17`
- 契约定义 layout 迁移为归属迁移，移动路径、转交模块或明确退休旧来源，本机持有执行进度。`docs/transaction-sync-contract.md:18`
- 契约定义 SQL 迁移为格式迁移，转换表结构及行的表示，数据库结构版本与业务修改版本分别记录。`docs/transaction-sync-contract.md:19`
- `rename_field` 在目标字段已存在时返回 `Field destination exists` 错误。`core/crates/persistence/store/src/Transaction.rs:657`
- `Migrations` 的 `resolve_path` 沿 layout 路由链解析当前路径，成环时返回 `Layout migration cycle` 错误。`core/crates/persistence/store/src/Transaction.rs:984`
- Migrations 的 `migrate_data` 按步骤应用格式规则并迁移数据。`core/crates/persistence/store/src/Transaction.rs:996`
- `migrate_data` 在应用规则后经 `relocate` 改写路径并替换 `owner`。`core/crates/persistence/store/src/Transaction.rs:997`
- Migrations 的 `migrate_transaction` 只对 `Target` 的 `Data` 的事务做迁移。`core/crates/persistence/store/src/Transaction.rs:1007`
- Migrations 的 `steps` 在归属未知时返回 `Pending layout owner` 错误。`core/crates/persistence/store/src/Transaction.rs:1020`
- 来源版本高于当前版本时返回 `Pending future layout/format` 错误。`core/crates/persistence/store/src/Transaction.rs:1026`
- 格式迁移规则按来源 `format` 到当前 `format` 逐版本选取。`core/crates/persistence/store/src/Transaction.rs:1030`
- Data 的 `relocate` 按新路径改写 `aliases` 中的身份映射并替换 `owner.path`。`core/crates/persistence/store/src/Transaction.rs:403`
- 契约要求收到未来格式时原文进入待处理，升级就绪后应用。`docs/transaction-sync-contract.md:41`
- 契约要求旧路径事务晚到时按 layout 映射交给当前归属。`docs/transaction-sync-contract.md:42`
- 契约要求同一规则通过 f 作用于 DataStore、业务 SQL 及 SQL 事务视图。`docs/transaction-sync-contract.md:67`
- `Form` 要求实现 `migrate` 与 `apply_rule`。`core/crates/persistence/store/src/Transaction.rs:1645`
- `Data` 实现 `Form`。`core/crates/persistence/store/src/Transaction.rs:1649`
- `Transaction` 实现 `Form`。`core/crates/persistence/store/src/Transaction.rs:1657`
- `Migrations` 的 `migrate` 先在副本上迁移，成功后才替换原文。`core/crates/persistence/store/src/Transaction.rs:1666`
- `Rule` 的 `apply` 先在副本上应用规则，成功后才替换原文。`core/crates/persistence/store/src/Transaction.rs:1674`
- SqlDataset 的 `domain` 在聊天数据库路径下为 `chat`，否则为 `plugin_storage`。`core/crates/persistence/store/src/Transaction.rs:1464`
- SqlDataset 的 `coverage` 合并已提交事务身份、初始化覆盖与初始化事务操作身份。`core/crates/persistence/store/src/Transaction.rs:1474`
- SqlDataset 的 `initialization` 返回当前已保存的初始化事务操作。`core/crates/persistence/store/src/Transaction.rs:1468`
- 提交快照时在定义给出时经 `restore_schema` 恢复表结构声明。`core/crates/persistence/store/src/Transaction.rs:1601`
- Snapshot 的 `projected_content_digest` 允许 `owner` 把本地 SQL 账本列投影出内容比较。`core/crates/persistence/store/src/Transaction.rs:1217`
- `project_sql_table` 把声明的本地列投影出 SQL 内容比较，并按行排序去重。`core/crates/persistence/store/src/Transaction.rs:1406`
- `Target` 分 `Data(Owner)` 与 `Transaction(String)` 两种目标。`core/crates/persistence/store/src/Transaction.rs:102`
- `root` 沿事务目标链追溯到一阶事务。`core/crates/persistence/store/src/Transaction.rs:1101`
- 高阶事务只允许修改目标事务的 `edits` 字段，其余元数据不可变。`core/crates/persistence/store/src/Transaction.rs:1082`
- History 的 `effective` 在高阶事务依赖成环时返回错误。`core/crates/persistence/store/src/Transaction.rs:1064`
- `Snapshot` 含 `damage` 字段，记录损坏证据。`core/crates/persistence/store/src/Transaction.rs:1205`
- `Snapshot` 的 `token` 是整份快照的摘要。`core/crates/persistence/store/src/Transaction.rs:1209`
- `Snapshot` 的 `content_digest` 只对数据值做摘要，与重放账本无关。`core/crates/persistence/store/src/Transaction.rs:1213`
- Snapshot 的 `replace` 以 `token` 做 CAS，期望 `token` 不符时返回 `false`。`core/crates/persistence/store/src/Transaction.rs:1233`
- 替换成功时 `generation` 加一。`core/crates/persistence/store/src/Transaction.rs:1241`
- 替换成功时合并来源与本地的 `covered`。`core/crates/persistence/store/src/Transaction.rs:1249`
- Snapshot 的 `replay` 只重放未被 `covered` 覆盖的事务。`core/crates/persistence/store/src/Transaction.rs:1253`
- Manifest 含 `damaged` 标记。`core/crates/persistence/store/src/Transaction.rs:1274`
- `compare_manifests` 在两端 `owner` 不一致时返回错误。`core/crates/persistence/store/src/Transaction.rs:1284`
- `compare_manifests` 在一端损坏而另一端完好时选完好一方为权威，两端都损坏时返回错误。`core/crates/persistence/store/src/Transaction.rs:1288`
- 摘要相等时判定 `Equal`。`core/crates/persistence/store/src/Transaction.rs:1295`
- 摘要不等时按 `revision` 再按 `node` 的字典序选权威方。`core/crates/persistence/store/src/Transaction.rs:1299`
- `compare` 在摘要相等时返回 `None`。`core/crates/persistence/store/src/Transaction.rs:1331`
- `serialized_digest` 用 `Sha256` 对序列化形式做摘要，`digest` 返回其哈希。`core/crates/persistence/store/src/Transaction.rs:1181`
- SqlDataset 的 `receive_initialization` 在操作身份已被覆盖时返回 `false`，不重复接收。`core/crates/persistence/store/src/Transaction.rs:1542`
- `receive_validated_initialization` 在初始化数据的 `owner` 或 `domain` 不符时返回 `Initialization owner differs` 错误。`core/crates/persistence/store/src/Transaction.rs:1551`
- 提交快照时以 `token` 做 CAS，当前 `token` 与期望不符时返回 `false`。`core/crates/persistence/store/src/Transaction.rs:1593`
- `covered_by_initialization` 按初始化覆盖表判断操作是否已被封存。`core/crates/persistence/store/src/Transaction.rs:1636`
- `operation_digest` 对初始化引用返回其内容哈希，否则对事务操作做摘要。`core/crates/persistence/store/src/Transaction.rs:36`
- 契约要求同版本、本轮增量已交换且比较未过期、内容仍不同时判为同步错误，选权威快照覆盖并再次比较。`docs/transaction-sync-contract.md:54`
- Transaction.rs 声明 `transaction/Compaction.rs` 为 `compaction` 模块。`core/crates/persistence/store/src/Transaction.rs:14`

## 关键符号

- `Transaction` — 一条带固定身份、顺序、目标与操作的原子修改。`core/crates/persistence/store/src/Transaction.rs:329`
- `Transaction` 的 `backend` — 恒返回 `Sql`。`core/crates/persistence/store/src/Transaction.rs:338`
- `Revision` — `SyncOperationOrder` 的公开类型别名。`core/crates/persistence/store/src/Transaction.rs:12`
- `Owner` — 归属，字段为 `backend`、`path`、`format` 与 `layout`。`core/crates/persistence/store/src/Transaction.rs:94`
- `Backend` — 只有 `DataStore` 与 `Sql` 两项。`core/crates/persistence/store/src/Transaction.rs:88`
- `Target` — 分 `Data` 与 `Transaction` 两种目标。`core/crates/persistence/store/src/Transaction.rs:102`
- `Edit` 的 `Set` — 按 `key` 与 `path` 写入值。`core/crates/persistence/store/src/Transaction.rs:127`
- Edit 的 `Delete` — 按 `key` 与 `path` 删除。`core/crates/persistence/store/src/Transaction.rs:132`
- Edit 的 `Increment` — 按 `key`、`path` 与 `delta` 做增量。`core/crates/persistence/store/src/Transaction.rs:136`
- Edit 的 `Patch` — 一次批量设置与删除同一 `key` 的多个字段。`core/crates/persistence/store/src/Transaction.rs:141`
- Edit 的 `ReplaceRecords` — 原子替换一个记录命名空间。`core/crates/persistence/store/src/Transaction.rs:147`
- `Path` — 分 `Field`、`Item` 与 `Records` 三种定位。`core/crates/persistence/store/src/Transaction.rs:109`
- `Data` — 完整业务状态，含 `owner` 与 `values`。`core/crates/persistence/store/src/Transaction.rs:351`
- Data 的 `revision` — 文件最后业务修改的顺序。`core/crates/persistence/store/src/Transaction.rs:357`
- Data 的 `deleted` 与 `aliases` — 删除事实与身份映射。`core/crates/persistence/store/src/Transaction.rs:358`
- Data 的 `versions` 与 `additions` — 各修改范围的优先级与尚需保留的增量贡献。`core/crates/persistence/store/src/Transaction.rs:361`
- `History` 的 `insert` — 拒绝空身份，同身份事务须与已存原文一致。`core/crates/persistence/store/src/Transaction.rs:1046`
- History 的 `materialize` — 先对基线做 `migrate_data` 再重放事务。`core/crates/persistence/store/src/Transaction.rs:1115`
- History 的 `effective` — 在高阶事务依赖成环时返回错误。`core/crates/persistence/store/src/Transaction.rs:1064`
- History 的 `root` — 沿事务目标链追溯到一阶事务。`core/crates/persistence/store/src/Transaction.rs:1101`
- `Replay` — 重放结果，含 `data`、`applied` 与 `pending` 三个字段。`core/crates/persistence/store/src/Transaction.rs:1170`
- `Migrations` — 格式与 layout 迁移表，含 `owners`、`layouts` 与 `formats`。`core/crates/persistence/store/src/Transaction.rs:977`
- `Migrations` 的 `resolve_path` — 沿 layout 路由链解析当前路径，成环时返回错误。`core/crates/persistence/store/src/Transaction.rs:984`
- Migrations 的 `migrate_data` — 按步骤应用格式规则并迁移数据。`core/crates/persistence/store/src/Transaction.rs:996`
- Migrations 的 `migrate_transaction` — 只对 `Target` 的 `Data` 的事务做迁移。`core/crates/persistence/store/src/Transaction.rs:1007`
- `Rule` — 含 `RenameKey` 与 `RenameField` 两种重命名规则。`core/crates/persistence/store/src/Transaction.rs:632`
- Rule — 含 `SplitObject`、`DropKey` 与 `SplitRecords` 三种结构规则。`core/crates/persistence/store/src/Transaction.rs:647`
- `rename_field` — 在目标字段已存在时返回错误。`core/crates/persistence/store/src/Transaction.rs:657`
- `Snapshot` — 快照，字段为 `node`、`data`、`covered` 与 `generation`。`core/crates/persistence/store/src/Transaction.rs:1198`
- `Snapshot` 的 `token` — 整份快照的摘要。`core/crates/persistence/store/src/Transaction.rs:1209`
- `Snapshot` 的 `content_digest` — 只对数据值做摘要，与重放账本无关。`core/crates/persistence/store/src/Transaction.rs:1213`
- Snapshot 的 `replace` — 以 `token` 做 CAS，期望 `token` 不符时返回 `false`。`core/crates/persistence/store/src/Transaction.rs:1233`
- Snapshot 的 `replay` — 只重放未被 `covered` 覆盖的事务。`core/crates/persistence/store/src/Transaction.rs:1253`
- Snapshot 的 `projected_content_digest` — 允许 `owner` 把本地 SQL 账本列投影出内容比较。`core/crates/persistence/store/src/Transaction.rs:1217`
- `Manifest` — 有线比较视图，字段为 `owner`、`node`、`revision`、`token` 与 `digest`。`core/crates/persistence/store/src/Transaction.rs:1267`
- `Correction` — 合并两端 `covered` 的校正结果。`core/crates/persistence/store/src/Transaction.rs:1339`
- `compare_manifests` — 在两端 `owner` 不一致时返回错误。`core/crates/persistence/store/src/Transaction.rs:1284`
- `compare` — 在摘要相等时返回 `None`。`core/crates/persistence/store/src/Transaction.rs:1331`
- `ordered` — 按身份去重并按业务顺序排序，返回统一顺序的事务序列。`core/crates/persistence/store/src/Transaction.rs:46`
- `newer` — 在同一来源设备内比较 `sequence`，否则按 `Revision` 的全序比较。`core/crates/persistence/store/src/Transaction.rs:21`
- `verify_original` — 在同身份原文不一致时返回错误。`core/crates/persistence/store/src/Transaction.rs:29`
- SqlDataset 的 `domain` — 在聊天数据库路径下为 `chat`，否则为 `plugin_storage`。`core/crates/persistence/store/src/Transaction.rs:1464`
- SqlDataset 的 `coverage` — 合并已提交事务身份、初始化覆盖与初始化事务操作身份。`core/crates/persistence/store/src/Transaction.rs:1474`
- SqlDataset 的 `initialization` — 返回当前已保存的初始化事务操作。`core/crates/persistence/store/src/Transaction.rs:1468`
- SqlDataset 的 `receive_initialization` — 在操作身份已被覆盖时返回 `false`，不重复接收。`core/crates/persistence/store/src/Transaction.rs:1542`
- `covered_by_initialization` — 按初始化覆盖表判断操作是否已被封存。`core/crates/persistence/store/src/Transaction.rs:1636`
- `Form` — 要求实现 `migrate` 与 `apply_rule`。`core/crates/persistence/store/src/Transaction.rs:1645`
- `serialized_digest` — 用 `Sha256` 对序列化形式做摘要。`core/crates/persistence/store/src/Transaction.rs:1181`
- `operation_digest` — 对初始化引用返回其内容哈希，否则对事务操作做摘要。`core/crates/persistence/store/src/Transaction.rs:36`
- `project_sql_table` — 把声明的本地列投影出 SQL 内容比较，并按行排序去重。`core/crates/persistence/store/src/Transaction.rs:1406`

## 调用链

1. `History` 的 `insert` 收录事务原文，同身份事务须与已存原文一致。`core/crates/persistence/store/src/Transaction.rs:1046`
2. History 的 `materialize` 先对基线做 `migrate_data` 再重放事务。`core/crates/persistence/store/src/Transaction.rs:1115`
3. 对高阶事务求有效视图，只允许修改目标事务的 `edits` 字段。`core/crates/persistence/store/src/Transaction.rs:1082`
4. Migrations 的 `migrate_transaction` 只对 `Target` 的 `Data` 的事务做迁移。`core/crates/persistence/store/src/Transaction.rs:1007`
5. `ordered` 按身份去重并按业务顺序排序，返回统一顺序的事务序列。`core/crates/persistence/store/src/Transaction.rs:46`
6. `Data` 的 `apply` 先在副本上应用全部 `edits`，全部成功后才整体提交。`core/crates/persistence/store/src/Transaction.rs:424`
7. 重放结果记入 `Replay`，含 `data`、`applied` 与 `pending` 三个字段。`core/crates/persistence/store/src/Transaction.rs:1170`
8. 两端以 `Manifest` 比较，`owner` 不一致时返回错误。`core/crates/persistence/store/src/Transaction.rs:1284`
9. 摘要相等时判定 `Equal`。`core/crates/persistence/store/src/Transaction.rs:1295`
10. 摘要不等时按 `revision` 再按 `node` 的字典序选权威方。`core/crates/persistence/store/src/Transaction.rs:1299`
11. `compare` 在摘要相等时返回 `None`。`core/crates/persistence/store/src/Transaction.rs:1331`
12. `Correction` 合并两端 `covered`。`core/crates/persistence/store/src/Transaction.rs:1339`
13. Snapshot 的 `replace` 以 `token` 做 CAS，期望 `token` 不符时返回 `false`。`core/crates/persistence/store/src/Transaction.rs:1233`
14. Snapshot 的 `replay` 只重放未被 `covered` 覆盖的事务。`core/crates/persistence/store/src/Transaction.rs:1253`
15. SQL 侧由 SqlDataset 的 `receive_initialization` 接收初始化事务，已覆盖的操作身份返回 `false`。`core/crates/persistence/store/src/Transaction.rs:1542`
16. 提交快照时以 `token` 做 CAS，当前 `token` 与期望不符时返回 `false`。`core/crates/persistence/store/src/Transaction.rs:1593`

## 来源

- `docs/transaction-model.md`
- `docs/transaction-sync-contract.md`
- `core/crates/persistence/store/src/Transaction.rs`
- 否定性结论核验方法（2026-11-11，基线 AAswordman/Operit2 @ 364d1d594）：对 `Transaction.rs` 全文 grep `File`，仅命中 1545–1546 两行代码（`RuntimeFileSyncStore::requiredBlob`／`readSqlInitialization`，为 SQL 初始化 blob 的文件同步仓储暂存引用），无文件载体分支，`Backend` 枚举只有 `DataStore` 与 `Sql` 两项；全文 grep `merge` 与 `equivalence`（不区分大小写）均为 0 命中，文档的 M 合并、迁移等价式逐步校验、J 检查点合并、`resume_m`、`readOptional`、内容判同在本文件内无对应函数，合并相关逻辑在 transaction/Compaction.rs（如 superseded :205），不在本文件内；全文 grep `export` 仅命中 1216 行注释，导出范围 `e_X`／`ê_X`（docs/transaction-model.md:27）在本文件内无对应实现；全文 grep `retire` 仅命中 1537、1538、1575、1619 行快照提交的 retire 回调，layout 退休映射为空效果 m_L(T)=ε（docs/transaction-model.md:71；docs/transaction-sync-contract.md:43、:65）在本文件内无对应实现。
