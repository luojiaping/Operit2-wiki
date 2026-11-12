---
title: Edge 契约 crate
module: edge
platforms: [all]
sources: 4
date: 2026-11-11
---

## 概述

- `operit-edge-contract` 是 Edge Services 的共享地址契约 crate。`edge/sdk/contract/README.md:3`
- 它包含稳定的 Edge 对象与属性标识符。`edge/sdk/contract/src/lib.rs:7`
- 它还导出可序列化的数据契约。`edge/sdk/contract/src/lib.rs:26`
- 它不实现 Host capabilities。`edge/sdk/contract/README.md:6`
- 它不实现 Link dispatch。`edge/sdk/contract/README.md:6`
- 它不实现 transport carriers。`edge/sdk/contract/README.md:6`
- 它不实现 app behavior。`edge/sdk/contract/README.md:6`
- Edge Node 与类型化的 Edge Proxy 都可以依赖它，且两者之间不因此产生依赖。`edge/sdk/contract/README.md:7`

## AI 速览

- `EDGE_DEVICE_IO_OBJECT_ID` — Edge 设备 I/O 服务的 Link 目标标识，值为 "edge.deviceIo"。`edge/sdk/contract/src/lib.rs:7`
- `EDGE_DEVICE_IO_STATE_PROPERTY` — 数字输出状态 watch 的 Link 属性名，值为 "digitalOutputState"。`edge/sdk/contract/src/lib.rs:10`
- `EDGE_ROBOT_FACE_OBJECT_ID` — Edge 机器人表情服务的 Link 目标标识，值为 "edge.robotFace"。`edge/sdk/contract/src/lib.rs:13`
- `EDGE_ROBOT_FACE_STATE_PROPERTY` — 机器人表情 watch 的 Link 属性名，值为 "robotFaceState"。`edge/sdk/contract/src/lib.rs:16`
- `EDGE_SCREEN_OBJECT_ID` — 通用轻量显示服务的 Link 目标标识，值为 "edge.screen"。`edge/sdk/contract/src/lib.rs:19`
- `EDGE_SCREEN_STATE_PROPERTY` — 为未来显示状态 watch 保留的 Link 属性名，值为 "screenState"。`edge/sdk/contract/src/lib.rs:22`
- `EdgeScreenSnapshot` — 一份完整的显示快照，通过标准 Link 值传输。`edge/sdk/contract/src/lib.rs:26`
- `EdgeScreenInputRequest` — Edge 显示服务接受的通用输入事件。`edge/sdk/contract/src/lib.rs:35`
- `EdgeScreenInputState` — 报告显示输入事件是否被 Edge 服务接受。`edge/sdk/contract/src/lib.rs:45`
- `ChatDisplayWindow` — 有界的显示窗口，业务消息与工具留在所属 Core。`edge/sdk/contract/src/chat_display.rs:6`
- `ChatDisplayMessage` — 纯展示文本，工具名由 Core 渲染为普通文本。`edge/sdk/contract/src/chat_display.rs:22`
- `ChatDisplayEvent` — 展示编辑与错误事件，不能表示调用、参数、结果或工具状态。`edge/sdk/contract/src/chat_display.rs:32`
- `ImagePreviewChunk` — 有界、无需解码器的图片预览分块。`edge/sdk/contract/src/image_preview.rs:11`
- 主入口：lib.rs 声明两个公开子模块 `image_preview` 与 `chat_display`。`edge/sdk/contract/src/lib.rs:3`
- 数据流向一句话：Core 投影生成 ChatDisplayWindow、EdgeScreenSnapshot 与 ImagePreviewChunk，交给受限显示客户端。`edge/sdk/contract/src/chat_display.rs:1`

## 核心机制

### 标识符与序列化数据契约，不含实现

- 本 crate 包含稳定的 Edge 对象与属性标识符。`edge/sdk/contract/src/lib.rs:7`
- 它还导出可序列化的数据契约。`edge/sdk/contract/src/lib.rs:26`
- 它不实现 Host 能力、Link 分发、传输载体或应用行为。`edge/sdk/contract/README.md:6`
- Edge Node 与类型化的 Edge Proxy 各自依赖它时，两者之间不产生依赖。`edge/sdk/contract/README.md:7`
- 相关实现页：[[edge-sdk-node|Edge 节点 crate]]、[[edge-sdk-proxy|Edge 代理 crate]]。

### 三个命名空间标识

