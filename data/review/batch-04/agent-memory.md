---
title: 记忆
module: agent
platforms: [all]
sources: 12
date: 2026-11-11
---

## 概述

记忆是 character_cards 插件的长期记忆图谱：从聊天记录里抽取实体、更新与关系，存进按 owner 划分的同步数据库（`plugins/packages/buildin/character_cards/src/storage/memory.ts:11`）。
记忆子系统现位于 plugins/packages/buildin/character_cards/src/memory-jobs，旧名 extended_memory_tools 在本页 7 个 seed 内零命中（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:1`）。
一个记忆 owner 是角色卡（`character:` 加角色卡 id）或共享库（`shared:` 加共享库 id）（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:45`）。
记忆写入分两步：先把候选排队，再由间隔任务批量提取（`plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts:24`）。
记忆提取直接消费原始消息，不经过聊天摘要（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:242`）。
记忆任务代码是 TypeScript，在 JS 执行宿主上运行；同步数据库文件位于各 Host 的 Space 数据目录下（`plugins/packages/buildin/character_cards/src/storage/memory.ts:20`）。

## AI 速览

- `MemoryJobRunner` — 间隔任务的执行器，每轮推进各 owner 的重建与候选批次
- `enqueueCandidate` — 把一条消息登记为记忆提取候选
- `extractMessages` — 对一批消息调 MEMORY 模型做提取并落库
- `startMemoryRebuild` — 为选定聊天规划重建窗口并登记重建任务
- `MemorySpace` — 一个 owner 的完整记忆空间
- `MemoryJobState` — 调度状态：记忆空间去掉记忆、关系、分块与向量后的部分
- `CharacterMemoryDatabase` — 同步化的记忆数据库
- `memoryJobProducer` — 读当前 CoreNode id，作为任务的生产设备标识
- `registerMemoryJobHooks` — 注册消息钩子与 60 秒间隔钩子
- `embeddingSpace` — 云端嵌入的空间标识（端点、模型、`unit-v1`）
- `extractionTemplate` — 记忆提取的提示词策略
- 主入口：`onMemoryMessagePersisted`（助手回复落库后入队）与 `onMemoryInterval`（每 60 秒推进任务）
- 数据流向：助手回复落库 → 候选入队 → 间隔任务按 owner 批量提取 → MEMORY 模型返回图谱操作 → 写入同步数据库

## 核心机制

### 记忆位于哪里

- 一个 owner 的完整记忆空间是 `MemorySpace`，含记忆、关系、分块、候选、设置、重建进度与向量（`plugins/packages/buildin/character_cards/src/model.ts:405`）。
- 调度只读写 `MemoryJobState`，即记忆空间去掉记忆、关系、分块与向量后的部分（`plugins/packages/buildin/character_cards/src/model.ts:417`）。
- 全部 owner 的记忆空间收在 CharacterState 的 `owners` 数组里（`plugins/packages/buildin/character_cards/src/model.ts:429`）。
- `CharacterState` 的注释写明它只拥有本插件的文件模式，不施加全运行时范围的存储模式（`plugins/packages/buildin/character_cards/src/model.ts:419`）。
- 记忆数据库文件是 Space 数据目录下的 `memory.sqlite`（`plugins/packages/buildin/character_cards/src/storage/memory.ts:20`）。
- 记忆操作作用于同步化的数据库记录，检索索引是 owner 本地的派生索引（`plugins/packages/buildin/character_cards/src/storage/memory-repository.ts:41`）。
- 源记录与向量在一次同步化事务里一起发布（`plugins/packages/buildin/character_cards/src/storage/memory.ts:76`）。

### 记忆如何进入 Space 同步

- 记忆数据库在 Space 数据目录下打开，文件名为 `memory.sqlite`（`plugins/packages/buildin/character_cards/src/storage/memory.ts:20`）。
- 候选与重建任务随任务状态进入同一同步数据库，读出用 `readMemoryJobState`（`plugins/packages/buildin/character_cards/src/storage/memory-repository.ts:310`）。
- 任务状态写回用 `writeMemoryJobState`（`plugins/packages/buildin/character_cards/src/storage/memory-repository.ts:320`）。
- 任务认领只认本设备：一个 owner 只有在本设备的重建仍在活动、或本设备有待处理候选时才会被推进（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:331`）。
- 任务的生产设备标识是当前 CoreNode id，由 `memoryJobProducer` 经 `list_core_nodes` 读出（`plugins/packages/buildin/character_cards/src/memory-jobs/producer.ts:5`）。
- 没有生产设备标识的历史候选会被标为失败，提示在应处理它的设备上重试（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:319`）。
- 没有生产设备标识且仍在活动的历史重建任务会被标为失败（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:326`）。

