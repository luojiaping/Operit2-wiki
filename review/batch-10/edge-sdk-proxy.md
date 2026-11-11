---
title: Edge 代理 crate
module: edge
platforms: [all]
sources: 2
date: 2026-11-11
---

## 概述

- `operit-proxy-edge` 是 Edge Services 的类型化投影（Typed projection）。`edge/sdk/proxy/README.md:3`
- 本 crate 是面向资源受限构建的紧凑类型化代理子集。`edge/sdk/proxy/src/lib.rs:1`
- Proxy 在内部拥有 Link 请求构造与响应/事件解码。`edge/sdk/proxy/README.md:5`
- 调用方使用 `setDigitalOutput` 与 `watchDigitalOutput` 等类型化方法，不直接构造 `CoreCallRequest`、`CoreValue` 或 `CoreEvent`。`edge/sdk/proxy/README.md:6`
- 生产 crate 依赖共享 Edge contract、Host DTO 与 Link client traits，不依赖本地 Edge Node 实现。`edge/sdk/proxy/README.md:9`
- Proxy 打包不决定节点身份、授权或传输。`edge/sdk/proxy/src/lib.rs:2`
- 对象 id、属性名等共享常量来自 contract 层，见 [[edge-sdk-contract|Edge 契约 crate]]。`edge/sdk/proxy/src/lib.rs:10`

## AI 速览

- `EdgeProxy` — 类型化代理入口，持有一个 Core Link 客户端。`edge/sdk/proxy/src/lib.rs:20`
- `EdgeDeviceIoProxy` — 设备 I/O 子代理，处理数字输出读写与订阅。`edge/sdk/proxy/src/lib.rs:171`
- `EdgeRobotFaceProxy` — 机器人表情子代理，处理表情读写与订阅。`edge/sdk/proxy/src/lib.rs:240`
- `EdgeScreenProxy` — 显示子代理，处理屏幕快照与屏幕输入。`edge/sdk/proxy/src/lib.rs:245`
- `EdgeDeviceIoClient` — Edge 应用层消费的类型化设备操作 trait。`edge/sdk/proxy/src/lib.rs:59`
- `EdgeRobotFaceClient` — Edge 应用层消费的类型化机器人表情操作 trait。`edge/sdk/proxy/src/lib.rs:79`
- `EdgeScreenClient` — Edge 应用层消费的通用显示操作 trait。`edge/sdk/proxy/src/lib.rs:93`
- `EdgeStateStream` / `EdgeRobotFaceStateStream` — 类型化事件流，内部持有 `CoreEventStream`。`edge/sdk/proxy/src/lib.rs:344`
- `EdgeProxyError` — 跨代理边界的错误，只有 `code` 与 `message` 两个字段。`edge/sdk/proxy/src/lib.rs:375`
- `decodeResponse` / `decodeValue` — 内部解码函数，把 `CoreValue` 解码为类型化值。`edge/sdk/proxy/src/lib.rs:400`
- 主入口函数：EdgeProxy 的 `new`，接收一个 Core Link 客户端。`edge/sdk/proxy/src/lib.rs:26`
- 数据流向一句话：类型化调用 → 内部构造 CoreCallRequest / CoreWatchRequest → Link 往返 → `fromCoreValue` 解码为类型化值返回调用方。`edge/sdk/proxy/src/lib.rs:408`

## 核心机制

