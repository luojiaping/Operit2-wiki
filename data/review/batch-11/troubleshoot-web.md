---
title: 排障·Web 与 Web Access
module: dev
platforms: [all]
sources: 3
date: 2026-11-11
---

## 概述

- 本页回答三个问题：Web Access 如何部署与访问、浏览器 Host 与 WebAssembly 运行时的能力边界是什么、Web 端与桌面端渲染差异如何排查。`apps/flutter/app/web/README.md:1`
- Web Access 前端边界由 apps/flutter/app/web/ 目录拥有，该目录是 `web.operit.app` 的标准 Flutter Web 入口目录。`apps/flutter/app/web/README.md:44`
- 浏览器执行属于运行时宿主，会话是否存在不由工作区是否打开决定。`docs/browser-session-lifecycle.md:3`
- Flutter 应用支持 Android、iOS、macOS、Windows、Linux、OHOS 与 Web，应用缩放与各浏览器的页面缩放相互独立。`docs/webview-rendering.md:3`
- 本页事实均引自三份文档原文，属于文档声明，未逐项核验对应实现代码。`apps/flutter/app/web/README.md:1`

## AI 速览

- `web.operit.app` — Web Access 部署域名，部署服务器或反向代理必须发出三个跨域隔离头。`apps/flutter/app/web/README.md:14`
- `web_dev_config.yaml` — Flutter 开发服务器配置，配置内置开发服务器 `http://127.0.0.1:4835` 并发送三个跨域隔离头。`apps/flutter/app/web/README.md:18`
- `operit2 cli web open` — 打开 `https://web.operit.app/` 的入口，不启动本地服务器，不把凭据放进 URL。`apps/flutter/app/web/README.md:53`
- `runtime/src/` — TypeScript 源码及其编译器配置。`apps/flutter/app/web/README.md:47`
- `runtime/generated/` — 生成的 JavaScript/WASM 产物与 v86 客户机运行时。`apps/flutter/app/web/README.md:48`
- `runtime/vendor/` — MessagePack 等第三方静态文件。`apps/flutter/app/web/README.md:50`
- `WebViewScaleScope` — 在不改变宿主 DPR 的情况下提供应用缩放。`docs/webview-rendering.md:10`
- `PlatformWebViewController.requiresNativeApplicationZoom` — 按后端能力选择缩放策略。`docs/webview-rendering.md:11`
- `NativeWebViewZoom` — 保留应用缩放与页面缩放两个因子，校验输入并序列化原生更新。`docs/webview-rendering.md:26`
- `OperitSafeWebView` — iOS 后端在 UIKit 布局前校验有限的 frame 与 bounds 值。`docs/webview-rendering.md:63`
- `RuntimeBrowserOwnerSurfaceHost` — 为每个存活会话保留一个真实 WebView，始终位于全局宿主。`docs/browser-session-lifecycle.md:29`
- `WorkspaceBrowserSurface` — 普通浏览器与临时网页访问共用的展示入口。`docs/browser-session-lifecycle.md:30`
- `RuntimeWebVisitSession` — 收到请求时直接创建会话并开始加载、检测与提取。`docs/browser-session-lifecycle.md:38`
- `visit_web` — 总执行期限 45 秒的临时网页访问工具。`docs/browser-session-lifecycle.md:42`
- 主入口：开发运行从 `apps/flutter/app` 执行 `fvm flutter run -d edge`；已部署访问走 `https://web.operit.app/`。`apps/flutter/app/web/README.md:26` `apps/flutter/app/web/README.md:53`
- 数据流向：`browser_*` 工具 → `BrowserAutomationBridge` → `RuntimeBrowserOwnerHost` → `RuntimeBrowserOwner` 持有的 `WebViewController`。`docs/browser-session-lifecycle.md:11`
- 数据流向：`visit_web` 工具 → `WebVisitBridge` → `RuntimeWebVisitSession` → `BrowserSessions` 协议。`docs/browser-session-lifecycle.md:17`

## 核心机制

### Web Access 部署与访问

