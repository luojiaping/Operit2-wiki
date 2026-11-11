---
title: 命令层——CLI 命令编排
module: core
platforms: [all]
sources: 6
date: 2026-11-11
---

## 概述

- 命令层是 `core` crate，把面向用户的命令行编排在应用表面之上（`core/crates/command/README.md:3`）。
- 命令层有两个入口：`run_core_command_with_context` 从 `HostManager` 上下文创建应用并运行命令（`core/crates/command/core/src/lib.rs:9`）。
- 另一个入口 `run_core_command` 接收已初始化的 `OperitApplication` 引用（`core/crates/command/core/src/lib.rs:22`）。
- 命令参数里的 `--json` 是 JSON 模式开关，分发前从参数中滤除（`core/crates/command/core/src/lib.rs:26`）。
- 本页 seed 覆盖 `chat`、`model`、`tool`、`sync` 四个命令文件的全文。
- README 列出 14 组命令：`chat`、`model`、`memory`、`tool`、`plugin`、`package`、`skill`、`MCP`、`storage`、`workspace`、`host`、`prefs`、`update`、`log`（`core/crates/command/README.md:9`）。
- README 列出的 14 组命令不含 sync，但 seed 内有 sync.rs 实现 `reset-transactions`（`core/crates/command/core/src/commands/sync.rs:11`）。
- 其余 10 组（`memory`、`plugin`、`package`、`skill`、`MCP`、`storage`、`workspace`、`host`、`prefs`、`update`、`log`）的实现不在本页 seed 内，本页不展开（`core/crates/command/README.md:9`）。
- 本页命令名以 seed 代码里的用法文本为准，不照抄 README 旧命令（`core/crates/command/core/src/commands/chat.rs:699`）。

## AI 速览

- `run_core_command_with_context` — 从 `HostManager` 上下文创建应用并运行命令（`core/crates/command/core/src/lib.rs:9`）
- `run_core_command` — 对已初始化应用执行命令，处理 `--json` 开关（`core/crates/command/core/src/lib.rs:22`）
- `CoreCommandOutput` — 命令输出载体，文本行与 JSON 两种形态（`core/crates/command/core/src/lib.rs:32`）
- `run_chat_command` — 聊天子命令分发（`core/crates/command/core/src/commands/chat.rs:26`）
- `run_model_command` — 模型与 Provider 子命令分发（`core/crates/command/core/src/commands/model.rs:34`）
- `run_tool_command` — 工具查看与执行分发（`core/crates/command/core/src/commands/tool.rs:8`）
- `run_sync_command` — 同步恢复命令分发（`core/crates/command/core/src/commands/sync.rs:5`）
- `ModelConfigManager` — 模型配置管理器，`model` 命令直接用其默认实例（`core/crates/command/core/src/commands/model.rs:25`）
- `FunctionalConfigManager` — 功能模型绑定管理器（`core/crates/command/core/src/commands/model.rs:30`）
- `OperitApplication` — 应用门面，是 chat、sync、tool 三组命令的操作对象（`core/crates/command/core/src/lib.rs:14`）
- 主入口函数之一是 `run_core_command_with_context`：新建应用走它（`core/crates/command/core/src/lib.rs:9`）。
- 另一个主入口是 `run_core_command`：复用已初始化应用（`core/crates/command/core/src/lib.rs:22`）。
- 数据流向：CLI 参数 → `run_core_command` 剥离 `--json`（`core/crates/command/core/src/lib.rs:26`）。
- 剥离后委托 `commands::run_core_command` 分发（`core/crates/command/core/src/lib.rs:34`）。
- 各组入口函数经门面方法或默认管理器读写状态，输出文本行与 JSON（`core/crates/command/core/src/commands/chat.rs:65`）。

## 核心机制

**入口与 JSON 模式**

