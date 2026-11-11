# 修订 brief：agent-character-cards（Issue #40，batch-04）

- 只改 `review/batch-04/agent-character-cards.facts.json` 与 `review/batch-04/agent-character-cards.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：**原有事实偏差**（基线本身就错了，1 项，涉及 3 处正文 + 2 条 fact）。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查版本：wiki `66baaf09`；对照上游最新 main `053c6686`，并检查相对条目原基线 `364d1d594` 的变化。

**[P2] Core 持久化聊天扩展、插件绑定文件与内部 ChatMarker 被混为一体。** 正文第 45 行及 fact 第 **12** 条称“绑定选择串以 version 1 的 ChatMarker 存在聊天扩展里”。真实创建入口 chat-lifecycle.ts:124 先将选择写入插件草稿绑定，返回给 Core 的扩展只有 `{recordId: chatId, schemaVersion: 1}`（第 127 行）。chats.ts:98 再在正式提交时将草稿转为插件偏好里的 binding_<chatId>。

执行解析也不是直接从 Core 扩展取选择：public-api.ts:11 先按 chatId 读取插件自己的绑定，然后临时构造 `{version:1, selection}` 写入内部 request.chatExtension，交给领域解析。因此正文第 **93** 行、调用链第 **166** 行及 fact 第 **54** 条也需补上公开 API 的这一步。

请明确：Core 扩展保存不透明引用；选择串由插件绑定文件持有；公开解析 API 读取绑定后构造内部 ChatMarker。仅凭 chat-markers.ts 的类型或注释不能判断真实持久化格式。这样也能与本页第 43、65–68 行已有描述一致，避免读者以为修改 Core 聊天扩展里的 selection 就能更改实际角色绑定。这项在原基线也存在。

另核对了草稿提交/作废、提示词拼接顺序、群组参与者，以及主题/TTS 应用的确认和错误传播。

本轮核对正文、同名 `.facts.json` 和固定提交实现，语义结论限于所述重点抽查范围；未运行编译、构建、测试或实机实验。修订时请同步更新正文及对应原子事实，并重核源码引用。

## 核实结论（已重钉行号）

- 基线与上游实测一致（`plugins/packages/buildin/character_cards/src/`）：`chat-lifecycle.ts:124` 为 `const result = await initializeChatExtension(payload, { readActiveSelectio...`（先将选择写入插件草稿绑定）；**:127** 为 `return { extension: { recordId: payload.chat.id, schemaVersion: 1 } };`（返回给 Core 的扩展只有不透明引用）；`storage/chats.ts:98` 为 `async commitDraftBinding(chatId: string): Promise<void> {`（正式提交时将草稿转为插件偏好里的 `binding_<chatId>`，具体写入行在函数体内，落笔时重钉）；`public-api.ts:11` 为 `export async function chatConfigurationResolveApi(event: ToolPkg.PublicApiEvent<...`，**:15** 为 `const binding = await findChatBinding(request.chatId);`（先按 chatId 读取插件自己的绑定），其后临时构造 `{version:1, selection}` 写入内部 `request.chatExtension` 交给领域解析（:16 行附近，落笔时重钉）。
- 结论：评审属实。三者必须分开：Core 扩展只存不透明引用；选择串由插件绑定文件持有；公开解析 API 读取绑定后构造内部 ChatMarker。

## 改法

- fact 第 12 条与正文第 45 行同步改：删除“绑定选择串以 version 1 的 ChatMarker 存在聊天扩展里”的说法，改为“Core 扩展只保存不透明引用 `{recordId, schemaVersion: 1}`（`chat-lifecycle.ts:127`）；选择串由插件绑定文件持有——创建时先写入插件草稿绑定（`:124`），正式提交时转为插件偏好里的 `binding_<chatId>`（`chats.ts:98` 起）”。
- 正文第 93 行、调用链第 166 行及 fact 第 54 条同步补公开 API 的一步：“公开解析 API 先按 chatId 读取插件自己的绑定（`public-api.ts:15`），再临时构造 `{version:1, selection}` 写入内部 `request.chatExtension`，交给领域解析。”
- 改完核对本页第 43、65–68 行已有描述，确认全页口径一致，不再让读者以为改 Core 聊天扩展里的 selection 就能改实际角色绑定。
- 改前按断言原文逐条再钉一次行号，不要只按编号（尤其 `chats.ts:98` 函数体内的写入行与 `public-api.ts:16` 附近的构造行）。

## 验收

- facts 总数预计不变（以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核——本页是 TS 文件，lint 同样不覆盖 `.ts` 引用，同样须自核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-04`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果。
