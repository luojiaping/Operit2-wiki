---
title: Subagent 并行
module: agent
platforms: [all]
sources: 9
date: 2026-11-11
---

## 概述

插件的 toolpkg_id 是 `com.operit.subagents`。(plugins/packages/external/subagents/manifest.json:3)
插件把独立任务交给子代理并行执行，创建后返回 agent ID。(plugins/packages/external/subagents/src/tools.ts:7)
子代理继承源聊天的执行配置，任务说明需要自包含。(plugins/packages/external/subagents/src/tools.ts:7)
插件作为可选插件提供，默认不启用。(plugins/packages/external/subagents/README.md:5)
子代理是独立的原生会话，继承源会话配置，不复制消息历史。(plugins/packages/external/subagents/README.md:9)
子代理完成不唤醒父会话，主聊天用 `wait_agent` 轮询结果。(plugins/packages/external/subagents/README.md:43)

## AI 速览

- `spawn_agent` — 创建并启动独立子代理，立即返回 agent ID。(plugins/packages/external/subagents/src/tools.ts:13)
- `wait_agent` — 等待指定子代理的当前轮次，任一结束即返回。(plugins/packages/external/subagents/src/tools.ts:21)
- `send_input` — 给子代理发送新指令。(plugins/packages/external/subagents/src/tools.ts:29)
- `close_agent` — 取消并关闭子代理及其后代。(plugins/packages/external/subagents/src/tools.ts:38)
- `list_agents` — 列出当前聊天的子代理、轮次、运行状态及最终结果。(plugins/packages/external/subagents/src/tools.ts:43)
- `AgentManager` — 管理创建、轮次、容量、等待订阅、取消和关闭。(plugins/packages/external/subagents/src/manager.ts:49)
- `MAX_ACTIVE_AGENTS` — 并发上限 8。(plugins/packages/external/subagents/src/model.ts:8)
- `DEFAULT_WAIT_MS` — 默认等待 30000 毫秒。(plugins/packages/external/subagents/src/model.ts:7)
- `AgentStatus` — 8 个状态：starting、running、completed、cancelled、failed、closing、closed、interrupted。(plugins/packages/external/subagents/src/model.ts:10)
- `Repository` — SQLite 持久化，串行化写操作。(plugins/packages/external/subagents/src/storage.ts:20)
- `Agents` — 工具与 UI 调主运行时 manager 的类型化入口。(plugins/packages/external/subagents/src/client.ts:10)
- `CHANNEL` — IPC 通道，值是 subagents.control。(plugins/packages/external/subagents/src/model.ts:5)
- `registerToolPkg` — 注册会话路由、导航入口与输入框上方插槽。(plugins/packages/external/subagents/src/main.ts:8)
- 主入口（模型工具）：`spawn_agent` 创建子代理。(plugins/packages/external/subagents/src/tools.ts:13)
- 主入口（分发）：`request` 按 action 分发五种操作。(plugins/packages/external/subagents/src/manager.ts:85)
- 数据流向：模型工具 → `Agents` 经 IPC 发到主运行时。(plugins/packages/external/subagents/src/client.ts:6)
- `receive` 校验后交给 manager 执行。(plugins/packages/external/subagents/src/service.ts:70)
- `Repository` 把记录落到 `subagents.sqlite`。(plugins/packages/external/subagents/src/storage.ts:15)
- `watchParent` 订阅父会话快照推给 UI。(plugins/packages/external/subagents/src/storage.ts:63)
- `watchAgent` 订阅单个代理快照推给 UI。(plugins/packages/external/subagents/src/storage.ts:81)

## 核心机制

### 五个工具

