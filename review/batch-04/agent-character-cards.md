---
title: 角色卡
module: agent
platforms: [all]
sources: 16
date: 2026-11-11
---

## 概述

- 角色卡插件是 ToolPkg `com.operit.character_cards`，角色卡与记忆同属一个包。(plugins/packages/buildin/character_cards/README.md:6)
- 一次聊天绑定一张角色卡、一个群组，或不绑角色只用模型；绑定以选择串表达，形态为 `card`、`group` 或 `model` 加冒号加标识。(plugins/packages/buildin/character_cards/src/chat-bindings.ts:10)
- 绑定在聊天创建前由插件的聊前创建钩子确定，先写草稿绑定。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:126)
- 执行时插件按绑定解析参与者档案，把角色提示词组装进对话。(plugins/packages/buildin/character_cards/src/domain.ts:395)
- 主题只以引用形式跟随选择，不归插件所有；主题的读取、校验与应用属于独立的主题所有者。(plugins/packages/buildin/character_cards/src/selection-application.ts:11)

## AI 速览

- `parseChatSelection` — 解析 `card` / `group` / `model` 选择串。(plugins/packages/buildin/character_cards/src/chat-bindings.ts:10)
- `ChatBinding` — 聊天与选择的绑定记录，字段为 `chatId` 与 `selection`。(plugins/packages/buildin/character_cards/src/model.ts:447)
- `beforeChatCreate` — 聊前创建钩子，确定新聊天的绑定。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:118)
- `prepareChatBinding` — 预写草稿绑定。(plugins/packages/buildin/character_cards/src/storage/chats.ts:81)
- `commitDraftBinding` — 把草稿绑定转为正式绑定。(plugins/packages/buildin/character_cards/src/storage/chats.ts:98)
- `abortDraftBinding` — 作废草稿绑定。(plugins/packages/buildin/character_cards/src/storage/chats.ts:110)
- `combineCharacterPrompt` — 按固定顺序组装角色提示词。(plugins/packages/buildin/character_cards/src/character-prompt.ts:6)
- `withGroupParticipantPrompt` — 给群组成员档案追加角色规划提示与有序成员名。(plugins/packages/buildin/character_cards/src/domain.ts:427)
- `activateChatSelection` — 打开会话时按绑定恢复生效选择。(plugins/packages/buildin/character_cards/src/service-runtime.ts:103)
- `SelectionReferences` — 选择、主题引用与 TTS 引用的组合。(plugins/packages/buildin/character_cards/src/selection-application.ts:11)
- 主入口：`registerChatInitialization` 注册的 `chat-initialization` 钩子。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:132)
- 数据流向：创建输入 → 钩子校验选择 → 预写草稿绑定。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:126)
- 数据流向：执行时按绑定解析档案并组装提示词。(plugins/packages/buildin/character_cards/src/domain.ts:395)

## 核心机制

### 角色卡与聊天如何绑定

- 聊天选择串只有三种形态：`card`、`group`、`model` 加冒号加标识，由 `parseChatSelection` 用正则解析。(plugins/packages/buildin/character_cards/src/chat-bindings.ts:10)
- `model` 类型选择只接受 id 为 `chat` 的值，其他值直接报错。(plugins/packages/buildin/character_cards/src/chat-bindings.ts:13)
- `requireChatSelection` 要求选择串恰好命中一条已存卡片或群组记录，否则报错。(plugins/packages/buildin/character_cards/src/chat-bindings.ts:22)
- 成员为空的群组不能作为绑定目标，校验时直接报错。(plugins/packages/buildin/character_cards/src/chat-bindings.ts:26)
- `selectionForActive` 把当前生效提示词映射为选择串：`Model` 对应 `model:chat`，`CharacterCard` 对应 `card:` 加卡片 id，其余对应 `group:` 加群组 id。(plugins/packages/buildin/character_cards/src/chat-bindings.ts:32)
- `ChatBinding` 只有 `chatId` 与 `selection` 两个字段。(plugins/packages/buildin/character_cards/src/model.ts:447)
- 绑定存在插件自己的偏好文件里，键名是 `binding_` 加聊天 id。(plugins/packages/buildin/character_cards/src/storage/chats.ts:22)
- `findChatBinding` 查无绑定时返回 `null`，不抛错。(plugins/packages/buildin/character_cards/src/storage/chats.ts:20)
- 绑定选择串以 version 1 的 `ChatMarker` 存在聊天扩展里。(plugins/packages/buildin/character_cards/src/chat-markers.ts:8)
- `decodeChatMarker` 拒绝扩展里出现 `groupId` 字段，群组成员关系只由插件文件拥有。(plugins/packages/buildin/character_cards/src/chat-markers.ts:47)
- `encodeChatMarker` 只改选择字段，保留扩展里其他已校验的业务字段。(plugins/packages/buildin/character_cards/src/chat-markers.ts:51)
- 插件命名空间常量是 `com.operit.character_cards`。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:24)
- `createChatInput` 生成以插件命名空间为键的新聊天输入。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:51)
- 选择标记为 `{ version: 1, selection }`，`parseChatSelectionMarker` 要求 version 必须为 1。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:41)
- `readMessageAuthor` 经 `Tools.Chat.readExtension` 读消息扩展里的作者身份。(plugins/packages/buildin/character_cards/src/chat-storage.ts:32)
- 消息作者身份扩展里只有一个键，取出的 `participantId` 即作者标识。(plugins/packages/buildin/character_cards/src/chat-storage.ts:40)

