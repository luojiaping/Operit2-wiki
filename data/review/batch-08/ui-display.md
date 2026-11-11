---
title: 工具展示语义与 WebView 渲染
module: theme
platforms: [android, ios, macos, windows, linux, ohos, web]
sources: [13]
date: 2026-11-11
---

## 概述

- 本页讲工具调用在界面上如何展示，以及 WebView 里应用缩放与页面缩放如何分开工作。`docs/tool-display-semantics.md:3`
- 工具的展示信息由工具所有者声明，Core 在消息展示投影中传递，Flutter 负责渲染。`docs/tool-display-semantics.md:3`
- 工具名称、参数名称、运行平台和结果的自然语言文案都不用于推断展示语义。`docs/tool-display-semantics.md:3`
- Flutter 应用支持 Android、iOS、macOS、Windows、Linux、OHOS 与 Web。`docs/webview-rendering.md:3`
- 应用缩放与各浏览器的页面缩放相互独立。`docs/webview-rendering.md:4`
- 视觉上内容按应用缩放与页面缩放的乘积缩放。`docs/webview-rendering.md:5`
- 应用缩放回到 1x 时不重置浏览器已选的页面缩放。`docs/webview-rendering.md:6`

## AI 速览

- `ToolResultMap` — 内置工具名到结果类型的映射，展示声明与工具名和结果类型放在一起。`core/crates/plugin/sdk/src/js_sdk/tool_types.rs:10`
- `tool_display` — 过程宏属性，解析各字段的 `display` 属性。`core/crates/plugin/sdk-macros/src/lib.rs:58`
- `BuiltinToolName` 的 `display` — 按工具名字符串精确查找展示声明，未声明的工具返回 `None`。`core/crates/plugin/sdk-macros/src/lib.rs:118`
- `ToolDisplayDeclaration` — 展示声明，含本地化 `label`、语义 `icon`、可选 `target_parameter` 与 `result_renderer`。`core/crates/plugin/sdk/src/js_sdk/tool_display.rs:21`
- `ToolResultRenderer` — 结果视图选择器，取值为 `Directory`、`FileDiff` 与默认的 `Text`。`core/crates/plugin/sdk/src/js_sdk/tool_display.rs:9`
- `PackageTool` — 插件工具声明，`display` 为可选字段。`core/crates/plugin/sdk/src/package.rs:106`
- `WebViewScaleScope` — 提供应用缩放的 `InheritedWidget`。`apps/flutter/thirdparty/webview_all/lib/src/webview_widget.dart:24`
- `requiresNativeApplicationZoom` — 按后端能力选择缩放策略的开关，默认 `false`。`apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/platform_webview_controller.dart:360`
- `NativeWebViewZoom` — 组合页面缩放与应用缩放，用于无原生绘制缩放的视图。`apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/native_webview_zoom.dart:6`
- `OperitSafeWebView` — iOS 的 `WKWebView` 子类，布局前校验有限几何值。`apps/flutter/thirdparty/webview_flutter_wkwebview/darwin/webview_flutter_wkwebview/Sources/OperitWebViewSafety/include/OperitSafeWebView.h:11`
- 数据流向：工具所有者声明展示 → Core 传递声明与原生结果 → Flutter 按声明选视图并校验结构后渲染；应用缩放与页面缩放各自独立进入原生页面 API。`docs/tool-display-semantics.md:52`

## 核心机制

### 展示声明由谁写

- 内置工具的展示声明写在 SDK 的 `ToolResultMap` 字段上，`list_files` 的声明为 `action = "list"`、`icon = "folder"`、`target = "path"`、`result = "directory"`。`core/crates/plugin/sdk/src/js_sdk/tool_types.rs:10`
- `tool_display` 是 `operit_plugin_sdk_macros` 的过程宏属性，标注在 `ToolResultMap` 上。`core/crates/plugin/sdk/src/js_sdk/tool_types.rs:8`
- 宏生成的 `BuiltinToolName` 的 `display` 方法按工具名字符串精确匹配，未声明展示的工具返回 `None`。`core/crates/plugin/sdk-macros/src/lib.rs:118`
- `tool_display` 宏遇到未知的 `result` 取值时返回编译错误 `unknown result renderer`。`core/crates/plugin/sdk-macros/src/lib.rs:106`
- 插件工具的 `display` 是 `PackageTool` 的可选字段，类型为 `Option<ToolDisplayDeclaration>`。`core/crates/plugin/sdk/src/package.rs:106`
- 条件状态 `ToolPackageState` 的工具列表同样是 `Vec<PackageTool>`，与普通工具共用同一 `display` 声明格式。`core/crates/plugin/sdk/src/package.rs:104` `core/crates/plugin/sdk/src/package.rs:94`
- 没有 `display` 的工具使用通用展示。`docs/tool-display-semantics.md:48`
- 非法的 `display` 声明使元数据加载返回错误，不会静默丢弃对应工具。`docs/tool-display-semantics.md:48`
- Core 从当前运行时的有效插件声明读取展示信息，不向其他身份、节点或 Host 查询展示信息。`docs/tool-display-semantics.md:48`

