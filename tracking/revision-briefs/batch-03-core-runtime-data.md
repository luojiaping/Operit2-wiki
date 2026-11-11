# 修订 brief：core-runtime-data（Issue #28，batch-03）

- 只改 `review/batch-03/core-runtime-data.facts.json` 与 `review/batch-03/core-runtime-data.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：**原有事实偏差**（基线本身就错了，1 项）。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**[P2] 角色与记忆迁移的实际执行阶段写错了，不能把进度文案当作该阶段的副作用。** 正文第 56 行及 fact 第 **43** 条把角色卡、提示词、角色组和记忆写入插件存储归到 `structured_preferences` 阶段。

实际 Operit1SnapshotImportManager.rs:429 第 432 行只是进度提示；第 435 行仅调用 `importSpeechPreferences`。该函数第 **480–487** 行只构建并导入 TTS 配置。真正的 `importCharactersAndMemory` 调用位于后续 `chats` 阶段的 `importChatDatabase` 内，见 Operit1SnapshotImportManager.rs:717。

请把第 56 行和 fact 第 43 条限定为语音配置迁移，将角色/记忆写入放入 chats 调用链。正文第 60 行及 fact 第 47 条本来已正确写出“只采纳语音配置”，修订也能消除页内矛盾。此问题在旧基线与当前源码中均存在。

另核对了内置插件一次性注册、分支来源及正时间戳限制、钩子所有者扩展隔离和返回值结构，所核部分未发现阻断问题。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

## 核实结论（已重钉行号）

- 基线与上游实测一致（文件 `core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs`）：**:432** 为进度提示文案（“正在写入 TTS 配置；角色卡、提示……”）；**:435** 为 `self.importSpeechPreferences(&parsed)?;`；`importSpeechPreferences` 在 :480–487 只构建并导入 TTS 配置；**:717** 为 `let (memoryCount, linkCount) = self.importCharactersAndMemory(...`，位于后续 `chats` 阶段的 `importChatDatabase` 内（基线 :717 同行）。
- 结论：评审属实。`structured_preferences` 阶段只做语音配置迁移；角色/记忆写入在 chats 阶段。页内原 fact #43 与 fact #47（“只采纳语音配置”）自相矛盾，修订后消除。

## 改法

- fact 第 43 条与正文第 56 行同步改：把该阶段限定为语音配置迁移（`structured_preferences` 阶段只调 `importSpeechPreferences`，仅导入 TTS 配置），把角色卡、提示词、角色组和记忆写入插件存储移到 chats 阶段调用链（`importChatDatabase` 内调 `importCharactersAndMemory`，`:717`）。
- ref 按落笔重钉（:435、:717 为锚点；:432 是进度文案行，如引用它须确认窗口内含对应符号）；改前按断言原文逐条再钉一次行号，不要只按编号。
- 改完核对正文第 60 行与 fact 第 47 条，确认页内不再矛盾。

## 验收

- facts 总数预计不变（以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-03`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果。
