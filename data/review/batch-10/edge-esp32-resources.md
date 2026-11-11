---
title: ESP32 资源预算与内存实测
module: edge
platforms: [windows]
sources: 1
date: 2026-11-11
---

## 概述

- 本页记录 2026-10-27 一份 ESP32 模拟器 Rust 堆分配实测报告的数字与测量条件。`edge/docs/esp32-memory-profile-2026-10-27.md:1`
- 报告按真实分配/释放记录给出字节数，分项统计对应同一次总堆峰值。`edge/docs/esp32-memory-profile-2026-10-27.md:3`
- 模拟器 Rust 堆固定 262,144 字节，分配器仍使用原来的 `linked_list_allocator`。`edge/docs/esp32-memory-profile-2026-10-27.md:8`
- 诊断运行临时使用 64 KiB 的主/异步/阻塞栈。`edge/docs/esp32-memory-profile-2026-10-27.md:12`
- 严格预算是主栈 16 KiB、异步栈 24 KiB、阻塞栈 20 KiB。`edge/docs/esp32-memory-profile-2026-10-27.md:55`
- 本页全部数字来自该份文档的记载，是 Windows 模拟器上的测量结果，不是真机整板 RAM 的测量结果。`edge/docs/esp32-memory-profile-2026-10-27.md:13`

## AI 速览

- `linked_list_allocator` — 模拟器 Rust 堆使用的分配器。`edge/docs/esp32-memory-profile-2026-10-27.md:8`
- `simulator-space.test.mjs` — 测量运行的完整集成场景。`edge/docs/esp32-memory-profile-2026-10-27.md:7`
- `heap.used()` — 每次分配记录的实际堆增量。`edge/docs/esp32-memory-profile-2026-10-27.md:8`
- `edge_chat::projectMessages` — 聊天消息展示行的直接分配点。`edge/docs/esp32-memory-profile-2026-10-27.md:46`
- `edge_chat::pluginsAction` — 插件列表处理闭包的直接分配点。`edge/docs/esp32-memory-profile-2026-10-27.md:47`
- `edge_chat::pluginsSnapshot` — 插件界面快照的直接分配点。`edge/docs/esp32-memory-profile-2026-10-27.md:48`
- `edge_chat::snapshot` — 聊天界面快照的直接分配点。`edge/docs/esp32-memory-profile-2026-10-27.md:49`
- `EncodedMessage<T>` — 清理后队列统一保存的编码消息类型。`edge/docs/esp32-memory-profile-2026-10-27.md:83`
- `SimulatorState` — 清理后类型化的状态响应。`edge/docs/esp32-memory-profile-2026-10-27.md:86`
- `assistance2-analyze-heap.py` — 离线解析及核对原始分配数据的程序。`edge/docs/esp32-memory-profile-2026-10-27.md:65`
- 主入口：测量运行完整 `simulator-space.test.mjs`，覆盖配对审批、聊天、插件调用、断线重连、90 行历史分页、取消及进程重启。`edge/docs/esp32-memory-profile-2026-10-27.md:7`
- 数据流向：同一时刻峰值分项表与分配器总账核对。`edge/docs/esp32-memory-profile-2026-10-27.md:3`

## 核心机制

### 测量条件