- `run_core_command_with_context` 用 `OperitApplication::newWithContext` 创建应用（`core/crates/command/core/src/lib.rs:14`）。
- 创建应用后调 `onCreate` 初始化（`core/crates/command/core/src/lib.rs:13`）。
- `run_core_command` 新建 `CoreCommandOutput` 并按 `jsonMode` 调 `setJsonMode` 设 JSON 模式（`core/crates/command/core/src/lib.rs:33`）。
- 分发结束后调 `output.finalizeJson` 收尾（`core/crates/command/core/src/lib.rs:35`）。

**命令组覆盖**

- `chat` 组有 15 个子命令，分两段列出：`new`、`list`、`show`、`current`、`switch`、`delete`（`core/crates/command/core/src/commands/chat.rs:39`）。
- 其余 9 个是 `delete-message`、`clear`、`rollback`、`branch`、`branches`、`lock`、`pin`、`send`、`stats`（`core/crates/command/core/src/commands/chat.rs:47`）。
- `model` 组的 match 分支从 `provider-type-list` 起（`core/crates/command/core/src/commands/model.rs:48`）。
- `model` 组的 match 分支到 `function-reset` 止（`core/crates/command/core/src/commands/model.rs:642`）。
- catalog-status 与 `catalog-refresh` 共用一个分支，分别查与刷新 `models.dev` 目录（`core/crates/command/core/src/commands/model.rs:287`）。
- `tool` 组有 `list` 与 `show` 子命令（`core/crates/command/core/src/commands/tool.rs:22`）。
- `tool` 组有 `exec` 子命令（`core/crates/command/core/src/commands/tool.rs:31`）。
- `sync` 组只有 `reset-transactions` 一个子命令，且要求不带额外参数（`core/crates/command/core/src/commands/sync.rs:11`）。
- `sync` 其他输入一律打印用法（`core/crates/command/core/src/commands/sync.rs:13`）。

**与 core-application 门面的关系**

- README 声明命令层应消费门面句柄、本地客户端与显式访问句柄，不直接创建 `runtime`、`node`、`proxy`、`provider`、`tool` 或 `access` 内部构件（`core/crates/command/README.md:5`）。
- `chat` 命令取 `application.chatRuntimeHolder` 的锁，再取 `MAIN` 槽操作（`core/crates/command/core/src/commands/chat.rs:63`）。
- `tool` 命令直接用 `application.toolHandler` 查工具与执行调用（`core/crates/command/core/src/commands/tool.rs:26`）。
- `sync` 命令调 `application.syncResetTransactions()` 重建同步历史（`core/crates/command/core/src/commands/sync.rs:25`）。
- 有附件时经 `AttachmentTransferManager::getInstance` 取传输管理器，传入 `application.hostManager`（`core/crates/command/core/src/commands/chat.rs:601`）。
- `model` 命令不接收应用：首个参数是以下划线开头的 `_context: HostManager`，命令体不使用它（`core/crates/command/core/src/commands/model.rs:35`）。
- `model` 命令改用 `ModelConfigManager::default()` 读写 Provider 与模型配置（`core/crates/command/core/src/commands/model.rs:25`）。
- `model` 命令改用 `FunctionalConfigManager::default()` 读写功能模型绑定（`core/crates/command/core/src/commands/model.rs:30`）。
- 门面关系分两类：chat、sync、tool 走 `OperitApplication` 门面，model 绕开门面直接用两个默认管理器（`core/crates/command/core/src/lib.rs:22`）。

**输出形态**

- 每条命令写文本行用 `push_stdout_line`（`core/crates/command/core/src/commands/chat.rs:65`）。
- 结构化结果用 `setJsonStdout` 输出（`core/crates/command/core/src/commands/chat.rs:78`）。
- JSON 输出是整个会话列表的序列化值（`core/crates/command/core/src/commands/chat.rs:78`）。

**密钥处理**

- provider-set-key 只输出 API key 长度，不输出 key 本身（`core/crates/command/core/src/commands/model.rs:149`）。
- `print_provider_profile` 只输出 API key 长度，不输出 key 本身（`core/crates/command/core/src/commands/model.rs:734`）。
- Provider JSON 只含 `apiKeyLength` 与密钥池元数据，不含 key 值（`core/crates/command/core/src/commands/model.rs:901`）。

