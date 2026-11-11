---
title: operit-edge-sdk 入口与功能开关
module: edge
platforms: [all]
sources: 7
date: 2026-11-11
---

## 概述

- 稳定厂商入口是 `operit-edge-sdk` crate，接口手工维护，不要求厂商使用 Core 的生成客户端。edge/sdk/README.md:3
- operit-edge-sdk 的默认构建没有依赖，`agent` 模块无条件公开，本地工具与 agent 后端无需显示器或网络即可工作。edge/sdk/src/lib.rs:1、edge/sdk/src/lib.rs:3、edge/sdk/src/lib.rs:6
- `operit-edge-sdk` 包版本为 0.1.0。edge/sdk/Cargo.toml:3
- 该 workspace 的成员包括当前目录、`contract`、`node`、`proxy`、`scene`。edge/sdk/Cargo.toml:10
- 这不是 `no_std` SDK，启用空间接入需要 Rust `std`、持久化、熵源和异步 Host。edge/sdk/README.md:53
- ESP32 产品使用 ESP-IDF，默认零依赖不意味着启用网络与认证也零成本。edge/sdk/README.md:53
- 产品提供 Host 适配器，SDK 不选择 MCU、操作系统、网络库或 UI。edge/sdk/README.md:17

## AI 速览

- `operit-edge-sdk` — 稳定厂商入口 crate，默认零依赖。edge/sdk/README.md:3
- `agent` — 默认启用的模块，注册本地工具、有界 agent 执行循环、可替换模型后端。edge/sdk/README.md:12
- `space` — 可选 feature，配对、加密连接、空间审批、权限、设备服务路由。edge/sdk/README.md:13
- `http-agent` — 可选 feature，使用 Host HTTP 流的 OpenAI 兼容模型工具调用。edge/sdk/README.md:14
- `scene` — 可选 feature，有屏产品的资源和场景渲染。edge/sdk/README.md:15
- `SpaceDevice::assemble` — 普通产品的装配入口，同步初始化 Space，把厂商服务接到共享配对与空间服务上。edge/sdk/README.md:17、edge/sdk/README.md:23
- `EdgeNode::headless` — 只注册自定义服务的节点构造方式，显示、GPIO 和表情均不是必需能力。edge/sdk/README.md:17
- `agent::Agent` — 有界 agent 执行循环，只执行产品显式注册的工具。edge/sdk/README.md:19
- `Backend` — 模型后端 trait，对接本地推理、HTTP 模型或经过认证的 Core 服务。edge/sdk/README.md:19
- `http_agent::HttpBackend` — 可选的 HTTP 模型适配，含工具调用结果回传、响应字节限制、超时及取消时的连接清理。edge/sdk/README.md:19
- `check-sdk-dependencies.py` — 依赖审计脚本，检查默认、每个可选功能及所有功能组合。edge/sdk/README.md:39
- 主入口函数是 `SpaceDevice::assemble`：普通产品用它装配共享配对与空间服务。edge/sdk/README.md:23
- 另一主入口是 Agent 的 `run`：按 Limits 有界执行注册工具与后端调用。edge/sdk/src/agent.rs:116
- 数据流向一句话：`Agent` 只执行产品显式注册的工具，`Backend` 决定回复或工具调用，`HttpBackend` 把工具调用结果回传给模型。edge/sdk/README.md:19

## 核心机制

### 功能开关

- `default` feature 为空列表。edge/sdk/Cargo.toml:28
- `agent` 模块默认启用，无第三方依赖。edge/sdk/README.md:12
- `space` feature 默认不启用，引入 `operit-node-edge`、`operit-node-runtime`、`operit-host-api`、`operit-link`、`operit-store`、`operit-edge-contract`、`operit-proxy-edge`。edge/sdk/Cargo.toml:30
- `scene` feature 默认不启用，引入 `operit-edge-scene`。edge/sdk/Cargo.toml:32
- `http-agent` feature 默认不启用，引入 `operit-host-api`、`serde_json`、`tokio`。edge/sdk/Cargo.toml:34
- `http_agent` 模块仅在启用 `http-agent` feature 时公开。edge/sdk/src/lib.rs:8
- `scene` 仅在产品需要可选场景渲染器时启用。edge/sdk/src/lib.rs:5
- `space` feature 提供认证配对、成员关系与远程服务。edge/sdk/src/lib.rs:4
- `tokio` 依赖仅启用 `sync` 与 `time` 功能。edge/sdk/Cargo.toml:38
- `operit-node-runtime` 依赖关闭默认 feature 并启用 `peer-runtime`。edge/sdk/Cargo.toml:43
- `operit-store` 依赖关闭默认 feature 并启用 `node-state`。edge/sdk/Cargo.toml:44