- 测量运行完整 `simulator-space.test.mjs`，覆盖配对审批、聊天、插件调用、断线重连、90 行历史分页、取消及进程重启。`edge/docs/esp32-memory-profile-2026-10-27.md:7`
- 模拟器 Rust 堆固定 262,144 字节，分配器仍使用原来的 `linked_list_allocator`。`edge/docs/esp32-memory-profile-2026-10-27.md:8`
- 每次分配记录请求大小、实际 `heap.used()` 增量、指针及调用栈，释放时撤销原始分配。`edge/docs/esp32-memory-profile-2026-10-27.md:8`
- 总占用刷新峰值时复制当时仍存活的分配计数，表中的峰值是同一时刻的占用，未累加各模块在不同时刻的最大值。`edge/docs/esp32-memory-profile-2026-10-27.md:9`
- 调用栈地址使用本轮匹配的 EXE/PDB 离线解析，按分配点向上的第一个项目源码帧分类。`edge/docs/esp32-memory-profile-2026-10-27.md:10`
- 分类结果表示直接分配来源，跨模块传递后的对象所有权需要另行分析。`edge/docs/esp32-memory-profile-2026-10-27.md:10`
- 诊断表位于独立静态区，写文件直接调用系统 API，未从设备堆分配统计元数据。`edge/docs/esp32-memory-profile-2026-10-27.md:11`
- 统计区、诊断工具自身和线程栈均不计入分项表。`edge/docs/esp32-memory-profile-2026-10-27.md:11`
- Windows 调用栈采样会增加执行栈消耗，诊断运行临时使用 64 KiB 的主/异步/阻塞栈。`edge/docs/esp32-memory-profile-2026-10-27.md:12`
- 本轮启用 release 行号调试信息，优化级别仍为 3。`edge/docs/esp32-memory-profile-2026-10-27.md:13`
- 测量结果属于 Windows 模拟器的 Rust 堆，不能直接当作真机整板 RAM。`edge/docs/esp32-memory-profile-2026-10-27.md:13`

### 同时峰值分项（252,208 字节）

- Peer/节点通信及连接状态峰值时 64,744 字节，占 25.67%，是占比最大的分项。`edge/docs/esp32-memory-profile-2026-10-27.md:19`
- 模拟器主循环与标准输入/输出峰值时 52,752 字节，占 20.92%，是占比第二的分项。`edge/docs/esp32-memory-profile-2026-10-27.md:20`
- 聊天、插件投影及订阅峰值时 38,664 字节，占 15.33%，是占比第三的分项。`edge/docs/esp32-memory-profile-2026-10-27.md:21`
- Host 调度器与 Tokio 运行时峰值时 29,600 字节，占 11.74%。`edge/docs/esp32-memory-profile-2026-10-27.md:22`
- Host 能力及引导描述元数据峰值时 23,784 字节，占 9.43%。`edge/docs/esp32-memory-profile-2026-10-27.md:23`
- 状态存储与打包缓存峰值时 19,480 字节，占 7.72%。`edge/docs/esp32-memory-profile-2026-10-27.md:24`
- Link 值、协议对象及编码峰值时 13,304 字节，占 5.28%。`edge/docs/esp32-memory-profile-2026-10-27.md:25`
- 其他界面、语音及设备服务峰值时 9,720 字节，占 3.85%。`edge/docs/esp32-memory-profile-2026-10-27.md:26`
- 其他 Host HTTP 与日志峰值时 160 字节，占 0.06%。`edge/docs/esp32-memory-profile-2026-10-27.md:27`
- 九个分项合计峰值 252,208 字节，占 100%。`edge/docs/esp32-memory-profile-2026-10-27.md:28`
- 九个分项最后一次导出时合计 195,416 字节。`edge/docs/esp32-memory-profile-2026-10-27.md:28`
- 最后一次导出时的占用表示该次快照的 live bytes，未将它认定为空闲常驻基线。`edge/docs/esp32-memory-profile-2026-10-27.md:30`
- 峰值时共有 1,527 笔仍存活的分配。`edge/docs/esp32-memory-profile-2026-10-27.md:32`
- 请求大小合计 245,007 字节，分配器实际计费合计 252,208 字节。`edge/docs/esp32-memory-profile-2026-10-27.md:32`
- 布局对齐及最小分配粒度增加 7,201 字节。`edge/docs/esp32-memory-profile-2026-10-27.md:32`
- 跟踪丢失记录数为 0，所有分项之和与实际总账一致，堆分配失败数为 0。`edge/docs/esp32-memory-profile-2026-10-27.md:32`

### 可追到具体机制的占用

