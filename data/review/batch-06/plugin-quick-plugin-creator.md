---
title: QuickPluginCreator（App 内现场生成插件）
module: plugins
platforms: [all]
sources: [apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart, apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart, plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md]
date: 2026-11-11
---

## 概述

`QuickPluginCreatorDialog` 是实现包管理里“快速创作你的插件”入口的 `StatefulWidget` 对话框（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:9`）。
该入口只做准备工作，不自动生成源码、不自动配置编译器，也不自动安装或发布成品（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:17`）。
准备完成后需求作为聊天草稿填入输入框，用户发送后才开始与 AI 协作开发（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:17`）。
现场开发出的插件按本文“首次安装与测试”“同 ID 的修改与重新安装”“发布与交付”三节的流程处理，步骤通过 `operit_editor` 工具或系统工具 `execute_cli_command` 执行（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:82`）。
相关条目：[[plugin-toolpkg-overview|ToolPkg 2.0.0 总览]]、[[plugin-skills|Skills 机制]]。

## AI 速览

- `QuickPluginCreatorDialog` — 需求对话框（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:9`）
- `show` — 打开需求对话框并返回确认后的开发需求（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:16`）
- `runQuickPluginCreatorSetup` — 准备创作资源并核验编辑器状态（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:22`）
- `QuickPluginCreatorSetupResult` — 准备结果（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:6`）
- `ensureQuickPluginCreatorSkillVisible` — 确保创作 Skill 对 AI 可见（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:28`）
- `enablePackage` — 启用 `operit_editor`（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:31`）
- `isPackageEnabled` — 复核 `operit_editor` 的真实启用状态（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:34`）
- `operit_editor` — 平台编辑工具包，开发期执行包命令的入口（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`）
- `PackageBuilder` — 插件创作 Skill，随包携带当前版本 `types/`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:9`）
- `api_version` — 新建 ToolPkg 显式声明 `2.0.0`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:9`）
- 主入口函数是 `show`（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:16`）
- 数据流向：用户输入需求 → 确认时准备资源 → 需求填为聊天草稿 → 用户发送后开始与 AI 协作开发（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:17`）
- 准备成功后对话框返回需求字符串（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:72`）

## 核心机制

### 入口实际做什么

对话框标题是“快速创作你的插件”（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:81`）。
需求输入框是多行文本框，最少 4 行、最多 8 行（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:98`）。
需求输入框的 `hintText` 举例“做一个可以批量整理下载目录图片并生成索引的工具”（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:102`）。
需求输入为空时，对话框把 `_requirementError` 置为“请先输入插件需求”并阻止确认（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:53`）。
输入内容变化时若已有错误提示则清除 `_requirementError`（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:106`）。
确认时调用 `runQuickPluginCreatorSetup` 准备创作资源（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:61`）。
准备进行中确认按钮与取消按钮均被禁用，确认按钮显示 `M3LoadingIndicator`（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:130`）。
取消按钮点击后调用 `Navigator.pop` 关闭对话框（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:125`）。
确认按钮文案是“准备并前往聊天”（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:133`）。
准备失败时对话框不关闭，停留在当前界面（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:65`）。
准备失败时对话框在输入框下方以错误色显示 `setupResult` 的 `error`（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:116`）。
准备成功后对话框返回需求字符串（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:72`）。
对话框正文写明确认后准备并开放 `PackageBuilder` Skill、启用 `operit_editor` 平台编辑工具包，然后跳转聊天并填入需求草稿（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:92`）。
对话框正文写明发送草稿后才开始开发，本操作不会自动生成、安装或发布插件（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:92`）。

### 与 PackageBuilder、operit_editor 的关系

`runQuickPluginCreatorSetup` 接收 `GeneratedCoreProxyClients` 并返回 `QuickPluginCreatorSetupResult`（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:22`）。
`QuickPluginCreatorSetupResult` 承载准备结果，字段为 `success`、`skillName`、`packageResult`、`error`（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:8`）。
准备流程先调用 `skillRepository` 的 `ensureQuickPluginCreatorSkillVisible`（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:28`）。
准备流程接着调用 `packageManager` 的 `enablePackage` 启用 `operit_editor`（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:31`）。
启用后调用 `packageManager` 的 `isPackageEnabled` 复核 `operit_editor` 的真实启用状态（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:34`）。
复核未启用时抛出 `StateError`，提示 `operit_editor` 未启用、插件创作准备未完成（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:36`）。
复核通过后调用 `ToolPkgCatalogChangeBus` 的 `notifyCatalogChanged` 通知目录变更（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:38`）。
成功结果的 `skillName` 取自 `skill` 的 `name`，`packageResult` 取自启用调用的返回值（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:41`）。
准备流程捕获异常并返回 `success` 为 `false`、`error` 为异常字符串的结果（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:46`）。
文档说明包管理中的“快速创作你的插件”会安装 `PackageBuilder`、将它设为 AI 可见，并启用 `operit_editor`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:17`）。
当前创作准备流程会复用已经安装的 `PackageBuilder`，不会自动覆盖它的附件（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:34`）。
更新应用资源不会同步改写用户已安装的 `Skill`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:34`）。
要使用当前版本的内置资料，先核对 `["skill", "show", "PackageBuilder"]` 返回的目录并备份用户修改，获得用户确认后执行（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:36`）。
更新内置资料的四步是删除、加载、设为可见、再查看 `PackageBuilder`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:41`）。
更新资料时逐项核验结果及 references/types/examples 文件，不删除其他 `Skill`；任一步失败停止并报告（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:45`）。
已有安装不应被描述成“已经自动更新为当前资料”（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:45`）。
`operit_editor` 的 `operit_editor` 工具实际调用 `Tools.SoftwareSettings.exec(args)`，与系统工具 `execute_cli_command` 使用同一 core command 执行入口（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`）。
该调用返回真实命令结果并传播执行错误（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`）。
传入 `args` 是 CLI 字符串数组，也接受数组的 JSON 字符串，不含 `operit2` 可执行文件名（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`）。
自然语言 `query` 已移除，不会被转换成编辑动作（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`）。
Core command 与终端 shell 是不同的执行入口，不要假定终端已安装 `operit2` 命令（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`）。
空 `args` 数组从实际执行入口读取帮助，需要包命令帮助时传入 `["package", "help"]`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:30`）。
修改用户配置、启停包或 `MCP`、删除资源前取得用户确认，执行后重新读取状态核验（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:30`）。
不能把命令已调用当作修改成功（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:30`）。

### 确定开发目录与编写构建

开发前调用 `execute_cli_command` 传入 `["skill", "show", "PackageBuilder"]` 读取 `Skill` 的真实目录与附件位置（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:49`）。
`get_terminal_info` 对应脚本内的 `Tools.System.terminal.info()`，根据 host 返回的 `terminalType` 和可用终端信息使用正确的 shell 语法（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:50`）。
`get_terminal_info` 不返回下载目录或开发目录（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:50`）。
在已选定的终端会话中查询实际工作目录及工具版本，确定用户同意使用的可写目录，记为 `<dev_root>`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:51`）。
路径或工具不可用时报告具体原因并停止，不猜目录、不改用另一套执行入口（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:51`）。
`Tools.Files` 接收 `VFS` 路径，终端和 `package import` 需要各自 host 可读的路径（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:52`）。
`VFS` 路径、终端路径与 `FileSystemHost` 路径不能仅凭相同字符串认定指向同一文件，核对真实文件内容与路径映射后再使用（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:52`）。
`["package", "dir"]` 返回的是安装存储目录，不是源码开发目录（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:54`）。
host paths 和 host capabilities 当前并未通过 core command 暴露（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:54`）。
开发目录在 `<dev_root>/` 下组织 `types/` 与 `<package_id>/` 子目录（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:61`）。
成品放在 `artifacts/`，位于源码目录之外，避免打包包含自身（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:67`）。
包 id 确定后保持不变，继续开发时先定位原始源码，安装成品不能被当作完整源码项目（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:70`）。
确认包内的 `.ts`、`tsconfig.json`、资源与 `dist/` 是否齐全，说明缺失项，不凭空声称已经恢复项目（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:70`）。
完整复制 `Skill` 的 `types/`，不从旧仓库或云端下载另一版声明，项目通过 `../types` 引用声明（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:74`）。
位于 `src/` 的三斜线引用是 `../../types/index.d.ts`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:74`）。
`TypeScript` 输出可读的 `CommonJS` `JavaScript`，`Compose` UI 保留 `ctx.UI.*` 界面声明和回调，由运行时完成 `Compose` 编译与缓存（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:75`）。
按实际 shell 执行项目已声明的构建命令，检查退出码、超时状态和真实输出文件；没有可用编译器时说明环境未准备完成（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:75`）。
网络、文件与终端操作使用 `Tools.Network`、`Tools.Files`、`Tools.System.terminal` 及其 host API（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:76`）。
声明文件的存在不代表当前 host 实现了所有能力（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:76`）。
单文件脚本包保留 `METADATA` 与导出函数，`ToolPkg` 在归档根目录放置 `manifest`，并按清单路径包含编译后的入口、子包、UI、资源与二次开发源码（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:77`）。
用文件工具 `Tools.Files.zip(sourceVfsPath, artifactVfsPath, false)` 创建不含外层目录的归档，成品扩展名为 `.toolpkg`，`manifest` 位于 ZIP 根目录（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:78`）。
接口以本 `Skill` 的 `types/` 为准，教程中的 `<dev_root>`、`<artifact_host_path>`、`<package_id>`、`<runtime_package_name>` 和 `<tool_name>` 是需要用真实值替换的占位符（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:3`）。

### 首次安装与测试

首次安装与测试的每行都是一次 `operit_editor` 工具的 `args` 参数数组，也可用于系统工具 `execute_cli_command`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:82`）。
导入结果给出 `packageName`、`packageFormat` 和 `storedPath`，以实际解析结果确认身份，不根据文件名猜包 id（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:94`）。
`ToolPkg` 容器 id 与可执行子包名不同，从 `package list` 和 `package show` 读取实际工具名（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:95`）。
只注册 `UI`、`hook` 或 `provider` 的包不一定有可执行工具（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:95`）。
启用后重新读取 `package list` 的真实 `enabled` 状态，不能把启用命令自身的文字或请求参数当作状态证明（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:96`）。
`package exec` 会激活对应工具包并执行导出工具，根据该工具声明填写 `JSON` 参数并检查返回内容（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:97`）。
`UI`、`hook`、`provider` 在对应应用场景验证（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:97`）。
调试小片段时将它写成有 `METADATA` 和导出函数的独立测试包，按导入、启用、执行、查看日志的流程测试（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:98`）。
`operit_editor` 不提供脚本直跑工具（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:98`）。
每一步出现错误即停止并定位原因，不要根据“命令已调用”宣称安装、启用或测试成功（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:99`）。

### 同 ID 的修改与重新安装

当前 `package import` 拒绝重复的已注册包名，不提供覆盖安装或自动热更新（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:104`）。
同 ID 更新是用户明确授权后的替换操作，不是失败后的自动处理（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:104`）。
删除已安装版本之前完成新版本构建，核验归档，并在开发目录保留源码及所需旧版本成品（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:106`）。
用 `package list` 和 `package show` 记录容器、子包的真实名称及启用状态，向用户说明删除与重新安装的影响并获得确认（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:107`）。
同 ID 更新时调用 `["package", "delete", "<package_id>"]`，确认删除成功；只对本次要更新的外部包执行该操作，不删除其他包（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:108`）。
调用 `["package", "import", "<artifact_host_path>"]` 重新导入，确认新版本导入成功；导入失败时保留错误并停止，不自动改变包 id 或执行其他安装路径（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:109`）。
按用户确认的配置逐项恢复容器及子包的启用状态，再读取列表核验，并重新测试工具、`UI` 与 `hook`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:110`）。
不要宣称包管理已经具有一键继续开发、合并开发或覆盖安装功能，创作入口目前接入的是新建需求草稿（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:112`）。
继续开发需要明确定位原项目并按上述流程处理（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:112`）。