- 部署服务器必须为每个应用资产发送三个跨域隔离头，以便线程化 Sherpa ONNX WebAssembly 运行本地 STT 与 TTS。`apps/flutter/app/web/README.md:6`
- 三个头是 `Cross-Origin-Opener-Policy: same-origin`、`Cross-Origin-Embedder-Policy: require-corp`、`Cross-Origin-Resource-Policy: same-origin`。`apps/flutter/app/web/README.md:9`
- `web.operit.app` 的部署服务器或反向代理必须发出这三个头。`apps/flutter/app/web/README.md:14`
- CLI 对外暴露的 Link Access 服务器不提供 Web 前端。`apps/flutter/app/web/README.md:14`
- 跨域隔离头只启用跨域隔离，不开放对远程 API 的无限制 CORS 访问，远程 API 服务器仍须通过自身 CORS 策略授权开发源。`apps/flutter/app/web/README.md:37`
- `web_dev_config.yaml` 只配置 Flutter 开发服务器，已部署的托管须独立发送这些头。`apps/flutter/app/web/README.md:39`
- FVM 锁定的 Flutter SDK 原生读取 Flutter 应用根目录的 `web_dev_config.yaml`。`apps/flutter/app/web/README.md:18`
- `web_dev_config.yaml` 配置内置开发服务器 `http://127.0.0.1:4835`，并发送三个跨域隔离头。`apps/flutter/app/web/README.md:19`
- Flutter Web 开发不需要单独的 Node 进程或代理端口。`apps/flutter/app/web/README.md:21`
- 从 `apps/flutter/app` 运行 `fvm flutter run -d edge` 启动 Edge 开发运行。`apps/flutter/app/web/README.md:26`
- Chrome 开发运行使用 `fvm flutter run -d chrome`。`apps/flutter/app/web/README.md:29`
- 手动打开浏览器时使用 `fvm flutter run -d web-server`，然后打开 `http://127.0.0.1:4835`。`apps/flutter/app/web/README.md:30`
- edge、chrome、web-server 三种设备共享同一原生服务器配置，Flutter 调试连接与热重载直接使用该源。`apps/flutter/app/web/README.md:31`
- VS Code 里从 Run and Debug 选择 `Operit2: Web (isolated)` 并按 F5，经 FVM Flutter SDK 启动 Edge，无需预启动代理任务。`apps/flutter/app/web/README.md:34`
- 原生应用与 CLI 不打包、不提供 apps/flutter/app/web/ 目录。`apps/flutter/app/web/README.md:52`
- 设置入口与 `operit2 cli web open` 打开 `https://web.operit.app/`，不启动本地服务器，不把凭据放进 URL。`apps/flutter/app/web/README.md:53`
- 连接另一台设备是独立的节点监听/配对操作，不是 Web Access 服务器生命周期。`apps/flutter/app/web/README.md:54`
- 独立浏览器运行时保存在 `runtime/` 下并按用途拆分：`runtime/src/` 含 TypeScript 源码及编译器配置，`runtime/generated/` 含生成的 JavaScript/WASM 产物与 v86 客户机运行时，`runtime/vendor/` 含 MessagePack 等第三方静态文件。`apps/flutter/app/web/README.md:47`

### 浏览器 Host 与 WebAssembly 运行时能力边界

