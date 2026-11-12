---
title: 跨边界测试集
module: tools
platforms: [all]
sources: 3
date: 2026-11-11
---

## 概述

- 本页是索引型页面：三个种子文件仅作示例，其余 149 个文件未逐个列出、未读内容。
- tools/tests/ 收纳跨语言、跨宿主契约检查：android_runtime_contracts.test.mjs 用 `source()` 读取生产文件做校验 `tools/tests/android_runtime_contracts.test.mjs:9`
- tools/tests/ 共 152 个文件，顶层 124 个文件，另有 fixtures、kotlin、support、web_local_inference_smoke 共 4 个子目录（清点证据：wiki 仓库 tracking/count-tools-tests-364d1d594.txt）
- 顶层 124 个文件中 .mjs 文件 81 个、.kt 文件 1 个，合计 82 个 `test` 文件（清点证据：wiki 仓库 tracking/count-tools-tests-364d1d594.txt）
- 顶层其余 42 个文件是 37 个 .py `test` 脚本、2 个 .ts 文件、2 个 .rb 文件与 1 个 .dart 文件（清点证据：wiki 仓库 tracking/count-tools-tests-364d1d594.txt）
- 4 个子目录共 28 个文件：fixtures/ 19 个、kotlin/ 3 个、support/ 2 个、web_local_inference_smoke/ 4 个（清点证据：wiki 仓库 tracking/count-tools-tests-364d1d594.txt）
- 相关页：[[tools-overview|tools 总览]]收纳 tools/ 下各类工具，[[tools-build-scripts|构建脚本入口]]覆盖 Android 发布脚本。

## AI 速览

- `source()` — 读取生产文件做跨语言宿主契约检查 `tools/tests/android_runtime_contracts.test.mjs:9`
- `test()` — node:test 用例定义，android_runtime_contracts.test.mjs 定义 24 个用例 `tools/tests/android_runtime_contracts.test.mjs:37`
- `declaration()` — 抽取 Rust 提示声明 `tools/tests/builtin_tool_catalog.test.mjs:10`
- `toolNames()` — 从提示声明中读出工具名 `tools/tests/builtin_tool_catalog.test.mjs:18`
- `compileComposeModule()` — 构建 Compose 产物 `tools/tests/compose_dsl_artifact.test.mjs:22`
- `wrapComposeScript()` — 包装脚本做运行时注册，注册后 `__operit_render_compose_dsl` 为函数 `tools/tests/compose_dsl_artifact.test.mjs:118`
- 数据流向：测试文件读取生产文件，再断言契约 `tools/tests/android_runtime_contracts.test.mjs:9`

## 核心机制

### 组织维度

- android 前缀的顶层文件共 8 个（清点证据：wiki 仓库 tracking/count-tools-tests-364d1d594.txt）
- compose_dsl 前缀的顶层文件共 9 个（清点证据：wiki 仓库 tracking/count-tools-tests-364d1d594.txt）
- builtin_tool_catalog.test.mjs 校验 `SystemToolPrompts` 与 `SystemToolPromptsInternal` 组成的内置工具目录 `tools/tests/builtin_tool_catalog.test.mjs:6`

### Android 运行时契约（Android 平台）

