---
title: Core 总览与 crate 边界
module: core
platforms: [all]
sources: [32]
date: 2026-11-11
---

## 概述

Operit2 的 Core 是 Rust 实现主体，由 `core/Cargo.toml` 的 workspace 组织，11 个领域分组、29 个真 crate（`core/Cargo.toml:3`）。
`core/CRATE_BOUNDARIES.md` 定义以 `operit-runtime` 为中心的 crate 拆分：下层 crate 暴露数据、服务与 trait，父级 runtime 把具体行为装配在一起（`core/CRATE_BOUNDARIES.md:3`）。
本页回答四个问题：11 个领域分组与 29 个真 crate 是什么关系、依赖方向为什么是 `plugin-sdk/host-api` → `util` → `model` → `store` → `tools/local-models/providers/js-bridge` → `runtime` → `core-proxy/command-core`、子 crate 需要父级行为时走什么机制、`core/peer-protocol.json` 是什么的来源。
相关页：[[arch-overview|架构总览]]、[[arch-corenode|CoreNode]]、[[arch-sync|多设备同步]]。
限定：本页的边界定义以 `CRATE_BOUNDARIES.md` 为准；凡文档声称与 `Cargo.toml` 实际依赖不一致处，本页按 `Cargo.toml` 写并逐条标出；未做真实双设备实验，同步与配对行为只覆盖代码与文档路径。

## AI 速览

- `operit-runtime` — 父级编排 crate，拥有应用启动、服务装配与聊天服务生命周期（`core/CRATE_BOUNDARIES.md:41`）
- `operit-host-api` — 宿主能力 trait 与 `HostManager`（`core/CRATE_BOUNDARIES.md:9`）
- `operit-util` — 共享工具代码、流助手、日志助手、序列化器（`core/CRATE_BOUNDARIES.md:11`）
- `operit-model` — 各层共用的数据结构（`core/CRATE_BOUNDARIES.md:13`）
- `operit-store` — 持久化层、DAO/仓库代码、偏好存储（`core/CRATE_BOUNDARIES.md:15`）
- `operit-plugin-sdk` — 可发布的插件契约、ToolPkg 解析/加载、钩子分发（`core/CRATE_BOUNDARIES.md:17`）
- `operit-plugin-theme` — 与运行时无关的 theme v1 模式与完整性检查（`core/CRATE_BOUNDARIES.md:21`）
- `operit-tools` — 工具系统，包括内置工具、ToolPkg、MCP、技能包（`core/CRATE_BOUNDARIES.md:27`）
- `operit-local-models` — 本地模型清单、已安装模型注册表契约（`core/CRATE_BOUNDARIES.md:31`）
- `operit-providers` — Provider 契约与内置实现，包括 `AIService`（`core/CRATE_BOUNDARIES.md:34`）
- `operit-js-bridge` — JavaScript 引擎集成与 JS 专用的 ToolPkg 执行面（`core/CRATE_BOUNDARIES.md:38`）
- `operit-proxy-local` — 构建时代理生成与本地分发（`core/CRATE_BOUNDARIES.md:45`）
- `operit-link` — 传输协议与客户端/服务端原语（`core/CRATE_BOUNDARIES.md:48`）
- `operit-edge-contract` — 共享的 Edge 服务地址与属性名（`core/CRATE_BOUNDARIES.md:49`）
- `operit-node-edge` — 轻量设备侧 Edge Core 节点（`core/CRATE_BOUNDARIES.md:51`）
- `operit-command-core` — CLI 命令层（`core/CRATE_BOUNDARIES.md:56`）
- `ToolRuntimeSupport` — 工具侧对父级运行时的请求 trait（`core/crates/tool/services/src/runtime_support.rs:417`）
- `ProviderRuntimeSupport` — Provider 侧对父级运行时的请求 trait（`core/crates/provider/services/src/runtime_support.rs:281`）
- `LocalModelRuntimeSupport` — 本地模型侧对父级运行时的请求 trait（`core/crates/provider/local-model/src/runtime_support.rs:7`）
- `HostManager` — 活动宿主能力集与面向生命周期的宿主句柄（`core/crates/foundation/host-api/src/HostManager.rs:139`）
- 主入口：`core/Cargo.toml` 的 workspace，members 从 `crates/foundation/host-api` 开始、到 `crates/command/core` 结束（`core/Cargo.toml:3`）
- 数据流向：下层 crate 暴露数据、服务与 trait，`operit-runtime` 把具体行为装配在一起，子 crate 需要父级行为时通过 trait 对象调用（`core/CRATE_BOUNDARIES.md:98`）