- 浏览器执行属于运行时宿主，会话是否存在不由工作区是否打开决定。`docs/browser-session-lifecycle.md:3`
- Android、iOS、macOS、Windows、Linux 共用相同的会话与展示生命周期，平台实现仍由现有 WebView 插件承担，Web 客户端通过现有会话协议观看宿主合成画面。`docs/browser-session-lifecycle.md:3`
- Core 会话及事件协议没有添加 Android 专用操作。`docs/browser-session-lifecycle.md:23`
- `RuntimeBrowserOwnerSurfaceHost` 为每个存活会话保留一个真实 WebView，始终位于全局宿主，打开、隐藏、切换工作区不迁移它的 Element，不重建平台视图。`docs/browser-session-lifecycle.md:29`
- `WorkspaceBrowserSurface` 是普通浏览器与临时网页访问共用的展示入口，原生展示提供 `RuntimeBrowserSurfaceTarget` 锚点，Web 展示继续使用已有的合成画面传输。`docs/browser-session-lifecycle.md:30`
- 锚点通过 RenderObject 的 attach、layout、detach 发布展示位置与大小，`RetainedPage` 隐藏嵌套页面时即使 widget 未 dispose 也释放锚点，恢复时重新提供锚点，不依赖休眠子树完成构建。`docs/browser-session-lifecycle.md:31`
- `RuntimeBrowserSurface` 在相同挂载位置跟随锚点，没有锚点时禁用绘制、触摸与语义，但保留 WebView 及最后的非零视口，首次后台创建使用宿主视口，不使用屏幕外 1×1 布局。`docs/browser-session-lifecycle.md:32`
- 锚点只表达展示权，不表达会话存活权，显式关闭会话才销毁浏览器，多个展示锚点使用最后注册的存活锚点，释放后可回到先前锚点。`docs/browser-session-lifecycle.md:33`
- TTS 与运行时浮层位于浏览器宿主之上，避免全局浏览器展示覆盖应用浮层。`docs/browser-session-lifecycle.md:34`
- 创建浏览器会话时，宿主打开标签的操作直接返回该标签的会话 ID，运行时按这个 ID 返回对应会话。`docs/browser-session-lifecycle.md:25`
- 并发创建与宿主尚未挂载时排队的创建各自保留返回值与错误。`docs/browser-session-lifecycle.md:25`
- 请求归属不得通过全局新增会话列表或当前活动标签推断，否则两个访问会绑定到同一会话，并在其中一个完成清理时影响另一个。`docs/browser-session-lifecycle.md:25`
- `RuntimeWebVisitSession` 在收到请求时直接创建会话并开始加载、检测与提取，工作区展示回调尚未注册或已被移除时执行仍可完成，后注册的工作区可以展示仍在执行的访问，展示失败只记录日志。`docs/browser-session-lifecycle.md:38`
- 工作区观察任务状态并提供手动提取、取消等操作，不拥有定时器、加载过程或工具返回的 Completer，工作区销毁不取消任务。`docs/browser-session-lifecycle.md:40`
- 用户明确关闭访问标签才取消该请求，正常完成、失败与取消都会关闭临时会话，创建请求迟到时也会关闭已经失去任务所有者的会话。`docs/browser-session-lifecycle.md:40`
- `visit_web` 总执行期限为 45 秒，单次脚本与清理分别最多 10 秒，为 Rust 宿主现有的 60 秒请求期限留出返回时间。`docs/browser-session-lifecycle.md:42`
- 脚本等待同时观察任务完成，取消时释放本地超时，事件订阅取消与会话关闭同时发起，避免互相等待。`docs/browser-session-lifecycle.md:42`
- `browser_wait_for` 的文本条件由宿主进行限时轮询，不依赖页面内定时器或原生 WebView 对 Promise 返回值的处理。`docs/browser-session-lifecycle.md:42`
- 宿主交互订阅并发处理请求，`visit_web` 等待期间仍可处理它发起的浏览器会话命令。`docs/browser-session-lifecycle.md:23`
- Web Host 的完整实现见 [[host-web|Web/WASM Host]]，桌面端排障见 [[troubleshoot-desktop|排障·桌面端（Windows / macOS / Linux）]]。`docs/browser-session-lifecycle.md:3`

### Web 端与桌面端渲染差异排查