- 具体机制拆解表与分项表存在包含关系，不应再次相加。`edge/docs/esp32-memory-profile-2026-10-27.md:36`
- Tokio MPSC 队列存储块峰值时 39,456 字节，共 9 个仍存活块，来自 Peer 通道、watch 及语音队列。`edge/docs/esp32-memory-profile-2026-10-27.md:40`
- 其中 LiveChannel 与复用通道的消息块峰值时 22,656 字节，即 4 × 5,664 字节，包含初始块及后续增长的块。`edge/docs/esp32-memory-profile-2026-10-27.md:41`
- 其中三个远程 watch 的事件块峰值时 11,616 字节，即 3 × 3,872 字节。`edge/docs/esp32-memory-profile-2026-10-27.md:42`
- 模拟器标准输入链路缓冲峰值时 28,672 字节，由 stdin 12,288 字节、BufReader 8,192 字节与 blocking read buffer 8,192 字节组成。`edge/docs/esp32-memory-profile-2026-10-27.md:43`
- 三个 Tokio 时间轮峰值时 18,720 字节，即 3 × 6,240 字节，两个来自 Host worker，一个来自模拟器主运行时。`edge/docs/esp32-memory-profile-2026-10-27.md:44`
- Host 能力及引导描述元数据峰值时 23,784 字节，描述构建及其克隆共 501 笔分配。`edge/docs/esp32-memory-profile-2026-10-27.md:45`
- 聊天消息展示行的直接分配峰值时 6,928 字节，分配点是 `edge_chat::projectMessages`。`edge/docs/esp32-memory-profile-2026-10-27.md:46`
- 插件列表处理闭包的直接分配峰值时 10,064 字节，分配点是 `edge_chat::pluginsAction` 对应列表投影。`edge/docs/esp32-memory-profile-2026-10-27.md:47`
- 插件界面快照的直接分配峰值时 6,032 字节，分配点是 `edge_chat::pluginsSnapshot`。`edge/docs/esp32-memory-profile-2026-10-27.md:48`
- 聊天界面快照的直接分配峰值时 5,992 字节，分配点是 `edge_chat::snapshot`。`edge/docs/esp32-memory-profile-2026-10-27.md:49`
- 6,928 字节只表示 `projectMessages` 分配点，不表示聊天相关对象的全部内存。`edge/docs/esp32-memory-profile-2026-10-27.md:51`
- MPSC 存储块的大小包含槽位空间，不能等同于待处理消息内容的字节数。`edge/docs/esp32-memory-profile-2026-10-27.md:51`

### 恢复严格预算后的复验

- 恢复主栈 16 KiB、异步栈 24 KiB、阻塞栈 20 KiB，移除本轮所有临时分配钩子，再次执行完整集成场景，结果为 1/1 PASS。`edge/docs/esp32-memory-profile-2026-10-27.md:55`
- 复验的堆历史峰值为 249,168 / 262,144 字节。`edge/docs/esp32-memory-profile-2026-10-27.md:55`
- 复验中所有采样的分配失败数为 0。`edge/docs/esp32-memory-profile-2026-10-27.md:55`
- 两轮的异步调度时序及测量条件有差异，分项表仅对应 252,208 字节诊断运行。`edge/docs/esp32-memory-profile-2026-10-27.md:55`

### 删除 Peer 中转链路与模拟器标准输入 IPC 后的验证

