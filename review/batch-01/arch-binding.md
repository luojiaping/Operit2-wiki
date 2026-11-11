---
title: Binding
module: arch
platforms: [all]
sources: [docs/core-node-space-binding-architecture.md, core/crates/persistence/store/src/CoreNodeBindingStore.rs]
date: 2026-11-11
---

# Binding

## 概述

Binding 是一条记录：一个不透明的业务 key 对应的下一次路由执行由哪个 CoreNode 完成。`docs/core-node-space-binding-architecture.md:143`

Binding 由 `key`、`nodeId`、`generation` 三个字段组成。`docs/core-node-space-binding-architecture.md:134`

Binding 层不知道 `key` 是否来自聊天、任务或其他业务对象；聊天路由直接使用现有 `chatId` 作为 `key`。`docs/core-node-space-binding-architecture.md:145`

Binding 不表示业务数据位于目标节点。`docs/core-node-space-binding-architecture.md:146`

同一个 Agent 的不同聊天可以绑定不同 CoreNode；切换 Binding 不移动 Agent，也不移动其对话。`docs/core-node-space-binding-architecture.md:150`

Binding 是 [[arch-corenode|CoreNode]] 与 [[arch-space|Space]] 之间的执行指向：Space 把多个已配对 CoreNode 组成同一个持续同步网络，Binding 决定一个聊天的下一步在哪个 CoreNode 执行，实时转发层把调用送到该节点。

## AI 速览

核心符号：

- `CoreNodeBindingRecord` — Binding 的持久化记录：`key`、`nodeId`、`generation` 三个字段。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:84`
- `CoreNodeBindingStore` — 持久化 Binding 记录的存储，以公共同步日志为后盾。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:99`
- `CoreNodeBindingCommit` — 一次已提交的 Binding 变更：变更后的记录与持久化它的同步操作。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:92`
- `BINDING_SYNC_DOMAIN` — Binding 记录的同步域，值为 `binding`。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:17`
- `create` — 为新业务 key 创建初始 Binding，`generation` 从 1 开始。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:145`
- `compareAndSet` — 以当前值比较写入的方式原子切换 Binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:180`
- `binding` — 读取一个 key 的当前 Binding 记录，不存在时报错。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:125`
- `delete` — 退役一个 key，即使其 Binding 尚未到达。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:168`
- `applySyncedOperation` — 应用已同步的 Binding 操作，不产生新的本地操作。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:215`
- `applyImmediateOperation` — 应用直接传输的 Binding 操作，不推进持久化同步时钟。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:261`

主入口：`CoreNodeBindingStore::compareAndSet`（比较写入切换 Binding）与 `CoreNodeBindingStore::create`（新建 Binding）。

数据流向：Binding 记录以 `upsert` 或 `delete` 操作写进公共同步日志的 `binding` 域，经 Space 持久化同步复制到获准成员，各节点按最新操作物化当前记录。

## 核心机制

### key 的含义

Binding 的 `key` 是业务方法声明的不透明 key，Binding 层不解释它的业务含义。聊天路由直接使用现有 `chatId` 作为 `key`，但该含义只存在于 Chat 业务代码和方法注解中。`docs/core-node-space-binding-architecture.md:145`

Agent 在当前工具调用上下文中已经拥有 `chatId`，因此切换工具只需要目标 `nodeId`。`docs/core-node-space-binding-architecture.md:151`

Binding 不表示业务数据位于目标节点；Agent、聊天、消息、记忆、工具结果、配置和 Binding 本身都由 Space 持久化同步服务复制到获准参与业务存储的成员。`docs/core-node-space-binding-architecture.md:146`

### generation 单调递增

创建可执行聊天时，Chat 仓库单独写入 `Binding(chatId)`。`docs/core-node-space-binding-architecture.md:170`

每次比较写入成功后 `generation` 单调递增，它同时标识目标节点即将执行的 `continuation`。`docs/core-node-space-binding-architecture.md:171`

存储层印证这一规则：初始 Binding 的 `generation` 为 1。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:157`

比较写入成功时新记录的 `generation` 为 `current.generation + 1`。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:209`

校验规则要求 Binding 的 `generation` 必须为正数。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:461`

目标节点按 `(chatId, executionGeneration)` 识别 `continuation`；已完成相同或更高 `generation` 时直接返回，不重复调用模型或工具。`docs/core-node-space-binding-architecture.md:420`

### 比较写入与冲突

`compareAndSet` 以当前值比较写入的方式原子切换 Binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:180`

