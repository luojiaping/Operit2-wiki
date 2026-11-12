---
title: 无屏传感器产品
module: edge
platforms: [all]
sources: 2
date: 2026-11-11
---

## 概述

- 无屏传感器产品是不带显示屏的独立产品，演示 manufacturer SDK，不含 GPIO 服务、场景渲染器与完整 Core。`edge/boards/headless_sensor/README.md:3`
- 产品通过已认证的设备服务路由器暴露 `manufacturer.sensor/read` 与 `manufacturer.agent/run` 两个服务。`edge/boards/headless_sensor/README.md:5`
- 桌面演示传感器返回 23.5 C，替换 `Temperature::call` 即可接入真实 HAL。`edge/boards/headless_sensor/README.md:6`
- 离线后端演示完整的模型 → 工具 → 观测 → 回复循环。`edge/boards/headless_sensor/README.md:7`
- 本页只讲无屏产品，Edge 整体定位见 [[edge-overview|Edge 总览与产品形态]]。

## AI 速览

- `Temperature` — 桌面演示温度传感器工具，`spec` 的 `name` 为 `temperature.read`。`edge/boards/headless_sensor/src/main.rs:22`
- `OfflineBackend` — 离线后端，无观测时调用 `temperature.read`，有观测时回复温度读数。`edge/boards/headless_sensor/src/main.rs:40`
- `agent()` — 创建 agent 并注册 `Temperature`。`edge/boards/headless_sensor/src/main.rs:50`
- `EdgeNode::headless()` — 创建无屏设备节点并注册调用处理器。`edge/boards/headless_sensor/src/main.rs:72`
- `SpaceDevice::assemble` — 组装设备，平台 `headless`，模型 `Temperature sensor`。`edge/boards/headless_sensor/src/main.rs:96`
- 主入口函数为 `main`，传入 `--once` 时直接运行本地 agent 并返回。`edge/boards/headless_sensor/src/main.rs:58`
- 数据流向一句话：manufacturer.sensor/read 走 `Temperature.call`，manufacturer.agent/run 走本地 agent 的 `run`。`edge/boards/headless_sensor/src/main.rs:74`

## 核心机制

### 暴露的两个服务

- 产品通过已认证的设备服务路由器暴露 `manufacturer.sensor/read` 与 `manufacturer.agent/run` 两个服务。`edge/boards/headless_sensor/README.md:5`
- `manufacturer.sensor` 的 `read` 方法调用 `Temperature.call("{}")`。`edge/boards/headless_sensor/src/main.rs:75`
- `manufacturer.agent` 的 `run` 方法运行 agent().run("Read the sensor", "temperature")。`edge/boards/headless_sensor/src/main.rs:78`
- 未匹配的调用目标与方法返回 `None`。`edge/boards/headless_sensor/src/main.rs:85`
- 工具调用失败时返回 `CoreCallResponse::err`，错误码为 `SENSOR_ERROR`。`edge/boards/headless_sensor/src/main.rs:89`
- 传感器工具的 `ToolSpec` 的 `name` 为 `temperature.read`，`description` 为 `Read the product temperature sensor`。`edge/boards/headless_sensor/src/main.rs:22`
- 温度读取工具的 `call` 要求参数为 `{}`，否则返回 `AgentError::Tool` 错误 `Expected an empty object`。`edge/boards/headless_sensor/src/main.rs:28`
- 温度读取工具的 `call` 返回 `{"celsius":23.5,"source":"desktop-demo"}`。`edge/boards/headless_sensor/src/main.rs:32`

### 启动与状态