**条件与边界**

- `chat send` 未指定会话且无当前会话时报错（`core/crates/command/core/src/commands/chat.rs:594`）。
- `chat send` 先调 `requireChatExists` 确认会话存在（`core/crates/command/core/src/commands/chat.rs:595`）。
- `chat send` 无 --chat 时用当前会话 id（`core/crates/command/core/src/commands/chat.rs:594`）。
- 回滚未应用时输出提示：消息须存在且为用户消息、工作区快照须仍可用，只保留最新一次编辑轮次（`core/crates/command/core/src/commands/chat.rs:216`）。
- `stats` 只输出中性汇总统计：总会话数与总消息数（`core/crates/command/core/src/commands/chat.rs:364`）。
- `tool exec` 用 `ToolExecutionPolicy::Direct` 策略执行，只取最后一个结果（`core/crates/command/core/src/commands/tool.rs:117`）。
- `tool list` 的 `scope` 只接受 `public`、`internal`、`all`，其他值返回用法错误（`core/crates/command/core/src/commands/tool.rs:60`）。
- `model use` 只把 `CHAT` 功能的模型绑定设为指定 provider 与 model（`core/crates/command/core/src/commands/model.rs:347`）。
- provider-model-available-list 默认只保留 `isFetched` 的模型，传 `all` 才含历史（`core/crates/command/core/src/commands/model.rs:201`）。
- provider-model-add 要求模型已在可用列表里，否则报错并提示用 `provider-model-create` 按 id 添加（`core/crates/command/core/src/commands/model.rs:242`）。
- `summary-set` 要求恰好 5 个参数（`core/crates/command/core/src/commands/model.rs:511`）。
- `chat new` 的 `--set-current` 默认值为 `true`（`core/crates/command/core/src/commands/chat.rs:419`）。
- `chat` 未知子命令返回错误，不打印用法（`core/crates/command/core/src/commands/chat.rs:52`）。
- `model` 未知子命令落到 `print_model_usage`（`core/crates/command/core/src/commands/model.rs:663`）。
- `tool` 未知子命令打印用法（`core/crates/command/core/src/commands/tool.rs:31`）。

**用法文本与实现的两处不一致**

- `print_model_usage` 的用法列表包含 `codex-login`（`core/crates/command/core/src/commands/model.rs:974`）。
- 未知 `model` 子命令落到 `print_model_usage`；用法里列出的 codex-login 没有对应的执行分支（`core/crates/command/core/src/commands/model.rs:663`）。
- `print_chat_usage` 写 `operit2 chat show <chat-id> [--runtime]`（`core/crates/command/core/src/commands/chat.rs:701`）。
- `show_chat` 只读 `args`[0] 作 `chatId`，不读后续参数，`--runtime` 不起作用（`core/crates/command/core/src/commands/chat.rs:86`）。
- `print_chat_usage` 的 `chat new` 用法行没有列出 --workspace（`core/crates/command/core/src/commands/chat.rs:699`）。
- 解析器接受 `--workspace` 选项（`core/crates/command/core/src/commands/chat.rs:447`）。

## 关键符号

