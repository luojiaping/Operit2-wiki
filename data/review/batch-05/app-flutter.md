---
title: Flutter 应用（主客户端）
module: apps
platforms: [android, ios, macos, windows, linux, web, ohos]
sources: [apps/flutter/app/README.md, apps/flutter/app/pubspec.yaml, apps/flutter/app/.fvmrc, apps/flutter/app/android/app/src/main/AndroidManifest.xml, apps/flutter/app/ios/Runner/Info.plist, apps/flutter/app/macos/Runner/Info.plist, apps/flutter/app/windows/runner/main.cpp, apps/flutter/app/linux/CMakeLists.txt, apps/flutter/app/web/index.html, apps/flutter/app/ohos/build-profile.json5, apps/flutter/native/operit-flutter-bridge/Cargo.toml, apps/flutter/native/operit-flutter-bridge/src/lib.rs, apps/flutter/native/operit-flutter-bridge/src/platform_runtime/mod.rs, apps/flutter/native/operit-flutter-bridge/src/BridgeExports.rs, apps/flutter/native/operit-flutter-bridge/src/FfiTransport.rs, apps/flutter/native/operit-flutter-bridge/FFI.md, apps/flutter/app/lib/core/bridge/FfiCoreTransport.dart, apps/flutter/app/lib/core/bridge/PlatformCoreProxy.dart, apps/flutter/app/lib/core/bridge/PlatformCoreProxyNative.dart, apps/flutter/app/lib/core/bridge/PlatformCoreProxyWeb.dart, apps/flutter/app/lib/core/bridge/CoreProxy.dart, apps/flutter/app/lib/main.dart, apps/flutter/app/lib/ui/main/OperitApp.dart, apps/flutter/packages/operit_ui/pubspec.yaml, apps/flutter/packages/operit_ui/README.md, apps/flutter/packages/operit_ui/lib/operit_ui.dart]
date: 2026-11-11
---

## 概述

Flutter 应用是 Operit2 的主客户端，包名是 operit2（`apps/flutter/app/pubspec.yaml:1`）。
Flutter 应用的 version 是 2.0.0+38（`apps/flutter/app/pubspec.yaml:19`）。
Flutter 应用的 environment 要求 sdk ^3.10.8（`apps/flutter/app/pubspec.yaml:22`）。
README 声明全部平台使用 AAswordman/flutter-ohos（`apps/flutter/app/README.md:3`）。
README 写明的 fork 版本是 3.41.10-ohos-0.0.2-beta.operit.1（`apps/flutter/app/README.md:4`）。
.fvmrc 钉住的 Flutter 版本是 3.41.10-ohos-0.0.2-beta.operit.9（`apps/flutter/app/.fvmrc:2`）。
README 写明的版本与 .fvmrc 钉住的版本不一致，前者是 operit.1，后者是 operit.9（`apps/flutter/app/.fvmrc:2`）。
.fvmrc 的 flutterUrl 是 https://github.com/AAswordman/flutter-ohos.git（`apps/flutter/app/.fvmrc:3`）。
FVM 把 fork 安装在 .fvm/flutter_sdk（`apps/flutter/app/README.md:5`）。
构建脚本对全部平台使用同一份 SDK，包含 OpenHarmony（`apps/flutter/app/README.md:18`）。
README 要求执行 fvm flutter precache --web --ohos（`apps/flutter/app/README.md:11`）。
服务端应用见 [[app-server|服务端应用（占位）]]。

## AI 速览

