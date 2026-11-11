## luojiaping @ 2026-11-11T07:09:43Z (https://github.com/luojiaping/Operit2-wiki/issues/7#issuecomment-6789508624)

审查结论：**需修改**。

核对基线：wiki `b75bcad9`，上游 `AAswordman/Operit2` 最新 `main` 已确认是 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与 wiki 标注一致。以下是静态源码审查意见。

1. **[P2] 第 115 行的 list_core_nodes 返回结构写错。** 正文及 facts 第 29 条写成 `{ currentNodeId, nodeIds }`，实际 [ToolRegistration.rs:179–198](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/tool/services/src/tools/ToolRegistration.rs#L179) 返回 `{ currentNodeId, nodes }`。`nodes` 是对象数组，每项有 `nodeId`、`displayName`、`userName`、`platform`、`model`、`reachable`、`canExecute`，并按条件带 `relayHops` / `relayPath`。建议更正正文和 facts，并引用工具实现，避免客户端据此读取不存在的 `nodeIds` 字段；架构文档的简化伪代码不能替代实际接口。

2. **[P2] 第 141 行“每个同步周期对每个可达成员先发 syncClockDigest”过于绝对。** [SpacePersistenceSyncService.rs:716–734](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/SpacePersistenceSyncService.rs#L716) 先处理退避、待处理工作和失败重试；未获存储复制授权的成员走 `authority_only` 分支，直接继续控制交换，只有正常存储复制门控分支才调用摘要探针。建议限定为“具备存储复制授权、处于正常变更门控状态的可达成员使用 `syncClockDigest` 判断是否需要完整交换”。这是**源码直引、wiki 未覆盖**。 请同步修正 facts 第 43 条。

另已直接核对 CoreApplication::start 的组装顺序（core/crates/application/core/src/lib.rs:81）、CoreNodeRouter 类型（CoreNodeRouter.rs:65）和 Host 能力容器（HostManager.rs:139），这些抽查项与引用一致。frontmatter 和六个固定小节齐全；本页 135 条 facts 引用路径均存在且行号未越界。未执行编译、构建或测试。