### 命名入口

- `device`、`contract`、`proxy`、`host`、`link`、`runtime`、`storage` 为共享实现的命名入口。edge/sdk/README.md:21
- 产品首先使用 SDK 装配接口，底层模块用于需要精细配置的场景。edge/sdk/README.md:21
- 内部子 crate 继续复用 Core 的协议、存储与权限实现，避免维护两套配对协议。edge/sdk/README.md:21
- `contract` 命名入口仅在 `space` feature 下重导出 `operit_edge_contract`，契约内容见 [[edge-sdk-contract|Edge 契约 crate]]。edge/sdk/src/lib.rs:11
- `scene` 命名入口仅在 `scene` feature 下重导出 `operit_edge_scene`。edge/sdk/src/lib.rs:13
- `host` 命名入口仅在 `space` feature 下重导出 `operit_host_api`。edge/sdk/src/lib.rs:15
- `link` 命名入口仅在 `space` feature 下重导出 `operit_link`。edge/sdk/src/lib.rs:17
- `device` 命名入口仅在 `space` feature 下重导出 `operit_node_edge`。edge/sdk/src/lib.rs:19
- `runtime` 命名入口仅在 `space` feature 下重导出 `operit_node_runtime`。edge/sdk/src/lib.rs:21
- `proxy` 命名入口仅在 `space` feature 下重导出 `operit_proxy_edge`。edge/sdk/src/lib.rs:23
- `storage` 命名入口仅在 `space` feature 下重导出 `operit_store`。edge/sdk/src/lib.rs:25
- `space` 模块仅在 `space` feature 下公开，重导出 `SpaceDevice`、`createPeerService`、`EdgePeerRouter`、`HostRuntimePeerService`、`PeerRuntimeLimits`。edge/sdk/src/lib.rs:30
- `space` 模块还重导出 `NodeServices`、`NodeSpaceContext`、`NodeSpaceService`、`PeerStateStore`、`RuntimePeerService`。edge/sdk/src/lib.rs:37

### 有界 agent 执行

- `Limits` 默认值为 `max_steps` 4、`max_input_bytes` 2048、`max_output_bytes` 2048、`max_context_bytes` 4096。edge/sdk/src/agent.rs:36
- Agent 的 `new` 在任一 `Limits` 字段为 0 时返回 `AgentError::InvalidLimits`。edge/sdk/src/agent.rs:91
- Agent 的 `register` 对重名工具返回 `AgentError::DuplicateTool`。edge/sdk/src/agent.rs:109
- Agent 的 `run` 在指令与提示总长度超过 `max_input_bytes` 时返回 `AgentError::InputTooLarge`。edge/sdk/src/agent.rs:118
- 步数耗尽仍未得到回复时返回 `AgentError::StepLimit`。edge/sdk/src/agent.rs:170
- `Tool` trait 要求实现 `spec` 与 `call`，`call` 接收字符串参数并返回 `Result<String, AgentError>`。edge/sdk/src/agent.rs:54
- `Backend` trait 的 `next` 方法接收 `Request` 并返回 `AgentFuture`。edge/sdk/src/agent.rs:79
- `Backend` 可以对接本地推理、HTTP 模型或经过认证的 Core 服务。edge/sdk/README.md:19
- 物理动作的参数、范围与权限由产品工具实现检查。edge/sdk/README.md:19

### HTTP 模型适配