- 设备 I/O、机器人表情、通用显示各有一对常量：对象标识与状态属性名。`edge/sdk/contract/src/lib.rs:7`
- `EDGE_DEVICE_IO_OBJECT_ID` 的值是 "edge.deviceIo"。`edge/sdk/contract/src/lib.rs:7`
- `EDGE_DEVICE_IO_STATE_PROPERTY` 的值是 "digitalOutputState"，用于数字输出状态 watch。`edge/sdk/contract/src/lib.rs:10`
- `EDGE_ROBOT_FACE_OBJECT_ID` 的值是 "edge.robotFace"。`edge/sdk/contract/src/lib.rs:13`
- `EDGE_ROBOT_FACE_STATE_PROPERTY` 的值是 "robotFaceState"，用于机器人表情 watch。`edge/sdk/contract/src/lib.rs:16`
- `EDGE_SCREEN_OBJECT_ID` 的值是 "edge.screen"。`edge/sdk/contract/src/lib.rs:19`
- `EDGE_SCREEN_STATE_PROPERTY` 的值是 "screenState"，为未来显示状态 watch 保留。`edge/sdk/contract/src/lib.rs:22`

### 聊天展示：只投影，不搬业务

- chat_display 模块是 Core 投影与受限显示共享的展示契约。`edge/sdk/contract/src/chat_display.rs:1`
- `ChatDisplayWindow` 是有界的显示窗口，业务消息与工具留在所属 Core。`edge/sdk/contract/src/chat_display.rs:6`
- `ChatDisplayCursor` 是一条带时间戳消息的投影显示文本内的 UTF-8 字节偏移。`edge/sdk/contract/src/chat_display.rs:14`
- `ChatDisplayMessage` 的 `contentStream` 类型是 `Option<operit_link::CoreStream<ChatDisplayEvent>>`。`edge/sdk/contract/src/chat_display.rs:26`
- `ChatDisplayEvent` 使用 serde 的 tag = "type"、rename_all = "camelCase"、`deny_unknown_fields`。`edge/sdk/contract/src/chat_display.rs:31`

### 图片预览：有界分块，先校验后分配

- image_preview 模块为受限 Link 客户端提供有界、无需解码器的图片预览。`edge/sdk/contract/src/image_preview.rs:1`
- `PREVIEW_WIDTH` 为 128。`edge/sdk/contract/src/image_preview.rs:5`
- `PREVIEW_HEIGHT` 为 96。`edge/sdk/contract/src/image_preview.rs:6`
- `PREVIEW_CHUNK_BYTES` 为 1024。`edge/sdk/contract/src/image_preview.rs:7`
- `PREVIEW_MAX_BYTES` 为 `PREVIEW_WIDTH * PREVIEW_HEIGHT * 2`。`edge/sdk/contract/src/image_preview.rs:8`
- ImagePreviewChunk 的 `from_value` 在 Edge 上分配前先校验，拒绝任意远端尺寸。`edge/sdk/contract/src/image_preview.rs:30`
- `from_value` 拒绝 format 不是 "rgb565le" 的值，错误为 "Unsupported preview format"。`edge/sdk/contract/src/image_preview.rs:32`
- from_value 拒绝 `width` 为 0、`height` 为 0、`width` 超过 `PREVIEW_WIDTH` 或 `height` 超过 `PREVIEW_HEIGHT` 的分块。`edge/sdk/contract/src/image_preview.rs:46`
- from_value 拒绝空 `bytes`、`bytes` 长度超过 `PREVIEW_CHUNK_BYTES`、`offset` 为奇数或 `bytes` 长度为奇数的分块。`edge/sdk/contract/src/image_preview.rs:47`
- from_value 拒绝 `offset` 大于等于 `width * height * 2`，或 `bytes` 超出 `width * height * 2 - offset` 的分块。`edge/sdk/contract/src/image_preview.rs:48`
- 超出预览上限时 from_value 返回错误 "Image chunk exceeds preview limits"。`edge/sdk/contract/src/image_preview.rs:49`

## 关键符号