- 应用缩放与各浏览器的页面缩放相互独立，视觉上内容按两者乘积缩放，应用缩放回到 1x 时不得重置浏览器已选的页面缩放。`docs/webview-rendering.md:4`
- `WebViewScaleScope` 在不改变宿主 DPR 的情况下提供应用缩放。`docs/webview-rendering.md:10`
- `PlatformWebViewController.requiresNativeApplicationZoom` 按后端能力选择策略，不是共享 widget 里的 macOS 专属分支。`docs/webview-rendering.md:11`
- macOS / WKWebView 后端使用未缩放原生视口加原生内容缩放，页面缩放用 WKWebView pageZoom，AppKit 使用仅平移的原生帧。`docs/webview-rendering.md:16`
- Linux / WebKitGTK 后端使用未缩放原生视口加原生内容缩放，页面缩放用 WebKitGTK zoom level，GTK 收到仅平移的帧，不做不支持的缩放隐藏。`docs/webview-rendering.md:17`
- iOS / WKWebView 后端使用 Flutter/UIKit 合成，页面缩放用 WKWebView pageZoom，输入映射沿用已有 UIKit 平台视图映射。`docs/webview-rendering.md:18`
- Android / WebView 后端使用 Flutter 平台视图合成，页面缩放用已有 WebView zoom API，输入映射沿用已有平台视图输入映射。`docs/webview-rendering.md:19`
- Windows / WebView2 后端使用 Flutter/原生合成，页面缩放用 WebView2 zoom factor，指针转发使用 Flutter 本地坐标。`docs/webview-rendering.md:20`
- OHOS / ArkWeb 后端使用 Flutter/OHOS 平台视图合成，页面缩放经每引擎桥接用主帧 CSS zoom，输入映射沿用已有平台视图输入映射。`docs/webview-rendering.md:21`
- Web / iframe 后端使用 Flutter/DOM 合成，页面缩放用裁剪、反向定尺寸并缩放的 iframe，浏览器 DOM 变换映射指针输入，含跨域帧。`docs/webview-rendering.md:22`
- 原生覆盖后端在视口周围抵消应用绘制缩放，按显示尺寸布局视口，并把 `applicationZoom * pageZoom` 发给原生页面 API。`docs/webview-rendering.md:26`
- `NativeWebViewZoom` 保留应用缩放与页面缩放两个因子，校验输入并序列化原生更新，同一 widget 结构在所有缩放下保持不变，避免重建平台视图。`docs/webview-rendering.md:26`
- 合成后端保留应用绘制缩放，把应用因子再发给页面 API 会导致内容缩放两次，因此其能力标志保持 false。`docs/webview-rendering.md:30`
- iframe 页面缩放实现不检查嵌入文档，支持跨域内容与禁用 JavaScript 的页面。`docs/webview-rendering.md:33`
- 较旧的 ArkWeb SDK 缺少绝对原生浏览器缩放 API，OHOS 页面缩放桥因此对应用的 JavaScript 已启用浏览器使用整页 CSS zoom。`docs/webview-rendering.md:36`
- OHOS 页面缩放桥把主帧 document-start 脚本与用户脚本分开保留，对当前文档应用缩放，重置时恢复已有的内联根缩放。`docs/webview-rendering.md:38`
- 应用缩放本身不要求页面 JavaScript。`docs/webview-rendering.md:39`
- WebView2 直接向 Windows 引擎提供合成视觉，Flutter 平台视图层决定放置、变换、裁剪与绘制顺序。`docs/webview-rendering.md:42`
- Windows 后备存储使用预乘 alpha 的 DXGI 交换链，原生浏览器显示使用合成视觉，不用 Flutter Texture，不做连续屏幕捕获。`docs/webview-rendering.md:44`
- ANGLE 保持帧缓冲方向，DirectComposition 按 Flutter 由后向前的绘制顺序用 `AddVisual(visual, FALSE, nullptr)` 追加图层。`docs/webview-rendering.md:48`
- Flutter 对话框与模态屏障必须覆盖浏览器并拦截指针输入。`docs/webview-rendering.md:49`
- iOS 后端用 `OperitSafeWebView` 在 UIKit 布局前校验有限的 frame 与 bounds 值。`docs/webview-rendering.md:63`
- 无效几何尺寸会禁用受影响的原生视图，`CALayerInvalidGeometry` 在 Objective-C 边界隔离，并在布局调用结束后经已有导航错误通道上报一次。`docs/webview-rendering.md:65`
- 失败的 iOS 视图不再布局、不再复用。`docs/webview-rendering.md:67`
- 引擎或 SDK 变更后，原生渲染、IME 与手势行为必须在对应设备上检查。`docs/webview-rendering.md:81`
- Flutter 测试验证共享生命周期与控制器契约，各平台真实 WebView 的渲染、输入与后台行为仍需设备验证。`docs/browser-session-lifecycle.md:46`