### 角色卡的生命周期由谁管理

- `registerChatInitialization` 注册 id 为 `chat-initialization` 的聊前创建钩子，处理函数是 `beforeChatCreate`。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:132)
- `registerToolPkg` 是插件注册入口，内含钩子与 API 的挂载。(plugins/packages/buildin/character_cards/src/main.ts:51)
- `registerChatInitialization` 在插件注册入口内被调用，完成钩子挂载。(plugins/packages/buildin/character_cards/src/main.ts:58)
- `beforeChatCreate` 只接受 `before_create` 事件。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:118)
- 分支建聊时，`beforeChatCreate` 先查源聊天的绑定，无绑定则回退为 `model:chat`。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:122)
- `parseChatInitialization` 要求载荷恰好 7 个顶层字段，且 eventName 为 `before_create`、creationKind 为 `new` 或 `branch`。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:63)
- 无源聊天时，源扩展与源消息时间戳必须同时为 null。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:73)
- `initializeChatExtension` 按三路定选择：显式 input 直接校验；有源聊天时从源扩展解码标记再校验；两者皆无时读当前生效选择。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:87)
- `requireSelection` 对卡片调 `character.get` 校验存在；对群组要求成员非空并逐个校验成员卡片。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:106)
- 聊前创建钩子在原生创建提交前调 `prepareChatBinding` 预写草稿绑定，并返回含 `recordId` 与 `schemaVersion` 的扩展。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:126)
- `prepareChatBinding` 以 `draft_` 加聊天 id 为键写草稿，已有草稿时报错。(plugins/packages/buildin/character_cards/src/storage/chats.ts:81)
- `commitDraftBinding` 从草稿键读出绑定并校验标记，再转为正式绑定。(plugins/packages/buildin/character_cards/src/storage/chats.ts:98)
- 提交时若正式绑定已存在则报错，提交成功后草稿键被删除。(plugins/packages/buildin/character_cards/src/storage/chats.ts:104)
- `abortDraftBinding` 只删草稿键，不动已提交的正式绑定。(plugins/packages/buildin/character_cards/src/storage/chats.ts:110)
- `readDraftBinding` 无草稿时报错。(plugins/packages/buildin/character_cards/src/storage/chats.ts:91)
- `readChatBinding` 要求绑定已持久化，并对照仓库卡片与群组校验选择串。(plugins/packages/buildin/character_cards/src/storage/chats.ts:26)
- `listChatBindings` 从一次不可变偏好快照里列出全部 `binding_` 前缀记录。(plugins/packages/buildin/character_cards/src/storage/chats.ts:33)
- `bindingsForChats` 批量读多个聊天的选择串，缺绑定的聊天不进结果。(plugins/packages/buildin/character_cards/src/storage/chats.ts:37)
- `writeChatBinding` 校验标记与选择串后才把绑定写入偏好文件。(plugins/packages/buildin/character_cards/src/storage/chats.ts:73)
- `chat.configuration.draft.commit` 只发布 Core 认证提交选中的已预写绑定。(plugins/packages/buildin/character_cards/src/public-api.ts:473)
- `chat.configuration.draft.abort` 在 Core 复用已有会话后移除作废草稿。(plugins/packages/buildin/character_cards/src/public-api.ts:474)
- `chat.configuration.draft.resolve` 只解析已预写的创建草稿，不暴露已提交聊天查询。(plugins/packages/buildin/character_cards/src/public-api.ts:472)
- 插件注册 `chat.configuration.delete` 公开 API，Core 删会话后用它释放插件侧绑定。(plugins/packages/buildin/character_cards/src/public-api.ts:74)
- `chatConfigurationDeleteApi` 只接受 host 调用方；无绑定时直接返回已删除，不报错。(plugins/packages/buildin/character_cards/src/public-api.ts:42)
- `deleteChatBinding` 删 `binding_` 键并报告该绑定是否真实存在过。(plugins/packages/buildin/character_cards/src/storage/chats.ts:118)
- Core 删会话后经该 API 释放插件绑定，历史快照仍保留，Core 不直接调绑定业务 API。(plugins/packages/buildin/character_cards/README.md:165)
- `chatsForMemoryOwner` 反查属于某记忆 owner 的全部绑定聊天。(plugins/packages/buildin/character_cards/src/storage/chats.ts:48)

