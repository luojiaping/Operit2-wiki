---
title: 受限设备的空间与展示链路
module: edge
platforms: [all]
sources: 1
date: 2026-11-11
---

## 概述

- `ESP` 是共享节点架构中的对等节点，`Peer` 负责身份、配对和会话，`Space` 与 `Router` 负责成员、权限和路由，`Host` 提供网络、存储和调度。`edge/docs/core-entry-protocol.md:3`
- 设备可审批加入自己的空间，也可经正常配对与审批加入另一个节点的空间。`edge/docs/core-entry-protocol.md:4`
- 展示投影不改变 `Peer`、`Space`/`Router` 与 `Host` 之间的权威关系。`edge/docs/core-entry-protocol.md:5`
- 控制日志是成员与权限的权威。`edge/docs/core-entry-protocol.md:29`

## AI 速览

- `Peer` — 负责身份、配对和会话。`edge/docs/core-entry-protocol.md:3`
- `Space` 与 `Router` — 负责成员、权限和路由。`edge/docs/core-entry-protocol.md:3`
- `Host` — 提供网络、存储和调度。`edge/docs/core-entry-protocol.md:4`
- `ConsentProjection` — 列表、审核分配、状态轮询和诊断只读取的审批投影，保留请求身份、来源世代、成员 ID 与决策事实。`edge/docs/core-entry-protocol.md:30`
- `joinStatus(requestId)` — 首次提交后查询审批状态的入口。`edge/docs/core-entry-protocol.md:35`
- `operit-edge-contract` — 中立的生产依赖描述，设备不依赖 `Core` 的聊天、工具或 `proxy` 实现。`edge/docs/core-entry-protocol.md:52`
- `PackedRuntimeStorageHost` — 固件和模拟器共用的存储 Host。`edge/docs/core-entry-protocol.md:65`
- `OPERIT_SIM_DISCOVERY_IP` — 直接启动且启用发现时必须设置的环境变量。`edge/docs/core-entry-protocol.md:81`
- 请求沿 `Peer` 会话进入 `Router`，由当前空间及已接受的控制状态验证。`edge/docs/core-entry-protocol.md:9`
- 状态查询入口是 `joinStatus(requestId)`。`edge/docs/core-entry-protocol.md:35`
- 数据流向一句话（控制）：请求沿 Peer 会话进入 Router，由当前空间及已接受的控制状态验证。`edge/docs/core-entry-protocol.md:9`
- 数据流向一句话（审批）：列表、审核分配、状态轮询和诊断只读取 `ConsentProjection`。`edge/docs/core-entry-protocol.md:30`
- 数据流向一句话（聊天）：Core 从标准消息 `parts` 投影普通正文、图片占位文字和工具公开名称。`edge/docs/core-entry-protocol.md:54`

## 核心机制

### 控制状态的发布与校验

- 请求沿 `Peer` 会话进入 `Router`，由当前空间及已接受的控制状态验证。`edge/docs/core-entry-protocol.md:9`
- 控制状态按存储 `Host` 共享：新建查询句柄不重新装载和重放整份日志，也不复制整份权限集合。`edge/docs/core-entry-protocol.md:9`
- 控制投影发布版本和控制日志修改版本共同标识快照。`edge/docs/core-entry-protocol.md:12`
- 控制操作追加、导入、移除与日志重写使快照失效；重放完成后再次检查源版本，发布一致的已接受状态。`edge/docs/core-entry-protocol.md:12`
- 撤销必须被后续请求观察到。`edge/docs/core-entry-protocol.md:13`
- 审计和完整历史导出仍读取历史，它们不位于每次权限查询的路径中。`edge/docs/core-entry-protocol.md:14`
- 空间传输按明确的版本、节点身份和接收报文上限校验。`edge/docs/core-entry-protocol.md:16`
- `Core` 和 `Edge` 都提供 `manifest` 与逐条权限导出，申请方使用同一收集器验证不可变操作、完整清单和最终版本，再按共享权限规则导入。`edge/docs/core-entry-protocol.md:16`
- 加入路径只接受明确支持分页的目标，不再请求完整历史快照。`edge/docs/core-entry-protocol.md:18`
- 协议错误直接结束本次交换，不能把网络错误解释为新的权限。`edge/docs/core-entry-protocol.md:19`
- 出站建连和配对确认由 `Host` 异步任务执行，空间工作任务只等待结果。`edge/docs/core-entry-protocol.md:21`
- 配对确认前和凭据提交时分别校验原事务的当前授权。`edge/docs/core-entry-protocol.md:21`
- 身份、凭据和带版本的配对记录直接解码目标类型，不先构造完整 `Preferences` 树。`edge/docs/core-entry-protocol.md:22`
- 审批记录的 `envelope` 与 `source` 分阶段解码，再通过所有权句柄跨阶段传递。`edge/docs/core-entry-protocol.md:23`
- 申请准备阶段结束并释放来源、目标快照及其工作 `Future` 后，只携带 request ID 进入响应阶段，重新读取持久记录。`edge/docs/core-entry-protocol.md:23`
- `Peer` 按报文 `body.result` 的结构字段区分请求和响应，字段扫描使用固定栈，不先尝试错误类型的完整解码。`edge/docs/core-entry-protocol.md:24`