当前 `nodeId` 与 `expectedNodeId` 不一致时，比较写入返回 `Binding conflict` 错误。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:196`

目标与当前相同时，比较写入直接返回当前记录与最新操作，不写入新记录。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:201`

Binding 的冲突顺序复用持久化同步操作的设备序列和向量时钟；同步元数据不是 Binding 的业务字段。`docs/core-node-space-binding-architecture.md:178`

物化时，每个 `entityId` 只取按 `bindingOperationOrder` 排序的最新操作；只有 `operation` 为 `upsert` 的操作才成为当前 Binding 记录。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:301`

每个需要路由的业务 key 必须有一条 Binding。Binding 缺失或指向非 Space 成员时，请求返回明确错误。`docs/core-node-space-binding-architecture.md:172`

### 切换边界与续接

切换 CoreNode 直接携带当前运行上下文续接，不触发会话总结或上下文压缩。`docs/core-node-space-binding-architecture.md:379`

CoreNode 切换必须发生在工具调用已经完成、工具结果已经持久化、下一轮模型请求尚未发起的边界。`docs/core-node-space-binding-architecture.md:385`

切换流程中，源节点验证目标可达、在一个事务内持久化工具调用与工具结果、Router 比较写入得到新的 `generation` 和操作、目标节点在恢复业务前应用并校验 Binding 操作。`docs/core-node-space-binding-architecture.md:396`

`requiredClock` 是持久化同步屏障；`execution generation` 来自 Binding 比较写入，不复用模型进程内部的 `execution` 或 `round` 身份。`docs/core-node-space-binding-architecture.md:407`

Router 在比较写入前验证目标属于 Space 且 Link 路由可达；比较写入成功后它就是新的唯一执行位置；后续失败不自动把 Binding 改回源节点。`docs/core-node-space-binding-architecture.md:410`

Binding 目标不可达时由发起设备原子接管，显式设备调用仍返回明确错误。`docs/core-node-space-binding-architecture.md:488`

### 单一执行者

每轮模型请求开始前，CoreNode 必须确认 `Binding(chatId)` 指向自己；只有当前执行节点能够提交 Agent 发起的切换；旧节点观察到 Binding 已改变后不得继续下一轮模型请求。`docs/core-node-space-binding-architecture.md:416`

门控持有期间，最终 assistant message、结构化 parts、chat metadata、`completedExecutionGeneration` 和同步操作在同一个 SQLite 事务内提交；Binding Store 不读取任何 Chat 类型或表。`docs/core-node-space-binding-architecture.md:424`

### 哪些请求走 Binding 路由

只有模型执行、工具循环、取消当前执行和实时执行状态进入 Binding 路由；聊天历史读取、配置编辑和其他持久化数据操作在本地 Core 执行。`docs/core-node-space-binding-architecture.md:362`

整段会话删除属于本地持久化操作，不要求存在 Binding，也不要求执行节点在线。`docs/core-node-space-binding-architecture.md:365`

请求类型由真实 Core 方法上的 `#[operit_core_route(...)]` 声明，经 typed Core codegen 生成。`docs/core-node-space-binding-architecture.md:371`

### Agent 的切换工具

`list_core_nodes` 只读取本机已经同步的 Space 成员视图。`docs/core-node-space-binding-architecture.md:159`

成员 `reachable` 与设备面板同源：只要当前 Peer Link 图能解析出路由计划（含直连的 1 跳）即为可达。`docs/core-node-space-binding-architecture.md:160`

`switch_core` 在调用时按同一份路由视图校验目标：目标不是 Space 成员或当前不可达时，工具直接返回失败。`docs/core-node-space-binding-architecture.md:164`

目标引用按精确 ID、精确名称、大小写不敏感名称、唯一前缀的顺序解析，重名或前缀歧义时返回候选列表而不猜测。`docs/core-node-space-binding-architecture.md:166`

`BindingRouteStatus` 表示对话的执行节点，不表示模型推理位置或请求是否需要联网。`docs/core-node-space-binding-architecture.md:175`

### 存储操作与校验

`createLocal` 创建以本机 CoreNode 为初始目标的 Binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:163`

`delete` 退役一个 key，即使其 Binding 尚未到达，也不需要其执行节点。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:168`

`applyBootstrapOperation` 应用 Space 启动引导的 Binding 操作且不做本地冲突过滤。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:221`

`validateBindingOperation` 要求 `domain` 为 `binding`、`entityType` 为 `binding`、`operation` 为 `upsert` 或 `delete`、`semantics` 为 `EntityState`。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:441`

`delete` 操作的 `payload` 必须为 null。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:449`

`upsert` 操作的 `payload` 中 `binding.key` 必须与 `entityId` 一致。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:457`