### 角色提示词如何组装进对话

- 提示词组装只接受 `CHAT` 或 `VOICE` 两种功能类型，其他值直接报错。(plugins/packages/buildin/character_cards/src/character-prompt.ts:14)
- 提示词先放角色设定，再放 `CHAT` 或 `VOICE` 的专属附加内容。(plugins/packages/buildin/character_cards/src/character-prompt.ts:16)
- 标签内容按已挂标签加追加标签去重后的顺序拼接。(plugins/packages/buildin/character_cards/src/character-prompt.ts:20)
- 高级自定义提示词是最后一段，各段以双换行连接后整体 trim。(plugins/packages/buildin/character_cards/src/character-prompt.ts:27)
- 标签读取时校验返回的标签 id 与请求 id 一致，不一致报错。(plugins/packages/buildin/character_cards/src/character-prompt.ts:23)
- 内容为空的标签不参与拼接。(plugins/packages/buildin/character_cards/src/character-prompt.ts:25)
- `combinePrompts` 先按 id 取卡片，再调 `combineCharacterPrompt` 组装。(plugins/packages/buildin/character_cards/src/operations.ts:530)
- 执行侧解析先从聊天扩展解码标记，再用 `parseChatSelection` 解析选择串。(plugins/packages/buildin/character_cards/src/domain.ts:395)
- 单卡解析出的提示词直接作为参与者的 `introPrompt`。(plugins/packages/buildin/character_cards/src/domain.ts:375)
- `withGroupParticipantPrompt` 为群组成员的执行档案追加角色规划提示与有序成员名。(plugins/packages/buildin/character_cards/src/domain.ts:427)
- 群组追加提示直接拼在参与者原 `introPrompt` 之后返回新档案。(plugins/packages/buildin/character_cards/src/group-execution/prompts.ts:19)
- 追加提示末尾列出有序成员名，格式为 `Group participants: ` 加名字串。(plugins/packages/buildin/character_cards/src/group-execution/prompts.ts:18)
- 群组执行的历史策略是参与者隔离、用户消息打标签。(plugins/packages/buildin/character_cards/src/domain.ts:438)
- 纯模型执行的档案 `introPrompt` 为空、主记忆 owner 为空串。(plugins/packages/buildin/character_cards/src/chat-markers.ts:119)
- `userPreferencesText` 只在全局记忆偏好开启用户描述时才读，否则为空串。(plugins/packages/buildin/character_cards/src/domain.ts:371)
- 记忆主 owner：CHARACTER 模式为 `character:` 加卡片 id，SHARED 模式为 `shared:` 加共享库 id。(plugins/packages/buildin/character_cards/src/domain.ts:354)
- 主记忆 owner 在资源表里可读可写。(plugins/packages/buildin/character_cards/src/domain.ts:363)
- 卡片未指定 TTS 配置时用请求的默认 TTS 配置。(plugins/packages/buildin/character_cards/src/domain.ts:349)
- 执行数据 `ExecutionData` 含 version、selection、promptFunctionType、primaryOwnerKey、profile 与 participants。(plugins/packages/buildin/character_cards/src/chat-markers.ts:13)
- 单卡执行要求恰好一个参与者且其 id 等于卡片 id。(plugins/packages/buildin/character_cards/src/chat-markers.ts:117)
- 群组执行把身份约束与有序成员名加进各参与者的提示词，同一档案冻结进消息快照。(plugins/packages/buildin/character_cards/README.md:157)
- 单卡执行只用卡片自己的 authored 提示词。(plugins/packages/buildin/character_cards/README.md:160)

### 角色卡与主题配置的关系

