---
title: 厂商接入指南
module: edge
platforms: [all]
sources: 1
date: 2026-11-11
---

## 概述

- 本页是厂商接入 Operit2 Edge 的第一页：一个产品拥有自己的固件入口、设备能力、配置、存储策略和开发工具。`edge/docs/manufacturer-guide.md:3`
- 厂商产品在 `edge/boards/<product>` 下创建独立项目，通过 `operit-edge-sdk` 使用共享协议；产品形态总览见 [[edge-overview|Edge 总览与产品形态]]。`edge/docs/manufacturer-guide.md:3`
- 离线传感器或小机器人可以只使用默认的 `agent` 模块。`edge/docs/manufacturer-guide.md:7`
- 需要 HTTP 模型时启用 `http-agent`。`edge/docs/manufacturer-guide.md:9`
- 需要加入 Operit 空间时启用 `space`，功能开关的完整清单见 [[edge-sdk-entry|operit-edge-sdk 入口与功能开关]]。`edge/docs/manufacturer-guide.md:11`
- 屏幕产品可以额外启用 `scene`，无屏设备无需选择显示尺寸、表情或触摸组件。`edge/docs/manufacturer-guide.md:11`

## AI 速览

- `agent` — 默认模块，离线传感器或小机器人只用它即可。`edge/docs/manufacturer-guide.md:7`
- `http-agent` — HTTP 模型功能，创建 `HttpBackend`，传入已有的 `HttpHost` 和 `HttpAgentConfig`。`edge/docs/manufacturer-guide.md:9`
- `space` — 加入 Operit 空间的功能。`edge/docs/manufacturer-guide.md:11`
- `scene` — 屏幕产品额外启用的显示功能。`edge/docs/manufacturer-guide.md:11`
- `RuntimeStorageHost` — 持久化存储 Host，让身份、配对和空间状态能在设备重启后恢复。`edge/docs/manufacturer-guide.md:19`
- `HostRuntimeTaskSchedulerHost` — 任务调度 Host，为共享服务提供任务执行与延时能力。`edge/docs/manufacturer-guide.md:21`
- `HostManager` — 装配入口，安装持久化存储、传输、熵源和任务调度能力。`edge/docs/manufacturer-guide.md:26`
- `EdgeNode` — 服务边界，用 `headless` 创建无屏服务边界。`edge/docs/manufacturer-guide.md:27`
- `SpaceDevice` — 空间设备，`assemble` 同步完成共享身份与空间初始化。`edge/docs/manufacturer-guide.md:35`
- `Tool` — 厂商实现它接到传感器或电机，注册到 `Agent`。`edge/docs/manufacturer-guide.md:7`
- `Backend` — 厂商实现它选择本地规则、本地推理或远程模型。`edge/docs/manufacturer-guide.md:7`
- `Limits` — 约束保留的上下文，HTTP 字节预算约束网络缓冲。`edge/docs/manufacturer-guide.md:9`
- 主入口函数：SpaceDevice 的 `assemble`，接收 host、device_info、node、limits 四个参数。`edge/docs/manufacturer-guide.md:28`
- 数据流向一句话：装配 Host 能力 → 创建服务边界并注册服务 → `assemble` 复用同一身份与配对服务 → `listen` 启动传输 → 配对确认 → 申请加入空间。`edge/docs/manufacturer-guide.md:28`

## 核心机制

### 选择能力

- 离线传感器或小机器人可以只使用默认的 `agent` 模块。`edge/docs/manufacturer-guide.md:7`
- 厂商实现 `Tool` 接到传感器或电机，注册到 `Agent`。`edge/docs/manufacturer-guide.md:7`
- 厂商实现 `Backend` 选择本地规则、本地推理或远程模型。`edge/docs/manufacturer-guide.md:7`
- 只使用 `agent` 模块时 SDK 不会启动 Core、插件引擎或聊天数据库。`edge/docs/manufacturer-guide.md:7`
- 需要 HTTP 模型时启用 `http-agent`，创建 `HttpBackend`，传入已有的 `HttpHost` 和 `HttpAgentConfig`。`edge/docs/manufacturer-guide.md:9`
- `http-agent` 配置的是完整 chat completions URL，模型和密钥由产品管理。`edge/docs/manufacturer-guide.md:9`
- 模型响应只允许每一步调用一个已注册工具，工具返回值会回传模型。`edge/docs/manufacturer-guide.md:9`
- `Limits` 和 HTTP 字节预算分别约束保留的上下文与网络缓冲。`edge/docs/manufacturer-guide.md:9`
- 厂商仍需在工具中校验硬件参数。`edge/docs/manufacturer-guide.md:9`
- 需要加入 Operit 空间时启用 `space`。`edge/docs/manufacturer-guide.md:11`
- 屏幕产品可以额外启用 `scene`；无屏设备无需选择显示尺寸、表情或触摸组件。`edge/docs/manufacturer-guide.md:11`

