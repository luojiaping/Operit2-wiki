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