- 改动直接替换旧实现，保留标准 Link Call / Watch / Push 编码、认证、心跳、授权重检及事件顺序。`edge/docs/esp32-memory-profile-2026-10-27.md:80`
- 改动删除 `peer/live_channel.rs`，同一个连接读取任务完成解密后的心跳处理与响应关联，请求进入独立执行端。`edge/docs/esp32-memory-profile-2026-10-27.md:82`
- 改动删除原有 inbox、搬运读取任务及重复终止状态。`edge/docs/esp32-memory-profile-2026-10-27.md:82`
- 改动删除 `StoredMessage::Value / Encoded` 双表示及 `peer/compact_message.rs`，队列统一保存 `EncodedMessage<T>`。`edge/docs/esp32-memory-profile-2026-10-27.md:83`
- 改动通过共享的常量栈字段扫描器读取路由字段，执行时才展开业务负载。`edge/docs/esp32-memory-profile-2026-10-27.md:83`
- Call 请求与响应的队列交接保留原字节分配。`edge/docs/esp32-memory-profile-2026-10-27.md:83`
- Watch 队列保存编码后的事件，消费时解码，移交事件时不再克隆值树。`edge/docs/esp32-memory-profile-2026-10-27.md:84`
- 调度失败和连接结束共用同步终止步骤，释放等待者及队列。`edge/docs/esp32-memory-profile-2026-10-27.md:84`
- 编辑器与模拟器通过一个经过启动令牌认证的 loopback TCP 连接交换现有 JSON 命令。`edge/docs/esp32-memory-profile-2026-10-27.md:85`
- 改动删除 `stdin`、异步标准输入阻塞中转及其多层缓冲，接收端使用 1 KiB 帧缓冲。`edge/docs/esp32-memory-profile-2026-10-27.md:85`
- 改动后输出字节仅在一次发送期间持有。`edge/docs/esp32-memory-profile-2026-10-27.md:85`
- 状态响应改为类型化 `SimulatorState`，借用设备标识及发送回执，直接序列化。`edge/docs/esp32-memory-profile-2026-10-27.md:86`
- 改动删除仅为输出构造的外层动态 JSON 树。`edge/docs/esp32-memory-profile-2026-10-27.md:86`
- 网络启动、命令执行、响应序列化保持清晰的执行阶段，mDNS 首次初始化在独立的主栈生命周期中完成。`edge/docs/esp32-memory-profile-2026-10-27.md:87`
- 命令完成后才进入序列化，改动删除额外响应包装造成的约 3 KiB 轮询帧叠加。`edge/docs/esp32-memory-profile-2026-10-27.md:87`
- 改动后所有阶段仍使用原定主栈预算。`edge/docs/esp32-memory-profile-2026-10-27.md:87`
- 清理后场景峰值是各场景进程跨重启观测到的 Rust 堆历史峰值，不是同一次诊断运行的分项账目。`edge/docs/esp32-memory-profile-2026-10-27.md:89`
- 设备空间 UI、mDNS、凭据替换及重启恢复场景修改前已有峰值 218,144 字节，本次峰值 173,824 字节。`edge/docs/esp32-memory-profile-2026-10-27.md:93`
- 完整聊天、插件、重连及 90 行分页场景修改前已有峰值 248,848 字节，另一次 252,712 字节，本次峰值 187,600 字节。`edge/docs/esp32-memory-profile-2026-10-27.md:94`
- CLI 退出后的独立聊天与设备重启场景修改前已有峰值 235,888 字节，另一次 235,880 字节，本次峰值 192,240 字节。`edge/docs/esp32-memory-profile-2026-10-27.md:95`
- 清理后本次最高观测值为 192,240 / 262,144 字节，剩余 69,904 字节。`edge/docs/esp32-memory-profile-2026-10-27.md:97`
- 清理没有放宽 256 KiB 堆、16 KiB 主栈、24 KiB 异步栈或 20 KiB 阻塞栈。`edge/docs/esp32-memory-profile-2026-10-27.md:97`
- 清理后场景中的所有内存采样分配失败数均为 0。`edge/docs/esp32-memory-profile-2026-10-27.md:97`
- 清理后本次没有重新采样调用栈分项，不能据此给出新的 Peer / IPC 分项总量。`edge/docs/esp32-memory-profile-2026-10-27.md:97`
- 模拟器数值仍不等于真机整板 RAM。`edge/docs/esp32-memory-profile-2026-10-27.md:97`
- 验证中 Peer runtime 97 项测试、模拟器及共享固件模块 43 项测试通过。`edge/docs/esp32-memory-profile-2026-10-27.md:99`
- 验证中三项真实 Core / Edge 场景、编辑器启停场景及堆栈保护页探针共 5 项通过，编辑器 TypeScript 检查通过。`edge/docs/esp32-memory-profile-2026-10-27.md:99`
- Core 对端使用现有 `assistance2-core-main-merged.exe`，同时验证了标准线协议与现有版本的互通。`edge/docs/esp32-memory-profile-2026-10-27.md:99`