### 审批的证据与投影

- 控制日志是成员与权限的权威；申请保存的不可变来源快照是命令证据。`edge/docs/core-entry-protocol.md:29`
- 列表、审核分配、状态轮询和诊断只读取 `ConsentProjection`，保留请求身份、来源世代、成员 ID 与决策事实。`edge/docs/core-entry-protocol.md:30`
- 投影直接从编码记录读取所选字段，不先解码完整记录再丢弃证据。`edge/docs/core-entry-protocol.md:31`
- 命令输入的已认证路由使用固定栈扫描器定位，退出路由解析后再独立解码业务字段，避免通用值树再转换成命令。`edge/docs/core-entry-protocol.md:31`
- 审核收件箱只保存分配投影；实际领取审批时才从网关取得证据。`edge/docs/core-entry-protocol.md:32`
- 不存在的记录集合读取为空，不创建 `schema` 文件。`edge/docs/core-entry-protocol.md:33`
- 首次提交携带来源证据，网关确认后持久标记 `submitted`。`edge/docs/core-entry-protocol.md:35`
- 此后用 `joinStatus(requestId)` 查询状态；网络错误结束本次调用，不切换成重新提交。`edge/docs/core-entry-protocol.md:35`
- 状态回复只含请求事实和批准后的成员投影，不回传来源快照、`profile`、拓扑或控制历史。`edge/docs/core-entry-protocol.md:36`
- 网关不保存第二份 `accepted` 快照；批准回复按当前日志中的精确 `admission`、审批者、来源成员集合和当前权限生成。`edge/docs/core-entry-protocol.md:37`
- 申请方收到批准投影后，独立收集当前目标控制日志并验证 `admission`，再导入成员与展示资料。`edge/docs/core-entry-protocol.md:40`
- 投影不能代替授权。`edge/docs/core-entry-protocol.md:41`
- 审批按领取证据、生成决策和完成提交分阶段执行，证据在生成决策阶段结束时释放，完成阶段只持有决策结果。`edge/docs/core-entry-protocol.md:41`
- 无变化的状态轮询不重写原始申请。`edge/docs/core-entry-protocol.md:42`
- 控制导出同样区分 `manifest` 和操作页；快照头只读取版本和数量。`edge/docs/core-entry-protocol.md:44`
- 分页先完成不可变记录校验与版本关联，退出扫描后才解码选中的操作。`edge/docs/core-entry-protocol.md:45`
- `manifest` 的摘要覆盖原始完整字节，包含未知字段；重名操作仍需证明内容一致，游标和版本不匹配直接报错。`edge/docs/core-entry-protocol.md:45`
- 分页结束时校验成员、控制日志版本和退出事实，展示 `profile` 与拓扑取最后一次头部投影。`edge/docs/core-entry-protocol.md:47`
- 链路测量时间更新不改变授权，不能让正常测量更新打断权威导出。`edge/docs/core-entry-protocol.md:48`

### 聊天展示