### 候选入队

- 助手回复落库后，消息钩子 `onMemoryMessagePersisted` 只处理 `ai` 或 `assistant` 发送者（`plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts:8`）。
- 内容（`content`）空白的消息会被忽略（`plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts:11`）。
- 钩子派发 `memory.candidate.enqueue`，来源类型为 `reply_finalized_auto`（`plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts:14`）。
- 自动候选在全局记忆偏好 `autoUpdateEnabled` 关闭时直接返回空结果，不入队（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:54`）。
- 候选必须恰好定位到一条源消息，否则抛错（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:61`）。
- 自动候选在当前消息作者缺失时直接返回空结果，不入队（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:72`）。
- 自动候选在 `ownerKey` 为空时取当前消息的 `primaryOwnerKey`（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:73`）。
- 选定用户消息的候选在显式给出 `ownerKey` 时用 `requireChatOwner` 校验（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:81`）。
- 群聊的选定用户消息候选在参与者不是恰好一人时要求显式给出 owner（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:84`）。
- 同一 owner 下已有相同四元组（聊天、时间戳、版本序号、来源类型）的候选时，返回已有候选 id，不再重复入队（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:94`）。
- 新候选状态为 `pending`、`attemptCount` 为 0，并携带产生它的 `producerNodeId`（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:102`）。

### 间隔推进

- 间隔钩子每 60 秒调用 `runMemoryJobs()`（`plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts:18`）。
- 导出的 `runMemoryJobs()` 把调用转给服务实例（`plugins/packages/buildin/character_cards/src/service-runtime.ts:267`）。
- 服务运行时的 `runMemoryJobs` 调用 `jobs.tick()`（`plugins/packages/buildin/character_cards/src/service-runtime.ts:115`）。
- `tick()` 在已有一次正在跑的 pass 时共享它（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:286`）。
- 每轮先列出全部记忆 owner 再逐个推进（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:296`）。
- 处理中超过 30 分钟租约的本设备候选会被打回 `pending`（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:320`）。
- 候选批次只有在待处理候选达到 5 条时才开始组织（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:355`）。
- 待处理候选按聊天分组，按触发时间戳最旧优先排序，每聊天至多取 20 条（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:361`）。
- 认领批次时候选状态改为 `processing`，`attemptCount` 加 1（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:386`）。
- 本轮在任一 owner 失败时抛出 `MemoryJobPassError`（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:306`）。

### 提取与落库

- 提取前逐条校验候选源消息：已删除、版本变化或发送者变化的候选会被跳过并记为 failed（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:212`）。
- 选定用户消息的批次只提取通过校验的选定用户消息（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:230`）。
- 自动回复来源的批次只取截至最后一条候选时间戳的消息，且至多取最后 48 条（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:237`）。
- 提取要求消息里有真实用户上下文，否则抛错（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:242`）。
- 提取用 `MEMORY_SEARCH_THRESHOLD` 作为相关度阈值检索已有记忆（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:252`）。
- 提取提示最多只带前 15 条检索到的候选记忆（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:253`）。
- 提取调用 `Tools.Chat.call`，`functionType` 为 `MEMORY`，不启用思考（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:254`）。
- 模型输出先经 `parseModelJson` 去掉思考块与代码围栏，失败时回退到首尾花括号切片（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:16`）。
- 空对象 `{}` 表示没有可复用的事实，分析结果为 null（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:66`）。
- `new` 超过 5 条时提取抛错（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:72`）。
- 合并用 `mergeMemories` 生成新记忆，`credibility` 与 `importance` 均为 0.5（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:199`）。
- 主记录新建时 `source` 为 `memory_analysis`、`credibility` 为 1、`importance` 为 0.8（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:215`）。
- 新建记忆时 `credibility` 与 `importance` 均为 0.5（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:222`）。
- 连边用 `createLink` 按解析出的两端记忆 id 建边（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:229`）。
- 资料更新通过 `writeUser` 写回（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:233`）。
- 模型引用了无法解析的标题时只跳过该条，不丢弃整轮提取（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:198`）。
- 提取提交后，已完成的候选从任务状态里删除（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:248`）。
- 失败的候选保留在任务状态里，状态为 `failed` 并记录 `lastError`（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:193`）。

### 提取策略（提示词）

- 只记录用户特异且可复用的信息，不记录常识与公开定义（`plugins/packages/buildin/character_cards/src/memory-jobs/prompt-template.ts:2`）。
- 不记录未来推测项，没有长期价值信号时返回 `{}`（`plugins/packages/buildin/character_cards/src/memory-jobs/prompt-template.ts:2`）。
- 优先 `update` 与 `merge`，`new` 仅在确实新增概念时使用且最多 5 条（`plugins/packages/buildin/character_cards/src/memory-jobs/prompt-template.ts:2`）。
- `main` 标题优先写事件；引用的标题必须从已有记忆标题中逐字复制（`plugins/packages/buildin/character_cards/src/memory-jobs/prompt-template.ts:2`）。
- 输出严格 JSON，可信度、重要性与权重为 0.0 到 1.0 的数字（`plugins/packages/buildin/character_cards/src/memory-jobs/prompt-template.ts:2`）。
- 只在对话里有明确证据时建边（`plugins/packages/buildin/character_cards/src/memory-jobs/prompt-template.ts:2`）。

### 重建

- 重建为选定聊天规划窗口：窗口大小限制在 8 到 48 条消息之间（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:194`）。
- 窗口按 `fromInclusive` / `toInclusive` 时间范围与空白内容过滤消息（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:202`）。
- 助手回复前面没有用户消息时跳过该回复（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:208`）。
- 窗口满时把最近一条用户消息作为下一窗口的携带上下文（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:209`）。
- 已有重建处于 `preparing` 或 `running` 时新建重建抛错（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:116`）。
- 重建窗口执行前逐条复核计划源消息的版本，版本变化或删除时抛错（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:161`）。
- 重建窗口失败时 `failedWindows` 加 1 并记录 `lastError`，窗口照常推进（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:180`）。
- 没有下一个窗口时进度状态置为 `completed`（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:141`）。

### 向量嵌入

- 云端嵌入要求开启且端点为绝对 HTTP 地址，空间标识为端点、模型与 `unit-v1` 的组合（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:22`）。
- 每批从 `next` 起取 64 条文本（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:47`）。
- 最多用 4 个并发 worker（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:67`）。
- 请求向端点加 `/embeddings` 后缀发 POST（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:51`）。
- 返回的向量会归一化为单位长度（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:35`）。
- 嵌入批次内向量维度不一致时抛错（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:69`）。
- 向量重建交给仓库的 `rebuildMemoryEmbeddings`（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:75`）。