### 装配前准备

- 指南以无屏产品 `headless_sensor` 的 main.rs 作为完整参考。`edge/docs/manufacturer-guide.md:15`
- 持久化存储需要安装 `RuntimeStorageHost`，让身份、配对和空间状态能在设备重启后恢复。`edge/docs/manufacturer-guide.md:19`
- 传输需要为选用的 TCP、串口等传输安装 Host 适配器，并确定监听配置。`edge/docs/manufacturer-guide.md:20`
- 任务调度需要安装 `HostRuntimeTaskSchedulerHost`，为共享服务提供任务执行与延时能力。`edge/docs/manufacturer-guide.md:21`
- 随机源需要在目标平台提供配对和加密使用的熵源，具体适配由产品运行环境负责。`edge/docs/manufacturer-guide.md:22`

### 配对、加入空间、授权

- 配对与空间授权分别验证，不能把“TCP 已连通”当成“已获授权”。`edge/docs/manufacturer-guide.md:31`
- 成员身份、审批和持久化由共享 runtime 维护。`edge/docs/manufacturer-guide.md:33`
- 自定义服务通过原有 Link 路由进入设备，路由检查空间、调用方和能力。`edge/docs/manufacturer-guide.md:33`
- 不要另开绕过这些检查的业务 HTTP 入口。`edge/docs/manufacturer-guide.md:33`
- SpaceDevice 的 `assemble` 同步完成共享身份与空间初始化，实际监听由后续的 `listen` 启动。`edge/docs/manufacturer-guide.md:35`
- 产品在接收远端调用期间持有返回的 `SpaceDevice`，结束服务时调用 `device.stop().await` 停止共享 Peer 服务。`edge/docs/manufacturer-guide.md:36`
- 重新启动时继续使用同一份持久化存储，保留设备身份和配对关系。`edge/docs/manufacturer-guide.md:37`

### 三种产品形态

- `ESP32` 产品包含原生 UI、独立聊天、空间聊天、语音、板卡适配与调试工具。`edge/docs/manufacturer-guide.md:42`
- `ESP32` 模拟器编译产品共用的 `Rust` 模块，并通过真实 TCP 连到桌面 `Core`。`edge/docs/manufacturer-guide.md:42`
- 无屏传感器只暴露传感器和 `agent` 服务，控制台完成配对与加入。`edge/docs/manufacturer-guide.md:44`
- 无屏传感器复用同一 SDK，不带 `ESP32` UI、表情或 `scene`。`edge/docs/manufacturer-guide.md:44`
- 桌面演示传感器返回固定读数，厂商替换 `Tool::call` 即可接入真实 `HAL`。`edge/docs/manufacturer-guide.md:44`
- 无屏传感器的配对和空间加入使用生产协议。`edge/docs/manufacturer-guide.md:44`
- Linux 机器人 `PB_SBC01_H3` 选择运行完整 Core。`edge/docs/manufacturer-guide.md:46`
- 只有需要本机执行完整 Core 的产品才承担对应依赖。`edge/docs/manufacturer-guide.md:46`

### 资源与构建边界

- SDK 默认无外部依赖。`edge/docs/manufacturer-guide.md:50`
- `space` 的正常依赖中不允许出现完整 Core、SQL、JavaScript、本地模型引擎或通用桌面 HTTP 客户端。`edge/docs/manufacturer-guide.md:50`
- `edge/tools/check-sdk-dependencies.py` 会检查默认、各可选功能及所有功能组合的依赖图。`edge/docs/manufacturer-guide.md:50`
- `ESP32` 模拟器固定 256 KiB `Rust` 堆。`edge/docs/manufacturer-guide.md:52`
- `ESP32` 模拟器的主线程、异步任务、阻塞任务分别使用 16/24/20 KiB 逻辑栈和保护页。`edge/docs/manufacturer-guide.md:52`
- 超过预算会真实失败。`edge/docs/manufacturer-guide.md:52`
- 桌面操作系统、C/Wasm UI 和网络系统库拥有各自内存，这些数值不能代表整板 RAM 或闪存。`edge/docs/manufacturer-guide.md:52`
- 修改固件后仍需 ESP-IDF 构建与硬件验收。`edge/docs/manufacturer-guide.md:52`
- 厂商扩展能力时须明确网络响应、历史记录、工具输出、并发和消息帧上限。`edge/docs/manufacturer-guide.md:54`
- 优先通过 Host 和本产品服务提供能力，保持 SDK 与板卡、UI 和模型引擎解耦。`edge/docs/manufacturer-guide.md:54`

## 关键符号