- 卡片有一个可空的 `themeConfigId` 字段。(plugins/packages/buildin/character_cards/src/model.ts:21)
- 群组也有一个可空的 `themeConfigId` 字段。(plugins/packages/buildin/character_cards/src/model.ts:45)
- 选择引用只存 `themeConfigId` 引用，不存主题本身。(plugins/packages/buildin/character_cards/src/selection-application.ts:11)
- `model` 选择的主题与 TTS 引用均为 null。(plugins/packages/buildin/character_cards/src/selection-application.ts:65)
- 卡片选择的主题引用取自卡片自身的 `themeConfigId`，群组取自群组的。(plugins/packages/buildin/character_cards/src/selection-application.ts:69)
- 主题只在 `themeConfigId` 非空时才应用，通过主题所有者的 `applyTheme` 确认。(plugins/packages/buildin/character_cards/src/selection-application.ts:116)
- 主题或 TTS 应用失败时抛 `SelectionApplicationFailure`，记录已确认步骤与失败步骤。(plugins/packages/buildin/character_cards/src/selection-application.ts:94)
- 应用失败后不自动撤销或重试，配置的实际存储状态待核对。(plugins/packages/buildin/character_cards/src/selection-application.ts:102)
- 选择提交前先校验主题与 TTS 引用，整次提交恰好校验一次。(plugins/packages/buildin/character_cards/src/selection-application.ts:161)
- 主题选择器经 `Tools.Theme.listConfigs()` 读真实命名配置。(plugins/packages/buildin/character_cards/README.md:114)
- 选中只暂存编辑器的 `themeConfigId`，保存后才持久化，激活时经 `Tools.Theme.applyConfig(id)` 应用 exact 配置。(plugins/packages/buildin/character_cards/README.md:118)
- 主题引用为 null 表示保持当前主题，群组不借用成员的主题。(plugins/packages/buildin/character_cards/README.md:120)
- 主题引用可编辑，由持久化与互换保留。(plugins/packages/buildin/character_cards/README.md:113)
- 打开会话时，`onChatViewTheme` 在 `view_opened` 事件里调 `activateChatSelection`。(plugins/packages/buildin/character_cards/src/chat-view-theme.ts:5)
- 视图钩子注册 id 为 `character-bound-theme`。(plugins/packages/buildin/character_cards/src/chat-view-theme.ts:13)
- 按绑定类型分派：卡片调 `activePrompt.setCard`，群组调 `activePrompt.setGroup`，纯模型调 `activePrompt.setModel`。(plugins/packages/buildin/character_cards/src/service-runtime.ts:109)
- 无绑定时 `activateChatSelection` 直接返回，不做任何事。(plugins/packages/buildin/character_cards/src/service-runtime.ts:106)
- 插件关闭时 Core 用独立普通模型配置；无角色聊天不注入角色提示词、不授予角色记忆资源。(plugins/packages/buildin/character_cards/README.md:389)
- 主题选择器的一行只是私有 picker 行，不是独立的主题 SDK 记录，也不是角色拥有的持久化主题。(plugins/packages/buildin/character_cards/src/selection-application.ts:15)

## 关键符号

- `parseChatSelection` — 解析 `card` / `group` / `model` 选择串。(plugins/packages/buildin/character_cards/src/chat-bindings.ts:10)
- `requireChatSelection` — 要求选择串恰好命中一条已存记录。(plugins/packages/buildin/character_cards/src/chat-bindings.ts:22)
- `selectionForActive` — 当前生效提示词映射为选择串。(plugins/packages/buildin/character_cards/src/chat-bindings.ts:32)
- `ChatBinding` — 聊天与选择的绑定记录，字段为 `chatId` 与 `selection`。(plugins/packages/buildin/character_cards/src/model.ts:447)
- `ChatMarker` — version 1 的聊天扩展标记，含选择串。(plugins/packages/buildin/character_cards/src/chat-markers.ts:8)
- `ExecutionData` — 执行数据，含选择、功能类型、主记忆 owner 与参与者档案。(plugins/packages/buildin/character_cards/src/chat-markers.ts:13)
- `CHARACTER_CARDS_NAMESPACE` — 插件命名空间常量 `com.operit.character_cards`。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:24)
- `parseChatInitialization` — 校验聊前创建载荷的字段与事件名。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:63)
- `initializeChatExtension` — 按三路确定新聊天的选择。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:87)
- `beforeChatCreate` — 聊前创建钩子。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:118)
- `registerChatInitialization` — 注册 `chat-initialization` 钩子。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:132)
- `CharacterChatStore` — 偏好文件里的绑定读写与草稿管理。(plugins/packages/buildin/character_cards/src/storage/chats.ts:10)
- `combineCharacterPrompt` — 按固定顺序组装角色提示词。(plugins/packages/buildin/character_cards/src/character-prompt.ts:6)
- `combinePrompts` — 按卡片 id 取卡片再组装提示词。(plugins/packages/buildin/character_cards/src/operations.ts:530)
- `withGroupParticipantPrompt` — 群组成员档案追加角色规划提示。(plugins/packages/buildin/character_cards/src/domain.ts:427)
- `SelectionReferences` — 选择、主题引用与 TTS 引用的组合。(plugins/packages/buildin/character_cards/src/selection-application.ts:11)
- `applyConfigurations` — 按引用逐个应用主题与 TTS。(plugins/packages/buildin/character_cards/src/selection-application.ts:116)
- `activateChatSelection` — 按绑定恢复生效选择。(plugins/packages/buildin/character_cards/src/service-runtime.ts:103)
- `onChatViewTheme` — 打开会话时触发主题恢复。(plugins/packages/buildin/character_cards/src/chat-view-theme.ts:5)
- `chat.configuration.delete` — Core 删会话后释放插件绑定的公开 API。(plugins/packages/buildin/character_cards/src/public-api.ts:74)
- `chat.configuration.draft.commit` — 发布 Core 认证提交选中的已预写绑定。(plugins/packages/buildin/character_cards/src/public-api.ts:473)
- `chat.configuration.draft.abort` — Core 复用已有会话后移除作废草稿。(plugins/packages/buildin/character_cards/src/public-api.ts:474)