## 核心机制

### 领域分组与真 crate

- `core/crates` 先按领域分 11 个一级目录，再按 crate 分第二级目录（`core/crates/README.md:3`）
- `foundation` 领域是共享的宿主契约、模型、工具与 Link 协议类型（`core/crates/README.md:9`）
- `persistence` 领域是存储、仓库、身份数据与同步持久化（`core/crates/README.md:10`）
- `provider` 领域是 LLM、媒体、市场、记忆与本地模型服务（`core/crates/README.md:11`）
- `tool` 领域是工具执行、内置工具、技能、包、MCP 与工具脚本（`core/crates/README.md:12`）
- `plugin` 领域是插件 SDK、SDK 代码生成、插件运行时支持与 JavaScript 桥（`core/crates/README.md:13`）
- `runtime` 领域是核心业务运行时与应用层服务（`core/crates/README.md:14`）
- `node` 领域是节点身份、配对、认证对等链接与传输、路由宏、节点路由、空间运行时与同步，以及受限设备用的紧凑 Edge 契约与能力运行时（`core/crates/README.md:15`）
- `rslink` 领域是纯 Rust 到 Link 再到 Rust 的协议运行时与共享代码生成基础（`core/crates/README.md:18`）
- `proxy` 领域是核心应用代理扫描、语言发射器、桥契约、本地代理运行时与类型化 Edge 服务投影（`core/crates/README.md:19`）
- `application` 领域是把 runtime、proxy 与 node 组装成一棵 Core 树的组合根（`core/crates/README.md:21`）
- `command` 领域是在核心应用门面之上的命令编排（`core/crates/README.md:22`）
- `core/Cargo.toml` 的 workspace members 列出 29 个 crate（`core/Cargo.toml:3`）
- members 列出的 29 个路径在磁盘上都有自己的 `Cargo.toml` 与 `src` 目录（`core/Cargo.toml:3`）
- `crates/README.md` 要求每个第二级 crate 目录都有自己的 `Cargo.toml`、`src` 与 `README.md`，但 `node/peer-link`、`persistence/rescue`、`plugin/sdk-ipc`、`plugin/sdk-ipc-bridge`、`plugin/sdk-macros` 共 5 个 crate 目录下没有 `README.md`（`core/crates/README.md:5`）
- core 工作区用 resolver 2（`core/Cargo.toml:33`）
- core 工作区包默认 edition 2021、license MIT、publish 为 false（`core/Cargo.toml:36`）
- `CRATE_BOUNDARIES.md` 的 Crates 一节列出 16 个 crate，其中 14 个是 core 工作区成员，`operit-edge-contract` 与 `operit-node-edge` 不在 core 工作区内，实体在 `edge/sdk`（`core/CRATE_BOUNDARIES.md:49`）
- core 工作区 29 个成员中有 15 个不在 `CRATE_BOUNDARIES.md` 的 Crates 一节中，包括 `operit-node-runtime`、`operit-data-rescue`、`operit-plugin-sdk-ipc`、`operit-plugin-sdk-ipc-bridge`、`operit-plugin-sdk-codegen`、`operit-plugin-sdk-macros`、`operit-route-macros`、`operit-peer-link`、`operit-rslink-runtime`、`operit-rslink-codegen`、`operit-proxy-scan`、`operit-proxy-rust-codegen`、`operit-proxy-dart-codegen`、`operit-proxy-bridge`、`operit-core-application`（`core/Cargo.toml:3`）