- `run_core_command_with_context` — 从 `HostManager` 上下文创建应用并运行命令（`core/crates/command/core/src/lib.rs:9`）
- `run_core_command` — 对已初始化应用执行命令，处理 `--json` 开关（`core/crates/command/core/src/lib.rs:22`）
- `CoreCommandOutput` — 命令输出载体，文本行与 JSON 两种形态（`core/crates/command/core/src/lib.rs:32`）
- `run_chat_command` — 聊天子命令分发（`core/crates/command/core/src/commands/chat.rs:26`）
- `run_model_command` — 模型与 Provider 子命令分发（`core/crates/command/core/src/commands/model.rs:34`）
- `run_tool_command` — 工具查看与执行分发（`core/crates/command/core/src/commands/tool.rs:8`）
- `run_sync_command` — 同步恢复命令分发（`core/crates/command/core/src/commands/sync.rs:5`）
- `ModelConfigManager` — 模型配置管理器，`model` 命令直接用其默认实例（`core/crates/command/core/src/commands/model.rs:25`）
- `FunctionalConfigManager` — 功能模型绑定管理器（`core/crates/command/core/src/commands/model.rs:30`）
- `ChatServiceCore` — 聊天运行时核心，chat 命令经 MAIN 槽取它操作（`core/crates/command/core/src/commands/chat.rs:8`）
- `ChatRuntimeSlot` — 聊天运行时槽位，chat 命令用 MAIN 槽（`core/crates/command/core/src/commands/chat.rs:7`）
- `EnhancedAIService` — 增强 AI 服务，建会话、建分支与发消息前注入 `ChatServiceCore`（`core/crates/command/core/src/commands/chat.rs:6`）
- `ChatHistoryManager` — 聊天历史管理器，stats 用它读汇总计数（`core/crates/command/core/src/commands/chat.rs:9`）
- `AIToolHandler` — 工具处理器，`tool` 命令的查询与执行对象（`core/crates/command/core/src/commands/tool.rs:4`）
- `ToolExecutionPolicy` — 工具执行策略，tool exec 用 Direct（`core/crates/command/core/src/commands/tool.rs:6`）
- `FunctionType` — 功能模型角色枚举，共 11 种（`core/crates/command/core/src/commands/model.rs:6`）
- `ThinkingLevel` — 思考档位枚举，thinking 子命令读写它（`core/crates/command/core/src/commands/model.rs:12`）
- `ProviderProfile` — Provider 档案，含 endpoint、密钥池与模型列表（`core/crates/command/core/src/commands/model.rs:9`）
- `ResolvedModelConfig` — 解析后模型配置，show 与 context-show 的输出对象（`core/crates/command/core/src/commands/model.rs:10`）

## 调用链

1. CLI 入口调 `run_core_command_with_context`，传 `HostManager` 上下文（`core/crates/command/core/src/lib.rs:9`）。
2. 该函数用 `OperitApplication::newWithContext` 建应用并调 `onCreate` 初始化（`core/crates/command/core/src/lib.rs:14`）。
3. `run_core_command` 识别并剥离 `--json`，建 CoreCommandOutput（`core/crates/command/core/src/lib.rs:26`）。
4. 委托 `commands::run_core_command` 分发（`core/crates/command/core/src/lib.rs:34`）。
5. `chat` 的 15 个子命令由 `match` 分支分发（`core/crates/command/core/src/commands/chat.rs:39`）。
6. `chat send`：解析参数 → 取会话（--chat 或当前会话）（`core/crates/command/core/src/commands/chat.rs:594`）。
7. 附件经 `AttachmentTransferManager` 导入（`core/crates/command/core/src/commands/chat.rs:601`）。
8. `sendChatMessage` 发送并等回执（`core/crates/command/core/src/commands/chat.rs:623`）。
9. `model` 组不经应用门面（`core/crates/command/core/src/commands/model.rs:35`）。
10. `ModelConfigManager::default()` 与 `FunctionalConfigManager::default()` 直接读写配置（`core/crates/command/core/src/commands/model.rs:25`）。
11. `tool exec`：解析 params-json 为 `ToolCall`，以 `Direct` 策略执行，取最后一个结果（`core/crates/command/core/src/commands/tool.rs:117`）。
12. sync reset-transactions：调 `syncResetTransactions` 重建同步历史（`core/crates/command/core/src/commands/sync.rs:25`）。
13. 收尾：`output.finalizeJson`（`core/crates/command/core/src/lib.rs:35`）。

## 来源

- core/crates/command/README.md（9 行）
- core/crates/command/core/src/lib.rs（37 行）
- core/crates/command/core/src/commands/chat.rs（719 行）
- core/crates/command/core/src/commands/sync.rs（44 行）
- core/crates/command/core/src/commands/tool.rs（156 行）
- core/crates/command/core/src/commands/model.rs（1006 行）

命令层与应用门面的关系见 [[core-application|应用组装——CoreApplication 门面]]。
