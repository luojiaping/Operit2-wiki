---
title: Edge 在设备空间中的职责与边界
module: edge
platforms: [all]
sources: 1
date: 2026-11-11
---

## 概述

- `Edge` 是拥有自身原生业务的设备能力节点，固件负责硬件运行、本地交互及设备自身业务；整体产品形态见 [[edge-overview|Edge 总览与产品形态]]。`edge/docs/architecture.md:10`
- 硬件 `Edge` 节点与名为 `edge` 的权限角色分别表达实现和授权。`edge/docs/architecture.md:14`
- 屏幕、麦克风、`GPIO` 和模型请求都是设备可以选择实现的能力，不是成为 `Edge` 的必要条件。`edge/docs/architecture.md:11`
- 本页断言全部来自架构文档 edge/docs/architecture.md 的说法，未逐项在代码层验证。`edge/docs/architecture.md:3`

## AI 速览

- `Edge` — 拥有自身原生业务的设备能力节点。`edge/docs/architecture.md:10`
- `edge` — 内置权限角色，具有设备查看和 `runtime.execute`，没有默认 `network.relay` 或 `storage.provide`。`edge/docs/architecture.md:23`
- `EdgePeerRouter` — 接入共享 runtime，处理本机 `Target` 请求及规定的空间控制入口。`edge/docs/architecture.md:81`
- `operit-edge-contract` — 只共享地址和 `DTO`。`edge/docs/architecture.md:83`
- `operit-proxy-edge` — 封装类型化调用。`edge/docs/architecture.md:83`
- `coreVersion` — 当前 `ESP32` 的该值为 `None`，不能作为 `switch_core` 或聊天 `Binding` 的执行目标。`edge/docs/architecture.md:25`
- `chat` — 保存有效的该 preference 后进入设备独立模式。`edge/docs/architecture.md:94`
- 主入口（独立模式）：保存有效的 `chat` preference，设备通过 `Host` HTTP 直接请求配置的模型服务。`edge/docs/architecture.md:94`
- 主入口（远端 Core 模式）：未配置独立模式时，通过已准入的入口 `Core` 使用现有 `Binding` 路由。`edge/docs/architecture.md:105`
- 数据流向：完整聊天、工具参数、工具结果和执行状态留在 `Core`；投影通过中立契约交换普通展示文字。`edge/docs/architecture.md:57`

## 核心机制

### 节点形态与权限角色

- 硬件 `Edge` 节点的应用组成是原生设备应用、Edge Services、共享节点服务与 `Host`；完整 `CoreNode` 的应用组成是 `OperitApplication`、Core 路由、业务服务与 `Host`。`edge/docs/architecture.md:18`
- 硬件 `Edge` 节点的设备配置和自身状态由设备应用负责，按需持久保存；完整 `CoreNode` 的对应状态由对应业务 `owner` 负责。`edge/docs/architecture.md:19`
- 当前 `ESP32` 不提供 `Agent` / `ToolPkg` 执行；完整 `CoreNode` 的 `Agent` / `ToolPkg` 执行取决于实际服务和当前授权。`edge/docs/architecture.md:20`
- 当前 `ESP32` 不提供共享业务副本；完整 `CoreNode` 在双方具备存储授权且实际提供 `Core` 存储服务时交换共享业务副本。`edge/docs/architecture.md:21`
- 内置 `edge` 角色具有设备查看和 `runtime.execute`，没有默认 `network.relay` 或 `storage.provide`。`edge/docs/architecture.md:23`
- 权限本身不会安装 `Core`。`edge/docs/architecture.md:24`
- 执行目标同时要求 profile 声明 `Core` 且具有 `runtime.execute`。`edge/docs/architecture.md:24`
- 当前 `ESP32` 的 `coreVersion` 为 `None`，不能作为 `switch_core` 或聊天 `Binding` 的执行目标；完整 `Core` 也可以被授予 `edge` 角色。`edge/docs/architecture.md:25`

### 发现、配对与成员资格

- `Edge` 和 `Core` 复用共享 `Peer` runtime 的身份、验证码配对、加密会话和连接恢复，通过 `Host` 提供 `TCP`、串口等载体能力。`edge/docs/architecture.md:30`
- 固件不另建 `Edge` token 或第二套配对协议。`edge/docs/architecture.md:31`
- 配对证明两台设备之间的直接信任；加入 `Space` 另需申请和明确审批。`edge/docs/architecture.md:33`
- 配对成功不表示成员资格、执行授权或业务副本同步完成。`edge/docs/architecture.md:33`
- `Edge` 可以发起申请，也可以展示并处理共享服务分配给本机的审批。`edge/docs/architecture.md:34`
- 初始化、申请、取消和审批恢复使用共享服务的持久记录；`UI` 只保留有界展示状态，不生成第二份审批权威。`edge/docs/architecture.md:35`
- 配对 / 重新配对：成功确认后建立或替换凭据，不自动授予成员资格。`edge/docs/architecture.md:40`
- 本机解除配对：删除本机对应的直连授权，不等同于退出或移除成员。`edge/docs/architecture.md:41`
- 主动退出空间：保留直接配对，回到本机单设备空间。`edge/docs/architecture.md:42`
- 隔离设备：保留成员和配对，策略阻止连接与中转，解除隔离后才允许恢复连接。`edge/docs/architecture.md:43`
- 移除设备：按共享控制服务处理撤销与凭据遗忘，移除成员；再次接入走标准配对和加入流程。`edge/docs/architecture.md:44`
- 离线时的撤销、重新接纳和旧移除消息按共享控制日志及配对世代判断，固件不能根据一次网络错误自行清空身份或重写权限。`edge/docs/architecture.md:46`
- 旧管理员不可达时，设备可以经本地确认主动退出；未入空间的远端不能通过 `RPC` 代替用户重置设备。`edge/docs/architecture.md:47`