五个工具由 ToolPkg 子包（入口 `dist/tools.js`）注册，包工具的执行路径见 [[core-tool-packages-mcp|工具系统——包、技能与 MCP]]。(plugins/packages/external/subagents/manifest.json:15)
`spawn_agent` 创建并启动独立子代理，立即返回 agent ID。(plugins/packages/external/subagents/src/tools.ts:13)
`spawn_agent` 的参数只有 `name` 与 `task`，均为必填。(plugins/packages/external/subagents/src/tools.ts:15)
`wait_agent` 等待指定子代理的当前轮次，任一结束即返回。(plugins/packages/external/subagents/src/tools.ts:21)
`wait_agent` 的 `agent_ids` 接受 1 到 16 个不重复的本聊天子代理 ID。(plugins/packages/external/subagents/src/tools.ts:23)
`wait_agent` 的 `timeout_ms` 范围是 1 到 30000 毫秒，默认 30000。(plugins/packages/external/subagents/src/tools.ts:24)
`send_input` 给子代理发送新指令，`interrupt` 默认是 false。(plugins/packages/external/subagents/src/tools.ts:31)
`close_agent` 取消并关闭子代理及其后代，保留会话与执行记录。(plugins/packages/external/subagents/src/tools.ts:38)
`list_agents` 列出当前聊天的子代理、轮次、运行状态及最终结果。(plugins/packages/external/subagents/src/tools.ts:43)
五个工具都只操作调用者所在聊天的子代理，工具层经 `parentChat` 取宿主认证的聊天 ID。(plugins/packages/external/subagents/src/tools.ts:65)
子代理只由 AI 经 `spawn_agent` 创建，面板不提供手动创建入口。(plugins/packages/external/subagents/README.md:9)

### 并发上限与调度

并发上限是 8，由 `MAX_ACTIVE_AGENTS` 定义。(plugins/packages/external/subagents/src/model.ts:8)
未结算执行数加待启动数达到 8 时，`reserveStart` 抛错拒绝创建。(plugins/packages/external/subagents/src/manager.ts:159)
达到上限时直接抛错，不等待空位。(plugins/packages/external/subagents/src/manager.ts:159)
新建和后续轮次共享同一个 8 个并发上限。(plugins/packages/external/subagents/README.md:27)
创建子代理前调用 `reserveStart` 占位。(plugins/packages/external/subagents/src/manager.ts:132)
发新轮次前同样调用 `reserveStart` 占位。(plugins/packages/external/subagents/src/manager.ts:299)
同一子代理同一时间只允许一个控制操作，已有控制操作进行中时 `command` 抛错。(plugins/packages/external/subagents/src/manager.ts:166)
父会话本身是子代理且正在关闭或已有控制操作时，创建被拒绝。(plugins/packages/external/subagents/src/manager.ts:131)

### 等待语义

默认等待 30 秒，由 `DEFAULT_WAIT_MS` 定义。(plugins/packages/external/subagents/src/model.ts:7)
`wait` 要求 `agent_ids` 为 1 到 16 个不重复 ID。(plugins/packages/external/subagents/src/manager.ts:337)
`wait` 要求 `timeoutMs` 为 1 到 30000 的整数。(plugins/packages/external/subagents/src/manager.ts:338)
任一目标轮次不活跃时立即返回，`timed_out` 为 false。(plugins/packages/external/subagents/src/manager.ts:344)
超时只结束本次等待，任务继续执行，可继续调用 `wait_agent`。(plugins/packages/external/subagents/src/tools.ts:21)
超时回调调用 `finishWait`，以超时标记结束本次等待。(plugins/packages/external/subagents/src/manager.ts:351)
`finishWait` 用观察到的轮次快照结束等待，`timed_out` 只属于本次等待。(plugins/packages/external/subagents/src/manager.ts:360)
`publish` 按 `runNumber` 匹配等待目标，不匹配的轮次不结束等待。(plugins/packages/external/subagents/src/manager.ts:366)
`publish` 只在目标轮次结算为非活跃状态时结束等待。(plugins/packages/external/subagents/src/manager.ts:368)
`wait_agent` 观察的是调用时的轮次，打断启动新轮次后旧 wait 返回旧轮次的取消回执。(plugins/packages/external/subagents/README.md:29)
多选等待采用任一结束语义。(plugins/packages/external/subagents/README.md:29)

