---
title: Operit2 不是什么
module: intro
platforms: [all]
sources: [README.md, README-zh.md, docs/core-node-space-binding-architecture.md]
date: 2026-11-11
---

# Operit2 不是什么

## 概述

Operit2 的定位是一个连接用户设备空间的 `Agent` 核心，见 `README.md:3`。本页只讲 Operit2 不是什么：以 README 与架构文档原文划出的边界为准，不做引申，见 [[intro-overview|Operit2 是什么]]。

预览阶段，底层结构、数据格式、插件契约和跨设备流程仍未冻结，见 `README.md:14`。架构文档中标注为目标、计划或演进方向的内容不代表所有平台已经实现，判断当前实际行为以源码、命令帮助输出、构建结果和目标平台运行结果为准，见 `README.md:246`。

## AI 速览

- `CoreNode` — 运行 Core 的应用实例，见 `README.md:18`
- `Space` — 节点成员、路由和持久化同步的范围，见 `docs/core-node-space-binding-architecture.md:28`
- `Binding` — 一个 key 的下一次路由执行由哪个 `CoreNode` 完成，见 `docs/core-node-space-binding-architecture.md:141`
- `Host` — 节点本地能力的来源，见 `README.md:18`
- `HostManager` — 一个 `CoreNode` 唯一持有的一套组合中的一员，见 `docs/core-node-space-binding-architecture.md:51`
- `OperitApplication` — `CoreNode` 的组成部分，见 `docs/core-node-space-binding-architecture.md:51`
- `LocalCoreProxy` — `CoreNode` 的组成部分，见 `docs/core-node-space-binding-architecture.md:51`
- `RoutedLink` — 转发时在现有 Link 消息外加的一层，见 `docs/core-node-space-binding-architecture.md:289`

主入口：`operit2 cli link space join <session-name>`，加入 Space 前先完成配对与连接，见 `docs/core-node-space-binding-architecture.md:88`。

数据流向：任务交接以工具结果已持久化、下一轮模型请求尚未开始为边界，目标节点取得同步记录后继续，见 `README.md:22`。

## 核心机制

### 没有固定主节点

`Space` 中的节点地位对等，见 `README.md:20`。
`Linux` 云端设备承担更多任务也不会因此成为固定的主节点，见 `README.md:20`。
服务监听方、连接发起方和请求执行方只是一次连接或调用中的角色，不形成主节点和从节点，见 `docs/core-node-space-binding-architecture.md:58`。
`Linux` 云端设备是 `Space` 中的普通 `CoreNode`，不因此拥有中心身份，见 `README.md:101`。

### 加入 Space 不继承权限

加入 `Space` 不会自动授予节点其他设备的系统权限，见 `README.md:20`。
`Space` 成员资格不会授予其他节点读取本机文件、使用本机终端或获得管理员/root 能力，见 `README.md:127`。
`API` key、设备私钥、配对密钥、session 和本地平台权限默认属于节点本地，不会因为加入 `Space` 自动复制，见 `README.md:128`。
`Full` 只表示 AI 能力限制放宽，不表示 `Host` 提权，也不能创造操作系统没有的能力，见 `README.md:129`。
设备身份、配对 secret 和 `Host` 授权保持节点本地，`Space` 成员资格不授予其他节点直接读取本机文件或终端的能力，见 `docs/core-node-space-binding-architecture.md:472`。

### 不搬迁运行中的东西

任务交接以工具结果已持久化、下一轮模型请求尚未开始为边界，见 `README.md:22`。
任务接续依赖保存的上下文和任务事实，不搬迁正在运行的模型请求、终端进程或浏览器会话，见 `README.md:22`。
活动中的进程和实时会话仍然属于原节点，备份不等于所有运行时状态已经能够无缝迁移，见 `README.md:90`。
切换 `CoreNode` 不触发会话总结或上下文压缩，上下文压缩仍由独立的自动阈值或用户手动操作触发，见 `docs/core-node-space-binding-architecture.md:379`。
实时传输不负责复制持久化业务数据，见 `docs/core-node-space-binding-architecture.md:280`。
实时 continuation 的同步时钟只是交接屏障，不表示数据迁移，见 `docs/core-node-space-binding-architecture.md:281`。

### Binding 只决定下一步，不移动数据

`Binding` 只表达一句话：这个 key 对应的下一次路由执行由哪个 `CoreNode` 完成，见 `docs/core-node-space-binding-architecture.md:141`。`Binding` 不表示业务数据位于目标节点，见 `docs/core-node-space-binding-architecture.md:146`。同一个 Agent 的不同聊天可以绑定不同 `CoreNode`，切换 `Binding` 不会移动 Agent，也不会移动其对话，见 `docs/core-node-space-binding-architecture.md:150`。`Binding` 改变不移动数据，见 `docs/core-node-space-binding-architecture.md:482`。一个 chat 的同一执行轮次只有一个 `CoreNode` 可以推进，见 `docs/core-node-space-binding-architecture.md:484`。`Binding` 目标不可达时由发起设备原子接管，显式设备调用仍返回明确错误，见 `docs/core-node-space-binding-architecture.md:488`。

### Space 不表达执行位置与数据归属