- `HttpBackend` 不在这里链接 HTTP 客户端或模型运行时，厂商提供已有的流式 HTTP Host。edge/sdk/src/http_agent.rs:2、edge/sdk/src/http_agent.rs:21
- HttpBackend 的 `new` 要求 `endpoint` 以 `http://` 或 `https://` 开头且长度不超过 1024。edge/sdk/src/http_agent.rs:27
- HttpBackend 的 `new` 要求 `model` 非空且长度不超过 128。edge/sdk/src/http_agent.rs:29
- HttpBackend 的 `new` 要求 `api_key` 长度不超过 512 且不含回车换行。edge/sdk/src/http_agent.rs:31
- HttpBackend 的 `new` 要求 `max_response_bytes`、`max_request_bytes`、`timeout_seconds` 均非 0。edge/sdk/src/http_agent.rs:33、edge/sdk/src/http_agent.rs:26
- HttpBackend 请求体设置 `max_tokens` 为 256。edge/sdk/src/http_agent.rs:72
- 仅当请求携带工具时，HttpBackend 请求体才设置 `parallel_tool_calls` 为 `false`。edge/sdk/src/http_agent.rs:80
- HttpBackend 请求体超过 `max_request_bytes` 时返回 `AgentError::InputTooLarge`。edge/sdk/src/http_agent.rs:83
- HttpBackend 未设置 `api_key` 时不发送 `Authorization` 头，设置时发送 `Bearer` 认证头。edge/sdk/src/http_agent.rs:89
- 非 200-299 的 HTTP 状态返回 `AgentError::Backend`。edge/sdk/src/http_agent.rs:142
- HttpBackend 请求超时后返回 `AgentError::Backend`，消息为 `Agent request timed out`。edge/sdk/src/http_agent.rs:163
- `StreamLease` 析构时调用 `HttpHost` 的 `closeHttpByteStream` 关闭连接。edge/sdk/src/http_agent.rs:48
- 每步只接受一次工具调用，多次调用返回 `AgentError::Backend`。edge/sdk/src/http_agent.rs:180
- 无工具调用时从 `message` 的 `content` 取回复文本，缺失时返回 `AgentError::Backend`。edge/sdk/src/http_agent.rs:198

### 装配方式与平台约束

- 普通产品使用 `SpaceDevice::assemble`，该方法同步初始化 Space。edge/sdk/README.md:23
- ESP32 固件将 `SpaceDevice::assemble` 放在受限的 Host 后台任务栈执行，并保留失败重试。edge/sdk/README.md:23
- ESP32 固件使用底层命名入口装配共享服务。edge/sdk/README.md:24
- 模拟器保留分阶段初始化与相同的资源限制。edge/sdk/README.md:25
- 调整装配方式时必须同时验证任务栈与堆预算，不能只以普通桌面进程启动成功作为依据。edge/sdk/README.md:25
- 网络 `PeerListener::localAddress()` 返回 `Option<String>`，网络监听器必须返回实际绑定地址，串口等非网络传输可以返回 `None`。edge/sdk/README.md:28
- 自动端口应读取持久化配置中的实际端口，不要在客户端写死 `8765`。edge/sdk/README.md:29
- 需要生成连接码时，Host 还须实现 `ServiceDiscoveryHost::localAddresses`，该查询独立于 mDNS 广播和浏览。edge/sdk/README.md:30
- ESP32 当前支持广播及活动 Wi-Fi IPv4 地址查询，不提供主动浏览其他设备的功能。edge/sdk/README.md:31
- 连接码仍须经过验证码确认和独立的 Space 审批。edge/sdk/README.md:32

### 协议兼容性

- Core 与 Edge 的运行时兼容性只按独立通信协议版本判断，与 Operit 软件版本及厂商固件版本无关。edge/sdk/README.md:55
- 协议源码指纹在构建时检查，变化后必须递增协议版本。edge/sdk/README.md:56

### 依赖审计

- 依赖审计脚本枚举 `space`、`http-agent`、`scene` 三个可选功能的所有组合，共 8 种组合：默认、3 个单功能、3 个双功能与 3 功能全开。edge/tools/check-sdk-dependencies.py:10
- 依赖审计脚本对每种组合运行 cargo tree -p operit-edge-sdk -e normal,build 检查正常及构建依赖。edge/tools/check-sdk-dependencies.py:13
- 禁止依赖包括 `operit-runtime`、`operit-core-application`、`operit-tools`、`operit-local-models`、`v8`、`rusqlite`、`sqlparser`、`reqwest`。edge/tools/check-sdk-dependencies.py:19
- 任一组合拉入禁止包时脚本退出报错。edge/tools/check-sdk-dependencies.py:23
- 默认组合的包集合必须恰为 1 个包，即零外部依赖，否则脚本退出报错。edge/tools/check-sdk-dependencies.py:24
- 依赖脚本分别检查默认、`space`、`http-agent` 和 `scene` 的正常及构建依赖。edge/sdk/README.md:48
- 依赖脚本确认默认入口没有外部依赖，并阻止完整 Core、SQL 和模型引擎等依赖进入设备侧。edge/sdk/README.md:49
- SDK 测试命令为 `cargo test --locked --manifest-path edge/sdk/Cargo.toml --workspace --all-features`，依赖检查命令为 `python3 edge/tools/check-sdk-dependencies.py`。edge/sdk/README.md:37、edge/sdk/README.md:38
- Windows PowerShell 下依赖检查命令可替换为 `python -X utf8 edge/tools/check-sdk-dependencies.py`。edge/sdk/README.md:45