- 请求构造全部发生在 Proxy 内部，调用方只传类型化参数：`setDigitalOutput` 接收 `pin: u8` 与 `level: bool`，返回 `DeviceDigitalOutputState`。`edge/sdk/proxy/src/lib.rs:61`
- `setDigitalOutput` 内部用 `CoreCallRequest` 的 `new` 构造请求，调用 id 为 `edge-device-io-write`，方法名为 `setDigitalOutput`。`edge/sdk/proxy/src/lib.rs:187`
- 该请求以 `EDGE_DEVICE_IO_OBJECT_ID` 为调用对象。`edge/sdk/proxy/src/lib.rs:189`
- 参数装进 `CoreValue::Map`，`pin` 编码为 `CoreValue::Unsigned`，`level` 编码为 `CoreValue::Bool`。`edge/sdk/proxy/src/lib.rs:192`
- 响应经 `decodeResponse` 解码：setDigitalOutput 把 `response.result` 交给 `decodeResponse`。`edge/sdk/proxy/src/lib.rs:197`
- `getDigitalOutput` 用 `CoreCallRequest` 的 `new` 构造调用 id 为 `edge-device-io-read`、方法名为 `getDigitalOutput` 的请求。`edge/sdk/proxy/src/lib.rs:207`
- `getDigitalOutput` 的参数只含 `pin`，编码为 `CoreValue::Unsigned`。`edge/sdk/proxy/src/lib.rs:211`
- 无参数的读调用用 `CoreValue::emptyMap()` 作参数：`getScreenSnapshot` 的调用 id 为 `edge-screen-read`，方法名为 `getScreenSnapshot`。`edge/sdk/proxy/src/lib.rs:257`
- `getExpression` 的调用 id 为 `edge-robot-face-read`，方法名为 `getExpression`，参数同样为 `CoreValue::emptyMap()`。`edge/sdk/proxy/src/lib.rs:317`
- `sendScreenInput` 先用 `operit_link::toCoreValue` 把 `EdgeScreenInputRequest` 编码为参数，编码失败时 `EdgeProxyError` 的 `code` 为 `INVALID_ARGS`。`edge/sdk/proxy/src/lib.rs:272`
- `sendScreenInput` 再用 `CoreCallRequest` 的 `new` 构造调用 id 为 `edge-screen-input`、方法名为 `sendScreenInput` 的请求。`edge/sdk/proxy/src/lib.rs:278`
- `setExpression` 用 `CoreCallRequest` 的 `new` 构造调用 id 为 `edge-robot-face-write`、方法名为 `setExpression` 的请求。`edge/sdk/proxy/src/lib.rs:300`
- `setExpression` 把 `expression` 编码为 `CoreValue::String`。`edge/sdk/proxy/src/lib.rs:305`
- 订阅同样由 Proxy 内部构造：`watchDigitalOutput` 用 `CoreWatchRequest` 的 `new` 构造订阅 id 为 `edge-device-io-watch`、对象为 `EDGE_DEVICE_IO_OBJECT_ID`、属性为 `EDGE_DEVICE_IO_STATE_PROPERTY` 的请求。`edge/sdk/proxy/src/lib.rs:224`
- `watchExpression` 用 `CoreWatchRequest` 的 `new` 构造订阅 id 为 `edge-robot-face-watch`、对象为 `EDGE_ROBOT_FACE_OBJECT_ID`、属性为 `EDGE_ROBOT_FACE_STATE_PROPERTY`、参数为 `CoreValue::emptyMap()` 的请求。`edge/sdk/proxy/src/lib.rs:331`
- 订阅返回类型化流：watchDigitalOutput 返回 `EdgeStateStream` 包裹内部流。`edge/sdk/proxy/src/lib.rs:235`
- 事件解码发生在流的 `recv` 里：`EdgeStateStream` 的 `recv` 在流结束时返回 `Ok(None)`，收到事件时用 `decodeValue` 把 `event.value` 解码为 `DeviceDigitalOutputState`。`edge/sdk/proxy/src/lib.rs:350`
- `EdgeRobotFaceStateStream` 的 `recv` 用同样方式把 `event.value` 解码为 `RobotFaceState`。`edge/sdk/proxy/src/lib.rs:365`
- `decodeResponse` 先把 `CoreLinkError` 转为 `EdgeProxyError`，再把 `CoreValue` 交给 `decodeValue`。`edge/sdk/proxy/src/lib.rs:400`
- `decodeValue` 用 `fromCoreValue` 把 `CoreValue` 解码为类型化值，失败时 `EdgeProxyError` 的 `code` 为 `INVALID_RESPONSE`。`edge/sdk/proxy/src/lib.rs:408`
- 错误穿越代理边界时保持原样：`EdgeProxyError` 的 `From<CoreLinkError>` 实现把 `CoreLinkError` 的 `code` 与 `message` 原样搬运。`edge/sdk/proxy/src/lib.rs:389`
- `EdgeProxyError` 的 Display 格式为 `code` 加冒号加 `message`。`edge/sdk/proxy/src/lib.rs:382`
- 调用方不直接构造 CoreCallRequest / CoreValue / CoreEvent 的原因是 Proxy 已把构造与解码收进内部，调用方只接触类型化方法与类型化返回值，测试 `typedProxyCallsAndWatchesEdgeService` 验证类型化 Proxy 能在 API 不出现 Link 值的情况下调用与订阅 Edge Service。`edge/sdk/proxy/src/lib.rs:493`

## 关键符号

