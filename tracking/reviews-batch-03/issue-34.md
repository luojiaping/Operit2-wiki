本轮静态审查结论：**本轮未发现阻断问题**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

核对了 --json 识别、chat 分发及历史操作、model 的默认管理器路径与密钥长度输出、tool exec 的 Direct 策略及末项结果、sync reset-transactions，以及帮助文本与实现的差异。所核原有机制与正文/facts一致。

有两项非阻断更新建议：

- **补充最新 main 新增的 --cwd 调用作用域。** [lib.rs:32](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/command/core/src/lib.rs#L32) 在剥离 --json 后，识别首位 `--cwd <VFS directory>`，解析 VFS 目录并从参数中移除；第 **49–65** 行在指定的 ToolRuntimeContext 中分发命令。因此 [正文第 35 行](https://github.com/luojiaping/Operit2-wiki/blob/cd042091244eb5bc5ab9c035342b0f88bc2f9e3d/review/batch-03/core-command.md#L35)、入口机制和第 137–138 行调用链可补上这一步。附件也已改为经 `command_file_path` 解析，而不是原来的 std::fs::canonicalize；见 [util.rs:52](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/command/core/src/commands/util.rs#L52)及 [chat.rs:606](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/command/core/src/commands/chat.rs#L606)。这项是上游新增行为，非原基线事实错误，迁移源码版本时请补充事实并重定位相关引用。
- 正文第 **18** 行“其余 10 组”实际列出 **11** 组：README 的 14 组中，本页展开 chat/model/tool 三组，另加 README 未列出的 sync。可直接改计数或删去数量。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