### 依赖方向

- `CRATE_BOUNDARIES.md` 规定的依赖方向是 `plugin-sdk/host-api` → `util` → `model` → `store` → `tools/local-models/providers/js-bridge` → `runtime` → `core-proxy/command-core`，箭头表示左侧定义可被右侧依赖（`core/CRATE_BOUNDARIES.md:63`）
- `CRATE_BOUNDARIES.md` 规定 runtime 可以依赖全部子 crate，子 crate 不得依赖 `operit-runtime`（`core/CRATE_BOUNDARIES.md:66`）
- `operit-util` 依赖 `operit-host-api`（`core/crates/foundation/util/Cargo.toml:17`）
- `operit-model` 依赖 `operit-util`、`operit-host-api` 与 `operit-link`（`core/crates/foundation/model/Cargo.toml:15`）
- `operit-store` 依赖 `operit-model`（可选）、`operit-util` 与 `operit-host-api`（`core/crates/persistence/store/Cargo.toml:24`）
- `operit-tools` 依赖 `operit-plugin-sdk`、`operit-store`、`operit-model`、`operit-util`、`operit-host-api`，以及 `operit-link`、`operit-rslink-runtime`、`operit-route-macros`、`operit-edge-contract`（`core/crates/tool/services/Cargo.toml:30`）
- `operit-local-models` 依赖 `operit-host-api` 与 `operit-util`，不依赖 `operit-runtime`（`core/crates/provider/local-model/Cargo.toml:20`）
- `operit-providers` 依赖 `operit-tools`、`operit-store`、`operit-plugin-sdk`、`operit-model`、`operit-util`、`operit-host-api` 与 `operit-link`，不依赖 `operit-runtime`（`core/crates/provider/services/Cargo.toml:22`）
- `operit-js-bridge` 依赖 `operit-plugin-sdk`、`operit-store`、`operit-util`、`operit-host-api`，不依赖 `operit-tools`（`core/crates/plugin/javascript-bridge/Cargo.toml:16`）
- `operit-runtime` 依赖 `operit-tools`、`operit-providers`、`operit-store`、`operit-model`、`operit-util`、`operit-plugin-sdk`、`operit-plugin-theme`、`operit-local-models`（`core/crates/runtime/application/Cargo.toml:32`）
- `operit-runtime` 还依赖 `operit-host-api`、`operit-link`、`operit-rslink-runtime`、`operit-route-macros`，其中 `operit-js-bridge` 是可选依赖（`core/crates/runtime/application/Cargo.toml:27`）
- `operit-runtime` 依赖 `operit-edge-contract`（`core/crates/runtime/application/Cargo.toml:13`）
- `operit-proxy-local` 依赖 `operit-proxy-bridge`、`operit-rslink-runtime`、`operit-host-api`、`operit-link`、`operit-local-models`、`operit-model`、`operit-plugin-sdk`、`operit-plugin-sdk-ipc`、`operit-providers`、`operit-runtime`（`core/crates/proxy/local/Cargo.toml:17`）
- `operit-proxy-local` 依赖 `operit-store`、`operit-plugin-theme`、`operit-tools`、`operit-util`（`core/crates/proxy/local/Cargo.toml:24`）
- `operit-proxy-local` 依赖 `operit-edge-contract`、`operit-node-runtime`、`operit-peer-link`（`core/crates/proxy/local/Cargo.toml:10`）
- `operit-command-core` 依赖 `operit-runtime`、`operit-providers`、`operit-store`、`operit-host-api`、`operit-local-models`、`operit-model`、`operit-tools`、`operit-util`（`core/crates/command/core/Cargo.toml:12`）
- `operit-core-application` 依赖 `operit-runtime`、`operit-proxy-local`、`operit-node-runtime`、`operit-tools`、`operit-plugin-sdk`、`operit-plugin-sdk-ipc`、`operit-plugin-sdk-ipc-bridge`、`operit-host-api`、`operit-link`、`operit-util`（`core/crates/application/core/Cargo.toml:13`）
- `operit-node-runtime` 依赖 `operit-peer-link`、`operit-host-api`、`operit-link`，以及可选的 `operit-rslink-runtime`、`operit-runtime`（features 为 javascript）、`operit-store`、`operit-tools`、`operit-util`（`core/crates/node/runtime/Cargo.toml:33`）
- `operit-node-edge` 依赖 `operit-node-runtime`、`operit-host-api`、`operit-edge-contract`、`operit-link`（`edge/sdk/node/Cargo.toml:12`）
- `operit-proxy-edge` 依赖 `operit-edge-contract`、`operit-host-api`、`operit-link`（`edge/sdk/proxy/Cargo.toml:12`）
- `operit-edge-contract` 依赖 `operit-link`（`edge/sdk/contract/Cargo.toml:11`）
- `operit-plugin-theme` 的 `[dependencies]` 只有公开生态 crate，文档该句与实现一致（`core/crates/plugin/theme/Cargo.toml:20`）
- `operit-proxy-local` 在非 wasm32 目标上还依赖 `operit-command-core`（`core/crates/proxy/local/Cargo.toml:48`）

