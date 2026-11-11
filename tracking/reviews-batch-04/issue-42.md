本轮静态审查结论：**本轮未发现阻断问题**。

审查版本：wiki `66baaf09`；对照上游最新 main `053c6686`，并检查相对条目原基线 `364d1d594` 的变化。

已核对 TUI 静态补全表、插件补全展开与关键词选项、交互 shell 分发及参数解析、两种 resume 的区别、附件队列的成功清空/失败保留，以及 CLI 插件命令目录与冲突检查。正文明确区分“补全定义”与“真正执行分发”，没有把 TUI 的 81 条建议当成交互 shell 都支持的命令。

所核关键实现包括 [commands.rs:558](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/apps/cli/src/tui/input/commands.rs#L558) 的插件候选展开、[commands.rs:656](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/apps/cli/src/tui/input/commands.rs#L656) 的前缀筛选、[chat_runtime.rs:517](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/apps/cli/src/chat_runtime.rs#L517) 的 shell 分发及第 643 行的引用/转义解析。/resume 排除当前会话、按 updatedAt 和 displayOrder 选择，启动 --resume 从全部历史选择，两者描述准确。

一项非阻断源码更新建议：当前 [mod.rs:1443](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/apps/cli/src/cli/mod.rs#L1443) 新增 cli_core_command_args，把调用者目录规范化为 VFS 工作目录并前置 --cwd；本地与 daemon 的 Core 命令转发都会携带它。更新本页调用链和第 105 行/fact 第 **89** 条附近时可补充，避免仍只说明 --json 转发。原有 --json 事实本身仍成立；相关旧引用因新增 helper 有行号移动。

本轮核对正文、同名 `.facts.json` 和固定提交实现，语义结论限于所述重点抽查范围；未运行编译、构建、测试或实机实验。修订时请同步更新正文及对应原子事实，并重核源码引用。