## 关键符号

- `linked_list_allocator` — 模拟器 Rust 堆使用的分配器。`edge/docs/esp32-memory-profile-2026-10-27.md:8`
- `simulator-space.test.mjs` — 测量运行的完整集成场景。`edge/docs/esp32-memory-profile-2026-10-27.md:7`
- `heap.used()` — 每次分配记录的实际堆增量。`edge/docs/esp32-memory-profile-2026-10-27.md:8`
- `edge_chat::projectMessages` — 聊天消息展示行的直接分配点。`edge/docs/esp32-memory-profile-2026-10-27.md:46`
- `edge_chat::pluginsAction` — 插件列表处理闭包的直接分配点。`edge/docs/esp32-memory-profile-2026-10-27.md:47`
- `edge_chat::pluginsSnapshot` — 插件界面快照的直接分配点。`edge/docs/esp32-memory-profile-2026-10-27.md:48`
- `edge_chat::snapshot` — 聊天界面快照的直接分配点。`edge/docs/esp32-memory-profile-2026-10-27.md:49`
- `EncodedMessage<T>` — 清理后队列统一保存的编码消息类型。`edge/docs/esp32-memory-profile-2026-10-27.md:83`
- `SimulatorState` — 清理后类型化的状态响应。`edge/docs/esp32-memory-profile-2026-10-27.md:86`
- `assistance2-analyze-heap.py` — 离线解析及核对原始分配数据的程序。`edge/docs/esp32-memory-profile-2026-10-27.md:65`
- `heap_profile.rs` — 本轮临时采样代码，未保留在运行代码中。`edge/docs/esp32-memory-profile-2026-10-27.md:66`
- `allocation-breakdown.json` — 原始证据中的完整分类文件。`edge/docs/esp32-memory-profile-2026-10-27.md:61`

## 调用链

1. 运行完整 `simulator-space.test.mjs`，覆盖配对审批、聊天、插件调用、断线重连、90 行历史分页、取消及进程重启。`edge/docs/esp32-memory-profile-2026-10-27.md:7`
2. 每次分配记录请求大小、实际 `heap.used()` 增量、指针及调用栈，释放时撤销原始分配。`edge/docs/esp32-memory-profile-2026-10-27.md:8`
3. 总占用刷新峰值时复制当时仍存活的分配计数，得到同一时刻的峰值分项表。`edge/docs/esp32-memory-profile-2026-10-27.md:9`
4. 调用栈地址使用本轮匹配的 EXE/PDB 离线解析，按分配点向上的第一个项目源码帧分类。`edge/docs/esp32-memory-profile-2026-10-27.md:10`
5. 恢复主栈 16 KiB、异步栈 24 KiB、阻塞栈 20 KiB，移除本轮所有临时分配钩子，再次执行完整集成场景复验。`edge/docs/esp32-memory-profile-2026-10-27.md:55`
6. 用 `.venv/Scripts/python.exe -X utf8 edge/boards/esp32/editor/generated/memory-profile-20261027/assistance2-analyze-heap.py` 重新核对原始分配和符号。`edge/docs/esp32-memory-profile-2026-10-27.md:72`

## 来源

- 本页 seed 文件：`edge/docs/esp32-memory-profile-2026-10-27.md`（107 行，基线 AAswordman/Operit2 @ 364d1d594，2026-11-11 全文读完）。
- 本页断言均来自该份 2026-10-27 测量报告文档的记载，未逐项在代码层验证；数字是文档记录的 Windows 模拟器 Rust 堆实测值，不是真机整板 RAM 的测量值。
- 原始证据文件保存在 `edge/boards/esp32/editor/generated/memory-profile-20261027/`，generated 目录被 Git 忽略，基线 checkout 内无该目录，本页未核对原始证据文件。`edge/docs/esp32-memory-profile-2026-10-27.md:59`
- 本页无全仓零命中类断言，无需写核验方法。
- Edge 总览见 [[edge-overview|Edge 总览与产品形态]]。