- `EdgeProxy` — 类型化代理入口，持有一个 Core Link 客户端，泛型参数为客户端类型 `C`。`edge/sdk/proxy/src/lib.rs:20`
- EdgeProxy 的 `new` — 接收一个 Core Link 客户端并创建类型化 Edge 代理。`edge/sdk/proxy/src/lib.rs:26`
- EdgeProxy 的 `deviceIo` — 返回 `EdgeDeviceIoProxy`。`edge/sdk/proxy/src/lib.rs:31`
- EdgeProxy 的 `robotFace` — 返回 `EdgeRobotFaceProxy`。`edge/sdk/proxy/src/lib.rs:38`
- EdgeProxy 的 `screen` — 返回 `EdgeScreenProxy`。`edge/sdk/proxy/src/lib.rs:45`
- EdgeProxy 的 `intoInner` — 在代理使用完成后返回底层 Link 客户端。`edge/sdk/proxy/src/lib.rs:52`
- `EdgeDeviceIoClient` — 定义 Edge 应用层消费的类型化设备操作。`edge/sdk/proxy/src/lib.rs:59`
- `EdgeRobotFaceClient` — 定义类型化机器人表情操作。`edge/sdk/proxy/src/lib.rs:79`
- `EdgeScreenClient` — 定义通用显示操作。`edge/sdk/proxy/src/lib.rs:93`
- EdgeDeviceIoClient 的 `watchDigitalOutput` — 接收 `pin: u8`，返回 `EdgeStateStream`。`edge/sdk/proxy/src/lib.rs:74`
- `EdgeRobotFaceClient` 的 `setExpression` — 接收 `expression: String`，返回 `RobotFaceState`。`edge/sdk/proxy/src/lib.rs:81`
- EdgeRobotFaceClient 的 `watchExpression` — 返回 `EdgeRobotFaceStateStream`。`edge/sdk/proxy/src/lib.rs:88`
- `EdgeScreenClient` 的 `getScreenSnapshot` — 返回 `EdgeScreenSnapshot`。`edge/sdk/proxy/src/lib.rs:94`
- `EdgeScreenClient` 的 `sendScreenInput` — 接收 `EdgeScreenInputRequest`，返回 `EdgeScreenInputState`。`edge/sdk/proxy/src/lib.rs:95`
- `CoreLinkSharedClient` — EdgeProxy 的 trait 实现对客户端泛型参数的要求。`edge/sdk/proxy/src/lib.rs:104`
- `EDGE_DEVICE_IO_OBJECT_ID` / `EDGE_DEVICE_IO_STATE_PROPERTY` / `EDGE_ROBOT_FACE_OBJECT_ID` / `EDGE_ROBOT_FACE_STATE_PROPERTY` / `EDGE_SCREEN_OBJECT_ID` — 从 `operit_edge_contract` 引入的共享常量。`edge/sdk/proxy/src/lib.rs:10`
- `EdgeStateStream` — 内部持有 `CoreEventStream` 的类型化数字输出状态流。`edge/sdk/proxy/src/lib.rs:344`
- `EdgeRobotFaceStateStream` — 内部持有 `CoreEventStream` 的类型化机器人表情状态流。`edge/sdk/proxy/src/lib.rs:359`
- `EdgeProxyError` — 只有 `code` 与 `message` 两个字段的代理边界错误。`edge/sdk/proxy/src/lib.rs:375`
- `decodeResponse` — 把一次 Link 调用结果解码为类型化值。`edge/sdk/proxy/src/lib.rs:400`
- `decodeValue` — 把一个 `CoreValue` 解码为类型化值。`edge/sdk/proxy/src/lib.rs:408`

## 调用链

1. 调用方用 EdgeProxy 的 `new` 创建代理，传入一个 Core Link 客户端。`edge/sdk/proxy/src/lib.rs:26`
2. 调用方调 `deviceIo` / robotFace / screen 拿到对应子代理。`edge/sdk/proxy/src/lib.rs:31`
3. 调用方调类型化方法，例如 setDigitalOutput(pin, level)。`edge/sdk/proxy/src/lib.rs:61`
4. EdgeProxy 的 trait 实现把调用转发给子代理的同名方法。`edge/sdk/proxy/src/lib.rs:112`
5. 子代理在内部用 `CoreCallRequest` 的 `new` 构造请求，经 `client` 的 `call` 发送。`edge/sdk/proxy/src/lib.rs:187`
6. 响应经 `decodeResponse` 与 `decodeValue` 解码为类型化值返回调用方。`edge/sdk/proxy/src/lib.rs:400`
7. 订阅调用方调 `watchDigitalOutput`，子代理在内部用 `CoreWatchRequest` 的 `new` 构造订阅请求，返回 `EdgeStateStream`。`edge/sdk/proxy/src/lib.rs:224`
8. 调用方反复调 `EdgeStateStream` 的 `recv`，每次收到事件即得一个解码后的 `DeviceDigitalOutputState`，流结束得 `Ok(None)`。`edge/sdk/proxy/src/lib.rs:350`
9. 调用方用完代理后调 `intoInner` 取回底层 Link 客户端。`edge/sdk/proxy/src/lib.rs:52`

## 来源

- `edge/sdk/proxy/README.md`（10 行）：crate 定位与调用方契约。
- `edge/sdk/proxy/src/lib.rs`（545 行）：`EdgeProxy`、三个子代理、三个 trait、两个类型化事件流、`EdgeProxyError` 与内部解码函数。
- 本页事实全部来自上述 2 个 seed 文件，基线为 `AAswordman/Operit2 @ 364d1d594`（2026-11-11）；本页未作全仓零命中类断言。
