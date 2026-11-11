本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**[P2] 角色与记忆迁移的实际执行阶段写错了，不能把进度文案当作该阶段的副作用。** [正文第 56 行](https://github.com/luojiaping/Operit2-wiki/blob/cd042091244eb5bc5ab9c035342b0f88bc2f9e3d/review/batch-03/core-runtime-data.md#L56)及 fact 第 **43** 条把角色卡、提示词、角色组和记忆写入插件存储归到 `structured_preferences` 阶段。

实际 [Operit1SnapshotImportManager.rs:429](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs#L429) 第 432 行只是进度提示；第 435 行仅调用 `importSpeechPreferences`。该函数第 **480–487** 行只构建并导入 TTS 配置。真正的 `importCharactersAndMemory` 调用位于后续 `chats` 阶段的 `importChatDatabase` 内，见 [Operit1SnapshotImportManager.rs:717](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs#L717)。

请把第 56 行和 fact 第 43 条限定为语音配置迁移，将角色/记忆写入放入 chats 调用链。正文第 60 行及 fact 第 47 条本来已正确写出“只采纳语音配置”，修订也能消除页内矛盾。此问题在旧基线与当前源码中均存在。

另核对了内置插件一次性注册、分支来源及正时间戳限制、钩子所有者扩展隔离和返回值结构，所核部分未发现阻断问题。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

