# Operit2-wiki 内容目录

> 每次条目合并时更新。每页一句话摘要。
> 大纲见 `outline/outline-v1.yaml`（v1 已批准，2026-11-11）。

## 定位与入门

- Operit2 是什么（`intro-overview`）：一句话定位是连接用户设备空间的 Agent 核心，面向个人用户，手机、桌面与云端设备各展所长。
- Operit2 不是什么（`intro-not-what`）：以 README 与架构文档原文划出的边界为准，不做引申。
- Preview 阶段与版本规则（`intro-preview`）：当前处于 Preview Release 阶段；版本格式、更新通道与 release notes 覆盖缺口。
- 第一次运行（`intro-quickstart`）：本机装环境、启动第一个 CoreNode、配对另一台设备、加入 Space、打开 Web Access 的完整路径。

## 架构总览

- 架构总览（`arch-overview`）：CoreNode、Space、Binding 三大概念与 29 个 Core crate 的分工总图。
- CoreNode 是什么（`arch-corenode`）：一个运行 Operit Core 的应用实例，由 OperitApplication、LocalCoreProxy 与 HostManager 组装。
- Space 是什么（`arch-space`）：节点成员、路由与持久化同步的范围，不是执行容器。
- Binding 是什么（`arch-binding`）：一个业务 key 的下一次路由执行由哪个 CoreNode 完成，不移动 Agent、对话与数据。
- 持久化同步（总览）（`arch-sync`）：同一 Space 内具备 storage.provide 的节点之间交换持久化操作与 Blob 的机制。
- 路由与 Binding（`arch-routing`）：一个聊天的下一步由哪个 CoreNode 执行，以及一条 Link 调用怎样逐跳到达那个节点。

## Core

- Core 总览与 crate 边界（`core-overview`）：11 个领域分组、29 个真 crate、依赖方向、父级行为 trait 机制与 peer-protocol.json。
- 基础层——共享契约与数据模型（`core-foundation`）：host-api 宿主能力契约、HostManager、model 聊天消息与模型目录、Link 协议层。
- 基础层——通用工具库（`core-foundation-util`）：日志器、文件分类与流框架，48 个公开模块清点与 3 个 full feature 门。
- 持久化——store 聚合 crate（`core-persistence-store`）：SQLite 连接与事务、节点身份、Binding、Space 成员与选路、偏好存储的同步与节点本地两种形态。
- 持久化——同步存储（`core-persistence-sync`）：操作日志、时钟、实体版本、blob、工作区清单、文件策略与偏好合并声明的存法。
- 持久化——数据救援（`core-persistence-rescue`）：不启动 Core/数据库，ZIP 归档加 manifest 校验后暂存发布。
- Provider——服务聚合（`core-provider-services`）：AIService 接口、ClaudeProvider 适配器、EnhancedAIService 对话编排与 ProviderRuntimeSupport 运行时支持。
- Provider——本地模型（`core-provider-local-model`）：已装模型与引擎注册表、清单结构、桌面 Sherpa STT/TTS 推理与 LocalModelRuntimeSupport。
- 工具系统——执行与注册（`core-tool-execution`）：解析、批处理、注册表、权限与 hook 的完整链路。
- 工具系统——包、技能与 MCP（`core-tool-packages-mcp`）：包工具执行、技能加载管理、MCP 接入调用与 JS 运行时。
- 插件——Plugin SDK（`core-plugin-sdk`）：ToolPkg 包模型与加载流程、Hook 挂载点、Compose DSL UI 声明、JS SDK 宿主契约。
- 插件——JS 桥（`core-plugin-js-bridge`）：JsEngine 实现 JsExecutionEngine，35 个同步与 12 个异步宿主绑定调宿主操作。
- 插件——主题 v1 契约（`core-plugin-theme`）：纯契约 crate，只做内存内校验，校验通过不等于安装与渲染安全。
- 插件——SDK 代码生成与 IPC（`core-plugin-codegen`）：SDK 声明树、JS 运行时、四语言客户端、注册契约与 sdk-ipc 通道及 36 行桥接器。
- Runtime 总览与 OperitApplication（`core-runtime`）：进程级运行时组装、启动生命周期、CORE_VERSION 与聊天消息管理。
- Runtime——业务服务（`core-runtime-services`）：ChatServiceCore 聊天管线、Provider/Tool 两座运行时支持桥、终端 PTY 服务。
- Runtime——数据与插件宿主（`core-runtime-data`）：Operit1 快照导入迁移、偏好导入分流、插件注册表与 ToolPkg 会话创建钩子桥。
- 节点——节点运行时（`core-node-runtime`）：CoreNodeRouter 本地/跨节点路由决策、SpaceRuntime 本地执行、持久化同步与 NodeSpaceService 准入。
- 节点——PeerLink 传输与路由宏（`core-node-peer-link`）：五载体传输契约与载体探测、mDNS 发现与重连、配对令牌桶节流、路由宏生成的包装器与路由元数据。
- 代理生成——扫描、发射器与本地代理运行时（`core-proxy`）：扫描从源码生成代理 IR，Rust 与 Dart 发射器分别生成分发代码与客户端，本地代理运行时分发调用与管理流。
- RsLink——Rust 间 Link 协议层（`core-rslink`）：值转换、路由调用、流与 watch、反向流、内嵌流与 codegen 共享 IR/类型解析。
- 应用组装——CoreApplication 门面（`core-application`）：runtime、proxy、node、access 四类 crate 组装成一棵 Core 树，Host 只拿公开句柄。
- 命令层——CLI 命令编排（`core-command`）：core crate 的命令入口、chat/model/tool/sync 四组命令与 OperitApplication 门面的关系。

## Agent 回路

（待生成，大纲 v1 评审中）

## 跨平台矩阵

（待生成，大纲 v1 评审中）

## 插件系统

（待生成，大纲 v1 评审中）

## 模型与 Provider

（待生成，大纲 v1 评审中）

## 多设备同步

（待生成，大纲 v1 评审中）

## UI 与主题

（待生成，大纲 v1 评审中）

## Edge 与厂商接入

（待生成，大纲 v1 评审中）

## 开发、排障与迁移

（待生成，大纲 v1 评审中）