- `main` — 应用入口，执行启动序列（`apps/flutter/app/lib/main.dart:32`）
- `platformCoreProxy` — Dart 侧 Core 代理，原生走 FFI、Web 走 WASM（`apps/flutter/app/lib/core/bridge/PlatformCoreProxy.dart:3`）
- `FfiCoreTransport` — 原生 FFI 传输，实现 `CoreByteTransport`（`apps/flutter/app/lib/core/bridge/FfiCoreTransport.dart:41`）
- `WebWasmCoreProxy` — Web 平台的 Core 代理（`apps/flutter/app/lib/core/bridge/PlatformCoreProxyWeb.dart:6`）
- `OperitApp` — 主窗口根组件（`apps/flutter/app/lib/ui/main/OperitApp.dart:19`）
- `RuntimeBootstrapManager` — 启动时初始化 runtime 引导状态（`apps/flutter/app/lib/main.dart:105`）
- `CoreApplicationService` — 主窗口启动 Core 应用服务（`apps/flutter/app/lib/main.dart:162`）
- `operit_flutter_bridge_create` — 在非 Android、非 OpenHarmony 平台上创建 runtime 的 C 导出（`apps/flutter/native/operit-flutter-bridge/src/BridgeExports.rs:26`）
- `operit_flutter_bridge_ffi_connect` — FFI 连接入口（`apps/flutter/native/operit-flutter-bridge/src/FfiTransport.rs:288`）
- `prepareLiquidGlass` — 预载液态玻璃光学着色器（`apps/flutter/packages/operit_ui/README.md:21`）
- 主入口函数是 `main`（`apps/flutter/app/lib/main.dart:32`）。
- 数据流向一句话：Dart 侧经 platformCoreProxy 发请求，原生平台走 FFI 会话进 Rust bridge，Web 平台走 JS interop 与 Rust WASM（`apps/flutter/native/operit-flutter-bridge/FFI.md:153`、`apps/flutter/app/lib/core/bridge/PlatformCoreProxy.dart:3`、`apps/flutter/app/lib/core/bridge/FfiCoreTransport.dart:69`）。

## 核心机制

### 单一代码库覆盖七个平台

Android 平台壳的清单文件是 AndroidManifest.xml，首行声明 manifest 元素（`apps/flutter/app/android/app/src/main/AndroidManifest.xml:1`）。
iOS 平台壳包含 Runner/Info.plist，其 DOCTYPE 声明 plist 格式（`apps/flutter/app/ios/Runner/Info.plist:2`）。
macOS 平台壳包含 Runner/Info.plist，其 DOCTYPE 声明 plist 格式（`apps/flutter/app/macos/Runner/Info.plist:2`）。
Windows 平台壳入口 windows/runner/main.cpp 引用 flutter/dart_project.h（`apps/flutter/app/windows/runner/main.cpp:1`）。
Linux 平台壳由 linux/CMakeLists.txt 定义 runner 工程（`apps/flutter/app/linux/CMakeLists.txt:3`）。
Web 平台壳包含 web/index.html，首行是 html 文档声明（`apps/flutter/app/web/index.html:1`）。
OpenHarmony 平台壳包含 ohos/build-profile.json5，其 app 配置块以 app 开头（`apps/flutter/app/ohos/build-profile.json5:3`）。
README 要求执行 fvm flutter precache --web --ohos（`apps/flutter/app/README.md:11`）。
Web 调试用 web_dev_config.yaml 给 Flutter 原生 Web 开发服务器配置跨域隔离头，用于本地多线程 STT/TTS（`apps/flutter/app/README.md:22`）。
Web 开发源地址是 http://127.0.0.1:4835，不需要单独的代理进程（`apps/flutter/app/README.md:26`）。
pubspec 声明 path_provider_ohos，来自 openharmony-sig/flutter_packages 的 git 仓库（`apps/flutter/app/pubspec.yaml:61`）。
pubspec 声明 url_launcher_ohos，来自 openharmony-sig/flutter_packages 的 git 仓库（`apps/flutter/app/pubspec.yaml:78`）。
pubspec 声明 record_ohos，来自本地 thirdparty 路径（`apps/flutter/app/pubspec.yaml:69`）。
pubspec 声明 image_picker_ohos，来自本地 thirdparty 路径（`apps/flutter/app/pubspec.yaml:93`）。
pubspec 在 dependency_overrides 中把 webview_all_ohos 指向本地 thirdparty 路径（`apps/flutter/app/pubspec.yaml:157`）。
ffi ^2.2.0 声明在 pubspec 的 dev_dependencies 段（`apps/flutter/app/pubspec.yaml:131`）。

### Dart 侧与 Rust Core 的桥接