- 生产依赖由中立的 `operit-edge-contract` 描述，契约内容见 [[edge-sdk-contract|Edge 契约 crate]]；设备不依赖 `Core` 的聊天、工具或 `proxy` 实现。`edge/docs/core-entry-protocol.md:52`
- `Core` 从标准消息 `parts` 投影普通正文、图片占位文字和工具公开名称。`edge/docs/core-entry-protocol.md:54`
- `Thinking`、`ToolResult`、工具参数、调用 ID 和工具执行状态不进入设备展示数据。`edge/docs/core-entry-protocol.md:54`
- 工具名称是普通文字，不是私有控制字符、`XML` 或设备端状态机。`edge/docs/core-entry-protocol.md:55`
- 窗口用时间戳和 UTF-8 字节游标分页，并按请求的字节数与行数限制。`edge/docs/core-entry-protocol.md:58`
- 订阅在 `Core` 侧处理源流、保存点和回滚，输出有界的追加或替换文字。`edge/docs/core-entry-protocol.md:58`
- 设备不保存源流修订历史。`edge/docs/core-entry-protocol.md:59`
- 流完成时校验未闭合的语义内容，历史 `Markdown` 也先由 `Core` 解释。`edge/docs/core-entry-protocol.md:59`
- 无效语义以窗口错误返回，不能直接展示其中的工具载荷。`edge/docs/core-entry-protocol.md:60`
- 另一设备产生的消息通过同一聊天窗口订阅进入展示；断线恢复重开当前窗口，权限仍由共享 `Router` 校验。`edge/docs/core-entry-protocol.md:60`

### 存储与执行

- 固件和模拟器共用 `PackedRuntimeStorageHost` 与记录/快照 codec。`edge/docs/core-entry-protocol.md:65`
- `NVS` 和桌面文件只是载体；压缩、记录大小、逻辑容量和事务发布顺序共用同一实现。`edge/docs/core-entry-protocol.md:65`
- 桌面原始文件 API 在独立载体栈上执行，压缩、解析和空间处理仍在设备任务栈内；载体不解释空间或聊天业务。`edge/docs/core-entry-protocol.md:66`
- 模拟器的 Rust 堆是固定 256 KiB `arena`，分配器不能向系统追加容量。`edge/docs/core-entry-protocol.md:69`
- 主任务栈 16 KiB，异步工作栈 24 KiB，阻塞工作栈 20 KiB，均由保护页限制；栈映射与 Rust `arena` 分开计量。`edge/docs/core-entry-protocol.md:69`
- 这些是模拟器预算，不是 ESP-IDF、Wi-Fi、TLS 或 C UI 的整板内存测量；C/Wasm 展示层报告自己的静态缓冲与栈。`edge/docs/core-entry-protocol.md:71`
- 编辑器每次状态查询只构造一份聊天展示快照，标题和空状态文字复用该快照。`edge/docs/core-entry-protocol.md:72`
- 错误对象保留代码、消息和调用位置，不在设备错误路径强制解析完整回溯。`edge/docs/core-entry-protocol.md:73`
- 桌面 `Tokio` 的事件批量受到限制，避免默认桌面驱动缓冲挤占设备预算。`edge/docs/core-entry-protocol.md:74`
- HTTP/WebSocket 网络任务在设备兼容配置中进入同一个 24 KiB `Host` 异步工作线程，不能额外创建四个桌面网络运行时，也不能绕过设备栈预算。`edge/docs/core-entry-protocol.md:75`
- HTTP 连接建立以同一 `executor` 中的独立任务执行，避免 `reqwest` 连接器与请求处理叠加调用栈。`edge/docs/core-entry-protocol.md:76`
- 请求取消或连接超时会丢弃并终止连接任务。`edge/docs/core-entry-protocol.md:78`
- `Peer` Call 的传输阶段也由 `Host` 异步任务承接，调用者取消即释放排队或进行中的工作，原始请求关联与权限校验保持完整。`edge/docs/core-entry-protocol.md:78`
- 模拟器发现服务绑定明确的本机接口；直接启动且启用发现时必须设置 `OPERIT_SIM_DISCOVERY_IP`。`edge/docs/core-entry-protocol.md:81`
- 编辑器使用与广告地址一致的接口。`edge/docs/core-entry-protocol.md:82`
- 桌面 `mDNS` 原始事件收集使用独立的 128 KiB `Host` 载体栈和一个无 I/O 驱动的服务工作线程，业务仍在设备预算内。`edge/docs/core-entry-protocol.md:83`
- 发现依赖 `polling` 2.8.0 的桌面事件批量固定为 16，来源归档经 SHA-256 校验后在隔离目录生成，所有 Rust 分配仍计入同一 `arena`。`edge/docs/core-entry-protocol.md:84`
- 运行 Cargo 前执行项目虚拟环境中的 `edge/boards/esp32/editor/prepare-simulator.py`；编辑器和内存检查会自动准备。`edge/docs/core-entry-protocol.md:85`
- 监听的自动模式优先复用已保存的端口；首次配置为端口 0 时由 `Host` 分配端口，并保存实际绑定地址。`edge/docs/core-entry-protocol.md:88`
- 复用端口被占用且尚未打开其他网络监听器时，自动模式以端口 0 重试一次；固定模式不更换端口，也不允许端口 0。`edge/docs/core-entry-protocol.md:89`
- 两种模式均不扫描端口。`edge/docs/core-entry-protocol.md:90`
- 当前 `PeerLink` 以字符串传递绑定错误，运行时通过已识别的地址占用消息或系统错误码判断是否允许这一次重试。`edge/docs/core-entry-protocol.md:90`
- 网络 `PeerListener` 必须提供实际地址；HTTP 与 WebSocket 共用同一监听端口。`edge/docs/core-entry-protocol.md:92`

