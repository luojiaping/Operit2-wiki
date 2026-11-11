---
title: Compose DSL 界面
module: plugins
platforms: [all]
sources: [core/crates/plugin/sdk/src/toolpkg/compose/README.md, core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslBridge.rs, core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslRuntimeScript.rs, plugins/types/compose-dsl.d.ts, plugins/tools/compile_compose_module.mjs]
date: 2026-11-11
---

## 概述

Compose DSL 是插件声明界面的方式：插件用 JavaScript 写屏幕函数，编译器把源码编译为 ABI 4 制品，制品包含不可变布局程序（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:9`）。
屏幕函数接收 `ComposeDslContext`，返回根节点树（`plugins/types/compose-dsl.d.ts:4956`）。
界面不直接展开为 JavaScript 节点，提交时以事务形式交给宿主渲染（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:21`）。
Flutter、CLI 与桌面共用同一套程序存储，CLI 与桌面消费者使用相同的程序存储与瞬时指令视图（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:35`）。
Web 使用相同的 Host 注册与 Compose 格式（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:98`）。

## AI 速览

- `ComposeDslScreen` — 接收 `ComposeDslContext` 并产出根节点树的屏幕渲染器（`plugins/types/compose-dsl.d.ts:4956`）
- `ComposeDslContext` 的 `UI` — 核心、Material 3 与宿主注册组件工厂的交集（`plugins/types/compose-dsl.d.ts:4810`）
- `ComposeNode` — 由 `type` 字段标识组件工厂的节点（`plugins/types/compose-dsl.d.ts:4191`）
- `ComposeNodeFactory` — 把组件属性与子节点编码为 `ComposeNode` 的工厂（`plugins/types/compose-dsl.d.ts:4210`）
- `compileComposeModule` — 在页面创建前提前编译可移植 JavaScript 的编译入口（`plugins/tools/compile_compose_module.mjs:10`）
- `useEffect` — 运行组合拥有的工作，并在依赖变化或处置时执行清理（`plugins/types/compose-dsl.d.ts:4834`）
- `useState` — 按键保留跨渲染的值，并返回调度更新的 setter（`plugins/types/compose-dsl.d.ts:4818`）
- `useMemo` — 按键复用计算值，直至依赖列表变化（`plugins/types/compose-dsl.d.ts:4830`）
- `lazyItems` — 用稳定条目键与固定主轴尺寸构建指定范围（`plugins/types/compose-dsl.d.ts:4814`）
- `ComposeTheme` — 读取与观察当前插件 UI 宿主已解析主题的服务（`plugins/types/compose-dsl.d.ts:4784`）
- 主入口：`compiler.artifact(source, identity)` 是 `compileComposeModule` 返回的编译结果（`plugins/tools/compile_compose_module.mjs:11`）（`plugins/tools/compile_compose_module.mjs:24`）。
- 数据流向：插件源码编译为布局程序，常规提交发出事务（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:21`）。

## 核心机制

### 声明界面

编译器产出 ABI 4 制品，制品包含不可变布局程序（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:9`）。
布局程序包含常量、动态参数、对象、数组、局部指令地址与数组拼接的指令操作数（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:10`）。
直接嵌套的 UI 调用共享同一个布局程序（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:12`）。
`ComposeDslScreen` 是接收 `ComposeDslContext` 并产出根节点树的屏幕渲染器（`plugins/types/compose-dsl.d.ts:4956`）。
`UI` 字段是核心、Material 3 与宿主注册组件工厂的交集，类型为 `ComposeDslContextUIIntersection`（`plugins/types/compose-dsl.d.ts:4810`）。
`ComposeUiFactoryRegistry` 提供通过 `ComposeDslContext::UI` 访问的核心组件工厂（`plugins/types/compose-dsl.d.ts:4383`）。
`ComposeNode` 由 `type` 与 `props` 字段组成，`type` 是宿主渲染器解析的组件工厂名（`plugins/types/compose-dsl.d.ts:4191`）。
`ComposeNode` 的 `children` 是在该元素内渲染的有序后代节点（`plugins/types/compose-dsl.d.ts:4199`）。
`ComposeNodeFactory` 把组件属性与子节点编码为 `ComposeNode`（`plugins/types/compose-dsl.d.ts:4210`）。
`h` 按组件名、属性与子节点构造原始 `ComposeNode`（`plugins/types/compose-dsl.d.ts:4950`）。
调用已编译 UI 表达式会声明一个源实例及其参数向量（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:17`）。
调用已编译 UI 表达式不把程序展开为 JavaScript 节点（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:20`）。
`useState` 按键保留跨渲染的值，并返回调度更新的 setter（`plugins/types/compose-dsl.d.ts:4818`）。
`useMutable` 按键保留可变值，并返回替换该值的回调（`plugins/types/compose-dsl.d.ts:4822`）。
`useRef` 按键返回跨重渲染保持当前值的稳定引用（`plugins/types/compose-dsl.d.ts:4826`）。
`useMemo` 按键复用计算值，直至依赖列表变化（`plugins/types/compose-dsl.d.ts:4830`）。
`lazyItems` 用稳定条目键与固定主轴尺寸构建指定范围，返回 `ComposeLazyItems`（`plugins/types/compose-dsl.d.ts:4814`）。
`ComposeLazyItems` 的 `content` 是带稳定条目标识的已物化节点数组（`plugins/types/compose-dsl.d.ts:3877`）。