### 内置声明与本地化资源的配合

- `ToolDisplayDeclaration` 的 `builtin` 方法从 `tool_display_labels.json` 加载本地化资源，`action` 是该文件的键。`core/crates/plugin/sdk/src/js_sdk/tool_display.rs:34`
- `tool_display_labels.json` 为 `list` 提供英文 `List` 与中文 `列出`。`core/crates/plugin/sdk/src/js_sdk/tool_display_labels.json:19`
- `tool_display_labels.json` 缺少 `action` 对应的资源时触发 panic。`core/crates/plugin/sdk/src/js_sdk/tool_display.rs:44`
- 测试断言 `ReadFile` 的 `display()` 结果 `target_parameter` 为 `path`、`icon` 为 `file`、`result_renderer` 为 `Text`。`core/crates/plugin/sdk/src/js_sdk/tool_display.rs:69`
- `ListFiles` 的 `display` 的 `result_renderer` 为 `Directory`。`core/crates/plugin/sdk/src/js_sdk/tool_display.rs:75`
- `ApplyFile` 的 `display` 的 `result_renderer` 为 `FileDiff`。`core/crates/plugin/sdk/src/js_sdk/tool_display.rs:82`

### 标签、图标与结果视图的选择

- 客户端解析 `label` 时依次选择完整语言标签、语言代码、`default`、`en`、首个声明文本。`apps/flutter/app/lib/ui/features/chat/components/part/ToolDisplayComponents.dart:160`
- 没有声明文本时显示原始工具名。`docs/tool-display-semantics.md:40`
- Rust 侧 `ToolResultRenderer` 用 `#[serde(other)]` 把未知值反序列化为 `Text`。`core/crates/plugin/sdk/src/js_sdk/tool_display.rs:12`
- `resultRenderer` 缺省或未知值时，Flutter 侧回退为通用文本视图 `ToolResultRenderer.text`。`apps/flutter/app/lib/ui/features/chat/components/part/ToolDisplayComponents.dart:148`
- Flutter 不根据工具名、返回值的 `__type` 或对象是否含有某些字段自动选择结果视图。`docs/tool-display-semantics.md:42`
- 目录视图读取含 `path` 与 `entries` 数组的结构，条目含 `name`、`isDirectory`、`size`。`docs/tool-display-semantics.md:44`
- 文件差异视图读取含 `operation` 与 `diffContent` 的结构，`operation` 含 `path` 与 `details`。`docs/tool-display-semantics.md:44`
- `icon` 支持 `file`、`folder`、`edit`、`delete`、`search`、`terminal`、`web`、`download`、`package`、`time`、`notification`、`clipboard`、`audio`。`docs/tool-display-semantics.md:46`
- `icon` 缺省时 Flutter 侧解析为通用工具图标 `tool`。`apps/flutter/app/lib/ui/features/chat/components/part/ToolDisplayComponents.dart:143`
- `icon` 不改变执行行为或权限。`docs/tool-display-semantics.md:46`

### 结果与消息链路