### 发布与交付

本地安装、执行和界面测试完成后，用户在 `Artifact` 市场的发布页面选择已安装的本地插件，填写资料和版本（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:115`）。
直接发布本地插件时，页面处理当前成品，在当前 `GitHub` 账号的 `OperitForge` 仓库保存 `Release` 资产并登记市场条目（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:117`）。
引用 `GitHub` `Release` 资产时，选择自己仓库的 `Release` 与资产；页面核对所选资产与当前本地成品，并提交登记（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:118`）。
发布需要登录、用户确认及真实服务响应，不是创作入口自动完成的动作（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:120`）。
交付时分别列出源码目录、成品路径、包 id、安装与启用状态、已执行的测试和结果，以及发布状态；未测试或未发布的环节明确标注（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:120`）。

### API 版本与跨平台要求

`Operit2` 的 `ToolPkg` API 支持版本为 `2.0.0`，对 `1.0.0` 和 `1.0.1` 的加载支持并不完整（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:7`）。
`Operit1` 完整支持 `ToolPkg` API `1.0.0` 和 `1.0.1`，这两个版本主要面向 `Android`，是旧版 API 形式（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:7`）。
为 `Operit2` 新建 `ToolPkg` 时，在 `manifest` 中显式声明 `"api_version": "2.0.0"`，并使用 `PackageBuilder` 随包携带的当前版本 `types/`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:9`）。
解析器接受旧版本号不等于完整实现旧接口，旧包需要逐项验证所用能力，不能仅凭导入成功宣称兼容（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:9`）。
`schema_version` 表示清单格式版本，`api_version` 表示 `ToolPkg` API 契约，`version` 表示插件自身的发布版本，三者不能混用（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:13`）。
`ToolPkg` API `2.0.0` 面向多平台开发，基本所有公共接口都通过统一 host 能力提供跨平台兼容（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:11`）。
作者遇到平台特异接口时须明确其适用范围，考虑并验证其他平台的安装、界面与核心功能；不能把某个平台的专用能力当作所有平台都具备的接口（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:11`）。

