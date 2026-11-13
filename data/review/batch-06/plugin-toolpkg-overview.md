---
title: ToolPkg 2.0.0 总览
module: plugins
platforms: [all]
sources: [plugins/README.md, plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md, plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md, docs/toolpkg-runtime.md]
date: 2026-11-11
---

## 概述

ToolPkg 是 Operit 项目中用于打包和分发工具包的标准格式（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:11`）。
`.toolpkg` 文件本质上是一个标准的 ZIP 压缩包，内含一个清单文件（`manifest`）和相关的资源文件（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:15`）。
ToolPkg 支持将多个功能相关的子包（`subpackages`）组织在一起，支持打包二进制资源、脚本文件和 UI 模块（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:13`）。
本指南中的包名和目录树是格式示例，具体 API 以 PackageBuilder 的当前版本 `types/` 为准（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:9`）。
对照说明：Agent Plugins 1.0 的可移植子集（`plugin.json`、`mcp.json`）在 Operit2 基线全仓无对应实现，本页仅作对照，不将其写作 Operit2 已实现的功能；核验方法见“来源”小节。

## AI 速览

- `ToolPkg` — 打包和分发工具包的标准格式（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:11`）
- `api_version` — ToolPkg API 契约版本，Operit2 新建包显式填写 `2.0.0`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:173`）
- `schema_version` — 清单格式版本，当前为 `1`，不是 ToolPkg API 版本（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:172`）
- `version` — 插件自身的发布版本，与 `api_version`、`schema_version` 分别声明（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:175`）
- `toolpkg_id` — 包的唯一标识符，建议使用反向域名格式（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:174`）
- `main` — ToolPkg 主入口脚本路径，用于执行注册函数（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:177`）
- `registerToolPkg` — 包注册函数，在独立的临时 JavaScript engine 中执行，60 秒期限仅为格式指南要求，注册链路实际不执行该期限，详见“注册与执行上下文”一节（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:467`）
- `ToolPkg.ipc` — 跨上下文共享状态与调用能力的显式通道（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:574`）
- `ToolPkg.wasm.call` — 调用 native WASM runtime 的导出函数，当前 ABI 支持 `i32`、`i64`、`f32`、`f64` 标量参数和返回值（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:309`）
- `ToolPkg.getConfigDir` — 包配置目录，在模块顶层、`registerToolPkg()` 内和执行期间均可用（`docs/toolpkg-runtime.md:95`）
- `ToolPkg.route` — 路由装饰器，`binding` 是包含现有 Core Binding key 的参数的从零开始的位置（`docs/toolpkg-runtime.md:18`）
- `installation_scope` — 固定安装范围为 `device` 或 `space`（`docs/toolpkg-runtime.md:3`）
- 主入口函数是 `registerToolPkg`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:467`）

## 核心机制

### API 版本关系

Operit2 当前支持的 ToolPkg API 版本是 `2.0.0`，面向多平台开发（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:27`）。
Operit2 对 `1.0.0`、`1.0.1` 的旧版兼容加载支持并不完整，需要逐项验证（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:28`）。
Operit1 完整支持 ToolPkg API `1.0.0` 和 `1.0.1`，这两个版本主要面向 Android，是旧版 API 形式（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:29`）。
接受某个版本号、成功导入包和完整支持该版本的接口是不同的事情（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:38`）。
旧包迁移不能只改版本号，还需检查接口、路径与平台行为（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:38`）。
解析器接受旧版本号不等于完整实现旧接口，旧包需要逐项验证所用能力，不能仅凭导入成功宣称兼容（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:9`）。
ToolPkg API `2.0.0` 基本所有公共接口都通过统一 host 能力提供跨平台兼容（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:40`）。
作者遇到平台特异接口时须明确其适用范围，不能把某个平台的专用能力当作所有平台都具备的接口（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:40`）。

### 三个版本号

