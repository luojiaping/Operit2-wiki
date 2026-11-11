第 2 轮复核结论：**本轮已列问题均已修复，未发现新的阻断问题**。

本轮 wiki：`77e3b7ca`；核对源码：上游 main `053c6686`。复核范围是本次修订、对应原子事实及相邻调用链。

正文第 **45–47** 行及 fact 第 **12** 条，已明确 Core 扩展仅持有 `{recordId, schemaVersion:1}`，实际选择由插件绑定文件持有；第 **95** 行、调用链第 **169** 行及 fact 第 **54** 条，也补上“按 chatId 读取插件绑定，再构造内部 request.chatExtension”的步骤。

已重新核对 [chat-lifecycle.ts:124](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/chat-lifecycle.ts#L124)、[chats.ts:98](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/storage/chats.ts#L98)与 [public-api.ts:11](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/plugins/packages/buildin/character_cards/src/public-api.ts#L11)。当前归属和调用链与实现一致，正文与 facts 已同步消除将内部选择标记当成 Core 持久化扩展的误解。

本轮为静态差异与源码核对；涉及显示问题时使用了站点同版本 Markdown 渲染器检查。未运行项目编译、构建或测试。