### ctx.useEffect 的订阅与清理规则

`useEffect` 运行组合拥有的工作，并在依赖变化或处置时执行清理（`plugins/types/compose-dsl.d.ts:4834`）。
`useEffect` 的 `setup` 返回清理函数，签名是 `setup: () => () => void`（`plugins/types/compose-dsl.d.ts:4834`）。
`State.js` 与 `Lazy.js` 拥有 hook、memo 执行与有界列表窗口（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:48`）。
`Reactive.js` 跟踪词法依赖、源槽位与已调度的表达式执行（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:47`）。
Memo 与惰性条目执行保留其词法 hook 与订阅归属（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:72`）。
共享布局程序不合并独立的响应式执行及其 effect（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:74`）。
一个上下文拥有一个事件注册表（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:59`）。
已分离的源保留缓存的闭包，但其活动传输地址过期（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:61`）。
重新挂载会创建新的传输地址（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:62`）。
从活动源移除事件也会使其注册过期（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:62`）。
外部上下文不能仅因字符串 ID 恰好匹配就绑定回调（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:64`）。
宿主输入更新在同一命令内刷新当前根并执行 `onInputsChanged`（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:71`）。
`ComposeTheme` 的 `subscribe` 观察后续主题变化，并返回取消订阅函数（`plugins/types/compose-dsl.d.ts:4788`）。

### 页面资源快照机制

`Theme.js`、`WebView.js` 与 `Host.js` 绑定宿主快照、控制器操作与宿主能力（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:49`）。
`ComposeThemeSnapshot` 包含 `brightness` 与 `colors`，`colors` 是以 CSS RRGGBBAA 十六进制字符串编码的已解析 Material 颜色角色（`plugins/types/compose-dsl.d.ts:4765`）。
`ComposeTheme` 的 `getCurrent` 返回当前已解析主题，在没有 UI 宿主提供主题时抛出错误（`plugins/types/compose-dsl.d.ts:4784`）。
`ComposeTheme` 的 `subscribe` 观察后续主题变化，并返回取消订阅函数（`plugins/types/compose-dsl.d.ts:4788`）。
被显式编辑隐藏的参数不在传输快照中保留已移除源地址（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:27`）。
`ComposeLazyViewport` 的 `contentRevision` 在插件内容变化时使已测量的占位尺寸失效（`plugins/types/compose-dsl.d.ts:3843`）（`plugins/types/compose-dsl.d.ts:3851`）。
`ComposeLazyViewport` 是所属 Flutter 列表的视口元数据（`plugins/types/compose-dsl.d.ts:3885`）。
有限的 CLI 与桌面快照使用相同二进制格式显式物化其视图（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:96`）。
Flutter 从该缓冲投影索引容器，而不解码第二棵参数树（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:95`）。
公开节点句柄为显式读取 `props`、`children`、`slots` 或 `type` 的插件暴露惰性指令视图（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:25`）。
对公开节点句柄的赋值产生局部字段补丁，局部变更校验是原子的（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:26`）。

### 修订号机制