`schema_version` 是清单格式版本，当前为 `1`，不是 ToolPkg API 版本（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:172`）。
`api_version` 是 ToolPkg API 契约版本，Operit2 新建包显式填写 `2.0.0`，省略时按旧版 `1.0.0` 契约加载，启用对应适配和运行依赖（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:173`）。
`version` 是插件自身的发布版本，建议使用语义化版本，与 `api_version`、`schema_version` 分别声明（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:175`）。
`schema_version` 表示清单格式版本，`api_version` 表示 ToolPkg API 契约，`version` 表示插件自身的发布版本，三者不能混用（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:13`）。

### 三类包的打包区别

`packages/buildin/` 是打包为内置插件的 ToolPkg 源码（`plugins/README.md:8`）。
`packages/external/` 是随应用打包、由用户从 "more plugins" 加载的官方捆绑 ToolPkg 源码（`plugins/README.md:9`）。
`packages/examples/` 是用于开发和手动测试的示例 ToolPkg 源码（`plugins/README.md:10`）。
`packages/buildin/`、`packages/external/`、`packages/examples/` 使用相同的源码布局，区别是打包方式：`buildin` 作为当前内置插件加载，`external` 作为可选官方插件捆绑，`examples` 保留为开发示例（`plugins/README.md:17`）。
`packages/external/image_workbench/` 提供可选的官方 Image Workbench，从 "more plugins" 提供，默认禁用（`plugins/README.md:14`）。
主仓库内置与 external 资源同步脚本是 `plugins/tools/sync_plugin_packages.py`，同步更新 `core/crates/runtime/application/assets/plugins/buildin/` 与 `external/`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:830`）。
内置资源同步服务于应用资源构建，不等于向正在运行的应用安装插件（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:830`）。

### 注册与执行上下文

清单文件是 `manifest.json` 或 `manifest.hjson`，定义包的元数据和结构（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:68`）。
`main` 是 ToolPkg 主入口脚本路径（相对于 ZIP 根目录），用于执行注册函数（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:177`）。
`subpackages` 是子包列表，每个子包是一个独立的工具集（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:180`）。
子包脚本必须包含 `METADATA` 注释块（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:242`）。
子包脚本中定义的工具会被注册为 `<subpackage_id>:<tool_name>` 格式（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:243`）。
子包的 `enabled_by_default` 表示是否默认启用，默认为 `false`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:236`）。
每个 ToolPkg 的 `registerToolPkg()` 在独立的临时 JavaScript engine 中执行，注册状态不会跨包共享（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:467`）。
格式指南要求主脚本注册在 60 秒内完成，并要求终止同步死循环和超过时限的异步注册（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:467`）。
注册链路实际未执行该期限：注册执行传入的中断参数是 `HostJavaScriptExecutionInterrupt::unlimited()`，即无截止时间（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:582`）。
注册期间禁止调用 `ToolPkg.readResource(...)` 和 `ToolPkg.wasm.call(...)`，调用会立即抛出异常（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:467`）。
`ToolPkg.registerToolboxUiModule` 注册 UI 模块，`runtime` 默认 `compose_dsl`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:473`）。
`ToolPkg.registerUiRoute` 注册 UI 路由，不填 `route` 或 `routeId` 时宿主按 `toolpkg:<toolpkg_id>:ui:<id>` 自动生成稳定路由 ID（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:479`）。
`ToolPkg.registerNavigationEntry` 的挂载面 `surface` 支持 `toolbox`、`main_sidebar_plugins`、`app_bar`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:486`）。
`ToolPkg.registerAppLifecycleHook` 的 `event` 字段是生命周期事件名（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:499`）。
`ToolPkg.registerAppLifecycleHook` 支持的 `event` 包括 `application_on_create`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:511`）。
`ToolPkg.registerDesktopWidget` 是桌面小部件注册接口（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1405`）。
ToolPkg 运行时按执行来源分为 `main`、`ui`、`sandbox`、`provider` 四类上下文（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:536`）。
同一个 ToolPkg 容器共用一个包级 JS engine，`main` 上下文的内部 context key 形如 `toolpkg_main:<toolpkg_id>`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:536`）。
每个 UI route、widget、XML render 实例有自己的 JS engine（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:537`）。
ToolPkg main 上下文导入一次、UI 上下文再导入一次同一模块时，`count` 是两份，模块顶层变量不会自动跨上下文共享（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:572`）。
跨上下文共享状态或调用能力时显式使用 `ToolPkg.ipc`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:574`）。
`ToolPkg.ipc.call(channel, payload)` 的语义是非 main 上下文调用同包 ToolPkg main，main 上下文调用本地 handler（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:621`）。
`ToolPkg.ipc` 的 `payload` 和返回值使用 JSON 可序列化数据，包括字符串、数字、布尔值、数组、普通对象和 `null`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:623`）。
UI 模块通过 `ToolPkg.readResource(key)` 访问资源（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:664`）。
目录资源在 `ToolPkg.readResource(key)` 时先被压缩成 zip，再返回这个 zip 的临时文件路径（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:667`）。
`ToolPkg.wasm.call(moduleId, exportName, args)` 已接入 native WASM runtime，当前 ABI 支持 `i32`、`i64`、`f32`、`f64` 标量参数和返回值（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:309`）。
`i64` 结果以字符串返回，JS 传入 `i64` 时建议使用字符串，避免超过 JS safe integer 后丢精度（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:310`）。
Java/Kotlin Bridge 仅适用于已提供 Java Bridge 的 host，不代表所有宿主都具备 Java 或 Android 类（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:937`）。