## 关键符号

- `operit-edge-sdk` — 稳定厂商入口 crate，版本 0.1.0。edge/sdk/Cargo.toml:3
- `agent` — 默认启用的模块，本地工具与有界 agent 执行循环。edge/sdk/src/lib.rs:6
- `http_agent` — 仅在 `http-agent` feature 下公开的模块。edge/sdk/src/lib.rs:8
- `space` — 仅在 `space` feature 下公开的模块，重导出共享配对与空间组件。edge/sdk/src/lib.rs:29
- `SpaceDevice` — 拥有 `node`、`services`、`space`、`node_id` 四个公开字段，`node` 为 `Arc<EdgeNode>`，`space` 为 `Arc<NodeSpaceService>`。edge/sdk/src/space_device.rs:16
- SpaceDevice 的 `assemble` — 接收 `host`、`info`、`node`、`limits` 四个参数，同步初始化 Space。edge/sdk/src/space_device.rs:25
- SpaceDevice 的 `listen` — 先保存监听配置再启动监听。edge/sdk/src/space_device.rs:66
- SpaceDevice 的 `stop` — 停止对等服务。edge/sdk/src/space_device.rs:76
- `EdgeNode::headless` — 只注册自定义服务的节点构造方式。edge/sdk/README.md:17
- `Agent` — 有界 agent 执行循环，泛型参数为后端类型。edge/sdk/src/agent.rs:83
- Agent 的 `new` — 用后端与 `Limits` 构造 `Agent`，零值限制返回 `AgentError::InvalidLimits`。edge/sdk/src/agent.rs:91
- Agent 的 `register` — 注册产品工具，重名返回 `AgentError::DuplicateTool`。edge/sdk/src/agent.rs:109
- Agent 的 `run` — 执行有界循环，返回回复文本或 `AgentError`。edge/sdk/src/agent.rs:116
- `Limits` — 限制步数、输入字节、输出字节与上下文字节的结构体。edge/sdk/src/agent.rs:36
- `Tool` — 产品工具 trait，`spec` 描述工具，`call` 执行工具。edge/sdk/src/agent.rs:54
- `Backend` — 模型后端 trait，`next` 方法按 `Request` 产生下一步。edge/sdk/src/agent.rs:79
- `Step` — 分为 `Reply(String)` 与 `Call` { tool, arguments } 两种。edge/sdk/src/agent.rs:73
- `AgentError` — 包含 `InvalidLimits`、`InputTooLarge`、`OutputTooLarge`、`StepLimit`、`UnknownTool`、`DuplicateTool`、`Backend`、`Tool` 八个变体。edge/sdk/src/agent.rs:11
- `HttpBackend` — 可选的 HTTP 模型适配，持有 `Arc<dyn HttpHost>` 与 `HttpAgentConfig`。edge/sdk/src/http_agent.rs:21
- `HttpAgentConfig` — 含 `endpoint`、`model`、`api_key`、`max_response_bytes`、`max_request_bytes`、`timeout_seconds` 的配置结构体。edge/sdk/src/http_agent.rs:12、edge/sdk/src/http_agent.rs:18
- HttpBackend 的 `new` — 校验 `HttpAgentConfig` 的 `endpoint`、`model`、`api_key` 与字节超时字段。edge/sdk/src/http_agent.rs:26
- `StreamLease` — 析构时关闭 HTTP 字节流的租约结构。edge/sdk/src/http_agent.rs:46
- `decode_step` — 把 HTTP 响应字节解码为 `Step` 的函数。edge/sdk/src/http_agent.rs:170
- `createPeerService` — `space` 模块重导出的对等服务创建函数。edge/sdk/src/lib.rs:31
- `EdgePeerRouter` — `space` 模块重导出的对等路由。edge/sdk/src/lib.rs:32
- `NodeServices` — space 模块重导出的节点服务集合。edge/sdk/src/lib.rs:36
- `NodeSpaceService` — `space` 模块重导出的空间服务。edge/sdk/src/lib.rs:37
- `PeerStateStore` — `space` 模块重导出的对等状态存储。edge/sdk/src/lib.rs:38
- `RuntimePeerService` — `space` 模块重导出的运行时对等服务。edge/sdk/src/lib.rs:39
- `PeerRuntimeLimits` — `space` 模块重导出的对等运行时限制。edge/sdk/src/lib.rs:33

