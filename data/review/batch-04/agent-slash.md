---
title: Slash 命令
module: agent
platforms: [windows, macos, linux]
sources: 3
date: 2026-11-11
---

## 概述

TUI 一侧的命令清单由 `COMMAND_SPECS` 静态表定义（apps/cli/src/tui/input/commands.rs:56）。
交互式 shell 一侧由 `handle_shell_command_with_core` 按首词 match 分发（apps/cli/src/chat_runtime.rs:517）。
旧调查称 18 个内置命令，与当前 HEAD 实测的 81 条不符（apps/cli/src/tui/input/commands.rs:56）。
commands.rs 只定义补全表与补全逻辑，不含执行分发（apps/cli/src/tui/input/commands.rs:610）。

## AI 速览

- `COMMAND_SPECS` — TUI 内置 slash 命令静态表，81 条（apps/cli/src/tui/input/commands.rs:56）。
- `TuiCommandSpec` — 一条内置命令的定义：名、用法、描述键、选项（apps/cli/src/tui/input/commands.rs:4）。
- `TuiPluginCommandSpec` — 一条 Core 返回的插件命令（apps/cli/src/tui/input/commands.rs:17）。
- `TuiCommandSuggestion` — 内置或插件命令建议（apps/cli/src/tui/input/commands.rs:25）。
- `matching_command_specs` — 按前缀筛补全候选，混入插件命令（apps/cli/src/tui/input/commands.rs:656）。
- `expand_plugin_command` — 把插件用法展开为多条子命令建议（apps/cli/src/tui/input/commands.rs:558）。
- `handle_shell_command_with_core` — 交互式 shell 的命令分发器（apps/cli/src/chat_runtime.rs:517）。
- `split_shell_command_line` — shell 输入切分器（apps/cli/src/chat_runtime.rs:643）。
- `parse_shell_args` — shell 启动参数解析器，含 --resume（apps/cli/src/chat_runtime.rs:321）。
- `read_cli_plugin_commands` — 向 Core 取插件命令目录（apps/cli/src/cli/mod.rs:1844）。
- `CLI_COMMANDS` — 31 个固有 CLI 命令族（apps/cli/src/cli/mod.rs:1794）。
- `run_cli_root_inner` — CLI 总分发器（apps/cli/src/cli/mod.rs:116）。
- 主入口（shell）：`run_shell_command_with_core`（apps/cli/src/chat_runtime.rs:393）。
- 主入口（CLI）：`run_cli_root_inner`（apps/cli/src/cli/mod.rs:116）。
- 数据流向（补全）：TUI 输入 → `matching_command_specs` 筛候选（apps/cli/src/tui/input/commands.rs:656）。
- 数据流向（shell）：输入 → `split_shell_command_line` 切分 → `handle_shell_command_with_core` 分发（apps/cli/src/chat_runtime.rs:522）。

## 核心机制

