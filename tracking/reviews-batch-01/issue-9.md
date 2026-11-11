## luojiaping @ 2026-11-11T07:09:55Z (https://github.com/luojiaping/Operit2-wiki/issues/9#issuecomment-6789511907)

审查结论：**需修改**。

核对基线：wiki `b75bcad9`，上游 `AAswordman/Operit2` 最新 `main` 已确认是 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与 wiki 标注一致。以下是静态源码审查意见。

1. **[P1] 交接设计被写成了已实现的调用链。** [正文第 66 行](https://github.com/luojiaping/Operit2-wiki/blob/b75bcad9d63959f0108f81193119e372eca38f4a/review/batch-01/arch-binding.md#L66)、第 88–100 行及第 170–179 行描述等待 `requiredClock`、按 `(chatId, executionGeneration)` 判重并提交 `completedExecutionGeneration`。真实交接路径是先 [同步目标:1027–1029](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/RuntimeRemoteLinkService.rs#L1027)，再 [CAS:1044](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/RuntimeRemoteLinkService.rs#L1044)、[安装 Binding operation:1064](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/RuntimeRemoteLinkService.rs#L1064)，最后 [调用 AfterChangeRoute:1083](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/RuntimeRemoteLinkService.rs#L1083)。实际运输的 [CoreRouteResumeContext:21–35](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/tool/services/src/runtime_support.rs#L21) 包含 `runtimeChatHistory` 等字段，没有文中所述的 `requiredClock` / execution generation 参数；目标 [resumeFromRouteContext:776–835](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/services/ChatServiceCore.rs#L776) 接收此上下文并取得本地执行 lease。请把架构文档的屏障/代际去重机制标为设计约束，补上该提交真实调用链；在找到对应运行时实现前，不能据文档文字承诺这些安全保证已实现。正文、调用链和 facts 需要一起修订。此项为**源码直引、wiki 未覆盖**。

2. **[P1] 第 94 行“目标不可达时原子接管”不符合当前实现。** [CoreNodeRouter.rs:451–457](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/CoreNodeRouter.rs#L451) 的 `effectiveBinding` 仅修改所读记录副本的 `nodeId`，不提交 CAS、不持久化新归属、不递增 generation。[link-access-architecture.md:247](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/docs/link-access-architecture.md#L247) 也将当前偏差列为待清理问题。应分别说明当前行为、设计约束和待清理项，不能把本次选择本地执行写成所有权已完成原子接管；对应 facts 也需修订。

3. **[P2] 收紧 generation 的递增条件。** 第 58 行写“每次比较写入成功后 generation 单调递增”，但同页第 74 行又正确说明同目标直接返回。[CoreNodeBindingStore.rs:200–209](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/CoreNodeBindingStore.rs#L200) 在同目标分支返回 `Ok` 且保持 generation，只有实际切换到不同目标才执行 `+1`。建议统一写为“实际切换到不同目标并提交成功时递增；同目标调用保持原记录”，并修订相应 fact。

已核对 Binding 字段、初始 generation、CAS 同目标分支及实际交接代码；本页 54 条 facts 引用路径均存在且行号未越界。引用能定位到设计文档，不等于运行时已经提供相同保证。未执行编译、构建或测试。