- android_runtime_contracts.test.mjs 用 node:test 定义 24 个 `test` 用例 `tools/tests/android_runtime_contracts.test.mjs:37`
- Android 设备信息由 Flutter owner 实现 `tools/tests/android_runtime_contracts.test.mjs:37`
- hosts/android 的 `getDeviceInfo` 要求 Android get_device_info 走 owner 通道 `tools/tests/android_runtime_contracts.test.mjs:42`
- OwnerSystemCapabilityChannel.kt 把 get_device_info 映射到 `AndroidHostDeviceInfo.read` `tools/tests/android_runtime_contracts.test.mjs:47`
- Android 系统设置在宿主组装时绑定 `settingReader` 与 `settingWriter` `tools/tests/android_runtime_contracts.test.mjs:66`
- 共享 owner 设置适配器用 get_system_setting 与 modify_system_setting 平台无关协议读写设置 `tools/tests/android_runtime_contracts.test.mjs:83`
- Owner 端设置读取按 system、secure、global 三命名空间分别走 Settings.System、Settings.Secure、Settings.Global 的 `getString` `tools/tests/android_runtime_contracts.test.mjs:99`
- `NativeCrashActivity` 以 :crash 进程运行 `tools/tests/android_runtime_contracts.test.mjs:227`
- Android 崩溃进程跳过重启动作与全部 Core 生命周期事件 `tools/tests/android_runtime_contracts.test.mjs:225`
- Android 运行时创建用独立的 `runtimeCreationLock`，与 `runtimeLock` 分离 `tools/tests/android_runtime_contracts.test.mjs:254`
- `runtimeLock` 只保护状态，不含 `prepareAndroidRuntimePaths`、`AndroidRuntimeAssets.prepare`、`OperitRuntimeNative.create` 与 destroy 等昂贵工作 `tools/tests/android_runtime_contracts.test.mjs:197`
- Android 宿主广播经 `HostEventBridge` 走非阻塞运行时事件槽 `tools/tests/android_runtime_contracts.test.mjs:319`
- 该测试断言 AndroidRuntimeHost.kt 内 `OperitRuntimeNative.emitRuntimeEvent` 只出现一次调用 `tools/tests/android_runtime_contracts.test.mjs:352`
- Android 发布先校验 APK 的运行时资产再复制到 dist：`verify_android_runtime_assets` 在 `publish_android_apk` 之前执行 `tools/tests/android_runtime_contracts.test.mjs:310`
- Android Rust profile 跟随构建变体：debug 对应 debug，profile 与 release 对应 release `tools/tests/android_runtime_contracts.test.mjs:365`
- ProGuard 保留 `AndroidRuntimeHost` 的 JNI 方法 `tools/tests/android_runtime_contracts.test.mjs:290`

### 内置工具目录

- 内置工具目录由 `SystemToolPrompts` 的公开提示与 `SystemToolPromptsInternal` 的内部提示共同组成 `tools/tests/builtin_tool_catalog.test.mjs:6`
- 公开目录分 basic_tools、file_system_tools、http_tools 三类 `tools/tests/builtin_tool_catalog.test.mjs:25`
- 内部目录由 `internalToolCategoriesEnSource` 与 `internalToolCategoriesCnSource` 提供 `tools/tests/builtin_tool_catalog.test.mjs:27` `core/crates/provider/services/src/chat/config/SystemToolPromptsInternal.rs:45` `core/crates/provider/services/src/chat/config/SystemToolPromptsInternal.rs:1281`
- 英文与中文两套目录各自断言每个内置工具恰好出现一次 `tools/tests/builtin_tool_catalog.test.mjs:24`
- builtin_tool_catalog.test.mjs 定义 2 个 `test`，在 En 与 Cn 双语下各跑一次，共 4 个用例 `tools/tests/builtin_tool_catalog.test.mjs:22`
- `write_file` 保持 AI 可见，公开 schema 含 path 与 content 必填参数和 append 可选参数 `tools/tests/builtin_tool_catalog.test.mjs:43`
- `write_file` 不在内部目录中，内部目录对应项是 `write_file_binary` `tools/tests/builtin_tool_catalog.test.mjs:47`

### Compose DSL 产物