### 文档与实现的六处不一致（以 Cargo.toml 为准）

- `core/CRATE_BOUNDARIES.md:74` 称 `operit-plugin-sdk` 只依赖公开生态 crate，但其 `Cargo.toml` 的 `[dependencies]` 列出 `operit-plugin-sdk-macros`、`operit-plugin-theme`、`operit-host-api`、`operit-util` 四个内部 crate（`core/crates/plugin/sdk/Cargo.toml:14`）
- `core/CRATE_BOUNDARIES.md:88` 称 `operit-runtime` 依赖全部子 crate，但其 `Cargo.toml` 的 `[dependencies]` 中没有 `operit-node-runtime`、`operit-peer-link`、`operit-proxy-scan`、`operit-proxy-rust-codegen`、`operit-proxy-dart-codegen`、`operit-proxy-bridge`、`operit-proxy-local`、`operit-rslink-codegen`、`operit-plugin-sdk-ipc`、`operit-plugin-sdk-ipc-bridge`、`operit-plugin-sdk-codegen`、`operit-plugin-sdk-macros`、`operit-data-rescue`、`operit-core-application`、`operit-command-core`（`core/crates/runtime/application/Cargo.toml:36`）
- `operit-node-runtime` 以可选依赖引用 `operit-runtime`，features 为 javascript，这与 `core/CRATE_BOUNDARIES.md:66` 的子 crate 不得依赖 `operit-runtime` 规则冲突（`core/crates/node/runtime/Cargo.toml:35`）
- `core/CRATE_BOUNDARIES.md:90–91` 列出的 `operit-node-edge` 依赖是 `operit-edge-contract`、Host API、Link 与小型序列化/任务原语，未列出 `operit-node-runtime`，但 `edge/sdk/node/Cargo.toml:10` 明确依赖 `operit-node-runtime`（`edge/sdk/node/Cargo.toml:10`）
- `core/CRATE_BOUNDARIES.md:92` 称 `operit-proxy-edge` 依赖 `operit-edge-contract` 与 Link，但 `edge/sdk/proxy/Cargo.toml:12` 还列出 `operit-host-api`（`edge/sdk/proxy/Cargo.toml:12`）
- `core/CRATE_BOUNDARIES.md:126–128` 称 `operit-js-bridge` 用 `QuickJsExecutionProvider` 实现 `JsExecutionProvider`，但该名字在 `operit-js-bridge` 源码中不存在，实际实现是 `HostJsExecutionProvider`（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:16`）

### 父级行为机制

- 子 crate 需要父级行为时，子 crate 定义 trait 并消费 trait 对象，父级 runtime 实现并安装该 trait（`core/CRATE_BOUNDARIES.md:98`）
- `ToolRuntimeSupport` trait 定义在 `core/crates/tool/services/src/runtime_support.rs:417`（`core/crates/tool/services/src/runtime_support.rs:417`）
- `operit-runtime` 在 `services/ToolRuntimeSupportService.rs` 中以 `RuntimeToolSupport` 实现 `ToolRuntimeSupport`（`core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:137`）
- `ProviderRuntimeSupport` trait 定义在 `core/crates/provider/services/src/runtime_support.rs:281`（`core/crates/provider/services/src/runtime_support.rs:281`）
- `operit-runtime` 在 `services/ProviderRuntimeSupportService.rs` 中以 `RuntimeProviderSupport` 实现 `ProviderRuntimeSupport`（`core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:443`）
- `LocalModelRuntimeSupport` trait 定义在 `core/crates/provider/local-model/src/runtime_support.rs:7`（`core/crates/provider/local-model/src/runtime_support.rs:7`）
- `GitHubTokenSource` trait 定义在 `core/crates/provider/services/src/market/MarketStatsApiService.rs:512`，请求已登录 GitHub 账号的访问令牌（`core/crates/provider/services/src/market/MarketStatsApiService.rs:512`）
- `JsExecutionHost` trait 定义在 `core/crates/plugin/sdk/src/javascript.rs:213`（`core/crates/plugin/sdk/src/javascript.rs:213`）
- `operit-tools` 在 `tools/AIToolHandler.rs` 中以 `AIToolHandler` 实现 `JsExecutionHost`（`core/crates/tool/services/src/tools/AIToolHandler.rs:1224`）
- `JsExecutionProvider` trait 定义在 `core/crates/plugin/sdk/src/javascript.rs:435`（`core/crates/plugin/sdk/src/javascript.rs:435`）
- `operit-js-bridge` 在 `javascript/JsExecutionProvider.rs` 中以 `HostJsExecutionProvider` 实现 `JsExecutionProvider`（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:91`）
- `JsPackageExecutor` trait 定义在 `core/crates/plugin/sdk/src/javascript.rs:426`（`core/crates/plugin/sdk/src/javascript.rs:426`）
- `JsExecutionEngine` trait 定义在 `core/crates/plugin/sdk/src/javascript.rs:653`（`core/crates/plugin/sdk/src/javascript.rs:653`）