## 调用链

1. 产品依赖 `operit-edge-sdk`，按需开启 `space`、`http-agent`、`scene` feature。edge/sdk/README.md:7、edge/sdk/README.md:14、edge/sdk/README.md:15
2. 产品实现 `Tool` 并用 Agent 的 `register` 注册工具。edge/sdk/src/agent.rs:106
3. Agent 的 `new` 用后端与 `Limits` 构造 `Agent`，零值限制返回 `AgentError::InvalidLimits`。edge/sdk/src/agent.rs:91
4. Agent 的 `run` 校验指令与提示总长度，超限返回 `AgentError::InputTooLarge`。edge/sdk/src/agent.rs:116
5. 执行循环按 `max_steps` 轮询，把 `Request` 交给 `next`。edge/sdk/src/agent.rs:122
6. HttpBackend 的 `new` 校验 `HttpAgentConfig` 的 `endpoint`、`model`、`api_key` 与字节超时字段。edge/sdk/src/http_agent.rs:26
7. `decode_step` 把 HTTP 响应字节解码为 `Step`。edge/sdk/src/http_agent.rs:170
8. 启用 space 时，普通产品调用 SpaceDevice 的 `assemble`，传入 `host`、`info`、`node`、`limits`。edge/sdk/src/space_device.rs:25
9. SpaceDevice 的 `assemble` 取 `RuntimeStorageHost`，未安装时返回错误。edge/sdk/src/space_device.rs:34、edge/sdk/src/space_device.rs:25
10. SpaceDevice 的 `assemble` 用 `CoreNodeIdentityStore` 初始化节点身份得到 `nodeId`，再用 `createPeerService` 创建对等服务。edge/sdk/src/space_device.rs:35、edge/sdk/src/space_device.rs:39、edge/sdk/src/space_device.rs:25
11. SpaceDevice 的 `assemble` 用 `NodeServices::new` 包装对等服务，用 `NodeSpaceService::new` 创建空间服务并初始化。edge/sdk/src/space_device.rs:41、edge/sdk/src/space_device.rs:25
12. SpaceDevice 的 `assemble` 把空间服务 `installSpace` 到路由，再用 `EdgeNode` 的 `withNodeServices` 把服务挂到节点上。edge/sdk/src/space_device.rs:54、edge/sdk/src/space_device.rs:25
13. `EdgeNode::headless` 只注册自定义服务，显示、GPIO 和表情均不是必需能力。edge/sdk/README.md:17
14. 装配完成后 SpaceDevice 的 `listen` 保存监听配置并启动监听。edge/sdk/src/space_device.rs:66
15. SpaceDevice 的 `stop` 停止对等服务。edge/sdk/src/space_device.rs:76
16. 依赖审计脚本对默认、每个单功能、每对双功能与三功能全开共 8 种组合运行 cargo tree。edge/tools/check-sdk-dependencies.py:10
17. 默认组合零外部依赖且无禁止包进入设备侧，否则脚本退出报错。edge/tools/check-sdk-dependencies.py:24

## 来源

- `edge/sdk/README.md`
- `edge/sdk/Cargo.toml`
- `edge/sdk/src/lib.rs`
- `edge/sdk/src/agent.rs`
- `edge/sdk/src/http_agent.rs`
- `edge/sdk/src/space_device.rs`
- `edge/tools/check-sdk-dependencies.py`
- 7 份 seed 文件合计 625 行（README 56、Cargo.toml 46、lib.rs 43、agent.rs 172、http_agent.rs 199、space_device.rs 83、check-sdk-dependencies.py 26），与大纲 `est_lines: 625` 一致；源码基线为 `AAswordman/Operit2 @ 364d1d594`（2026-11-11）。
- 范围说明：`EdgeNode::headless` 的定义不在本页 7 个 seed 文件中，本页只按 `edge/sdk/README.md` 第 17 行的说法转述其用途，不展开其构造细节。edge/sdk/README.md:17
- 否定性结论核验方法：本页未作全仓零命中类断言；“默认零依赖”由 `default` 空列表与依赖审计脚本的默认组合检查共同支撑，脚本在默认组合包集合不为 1 个包时退出报错。edge/sdk/Cargo.toml:28