`Space` 只负责三件事：确定协作范围、确定可承载 `Space` 流量的已配对连接、确定持久化数据同步范围，见 `docs/core-node-space-binding-architecture.md:69`。
`Space` 不表达执行位置，也不表达数据归属，见 `docs/core-node-space-binding-architecture.md:77`。
`Space` 不是执行容器，不拥有 Agent、聊天或运行时，见 `docs/core-node-space-binding-architecture.md:28`。
执行模型只包含 `CoreNode` 和 `Binding` 两个概念，见 `docs/core-node-space-binding-architecture.md:24`。
架构中不引入 Chat Core、Agent Core、Env、Placement、Lease、Circuit、Capability 或远程数据放置 Ownership 模型，见 `docs/core-node-space-binding-architecture.md:34`。
业务副本同步只在双方都具备 storage.provide 且实际提供 Core 存储服务时运行，见 `docs/core-node-space-binding-architecture.md:187`。

### 不是中心化 Server

`Web Access` 不是自动加入 `Space` 的浏览器节点，也不是中心化 Agent Server，见 `README.md:99`。
打开 `Web Access` 页面不会自动让浏览器成为 `Space` 中的独立节点，见 `README.md:72`。
当前仓库还没有可以直接发布的完整 Server 产品，见 `README.md:103`。
`ESP32` Edge Node 不保存完整业务副本，见 `README.md:102`。
当前以个人设备空间为主要场景，尚未验证数千节点调度，也不以企业组织治理为产品目标，见 `README.md:148`。

### 不是全平台相同

单节点 Agent 的能力取决于平台 `Host`、模型 Provider 和本地配置，见 `README.md:30`。
单节点 Agent 的能力并不在所有平台完全相同，见 `README.md:39`。
架构文档中标注为目标、计划或演进方向的内容不代表所有平台已经实现，见 `README.md:246`。

### 配对不等于加入

配对完成后不会自动加入设备空间，见 `docs/core-node-space-binding-architecture.md:93`。
退出设备空间只重写本机成员记录，保留完整业务数据和直接配对记录，并创建新的单设备空间，见 `docs/core-node-space-binding-architecture.md:111`。
身份不进入设备空间同步，也不通过 Link 传播，见 `docs/core-node-space-binding-architecture.md:17`。
下列数据保持节点本地，不进入 `Space` 持久化同步：`CoreNode` 身份私钥、两两配对密钥和 session、`HostManager` 平台状态、本机监听地址、应用界面缩放、本机平台能力和临时交互句柄，见 `docs/core-node-space-binding-architecture.md:258`。

## 关键符号

- `CoreNode` — 运行 Core 的应用实例，见 `README.md:18`
- `CoreNode` 只有一套 `OperitApplication` + `LocalCoreProxy` + `HostManager`，见 `docs/core-node-space-binding-architecture.md:51`
- `Space` — 节点成员、路由和持久化同步的范围，见 `docs/core-node-space-binding-architecture.md:28`
- `Binding` — 一个 key 的下一次路由执行由哪个 `CoreNode` 完成，见 `docs/core-node-space-binding-architecture.md:141`
- `chatId` — 聊天路由直接使用现有 `chatId` 作为 key，见 `docs/core-node-space-binding-architecture.md:146`
- `generation` — 每次比较写入成功后 `generation` 单调递增，见 `docs/core-node-space-binding-architecture.md:171`
- `RoutedLink` — 转发时在现有 Link 消息外加的一层，见 `docs/core-node-space-binding-architecture.md:289`
- 外层不携带 `chatId`、`Binding`、`envId`、文件路径或 `Host` 配置，见 `docs/core-node-space-binding-architecture.md:297`
- `list_core_nodes` — 只读取本机已经同步的 `Space` 成员视图，见 `docs/core-node-space-binding-architecture.md:159`
- `switch_core` — 在调用时按同一份路由视图校验目标，见 `docs/core-node-space-binding-architecture.md:164`
- `requiredClock` — 持久化同步屏障，见 `docs/core-node-space-binding-architecture.md:407`
- `Host` — 节点本地能力的来源，见 `README.md:18`

## 调用链

切换 `CoreNode` 发生在工具调用已经完成、工具结果已经持久化、下一轮模型请求尚未发起的边界，见 `docs/core-node-space-binding-architecture.md:386`。完整流程：

1. node-A 的模型产生 `switch_core(node-D)`，见 `docs/core-node-space-binding-architecture.md:395`
2. node-A 验证 node-D 是可达的 Space 成员，见 `docs/core-node-space-binding-architecture.md:396`
3. node-A 在一个事务内持久化 assistant 工具调用、工具结果、chat metadata 和同步操作，见 `docs/core-node-space-binding-architecture.md:397`
4. 响应业务向 Router 返回只包含目标和不透明 payload 的 route transition，见 `docs/core-node-space-binding-architecture.md:398`
5. Router 比较写入 Binding(chat-1) = node-D，得到新的 generation 和 operation，见 `docs/core-node-space-binding-architecture.md:399`
6. Router 把 Binding record 和 operation 放入 Link route context，把不透明 transition 作为业务参数发送到 node-D，见 `docs/core-node-space-binding-architecture.md:400`
7. node-D 的 Router 在调用业务恢复方法前应用并校验 Binding operation，但不提前推进持久化同步 clock，见 `docs/core-node-space-binding-architecture.md:401`
8. node-D 的响应业务只接收 Link 定义的 route key/generation，等待 `requiredClock`，见 `docs/core-node-space-binding-architecture.md:402`
9. node-D 加载已同步 assistant 消息并使用 `switch_core` 的工具结果发起下一轮模型请求，见 `docs/core-node-space-binding-architecture.md:403`
10. node-D 的输出事件继续写入原来的逻辑响应流，见 `docs/core-node-space-binding-architecture.md:404`

## 来源

- README.md
- README-zh.md
- docs/core-node-space-binding-architecture.md