### 安装范围与远程路由

manifest 可以用 `"installation_scope": "device"` 或 `"installation_scope": "space"` 固定安装范围，固定范围的包不能安装或移动到另一范围（`docs/toolpkg-runtime.md:3`）。
Device 安装拥有本地数据，Space 安装拥有同步数据（`docs/toolpkg-runtime.md:5`）。
Goal 和 Plan 都要求 `space` 安装，状态保存在各自的数据库中，与聊天工作区无关（`docs/toolpkg-runtime.md:5`）。
包环境变量属于安装所有者，包括其全部子包；Space 安装同步这些配置快照，device 安装保留在本地（`docs/toolpkg-runtime.md:7`）。
只有 `space` 安装的包才能对外暴露远程实现（`docs/toolpkg-runtime.md:37`）。
`@ToolPkg.route({ binding: 0 })` 装饰的方法可被路由，`binding` 是包含现有 Core Binding key 的参数的从零开始的位置（`docs/toolpkg-runtime.md:18`）。
示例用 `ToolPkg.getSpaceDataDir()` 拼接 `goals.sqlite` 路径打开 Space 数据目录下的数据库（`docs/toolpkg-runtime.md:21`）。
`ToolPkg.getConfigDir()` 在模块顶层、`registerToolPkg()` 内和执行期间均可用（`docs/toolpkg-runtime.md:95`）。
只有 `submit_requested` 和 pre-hooks 共享一个总期限，默认 10 秒，可在高级工具设置中配置为 1 至 60 秒（`docs/toolpkg-runtime.md:128`）。
`Tools.Files.write(path, content, append)` 返回 `FileApplyResultData`，与 `toolCall("write_file", ...)` 相同（`docs/toolpkg-runtime.md:85`）。

### 同 ID 更新与打包

通过 `Tools.Files.zip(sourceVfsPath, artifactVfsPath, false)` 创建不含外层目录的归档，第三个参数 `false` 保证 manifest 位于归档根目录（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:814`）。
当前 `package import` 拒绝已注册的同名包，不提供覆盖安装或通用热更新（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1360`）。
同 ID 更新是用户明确授权后的替换操作：先删除已安装版本再重新导入，不是失败后的自动处理（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:103`）。
同 ID 更新时调用 `["package", "delete", "<package_id>"]`，确认删除成功，只对本次要更新的外部包执行该操作（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:107`）。

## 关键符号

