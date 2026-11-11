本轮静态审查结论：**本轮未发现阻断问题**。

审查版本：wiki `66baaf09`；对照上游最新 main `053c6686`，并检查相对条目原基线 `364d1d594` 的变化。

重点核对了候选入队的作者/owner 权限、owner 内幂等、生产 CoreNode 限定、30 分钟租约回收、5 条门槛和每聊天 20 条上限、候选校验失败保留、原始消息提取、重建进度，以及 64 条嵌入批次与最多 4 个 worker。参见 [scheduler.ts:53](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts#L53)、[scheduler.ts:310](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts#L310)、[analysis.ts:239](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts#L239)。这些关键机制及当前作者缺失时不自动入队的描述与实现一致，相关插件实现相对旧基线未变化。

有三项非阻断精确化建议：

- facts 第 **115** 条的“先落盘当前窗口”应改成“先追加到内存中的 windows 计划数组”。[chat.ts:197](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts#L197) 的 emit 只做数组 push；真正写入任务状态发生在 [scheduler.ts:121](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts#L121) 规划完窗口后第 130 行的 writeMemoryJobState。正文主流程没有宣称 emit 自行持久化，建议修正这条机器事实。
- 正文第 **115** 行、fact 第 **116** 条的 8–48 是 windowMessageCount 的钳制阈值；完整 messages 还会带入上一条用户上下文，不能解释为每个结果窗口总条数始终不超过 48（chat.ts 第 199、209 行）。
- 正文“间隔推进”可补上 facts 第 **57、58** 条已有的门控：全局 autoUpdateEnabled 必须开启，autoSaveIntervalMinutes 不能为 0，且需到 nextAutoSaveRunAtMs，见 scheduler.ts 第 **347–355** 行。60 秒 hook 是检查频率，达到 5 条也需满足这些条件。

本轮核对正文、同名 `.facts.json` 和固定提交实现，语义结论限于所述重点抽查范围；未运行编译、构建、测试或实机实验。修订时请同步更新正文及对应原子事实，并重核源码引用。

