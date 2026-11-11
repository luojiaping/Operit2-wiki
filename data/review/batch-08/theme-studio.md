---
title: Theme Studio 预览协议 v1
module: theme
platforms: [web]
sources: [4]
date: 2026-11-11
---

## 概述

- Theme Studio 预览协议 v1 是 Theme Studio 与独立 Flutter Web + Rust/WASM 预览核（`client-shell-v7`）之间的同源 `MessagePort` 协议与二进制导出规范。`docs/theme-studio-protocol-v1.md:3`
- 主题作者只提供声明式 `JSON`、`PNG`/`JPEG`、受限静态 `SVG` 和静态 `TrueType`（`.ttf`）字节，不含任何可执行脚本。`docs/theme-studio-protocol-v1.md:7`
- 协议文档把 TypeScript 通道 `tools/theme/studio_message_port.ts`、预览 JS Worker `theme_contract_worker.js`、Dart 预览壳 `tools/theme/preview` 与 `wasm-bindgen` 胶水列为受信任的应用代码。`docs/theme-studio-protocol-v1.md:8`
- Studio 侧以 TypeScript 实现。`docs/theme-studio-protocol-v1.md:8`
- 预览核在自身同源 Rust/WASM Worker 中独立执行闭合 JSON Schema/语义校验以及与客户端导入完全一致的 `L4` 图片/SVG/字体/九宫格像素检查，校验通过后才允许调用 Flutter 图片解码与 `FontLoader`；媒体校验细节见 [[theme-render|主题渲染与媒体校验]]。`docs/theme-studio-protocol-v1.md:10`
- 父页声称的 `themeSha256` 或素材 SHA-256 仅用于一致性比对，不授予媒体解析权限。`docs/theme-studio-protocol-v1.md:9`
- `wasm.rs` 是指向同一原生契约实现的轻量浏览器绑定，生成确定性字节，但不批准包也不安装包。`core/crates/plugin/theme/src/wasm.rs:1`
- client-shell 回执不是跨平台 1:1 截图或整场景一致性/导出授权，最终界面需要两者。`tools/theme/studio_message_port.ts:427`

## AI 速览

- `ThemeStudioMessagePort` — Studio 侧协议通道，单次握手、校验回执、管理 revision 与捕获。`tools/theme/studio_message_port.ts:57`
- `ThemeStudioChannelOptions` — 建通道的配置：iframe、预览 URL、nonce、渲染版本与 fixture 摘要。`tools/theme/studio_message_port.ts:46`
- `ThemeContractBridge` — Rust/WASM 契约桥：`normalizeDraft`、`validatePreview`、`exportPackage`。`tools/theme/studio_message_port.ts:37`
- `ThemePreviewAsset` — 预览资产：`path`、`mediaType`、`sha256` 与 `Uint8Array` 字节。`tools/theme/studio_message_port.ts:2`
- `ClientShellReceipt` — 渲染帧回执：client-shell 作用域、`parityVerified`、`revision`、字体与资产摘要。`tools/theme/studio_message_port.ts:9`
- `ThemeStudioMessage` — 七种预览侧消息的联合类型。`tools/theme/studio_message_port.ts:23`
- `Header` — 固定消息头：`protocolVersion`、`nonce`、`rendererReleaseId`。`tools/theme/studio_message_port.ts:22`
- `exportWithContract` — 原始契约导出：先校验草稿再导出。`tools/theme/studio_message_port.ts:429`
- `isSha256` — SHA-256 格式校验：小写十六进制 64 位。`tools/theme/studio_message_port.ts:437`
- `isViewport` — 视口边界校验：宽 240～2400、高 360～2400。`tools/theme/studio_message_port.ts:438`
- `checkReceipt` — 渲染回执校验：作用域、哈希、字体与资产摘要逐项核对。`tools/theme/studio_message_port.ts:364`
- `ThemePreviewValidationReceipt` — 预览校验收据：`validator_version`、`theme_sha256`、`files`、`media`、`trust`。`core/crates/plugin/theme/src/preview.rs:22`
- `ValidatedThemePreview` — 校验通过后的密封预览：私有构造，只读访问主题、收据与文件字节。`core/crates/plugin/theme/src/preview.rs:33`
- `validate_theme_preview_transfer` — 预览校验入口：先规范化草稿，再解析资产传输并完整校验。`core/crates/plugin/theme/src/preview.rs:152`
- `parse_asset_transfer` — 解析闭合资产目录与连续二进制负载。`core/crates/plugin/theme/src/preview.rs:112`
- `normalizeThemeDraft` — 校验并展开编辑态草稿默认值，返回 `canonicalThemeJson` 与 `themeSha256`。`docs/theme-studio-protocol-v1.md:73`
- `validateThemePreviewDraft` — 接收闭合资产目录与连续二进制缓冲区，执行完整契约与 `L4` 媒体校验，返回规范化 JSON 与 `ThemePreviewValidationReceipt`。`docs/theme-studio-protocol-v1.md:74`
- `exportToolPkgFromTheme` — 生成固定顺序、固定 DOS 时间戳与权限的 Stored ZIP（`.toolpkg`），返回前用 `validate_toolpkg_theme_templates` 自检。`docs/theme-studio-protocol-v1.md:75`
- `validateAuthoredToolPkg` — 导出已有 ToolPkg 时校验合并后归档的全部模板，校验失败时不提供下载。`docs/theme-studio-protocol-v1.md:76`
- 主入口函数：Studio 侧为 `connect`。`tools/theme/studio_message_port.ts:106`
- 校验入口函数：`validate_theme_preview_transfer`。`core/crates/plugin/theme/src/preview.rs:152`
- 数据流向一句话：Studio 发送加载消息 → 预览核执行 Rust/WASM 校验 → Flutter 绘制真实帧 → 返回渲染回执。`docs/theme-studio-protocol-v1.md:48`