- `agent` — 默认模块，离线产品只用它即可。`edge/docs/manufacturer-guide.md:7`
- `Tool` — 厂商实现它接到传感器或电机，注册到 `Agent`。`edge/docs/manufacturer-guide.md:7`
- `Agent` — 注册 `Tool` 的目标。`edge/docs/manufacturer-guide.md:7`
- `Backend` — 厂商实现它选择本地规则、本地推理或远程模型。`edge/docs/manufacturer-guide.md:7`
- `http-agent` — HTTP 模型功能开关。`edge/docs/manufacturer-guide.md:9`
- `HttpBackend` — HTTP 模型后端，创建时传入已有的 `HttpHost` 和 `HttpAgentConfig`。`edge/docs/manufacturer-guide.md:9`
- `HttpHost` — 已有的 HTTP Host，传给 `HttpBackend`。`edge/docs/manufacturer-guide.md:9`
- `HttpAgentConfig` — HTTP agent 配置，传给 `HttpBackend`。`edge/docs/manufacturer-guide.md:9`
- `Limits` — 约束保留的上下文。`edge/docs/manufacturer-guide.md:9`
- `space` — 加入 Operit 空间的功能开关。`edge/docs/manufacturer-guide.md:11`
- `scene` — 屏幕产品额外启用的显示功能开关。`edge/docs/manufacturer-guide.md:11`
- `RuntimeStorageHost` — 持久化存储 Host。`edge/docs/manufacturer-guide.md:19`
- `HostRuntimeTaskSchedulerHost` — 任务调度 Host。`edge/docs/manufacturer-guide.md:21`
- `HostManager` — 装配入口，安装四类能力。`edge/docs/manufacturer-guide.md:26`
- EdgeNode 的 `headless` — 创建无屏服务边界。`edge/docs/manufacturer-guide.md:27`
- `withCallHandler` — 注册自己的服务。`edge/docs/manufacturer-guide.md:27`
- SpaceDevice 的 `assemble` — 同步完成共享身份与空间初始化，接收 host、device_info、node、limits。`edge/docs/manufacturer-guide.md:28`
- `listen` — 启动实际传输，接收 host_config。`edge/docs/manufacturer-guide.md:29`
- `peers` — 发现、发起配对和六位验证码确认的入口，挂在 device.services 下。`edge/docs/manufacturer-guide.md:30`
- `requestDeviceSpaceJoin` — 申请加入空间，接收 peer_node_id。`edge/docs/manufacturer-guide.md:31`
- `stop` — 结束服务时停止共享 Peer 服务。`edge/docs/manufacturer-guide.md:37`
- `check-sdk-dependencies.py` — 检查 SDK 依赖图的脚本。`edge/docs/manufacturer-guide.md:50`
- `ESP32` — 带原生 UI 与空间聊天的产品形态。`edge/docs/manufacturer-guide.md:42`
- `PB_SBC01_H3` — 选择运行完整 Core 的 Linux 机器人。`edge/docs/manufacturer-guide.md:46`

## 调用链

1. 提供 `HostManager`，安装持久化存储、TCP/串口等传输、熵源和任务调度能力；硬件寄存器和操作系统 API 留在本产品的 `board/`。`edge/docs/manufacturer-guide.md:26`
2. 用 EdgeNode 的 `headless` 创建服务边界，再通过 `withCallHandler` 注册自己的服务；SDK 的 GPIO、屏幕和表情服务均可按产品需要注册。`edge/docs/manufacturer-guide.md:27`
3. 调用 SpaceDevice 的 `assemble`，传入 host、device_info、node、limits，并持有返回值；这会复用同一个身份、配对服务和空间权限投影。`edge/docs/manufacturer-guide.md:28`
4. 调用 device 的 `listen`，传入 host_config，启动实际传输；产品决定监听地址、发现方式和是否允许自动端口。`edge/docs/manufacturer-guide.md:29`
5. 通过 device.services 的 `peers` 完成发现、发起配对和六位验证码确认；二维码或地址仅传递连接坐标，确认由用户在产品 UI 或控制台完成。`edge/docs/manufacturer-guide.md:30`
6. 调用 device.space 的 `requestDeviceSpaceJoin`，传入 peer_node_id，申请加入空间；审批通过后刷新请求。`edge/docs/manufacturer-guide.md:31`

## 来源

- `edge/docs/manufacturer-guide.md`（54 行）：厂商接入指南全文，本页唯一 seed 文件。
- 本页事实全部来自上述 1 个 seed 文件，基线为 `AAswordman/Operit2 @ 364d1d594`（2026-11-11）；本页未作全仓零命中类断言。
- 本页事实来自厂商指南文档，未引用实现代码；文档中的能力描述以指南文本为准，是否已在代码中实现不在本页断言范围内。