### 子任务完成不唤醒父会话

原生发送请求的 `notifyReply` 是 false。(plugins/packages/external/subagents/src/manager.ts:190)
插件不会在结果完成后自动恢复主模型生成。(plugins/packages/external/subagents/README.md:43)
主聊天用 `wait_agent` 获取结果并继续自己的轮次。(plugins/packages/external/subagents/README.md:43)

### 重启后状态

插件主运行时重启会丢失正在执行轮次的观察句柄。(plugins/packages/external/subagents/README.md:41)
重启加载时，仍活跃的记录被改成 `interrupted`。(plugins/packages/external/subagents/src/manager.ts:77)
错误文本写明观察已丢失，原生执行仍在运行。(plugins/packages/external/subagents/src/manager.ts:77)
重启后改写的记录会重新保存。(plugins/packages/external/subagents/src/manager.ts:80)
非活跃记录在重启后保持原状态。(plugins/packages/external/subagents/src/manager.ts:78)
`isActive` 把 starting、running、closing 视为活跃。(plugins/packages/external/subagents/src/model.ts:88)
SDK 当前没有重新附着到已有执行流或直接向生成中模型注入指令的接口。(plugins/packages/external/subagents/README.md:41)
重新发送前会核对原生会话是否仍在执行。(plugins/packages/external/subagents/README.md:41)

### 持久化与订阅

记录存在 `subagents.sqlite`，路径在包数据目录下。(plugins/packages/external/subagents/src/storage.ts:15)
详细记录与父会话列表在同一次宿主事务 `commit` 里提交。(plugins/packages/external/subagents/src/storage.ts:51)
写操作经一条 promise 链串行化。(plugins/packages/external/subagents/src/storage.ts:44)
加载时按每页 200 条读全部记录，身份不匹配或重复时抛错。(plugins/packages/external/subagents/src/storage.ts:30)
`watchParent` 用 exact-key watch 订阅父会话快照。(plugins/packages/external/subagents/src/storage.ts:63)
`watchAgent` 订阅单个代理的快照，记录不存在时抛错。(plugins/packages/external/subagents/src/storage.ts:81)
`summary` 去掉 messages 后返回摘要。(plugins/packages/external/subagents/src/model.ts:82)
`parseAgent` 拒绝 schemaVersion 不是 1 的记录。(plugins/packages/external/subagents/src/model.ts:95)

### 创建与身份

创建子会话用 `Tools.Chat.createNew`，不设为当前聊天。(plugins/packages/external/subagents/src/service.ts:11)
子代理通过独立的 `sourceChatId` 继承源会话配置，不复制消息历史。(plugins/packages/external/subagents/README.md:9)
工具创建携带实际调用参与者 ID。(plugins/packages/external/subagents/README.md:9)
`spawn_agent` 用宿主提供的调用者参与者 ID 创建子代理。(plugins/packages/external/subagents/src/tools.ts:60)
原生创建返回已用过的会话身份时抛错。(plugins/packages/external/subagents/src/manager.ts:137)
新建子代理状态为 `starting`，`runNumber` 为 1，`lastInput` 是任务文本。(plugins/packages/external/subagents/src/manager.ts:142)

### 默认启用：两处声明并不相同

manifest 的 `enabled_by_default` 是 false。(plugins/packages/external/subagents/manifest.json:12)
tools.ts 的 METADATA 把 `enabled_by_default` 写成 true。(plugins/packages/external/subagents/src/tools.ts:4)
README 说明工具子包的默认启用声明在 tools.ts 的 METADATA，容器本身仍默认关闭。(plugins/packages/external/subagents/README.md:57)

### 界面挂载