## 核心机制

- **信任边界**：主题作者只提供声明式 `JSON`、`PNG`/`JPEG`、受限静态 `SVG` 和静态 `TrueType`（`.ttf`）字节，不含任何可执行脚本。`docs/theme-studio-protocol-v1.md:7`
- **信任边界**：协议文档把 TypeScript 通道 `tools/theme/studio_message_port.ts`、预览 JS Worker `theme_contract_worker.js`、Dart 预览壳 `tools/theme/preview` 与 `wasm-bindgen` 胶水列为受信任的应用代码。`docs/theme-studio-protocol-v1.md:8`
- **信任边界**：父页声称的 `themeSha256` 或素材 SHA-256 仅用于一致性比对，不授予媒体解析权限。`docs/theme-studio-protocol-v1.md:9`
- **信任边界**：预览核在自身同源 Rust/WASM Worker 中独立执行闭合 JSON Schema/语义校验以及与客户端导入完全一致的 `L4` 图片/SVG/字体/九宫格像素检查，校验通过后才允许调用 Flutter 图片解码与 `FontLoader`。`docs/theme-studio-protocol-v1.md:10`
- **信任边界**：协议规定 `SVG` 仅支持标准命名空间下的路径、基本图形、分组、渐变和本地 `clip`/`paint` 引用，上限为 1 MiB、512 个元素、32 层深、4096×4096 且不超过 16,777,216 像素。`docs/theme-studio-protocol-v1.md:11`
- **信任边界**：协议规定 `SVG` 拒绝 `DTD`/实体、脚本、事件属性、`CSS/style`、外链、`foreignObject`、滤镜、动画、嵌入式文档和未知属性。`docs/theme-studio-protocol-v1.md:11`
- **信任边界**：`ValidatedThemePreview` 私有构造，调用方提供的哈希不能授予媒体权限。`core/crates/plugin/theme/src/preview.rs:30`
- **信任边界**：`ValidatedThemePreview` 既不是渲染回执，也不是可安装包。`core/crates/plugin/theme/src/preview.rs:31`
- **信任边界**：`wasm.rs` 是指向同一原生契约实现的轻量浏览器绑定，生成确定性字节，但不批准包也不安装包。`core/crates/plugin/theme/src/wasm.rs:1`
- **握手**：Studio 加载部署生成的 `theme-studio-config.json` / `renderer-release.json`，获取固定的 `rendererReleaseId`、`fixtureVersion` 与 `fixtureSourceSha256`，并先订阅 `window.message`。`docs/theme-studio-protocol-v1.md:15`
- **握手**：Studio 将 `iframe.src` 指向同源 `/theme-preview/<rendererReleaseId>/?studioOrigin=<origin>&nonce=<nonce>&rendererReleaseId=<id>`。`docs/theme-studio-protocol-v1.md:16`
- **握手**：预览核在自身 Rust/WASM Worker 启动就绪后，向 `window.parent` 发送 `operit.theme.preview.available.v1`。`docs/theme-studio-protocol-v1.md:17`
- **握手**：Studio 通过 `operit.theme.studio.connect.v1` 向子页转移唯一一个 `MessagePort`。`docs/theme-studio-protocol-v1.md:18`
- **握手**：子页核对 exact origin、`window.parent` 消息源、相同协议头、单一端口且无既有连接后，在私有端口返回 `operit.theme.preview.ready.v1` 与 `nextRevision`。`docs/theme-studio-protocol-v1.md:19`
- **握手**：所有协议消息携带固定头部 `protocolVersion`: 1、`nonce`（16～128 个 URL-safe 字符，由 Studio 用加密安全随机源生成）与 `rendererReleaseId`（当前固定的构建版本 ID）。`docs/theme-studio-protocol-v1.md:24`
- **握手**：初始内置样例占用 `revision` 1，Studio 从 `nextRevision` 开始递增，通道不可重复握手或在致命协议错误后复用。`docs/theme-studio-protocol-v1.md:29`
- **握手**：单次 `Worker` 契约操作超时为 15 秒，首次 Flutter Web 场景帧等待上限为 60 秒。`docs/theme-studio-protocol-v1.md:29`
- **握手**：构造函数要求 `previewUrl` 协议为 `http:` 或 `https:`，且无用户名、口令与 hash。`tools/theme/studio_message_port.ts:83`
- **握手**：构造函数要求 `nonce` 匹配 `/^[A-Za-z0-9_-]{16,128}$/`。`tools/theme/studio_message_port.ts:85`
- **握手**：构造函数要求 `rendererReleaseId` 匹配 `/^[A-Za-z0-9._-]{1,128}$/`，且 `fixtureVersion` 非空、`fixtureSourceSha256` 通过 `isSha256` 校验。`tools/theme/studio_message_port.ts:86`
- **握手**：`ThemeStudioMessagePort` 的状态机为 `idle`、`connecting`、`connected`、`failed`、`closed` 五态。`tools/theme/studio_message_port.ts:61`
- **握手**：`connect` 在 state 不为 `idle` 时抛 already-connected，通道为单次使用。`tools/theme/studio_message_port.ts:107`
- **握手**：握手先订阅 `window.message` 并启动 `port1`。`tools/theme/studio_message_port.ts:117`
- **握手**：`connect` 把 `studioOrigin`、`nonce` 与 `rendererReleaseId` 写进预览 URL 查询参数后才设置 `iframe.src`。`tools/theme/studio_message_port.ts:122`
- **握手**：连接启动定时器 `connectTimer` 为 15_000 毫秒，超时以 preview-startup-timeout 失败。`tools/theme/studio_message_port.ts:121`
- **握手**：`onWindowMessage` 仅接受 origin 等于预览 URL origin 且 source 为 `iframe.contentWindow` 的消息。`tools/theme/studio_message_port.ts:128`
- **握手**：收到 available.v1 后 Studio 以 `operit.theme.studio.connect.v1` 向预览窗口转移唯一一个端口（`channel.port2`）。`tools/theme/studio_message_port.ts:143`
- **握手**：收到 ready.v1 后把 `requestedRevision` 置为 `nextRevision` 减 1，状态转为 connected 并移除 `window.message` 监听。`tools/theme/studio_message_port.ts:319`
- **握手**：响应 `revision` 小于已请求 revision 时被忽略，不等于已请求 revision 时抛错。`tools/theme/studio_message_port.ts:328`
- **握手**：`requireHeader` 要求消息 `protocolVersion` 为 1 且 `rendererReleaseId` 与配置一致，否则抛协议或渲染版本不匹配错误。`tools/theme/studio_message_port.ts:389`
- **握手**：`fail` 把状态置为 failed、清空 `renderedReceipt`、拒绝待处理捕获与就绪等待，并向 handler 发送 error.v1。`tools/theme/studio_message_port.ts:401`
- **握手**：`close` 把状态置为 closed 并清空 `renderedReceipt`。`tools/theme/studio_message_port.ts:417`
- **加载与校验**：`operit.theme.preview.load.v1` 的 `revision` 为递增安全整数。`docs/theme-studio-protocol-v1.md:36`
- **加载与校验**：`canonicalThemeJson` 是 Rust `normalizeThemeDraft` 输出的完整规范化 JSON 字符串。`docs/theme-studio-protocol-v1.md:37`
- **加载与校验**：`themeSha256` 是该规范化 UTF-8 字节的 SHA-256。`docs/theme-studio-protocol-v1.md:38`
- **加载与校验**：`brightness` 为 "light" | "dark"，是预览环境亮暗模式，不写入 `theme.json`。`docs/theme-studio-protocol-v1.md:39`
- **加载与校验**：协议列出四组 `viewport` 取值：1280×800、390×844、768×1024、1440×900。`docs/theme-studio-protocol-v1.md:40`
- **加载与校验**：`showConversation` 为 boolean 固定场景对话开关，Studio 默认开启 true，不写入 `theme.json`。`docs/theme-studio-protocol-v1.md:41`
- **加载与校验**：`assets` 数组每项含 `path`、`mediaType`、`sha256` 与 `Uint8Array` 类型的 `bytes`。`docs/theme-studio-protocol-v1.md:42`
- **加载与校验**：素材通过 structured clone 的 `Uint8Array` 传输，不使用 `base64` 或 `JSON` 整数数组。`docs/theme-studio-protocol-v1.md:45`
- **加载与校验**：新 `revision` 一经接收立即撤销旧回执。`docs/theme-studio-protocol-v1.md:45`
- **加载与校验**：加载执行链路为 `reserve revision` → preview-owned Rust/WASM validation → verify normalization + immutable asset receipt → prepare global/user/AI fonts and glyph coverage + decode images → `operit.theme.preview.loaded.v1` → actual Flutter post-frame callback → `operit.theme.preview.rendered.v1`。`docs/theme-studio-protocol-v1.md:48`
- **加载与校验**：`operit.theme.preview.loaded.v1` 仅表示资源准备完成。`docs/theme-studio-protocol-v1.md:54`
- **加载与校验**：`operit.theme.preview.rendered.v1` 在真实 Flutter 帧绘制完成后发出，绑定同一 `revision`、`fixtureVersion`、`fixtureSourceSha256`、`themeSha256`、`brightness`、`viewport`、`showConversation`、完整资产摘要与字体摘要。`docs/theme-studio-protocol-v1.md:54`
- **加载与校验**：字体摘要按 `global`、probe monospace、`user`、`AI` 顺序返回四项。`docs/theme-studio-protocol-v1.md:54`
- **加载与校验**：`loadTheme` 要求 `revision` 为安全整数且严格大于已请求 revision，否则抛 stale-revision。`tools/theme/studio_message_port.ts:150`
- **加载与校验**：新 revision 收到后立即清空 `renderedReceipt`，并以 `superseded` 拒绝待处理捕获。`tools/theme/studio_message_port.ts:159`
- **加载与校验**：草稿要求 `themeSha256` 为 SHA-256、`canonicalThemeJson` 不超过 256 KiB、资产数不超过 24。`tools/theme/studio_message_port.ts:165`
- **加载与校验**：草稿要求 `brightness` 仅为 `light` 或 `dark`，`showConversation` 为 boolean。`tools/theme/studio_message_port.ts:169`
- **加载与校验**：草稿要求 `viewport` 通过 `isViewport` 校验。`tools/theme/studio_message_port.ts:175`
- **加载与校验**：`isViewport` 要求宽 240～2400、高 360～2400 的安全整数。`tools/theme/studio_message_port.ts:441`
- **加载与校验**：草稿要求规范化主题含 `typography`，且 `global` 为字符串，`user` 与 `ai` 为字符串或 null。`tools/theme/studio_message_port.ts:183`
- **加载与校验**：期望字体顺序为 `typography.global`、`cascadia-mono`、`typography.user`（为空时用 global）、`typography.ai`（为空时用 global）。`tools/theme/studio_message_port.ts:189`
- **加载与校验**：每个资产的 `bytes` 必须为 `Uint8Array`。`tools/theme/studio_message_port.ts:194`
- **加载与校验**：每个资产要求 `sha256` 有效、字节非空、单资产不超过 32 MiB、总字节不超过 128 MiB、路径唯一。`tools/theme/studio_message_port.ts:197`
- **加载与校验**：渲染定时器 `renderTimer` 为 60_000 毫秒，超时以 preview-render-timeout 失败。`tools/theme/studio_message_port.ts:210`
- **加载与校验**：`requestReceipt` 在未加载已校验草稿时抛 no-draft。`tools/theme/studio_message_port.ts:259`
- **加载与校验**：`ThemePreviewAsset` 的 `mediaType` 仅取 "image/png" | "image/jpeg" | "image/svg+xml" | "font/ttf" 四值。`tools/theme/studio_message_port.ts:4`
- **加载与校验**：`ThemePreviewAsset` 每项含 `path`、`mediaType`、`sha256` 与 `Uint8Array` 类型的 `bytes`。`tools/theme/studio_message_port.ts:4`
- **加载与校验**：`ClientShellReceipt` 的 `scope` 固定为 "client-shell"，且含 `parityVerified` 布尔字段。`tools/theme/studio_message_port.ts:11`
- **加载与校验**：渲染帧回执的 `fonts` 数组每项含 `reference`、`sha256`、`family` 与 `bytes`。`tools/theme/studio_message_port.ts:19`
- **加载与校验**：渲染帧回执的 `assetSha256` 为路径到 SHA-256 的映射。`tools/theme/studio_message_port.ts:20`
- **加载与校验**：`Header` 为 `protocolVersion`: 1、`nonce` 与 `rendererReleaseId`；`ThemeStudioMessage` 联合类型覆盖 ready.v1、progress.v1、loaded.v1、rendered.v1、captured.v1、selection.v1 与 error.v1 七种预览侧消息。`tools/theme/studio_message_port.ts:25`
- **加载与校验**：`isSha256` 要求字符串匹配小写十六进制 64 位（`/^[a-f0-9]{64}$/`）。`tools/theme/studio_message_port.ts:437`
- **加载与校验**：`validate_theme_preview_draft` 先调用 `normalize_draft` 规范化草稿。`core/crates/plugin/theme/src/preview.rs:50`
- **加载与校验**：`validate_theme_preview_draft` 在资产数超过 `MAX_RESOURCES` 时报错 asset entry budget exceeded。`core/crates/plugin/theme/src/preview.rs:51`
- **加载与校验**：预览草稿校验要求每个资产路径通过 `validate_theme_resource_path` 校验且以 assets/ 开头，媒体类型与声明一致、字节非空且不超过上限、路径唯一。`core/crates/plugin/theme/src/preview.rs:62`
- **加载与校验**：资产字节总数超过 `MAX_EXPANDED_BYTES` 或字体数超过 `MAX_FONTS` 时报错 asset byte or font budget exceeded。`core/crates/plugin/theme/src/preview.rs:71`
- **加载与校验**：资产路径集合必须与规范化主题的 `asset_paths()` 完全相等，否则报错 asset bytes must exactly match normalized theme references。`core/crates/plugin/theme/src/preview.rs:78`
- **加载与校验**：校验依次调用 `media::validate_media_files` 与 `media::validate_bubble_pixels`。`core/crates/plugin/theme/src/preview.rs:84`
- **加载与校验**：收据 `validator_version` 为 1，`trust` 固定为 `ThemeTemplateTrust::Untrusted`。`core/crates/plugin/theme/src/preview.rs:90`
- **加载与校验**：收据每项文件记录字节数与 `sha256_hex` 摘要。`core/crates/plugin/theme/src/preview.rs:90`
- **加载与校验**：`ThemePreviewValidationReceipt` 含 `validator_version`、`theme_sha256`、`files`、`media` 与 `trust` 五个字段。`core/crates/plugin/theme/src/preview.rs:25`
- **加载与校验**：`ThemePreviewValidationReceipt` 使用 serde camelCase 重命名并拒绝未知字段（`deny_unknown_fields`）。`core/crates/plugin/theme/src/preview.rs:21`
- **加载与校验**：`parse_asset_transfer` 要求二进制负载不超过 `MAX_EXPANDED_BYTES`。`core/crates/plugin/theme/src/preview.rs:116`
- **加载与校验**：资产目录用 `MAX_MANIFEST_BYTES` 上限解析。`core/crates/plugin/theme/src/preview.rs:119`
- **加载与校验**：目录条目必须唯一、有类型且偏移连续，`offset` 等于当前累计 `end`。`core/crates/plugin/theme/src/preview.rs:131`
- **加载与校验**：目录条目范围超出二进制负载时报错 asset range exceeds the binary payload。`core/crates/plugin/theme/src/preview.rs:140`
- **加载与校验**：目录总长度必须等于负载长度，否则报 binary payload has unreferenced bytes or too many fonts。`core/crates/plugin/theme/src/preview.rs:143`
- **加载与校验**：`validate_theme_preview_transfer` 先规范化草稿，失败时在复制媒体负载前返回。`core/crates/plugin/theme/src/preview.rs:156`
- **加载与校验**：`preview_error` 构造 code 为 theme-preview-input-invalid、阶段为 `ValidationStage::Integrity` 的错误。`core/crates/plugin/theme/src/preview.rs:161`
- **加载与校验**：`ValidatedThemePreview` 提供 `theme()`、`receipt()` 与 `file_bytes(path)` 访问器。`core/crates/plugin/theme/src/preview.rs:41`
- **加载与校验**：`normalize_theme_draft`（js 名 `normalizeThemeDraft`）成功时返回 ok、`theme`、`canonicalThemeJson` 与 `themeSha256`。`core/crates/plugin/theme/src/wasm.rs:10`
- **加载与校验**：`validate_theme_preview_draft`（js 名 `validateThemePreviewDraft`）内部调用 `validate_theme_preview_transfer`，成功时返回 `canonicalThemeJson`、`themeSha256` 与 `receipt`。`core/crates/plugin/theme/src/wasm.rs:37`
- **点选与场景**：预览核注册 6 个可检视部件目标：`background`、`navigation.sidebar`、`chat.topBar`、`chat.userMessage`、`chat.aiMessage` 与 `chat.composer`，点击后通过 `operit.theme.preview.selection.v1` 回传选中目标。`docs/theme-studio-protocol-v1.md:59`
- **点选与场景**：Studio 发送 `operit.theme.preview.inspectMode.v1` 时携带 `revision`、`enabled` 与可空 `targetId`。`docs/theme-studio-protocol-v1.md:58`
- **点选与场景**：Stage HUD（`stage-color-hud`）默认启用 `Light`/`Dark` 双套色彩角色同屏编辑，停靠在画布下方不遮挡预览输入框。`docs/theme-studio-protocol-v1.md:60`
- **点选与场景**：参数或颜色修改后经防抖重跑 Rust/WASM 校验并渲染新 Flutter revision。`docs/theme-studio-protocol-v1.md:60`
- **点选与场景**：`operit.theme.preview.sceneMode.v1` 在不改 `theme.json` 的前提下切换正常对话与空白会话，并等待真实帧结束后刷新 rendered.v1 回执。`docs/theme-studio-protocol-v1.md:61`
- **点选与场景**：`setConversationMode` 要求 `revision` 等于当前已请求 revision，否则抛 stale-revision。`tools/theme/studio_message_port.ts:214`
- **点选与场景**：切换场景要求检查模式关闭且当前 revision 已有渲染回执，否则抛 inspection-active 或 preview-not-rendered。`tools/theme/studio_message_port.ts:222`
- **点选与场景**：可检视目标集合为 `background`、`navigation.sidebar`、`chat.topBar`、`chat.userMessage`、`chat.aiMessage`、`chat.composer` 六项。`tools/theme/studio_message_port.ts:245`
- **点选与场景**：`targetId` 不在集合中时抛 invalid-target，关闭检查时不得保留已选 `targetId`。`tools/theme/studio_message_port.ts:248`
- **捕获与导出**：`operit.theme.preview.capture.v1` 要求当前未处于 Inspector 高亮描边状态，且 `revision` / `viewport` / `showConversation` 与当前 rendered.v1 回执完全一致。`docs/theme-studio-protocol-v1.md:65`
- **捕获与导出**：预览核调用 Flutter `RepaintBoundary.toImage(pixelRatio: 1)` 截取真实渲染帧，通过 `operit.theme.preview.captured.v1` 返回 `pngBytes` 与 `pngSha256`。`docs/theme-studio-protocol-v1.md:66`
- **捕获与导出**：导出 `.toolpkg` 时，若当前处于暗色、非 1280×800 视口、空白会话或存在未重新渲染的草稿改动，Studio 自动切换至亮色 + 1280×800 桌面视口 + 正常对话场景完成真实帧渲染与 `preview.png` 捕获，再调用 Rust/WASM `exportToolPkgFromTheme` 生成确定性 Stored ZIP 归档；导出包形态见 [[plugin-theme|主题即插件（theme-as-ToolPkg）]]。`docs/theme-studio-protocol-v1.md:67`
- **捕获与导出**：`capturePng` 在检查模式启用时抛 capture-inspection-active，在无渲染回执或已有待处理捕获时抛 capture-not-ready。`tools/theme/studio_message_port.ts:266`
- **捕获与导出**：捕获设 15_000 毫秒定时器，超时以 capture-timeout 拒绝。`tools/theme/studio_message_port.ts:272`
- **捕获与导出**：捕获校验 PNG 魔数 `[137, 80, 78, 71, 13, 10, 26, 10]`。`tools/theme/studio_message_port.ts:297`
- **捕获与导出**：捕获校验 PNG 宽高字段（偏移 16 与 20 的 `getUint32`）等于 `expectedViewport` 宽高。`tools/theme/studio_message_port.ts:300`
- **捕获与导出**：捕获重算字节的 SHA-256 并与 `pngSha256` 比对，不一致即以 invalid-capture 失败。`tools/theme/studio_message_port.ts:302`
- **捕获与导出**：捕获要求 `pngBytes` 长度在 33 字节至 4 MiB 之间且 `pngSha256` 有效。`tools/theme/studio_message_port.ts:292`
- **捕获与导出**：收到 rendered.v1 后用 `checkReceipt` 校验回执并保存为 `renderedReceipt`，同时清除渲染定时器。`tools/theme/studio_message_port.ts:346`
- **捕获与导出**：`checkReceipt` 要求回执 `scope` 为 client-shell、`parityVerified` 为布尔值、`revision` 与 `themeSha256` 与当前请求一致。`tools/theme/studio_message_port.ts:366`
- **捕获与导出**：渲染回执的字体数组恰好 4 项。`tools/theme/studio_message_port.ts:375`
- **捕获与导出**：回执资产摘要的键数量与期望资产数量一致且逐项哈希相等，否则报 frame asset hashes mismatch。`tools/theme/studio_message_port.ts:378`
- **捕获与导出**：每项字体 `family` 等于 "OperitThemeFont_" 加该字体 `sha256`，且 `bytes` 为大于 0 且不超过 32 MiB 的安全整数。`tools/theme/studio_message_port.ts:382`
- **捕获与导出**：`exportWithContract` 先调用 bridge 的 `normalizeDraft`，草稿无效时抛 draft-invalid，不直接导出。`tools/theme/studio_message_port.ts:431`
- **捕获与导出**：`export_toolpkg_from_theme`（js 名 `exportToolPkgFromTheme`）返回 `Result<Vec<u8>, JsValue>`，内部调用 `export_toolpkg_from_theme_transfer`。`core/crates/plugin/theme/src/wasm.rs:25`
- **捕获与导出**：`validate_authored_toolpkg`（js 名 `validateAuthoredToolPkg`）对归档调用 `validate_authored_toolpkg_theme_templates` 并返回各模板 `receipts`。`core/crates/plugin/theme/src/wasm.rs:53`
- **捕获与导出**：`validate_authored_toolpkg` 失败时返回 ok:false 与 errors。`core/crates/plugin/theme/src/wasm.rs:52`
- **捕获与导出**：生成不可变预览核版本的命令是 `tools/theme/build_preview.py`，需显式传入与应用一致的 Flutter SDK 与匹配 `core/Cargo.lock` 的 wasm-bindgen CLI。`docs/theme-studio-protocol-v1.md:83`
- **捕获与导出**：协议与契约测试入口为 `cargo test` --manifest-path `core/Cargo.toml` -p operit-plugin-theme 与 node --experimental-strip-types --test `studio_message_port.test.ts`。`docs/theme-studio-protocol-v1.md:89`
- **捕获与导出**：编辑既有 ToolPkg 时，Studio 将所选模板的渲染结果写回对应声明，保留其他脚本、资源和模板；原包及所选模板 ID 随本地草稿一起保存在 `IndexedDB`。`docs/theme-studio-protocol-v1.md:93`