- 正常启动命令为 `cargo run --manifest-path edge/boards/headless_sensor/Cargo.toml`。`edge/boards/headless_sensor/README.md:13`
- 传入 `--once` 时 `main` 直接运行 `agent()?.run("Read the sensor", "temperature")` 并返回，不再继续执行监听启动。`edge/boards/headless_sensor/src/main.rs:59`
- `--once` 以单次模式运行本地 agent，不创建网络监听器。`edge/boards/headless_sensor/README.md:16`
- 正常启动把身份与 Space 状态持久化到 `.sensor-state`，可用 `OPERIT_SENSOR_STATE` 环境变量覆盖。`edge/boards/headless_sensor/README.md:17`
- 状态目录取自环境变量 `OPERIT_SENSOR_STATE`，未设置时默认为 `.sensor-state`。`edge/boards/headless_sensor/src/main.rs:62`
- `HostManager` 配置 `NativeRuntimeStorageHost`，运行时目录与工作区目录分别为状态目录下的 `runtime` 与 `workspace`。`edge/boards/headless_sensor/src/main.rs:66`
- `HostManager` 配置 `NativeTcpHost` 作为 TCP 主机。`edge/boards/headless_sensor/src/main.rs:70`
- `LocalHostRuntimeTaskSchedulerHost` 被配置为主机运行时任务调度器。`edge/boards/headless_sensor/src/main.rs:71`
- 监听配置绑定 `127.0.0.1:0`，传输仅 `PeerTransport::Tcp`，`discoveryEnabled` 为 `false`，端口模式为 `PeerHostPortMode::Automatic`。`edge/boards/headless_sensor/src/main.rs:108`
- 启动后从 `PeerStateStore` 读取监听配置并打印 node id 与真实绑定地址。`edge/boards/headless_sensor/src/main.rs:115`
- 正常启动打印产品真实的 TCP 地址。`edge/boards/headless_sensor/README.md:18`

### 控制台配对与加入

- 配对与加入的命令顺序为 `pair` → `confirm` → `join` → `refresh`。`edge/boards/headless_sensor/README.md:22`
- `pair <address>` 向 Core 发起 SDK 配对协议。`edge/boards/headless_sensor/README.md:22`
- `pair` 调用 `peers` 的 `startPairing`，`PeerEndpoint` 的 `nodeId` 为空字符串，地址取自命令参数，传输为 `PeerTransport::Tcp`。`edge/boards/headless_sensor/src/main.rs:137`
- `confirm <pairing-id> <six-digit-code>` 确认 Core 显示的配对码。`edge/boards/headless_sensor/README.md:23`
- `confirm` 调用 `peers.finishPairing(id, code)`。`edge/boards/headless_sensor/src/main.rs:146`
- `join <core-node-id>` 向 Core 的设备空间请求加入。`edge/boards/headless_sensor/README.md:24`
- `join` 调用 `device.space.requestDeviceSpaceJoin`，参数为 peer。`edge/boards/headless_sensor/src/main.rs:149`
- `refresh <request-id>` 对账审批并持久化加入结果。`edge/boards/headless_sensor/README.md:25`
- `refresh` 调用 `device.space.refreshDeviceSpaceJoin`，参数为 id。`edge/boards/headless_sensor/src/main.rs:153`
- Core 也可使用打印出的地址主动发起配对，`status` 显示本地确认码。`edge/boards/headless_sensor/README.md:28`
- 打印出的地址为 loopback 地址，监听绑定 `127.0.0.1:0` 且端口自动分配，仅同机 Core 可用该地址主动发起配对；跨设备 Core 无法用该地址连接。`edge/boards/headless_sensor/src/main.rs:108`
- `status` 打印 Space ID、已配对 peers 与本地显示的配对码。`edge/boards/headless_sensor/README.md:21`
- `agent` 通过 agent 工具循环读取本地传感器。`edge/boards/headless_sensor/README.md:20`
- `quit` 停止监听器与连接。`edge/boards/headless_sensor/README.md:26`
- 产品在加入 Core 之前与 Core 离线之后都继续本地运行。`edge/boards/headless_sensor/README.md:29`
- Space 成员资格与服务授权与 ESP32 产品使用同一运行时，空间职责见 [[edge-architecture|设备空间中的职责与边界]]。`edge/boards/headless_sensor/README.md:30`

### 换后端：真实 HAL 与 HttpBackend

- 桌面演示传感器返回 23.5 C，替换 `Temperature::call` 即可接入真实 HAL。`edge/boards/headless_sensor/README.md:6`
- 温度读取工具的 `call` 内注释说明用厂商 HAL 替换这个确定性的桌面传感器。`edge/boards/headless_sensor/src/main.rs:31`
- 产品可启用 SDK 的可选 `http-agent` 特性，把离线后端换成 `http_agent::HttpBackend`。`edge/boards/headless_sensor/README.md:8`
- `OfflineBackend` 的 `next` 在已有观测时返回 `Step::Reply`，内容为 `Temperature:` 加观测结果。`edge/boards/headless_sensor/src/main.rs:39`
- `OfflineBackend` 的 `next` 在无观测时返回 `Step::Call`，调用 `temperature.read`，参数为 `{}`。`edge/boards/headless_sensor/src/main.rs:40`