事务记录的形状是 `[reset, revision, rootInstance, rootNode, programs, instances, removed]`（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:85`）。
一个命令拥有其响应接收端与完成修订号（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:66`）。
未变化的中间结果不分配修订号，成功的最终响应保持连续的修订号（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:67`）。
中间更新在最终响应前完成（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:66`）。
渲染、校验与动作失败会传播到所属命令（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:69`）。
常规提交遍历源成员关系，发出包含 `programs`、`instances`、显式补丁与已移除源 ID 的事务（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:21`）。
每个布局程序在每个会话中只宣告一次（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:22`）。
Flutter 对每个布局程序只安装与校验一次（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:30`）。
`Composition.js` 拥有源参数、引用成员关系、显式编辑与原子修订（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:44`）。
32 字节 CPB1 头存储版本、已用长度、阶段、事务地址、可选动作结果地址与导航地址（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:82`）。
值使用对齐的 16 字节描述符、小端字段与 UTF-16 字符串存储（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:83`）。

## 关键符号

- `compileComposeModule` — 在页面创建前提前编译可移植 JavaScript，不执行插件代码（`plugins/tools/compile_compose_module.mjs:10`）
- `compileComposeModule` 的 `TypeError` — `source` 与 `identity` 均为非空字符串的要求，违反时抛出（`plugins/tools/compile_compose_module.mjs:12`）
- `OperitComposeCompiler` — 首次使用时在 vm 上下文中装入解析器、制品与编译器源后缓存的编译器（`plugins/tools/compile_compose_module.mjs:22`）
- `compiler.artifact(source, identity)` — `compileComposeModule` 返回的编译结果（`plugins/tools/compile_compose_module.mjs:11`）（`plugins/tools/compile_compose_module.mjs:24`）
- `readComposeDslParserSource` — 返回与 facade 同一份构建清单中的受信任的仅源解析器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslBridge.rs:3`）
- `buildComposeDslParserDefinition` — 把同步源提供方注入解析器 facade（`core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslBridge.rs:7`）
- `buildComposeDslCompilerDefinition` — 组装独立宿主执行器与离线测试用的唯一源编译器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslBridge.rs:13`）
- `buildComposeDslContextBridgeDefinition` — 安装页面执行模块，不含解析器或源降级代码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslBridge.rs:21`）
- `buildComposeDslRuntimeWrappedScript` — 附加会话与动作入口点，不插值 JavaScript 大括号（`core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslRuntimeScript.rs:3`）
- `ComposeDslScreen` — 接收 `ComposeDslContext` 并产出根节点树的屏幕渲染器（`plugins/types/compose-dsl.d.ts:4956`）
- `ComposeDslContextUIIntersection` — 把核心工厂注册表、Material 3 生成注册表与通用节点工厂记录合并为一个类型（`plugins/types/compose-dsl.d.ts:547`）
- `ComposeUiFactoryRegistry` — 通过 `ComposeDslContext::UI` 访问的核心组件工厂（`plugins/types/compose-dsl.d.ts:4383`）
- `ComposeNode` — 由 `type` 字段标识组件工厂的节点（`plugins/types/compose-dsl.d.ts:4191`）
- `ComposeNodeFactory` — 把组件属性与子节点编码为 `ComposeNode` 的工厂（`plugins/types/compose-dsl.d.ts:4210`）
- `h` — 按组件名、属性与子节点构造原始 `ComposeNode`（`plugins/types/compose-dsl.d.ts:4950`）
- `useState` — 按键保留跨渲染的值，并返回调度更新的 setter（`plugins/types/compose-dsl.d.ts:4818`）
- `useEffect` — 运行组合拥有的工作，并在依赖变化或处置时执行清理（`plugins/types/compose-dsl.d.ts:4834`）
- `useMemo` — 按键复用计算值，直至依赖列表变化（`plugins/types/compose-dsl.d.ts:4830`）
- `lazyItems` — 用稳定条目键与固定主轴尺寸构建指定范围（`plugins/types/compose-dsl.d.ts:4814`）
- `ComposeLazyViewport` 的 `contentRevision` — 在插件内容变化时使已测量的占位尺寸失效（`plugins/types/compose-dsl.d.ts:3843`）（`plugins/types/compose-dsl.d.ts:3851`）
- `ComposeThemeSnapshot` — 包含 `brightness` 与 `colors` 的主题快照（`plugins/types/compose-dsl.d.ts:4765`）
- `ComposeTheme` 的 `getCurrent` — 返回当前已解析主题，在没有 UI 宿主提供主题时抛出错误（`plugins/types/compose-dsl.d.ts:4784`）
- `ComposeTheme` 的 `subscribe` — 观察后续主题变化，并返回取消订阅函数（`plugins/types/compose-dsl.d.ts:4788`）
- `sources.json` — Rust SDK 构建与 `tools/runtime/compose_scripts.mjs` 使用的有序源清单（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:3`）
- `Compiler.js`、`Parser.js` 与 `Artifact.js` — 把源码编译为共享程序并强制执行制品 ABI 4（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:42`）
- `Composition.js` — 拥有源参数、引用成员关系、显式编辑与原子修订（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:44`）
- `Reactive.js` — 跟踪词法依赖、源槽位与已调度的表达式执行（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:47`）
- `State.js` 与 `Lazy.js` — 拥有 hook、memo 执行与有界列表窗口（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:48`）
- `Theme.js`、`WebView.js` 与 `Host.js` — 绑定宿主快照、控制器操作与宿主能力（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:49`）
- `tools/tests/compose_dsl_*.test.mjs` — 覆盖编译、执行、归属、变更与事务行为（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:106`）

## 调用链

1. 插件调用 `compileComposeModule(source, identity)`，该函数在页面创建前提前编译可移植 JavaScript，不执行插件代码（`plugins/tools/compile_compose_module.mjs:10`）。
2. 编译器在 vm 上下文中装入解析器、制品与编译器源，并返回 `compiler.artifact(source, identity)`（`plugins/tools/compile_compose_module.mjs:24`）。
3. Rust 侧用 `buildComposeDslCompilerDefinition` 组装独立宿主执行器与离线测试用的唯一源编译器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslBridge.rs:13`）。
4. Rust 侧用 `buildComposeDslContextBridgeDefinition` 安装页面执行模块，不含解析器或源降级代码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslBridge.rs:21`）。
5. `buildComposeDslRuntimeWrappedScript` 为运行时脚本附加会话与动作入口点（`core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslRuntimeScript.rs:3`）。
6. 页面运行时通过宿主接收准备好的 SDK 脚本，不自行读取该目录（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:4`）。
7. 屏幕函数 `ComposeDslScreen` 接收 `ComposeDslContext` 并产出根节点树（`plugins/types/compose-dsl.d.ts:4956`）。
8. `h` 按组件名、属性与子节点构造原始 `ComposeNode`（`plugins/types/compose-dsl.d.ts:4950`）。
9. 调用已编译 UI 表达式声明源实例及其参数向量，构造时归一化动态值并绑定实例拥有的事件（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:17`）。
10. 常规提交发出包含 `programs`、`instances`、显式补丁与已移除源 ID 的事务（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:21`）。
11. Compose 只发送 `Uint8Array`，宿主注册接受普通结构化参数或顶层自有字节缓冲（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:90`）。
12. Rust 校验头部并独立读取应用结果与导航，更新通过 `CoreBuffer` 与 `CoreLink` 附件保留原始缓冲（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:93`）。
13. Flutter 对每个布局程序只安装与校验一次（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:30`）。
14. Flutter 从该缓冲投影索引容器，而不解码第二棵参数树（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:95`）。
15. 一个命令拥有其响应接收端与完成修订号，未变化的中间结果不分配修订号（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:66`）。
16. Web 使用相同的 Host 注册与 Compose 格式，其 Host 在把字节复制进 Wasm 内存前转移 JS 分配（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:98`）。
17. 有限的 CLI 与桌面快照使用相同二进制格式显式物化其视图（`core/crates/plugin/sdk/src/toolpkg/compose/README.md:96`）。

相关条目：[[plugin-toolpkg-overview|ToolPkg 概览]]、[[plugin-js-wasm-runtime|JS/Wasm 运行时]]。

## 来源

- `core/crates/plugin/sdk/src/toolpkg/compose/README.md`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslBridge.rs`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgComposeDslRuntimeScript.rs`
- `plugins/types/compose-dsl.d.ts`（生成文件，只引用、不展开）
- `plugins/tools/compile_compose_module.mjs`