## 关键符号

- `QuickPluginCreatorDialog` — 需求对话框（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:9`）
- `show` — 打开需求对话框并返回确认后的开发需求（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:16`）
- `_QuickPluginCreatorDialogState` — 对话框状态，持有需求输入控制器、进行中标志、准备结果与错误提示（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:33`）
- `_confirm` — 校验需求并准备创作资源，成功时返回需求（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:46`）
- `runQuickPluginCreatorSetup` — 准备函数（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:22`）
- `QuickPluginCreatorSetupResult` — 准备结果（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:6`）
- `ensureQuickPluginCreatorSkillVisible` — 确保创作 Skill 对 AI 可见（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:28`）
- `enablePackage` — 启用 `operit_editor`（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:31`）
- `isPackageEnabled` — 复核 `operit_editor` 的真实启用状态（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:34`）
- `ToolPkgCatalogChangeBus` — 目录变更通知总线，`notifyCatalogChanged` 通知目录变更（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:38`）
- `PackageBuilder` — 插件创作 Skill（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:17`）
- `operit_editor` — 平台编辑工具包（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`）
- `execute_cli_command` — 与 `operit_editor` 使用同一 core command 执行入口的系统工具（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`）
- `Tools.SoftwareSettings.exec(args)` — `operit_editor` 工具实际调用的执行入口（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`）
- `api_version` — ToolPkg API 契约版本（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:13`）
- `schema_version` — 清单格式版本（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:13`）
- `version` — 插件自身的发布版本（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:13`）
- `METADATA` — 单文件脚本包与调试测试包保留的注释块（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:77`）
- `Tools.Files.zip` — 创建不含外层目录的归档（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:78`）

## 调用链

1. 用户在包管理打开“快速创作你的插件”，`QuickPluginCreatorDialog` 的 `show` 打开需求对话框（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:16`）。
2. 用户输入需求并点击“准备并前往聊天”，`_confirm` 校验需求非空（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:46`）。
3. 确认处理调用 `runQuickPluginCreatorSetup` 准备创作资源（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:61`）。
4. `runQuickPluginCreatorSetup` 先调用 `skillRepository` 的 `ensureQuickPluginCreatorSkillVisible`（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:28`）。
5. 再调用 `packageManager` 的 `enablePackage` 启用 `operit_editor`，并用 `isPackageEnabled` 复核真实启用状态（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:31`）。
6. 复核未通过时抛出 `StateError`（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:36`）。
7. 准备流程捕获异常并返回 `success` 为 `false` 的结果（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:46`）。
8. 复核通过后调用 `ToolPkgCatalogChangeBus` 的 `notifyCatalogChanged` 通知目录变更（`apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart:38`）。
9. 准备成功后对话框返回需求字符串（`apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart:72`）。
10. 需求作为聊天草稿填入输入框，用户发送后才开始与 AI 协作开发（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:17`）。
11. 开发前调用 `execute_cli_command` 传入 `["skill", "show", "PackageBuilder"]` 读取 `Skill` 的真实目录与附件位置（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:49`）。
12. 在已选定的终端会话中确定用户同意使用的可写目录，记为 `<dev_root>`（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:51`）。
13. 完整复制 `Skill` 的 `types/`，不从旧仓库或云端下载另一版声明（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:74`）。
14. 按实际 shell 执行项目已声明的构建命令，检查退出码、超时状态和真实输出文件（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:75`）。
15. 用文件工具 `Tools.Files.zip(sourceVfsPath, artifactVfsPath, false)` 创建不含外层目录的 `.toolpkg` 归档，`manifest` 位于 ZIP 根目录（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:78`）。
16. 首次安装与测试按 `package list`、导入、启用、再查列表、查看包、执行工具、查看日志的顺序执行（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:88`）。
17. 同 ID 更新时调用 `["package", "delete", "<package_id>"]`，确认删除成功（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:108`）。
18. 再调用 `["package", "import", "<artifact_host_path>"]` 重新导入，导入失败时保留错误并停止（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:109`）。
19. 本地测试完成后，用户在 `Artifact` 市场的发布页面选择已安装的本地插件（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:115`）。
20. 直接发布本地插件时，页面处理当前成品，在当前 `GitHub` 账号的 `OperitForge` 仓库保存 `Release` 资产并登记市场条目（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:117`）。
21. 引用 `GitHub` `Release` 资产时，选择自己仓库的 `Release` 与资产，页面核对所选资产与当前本地成品并提交登记（`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:118`）。

## 来源

- apps/flutter/app/lib/ui/features/packages/dialogs/QuickPluginCreatorDialog.dart
- apps/flutter/app/lib/ui/features/packages/screens/QuickPluginCreatorSetupSupport.dart
- plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md

seed 清单见 tracking/read-batch-06/plugin-quick-plugin-creator.txt。