`registerToolPkg` 注册 `conversation` 路由，用 compose_dsl 渲染并 keepAlive。(plugins/packages/external/subagents/src/main.ts:10)
`registerToolPkg` 注册工作区导航入口，图标是 account_tree。(plugins/packages/external/subagents/src/main.ts:12)
`registerToolPkg` 注册 `above_input` 插槽，顺序是 20 并 keepAlive。(plugins/packages/external/subagents/src/main.ts:14)
面板只在存在运行中子代理时显示，没有运行中任务时整块收起。(plugins/packages/external/subagents/README.md:5)
`test_connection` 不创建会话或任务就返回 passed。(plugins/packages/external/subagents/src/main.ts:19)
`test_tool_call` 用 `listChats` 取 1 条聊天做只读检查。(plugins/packages/external/subagents/src/main.ts:25)

## 关键符号

- `AgentManager` — 管理创建、轮次、容量、等待订阅、取消和关闭。(plugins/packages/external/subagents/src/manager.ts:49)
- `spawn_agent` — 创建并启动独立子代理，立即返回 agent ID。(plugins/packages/external/subagents/src/tools.ts:13)
- `wait_agent` — 等待指定子代理的当前轮次，任一结束即返回。(plugins/packages/external/subagents/src/tools.ts:21)
- `send_input` — 给子代理发送新指令。(plugins/packages/external/subagents/src/tools.ts:29)
- `close_agent` — 取消并关闭子代理及其后代。(plugins/packages/external/subagents/src/tools.ts:38)
- `list_agents` — 列出当前聊天的子代理与最终结果。(plugins/packages/external/subagents/src/tools.ts:43)
- `MAX_ACTIVE_AGENTS` — 并发上限 8。(plugins/packages/external/subagents/src/model.ts:8)
- `DEFAULT_WAIT_MS` — 默认等待 30000 毫秒。(plugins/packages/external/subagents/src/model.ts:7)
- `AgentStatus` — 8 个状态：starting、running、completed、cancelled、failed、closing、closed、interrupted。(plugins/packages/external/subagents/src/model.ts:10)
- `Agent` — 持久化记录，摘要之外多一个 messages 快照数组。(plugins/packages/external/subagents/src/model.ts:45)
- `AgentSummary` — 不含消息的摘要。(plugins/packages/external/subagents/src/model.ts:26)
- `WaitResult` — 只有 `timed_out` 与 agents 两个字段。(plugins/packages/external/subagents/src/model.ts:56)
- `Repository` — SQLite 持久化，串行化写操作。(plugins/packages/external/subagents/src/storage.ts:20)
- `Agents` — 工具与 UI 调主运行时 manager 的类型化入口。(plugins/packages/external/subagents/src/client.ts:10)
- `registerService` — 把 `receive` 挂到 `CHANNEL` 通道。(plugins/packages/external/subagents/src/service.ts:75)
- `CHANNEL` — IPC 通道，值是 subagents.control。(plugins/packages/external/subagents/src/model.ts:5)
- `SCHEMA_VERSION` — 持久化记录版本 1。(plugins/packages/external/subagents/src/model.ts:6)
- `registerToolPkg` — 注册会话路由、导航入口与输入框上方插槽。(plugins/packages/external/subagents/src/main.ts:8)

## 调用链

### 创建子代理

