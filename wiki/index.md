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

（待生成，大纲 v1 评审中）

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