桥接 crate 名为 operit-flutter-bridge（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:2`）。
桥接 crate 的 version 是 0.1.0（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:3`）。
桥接 crate 的 crate-type 是 cdylib 与 rlib（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:9`）。
operit-flutter-bridge 是 Flutter 到平台无关 Core runtime 的传输边界（`apps/flutter/native/operit-flutter-bridge/src/lib.rs:2`）。
PlatformRuntimeFactory 选择 host 构造，PlatformRuntimeAbi 选择 ABI 模块（`apps/flutter/native/operit-flutter-bridge/src/lib.rs:3`）。
platform_runtime 用 cfg 门控为 android、ios、linux、macos 各设一个模块（`apps/flutter/native/operit-flutter-bridge/src/platform_runtime/mod.rs:13`）。
platform_runtime 用 cfg 门控为 ohos、web、windows 各设一个模块（`apps/flutter/native/operit-flutter-bridge/src/platform_runtime/mod.rs:21`）。
桥接在 Android 上依赖 operit-host-android-native，路径指向 hosts/android（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:51`）。
桥接在 Windows 上依赖 operit-host-windows-native，路径指向 hosts/windows（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:54`）。
桥接在 Linux 上依赖 operit-host-linux-native，路径指向 hosts/linux（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:57`）。
桥接在 OpenHarmony 上依赖 operit-host-ohos-native，路径指向 hosts/ohos（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:60`）。
桥接在 iOS 上依赖 operit-host-ios-native，路径指向 hosts/ios（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:63`）。
桥接在 macOS 上依赖 operit-host-macos-native，带 arm64-runtime 特性（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:66`）。
桥接在 wasm32 上依赖 operit-host-web，路径指向 hosts/web（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:71`）。
在非 Android、非 OpenHarmony 平台上，BridgeExports 导出 operit_flutter_bridge_create 创建引用计数的 runtime（`apps/flutter/native/operit-flutter-bridge/src/BridgeExports.rs:26`）。
OpenHarmony 用独立的 operit_flutter_bridge_create_ohos 入口，参数含 runtime_root、workspace_root、system_language_code、device_model（`apps/flutter/native/operit-flutter-bridge/src/BridgeExports.rs:95`）。
operit_flutter_bridge_ffi_connect 是 FFI 连接入口，位于 FfiTransport.rs（`apps/flutter/native/operit-flutter-bridge/src/FfiTransport.rs:288`）。
Flutter Core 调用与流只用 ABI 版本 3，ABI v1 与 v2 已移除（`apps/flutter/native/operit-flutter-bridge/FFI.md:3`）。
Dart 拒绝 version 不是 3 的描述符（`apps/flutter/native/operit-flutter-bridge/FFI.md:5`）。
每个 Flutter isolate 在 operit/runtime 平台通道上惰性调用 connectCoreFfi（`apps/flutter/native/operit-flutter-bridge/FFI.md:10`）。
FFI 描述符的 version 字段是整数 3（`apps/flutter/native/operit-flutter-bridge/FFI.md:16`）。
Web 用 WebWasmCoreProxy、JS interop、Runtime Worker 与 Rust WASM（`apps/flutter/native/operit-flutter-bridge/FFI.md:153`）。
FfiCoreTransport 实现 CoreByteTransport（`apps/flutter/app/lib/core/bridge/FfiCoreTransport.dart:41`）。
FfiCoreTransport 的 _connect 在 MethodChannel operit/runtime 上调用 connectCoreFfi（`apps/flutter/app/lib/core/bridge/FfiCoreTransport.dart:69`）。
FfiCoreTransport 校验描述符 version 等于 3 且 NativeApi.majorVersion 等于 2，否则抛错（`apps/flutter/app/lib/core/bridge/FfiCoreTransport.dart:99`）。
PlatformCoreProxy 按 dart.library.html 条件导出原生或 Web 实现（`apps/flutter/app/lib/core/bridge/PlatformCoreProxy.dart:3`）。
原生平台的 platformCoreProxy 是 FfiCoreProxy（`apps/flutter/app/lib/core/bridge/PlatformCoreProxyNative.dart:6`）。
Web 平台的 platformCoreProxy 是 WebWasmCoreProxy（`apps/flutter/app/lib/core/bridge/PlatformCoreProxyWeb.dart:6`）。
`PlatformRuntimeHost` 声明 `dataRescue`，CoreProxy 实现该接口（`apps/flutter/app/lib/core/bridge/CoreProxy.dart:10`）。

### flutter-ohos fork 的选用情况

README 声明全部平台使用 AAswordman/flutter-ohos（`apps/flutter/app/README.md:3`）。
.fvmrc 的 flutterUrl 是 https://github.com/AAswordman/flutter-ohos.git（`apps/flutter/app/.fvmrc:3`）。
构建脚本对全部平台使用同一份 SDK，包含 OpenHarmony（`apps/flutter/app/README.md:18`）。
README 要求执行 fvm flutter precache --web --ohos（`apps/flutter/app/README.md:11`）。
pubspec 声明 path_provider_ohos，来自 openharmony-sig/flutter_packages 的 git 仓库（`apps/flutter/app/pubspec.yaml:61`）。
pubspec 声明 url_launcher_ohos，来自 openharmony-sig/flutter_packages 的 git 仓库（`apps/flutter/app/pubspec.yaml:78`）。
桥接在 OpenHarmony 上依赖 operit-host-ohos-native，路径指向 hosts/ohos（`apps/flutter/native/operit-flutter-bridge/Cargo.toml:60`）。
OpenHarmony 用独立的 operit_flutter_bridge_create_ohos 入口，参数含 runtime_root、workspace_root、system_language_code、device_model（`apps/flutter/native/operit-flutter-bridge/src/BridgeExports.rs:95`）。