### 验收

- 独立子进程检查堆分配成功/拒绝、各任务栈的正常执行/保护页越界。`edge/docs/core-entry-protocol.md:96`
- 真实 `CLI` 与模拟器检查配对、设备空间审批、请求与交互、其他设备更新、撤销和重启。`edge/docs/core-entry-protocol.md:96`
- 单元测试通过不能代替完整交互。`edge/docs/core-entry-protocol.md:97`
- 集成测试在每次读取设备状态时校验固定预算与零分配失败，并汇总跨重启堆峰值。`edge/docs/core-entry-protocol.md:98`
- 独立 HTTP 聊天还验证 `CLI` 退出及设备重启后的行为。`edge/docs/core-entry-protocol.md:99`
- 模拟器通过不能声明真机全部场景已通过。`edge/docs/core-entry-protocol.md:99`

## 关键符号

- `Peer` — 负责身份、配对和会话。`edge/docs/core-entry-protocol.md:3`
- `Space` — 与 Router 共同负责成员、权限和路由。`edge/docs/core-entry-protocol.md:3`
- `Router` — 与 Space 共同负责成员、权限和路由。`edge/docs/core-entry-protocol.md:3`
- `Host` — 提供网络、存储和调度。`edge/docs/core-entry-protocol.md:4`
- `ConsentProjection` — 审批投影，列表、审核分配、状态轮询和诊断只读取它。`edge/docs/core-entry-protocol.md:30`
- `joinStatus(requestId)` — 首次提交后查询审批状态的入口。`edge/docs/core-entry-protocol.md:35`
- `submitted` — 网关确认后对首次提交的持久标记。`edge/docs/core-entry-protocol.md:35`
- `body.result` — Peer 区分请求和响应的报文结构字段。`edge/docs/core-entry-protocol.md:24`
- `Preferences` — 身份、凭据和带版本的配对记录直接解码目标类型，不先构造的完整树。`edge/docs/core-entry-protocol.md:22`
- `envelope` 与 `source` — 审批记录分阶段解码的两个部分，再通过所有权句柄跨阶段传递。`edge/docs/core-entry-protocol.md:23`
- `Future` — 申请准备阶段的工作 Future，阶段结束时随来源、目标快照一同释放。`edge/docs/core-entry-protocol.md:23`
- `manifest` — 控制导出与空间传输提供的清单，摘要覆盖原始完整字节。`edge/docs/core-entry-protocol.md:44`
- `admission` — 批准回复按当前日志中的精确 admission 生成，申请方导入前独立验证它。`edge/docs/core-entry-protocol.md:38`
- `accepted` — 网关不保存第二份 accepted 快照。`edge/docs/core-entry-protocol.md:37`
- `operit-edge-contract` — 描述生产依赖的中立契约。`edge/docs/core-entry-protocol.md:52`
- `PackedRuntimeStorageHost` — 固件和模拟器共用的存储 Host。`edge/docs/core-entry-protocol.md:65`
- `OPERIT_SIM_DISCOVERY_IP` — 模拟器发现服务直接启动且启用发现时必须设置的环境变量。`edge/docs/core-entry-protocol.md:81`
- `PeerLink` — 以字符串传递绑定错误。`edge/docs/core-entry-protocol.md:90`
- `PeerListener` — 网络监听器必须提供实际地址。`edge/docs/core-entry-protocol.md:92`
- `mDNS` — 桌面原始事件收集。`edge/docs/core-entry-protocol.md:83`
- `polling` — 发现依赖的桌面事件批量来源。`edge/docs/core-entry-protocol.md:84`
- `reqwest` — HTTP 连接建立避免其连接器与请求处理叠加调用栈。`edge/docs/core-entry-protocol.md:76`
- `Tokio` — 桌面事件批量受到限制。`edge/docs/core-entry-protocol.md:74`
- `NVS` — 固件存储载体之一。`edge/docs/core-entry-protocol.md:65`
- `schema` — 不存在的记录集合读取为空，不创建 schema 文件。`edge/docs/core-entry-protocol.md:33`