- compose_dsl_artifact.test.mjs 定义 8 个 `test` 用例 `tools/tests/compose_dsl_artifact.test.mjs:21`
- compose_dsl_artifact.test.mjs 用 `compileComposeModule` 构建 Compose 产物 `tools/tests/compose_dsl_artifact.test.mjs:22`
- Compose 产物头为 // @operit-compose-artifact 4，产物包含 `OperitComposeReactive.frame` `tools/tests/compose_dsl_artifact.test.mjs:23`
- Compose 产物确定且幂等：同一源码两次编译结果相等，编译产物再编译结果不变 `tools/tests/compose_dsl_artifact.test.mjs:25`
- 构建期编译不执行顶层插件代码 `tools/tests/compose_dsl_artifact.test.mjs:33`
- 运行时加载产物不走 parser 与 lowering：`OperitComposeCompiler.compile` 被替换为抛错后 prepare 仍返回产物 `tools/tests/compose_dsl_artifact.test.mjs:30`
- 版本 999 与版本 1 的产物在 prepare、compile、artifact 三方法下均抛 Unsupported Compose artifact version `tools/tests/compose_dsl_artifact.test.mjs:37`
- 旧产物版本 1、2、3 须用程序 ABI 重建 `tools/tests/compose_dsl_artifact.test.mjs:124`
- 预编译页面不初始化解析器，`parserInitializations` 保持为 0 `tools/tests/compose_dsl_artifact.test.mjs:79`
- 旧源码首次 prepare 后 `parserInitializations` 为 1，语法错误不使已初始化的解析器失效 `tools/tests/compose_dsl_artifact.test.mjs:85`
- 解析器初始化失败保留原错误，不重试，不留部分全局变量 `tools/tests/compose_dsl_artifact.test.mjs:95`
- 运行时从 `wrapComposeScript` 注册，`__operit_render_compose_dsl` 为函数 `tools/tests/compose_dsl_artifact.test.mjs:118`
- 产物正文与同一 SDK 编译器的运行时 lowering 完全一致 `tools/tests/compose_dsl_artifact.test.mjs:59`
- 运行时用 vm 加载 SDK 的 compose/Artifact.js 与 compose/Compiler.js `tools/tests/compose_dsl_artifact.test.mjs:12`
- 测试源码示例用 ctx.`useState` 管理 count 状态并用 ctx.UI.Button 渲染 `tools/tests/compose_dsl_artifact.test.mjs:18`

## 关键符号

- `source()` — 读取生产文件做跨语言宿主契约检查 `tools/tests/android_runtime_contracts.test.mjs:9`
- `test()` — node:test 用例定义 `tools/tests/android_runtime_contracts.test.mjs:37`
- `settingReader` / `settingWriter` — Android 系统设置在宿主组装时绑定的读写回调 `tools/tests/android_runtime_contracts.test.mjs:66`
- get_system_setting / modify_system_setting — 共享 owner 设置适配器的平台无关协议 `tools/tests/android_runtime_contracts.test.mjs:83`
- `HostEventBridge` — Android 宿主广播的非阻塞运行时事件槽入口 `tools/tests/android_runtime_contracts.test.mjs:319`
- `runtimeCreationLock` / `runtimeLock` — 运行时创建锁与状态锁，二者分离 `tools/tests/android_runtime_contracts.test.mjs:254`
- `verify_android_runtime_assets` — Android 发布前校验 APK 运行时资产 `tools/tests/android_runtime_contracts.test.mjs:310`
- `declaration()` — 抽取 Rust 提示声明 `tools/tests/builtin_tool_catalog.test.mjs:10`
- `toolNames()` — 从提示声明中读出工具名 `tools/tests/builtin_tool_catalog.test.mjs:18`
- `write_file` / `write_file_binary` — 公开写文件工具与内部二进制写文件工具 `tools/tests/builtin_tool_catalog.test.mjs:47`
- `compileComposeModule()` — 构建 Compose 产物 `tools/tests/compose_dsl_artifact.test.mjs:22`
- `OperitComposeCompiler` — 运行时编译器，加载产物时不走 lowering `tools/tests/compose_dsl_artifact.test.mjs:30`
- `__operit_render_compose_dsl` — 运行时注册后为函数 `tools/tests/compose_dsl_artifact.test.mjs:118`
- `parserInitializations` — 解析器初始化计数，预编译页面保持为 0 `tools/tests/compose_dsl_artifact.test.mjs:79`