### lib/core 与 lib/ui 的分工

main.dart 从 core/bridge 导入 PlatformCoreProxy（`apps/flutter/app/lib/main.dart:14`）。
main.dart 从 core/application 导入 CoreApplicationService（`apps/flutter/app/lib/main.dart:13`）。
main.dart 从 core/runtime 导入 RuntimeBootstrapManager（`apps/flutter/app/lib/main.dart:20`）。
main.dart 从 ui/main 导入 OperitApp（`apps/flutter/app/lib/main.dart:22`）。
main.dart 从 ui/rescue 导入 DataRescueApp（`apps/flutter/app/lib/main.dart:15`）。
Flutter 应用依赖本地路径包 operit_ui（`apps/flutter/app/pubspec.yaml:31`）。
operit_ui 包名为 operit_ui，版本 0.1.0（`apps/flutter/packages/operit_ui/pubspec.yaml:1`）。
operit_ui 的描述是共享 Operit Flutter UI 组件、外观模型与渲染资源（`apps/flutter/packages/operit_ui/pubspec.yaml:2`）。
operit_ui 不依赖 Core、Host、文件系统、HTTP、operit2 或原生构建钩子（`apps/flutter/packages/operit_ui/README.md:3`）。
operit_ui 的 ThemePreferenceSnapshot 有 104 个字段（`apps/flutter/packages/operit_ui/lib/src/model/theme_preference_snapshot.dart:3`）。
operit_ui 的入口 operit_ui.dart 导出 theme_asset_resolver 等模块（`apps/flutter/packages/operit_ui/lib/operit_ui.dart:4`）。
main.dart 从 operit_ui 导入 prepareLiquidGlass 与 OperitDesignCaptureScope（`apps/flutter/app/lib/main.dart:11`）。
operit_ui 要求在应用或预览启动时调用 prepareLiquidGlass 预载光学着色器（`apps/flutter/packages/operit_ui/README.md:21`）。

## 关键符号

- `main` — 应用入口，执行启动序列（`apps/flutter/app/lib/main.dart:32`）
- `platformCoreProxy` — Dart 侧 Core 代理（`apps/flutter/app/lib/core/bridge/PlatformCoreProxy.dart:3`）
- `FfiCoreProxy` — 原生平台的 Core 代理实现（`apps/flutter/app/lib/core/bridge/PlatformCoreProxyNative.dart:6`）
- `WebWasmCoreProxy` — Web 平台的 Core 代理实现（`apps/flutter/app/lib/core/bridge/PlatformCoreProxyWeb.dart:6`）
- `FfiCoreTransport` — 原生 FFI 传输（`apps/flutter/app/lib/core/bridge/FfiCoreTransport.dart:41`）
- `PlatformRuntimeHost` — 声明 `dataRescue` 的接口，CoreProxy 实现该接口（`apps/flutter/app/lib/core/bridge/CoreProxy.dart:10`）
- `RuntimeBootstrapManager` — runtime 引导管理（`apps/flutter/app/lib/main.dart:105`）
- `CoreApplicationService` — Core 应用服务（`apps/flutter/app/lib/main.dart:162`）
- `OperitApp` — 主窗口根组件（`apps/flutter/app/lib/ui/main/OperitApp.dart:19`）
- `DataRescueApp` — 数据救援应用（`apps/flutter/app/lib/main.dart:15`）
- `prepareLiquidGlass` — 预载液态玻璃光学着色器（`apps/flutter/app/lib/main.dart:113`）
- `operit_flutter_bridge_create` — 在非 Android、非 OpenHarmony 平台上创建引用计数的 runtime（`apps/flutter/native/operit-flutter-bridge/src/BridgeExports.rs:26`）
- `operit_flutter_bridge_create_ohos` — OpenHarmony 的 bridge 创建入口（`apps/flutter/native/operit-flutter-bridge/src/BridgeExports.rs:95`）
- `operit_flutter_bridge_ffi_connect` — FFI 连接入口（`apps/flutter/native/operit-flutter-bridge/src/FfiTransport.rs:288`）
- `connectCoreFfi` — 平台通道上的 FFI 连接方法（`apps/flutter/app/lib/core/bridge/FfiCoreTransport.dart:69`）
- `ThemePreferenceSnapshot` — operit_ui 的外观快照模型，有 104 个字段（`apps/flutter/packages/operit_ui/lib/src/model/theme_preference_snapshot.dart:3`）