## 关键符号

- `ThemeStudioMessagePort` — Studio 侧协议通道。`tools/theme/studio_message_port.ts:57`
- `ThemeStudioChannelOptions` — 建通道的配置。`tools/theme/studio_message_port.ts:46`
- `ThemeContractBridge` — Rust/WASM 契约桥。`tools/theme/studio_message_port.ts:37`
- `ThemePreviewAsset` — 预览资产。`tools/theme/studio_message_port.ts:2`
- `ClientShellReceipt` — 渲染帧回执。`tools/theme/studio_message_port.ts:9`
- `ThemeStudioMessage` — 七种预览侧消息的联合类型。`tools/theme/studio_message_port.ts:23`
- `Header` — 固定消息头。`tools/theme/studio_message_port.ts:22`
- `ThemeStudioProtocolError` — 协议错误类型。`tools/theme/studio_message_port.ts:42`
- `exportWithContract` — 原始契约导出。`tools/theme/studio_message_port.ts:429`
- `isSha256` — SHA-256 格式校验。`tools/theme/studio_message_port.ts:437`
- `isViewport` — 视口边界校验。`tools/theme/studio_message_port.ts:438`
- `checkReceipt` — 渲染回执校验。`tools/theme/studio_message_port.ts:364`
- `ThemePreviewValidationReceipt` — 预览校验收据。`core/crates/plugin/theme/src/preview.rs:22`
- `ValidatedThemePreview` — 校验通过后的密封预览。`core/crates/plugin/theme/src/preview.rs:33`
- `validate_theme_preview_draft` — 预览草稿校验。`core/crates/plugin/theme/src/preview.rs:47`
- `validate_theme_preview_transfer` — 预览校验入口。`core/crates/plugin/theme/src/preview.rs:152`
- `parse_asset_transfer` — 解析资产目录与二进制负载。`core/crates/plugin/theme/src/preview.rs:112`
- `preview_error` — 构造预览输入错误。`core/crates/plugin/theme/src/preview.rs:160`
- `normalize_theme_draft` — WASM 绑定：规范化草稿。`core/crates/plugin/theme/src/wasm.rs:6`
- `validate_theme_preview_draft` — WASM 绑定：校验预览草稿。`core/crates/plugin/theme/src/wasm.rs:33`
- `export_toolpkg_from_theme` — WASM 绑定：导出 ToolPkg。`core/crates/plugin/theme/src/wasm.rs:21`
- `validate_authored_toolpkg` — WASM 绑定：校验已有 ToolPkg。`core/crates/plugin/theme/src/wasm.rs:51`