### 维护检查命令

- SDK 版本锁定在 `apps/flutter/app/.fvmrc`，SDK 与应用命令从 `apps/flutter/app` 运行。`docs/webview-rendering.md:51`
- Windows 构建命令依次是 `fvm install --skip-pub-get`、`fvm flutter precache --windows`、`fvm flutter pub get`、`fvm flutter run -d windows`。`docs/webview-rendering.md:55`
- 维护检查命令是 `fvm flutter test test/application_zoom_webview_test.dart test/windows_native_composition_test.dart`，从 `apps/flutter/app` 运行。`docs/webview-rendering.md:74`
- 浏览器端缩放检查命令是 `fvm flutter test test/webview_zoom_browser_test.dart --platform chrome`。`docs/webview-rendering.md:75`
- `windows_native_composition_probe.dart` 是裁剪、排序、对话框与指针路由的独立验收夹具。`docs/webview-rendering.md:79`
- `webview_zoom.test.mjs` 检查脚本与通道契约。`docs/webview-rendering.md:80`
- Flutter 测试覆盖并发创建的正序与逆序返回、排队创建及错误传播、未打开工作区的访问、延迟展示、展示异常、并发完成与取消、迟到创建、脚本无响应、嵌套休眠、视图实例保持和偏移后的触摸命中。`docs/browser-session-lifecycle.md:46`

## 关键符号

- `web.operit.app` — Web Access 部署域名。`apps/flutter/app/web/README.md:14`
- `web_dev_config.yaml` — Flutter 开发服务器配置。`apps/flutter/app/web/README.md:18`
- `operit2 cli web open` — 打开 `https://web.operit.app/` 的入口。`apps/flutter/app/web/README.md:53`
- `runtime/src/` — TypeScript 源码及其编译器配置。`apps/flutter/app/web/README.md:47`
- `runtime/generated/` — 生成的 JavaScript/WASM 产物与 v86 客户机运行时。`apps/flutter/app/web/README.md:48`
- `runtime/vendor/` — MessagePack 等第三方静态文件。`apps/flutter/app/web/README.md:50`
- `WebViewScaleScope` — 在不改变宿主 DPR 的情况下提供应用缩放。`docs/webview-rendering.md:10`
- `PlatformWebViewController.requiresNativeApplicationZoom` — 按后端能力选择缩放策略。`docs/webview-rendering.md:11`
- `NativeWebViewZoom` — 保留两个缩放因子，校验输入并序列化原生更新。`docs/webview-rendering.md:26`
- `OperitSafeWebView` — iOS 后端校验有限 frame 与 bounds 值的视图。`docs/webview-rendering.md:63`
- `CALayerInvalidGeometry` — iOS 几何异常，在 Objective-C 边界隔离并经导航错误通道上报一次。`docs/webview-rendering.md:65`
- `RuntimeBrowserOwnerSurfaceHost` — 为每个存活会话保留一个真实 WebView。`docs/browser-session-lifecycle.md:29`
- `WorkspaceBrowserSurface` — 普通浏览器与临时网页访问共用的展示入口。`docs/browser-session-lifecycle.md:30`
- `RuntimeBrowserSurfaceTarget` — 原生展示提供的展示锚点。`docs/browser-session-lifecycle.md:30`
- `RuntimeBrowserSurface` — 在相同挂载位置跟随锚点的展示面。`docs/browser-session-lifecycle.md:32`
- `RuntimeWebVisitSession` — 收到请求时直接创建会话并开始加载、检测与提取。`docs/browser-session-lifecycle.md:38`
- `RuntimeBrowserSessionRegistry` — `browser_*` 链路中的会话注册表。`docs/browser-session-lifecycle.md:11`
- `RuntimeWebVisitRegistry` — `visit_web` 链路中的临时访问注册表。`docs/browser-session-lifecycle.md:17`
- `BrowserSessions` — create / evaluate / events / close 协议。`docs/browser-session-lifecycle.md:17`
- `browser_wait_for` — 文本条件由宿主限时轮询的等待工具。`docs/browser-session-lifecycle.md:42`