### 受限设备的实现边界

- `Edge` 和 `Core` 共享 `Peer`、`Space`、路由和权限语义；每个节点根据本地已接受的空间控制状态校验请求。`edge/docs/architecture.md:52`
- `Core` 不接管设备的授权，本机审批也由共享 `Space` 服务执行。`edge/docs/architecture.md:53`
- 设备只保留运行所需的节点状态、原生资源与有界展示窗口；完整聊天、工具参数、工具结果和执行状态留在 `Core`，投影通过中立契约交换普通展示文字。`edge/docs/architecture.md:56`

### 本地数据与配置交换

- `Edge` 可以保存身份、密钥、配对、必要的成员/权限/审批状态，以及设备原生配置和资源。`edge/docs/architecture.md:61`
- 不具备 `storage.provide` 不会禁止本地存储、设备运行或自身 preference 同步。`edge/docs/architecture.md:62`
- 设备 preference 按 `(spaceId, nodeId)` 隔离，通过同空间控制通道交换。`edge/docs/architecture.md:64`
- 每个 preference 键按逻辑版本和写入节点合并，删除保留标记，避免离线旧副本复活已删除配置。`edge/docs/architecture.md:64`
- 设备 preference 当前上限为 24 个键、6144 字节完整明文状态；删除标记也占用有界状态。`edge/docs/architecture.md:65`
- 设备 preference 本地加密保存，合并失败不得发布部分状态。`edge/docs/architecture.md:66`
- 设备 preference 交换重新检查当前成员、隔离、撤销及空间范围。`edge/docs/architecture.md:67`
- 设备配置交换不复制聊天数据库、附件、插件包或业务文件，不推进业务同步时钟。`edge/docs/architecture.md:69`
- 显示远端聊天所需的按需读取和有界 `RAM` 缓存也不构成业务副本。`edge/docs/architecture.md:70`
- `storage.provide` 与实际 `Core` 存储服务共同决定是否参与完整业务复制。`edge/docs/architecture.md:71`

### 原生服务与 Host 边界

- 设备应用注册自己的原生 `Call`、`Watch` / `Stream` 和 `Push` / `ReverseStream` 端点，并处理设备本地输入。`edge/docs/architecture.md:75`
- 宿主通过 `Tools.device(nodeId).transport` 或小型配置入口 `Edge.execute` / `Io.execute` 访问设备原生端点。`edge/docs/architecture.md:76`
- 能力、数据格式和动作由端点声明；无对应端点时返回明确错误。`edge/docs/architecture.md:77`
- 拥有通用通道不表示设备支持任何 `Core` 工具或任意宿主函数。`edge/docs/architecture.md:78`
- `Host` 实现平台 I/O、存储、HTTP、显示和调度；共享 `Peer` runtime 管理认证与连接。`edge/docs/architecture.md:80`
- `Edge` Services 和固件拥有设备行为；`EdgePeerRouter` 接入共享 runtime，处理本机 `Target` 请求及规定的空间控制入口，不承担完整 `Core` 的 `Binding` 分派。`edge/docs/architecture.md:81`
- `operit-edge-contract` 只共享地址和 `DTO`；`operit-proxy-edge` 封装类型化调用。`edge/docs/architecture.md:83`
- 固件不运行宿主 `ToolPkg`；配置 `ToolPkg` 负责编辑和保存，停止或卸载后不影响已经保存的设备行为。`edge/docs/architecture.md:84`
- 需要持续宿主计算时，使用单独的处理插件或已有 `Core` 服务。`edge/docs/architecture.md:85`
- 通道保留标准 `Link` 的顺序、完成、取消和错误语义；取消等待不代表撤销已提交的硬件动作。`edge/docs/architecture.md:87`
- 超时或断线后不得自动重放非幂等动作；文档要求不增加按传输类型分叉的业务协议。`edge/docs/architecture.md:88`

### ESP32 的两条聊天路径