## 调用链

1. Studio 加载部署生成的配置，获取固定的渲染版本与 fixture 摘要，并先订阅 `window.message`。`docs/theme-studio-protocol-v1.md:15`
2. Studio 将 `iframe.src` 指向同源 `/theme-preview/<rendererReleaseId>/?studioOrigin=<origin>&nonce=<nonce>&rendererReleaseId=<id>`。`docs/theme-studio-protocol-v1.md:16`
3. 预览核在自身 Rust/WASM Worker 启动就绪后，向 `window.parent` 发送 `operit.theme.preview.available.v1`。`docs/theme-studio-protocol-v1.md:17`
4. Studio 侧只接受 origin 与 source 均匹配的 available 消息，`onWindowMessage` 校验 origin 等于预览 URL origin 且 source 为 `iframe.contentWindow`。`tools/theme/studio_message_port.ts:128`
5. Studio 以 `operit.theme.studio.connect.v1` 向预览窗口转移唯一一个端口（`channel.port2`）。`tools/theme/studio_message_port.ts:143`
6. 子页核对 exact origin、`window.parent` 消息源、相同协议头、单一端口且无既有连接后，在私有端口返回 `operit.theme.preview.ready.v1` 与 `nextRevision`。`docs/theme-studio-protocol-v1.md:19`
7. Studio 收到 ready.v1 后把 `requestedRevision` 置为 `nextRevision` 减 1，状态转为 connected 并移除 `window.message` 监听。`tools/theme/studio_message_port.ts:319`
8. Studio 发送 `operit.theme.preview.load.v1`，携带 `revision`、`canonicalThemeJson`、`themeSha256`、`brightness`、`viewport`、`showConversation` 与 `assets`。`docs/theme-studio-protocol-v1.md:37`
9. 预览核执行加载链路：reserve revision → Rust/WASM 校验 → 核对规范化与资产收据 → 准备字体与解码图片 → loaded.v1 → Flutter 真实帧回调 → rendered.v1。`docs/theme-studio-protocol-v1.md:48`
10. `operit.theme.preview.loaded.v1` 仅表示资源准备完成，真实 Flutter 帧绘制后发出 `operit.theme.preview.rendered.v1`，绑定同一 revision 与摘要。`docs/theme-studio-protocol-v1.md:54`
11. 点选经 `operit.theme.preview.inspectMode.v1` 开启，6 个部件目标点击后经 selection.v1 回传。`docs/theme-studio-protocol-v1.md:59`
12. 场景切换经 `operit.theme.preview.sceneMode.v1`，不改 `theme.json`，等真实帧后刷新 rendered.v1 回执。`docs/theme-studio-protocol-v1.md:61`
13. 帧捕获经 `operit.theme.preview.capture.v1`，预览核调用 `RepaintBoundary.toImage(pixelRatio: 1)` 截取真实渲染帧并返回 `pngBytes` 与 `pngSha256`。`docs/theme-studio-protocol-v1.md:66`
14. 导出时 Studio 先切到亮色 + 1280×800 + 正常对话场景完成真实帧渲染与 `preview.png` 捕获，再调 `exportToolPkgFromTheme` 生成确定性 Stored ZIP。`docs/theme-studio-protocol-v1.md:67`

## 来源

- `docs/theme-studio-protocol-v1.md`
- `tools/theme/studio_message_port.ts`
- `core/crates/plugin/theme/src/preview.rs`
- `core/crates/plugin/theme/src/wasm.rs`
- 本页 seed 为以上 4 个文件；协议文档中点名的预览 JS Worker `theme_contract_worker.js` 与 Dart 预览壳 `tools/theme/preview` 不在本页 seed 内，本页不展开其实现。`docs/theme-studio-protocol-v1.md:8`