## 调用链

1. 插件注册入口调 `registerChatInitialization`，挂载聊前创建钩子。(plugins/packages/buildin/character_cards/src/main.ts:58)
2. 新建或分支聊天时 Core 触发 `before_create` 事件，`beforeChatCreate` 接到载荷。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:118)
3. `parseChatInitialization` 校验载荷恰好 7 个顶层字段与事件名、创建类型。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:63)
4. 分支建聊时先查源聊天绑定，无绑定回退为 `model:chat`。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:122)
5. `initializeChatExtension` 按三路定选择：显式 input、源扩展标记、当前生效选择。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:87)
6. `requireSelection` 校验选择指向真实卡片或非空群组。(plugins/packages/buildin/character_cards/src/chat-lifecycle.ts:106)
7. `prepareChatBinding` 以 `draft_` 键预写草稿绑定。(plugins/packages/buildin/character_cards/src/storage/chats.ts:81)
8. 原生创建提交后 Core 经 `chat.configuration.draft.commit` 发布已预写的绑定。(plugins/packages/buildin/character_cards/src/public-api.ts:473)
9. 执行时 `resolveChatExecution` 从聊天扩展解码标记并解析选择串。(plugins/packages/buildin/character_cards/src/domain.ts:395)
10. 单卡解析出提示词作为参与者档案的提示词；群组成员再经 `withGroupParticipantPrompt` 追加角色规划提示。(plugins/packages/buildin/character_cards/src/domain.ts:427)
11. 打开会话时 `onChatViewTheme` 调 `activateChatSelection`，按绑定恢复生效选择并应用其主题引用。(plugins/packages/buildin/character_cards/src/chat-view-theme.ts:5)
12. 删会话后 Core 调 `chat.configuration.delete`，插件释放该聊天的绑定。(plugins/packages/buildin/character_cards/src/public-api.ts:74)

## 来源

- plugins/packages/buildin/character_cards/README.md
- plugins/packages/buildin/character_cards/src/chat-lifecycle.ts
- plugins/packages/buildin/character_cards/src/chat-storage.ts
- plugins/packages/buildin/character_cards/src/chat-bindings.ts
- plugins/packages/buildin/character_cards/src/character-prompt.ts
- plugins/packages/buildin/character_cards/src/model.ts
- plugins/packages/buildin/character_cards/src/chat-markers.ts
- plugins/packages/buildin/character_cards/src/storage/chats.ts
- plugins/packages/buildin/character_cards/src/domain.ts
- plugins/packages/buildin/character_cards/src/operations.ts
- plugins/packages/buildin/character_cards/src/group-execution/prompts.ts
- plugins/packages/buildin/character_cards/src/selection-application.ts
- plugins/packages/buildin/character_cards/src/service-runtime.ts
- plugins/packages/buildin/character_cards/src/chat-view-theme.ts
- plugins/packages/buildin/character_cards/src/public-api.ts
- plugins/packages/buildin/character_cards/src/main.ts

本页是 [[core-plugin-sdk|插件——Plugin SDK]] 所述 ToolPkg 机制在角色卡插件上的具体实现。