- Core 保留原生 `ToolResultData`，Flutter 只按工具声明的 `resultRenderer` 选择结果视图，然后校验数据结构。`docs/tool-display-semantics.md:52`
- 目录数据来自执行 Host 返回的数据，不扫描 Flutter 所在设备。`docs/tool-display-semantics.md:52`
- 声明为 `fileDiff` 的工具还可以使用显式 `<file-diff>` 协议。`docs/tool-display-semantics.md:52`
- 实时工具调用的展示声明附加在 Markdown XML 事件的 `display` 属性中。`docs/tool-display-semantics.md:54`
- `proxy` / `package_proxy` 只按其明确的 `tool_name`、`params` 协议解析目标。`docs/tool-display-semantics.md:54`
- `proxy` / `package_proxy` 的目标尚未完整到达时使用通用展示。`docs/tool-display-semantics.md:54`
- 展示声明和结果载荷分别保存在已有 `MessagePart.attributes` 的 `display`、`result_data` 属性中。`docs/tool-display-semantics.md:56`
- 通用文本视图不额外附加重复的结构化结果。`docs/tool-display-semantics.md:56`
- 完整结构化结果仅在现有单条工具结果预算内附加，超过预算时仍保留原有的有界文本结果。`docs/tool-display-semantics.md:56`
- 提供给模型的工具结果及历史序列化排除 `display` 和 `result_data`。`docs/tool-display-semantics.md:58`
- 工具分组继续使用既有 `ThinkToolsXmlNodeGrouper` / `ToolCallResultMergeRender` 机制。`docs/tool-display-semantics.md:58`

### 应用缩放与页面缩放为何独立

- `WebViewScaleScope` 是 `InheritedWidget`，其 `scale` 必须是祖先总缩放而非屏幕 DPR。`apps/flutter/thirdparty/webview_all/lib/src/webview_widget.dart:24`
- `PlatformWebViewController` 的 `requiresNativeApplicationZoom` 按后端能力选择策略，不由共享 widget 的 macOS-only 分支决定。`docs/webview-rendering.md:11`
- `requiresNativeApplicationZoom` 的默认值为 `false`。`apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/platform_webview_controller.dart:360`
- 需要原生内容缩放的后端返回 `true` 并实现 `setApplicationZoomFactor`，复合平台视图保持默认。`apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/platform_webview_controller.dart:357`
- `build` 在 `requiresNativeApplicationZoom` 为真时包一层 `_NativeZoomWebViewViewport`，否则直接返回原生视图。`apps/flutter/thirdparty/webview_all/lib/src/webview_widget.dart:151`
- `NativeWebViewZoom` 组合页面缩放与应用缩放，用于无原生绘制缩放的视图。`apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/native_webview_zoom.dart:6`
- `_apply` 把页面缩放因子与应用缩放因子相乘后交给 `_applyZoom` 发给原生。`apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/native_webview_zoom.dart:39`
- `_queue` 把原生缩放更新串行化。`apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/native_webview_zoom.dart:40`
- `_validate` 拒绝非有限或小于等于 0 的缩放因子，抛 `ArgumentError`。`apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/native_webview_zoom.dart:45`
- 原生覆盖后端在视口周围取消应用绘制缩放、按显示尺寸布局视口，并把 `applicationZoom * pageZoom` 发给原生页面 API。`docs/webview-rendering.md:26`
- 同一 widget 结构在所有缩放级别下保持不变，避免重建 platform view。`docs/webview-rendering.md:28`
- 复合后端保留应用绘制缩放，把应用因子再发给页面 API 会使内容缩放两次，因此其 capability flag 保持 `false`。`docs/webview-rendering.md:31`
- iframe 页面缩放实现不检查嵌入文档，支持跨域内容与禁用 JavaScript。`docs/webview-rendering.md:32`

### 各后端页面缩放方式

- macOS 的 WKWebView 后端使用未缩放原生视口加原生内容缩放，页面缩放走 WKWebView `pageZoom`。`docs/webview-rendering.md:16`
- Linux 的 WebKitGTK 后端使用未缩放原生视口加原生内容缩放，页面缩放走 WebKitGTK zoom level。`docs/webview-rendering.md:17`
- iOS 的 WKWebView 后端使用 Flutter/UIKit 复合，页面缩放走 WKWebView `pageZoom`。`docs/webview-rendering.md:18`
- Android 的 WebView 后端使用 Flutter 平台视图复合，页面缩放走既有 WebView zoom API。`docs/webview-rendering.md:19`
- Windows 的 WebView2 后端使用 Flutter/原生复合，页面缩放走 WebView2 zoom factor，指针转发使用 Flutter 本地坐标。`docs/webview-rendering.md:20`
- OHOS 的 ArkWeb 后端使用 Flutter/OHOS 平台视图复合，页面缩放走主帧 CSS zoom 的每引擎桥接。`docs/webview-rendering.md:21`
- Web 的 iframe 后端使用 Flutter/DOM 复合，页面缩放走裁剪、反向尺寸与缩放的 iframe。`docs/webview-rendering.md:22`
- 旧版 ArkWeb SDK 缺乏绝对原生浏览器缩放 API。`docs/webview-rendering.md:35`
- OHOS 页面缩放桥接使用页面级 CSS zoom，运行在应用的 JavaScript 已启用浏览器上。`docs/webview-rendering.md:36`
- OHOS 桥接在重置时恢复先前已有的内联根缩放。`docs/webview-rendering.md:38`
- 应用缩放本身不需要页面 JavaScript。`docs/webview-rendering.md:39`
- OHOS 控制器用 `NativeWebViewZoom` 只发页面缩放，因为平台视图已复合应用绘制缩放，再乘应用缩放会翻倍。`apps/flutter/thirdparty/webview_all_ohos/lib/src/ohos_webview_controller.dart:1099`