- 保存有效的 `chat` preference 后，设备通过 `Host` HTTP 直接请求配置的模型服务，无需 `Core` 常驻或 `Binding`。`edge/docs/architecture.md:94`
- 其他成员掉线不清空同空间的本地对话；当前上下文仅在 `RAM` 中保留最多 8 条消息、6144 字节文本，单条最多 2048 字节。`edge/docs/architecture.md:95`
- 模型配置和上下文都受当前空间约束；切换空间后先退役旧上下文，再校验新配置。`edge/docs/architecture.md:98`
- 即使两个空间配置相同，或者新配置无效，也不沿用旧空间的会话。`edge/docs/architecture.md:99`
- 旧空间已提交的 `HTTP` 请求即使完成，其迟到结果也不能进入新会话。`edge/docs/architecture.md:99`
- 固件无法读取空间或配置时也会退役当前上下文并显示错误。`edge/docs/architecture.md:100`
- 重启保留配置并开始新的对话。`edge/docs/architecture.md:101`
- 未配置独立模式时，`Edge` 可通过已准入的入口 `Core` 使用现有 `Binding` 路由。`edge/docs/architecture.md:105`
- 远端 `Core` 模式下 `Core` 创建聊天、选择执行节点、保存历史和推进 `Agent`；`Edge` 只保存选择的聊天 ID、有界显示窗口和本次交互状态。`edge/docs/architecture.md:106`
- 订阅和发送需等待显式创建确认，不靠读写隐式创建 `Binding`。`edge/docs/architecture.md:107`
- 同空间短暂断线保留聊天选择，入口或认证会话变化后恢复订阅；换空间或显式退出、解除配对时清理旧查看状态。`edge/docs/architecture.md:109`
- 恢复显示不自动重放发送、新建聊天、插件测试或硬件动作。`edge/docs/architecture.md:110`
- 插件列表也在 `Core` 执行，`"edge": {"exclusive": true}` 只是展示分类。`edge/docs/architecture.md:111`

### 两条路径的切换

- 保存有效的 `chat` preference 后进入设备独立模式。`edge/docs/architecture.md:94`
- 未配置独立模式时走远端 `Core` 模式。`edge/docs/architecture.md:105`

## 关键符号

- `Edge` — 拥有自身原生业务的设备能力节点。`edge/docs/architecture.md:10`
- `edge` — 内置权限角色，具有设备查看和 `runtime.execute`。`edge/docs/architecture.md:23`
- `coreVersion` — 当前 `ESP32` 的该值为 `None`，不能作为 `switch_core` 或聊天 `Binding` 的执行目标。`edge/docs/architecture.md:25`
- `EdgePeerRouter` — 接入共享 runtime，处理本机 `Target` 请求及规定的空间控制入口。`edge/docs/architecture.md:81`
- `operit-edge-contract` — 只共享地址和 `DTO`。`edge/docs/architecture.md:83`
- `operit-proxy-edge` — 封装类型化调用。`edge/docs/architecture.md:83`
- `Tools.device(nodeId).transport` — 宿主访问设备原生端点的通道之一。`edge/docs/architecture.md:76`
- `Edge.execute` / `Io.execute` — 小型配置入口。`edge/docs/architecture.md:76`
- `chat` — 设备独立模式的模型配置 preference。`edge/docs/architecture.md:94`
- `storage.provide` — 与实际 `Core` 存储服务共同决定是否参与完整业务复制。`edge/docs/architecture.md:71`
- `Link` — 通道保留其顺序、完成、取消和错误语义。`edge/docs/architecture.md:87`

## 调用链

1. 设备与 `Core` 配对：复用共享 `Peer` runtime 的验证码配对建立直接信任，固件不另建 `Edge` token 或第二套配对协议。`edge/docs/architecture.md:30`
2. 加入 `Space`：配对后另需申请和明确审批，配对成功不自动授予成员资格。`edge/docs/architecture.md:33`
3. 成员操作：配对、解除配对、退出空间、隔离、移除五种操作按控制表分别影响直连授权与成员资格。`edge/docs/architecture.md:38`
4. 独立模式聊天：保存有效的 `chat` preference 后，设备通过 `Host` HTTP 直接请求配置的模型服务，上下文只在 `RAM` 中保留。`edge/docs/architecture.md:94`
5. 远端 `Core` 模式聊天：未配置独立模式时，通过已准入的入口 `Core` 使用现有 `Binding` 路由，`Core` 创建聊天并保存历史。`edge/docs/architecture.md:105`
6. 切换空间：先退役旧上下文，再校验新配置；即使配置相同或新配置无效，也不沿用旧空间的会话。`edge/docs/architecture.md:98`

## 来源

- 本页 seed 文件：edge/docs/architecture.md（128 行，基线 AAswordman/Operit2 @ 364d1d594，2026-11-11 全文读完）。
- 本页断言均来自该架构文档的说法，未逐项在代码层验证；`CoreNode`、`Binding` 和业务复制的细节由空间架构文档维护。`edge/docs/architecture.md:120`
- 命令、角色、成员操作及配置交换由网络控制文档维护。`edge/docs/architecture.md:121`
- 两条聊天路径的切换：文档用 `chat` preference 是否有效配置区分两条路径，未另行描述切换命令。`edge/docs/architecture.md:94`
- 本页无全仓零命中类断言，无需写核验方法。