## 调用链

1. 请求沿 `Peer` 会话进入 `Router`，由当前空间及已接受的控制状态验证。`edge/docs/core-entry-protocol.md:9`
2. 控制投影发布版本和控制日志修改版本共同标识快照；控制操作追加、导入、移除与日志重写使快照失效。`edge/docs/core-entry-protocol.md:12`
3. 首次提交携带来源证据，网关确认后持久标记 `submitted`。`edge/docs/core-entry-protocol.md:35`
4. 此后用 `joinStatus(requestId)` 查询状态；网络错误结束本次调用，不切换成重新提交。`edge/docs/core-entry-protocol.md:35`
5. 申请方收到批准投影后，独立收集当前目标控制日志并验证 `admission`，再导入成员与展示资料。`edge/docs/core-entry-protocol.md:40`
6. 投影不能代替授权；审批按领取证据、生成决策和完成提交分阶段执行。`edge/docs/core-entry-protocol.md:41`
7. `Core` 从标准消息 `parts` 投影普通正文、图片占位文字和工具公开名称；`Thinking`、`ToolResult`、工具参数、调用 ID 和工具执行状态不进入设备展示数据。`edge/docs/core-entry-protocol.md:54`
8. 窗口用时间戳和 UTF-8 字节游标分页；订阅在 `Core` 侧处理源流、保存点和回滚。`edge/docs/core-entry-protocol.md:58`
9. 另一设备产生的消息通过同一聊天窗口订阅进入展示；断线恢复重开当前窗口，权限仍由共享 `Router` 校验。`edge/docs/core-entry-protocol.md:60`
10. 固件和模拟器共用 `PackedRuntimeStorageHost` 与记录/快照 codec。`edge/docs/core-entry-protocol.md:65`
11. 模拟器发现服务绑定明确的本机接口；直接启动且启用发现时设置 `OPERIT_SIM_DISCOVERY_IP`。`edge/docs/core-entry-protocol.md:81`
12. 监听自动模式优先复用已保存的端口；复用端口被占用且尚未打开其他网络监听器时以端口 0 重试一次。`edge/docs/core-entry-protocol.md:88`
13. 集成测试在每次读取设备状态时校验固定预算与零分配失败，并汇总跨重启堆峰值。`edge/docs/core-entry-protocol.md:98`
14. 模拟器通过不能声明真机全部场景已通过。`edge/docs/core-entry-protocol.md:99`

## 来源

- `edge/docs/core-entry-protocol.md` — 本页唯一 seed 文件，全文 99 行（大纲 est_lines 99），已全文读完。
- 源码基线：AAswordman/Operit2 @ 364d1d594（2026-11-11）。
- 范围说明：本页 seed 是协议说明文档，正文断言转述该文档规定的协议行为；文档中的固定栈、固定 arena 预算等表述均按文档原文转述，不另作超出文档的 Rust 实现断言。
- 否定性结论核验方法：本页未作全仓零命中类断言；“设备不依赖 `Core` 的聊天、工具或 `proxy` 实现”等否定表述直接引自文档原文，不是 grep 零命中结论。`edge/docs/core-entry-protocol.md:52`
