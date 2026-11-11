作者：luojiaping
时间：2026-11-11T09:18:39Z UTC
comment_id：6791996388

复审结论：**本轮已列问题均已修复，未发现新的阻断问题。**

复审版本：wiki `0d80949be0731364dd1451cf3da681596baf0a63`；已核实上游 `AAswordman/Operit2` 最新 `main` 仍为 `364d1d594a0b7610e68fd804fc86fa342f18e14d`。

已逐项核对以下修订：

- [正文第 37–42 行](https://github.com/luojiaping/Operit2-wiki/blob/0d80949be0731364dd1451cf3da681596baf0a63/review/batch-02/core-persistence-sync.md#L37)及 facts 第 19、164–167 条已区分当前 `transactions.sqlite` Journal 和已退休的按来源 JSONL；与 [Journal::open:19](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/transaction/Journal.rs#L19)、[withJournal:1705](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/SyncOperationStore.rs#L1705)及追加/接收入口相符。
- [第 50–52 行](https://github.com/luojiaping/Operit2-wiki/blob/0d80949be0731364dd1451cf3da681596baf0a63/review/batch-02/core-persistence-sync.md#L50)、关键符号表和 facts 第 20、37–39 条已将扫描、隔离及边车限定为遗留 JSONL；来源列表已补充 Journal 实现。
- [第 77–79 行](https://github.com/luojiaping/Operit2-wiki/blob/0d80949be0731364dd1451cf3da681596baf0a63/review/batch-02/core-persistence-sync.md#L77)及 facts 第 5、41 条已统一为“4 MiB 页预算，首条超大操作例外保留”，与 [boundSyncOperationPage:1627–1643](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/SyncOperationStore.rs#L1627)一致。

一处非阻断措辞建议：第 39 行及 facts 第 165 条的“唯一读取已退休文件式 ledger 的入口”可收窄为“当前 Journal 的一次性迁移入口”。[scanOperationLog:1293–1299](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/SyncOperationStore.rs#L1293)仍可读取遗留 JSONL 做诊断；这一措辞不影响当前存储位置已修正的结论。未做真实同步实验。

本轮限于首轮问题、关联正文修订和变化的 facts，采用固定源码静态核对，未执行编译、构建或测试。