`validateBindingKey` 要求 `key` 去空白后非空。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:470`

`validateBindingNodeId` 要求 `nodeId` 去空白后非空。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:478`

## 关键符号

- `Binding` — 记录：key 对应的下一次路由执行由哪个 CoreNode 完成；字段为 `key`、`nodeId`、`generation`。`docs/core-node-space-binding-architecture.md:134`
- `CoreNodeBindingStore` — 持久化 Binding 记录的存储，以公共同步日志为后盾。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:99`
- `CoreNodeBindingRecord` — Binding 的持久化记录。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:84`
- `CoreNodeBindingCommit` — 一次已提交的 Binding 变更。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:92`
- `BINDING_SYNC_DOMAIN` — 同步域常量，值为 `binding`。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:17`
- `create` — 为新业务 key 创建初始 Binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:145`
- `createLocal` — 创建以本机 CoreNode 为初始目标的 Binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:163`
- `binding` — 读取一个 key 的当前 Binding 记录。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:125`
- `bindingOptional` — 读取一个 key 的当前 Binding 记录，不存在时返回空。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:132`
- `contains` — 报告一个 key 是否已有持久化的当前记录。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:140`
- `compareAndSet` — 以当前值比较写入的方式原子切换 Binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:180`
- `delete` — 退役一个 key。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:168`
- `applySyncedOperation` — 应用已同步的 Binding 操作。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:215`
- `applyBootstrapOperation` — 应用 Space 启动引导的 Binding 操作。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:221`
- `applyImmediateOperation` — 应用直接传输的 Binding 操作。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:261`
- `materializeBindingRecords` — 从公共同步日志物化全部当前 Binding。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:297`
- `validateBindingOperation` — 校验 Binding 操作的完整契约。`core/crates/persistence/store/src/CoreNodeBindingStore.rs:440`
- `list_core_nodes` — Agent 获取精确节点 ID 的工具，只读本机已同步的成员视图。`docs/core-node-space-binding-architecture.md:159`
- `switch_core` — Agent 切换执行节点的工具，调用时校验目标。`docs/core-node-space-binding-architecture.md:164`
- `BindingRouteStatus` — 对话执行节点的提示来源。`docs/core-node-space-binding-architecture.md:175`
- `requiredClock` — 持久化同步屏障，目标节点在继续执行前等待它。`docs/core-node-space-binding-architecture.md:407`

## 调用链

本地请求先进入本机 CoreNodeRouter：普通请求走 LocalCoreProxy；带注解的 Binding 请求经 `Binding(key)` 路由到目标 CoreNode；只有模型执行、工具循环、取消当前执行和实时执行状态进入 Binding 路由。`docs/core-node-space-binding-architecture.md:362`

一次 `switch_core` 交接的完整流程（`Binding(chat-1)` 从 node-A 切到 node-D）：

1. node-A 的模型产生 `switch_core(node-D)`。`docs/core-node-space-binding-architecture.md:395`
2. node-A 验证 node-D 是可达的 Space 成员。`docs/core-node-space-binding-architecture.md:396`
3. node-A 在一个事务内持久化 assistant 工具调用、工具结果、chat metadata 和同步操作。`docs/core-node-space-binding-architecture.md:397`
4. 响应业务向 Router 返回只包含目标和不透明 payload 的 route transition。`docs/core-node-space-binding-architecture.md:398`
5. Router 比较写入 `Binding(chat-1) = node-D`，得到新的 `generation` 和 operation。`docs/core-node-space-binding-architecture.md:399`
6. Router 把 Binding record 和 operation 放入 Link route context，把不透明 transition 作为业务参数发送到 node-D。`docs/core-node-space-binding-architecture.md:400`
7. node-D 的 Router 在调用业务恢复方法前应用并校验 Binding operation，但不提前推进持久化同步 clock。`docs/core-node-space-binding-architecture.md:401`
8. node-D 的响应业务只接收 Link 定义的 route key/generation，等待 `requiredClock`。`docs/core-node-space-binding-architecture.md:402`
9. node-D 加载已同步 assistant 消息并使用 `switch_core` 的工具结果发起下一轮模型请求。`docs/core-node-space-binding-architecture.md:403`
10. node-D 的输出事件继续写入原来的逻辑响应流。`docs/core-node-space-binding-architecture.md:404`

## 来源

- `docs/core-node-space-binding-architecture.md`（494 行，100% 已读）
- `core/crates/persistence/store/src/CoreNodeBindingStore.rs`（481 行，100% 已读）
