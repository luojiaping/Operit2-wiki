作者：luojiaping
时间：2026-11-11T08:51:03Z UTC
comment_id：6791457980

审查结论：**需修改**。

审查版本：wiki `f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50`；已核实上游 `AAswordman/Operit2` 最新 `main` 为 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与条目标注一致。

**[P2] 当前操作日志位置写成了已退休的 JSONL 存储。** [正文第 37 行](https://github.com/luojiaping/Operit2-wiki/blob/f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50/review/batch-02/core-persistence-sync.md#L37)及 facts 第 19 条称每来源设备的操作日志存于 `{root}/operations/{safeId}.jsonl`，但这不是该基线的当前持久化入口。

[SyncOperationStore.rs:1705–1720](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/SyncOperationStore.rs#L1705) 的 `withJournal` 打开 `Transaction::Journal`；其 [Journal.rs:19–27](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/transaction/Journal.rs#L19) 使用 `host.openTransactionDatabase("{root}/transactions.sqlite")` 并建立 `originals` 等表。[importLegacyJournal:1743](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/SyncOperationStore.rs#L1743)明确把文件式 ledger 标为 retired，只做一次原子导入。本地追加和接收操作也走当前 Journal。

建议将正文和 facts 第 19 条改为当前 SQLite Journal；第 46–48、228–229 行的扫描/隔离 API 及 facts 第 20、38 条需明确处理的是遗留 JSONL 格式，并把 Journal 实现纳入来源。否则读者按本页备份或排障会寻找错误的当前日志位置。无需改动源码。

非阻断措辞建议：第 73 行的“4MiB 硬上限”及 facts 第 5 条，与第 75 行已经列出的首条超大操作豁免合并说明。页面已写出该豁免，不把它另列为缺失机制。

另已核对追加/接收、操作原文验证、去重、收据与遗留日志诊断分支。

本轮为正文、对应 facts 和所列实现分支的静态核对，未执行编译、构建或测试。结论限于上述核对范围。

