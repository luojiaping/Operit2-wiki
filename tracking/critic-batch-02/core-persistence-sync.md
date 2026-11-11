# Critic：core-persistence-sync（持久化——同步存储）

- 页：`review/batch-02/core-persistence-sync.md` / `.facts.json`
- 评审 Issue：#16
- 源码基线：`AAswordman/Operit2 @ 364d1d594`（本地 `~/workspace/Operit2`，已核对 HEAD）
- 审读日期：2026-11-11
- 结论：**需修改**

## 方法

- 162 条 facts 逐条核对：每条取 ref 行 ±5 行源码逐行比对（符号名、字面值、条件分支、数值）。
- 正文逐行核对：全部 162 个正文引用与 facts 一一对应（双向 0 缺口）；禁用词 grep；结构按 SCHEMA §9.2 对照；frontmatter 与来源小节核对。
- 机器 lint：`python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-02`，全批硬失败 0、警告 0。
- 162 条 facts 机械核验（文件存在＋行号范围）：0 坏引用。

## 逐条判定汇总

- 支撑：160 条
- 不支撑：1 条（#33）
- 存疑：1 条（#137，事实本身为真，引用精度不足）
- 其余 160 条均已在源码亲眼核实，包括全部有条件分支（#11、#22、#29、#31、#35、#85、#86、#87、#111、#147 的条件表述均与代码一致，未发现把有条件分支写成无条件保证的情况；未发现把设计约束写成已实现的情况；未发现旧名/旧命令/断链）。

## 必改项

### 1. Fact #33（不支撑）：网络控制域的字面值写错

- Fact 原文：`observeNetworkControlOperation 只接受 domain 为 network-control 的操作。`
- 引用：`core/crates/persistence/store/src/SyncOperationStore.rs:1196`
- 代码实际内容：
  - `core/crates/persistence/store/src/NetworkControlStore.rs:53`：`pub const NETWORK_CONTROL_SYNC_DOMAIN: &str = "network_control";`（下划线，不是连字符）
  - `SyncOperationStore.rs:1195-1196`：`if operation.domain != NETWORK_CONTROL_SYNC_DOMAIN { return Err(...) }`，即只接受域值为 `network_control` 的操作
  - 全库 Rust 代码中 `"network-control"` 字面值出现 0 次；`"network_control"` 被实际使用，如 `core/crates/node/runtime/src/peer/space_projection.rs:302`、`NodeSpaceService.rs:804`、`SpacePersistenceSyncService.rs:30`
- 后果：按事实原文，域值为 `network-control` 的操作会被接受；按代码，它会被拒绝。事实与实现正好相反。
- 怎么改：
  - Fact #33 改为：`observeNetworkControlOperation 只接受 domain 为 network_control 的操作。`（引用不变）
  - 正文第 63 行同步改为：`` `observeNetworkControlOperation` 只接受 `domain` 为 `network_control` 的操作 ``（引用不变）
  - 注意：`docs/README.md` 里有 `network-control` 的 prose 写法，那是文档措辞不是代码值；wiki 以代码为准，不要反向引用文档。

### 2. Fact #137（存疑）：字面值不在引用行 ±5 行内

- Fact 原文：`FileReference 的 format 是 operit_file_reference，version 是 1，含 nodeId、path、fileName、fileSize 与可选的 modifiedAt。`
- 引用：`core/crates/persistence/store/src/FileSyncPolicy.rs:240`
- 代码实际内容：
  - 引用行 ±5 行（235–245）只有字段名：`format`、`version`、`nodeId`、`path`、`fileName`、`fileSize`、`modifiedAt`——字段清单本身有支撑
  - 但字面值 `operit_file_reference` 与 `version = 1` 只出现在 `FileReference::new`（`FileSyncPolicy.rs:258-259`：`format: "operit_file_reference".into(), version: 1`）和 `validate`（`:267-268`）中，离引用行 18–28 行，超出 ±5 行范围；只跟引用走的读者无法核实这两个值
- 怎么改（二选一，推荐拆分）：
  - Fact #137 改为字段清单：`FileReference 含 nodeId、path、fileName、fileSize 与可选的 modifiedAt。`（引用 `:240` 不变）
  - 新增一条事实：`FileReference 的 format 是 operit_file_reference，version 是 1。`，引用 `FileSyncPolicy.rs:266`（`validate` 行，两个值都在 ±5 行内）
  - 正文 `## 关键符号` 中 `FileReference` 一行（引用 `:240`）同步去掉 format/version 值，或把引用改为 `:266`

## 可选小修（不阻断）

### 3. Fact #131：引用可指向 `load` 本身

- Fact 原文：`策略文件不存在时 load 返回默认策略。`，引用 `FileSyncPolicy.rs:57`
- 代码实际内容：`load` 在 `:49`（`pub fn load(...)`），是薄壳，直接调 `loadForScan`；返回默认策略的行为在 `loadForScan` 的 `:57`。事实为真，行为完全一致。
- 建议：引用改为 `FileSyncPolicy.rs:49`，让被点名的符号落在引用行上；不改亦可。

### 4. Fact #96：引用可指向函数本身

- Fact 原文：`resetTransactions 重新发布当前字节与删除 tombstone。`，引用 `RuntimeFileSyncStore.rs:133`
- 代码实际内容：`:133` 是上一函数的右花括号，证据（doc 注释与函数签名）在 `:135-136`，在 ±5 行内，合规。
- 建议：引用改为 `:136`，精确落在函数签名上；不改亦可。

## 观察（无需改）

- `[[core-node-runtime|节点——节点运行时]]`（概述小节）指向大纲已列、但尚未落盘的页（`outline-v1.yaml:443`，batch-01/02 均无此文件）。前向引用本身合理，合并时留意图谱是否报断链，待该页写出后自动消除。
- Fact #123（`validatePath 要求托管路径属于 Space 所有权`）只陈述了 `validatePath` 的其中一个条件（函数同时要求 `manages(path)` 与路径无空段/`.`/`..`）；作为单条原子事实为真，不要求改。
- AI 速览与关键符号小节的 75 处“与事实措辞不一致”均为按 SCHEMA §9.2 设计的缩写式职责描述（`符号 — 一句话职责`），内容均有对应事实或代码支撑，不是内容出入；不列为问题。
- 正文 12 步调用链逐条与事实一致；概述、AI 速览数据流向一句为多条事实的综合复述，无超出事实的发挥。

## 结构合规检查

- Frontmatter 齐全（title / module: core / platforms: [all] / sources 8 个文件 / date: 2026-11-11）；`sources` 与 `## 来源` 所列 8 个文件一致。
- 小节齐全且顺序符合 SCHEMA §9.2：概述 / AI 速览 / 核心机制 / 关键符号 / 调用链 / 来源。
- 禁用词（可能/大概/似乎/应该/也许）：0 处。
- 正文引用与 facts 双向覆盖：正文 162 个引用全部落在 facts 内，facts 162 条全部在正文中出现。