- `schema_version` — 清单格式版本，当前为 `1`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:172`）
- `api_version` — ToolPkg API 契约版本（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:173`）
- `version` — 插件自身的发布版本（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:175`）
- `toolpkg_id` — 包的唯一标识符（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:174`）
- `main` — 主入口脚本路径（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:177`）
- `subpackages` — 子包列表（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:180`）
- `enabled_by_default` — 子包是否默认启用（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:236`）
- `METADATA` — 子包脚本必需的注释块（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:242`）
- `registerToolPkg` — 包注册函数（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:467`）
- `ToolPkg.registerToolboxUiModule` — 注册 UI 模块（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:473`）
- `ToolPkg.registerUiRoute` — 注册 UI 路由（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:478`）
- `ToolPkg.registerNavigationEntry` — 注册导航入口（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:484`）
- `ToolPkg.registerDesktopWidget` — 注册桌面小部件（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:490`）
- `ToolPkg.registerAppLifecycleHook` — 注册应用生命周期钩子（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:498`）
- `ToolPkg.registerMessageProcessingPlugin` — 注册消息处理插件（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:501`）
- `ToolPkg.registerXmlRenderPlugin` — 注册 XML 渲染插件（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:503`）
- `ToolPkg.registerInputMenuTogglePlugin` — 注册输入菜单开关插件（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:506`）
- `ToolPkg.ipc` — 跨上下文通道（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:574`）
- `ToolPkg.readResource` — 读取资源（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:664`）
- `ToolPkg.wasm.call` — 调用 WASM 导出函数（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:309`）
- `installation_scope` — 固定安装范围为 `device` 或 `space`（`docs/toolpkg-runtime.md:3`）
- `ToolPkg.getSpaceDataDir` — Space 数据目录（`docs/toolpkg-runtime.md:21`）
- `ToolPkg.getConfigDir` — 包配置目录（`docs/toolpkg-runtime.md:95`）
- `ToolPkg.route` — 路由装饰器（`docs/toolpkg-runtime.md:18`）
- `FileApplyResultData` — 文件写回执（`docs/toolpkg-runtime.md:85`）
- `submit_requested` — 与 pre-hooks 共享总期限的提交事件（`docs/toolpkg-runtime.md:128`）
- `sync_plugin_packages.py` — 主仓库内置与 external 资源同步脚本（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:818`）
- `types/` — 从 Rust SDK 生成的当前 v2 TypeScript 声明（`plugins/README.md:3`）
- `types-v1/` — 独立手写的 v1 声明快照（`plugins/README.md:6`）

## 调用链

1. 具体 API 以 PackageBuilder 的当前版本 `types/` 为准，包名和目录树是格式示例（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:9`）。
2. `Tools.Files.zip(sourceVfsPath, artifactVfsPath, false)` 创建不含外层目录的 .toolpkg 归档，`manifest` 位于归档根目录（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:814`）。
3. 用户在包管理中执行 package import 导入成品，再执行 package enable 启用包（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:86`）。
4. `registerToolPkg()` 在独立的临时 JavaScript engine 中执行注册，60 秒期限仅为格式指南要求，注册链路实际不执行该期限，详见“注册与执行上下文”一节（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:467`）。
5. 子包工具按 `<subpackage_id>:<tool_name>` 注册（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:243`）。
6. `ToolPkg.registerToolboxUiModule` 与 `ToolPkg.registerUiRoute` 注册 UI 模块与路由（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:473`）。
7. 运行时按 `main`、`ui`、`sandbox`、`provider` 分发执行上下文（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:536`）。
8. 跨上下文共享状态或调用能力时显式使用 `ToolPkg.ipc`（`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:574`）。
9. 只有 `submit_requested` 和 pre-hooks 共享一个总期限，默认 10 秒（`docs/toolpkg-runtime.md:128`）。
10. 超时终止所属 hook，报告错误并中止依赖操作（`docs/toolpkg-runtime.md:131`）。

## 来源

- plugins/README.md
- plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md
- plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md
- docs/toolpkg-runtime.md

对照核验：2026-11-11 对基线仓库（AAswordman/Operit2 @ 364d1d594）全仓 grep，`plugin.json` 与 `mcp.json` 零命中；`Agent Plugins 1.0` 在 plugins/ 与 docs/ 中零提及。
