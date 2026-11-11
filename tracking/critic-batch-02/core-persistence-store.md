# Critic：core-persistence-store（batch-02，Issue #15）

- 结论：**需修改**
- 评审者：独立 critic（未参与写作，全新 session）
- 日期：2026-11-11
- 对象：`review/batch-02/core-persistence-store.md` + `review/batch-02/core-persistence-store.facts.json`
- 基线：`~/workspace/Operit2 @ 364d1d594`（只读核对）

## 检查方法

- 182 条 facts 全部逐条核对：每条取 ref 行 ±5 行源码上下文亲眼比对；其中 12 处（[25] 测试体、[37]、[52]、[55]、[79]、[88]、[91]、[102]、[113]、[124]、[138]、[148]、[151]、[170]、[176]）追读了完整函数体或相关辅助函数。
- 正文 258 处引用逐个比对 facts 覆盖：183 个不同 `file:line`，仅 1 处无同行 fact（见次要建议第 5 条）。
- 结构按 SCHEMA.md §2/§9.2 核对；禁用词全文 grep；来源行数逐项 `wc -l` 核对；`[[...]]` 链接目标核对存在。

## 统计

- 支撑：180 / 182
- 存疑：2（[91]、[148]，均为 P2 精度问题，需改 fact + 正文）
- 不支撑：0
- 结构：合规（见“通过项”）

## 需修改的问题

### P2-1 · fact [91]：writeLocalDeviceProfile 的触发条件与行为都写偏了

- **fact 原文**（ref `core/crates/persistence/store/src/CoreSpaceStore.rs:641`）：
  > `CoreSpaceStore::writeLocalDeviceProfile` 首次创建 profile 时按 Space 是否仍为 revision 1 的初始 Space 选取默认显示名。
- **正文同款表述**（.md:227）：同一句话。
- **代码实际内容**（`CoreSpaceStore.rs:640-647`）：
  ```rust
  let initialSpace = self.initializeNamed(displayName.clone())?;
  if initialSpace.spaceRevision == 1
      && initialSpace.members.len() == 1
      && initialSpace.spaceName == defaultSpaceName()
      && initialSpace.spaceName != displayName
  {
      self.rename(displayName.clone())?;
  }
  ```
  两处不符：① 该判断在**每次** `writeLocalDeviceProfile` 调用时都执行，不是只在“首次创建 profile 时”（实践中只会触发一次，是因为重命名后 Space 名不再等于默认名 `Operit`，条件不再成立——这是结果，不是触发条件）；② 触发时的行为是把 **Space 重命名为设备的 displayName**，不是“选取默认显示名”——方向正好反了，是用设备显示名替换掉默认名。
- **怎么改**：fact 与 .md:227 一起改成条件与行为都按代码写，例如：
  > `CoreSpaceStore::writeLocalDeviceProfile` 写本地设备档案时，若 Space 仍是 revision 1 的初始单成员 Space 且名仍为默认名，则把 Space 重命名为设备显示名。
  ref 保持 `:641`（条件四要素均在 641-644 行，`rename` 在 646 行，±5 行内）。

### P2-2 · fact [148]：data() 的缓存直返漏了 retain 前置条件

- **fact 原文**（ref `core/crates/persistence/store/src/PreferencesDataStore.rs:3073`）：
  > `data()` 在已缓存快照且 schema 已是最新时直接返回缓存。
- **正文同款表述**（.md:389、.md:529，两处）：同一句话。
- **代码实际内容**（`PreferencesDataStore.rs:3070-3077`）：
  ```rust
  let retain = self.syncDescriptor.is_some() || self.storageHost.retainPreferencesCache();
  if retain {
      if let Some(preferences) = self.loadedPreferences() {
          if self.schemaIsCurrent(&preferences)? {
              return Ok(preferences);
          }
      }
  }
  ```
  缓存直返分支被 `retain` 门控。同步 store 的 `retain` 恒为真，但节点本地 store 在宿主不保留偏好缓存时 `retain` 为假——此时即使共享 state 里已有缓存快照且 schema 最新，`data()` 也会走重载路径（随后 `releaseNodeLocalCacheUnlocked`（:3089-3096）还会把该缓存清掉）。原文把有条件分支写成了无条件保证，是 batch-01 同类问题的缩小版。
- **怎么改**：fact 与 .md:389、.md:529 一起补上条件，例如：
  > `data()` 在同步 store 或宿主保留偏好缓存的前提下，已缓存快照且 schema 已是最新时直接返回缓存。
  ref 保持 `:3073`（`retain` 定义在 3070 行，±5 行内）。