`COMMAND_SPECS` 共 81 条，覆盖 25 个顶层命令词：help、diff、new、switch、resume、language、network、model、approval、attach、attachments、clear-attachments、queue、quit、exit、character、group、skill、package、plugin、mcp、status、log、tag、update（apps/cli/src/tui/input/commands.rs:56）。
`network` 一族 36 条，是最大的子树，含 network show、network bootstrap、network pair-confirm、network identity define 等（apps/cli/src/tui/input/commands.rs:120）。
`model` 一族 6 条：model、model current、model list、model choose、model use、model config（apps/cli/src/tui/input/commands.rs:336）。
`queue` 一族 5 条：queue、queue clear、queue delete、queue edit、queue send（apps/cli/src/tui/input/commands.rs:414）。
`approval` 一族 4 条：approval、approval allow、approval ask、approval forbid（apps/cli/src/tui/input/commands.rs:372）。
`new` 一族 3 条：new、new source、new input（apps/cli/src/tui/input/commands.rs:70）。
`language` 一族 3 条：language、language en、language zh-cn（apps/cli/src/tui/input/commands.rs:100）。
`character` 一族 2 条：character、character choose（apps/cli/src/tui/input/commands.rs:456）。
`group` 一族 2 条：group、group choose（apps/cli/src/tui/input/commands.rs:468）。
`package` 一族 2 条：package、package toggle（apps/cli/src/tui/input/commands.rs:486）。
`plugin` 一族 2 条：plugin、plugin toggle（apps/cli/src/tui/input/commands.rs:498）。
`mcp` 一族 2 条：mcp、mcp toggle（apps/cli/src/tui/input/commands.rs:510）。
其余 14 个顶层词各 1 条：help、diff、switch、resume、attach、attachments、clear-attachments、quit、exit、status、log、tag、update、skill（apps/cli/src/tui/input/commands.rs:56）。
`new` 是全表唯一声明 options 的条目，值为 `source` 与 `input`（apps/cli/src/tui/input/commands.rs:73）。
只有名等于命令词的那条才声明 `options`，路径式子命令不声明（apps/cli/src/tui/input/commands.rs:11）。
`language zh-cn` 用小写名做前缀匹配，usage 保留 zh-CN 拼写（apps/cli/src/tui/input/commands.rs:114）。
`help` 是命令表首条，用法为 /help（apps/cli/src/tui/input/commands.rs:58）。
`quit` 与 `exit` 是两条独立条目，共用 `CommandQuitDescription` 描述键（apps/cli/src/tui/input/commands.rs:447）。
`matching_command_specs` 把内置表与 Core 返回的插件命令拼成同一候选集（apps/cli/src/tui/input/commands.rs:656）。
空前缀时只列不含空格的裸命令名（apps/cli/src/tui/input/commands.rs:681）。
`complete_command_input` 用 usage 中第一个 < 或 [ 之前的字面段补全输入（apps/cli/src/tui/input/commands.rs:698）。
`active_command_prefix` 去掉前导斜杠并转小写，含换行的输入不补全（apps/cli/src/tui/input/commands.rs:731）。
`keyword_options_for` 只在有条目名等于命令词且 options 非空时返回选项（apps/cli/src/tui/input/commands.rs:616）。
补全与 TUI 的命令解析器共用 `keyword_options_for`，两边取同一份选项定义（apps/cli/src/tui/input/commands.rs:616）。
`TuiPluginCommandSpec` 是 Core 返回的插件 slash 命令，有 name、usage、description 三个字段（apps/cli/src/tui/input/commands.rs:17）。
`expand_plugin_command` 把 /name <a|b c|d> 形 usage 展开为每备选一条建议（apps/cli/src/tui/input/commands.rs:558）。
备选必须以字面词开头，`<value>` 开头的 usage 不展开（apps/cli/src/tui/input/commands.rs:587）。
插件命令的唯一来源是 Core：CLI 调 `plugin` `commands` `--json` 取目录（apps/cli/src/cli/mod.rs:1848），用户写文件定义 slash 命令的加载机制在 seed 内不存在。
插件命令名与 `CLI_COMMANDS` 冲突时 CLI 报错拒绝启动（apps/cli/src/cli/mod.rs:1855）。
三份 seed 内没有用户自定义 slash 命令的文件加载入口：custom 一词在三份文件里零命中，commands.rs 无文件读取调用；插件命令的唯一来源是 Core 返回的 `TuiPluginCommandSpec`（apps/cli/src/tui/input/commands.rs:17）。
交互式 shell 的提示符由 `short_chat_label` 取 chat-id 前 8 个字符拼成（apps/cli/src/chat_runtime.rs:402）。
空行跳过，以斜杠开头的输入进 `handle_shell_command_with_core`（apps/cli/src/chat_runtime.rs:416）。
不以斜杠开头的输入经 `ChatSendArgs` 发为当前聊天的消息（apps/cli/src/chat_runtime.rs:422）。
`split_shell_command_line` 处理单引号、双引号与反斜杠转义（apps/cli/src/chat_runtime.rs:643）。
引号未闭合时返回错误 unterminated quote（apps/cli/src/chat_runtime.rs:678）。
附件只在消息发送成功后清空，失败时保留队列（apps/cli/src/chat_runtime.rs:431）。
未知 shell 命令返回错误 unknown shell command: /{command}（apps/cli/src/chat_runtime.rs:637）。
`print_shell_usage` 打印 12 行命令，不含 current（apps/cli/src/chat_runtime.rs:690）。
/show 打印当前聊天的完整历史（apps/cli/src/chat_runtime.rs:591）。
`/attach` 只把路径排入待发送附件队列（apps/cli/src/chat_runtime.rs:595）。
/chat 与 /current 都打印当前聊天 id（apps/cli/src/chat_runtime.rs:535）。
`/new` 拒绝 --chat，执行 chat new --json 建新聊天（apps/cli/src/chat_runtime.rs:538）。
`/switch` 调 `switchChat` 切换（apps/cli/src/chat_runtime.rs:552）。
`send_chat_message_with_core_result` 走 Core 命令 chat send --json（apps/cli/src/chat_runtime.rs:722）。
chat send 可带 `--chat` 与 `--attachment` 选项（apps/cli/src/chat_runtime.rs:726）。
chat send 的 `--reply-to` 选项传消息时间戳（apps/cli/src/chat_runtime.rs:730）。
启动参数 --resume 走 `latest_chat_id_with_core`，取 updatedAt 最大的聊天切换（apps/cli/src/chat_runtime.rs:450）。
`latest_chat_id_with_core` 用 `max_by` 取 updatedAt 最大的聊天（apps/cli/src/chat_runtime.rs:475）。
无历史时返回错误 no previous chat to resume（apps/cli/src/chat_runtime.rs:492）。
交互式 shell 里的 /resume 排除当前聊天，取其他聊天中 `max_by` 选出的最新者（apps/cli/src/chat_runtime.rs:569）。
updatedAt 相同时用 `displayOrder` 二次比较（apps/cli/src/chat_runtime.rs:579）。
无其他聊天时 /resume 打印 no previous chat to resume 并继续循环（apps/cli/src/chat_runtime.rs:582）。
有目标时 /resume 调 `switchChat` 切换并打印 Chat: {id}（apps/cli/src/chat_runtime.rs:586）。
启动 --resume 与 shell 内 /resume 的差别：启动时取全部历史的最新者，shell 内排除当前聊天（apps/cli/src/chat_runtime.rs:450）。
parse_shell_args 拒绝重复的 `--resume`（apps/cli/src/chat_runtime.rs:333）。
parse_shell_args 拒绝 --chat 与 --resume 同用，也拒绝 --resume 与 --source 或 --input 同用（apps/cli/src/chat_runtime.rs:365）。
CLI 调用先处理 `help`、-h、--help，再按首词分发（apps/cli/src/cli/mod.rs:122）。
`version` 只打印本地版本，不建 Core（apps/cli/src/cli/mod.rs:129）。
`link`、`identity`、`web` 在建 Core 前本地分发（apps/cli/src/cli/mod.rs:138）。
`install` 与 `uninstall` 在建 Core 前本地分发（apps/cli/src/cli/mod.rs:146）。
`daemon` 命令在建 Core 前先试 `try_run_cli_command`（apps/cli/src/cli/mod.rs:155）。
chat shell 路由到 `run_chat_shell_command_with_core`（apps/cli/src/cli/mod.rs:175）。
`shell` 路由到 `run_shell_command`（apps/cli/src/cli/mod.rs:182）。
每次建 Core 后先调 `read_cli_plugin_commands` 取插件命令目录（apps/cli/src/cli/mod.rs:159）。
名命中插件命令目录的 CLI 命令转发给 `run_core_command_and_print`（apps/cli/src/cli/mod.rs:193）。
未知 CLI 命令报错 Unknown command（apps/cli/src/cli/mod.rs:196）。
`CLI_COMMANDS` 列 31 个固有命令族（apps/cli/src/cli/mod.rs:1794）。
cli_usage_lines 先列固有命令族，再追加插件命令（apps/cli/src/cli/mod.rs:1875）。
run_core_command_and_print 在 --json 模式下给 Core 命令追加 `--json` 参数（apps/cli/src/cli/mod.rs:1448）。
CLI 命令的完整分发见 [[core-command|命令层——CLI 命令编排]]。

## 关键符号

- `COMMAND_SPECS` — TUI 内置 slash 命令静态表，81 条（apps/cli/src/tui/input/commands.rs:56）。
- `TuiCommandSpec` — 一条内置命令的定义：名、用法、描述键、选项（apps/cli/src/tui/input/commands.rs:4）。
- `TuiPluginCommandSpec` — 一条 Core 返回的插件命令（apps/cli/src/tui/input/commands.rs:17）。
- `TuiCommandSuggestion` — 内置或插件命令建议（apps/cli/src/tui/input/commands.rs:25）。
- `matching_command_specs` — 按前缀筛补全候选，混入插件命令（apps/cli/src/tui/input/commands.rs:656）。
- `expand_plugin_command` — 把插件用法展开为多条子命令建议（apps/cli/src/tui/input/commands.rs:558）。
- `complete_command_input` — 用 usage 字面段补全输入（apps/cli/src/tui/input/commands.rs:698）。
- `keyword_options_for` — 取某命令词声明的 keyword-value 选项（apps/cli/src/tui/input/commands.rs:616）。
- `handle_shell_command_with_core` — 交互式 shell 的命令分发器（apps/cli/src/chat_runtime.rs:517）。
- `split_shell_command_line` — shell 输入切分器（apps/cli/src/chat_runtime.rs:643）。
- `parse_shell_args` — shell 启动参数解析器（apps/cli/src/chat_runtime.rs:321）。
- `ShellArgs` — shell 启动参数：resume、chatId、sourceChatId、input、updateCurrentVersion（apps/cli/src/chat_runtime.rs:263）。
- `latest_chat_id_with_core` — 取 updatedAt 最大的聊天 id（apps/cli/src/chat_runtime.rs:475）。
- `send_chat_message_with_core_result` — 经 Core 命令 chat send 发消息（apps/cli/src/chat_runtime.rs:722）。
- `print_shell_usage` — 打印 shell 的 12 行命令表（apps/cli/src/chat_runtime.rs:690）。
- `run_cli_root_inner` — CLI 总分发器（apps/cli/src/cli/mod.rs:116）。
- `CLI_COMMANDS` — 31 个固有 CLI 命令族（apps/cli/src/cli/mod.rs:1794）。
- `read_cli_plugin_commands` — 向 Core 取插件命令目录（apps/cli/src/cli/mod.rs:1844）。
- `run_core_command_and_print` — 转发命令给 Core 并打印输出（apps/cli/src/cli/mod.rs:1442）。
- `print_root_usage` — 打印 operit2 顶层用法（apps/cli/src/cli/mod.rs:1774）。

## 调用链

1. 用户在 TUI 输入 / 前缀，`matching_command_specs` 按前缀筛候选（apps/cli/src/tui/input/commands.rs:656）。
2. 选中建议后 `complete_command_input` 补全字面段（apps/cli/src/tui/input/commands.rs:698）。
3. 插件命令由 Core 返回，经 `expand_plugin_command` 展开后混入候选（apps/cli/src/tui/input/commands.rs:558）。
4. 交互式 shell 读行：斜杠开头进 `handle_shell_command_with_core`，其余当消息发（apps/cli/src/chat_runtime.rs:416）。
5. `handle_shell_command_with_core` 用 `split_shell_command_line` 切分后按首词 match（apps/cli/src/chat_runtime.rs:522）。
6. /resume 在除当前聊天外的历史里取 `max_by` 选出的最新聊天（apps/cli/src/chat_runtime.rs:569）。
7. 选中后调 `switchChat` 切换并打印 Chat: {id}（apps/cli/src/chat_runtime.rs:586）。
8. 消息经 `send_chat_message_with_core_result` 走 Core 命令 chat send --json（apps/cli/src/chat_runtime.rs:722）。
9. CLI 调用先处理 `help`、-h、--help，再按首词分发（apps/cli/src/cli/mod.rs:122）。
10. 插件命令先由 `read_cli_plugin_commands` 取目录，名命中后转发给 Core（apps/cli/src/cli/mod.rs:159）。

## 来源

- apps/cli/src/tui/input/commands.rs（925 行，全文已读）
- apps/cli/src/cli/mod.rs（2354 行，全文已读）
- apps/cli/src/chat_runtime.rs（842 行，全文已读）
- 基线 AAswordman/Operit2 @ 364d1d594；三份 seed 合计 4121 行，全部读完。
- 覆盖边界：TUI 收到回车后如何执行 /network、/model 等命令，分发路径不在三份 seed 内，本页不写；TUI 补全表与交互式 shell 分发器重合的命令词只有 help、exit、quit、new、switch、resume、attach、attachments、clear-attachments 共 9 个，chat、current、show、send 四词只存在于 shell 分发器。