### 各边界归属

- 宿主集成在 `operit-host-api` 之后，平台 crate 提供实现，运行时代码只看到显式 trait 与环境描述符（`core/CRATE_BOUNDARIES.md:140`）
- `HostManager` 结构体定义在 `core/crates/foundation/host-api/src/HostManager.rs:139`，拥有活动宿主能力集与面向生命周期的宿主句柄（`core/crates/foundation/host-api/src/HostManager.rs:139`）
- 仓库与持久化数据结构属于 `operit-store`，可复用值模型属于 `operit-model`，仓库所有权留在 store，工作区编排属于 `operit-runtime/src/services/WorkspaceService.rs`（`core/CRATE_BOUNDARIES.md:150`）
- Provider 契约、内置实现与 Provider 编排属于 `operit-providers`，运行时专属操作通过 `ProviderRuntimeSupport` 暴露（`core/CRATE_BOUNDARIES.md:157`）
- 本地模型清单、已安装模型注册表契约、存储路径助手与本地推理会话接口属于 `operit-local-models`，网络传输经 `operit-host-api::HttpHost` 提交，具体宿主拥有下载 worker 并发、进度报告与取消处理（`core/CRATE_BOUNDARIES.md:163`）
- MCP 与技能包属于工具系统，管理器、包模型、仓库与执行助手在 `operit-tools`；ToolPkg 包格式、通用包状态管理、钩子、加载器、DSL、固定 JavaScript API、完整包服务与 JS 执行契约在 `operit-plugin-sdk`；具体 JS 引擎在 `operit-js-bridge`（`core/CRATE_BOUNDARIES.md:171`）
- `operit-proxy-local` 是桌面投影层，扫描拆分 crate 的选中公开面并生成传输侧 Rust 与 Dart 代理代码；`operit-proxy-edge` 是 Edge 服务的类型化投影；共享的 `operit-edge-contract` 只含稳定 Edge 地址（`core/CRATE_BOUNDARIES.md:181`）

