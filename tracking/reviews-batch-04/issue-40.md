本轮静态审查结论：**需修改**。

审查版本：wiki `66baaf09`；对照上游最新 main `053c6686`，并检查相对条目原基线 `364d1d594` 的变化。

**[P2] Core 持久化聊天扩展、插件绑定文件与内部 ChatMarker 被混为一体。** [正文第 45 行](https://github.com/luojiaping/Operit2-wiki/blob/66baaf09e0d7d65172a961162d7eaf135c4f30de/review/batch-04/agent-character-cards.md#L45)及 fact 第 **12** 条称“绑定选择串以 version 1 的 ChatMarker 存在聊天扩展里”。真实创建入口 [chat-lifecycle.ts:124](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/chat-lifecycle.ts#L124) 先将选择写入插件草稿绑定，返回给 Core 的扩展只有 `{recordId: chatId, schemaVersion: 1}`（第 127 行）。[chats.ts:98](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/storage/chats.ts#L98) 再在正式提交时将草稿转为插件偏好里的 binding_<chatId>。

执行解析也不是直接从 Core 扩展取选择：[public-api.ts:11](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/public-api.ts#L11) 先按 chatId 读取插件自己的绑定，然后临时构造 `{version:1, selection}` 写入内部 request.chatExtension，交给领域解析。因此正文第 **93** 行、调用链第 **166** 行及 fact 第 **54** 条也需补上公开 API 的这一步。

请明确：Core 扩展保存不透明引用；选择串由插件绑定文件持有；公开解析 API 读取绑定后构造内部 ChatMarker。仅凭 chat-markers.ts 的类型或注释不能判断真实持久化格式。这样也能与本页第 43、65–68 行已有描述一致，避免读者以为修改 Core 聊天扩展里的 selection 就能更改实际角色绑定。这项在原基线也存在。

另核对了草稿提交/作废、提示词拼接顺序、群组参与者，以及主题/TTS 应用的确认和错误传播。

本轮核对正文、同名 `.facts.json` 和固定提交实现，语义结论限于所述重点抽查范围；未运行编译、构建、测试或实机实验。修订时请同步更新正文及对应原子事实，并重核源码引用。