## 次要建议（不阻塞，可随上两项一起改）

### N-1 · fact [124]：ref 落在右花括号上，锚点弱

- fact 原文：`导入的拓扑记录不产生本地同步操作。`（ref `CoreSpaceStore.rs:1264`）
- :1264 是 `importTopologyRecords` 的结束 `}`；断言本身由紧邻的 doc comment（:1266-1269，“Stores one imported topology announcement without staging a local operation”）支撑，结论为真。建议 ref 改为 `:1266`（doc 注释首行）或 `:1253`（函数签名），.md:249 同步改。

### N-2 · fact [102]：主语与 ref 所在函数不一致

- fact 原文：`` `deviceConnections` 只返回当前 Space 成员之间的有向直连。``（ref `CoreSpaceStore.rs:970`）
- :970 在 `deviceConnectionsForSpace` 内部（过滤逻辑），`deviceConnections` 本体在 :961-963，只是委托给前者。结论为真，建议 ref 改为 `:961`，.md:289 同步改；或把 fact 主语改为 `deviceConnectionsForSpace`。

### N-3 · .md:59 的 `:69` 引用无同行 fact（可接受）

- 正文 AI 速览 `PREFERENCES_REPLICATION_KEY` 一行引用 `PreferencesDataStore.rs:69`（常量定义行本身，引用准确）。
- facts.json 无 ref 为 `:69` 的 fact；但 fact [142] 以 ref `:71` 一并覆盖了 schema 版本键与复制元数据键两个常量，`:71` 与 `:69` 相差 2 行，在 ±5 行内，实质覆盖成立。可不改；如求严格一一对应，可把 fact [142] 拆成两条，分别 ref `:71` 与 `:69`。

### N-4 · 观察：`SqliteStore::*` 重导出本身也有 feature 门控

- `lib.rs:59` 的 `pub use SqliteStore::*;` 上方 `:58` 有 `#[cfg(feature = "full")]`，即重导出同样只在 `feature full` 下生效；正文“聚合与 feature 门控”一节只写了 `SqliteStore` 模块受门控，未写重导出也受门控。现有断言为真，不构成错误；如改 P2-1/P2-2 时顺手补一句更完整。

## 通过项

- **结构合规**：frontmatter 齐全（title / module: core / platforms: [all] / sources 7 文件 / date）；六节齐全且顺序符合 SCHEMA §9.2（概述 / AI 速览 / 核心机制 / 关键符号 / 调用链 / 来源）；全文无禁用词（可能/大概/似乎/应该/也许 grep 0 命中）。
- **来源行数逐项核对一致**：README.md 13、lib.rs 92、SqliteStore.rs 568、CoreNodeIdentityStore.rs 163、CoreNodeBindingStore.rs 481、CoreSpaceStore.rs 2972、PreferencesDataStore.rs 3972。
- **引用覆盖**：正文 258 处引用、183 个不同 `file:line`，除上述 N-3 外全部落在 facts 覆盖内；条目间链接 `[[core-persistence-sync|持久化——同步存储]]` 目标 `review/batch-02/core-persistence-sync.md` 存在。
- **其余 180 条 facts 逐条支撑**，包括易错点均已按现状核对：`Target Split` 明确写成目标计划而非已完成拆分（fact [4]）；`new`/`newNodeLocal` 两种形态的同步字段有无分开写（[132]/[133]）；`validateDeviceUserName` 不要求非空、只限长与禁控制字符（[110]，与 `validateDeviceProfileField` 的非空要求已区分）；`formatVersion` 事务要求 2 且至少 2 条、同步载荷只接受 1 与 2（[168]/[170]，含 `version => Err` 兜底分支已核）；`increment` 存增量而非绝对值（[138]，mutation 的 value 为 delta 已核）；`delete` 追加 delete 操作并清进程缓存（[52]，`removeCachedBinding` 已核）；`applyImmediateOperation` 不推进持久化时钟（[55]，doc 注释与 `appendUnobservedOperation` 已核）。
- 未发现文档声称与实现混淆、设计约束写成已实现、旧名/旧命令/断链类问题。

## 复验要求

- 改完 P2-1、P2-2（及采纳的 N 项）后重跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-02`，硬失败与警告均为 0；并对改动后的 facts 重新机械核验引用（文件存在 + 行号范围 + 符号在 ref 行 ±5 行内）。