## 关键符号

- `Temperature` — 桌面演示温度传感器工具。`edge/boards/headless_sensor/src/main.rs:18`
- `call` — 温度读取方法，返回固定 23.5 C 的读数，参数必须为 `{}`。`edge/boards/headless_sensor/src/main.rs:32`
- `OfflineBackend` — 离线后端。`edge/boards/headless_sensor/src/main.rs:35`
- `agent()` — 创建 agent 并注册 `Temperature`，返回 `Agent<OfflineBackend>`。`edge/boards/headless_sensor/src/main.rs:50`
- `EdgeNode::headless()` — 创建无屏设备节点并注册调用处理器，节点 crate 见 [[edge-sdk-node|Edge 节点 crate]]。`edge/boards/headless_sensor/src/main.rs:72`
- `SpaceDevice::assemble` — 组装设备，平台 `headless`，模型 `Temperature sensor`。`edge/boards/headless_sensor/src/main.rs:96`
- `PeerHostConfig` — 监听配置，绑定 `127.0.0.1:0`，仅 TCP 传输。`edge/boards/headless_sensor/src/main.rs:107`
- `PeerStateStore` — 读取监听配置以打印真实绑定地址。`edge/boards/headless_sensor/src/main.rs:115`
- `HostManager` — 配置运行时存储主机与 TCP 主机。`edge/boards/headless_sensor/src/main.rs:65`
- `LocalHostRuntimeTaskSchedulerHost` — 主机运行时任务调度器。`edge/boards/headless_sensor/src/main.rs:71`
- `main` — 程序入口，传入 `--once` 时直接运行本地 agent 并返回。`edge/boards/headless_sensor/src/main.rs:58`

## 调用链

1. 启动：正常启动用 `cargo run --manifest-path edge/boards/headless_sensor/Cargo.toml`。`edge/boards/headless_sensor/README.md:13`
2. 单次模式：加 `--once` 直接运行本地 agent，不创建网络监听器。`edge/boards/headless_sensor/README.md:16`
3. 组装：`SpaceDevice::assemble` 用平台 `headless`、模型 `Temperature sensor` 组装设备。`edge/boards/headless_sensor/src/main.rs:96`
4. 监听：按 `PeerHostConfig` 绑定 `127.0.0.1:0`，仅 TCP 传输，不开启发现。`edge/boards/headless_sensor/src/main.rs:107`
5. 打印：启动打印 node id 与真实绑定地址，并打印控制台命令提示。`edge/boards/headless_sensor/src/main.rs:119`
6. 配对与加入：`pair` → `confirm` → `join` → `refresh`。`edge/boards/headless_sensor/README.md:22`
7. 服务调用：manufacturer.sensor/read 得温度读数，manufacturer.agent/run 得 agent 回复。`edge/boards/headless_sensor/src/main.rs:74`
8. 停止：`quit` 退出命令读取循环。`edge/boards/headless_sensor/src/main.rs:126`
9. 命令循环结束后调用 `device.stop()` 停止设备。`edge/boards/headless_sensor/src/main.rs:158`

## 来源

- 本页 seed 文件：`edge/boards/headless_sensor/README.md`（32 行）、`edge/boards/headless_sensor/src/main.rs`（160 行），基线 AAswordman/Operit2 @ 364d1d594，2026-11-11 全文读完。
- 完整图形化验收套件位于 `../esp32/editor`，编辑器页见 [[edge-esp32-editor|ESP32 编辑器与调试工具]]；SDK 与 agent 边界位于 `../../sdk/tests`。`edge/boards/headless_sensor/README.md:32`
- 本页无全仓零命中类断言，无需写核验方法。
- 范围说明：23.5 C 与 desktop-demo 只适用于桌面演示传感器，真实产品用 HAL 替换 `Temperature::call`。`edge/boards/headless_sensor/README.md:6`
- 未读文件：本页只读 2 个 seed 文件；`Cargo.toml` 与 SDK 源码未读未引。