- `EDGE_DEVICE_IO_OBJECT_ID` — "edge.deviceIo"，Edge 设备 I/O 服务命名空间的 Link 目标。`edge/sdk/contract/src/lib.rs:7`
- `EDGE_DEVICE_IO_STATE_PROPERTY` — "digitalOutputState"，数字输出状态 watch 的 Link 属性名。`edge/sdk/contract/src/lib.rs:10`
- `EDGE_ROBOT_FACE_OBJECT_ID` — "edge.robotFace"，Edge 机器人表情服务命名空间的 Link 目标。`edge/sdk/contract/src/lib.rs:13`
- `EDGE_ROBOT_FACE_STATE_PROPERTY` — "robotFaceState"，机器人表情 watch 的 Link 属性名。`edge/sdk/contract/src/lib.rs:16`
- `EDGE_SCREEN_OBJECT_ID` — "edge.screen"，通用轻量显示服务的 Link 目标。`edge/sdk/contract/src/lib.rs:19`
- `EDGE_SCREEN_STATE_PROPERTY` — "screenState"，为未来显示状态 watch 保留的 Link 属性名。`edge/sdk/contract/src/lib.rs:22`
- `EdgeScreenSnapshot` — 完整显示快照，字段为 `width`、`height`、`format`、`pixels`，派生 `Serialize` 与 `Deserialize`。`edge/sdk/contract/src/lib.rs:26`
- `EdgeScreenInputRequest` — 通用输入事件，字段为 `action`、`x`、`y`、`endX`、`endY`，派生 `Serialize` 与 `Deserialize`。`edge/sdk/contract/src/lib.rs:35`
- `EdgeScreenInputRequest` 的 `endX` 与 `endY` 类型是 `Option<u16>`。`edge/sdk/contract/src/lib.rs:39`
- `EdgeScreenInputState` — 输入事件接受报告，字段为 `accepted` 与 `action`，派生 `Serialize` 与 `Deserialize`。`edge/sdk/contract/src/lib.rs:45`
- `ChatDisplayWindow` — 有界显示窗口，字段为 `messages`、`older`、`error`。`edge/sdk/contract/src/chat_display.rs:6`
- `ChatDisplayCursor` — UTF-8 字节偏移，字段为 `timestamp` 与 `offset`。`edge/sdk/contract/src/chat_display.rs:14`
- `ChatDisplayMessage` — 纯展示文本，字段为 `sender`、`timestamp`、`text`、`contentStream`。`edge/sdk/contract/src/chat_display.rs:22`
- `ChatDisplayEvent` — 枚举，变体为 `Chunk`、`Replace`、`Error`。`edge/sdk/contract/src/chat_display.rs:32`
- `PREVIEW_WIDTH` — 128。`edge/sdk/contract/src/image_preview.rs:5`
- `PREVIEW_HEIGHT` — 96。`edge/sdk/contract/src/image_preview.rs:6`
- `PREVIEW_CHUNK_BYTES` — 1024。`edge/sdk/contract/src/image_preview.rs:7`
- `PREVIEW_MAX_BYTES` — `PREVIEW_WIDTH * PREVIEW_HEIGHT * 2`。`edge/sdk/contract/src/image_preview.rs:8`
- `ImagePreviewChunk` — 预览分块，字段为 `width`、`height`、`offset`、`bytes`。`edge/sdk/contract/src/image_preview.rs:11`
- `ImagePreviewChunk` 的 `into_value` — 把分块编码为 `CoreValue::Map`，format 字段为 "rgb565le"。`edge/sdk/contract/src/image_preview.rs:19`
- ImagePreviewChunk 的 `from_value` — 从 `CoreValue` 解析分块并做边界校验。`edge/sdk/contract/src/image_preview.rs:30`

## 调用链

1. Core 投影生成 `ChatDisplayWindow`，业务消息与工具留在所属 Core。`edge/sdk/contract/src/chat_display.rs:6`
2. `ChatDisplayMessage` 经 `contentStream` 以 `ChatDisplayEvent` 流式输出 Chunk、Replace 或 Error。`edge/sdk/contract/src/chat_display.rs:26`
3. 显示服务以 `EdgeScreenSnapshot` 传输一份完整快照，字段为 `width`、`height`、`format`、`pixels`。`edge/sdk/contract/src/lib.rs:26`
4. 显示输入以 EdgeScreenInputRequest 提交，`EdgeScreenInputState` 报告是否被接受。`edge/sdk/contract/src/lib.rs:45`
5. 图片预览以 `ImagePreviewChunk` 分块传输，`into_value` 编码为 `CoreValue::Map`，format 为 "rgb565le"。`edge/sdk/contract/src/image_preview.rs:19`
6. 接收端用 ImagePreviewChunk 的 from_value 先校验边界再分配，超限返回错误 "Image chunk exceeds preview limits"。`edge/sdk/contract/src/image_preview.rs:49`

## 来源

- `edge/sdk/contract/README.md`
- `edge/sdk/contract/src/lib.rs`
- `edge/sdk/contract/src/chat_display.rs`
- `edge/sdk/contract/src/image_preview.rs`
- 本页 4 个 seed 文件已全部读完（共 161 行，与大纲 est_lines: 161 一致），源码基线为 AAswordman/Operit2 @ 364d1d594。
- 本页的否定性断言（不实现 Host 能力、Link 分发、传输载体、应用行为）直接引自 README 原文，不是全仓 grep 的零命中结论。`edge/sdk/contract/README.md:6`
- README 第 5 行写 crate“只含标识符”，与 lib.rs 当前导出的可序列化数据结构不符；本页范围按 lib.rs 实际导出写。`edge/sdk/contract/src/lib.rs:26`
- 模块内测试 `bounds_are_checked_before_allocation` 覆盖分块边界用例。`edge/sdk/contract/src/image_preview.rs:59`
- 四份 seed 文件中无平台分支表述，`platforms: [all]` 指本 crate 本身不区分 Host。