## 调用链

1. `main` 在 `runZonedGuarded` 内执行启动序列（`apps/flutter/app/lib/main.dart:35`）。
2. 启动时先向 `platformCoreProxy.dataRescue` 查询 launchMode（`apps/flutter/app/lib/main.dart:42`）。
3. 启动流程调用 `RuntimeBootstrapManager.instance.initialize`（`apps/flutter/app/lib/main.dart:105`）。
4. 启动流程调用 `prepareLiquidGlass` 初始化液态玻璃（`apps/flutter/app/lib/main.dart:113`）。
5. 主窗口启动 `CoreApplicationService.instance.initialize`，ownsRuntime 取 clientOnly 的反值（`apps/flutter/app/lib/main.dart:162`）。
6. 主窗口根组件是 `OperitDesignCaptureScope` 包裹的 `OperitApp`（`apps/flutter/app/lib/main.dart:236`）。
7. 原生平台上 FfiCoreTransport 在 MethodChannel operit/runtime 上调用 `connectCoreFfi` 取 FFI 描述符（`apps/flutter/app/lib/core/bridge/FfiCoreTransport.dart:69`）。
8. FfiCoreTransport 校验描述符 version 等于 3 且 NativeApi.majorVersion 等于 2，否则抛错（`apps/flutter/app/lib/core/bridge/FfiCoreTransport.dart:99`）。
9. Web 平台上 platformCoreProxy 是 `WebWasmCoreProxy`，走 JS interop 与 Rust WASM（`apps/flutter/native/operit-flutter-bridge/FFI.md:153`）。

## 来源

- 通读：apps/flutter/app/README.md、apps/flutter/app/pubspec.yaml。
- 抽查：apps/flutter/app/lib/ 的目录结构与 lib/main.dart 全文；apps/flutter/native/operit-flutter-bridge/ 的 Cargo.toml、FFI.md、src/lib.rs、src/platform_runtime/mod.rs、src/BridgeExports.rs 的导出入口、src/FfiTransport.rs 的连接入口；apps/flutter/packages/operit_ui/ 的 README.md、pubspec.yaml、lib/operit_ui.dart。
- 抽查：apps/flutter/app/lib/core/bridge/ 的文件清单与 FfiCoreTransport.dart、PlatformCoreProxy.dart、PlatformCoreProxyNative.dart、PlatformCoreProxyWeb.dart、CoreProxy.dart 的关键行；apps/flutter/app/lib/ui/main/OperitApp.dart 的类声明行。
- 抽查：七个平台壳目录的存在性，各抽查一个入口文件的前 3 行（android 的 AndroidManifest.xml、ios 与 macos 的 Info.plist、windows 的 main.cpp、linux 的 CMakeLists.txt、web 的 index.html、ohos 的 build-profile.json5）。
- 本页是总览页，只覆盖应用入口、桥接边界与目录分工；lib/ui 的功能页、bridge 的实现页、平台壳页在 v2 拆分。
- 本页未覆盖官方 Flutter 缺失 OpenHarmony 支持的具体原因，README 与 pubspec 只写明 fork 与 OHOS 依赖的选用结果。
- 本页未覆盖：lib/core/ 除 bridge 外的子目录（application、browser、compose、errors、host、link、logging、notifications、runtime、snapshot、theme、update、web_visit）的内部实现；lib/ui/ 除 main 与 rescue 入口外的 410 个 Dart 文件的界面实现；lib/data、lib/l10n、lib/util 的内容；bridge 的 src 内除 lib.rs、mod.rs、BridgeExports 导出入口、FfiTransport 连接入口外的实现文件；apps/flutter/thirdparty/ 的全部内容；各平台壳除入口文件前 3 行外的原生代码。
- 已发现的不一致：README 写明的 fork 版本是 3.41.10-ohos-0.0.2-beta.operit.1，.fvmrc 钉住的版本是 3.41.10-ohos-0.0.2-beta.operit.9，两处数字不一致（`apps/flutter/app/.fvmrc:2`）。
- 本页只写抽查证实的内容，凡没读到的写“本页未覆盖”。