### peer-protocol.json 是什么的来源

- `core/peer-protocol.json` 是 Core/Edge 通信协议版本及 SHA-256 指纹的唯一记录（`docs/peer-protocol-versioning.md:9`）
- `core/peer-protocol.json` 的 `sources` 数组列出 38 个参与协议指纹检查的源文件或目录（`core/peer-protocol.json:3`）
- `core/peer-protocol.json` 的 `revisions` 记录 15 个协议版本，从 version 1 到 version 15（`core/peer-protocol.json:100`）
- `core/peer-protocol.json` 的最新版本 15 的 SHA-256 指纹是 `6e1cd3450e8812471bfd25830cf769c1ce2e2181387b3b1a1357ea259952e80d`（`core/peer-protocol.json:101`）
- `core/peer-protocol.json` 的 `schemaRoots` 列出 7 个可序列化 DTO 扫描根（`core/peer-protocol.json:104`）
- `peer-protocol.json` 的 `sources` 覆盖 core 的 Link、节点、持久化、运行时源码与 `edge/sdk` 的 contract、node、proxy 三部分（`core/peer-protocol.json:28`）
- `peer-protocol.json` 的 `sources` 列出的 38 个路径在基线 364d1d594 上都存在，7 个 `schemaRoots` 也都存在（`core/peer-protocol.json:3`）
- 构建时递归收集 `sources` 中的 Rust 文件，按仓库相对路径排序、统一 CRLF/LF 后把路径、长度与内容纳入哈希（`docs/peer-protocol-versioning.md:10`）
- 协议指纹覆盖 Link 编解码、配对与认证会话、空间准入和权限、同步记录及事务应用、Core/Edge 路由和设备服务协议（`docs/peer-protocol-versioning.md:14`）
- 指纹变化时构建失败并打印新的 SHA-256，须在 `revisions` 末尾追加 version 递增的新记录，历史记录保持原样（`docs/peer-protocol-versioning.md:26`）
- 协议指纹的哈希只供构建和开发检查使用，不随握手、同步请求或设备资料发送，运行时也不比较哈希（`docs/peer-protocol-versioning.md:21`）
- 运行时只比较协议版本，相同继续配对、重连、路由和同步，不同返回明确的协议不兼容错误（`docs/peer-protocol-versioning.md:4`）
- 协议版本不匹配返回 `PEER_PROTOCOL_MISMATCH`，缺少协议声明返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`（`docs/peer-protocol-versioning.md:53`）
- 软件发布版本、厂商固件版本与协议版本各自独立，软件版本只用于展示，不参与兼容判断（`docs/peer-protocol-versioning.md:3`）
- 新协议实现文件必须加入 `sources`，不能只维护 DTO 而漏掉路由或同步行为（`docs/peer-protocol-versioning.md:19`）
- 指纹记录追加后，再次构建并执行 Core/Edge 互通回归，发布软件时无需再额外递增协议版本（`docs/peer-protocol-versioning.md:28`）
- CI 将版本记录与 PR/push 的基线比较，拒绝覆盖历史 hash、回退版本或不递增版本的修改（`docs/peer-protocol-versioning.md:39`）

## 关键符号

- `operit-host-api` — `core/crates/foundation/host-api` — 宿主能力 trait 与 `HostManager`（`core/CRATE_BOUNDARIES.md:9`）
- `operit-util` — `core/crates/foundation/util` — 共享工具代码与序列化器（`core/CRATE_BOUNDARIES.md:11`）
- `operit-model` — `core/crates/foundation/model` — 各层共用的数据结构（`core/CRATE_BOUNDARIES.md:13`）
- `operit-store` — `core/crates/persistence/store` — 持久化层（`core/CRATE_BOUNDARIES.md:15`）
- `operit-plugin-sdk` — `core/crates/plugin/sdk` — 可发布的插件契约（`core/CRATE_BOUNDARIES.md:17`）
- `operit-plugin-theme` — `core/crates/plugin/theme` — 与运行时无关的 theme v1 模式（`core/CRATE_BOUNDARIES.md:21`）
- `operit-tools` — `core/crates/tool/services` — 工具系统（`core/CRATE_BOUNDARIES.md:27`）
- `operit-local-models` — `core/crates/provider/local-model` — 本地模型清单与注册表契约（`core/CRATE_BOUNDARIES.md:31`）
- `operit-providers` — `core/crates/provider/services` — Provider 契约与内置实现（`core/CRATE_BOUNDARIES.md:34`）
- `operit-js-bridge` — `core/crates/plugin/javascript-bridge` — JavaScript 引擎集成（`core/CRATE_BOUNDARIES.md:38`）
- `operit-runtime` — `core/crates/runtime/application` — 父级编排 crate（`core/CRATE_BOUNDARIES.md:41`）
- `operit-proxy-local` — `core/crates/proxy/local` — 构建时代理生成与本地分发（`core/CRATE_BOUNDARIES.md:45`）
- `operit-link` — `core/crates/foundation/link` — 传输协议与客户端/服务端原语（`core/CRATE_BOUNDARIES.md:48`）
- `operit-edge-contract` — `edge/sdk/contract` — 共享的 Edge 服务地址与属性名（`core/CRATE_BOUNDARIES.md:49`）
- `operit-node-edge` — `edge/sdk/node` — 轻量设备侧 Edge Core 节点（`core/CRATE_BOUNDARIES.md:51`）
- `operit-command-core` — `core/crates/command/core` — CLI 命令层（`core/CRATE_BOUNDARIES.md:56`）
- `operit-node-runtime` — `core/crates/node/runtime` — 节点路由、空间运行时与同步，未列入 `CRATE_BOUNDARIES.md` 的 Crates 一节（`core/Cargo.toml:21`）
- `operit-peer-link` — `core/crates/node/peer-link` — 认证对等链接与传输，未列入 `CRATE_BOUNDARIES.md` 的 Crates 一节（`core/Cargo.toml:22`）
- `operit-data-rescue` — `core/crates/persistence/rescue` — 数据救援，未列入 `CRATE_BOUNDARIES.md` 的 Crates 一节（`core/Cargo.toml:8`）
- `operit-core-application` — `core/crates/application/core` — 把 runtime、proxy 与 node 组装成一棵 Core 树的组合根（`core/crates/application/core/Cargo.toml:2`）
- `operit-proxy-edge` — `edge/sdk/proxy` — Edge 服务的类型化投影（`core/CRATE_BOUNDARIES.md:181`）
- `ToolRuntimeSupport` — 工具侧对父级运行时的请求 trait（`core/crates/tool/services/src/runtime_support.rs:417`）
- `ProviderRuntimeSupport` — Provider 侧对父级运行时的请求 trait（`core/crates/provider/services/src/runtime_support.rs:281`）
- `LocalModelRuntimeSupport` — 本地模型侧对父级运行时的请求 trait（`core/crates/provider/local-model/src/runtime_support.rs:7`）
- `GitHubTokenSource` — 请求已登录 GitHub 账号访问令牌的 trait（`core/crates/provider/services/src/market/MarketStatsApiService.rs:512`）
- `JsExecutionHost` — JavaScript 到应用的执行边界 trait（`core/crates/plugin/sdk/src/javascript.rs:213`）
- `JsExecutionProvider` — 引擎 Provider 边界 trait（`core/crates/plugin/sdk/src/javascript.rs:435`）
- `JsPackageExecutor` — 绑定一个包运行时与执行宿主的 trait（`core/crates/plugin/sdk/src/javascript.rs:426`）
- `JsExecutionEngine` — ToolPkg 引擎操作 trait（`core/crates/plugin/sdk/src/javascript.rs:653`）
- `HostJsExecutionProvider` — `operit-js-bridge` 实现 `JsExecutionProvider` 的结构体（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:16`）
- `HostManager` — 活动宿主能力集与面向生命周期的宿主句柄（`core/crates/foundation/host-api/src/HostManager.rs:139`）

