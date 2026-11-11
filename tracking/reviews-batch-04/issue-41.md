本轮静态审查结论：**需修改**。

审查版本：wiki `66baaf09`；对照上游最新 main `053c6686`，并检查相对条目原基线 `364d1d594` 的变化。

**[P2] 共用 functionName/functionSource 的结论应限定为 hook 注册，不能包含 AI Provider 注册。** [正文第 55 行](https://github.com/luojiaping/Operit2-wiki/blob/66baaf09e0d7d65172a961162d7eaf135c4f30de/review/batch-04/agent-hooks.md#L55)和 fact 第 **18** 条称“除菜单对话框子结构外，所有注册结构都有 containerPackageName、functionName 与可选 functionSource”。

实际同页已列出的 [ToolPkgHooks.rs:144](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs#L144) 没有通用 functionName/functionSource；它包含四组独立方法字段：listModelsFunctionName/Source、sendMessageFunctionName/Source、testConnectionFunctionName/Source、calculateInputTokensFunctionName/Source。

请把范围改为“14 个 hook 注册结构具有这些共用字段”，将菜单对话框与 AI Provider 按各自契约说明。这也与正文第 54 行、fact 第 14 条“AI Provider 注册不是 hook 注册”的区分一致。该问题在原基线和最新源码均存在。

其余已核对 1–60 秒 pre-hook 超时限制及阶段名单、同一分发链共享总截止时间、通知 hook 单项失败后继续循环，以及摘要 hook 按序应用变更和传播错误，见 [ToolPkgPreHookTimeout.rs:20](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs#L20)、[ToolPkgChatRuntimeHookBridge.rs:102](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs#L102)、[SummaryHookRegistry.rs:78](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs#L78)。这些抽查项与正文一致。

本轮核对正文、同名 `.facts.json` 和固定提交实现，语义结论限于所述重点抽查范围；未运行编译、构建、测试或实机实验。修订时请同步更新正文及对应原子事实，并重核源码引用。