### 记忆与聊天摘要的关系

- 记忆提取的输入是调用方传入的原始消息数组，输入中不含聊天摘要（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:242`）。
- 摘要的正文不进入提取流程；`inputTokens`/`outputTokens` 只在 `assertChat` 校验里出现，`messageCount` 另用于 readMessages 界定读取范围（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:11`）。
- 手动更新取最后一条非空助手回复为锚点，只分析锚点及之前的消息，至多取最后 10 条（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:272`）。

### 自动分类

- 自动分类只处理放在根文件夹的记忆（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:278`）。
- 分类调用要求模型恰好为每条记忆返回一个文件夹，否则抛错（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:287`）。
- 分类结果按标题把记忆移入指定文件夹（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:292`）。

### 归属与权限

- 角色卡的记忆绑定分 `CHARACTER` 与 `SHARED` 两种模式（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:45`）。
- 参与者从持久化的聊天选择中解析，模型选择对应零个参与者（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:31`）。
- 群聊参与者按 `orderIndex` 排序后逐个取角色卡（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:37`）。
- 写校验接受参与者主 owner 匹配，或参与者挂载的可写共享库（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:57`）。
- 消息作者缺失时回退到聊天级的写校验（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:88`）。

### 清理

- `listMemoryChats` 每批读 200 个聊天，并把 Core 侧已消失的聊天 id 列入 `missingChatIds`（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:119`）。
- `pruneMissingMemoryChats` 删除已消失聊天的绑定与孤儿候选（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:138`）。

## 关键符号

- `MemoryJobRunner` — 间隔任务的执行器（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:279`）
- `enqueueCandidate` — 候选入队（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:53`）
- `startMemoryRebuild` — 规划重建并登记任务（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:110`）
- `processCandidates` — 批量校验并提取候选（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:198`）
- `processRebuildWindow` — 执行一个重建窗口（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:145`）
- `MemoryJobPassError` — 按 owner 汇总失败（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:28`）
- `MemoryJobStatusError` — 同时保留执行错误与状态发布错误（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:19`）
- `extractMessages` — 调 MEMORY 模型提取并落库（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:239`）
- `updateChatMemory` — 手动更新：取最后一条助手回复为锚点（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:262`）
- `autoCategorizeMemory` — 根文件夹记忆自动分类（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:276`）
- `buildCandidateSearchQuery` — 检索查询：最后提问、最后回答、最近上下文（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:93`）
- `parseModelJson` — 模型 JSON 解析（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:15`）
- `requireChat` — 精确匹配聊天 id（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:17`）
- `chatParticipants` — 从聊天选择解析参与者（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:27`）
- `primaryOwner` — 角色卡或共享库的记忆 owner（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:44`）
- `currentMessageMemoryAccess` — 解析消息作者的记忆读写权限（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:68`）
- `readMessages` — 按升序读完整消息范围（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:170`）
- `planWindows` — 切重建窗口（`plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts:193`）
- `embedTexts` — 云端嵌入批量请求（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:38`）
- `embeddingSpace` — 嵌入空间标识（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:20`）
- `rebuildMemoryEmbeddings` — 向量重建（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:75`）
- `onMemoryMessagePersisted` — 助手回复落库后入队（`plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts:5`）
- `onMemoryInterval` — 间隔推进（`plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts:18`）
- `registerMemoryJobHooks` — 注册两个钩子（`plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts:23`）
- `memoryJobProducer` — 读当前 CoreNode id（`plugins/packages/buildin/character_cards/src/memory-jobs/producer.ts:4`）
- `extractionTemplate` — 提取提示词策略（`plugins/packages/buildin/character_cards/src/memory-jobs/prompt-template.ts:2`）
- `MemorySpace` — 一个 owner 的完整记忆空间（`plugins/packages/buildin/character_cards/src/model.ts:403`）
- `MemoryJobState` — 调度状态（`plugins/packages/buildin/character_cards/src/model.ts:417`）
- `CharacterMemoryDatabase` — 同步化的记忆数据库（`plugins/packages/buildin/character_cards/src/storage/memory.ts:12`）
- `DatabaseMemoryRepository` — 同步数据库记录上的记忆操作（`plugins/packages/buildin/character_cards/src/storage/memory-repository.ts:41`）

## 调用链

1. 包注册时调用 `registerMemoryJobHooks()`，注册消息钩子与 60 秒间隔钩子（`plugins/packages/buildin/character_cards/src/main.ts:55`）。
2. 助手回复落库后，消息钩子派发 `memory.candidate.enqueue`（`plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts:14`）。
3. 校验发送者、作者权限与 owner，写入一条 `pending` 候选（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:102`）。
4. 每 60 秒，`onMemoryInterval` 调用 `runMemoryJobs()`（`plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts:18`）。
5. `runMemoryJobs` 转给服务实例，调用 `jobs.tick()`（`plugins/packages/buildin/character_cards/src/service-runtime.ts:115`）。
6. 推进各 owner：先回收超租约与无生产设备的历史任务（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:319`）。
7. 本设备的重建任务按窗口推进，每窗口先复核源消息版本再提取（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:161`）。
8. 待处理候选达到 5 条时才开始组织批次（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:355`）。
9. 批次按聊天分组，按触发时间戳最旧优先排序，每聊天至多取 20 条（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:361`）。
10. 认领批次后，`processCandidates` 逐条校验源消息，提取有效的候选（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:198`）。
11. 检索已有记忆、组装提示词、调 `MEMORY` 模型（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:254`）。
12. 模型结果经解析、校验后落库，合并先于更新处理（`plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts:198`）。
13. 提取提交后，已完成的候选从任务状态里删除（`plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts:248`）。
14. 云端嵌入开启时，记忆向量由 `embedTexts` 向云端端点批量请求（`plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts:38`）。

## 来源

- `plugins/packages/buildin/character_cards/src/memory-jobs/scheduler.ts`
- `plugins/packages/buildin/character_cards/src/memory-jobs/analysis.ts`
- `plugins/packages/buildin/character_cards/src/memory-jobs/chat.ts`
- `plugins/packages/buildin/character_cards/src/memory-jobs/embeddings.ts`
- `plugins/packages/buildin/character_cards/src/memory-jobs/hooks.ts`
- `plugins/packages/buildin/character_cards/src/memory-jobs/producer.ts`
- `plugins/packages/buildin/character_cards/src/memory-jobs/prompt-template.ts`
- `plugins/packages/buildin/character_cards/src/model.ts`
- `plugins/packages/buildin/character_cards/src/storage/memory.ts`
- `plugins/packages/buildin/character_cards/src/storage/memory-repository.ts`
- `plugins/packages/buildin/character_cards/src/service-runtime.ts`
- `plugins/packages/buildin/character_cards/src/main.ts`