## 调用链

1. 子 crate 需要父级行为时，子 crate 定义 trait 并消费 trait 对象（`core/CRATE_BOUNDARIES.md:98`）
2. 父级 `operit-runtime` 实现该 trait，例如 `RuntimeToolSupport` 实现 `ToolRuntimeSupport`（`core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:137`）
3. 父级 `operit-runtime` 安装该 trait，例如 `RuntimeProviderSupport` 实现 `ProviderRuntimeSupport`（`core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:443`）
4. 按 trait 机制，子 crate 通过 trait 对象调用父级服务，不直接依赖 `operit-runtime` 的内部实现（`operit-node-runtime` 的 javascript 可选依赖除外，见不一致小节）（`core/CRATE_BOUNDARIES.md:98`）
5. 修改协议相关源码后运行 Cargo 构建，构建递归收集 `peer-protocol.json` 的 `sources` 算哈希（`docs/peer-protocol-versioning.md:10`）
6. 指纹变化时构建失败并打印新的 SHA-256，须在 `revisions` 末尾追加 version 递增的新记录（`docs/peer-protocol-versioning.md:26`）
7. 指纹记录追加后，再次构建并执行 Core/Edge 互通回归，发布软件时无需再额外递增协议版本（`docs/peer-protocol-versioning.md:28`）
8. 运行时只比较协议版本，版本不匹配返回 `PEER_PROTOCOL_MISMATCH`（`docs/peer-protocol-versioning.md:53`）

