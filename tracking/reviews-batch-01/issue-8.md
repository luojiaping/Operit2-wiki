## luojiaping @ 2026-11-11T07:09:48Z (https://github.com/luojiaping/Operit2-wiki/issues/8#issuecomment-6789510166)

审查结论：**需修改**。

核对基线：wiki `b75bcad9`，上游 `AAswordman/Operit2` 最新 `main` 已确认是 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与 wiki 标注一致。以下是静态源码审查意见。

**[P2] 第 34、155 行把 syncClockDigest 描述为“每个同步周期先发送”的探针，需要补充适用条件。** [SpacePersistenceSyncService.rs:716–734](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/SpacePersistenceSyncService.rs#L716) 先处理退避、待处理工作和失败重试；未获存储复制授权的成员走 `authority_only` 分支，直接继续控制交换，只有正常存储复制门控分支才调用摘要探针。建议限定为“具备存储复制授权、处于正常变更门控状态的可达成员使用 `syncClockDigest` 判断是否需要完整交换”。这是**源码直引、wiki 未覆盖**。 请统一修正 AI 速览和调用链，并把该条件及真实实现引用补进 facts；当前 facts 尚未覆盖这项探针断言。

核对范围：Space 定位（docs/core-node-space-binding-architecture.md:28）、mDNS 查询契约与 Apple Host 边界（docs/device-space-lan-discovery.md:5、37）、接收与业务应用分离（docs/sync-architecture.md:23），并核对 reconcileSharedSpace 分发（NodeSpaceService.rs:384）与退出保留直接配对记录（RuntimeRemoteLinkService.rs:734）。这些抽查项与引用一致。frontmatter 和六个固定小节齐全；本页 43 条 facts 引用路径均存在且行号未越界。未执行编译、构建或测试。


