## luojiaping @ 2026-11-11T07:10:07Z (https://github.com/luojiaping/Operit2-wiki/issues/11#issuecomment-6789515331)

审查结论：**需修改**。

核对基线：wiki `b75bcad9`，上游 `AAswordman/Operit2` 最新 `main` 已确认是 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与 wiki 标注一致。以下是静态源码审查意见。

1. **[P1] 不可达 Binding 的行为有三种互不一致的说法。** [正文第 115 行](https://github.com/luojiaping/Operit2-wiki/blob/b75bcad9d63959f0108f81193119e372eca38f4a/review/batch-01/arch-routing.md#L115)写“原子接管”，第 123 行写必须明确报错，第 141 行又写当前代码静默改成本机。[CoreNodeRouter.rs:451–457](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/CoreNodeRouter.rs#L451) 的 `effectiveBinding` 仅修改所读记录副本的 `nodeId`，不提交 CAS、不持久化新归属、不递增 generation。[link-access-architecture.md:247](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/docs/link-access-architecture.md#L247) 也将当前偏差列为待清理问题。应分别说明当前行为、设计约束和待清理项，不能把本次选择本地执行写成所有权已完成原子接管；对应 facts 也需修订。

2. **[P1] 工具交接流程把设计屏障和代际去重写成了当前保证。** 第 109 行和第 183–189 行描述 `requiredClock` 及按 `executionGeneration` 判重。真实交接路径是先 [同步目标:1027–1029](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/RuntimeRemoteLinkService.rs#L1027)，再 [CAS:1044](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/RuntimeRemoteLinkService.rs#L1044)、[安装 Binding operation:1064](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/RuntimeRemoteLinkService.rs#L1064)，最后 [调用 AfterChangeRoute:1083](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/RuntimeRemoteLinkService.rs#L1083)。实际运输的 [CoreRouteResumeContext:21–35](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/tool/services/src/runtime_support.rs#L21) 包含 `runtimeChatHistory` 等字段，没有文中所述的 `requiredClock` / execution generation 参数；目标 [resumeFromRouteContext:776–835](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/services/ChatServiceCore.rs#L776) 接收此上下文并取得本地执行 lease。请把架构文档的屏障/代际去重机制标为设计约束，补上该提交真实调用链；在找到对应运行时实现前，不能据文档文字承诺这些安全保证已实现。正文、调用链和 facts 需要一起修订。此项为**源码直引、wiki 未覆盖**。

3. **[P2] 四字段 RoutedLink 应注明是概念示意，避免被当成 wire schema。** 第 21、61 行称外层“只含”四字段，第 65 行又列出六字段类型。实际 [protocol.rs:984–992](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/link/src/protocol.rs#L984) 的 `RoutedCoreRequest<T>` 还包含 `originNodeId` 和 `routeKind`，[peer/dispatch.rs:20](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/peer/dispatch.rs#L20) 使用这个完整类型编码请求。建议以真实六字段类型描述序列化契约；四字段图示如保留，应明确省略了来源和路由种类。

4. **[P2] 为机制段落和调用链补齐就近的 file:line 引用。** 第 43–143、170–198 行有大量具体行为断言未在对应段落/步骤附源码引用；关键符号表中的定义无法单独支撑完整交接流程、安全校验与共享 Watch 生命周期。建议把事实文件里的证据补到相应段落，尤其使用上述实现证据修正涉及安全保证的部分。

已抽查 Dijkstra、TTL 与慢订阅者处理的源文档，以及实际 RoutedCoreRequest、不可达路由和交接实现；本页 76 条 facts 引用路径均存在且行号未越界。未执行编译、构建或测试。