### Windows 复合与 iOS 几何

- Windows 上 WebView2 直接向 Windows 引擎提供 composition visual，原生浏览器显示使用 composition visual，不用 Flutter Texture 或连续截屏。`docs/webview-rendering.md:45`
- Windows 后端存储使用预乘 alpha 的 DXGI swapchain。`docs/webview-rendering.md:44`
- DirectComposition 用 `AddVisual(visual, FALSE, nullptr)` 按 Flutter 由后向前的绘制顺序追加图层。`docs/webview-rendering.md:48`
- Flutter 对话框与模态屏障必须覆盖浏览器并拦截指针输入。`docs/webview-rendering.md:49`
- SDK 版本钉在 `apps/flutter/app/.fvmrc`。`docs/webview-rendering.md:51`
- iOS 后端用 `OperitSafeWebView` 在 UIKit 布局前校验有限的 frame 与 bounds 值。`docs/webview-rendering.md:63`
- `OperitSafeWebView` 是 `WKWebView` 的子类。`apps/flutter/thirdparty/webview_flutter_wkwebview/darwin/webview_flutter_wkwebview/Sources/OperitWebViewSafety/include/OperitSafeWebView.h:11`
- 非法几何停用受影响的原生视图，`CALayerInvalidGeometry` 在 Objective-C 边界隔离，布局调用结束后经现有导航错误通道上报一次。`docs/webview-rendering.md:65`
- 失败的视图不再布局或复用。`docs/webview-rendering.md:67`

### 维护检查

- 维护检查从 `apps/flutter/app` 运行 `fvm flutter test test/application_zoom_webview_test.dart test/windows_native_composition_test.dart`。`docs/webview-rendering.md:74`
- `windows_native_composition_probe.dart` 是裁剪、排序、对话框与指针路由的独立验收夹具。`docs/webview-rendering.md:78`
- `webview_zoom.test.mjs` 检查脚本与通道契约。`docs/webview-rendering.md:80`

## 关键符号

- `ToolResultMap` — 内置工具名到结果类型的映射，展示声明写在字段的 `display` 属性上。`core/crates/plugin/sdk/src/js_sdk/tool_types.rs:10`
- `tool_display` — 过程宏属性，解析各字段的 `display` 属性。`core/crates/plugin/sdk-macros/src/lib.rs:58`
- `BuiltinToolName` 的 `display` — 精确查找展示声明，未声明者返回 `None`。`core/crates/plugin/sdk-macros/src/lib.rs:118`
- `ToolDisplayDeclaration` — 展示声明，含本地化 `label`、语义 `icon`、可选 `target_parameter` 与 `result_renderer`。`core/crates/plugin/sdk/src/js_sdk/tool_display.rs:21`
- `ToolResultRenderer` — 结果视图枚举，`Directory` / `FileDiff` / 默认 `Text`。`core/crates/plugin/sdk/src/js_sdk/tool_display.rs:9`
- `PackageTool` 的 `display` — 插件工具的可选展示声明。`core/crates/plugin/sdk/src/package.rs:106`
- `labelFor` — Flutter 侧标签回退解析，依次试完整语言标签、语言代码、`default`、`en`、首个声明文本。`apps/flutter/app/lib/ui/features/chat/components/part/ToolDisplayComponents.dart:160`
- `WebViewScaleScope` — 应用缩放作用域，不改变 host DPR。`docs/webview-rendering.md:10`
- `requiresNativeApplicationZoom` — 后端能力开关，默认 `false`。`apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/platform_webview_controller.dart:360`
- `NativeWebViewZoom` — 双因子缩放组合器，校验输入并串行化原生更新。`apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/native_webview_zoom.dart:6`
- `OperitSafeWebView` — iOS 安全 WebView，布局前校验几何值。`docs/webview-rendering.md:63`

## 调用链