## 来源

- `core/CRATE_BOUNDARIES.md`
- `core/Cargo.toml`
- `core/crates/README.md`
- `core/peer-protocol.json`
- `docs/peer-protocol-versioning.md`
- `core/crates/foundation/util/Cargo.toml`
- `core/crates/foundation/model/Cargo.toml`
- `core/crates/persistence/store/Cargo.toml`
- `core/crates/plugin/sdk/Cargo.toml`
- `core/crates/plugin/theme/Cargo.toml`
- `core/crates/tool/services/Cargo.toml`
- `core/crates/provider/services/Cargo.toml`
- `core/crates/provider/local-model/Cargo.toml`
- `core/crates/plugin/javascript-bridge/Cargo.toml`
- `core/crates/runtime/application/Cargo.toml`
- `core/crates/node/runtime/Cargo.toml`
- `core/crates/proxy/local/Cargo.toml`
- `core/crates/command/core/Cargo.toml`
- `core/crates/application/core/Cargo.toml`
- `edge/sdk/contract/Cargo.toml`
- `edge/sdk/node/Cargo.toml`
- `edge/sdk/proxy/Cargo.toml`
- `core/crates/tool/services/src/runtime_support.rs`
- `core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs`
- `core/crates/provider/services/src/runtime_support.rs`
- `core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs`
- `core/crates/provider/local-model/src/runtime_support.rs`
- `core/crates/provider/services/src/market/MarketStatsApiService.rs`
- `core/crates/plugin/sdk/src/javascript.rs`
- `core/crates/tool/services/src/tools/AIToolHandler.rs`
- `core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs`
- `core/crates/foundation/host-api/src/HostManager.rs`
