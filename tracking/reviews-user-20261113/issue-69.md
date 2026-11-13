# Issue 69 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:30:07Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/69#issuecomment-6854368768


本轮结论：需修改。

复核 Wiki f9c90d7a，仍有两处固定基线内部矛盾需要修正文及 facts：

1. L120–L124 / facts57、59–61 把 receive_state.json 和 pending JSON 的写入、账本提交及清理描述成当前接收流程，与 L113–L114“生产 transactions.sqlite、旧文件仅兼容导入”矛盾。基线 [receiveOperations:1874–1878](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/SyncOperationStore.rs#L1874-L1878) 经 storeOriginals/Journal::put 写 SQL；[Journal:19–25](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/transaction/Journal.rs#L19-L25) 打开 transactions.sqlite。旧文件只由 [importLegacyJournal:1743–1754](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/SyncOperationStore.rs#L1743-L1754) 读取。请明确将这段限定为已退休布局的迁移历史，不能再作为生产接收路径。
2. L23 / fact106 的“同步协议版本5”与同页的 receipt=1、consistency=7 混在一起。基线 [OperitApplication:1003–1004](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/core/application/OperitApplication.rs#L1003-L1004) 明确生成 protocolVersion:1、consistencyVersion:7，[validateDomainClock:1464–1473](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/SpacePersistenceSyncService.rs#L1464-L1473) 也只接收收据协议1。请区分字段语义，若保留5只能标明对应的旧设计/历史阶段。

以上不是仅因 main 后续漂移提出的问题。本轮仅静态核验，未运行双设备同步。

源码定位：
- [core/crates/persistence/store/src/SyncOperationStore.rs:1743](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/SyncOperationStore.rs#L1743)
- [core/crates/persistence/store/src/SyncOperationStore.rs:1800](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/SyncOperationStore.rs#L1800)
- [core/crates/persistence/store/src/SyncOperationStore.rs:1874](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/SyncOperationStore.rs#L1874)
- [core/crates/persistence/store/src/transaction/Journal.rs:19](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/transaction/Journal.rs#L19)
- [core/crates/persistence/store/src/transaction/Journal.rs:75](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/transaction/Journal.rs#L75)
- [core/crates/node/runtime/src/SpacePersistenceSyncService.rs:1464](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/SpacePersistenceSyncService.rs#L1464)
- [core/crates/runtime/application/src/core/application/OperitApplication.rs:1003](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/core/application/OperitApplication.rs#L1003)
- [core/crates/node/runtime/src/SyncConsistency.rs:22](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/SyncConsistency.rs#L22)