1. 模型调用 `spawn_agent`，传入 `name` 与 `task`。(plugins/packages/external/subagents/src/tools.ts:58)
2. 工具层用 `parentChat` 取宿主认证的聊天 ID，并取调用者参与者 ID。(plugins/packages/external/subagents/src/tools.ts:60)
3. `Agents` 经 `ToolPkg.ipc.call` 把请求发到 targetRuntime 为 main 的主运行时。(plugins/packages/external/subagents/src/client.ts:6)
4. `receive` 先 `decodeRequest` 校验再交给 manager。(plugins/packages/external/subagents/src/service.ts:70)
5. `request` 按 action 分发到 `spawn`。(plugins/packages/external/subagents/src/manager.ts:89)
6. 创建前调用 `reserveStart` 占位。(plugins/packages/external/subagents/src/manager.ts:132)
7. 原生创建子会话，状态为 `starting`，`runNumber` 为 1。(plugins/packages/external/subagents/src/manager.ts:142)
8. `launch` 在后台启动执行，立即返回摘要。(plugins/packages/external/subagents/src/manager.ts:146)
9. 执行向原生会话提交输入，`notifyReply` 为 false。(plugins/packages/external/subagents/src/manager.ts:190)
10. `part` 事件按 messageTimestamp 整体替换消息快照。(plugins/packages/external/subagents/src/manager.ts:214)
11. 终态按原生 outcome 映射：committed 与 not_persisted 取 outcome 的状态，blocked 与 consumed 记为 failed。(plugins/packages/external/subagents/src/manager.ts:228)
12. 父会话用 `wait_agent` 轮询结果。(plugins/packages/external/subagents/README.md:43)

### 等待子代理

1. 模型调用 `wait_agent`，传入 `agent_ids` 与可选的 `timeout_ms`。(plugins/packages/external/subagents/src/tools.ts:65)
2. `wait` 校验 ID 数量与超时范围。(plugins/packages/external/subagents/src/manager.ts:337)
3. 任一目标轮次不活跃时立即返回，`timed_out` 为 false。(plugins/packages/external/subagents/src/manager.ts:344)
4. 否则订阅等待，超时回调调用 `finishWait`。(plugins/packages/external/subagents/src/manager.ts:351)
5. 目标轮次结算时 `publish` 结束等待。(plugins/packages/external/subagents/src/manager.ts:368)

### 发送新指令

1. 模型调用 `send_input`，传入 `agent_id`、`message` 与可选的 `interrupt`。(plugins/packages/external/subagents/src/tools.ts:71)
2. 运行中且 `interrupt` 为 false 时明确抛错。(plugins/packages/external/subagents/src/manager.ts:296)
3. interrupt 为 true 时 `cancelExecution` 等真实结束。(plugins/packages/external/subagents/src/manager.ts:297)
4. 发新轮次前查 `isProcessing`，原生仍在执行就抛错。(plugins/packages/external/subagents/src/manager.ts:301)
5. 新轮次 `runNumber` 加 1，状态回到 `starting`。(plugins/packages/external/subagents/src/manager.ts:303)

### 关闭子代理

1. 模型调用 `close_agent`，传入 `agent_id`。(plugins/packages/external/subagents/src/tools.ts:77)
2. 关闭先递归调用 `close` 关闭未关闭的子任务。(plugins/packages/external/subagents/src/manager.ts:317)
3. 运行中的执行先存为 `closing` 再取消。(plugins/packages/external/subagents/src/manager.ts:320)
4. 原生仍在执行时请求取消并每 100 毫秒轮询直到空闲。(plugins/packages/external/subagents/src/manager.ts:327)
5. 关闭完成存为 `closed` 并发布。(plugins/packages/external/subagents/src/manager.ts:329)

### 重启

1. 插件主运行时重启，`initialize` 重新加载已保存记录。(plugins/packages/external/subagents/src/manager.ts:73)
2. 仍活跃的记录被改成 `interrupted` 并重新保存。(plugins/packages/external/subagents/src/manager.ts:77)
3. 非活跃记录保持原状态。(plugins/packages/external/subagents/src/manager.ts:78)

## 来源

- plugins/packages/external/subagents/src/main.ts
- plugins/packages/external/subagents/src/manager.ts
- plugins/packages/external/subagents/src/tools.ts
- plugins/packages/external/subagents/src/model.ts
- plugins/packages/external/subagents/src/service.ts
- plugins/packages/external/subagents/src/storage.ts
- plugins/packages/external/subagents/src/client.ts
- plugins/packages/external/subagents/manifest.json
- plugins/packages/external/subagents/README.md