## 调用链

1. 部署访问：部署服务器或反向代理为每个应用资产发送三个跨域隔离头 → 浏览器打开 `https://web.operit.app/` → 线程化 Sherpa ONNX WebAssembly 运行本地 STT 与 TTS。`apps/flutter/app/web/README.md:6` `apps/flutter/app/web/README.md:53`
2. 开发运行：从 `apps/flutter/app` 执行 `fvm flutter run -d edge`（或 `-d chrome`、`-d web-server`）→ `web_dev_config.yaml` 配置的内置服务器在 `http://127.0.0.1:4835` 发送三个跨域隔离头 → Flutter 调试连接与热重载使用该源。`apps/flutter/app/web/README.md:19` `apps/flutter/app/web/README.md:26`
3. `browser_*` 工具 → `StandardBrowserAutomationTools` / `BrowserAutomationHost` → `FlutterHostAdapters` → `RuntimeHostInteractionService` → `RuntimeHostInteractionSubscriber` → `BrowserAutomationBridge` → `RuntimeBrowserOwnerHost` → `RuntimeBrowserSessionRegistry` → `RuntimeBrowserOwner` 持有的 `WebViewController`。`docs/browser-session-lifecycle.md:11`
4. `visit_web` 工具 → `FlutterHostAdapters` → `RuntimeHostInteractionService` → `RuntimeHostInteractionSubscriber` → `WebVisitBridge` → `RuntimeBrowserOwnerHost` → `RuntimeWebVisitRegistry` / `RuntimeWebVisitSession` → `BrowserSessions`（create / evaluate / events / close 协议）→ `RuntimeBrowserService` → 同一个 `RuntimeBrowserOwner`。`docs/browser-session-lifecycle.md:17`
5. 展示链路：`RuntimeBrowserOwnerSurfaceHost` 为存活会话保留真实 WebView → `WorkspaceBrowserSurface` 经 `RuntimeBrowserSurfaceTarget` 锚点展示，原生展示用锚点，Web 展示用已有合成画面传输。`docs/browser-session-lifecycle.md:30`
6. 缩放链路（原生覆盖后端）：视口周围抵消应用绘制缩放，按显示尺寸布局视口 → `NativeWebViewZoom` 把 `applicationZoom * pageZoom` 发给原生页面 API。`docs/webview-rendering.md:26`
7. 超时链路：`visit_web` 总期限 45 秒，单次脚本与清理分别最多 10 秒，为 Rust 宿主现有的 60 秒请求期限留出返回时间。`docs/browser-session-lifecycle.md:42`

## 来源

- `apps/flutter/app/web/README.md`（55 行）：Web Access 部署、开发运行、运行时布局。`apps/flutter/app/web/README.md:1`
- `docs/webview-rendering.md`（82 行）：WebView 渲染策略、七后端缩放表、Windows 合成、iOS 几何、维护检查。`docs/webview-rendering.md:1`
- `docs/browser-session-lifecycle.md`（46 行）：浏览器会话与工作区展示生命周期、请求链路、超时与回归验证。`docs/browser-session-lifecycle.md:1`
- 本页事实均引自上述三份文档原文，属于文档声明，未逐项核验对应实现代码。`apps/flutter/app/web/README.md:1`
- `docs/browser-session-lifecycle.md` 在大纲备注中列为待补测 seed，实测 46 行，已纳入本页 seed。`docs/browser-session-lifecycle.md:1`
- 否定性核验：2026-11-12 对基线 `364d1d594` 的本地 checkout 执行 `ls docs/openharmony-flutter-adaptation-checklist.md`，返回 No such file or directory，该文件在 HEAD 上不存在，本页未引用它。`docs/browser-session-lifecycle.md:1`