## 调用链

### Android 运行时契约检查

1. `source()` 读取生产文件做跨语言宿主契约检查 `tools/tests/android_runtime_contracts.test.mjs:9`
2. hosts/android 的 `getDeviceInfo` 要求 Android get_device_info 走 owner 通道 `tools/tests/android_runtime_contracts.test.mjs:42`
3. OwnerSystemCapabilityChannel.kt 把 get_device_info 映射到 `AndroidHostDeviceInfo.read` `tools/tests/android_runtime_contracts.test.mjs:47`
4. Android 宿主广播经 `HostEventBridge` 走非阻塞运行时事件槽 `tools/tests/android_runtime_contracts.test.mjs:319`
5. Android 发布先校验 APK 的运行时资产再复制到 dist `tools/tests/android_runtime_contracts.test.mjs:310`

### 内置工具目录检查

1. 内置工具目录由 `SystemToolPrompts` 的公开提示与 `SystemToolPromptsInternal` 的内部提示共同组成 `tools/tests/builtin_tool_catalog.test.mjs:6`
2. `declaration()` 抽取 Rust 提示声明 `tools/tests/builtin_tool_catalog.test.mjs:10`
3. `toolNames()` 从提示声明中读出工具名 `tools/tests/builtin_tool_catalog.test.mjs:18`
4. 英文与中文两套目录各自断言每个内置工具恰好出现一次 `tools/tests/builtin_tool_catalog.test.mjs:24`
5. `write_file` 保持 AI 可见，公开 schema 含 path 与 content 必填参数和 append 可选参数 `tools/tests/builtin_tool_catalog.test.mjs:43`

### Compose DSL 产物检查

1. `compileComposeModule()` 构建 Compose 产物 `tools/tests/compose_dsl_artifact.test.mjs:22`
2. Compose 产物头为 // @operit-compose-artifact 4，产物包含 `OperitComposeReactive.frame` `tools/tests/compose_dsl_artifact.test.mjs:23`
3. 运行时加载产物不走 parser 与 lowering：`OperitComposeCompiler.compile` 被替换为抛错后 prepare 仍返回产物 `tools/tests/compose_dsl_artifact.test.mjs:30`
4. 预编译页面不初始化解析器，`parserInitializations` 保持为 0 `tools/tests/compose_dsl_artifact.test.mjs:79`
5. 版本 999 与版本 1 的产物在 prepare、compile、artifact 三方法下均抛 Unsupported Compose artifact version `tools/tests/compose_dsl_artifact.test.mjs:37`

## 来源

- 种子文件（3 个，均已读全文）：
  - tools/tests/android_runtime_contracts.test.mjs（395 行，24 个 test 用例）
  - tools/tests/builtin_tool_catalog.test.mjs（50 行，2 个 test 定义 × En/Cn 双语 = 4 个用例）
  - tools/tests/compose_dsl_artifact.test.mjs（129 行，8 个 test 用例）
- 文件总数与分类核验方法：2026-11-12 对基线 AAswordman/Operit2 @ 364d1d594，用 `find tools/tests -type f | wc -l` 得 152，`find tools/tests -maxdepth 1 -type f | wc -l` 得 124，顶层扩展名与文件名前缀用 `ls` 清点，子目录文件数用 `find <子目录> -type f | wc -l` 清点，用例数用 `grep -c '^test('` 计数。清点记录与完整文件清单见 wiki 仓库 tracking/count-tools-tests-364d1d594.txt；聚合总数只保留在正文，不再以无依据的引用出现在 facts.json 里。
- 范围限定：本页三个种子文件仅作示例，其余 149 个文件未逐个列出、未读内容；android 前缀 8 个文件、compose_dsl 前缀 9 个文件按文件名前缀归类，内容只核对了三个种子文件。
