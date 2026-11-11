## luojiaping @ 2026-11-11T07:10:01Z (https://github.com/luojiaping/Operit2-wiki/issues/10#issuecomment-6789513570)

审查结论：**需修改**。

核对基线：wiki `b75bcad9`，上游 `AAswordman/Operit2` 最新 `main` 已确认是 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与 wiki 标注一致。以下是静态源码审查意见。

1. **[P2] 完整快照校正不只在内容不同的时候发生。** [正文第 113 行](https://github.com/luojiaping/Operit2-wiki/blob/b75bcad9d63959f0108f81193119e372eca38f4a/review/batch-01/arch-sync.md#L113)及第 143 行调用链将“导出范围未过期且最终内容仍不同”写成前提，但 [SyncConsistency.rs:138–142](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/SyncConsistency.rs#L138) 明确处理 `Source::Equal`：当 `force` 为真或任一端仍有该 owner 的 `skipped` 原文，也会生成完整校正计划。[sync-architecture.md:121–123](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/docs/sync-architecture.md#L121) 同样说明失败后的初始化基线重建和 skip 封存。建议分别写清正常内容差异校正与失败/skip 的基线重建，并补充 facts；否则用户看到内容相同却出现 `mode=full_snapshot` 会按本页误判行为。

2. **[P2] 诊断日志字段和事件清单应按实际输出修正。** 第 96 行及 facts 中对应条目列出 `sync_consistency.correct` 的三个 `reason` 值，第 97 行列出 `sync_consistency.deferred`。实际 [SyncConsistency.rs:60–61](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/SyncConsistency.rs#L60) 输出 `owner/source/damaged/localRevision/remoteRevision` 等字段，没有该 `reason`；[同文件:86–87](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/SyncConsistency.rs#L86) 在快照版本竞争时直接返回 `false`，此处没有发送该 `deferred` 日志。建议修正正文和 facts，避免排障时搜索不存在的字段/事件。快照 `coverageOnly` 与字节数可由 [同文件:105](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/SyncConsistency.rs#L105) 直接支撑。

已抽查存储复制授权边界、事务合并、consistencyVersion、各端自身稳定收据比较及完整快照计划/日志源码；本页 127 条 facts 引用路径均存在且行号未越界。上述实现核对属于源码直引的验真补充。未执行编译、构建或测试。