1. 内置工具：`ToolResultMap` 字段的 `display` 属性 `core/crates/plugin/sdk/src/js_sdk/tool_types.rs:10` → `tool_display` 宏生成 `BuiltinToolName` 的 `display` 方法 `core/crates/plugin/sdk-macros/src/lib.rs:118` → `ToolDisplayDeclaration` 的 `builtin` 方法按 `action` 从 `tool_display_labels.json` 取本地化文本 `core/crates/plugin/sdk/src/js_sdk/tool_display.rs:34`
2. 插件工具：插件元数据的工具声明带可选 `display` → `PackageTool` 的 `display` 字段解析为 `ToolDisplayDeclaration` → Core 从当前运行时声明读取，不跨身份、节点或 Host 查询。`core/crates/plugin/sdk/src/package.rs:106`
3. 展示：Core 在消息展示投影中传递声明并保留原生 `ToolResultData` → Flutter 按声明的 `resultRenderer` 选视图并校验数据结构 → 实时调用的声明附加在 Markdown XML 事件的 `display` 属性中。`docs/tool-display-semantics.md:54`
4. 模型侧：提供给模型的工具结果及历史序列化排除 `display` 和 `result_data`。`docs/tool-display-semantics.md:58`
5. WebView 缩放：`WebViewScaleScope` 提供应用缩放 `apps/flutter/thirdparty/webview_all/lib/src/webview_widget.dart:24` → `WebViewWidget` `apps/flutter/thirdparty/webview_all/lib/src/webview_widget.dart:67` 的 `build` 按 `requiresNativeApplicationZoom` 决定是否包 `_NativeZoomWebViewViewport` `apps/flutter/thirdparty/webview_all/lib/src/webview_widget.dart:151`。
6. 乘积发给原生页面 API：原生覆盖后端经 `NativeWebViewZoom` 把 `applicationZoom * pageZoom` 发给原生页面 API `docs/webview-rendering.md:26`，复合后端保留应用绘制缩放。
7. iOS 几何：`OperitSafeWebView` 在 UIKit 布局前校验 frame 与 bounds → 非法几何停用原生视图，`CALayerInvalidGeometry` 经导航错误通道上报一次。`docs/webview-rendering.md:65`

## 来源

- `docs/tool-display-semantics.md`（seed，大纲指定）
- `docs/webview-rendering.md`（seed，大纲指定）
- `core/crates/plugin/sdk/src/js_sdk/tool_display.rs`（补定位：`ToolDisplayDeclaration` 与 `builtin` 加载逻辑）
- `core/crates/plugin/sdk/src/js_sdk/tool_types.rs`（补定位：`ToolResultMap` 上的 `display` 属性）
- `core/crates/plugin/sdk/src/js_sdk/tool_display_labels.json`（补定位：`action` 本地化资源）
- `core/crates/plugin/sdk/src/package.rs`（补定位：`PackageTool` 的 `display` 字段）
- `core/crates/plugin/sdk-macros/src/lib.rs`（补定位：`tool_display` 过程宏本体；宏实际位于 `sdk-macros` crate，不在 `core/crates/plugin/sdk` 目录内）
- `apps/flutter/app/lib/ui/features/chat/components/part/ToolDisplayComponents.dart`（核验：Flutter 侧 `labelFor` 回退顺序与 `resultRenderer` 回退）
- `apps/flutter/thirdparty/webview_all/lib/src/webview_widget.dart`（核验：`WebViewScaleScope` 与 `_NativeZoomWebViewViewport` 分支）
- `apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/platform_webview_controller.dart`（核验：`requiresNativeApplicationZoom` 默认值）
- `apps/flutter/thirdparty/webview_flutter_platform_interface/lib/src/native_webview_zoom.dart`（核验：`NativeWebViewZoom` 双因子、校验与串行化）
- `apps/flutter/thirdparty/webview_all_ohos/lib/src/ohos_webview_controller.dart`（核验：OHOS 只发页面缩放）
- `apps/flutter/thirdparty/webview_flutter_wkwebview/darwin/webview_flutter_wkwebview/Sources/OperitWebViewSafety/include/OperitSafeWebView.h`（核验：`OperitSafeWebView` 为 `WKWebView` 子类）
- 本页不涉及主题快照字段数，未写任何快照字段数字；大纲问的三个问题（展示信息由谁声明、内置声明与 `tool_display_labels.json` 如何配合、应用缩放与页面缩放为何独立）均在正文回答。
