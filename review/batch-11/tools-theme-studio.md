---
title: 主题工具与 Web Studio
module: tools
platforms: [all]
sources: 6
date: 2026-11-11
---

## 概述

- 主题包格式是 ToolPkg（`.toolpkg`），不是独立的主题格式；主题是 ToolPkg 的 `theme` 模板能力，在 `manifest.themes` 中声明。`tools/theme/README.md:3`
- `build_preview.py` 把 Rust/WASM 校验器 `operit-plugin-theme` 与独立 Flutter Web 预览内核 `tools/theme/preview` 编译进不可变的 `build/theme-preview/<rendererReleaseId>/` 发布目录。`tools/theme/README.md:8`
- `prepare_builtin_fonts.py` 是内置静态 TrueType 字体 `noto-sans-sc` 与 `cascadia-mono` 的可复现子集化配方。`tools/theme/README.md:7`
- `studio_message_port.ts` 与 `studio_contract_bridge.ts` 是版本化的浏览器 `MessagePort` 传输与 Web Worker 客户端，服务于 Rust/WASM 主题校验。`tools/theme/README.md:9`
- 预览协议的完整细节由 [[theme-studio|Theme Studio 预览协议 v1]] 覆盖，本页只写工具与构建配方。`tools/theme/studio_message_port.ts:1`

## AI 速览

- `build_preview.py` — 把 Rust/WASM 校验器与 Flutter Web 预览内核编译进不可变的 `build/theme-preview/<rendererReleaseId>/` 目录。`tools/theme/README.md:8`
- `prepare_builtin_fonts.py` — 内置静态字体的可复现子集化配方。`tools/theme/README.md:7`
- `ThemeStudioMessagePort` — 版本化的浏览器 `MessagePort` 传输。`tools/theme/studio_message_port.ts:57`
- `StudioContractBridge` — Web Worker 客户端，把校验委托给 Rust/WASM。`tools/theme/studio_contract_bridge.ts:20`
- `ThemeContractBridge` — 向 Rust/WASM 校验器暴露 `normalizeDraft`、`validatePreview` 与 `exportPackage`。`tools/theme/studio_message_port.ts:39`
- 主入口：仓库根目录运行 `tools/theme/build_preview.py --renderer-release-id <id> --flutter-sdk <sdk> --wasm-bindgen <path>`。`tools/theme/README.md:18`
- 数据流向：草稿经 Rust/WASM 校验工作器校验 → 预览内核渲染实时帧 → 导出已验证的 `.toolpkg` 包。`tools/theme/README.md:31`

## 核心机制

### 主题包格式为什么是 ToolPkg

- 主题包格式是 ToolPkg（`.toolpkg`），不是独立的主题格式。`tools/theme/README.md:3`
- 主题是 ToolPkg 的 `theme` 模板能力，在 `manifest.themes` 中声明。`tools/theme/README.md:3`
- 编辑器创建带 `themes` 声明的标准 ToolPkg，生成的文件是 `manifest.json`、`theme.json`、`preview.png`、引用的媒体资产（`assets/images/*`、`assets/fonts/*`）与 `manifest.license` 引用的协议文本。`tools/theme/studio/README.md:9`
- ToolPkg 本身也可声明脚本与其他能力；编辑器不按这些能力对包分类或拒绝。`tools/theme/studio/README.md:9`
- 归一化、L0–L4 媒体校验（PNG/JPEG、受限静态 SVG、静态 TrueType `.ttf`）与确定性 Stored-ZIP `.toolpkg` 导出由编译为 WebAssembly 的 `operit-plugin-theme` 执行。`tools/theme/studio/README.md:8`
- Rust 是校验与导出的权威；浏览器只解压 ZIP 条目并读取 ToolPkg 声明以供编辑。`tools/theme/studio/README.md:8`
- 导入读取 ToolPkg 的 `manifest.themes`，或打开可视化 JSON 草稿（`src/toolpkg_import.ts`）；编辑器遵循每个声明的实际路径，存在多个声明时询问编辑哪一个。`tools/theme/studio/README.md:24`
- 导入不要求唯一的 `default` 声明，也不要求固定的 `theme.json` / `preview.png` 路径。`tools/theme/studio/README.md:24`
- 导入提取草稿；导出从该草稿创建新的 ToolPkg，而不是重写原始档案的其他能力。`tools/theme/studio/README.md:24`
- 编辑已有 ToolPkg 时，编辑后的模板存入不可变的内容寻址目录，保留其他能力共享的资源。`tools/theme/studio/README.md:60`
- 未改动的 `manifest` 字段保留原始本地化值、作者数组与协议引用；显式的中文文本编辑只更新该翻译。`tools/theme/studio/README.md:60`
- 包 ID 遵循普通的非空 ToolPkg 规则；最终合并的档案在下载前必须对每个声明的模板通过 Rust 校验器。`tools/theme/studio/README.md:60`

### 预览内核如何构建为不可变的 rendererReleaseId 目录

- `build_preview.py` 构建一个不可变的预览/校验发布，永不安装 SDK 组件；失败的构建留在输出目录中，不删除。`tools/theme/build_preview.py:2`
- 三个必需参数是 `--renderer-release-id`、`--flutter-sdk`、`--wasm-bindgen`，`--base-prefix` 默认为空字符串。`tools/theme/build_preview.py:34`
- `--base-prefix` 必须以 `/` 开头，且不得包含 `..` 或 `//`。`tools/theme/build_preview.py:41`
- `renderer-release-id` 必须是 1–128 字符的单一规范路径组件，匹配 `[A-Za-z0-9._-]{1,128}`，且不是 `.` 或 `..`。`tools/theme/build_preview.py:33` `tools/theme/build_preview.py:42`
- 构建选用 SDK 声明的可执行文件 `sdk/bin/flutter`（Windows 上为 `flutter.bat`），而不是 PATH 上发现的其他 SDK。`tools/theme/build_preview.py:46`
- `wasm-bindgen` CLI 必须与 `core/Cargo.lock` 中锁定的 crate 版本完全一致，且锁文件中只能有一个该版本。`tools/theme/build_preview.py:50`
- 发布目标是 `build/theme-preview` 下以 `release_id` 命名的目录，且必须留在仓库构建目录内。`tools/theme/build_preview.py:52`
- 目标目录已存在时构建抛出 `FileExistsError`，拒绝复用渲染器发布目录。`tools/theme/build_preview.py:56`
- 夹具源包括 `operit_ui/lib/src` 下全部 `.dart` 文件、`tools/theme/preview/lib/main.dart`、`theme_studio_message_port.dart` 与 `theme_contract_client.dart`。`tools/theme/build_preview.py:60`
- `fixture_source_sha256` 是对各夹具源按（相对路径 + NUL + 字节 + NUL）逐项做 SHA-256。`tools/theme/build_preview.py:68`
- 构建用 `cargo build` 以 `--features wasm`、`--target wasm32-unknown-unknown`、`--release`、`--locked` 编译 `operit-plugin-theme`。`tools/theme/build_preview.py:73`
- 编译产物是 `workspace["target_directory"]` 下的 `wasm32-unknown-unknown/release/operit_plugin_theme.wasm`。`tools/theme/build_preview.py:75`
- 构建运行 `tools/prepare_flutter_web_fonts.py`，输出到 `tools/theme/preview/web/fonts`。`tools/theme/build_preview.py:76`
- Flutter 构建命令是 `flutter build web --release --no-pub --no-web-resources-cdn`，输出到发布目录，`base-href` 为 `<base-prefix>/theme-preview/<release-id>/`。`tools/theme/build_preview.py:80`
- Flutter 构建注入两个 `dart-define`：`OPERIT_THEME_RENDERER_RELEASE_ID` 与 `OPERIT_THEME_FIXTURE_SOURCE_SHA256`。`tools/theme/build_preview.py:82`
- `wasm-bindgen` 的版本须与锁定的 crate 版本完全一致，否则报错。`tools/theme/build_preview.py:50`
- 以 `--target web`、`--out-name operit_plugin_theme` 把 WASM 绑定输出到发布目录下的 `validator` 子目录。`tools/theme/build_preview.py:84` `tools/theme/build_preview.py:85`
- `renderer-release.json` 除自身外为发布目录下每个文件记录相对路径、字节数与 SHA-256。`tools/theme/build_preview.py:91`
- 描述符含 `rendererReleaseId`、`validatorVersion` 1、`fixtureSourceSha256`、`flutterRevision`、`engineRevision`、`coreCommit`、`sourceDirty` 与 `files`。`tools/theme/build_preview.py:96`
- `coreCommit` 取自 `git rev-parse HEAD`，`sourceDirty` 取自 `git status --porcelain` 是否非空。`tools/theme/build_preview.py:97`
- `renderer-release.json` 以排序键、2 空格缩进写入发布目录。`tools/theme/build_preview.py:101`
- 构建成功打印 `"Built renderer release (not parity-accepted): {destination}"`，即该发布未经一致性验收。`tools/theme/build_preview.py:103`

### Studio 与 Rust/WASM 校验器之间的协议（摘要）

- Studio 侧协议是受信协议，不解析 ZIP，也不执行主题代码；完整握手、修订排序、帧收据与帧捕获规则见 [[theme-studio|Theme Studio 预览协议 v1]]。`tools/theme/studio_message_port.ts:1`
- `studio_message_port.ts` 与 `studio_contract_bridge.ts` 是版本化的浏览器 `MessagePort` 传输与 Web Worker 客户端，服务于 Rust/WASM 主题校验。`tools/theme/README.md:9`
- 每条消息的 `Header` 含 `protocolVersion` 1、`nonce` 与 `rendererReleaseId`。`tools/theme/studio_message_port.ts:22`
- `ThemeContractBridge` 接口向 Rust/WASM 校验器暴露 `normalizeDraft`、`validatePreview` 与 `exportPackage` 三个方法。`tools/theme/studio_message_port.ts:39`
- `StudioContractBridge` 是 Studio 的校验适配器，工作器 URL 必须指向与 iframe 相同的不可变渲染器发布；该类不在 TypeScript 中实现 ZIP 或模式语义。`tools/theme/studio_contract_bridge.ts:17`
- 构造函数要求工作器 URL 同源，且路径以 `/theme_contract_worker.js` 结尾。`tools/theme/studio_contract_bridge.ts:25`
- 桥接器从工作器 URL 相对导入 `theme_contract_client.js`，并创建 `ThemeContractWorker(worker.href, rendererReleaseId)`。`tools/theme/studio_contract_bridge.ts:29`
- `normalizeDraft` 方法直接委托给工作器客户端。`tools/theme/studio_contract_bridge.ts:34`
- `validatePreview` 与 `exportPackage` 方法直接委托给工作器客户端。`tools/theme/studio_contract_bridge.ts:41`
- `validatePackage` 要求最终合并档案中的每个模板都通过共享 Rust 校验器；响应 `ok` 不为 `true` 时抛出 `response.errors`。`tools/theme/studio_contract_bridge.ts:50`
- `exportWithContract` 先调用 `normalizeDraft` 并要求返回 `ok === true`，否则抛出 `draft-invalid`，再调用 `bridge.exportPackage`。`tools/theme/studio_message_port.ts:431`
- 注释明确指出 `client-shell` 收据不是跨平台 1:1 截图，也不是整场景一致性/导出授权；最终 UI 需要两者。`tools/theme/studio_message_port.ts:427`
- 订阅须在导航 iframe 之前完成；可用性只在预览自身的校验工作器启动后通告；`"loaded"` 不是一帧。`tools/theme/studio_message_port.ts:55`
- 预览通道是单次使用的；重复连接抛出 `already-connected`。`tools/theme/studio_message_port.ts:107`
- 连接超时为 15 秒，失败码为 `preview-startup-timeout`。`tools/theme/studio_message_port.ts:121`

### 内置字体子集化配方

- `prepare_builtin_fonts.py` 制备已钉住的静态主题字体数据，不是应用构建；不执行 `pip install`，不修改 SDK，不安装系统字体。`tools/theme/prepare_builtin_fonts.py:3`
- 已有资产字节永不被不同内容覆盖；`write_new_or_identical` 遇不同字节拒绝写入。`tools/theme/prepare_builtin_fonts.py:56`
- FontTools wheel 钉住版本 4.61.1，SHA-256 为 `17d2bf5d541add43822bcf0c43d7d847b160c9bb01d15d5007d84e2217aaa371`。`tools/theme/prepare_builtin_fonts.py:21`
- 脚本下载 FontTools wheel 后先验哈希再使用，限 2 MiB，写入 `.venv/theme-font-tools/fonttools-4.61.1-py3-none-any.whl`。`tools/theme/prepare_builtin_fonts.py:134`
- Noto 源钉住提交 `f8d157532fbfaeda587e826d4cd5b21a49186f7c`，取自 `notofonts/noto-cjk` 的 `Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf`。`tools/theme/prepare_builtin_fonts.py:28`
- Cascadia 许可证钉住提交 `56bcca3f2c1e4cb19458954f0e2bb4635960df91`，源自 `microsoft/cascadia-code` 的 `LICENSE`。`tools/theme/prepare_builtin_fonts.py:29` `tools/theme/prepare_builtin_fonts.py:35`
- Cascadia 源字体取自仓库内 `apps/flutter/app/assets/fonts/CascadiaMono.ttf`，不是下载的。`tools/theme/prepare_builtin_fonts.py:142`
- `prepare_font` 要求源以 TrueType 魔数开头，且含 `fvar` 与 `glyf` 表。`tools/theme/prepare_builtin_fonts.py:68`
- 可变字体实例化时 `wght` 轴固定为 400；源必须显式含 `wght` 轴。`tools/theme/prepare_builtin_fonts.py:77`
- 输出禁止含 `fvar`、`gvar`、`avar`、`cvar`、`HVAR`、`MVAR`、`CFF`、`COLR` 等动态/彩色表，必须是静态单色 TrueType。`tools/theme/prepare_builtin_fonts.py:83`
- 输出必须含 `head`、`hhea`、`hmtx`、`maxp`、`loca`、`glyf`、`cmap` 七个表。`tools/theme/prepare_builtin_fonts.py:85`
- 输出表数上限 64，`font["maxp"].numGlyphs` 上限 65535。`tools/theme/prepare_builtin_fonts.py:87`
- 衍生字体重写 name ID 1、2、3、4、6、16、17，避免使用原始保留字体名；`OS/2.usWeightClass` 设为 400。`tools/theme/prepare_builtin_fonts.py:95`
- 许可证文本必须含 `"SIL OPEN FONT LICENSE"`，否则拒绝。`tools/theme/prepare_builtin_fonts.py:108`
- 捆绑的许可证以 `Operit static derivative: {family}` 开头，记录原始字体、来源、许可证来源、FontTools 版本与静态轴。`tools/theme/prepare_builtin_fonts.py:112`
- 输出写到 `apps/flutter/packages/operit_ui` 下的 `assets/fonts/{font_id}.ttf` 与 `assets/licenses/{font_id}.txt`。`tools/theme/prepare_builtin_fonts.py:17` `tools/theme/prepare_builtin_fonts.py:118`
- 输出单字体字节上限 32 MiB（`MAX_BYTES`）。`tools/theme/prepare_builtin_fonts.py:38`
- 两个内置字体是 `noto-sans-sc`（族名 `Operit Theme Sans SC`）与 `cascadia-mono`（族名 `Operit Theme Mono`）。`tools/theme/prepare_builtin_fonts.py:147`
- 目录文件是 `assets/fonts/catalog.v1.json`，格式版本 `formatVersion` 1。`tools/theme/prepare_builtin_fonts.py:152`
- 目录条目记录 `id`、`asset`、`bytes`、`sha256`、`license` OFL-1.1、`licenseAsset`、`licenseSha256`、`source`、`sourceSha256`、`sourceFontVersion` 与 `recipe`。`tools/theme/prepare_builtin_fonts.py:125`
- 脚本结束时声明原始应用字体与 SDK 未改变。`tools/theme/prepare_builtin_fonts.py:154`
- `fetch` 使用 User-Agent `"Operit2-theme-font-assets"`，超时 90 秒，超限或空内容拒绝。`tools/theme/prepare_builtin_fonts.py:47`

### Studio 编辑能力与本地运行

- 右侧舞台嵌入独立 Flutter Web 预览内核 `tools/theme/preview`，以 1:1 共享 Flutter 渲染（`client-shell-v7`）渲染与原生 Operit2 客户端完全相同的 `operit_ui` 组件。`tools/theme/studio/README.md:7`
- 预览内核渲染的组件包括桌面侧栏、会话历史、顶栏、用户/AI 消息气泡、九宫格表面与 Agent/Classic 聊天输入。`tools/theme/studio/README.md:7`
- 交互画布检查器通过点选元素（Inspect）或图层 chips 跳转到对应组件的模式参数。`tools/theme/studio/README.md:14`
- 预览支持正常对话（默认）与空白会话两种场景，以及 Desktop（1280×800）、Phone（390×844）、Tablet（768×1024）、Wide（1440×900）四种视口，浅色或深色模式。`tools/theme/studio/README.md:15`
- 双模式舞台颜色 HUD 默认在浅色 + 深色双模式下启用，可并排编辑 `palette.light` 与 `palette.dark`（或组件级浅色/深色覆盖）。`tools/theme/studio/README.md:18`
- 可上传背景图、用户/AI 气泡九宫格皮肤（`tiled_nine_slice` 或 `nine_patch`）与输入框九宫格皮肤（PNG/JPEG 或受限静态 SVG）。`tools/theme/studio/README.md:20`
- 聊天输入框右侧 5 个动作图标是 `settingsAsset`、`attachmentAsset`、`micAsset`、`sendAsset`、`stopAsset`，显示尺寸可调（12–44 px / 12–48 px）。`tools/theme/studio/README.md:21`
- 可上传自定义静态 TrueType 字体（`assets/fonts/*.ttf`），或为全局、用户与 AI 排版选用内置 `noto-sans-sc` / `cascadia-mono`。`tools/theme/studio/README.md:22`
- 编辑与上传的二进制资产自动持久化到浏览器 IndexedDB（`src/draft_store.ts`），并有显式的「保存草稿」确认与多步 Undo / Redo 历史。`tools/theme/studio/README.md:25`
- 点击「导出 ToolPkg」时自动确保渲染一帧新的 1280×800 浅色模式正常会话帧，从 Flutter `RepaintBoundary` 捕获 `preview.png`，检查声明的文件与引用的协议文本，再下载确定性的 `.toolpkg` 档案。`tools/theme/studio/README.md:26`
- 本地运行 Studio 时在 `tools/theme/studio` 下执行 `npm ci` 与 `npm run dev`。`tools/theme/README.md:27`
- 本地 Studio 打开 `http://127.0.0.1:7474/`。`tools/theme/README.md:31`
- Studio 同源挂载已钉住的 `build/theme-preview/<rendererReleaseId>/` 目录，通过共享 Flutter `operit_ui` 组件（`client-shell-v7`）渲染实时帧。`tools/theme/README.md:31`
- Studio 通过 Rust/WASM 校验工作器导出已验证的 `.toolpkg` 包。`tools/theme/README.md:31`
- 开发或构建期间用 `OPERIT_THEME_RENDERER_RELEASE_ID=<release-id>` 指定自定义预览发布 ID。`tools/theme/studio/README.md:44`

### 静态包与发布

- 在 `tools/theme/studio` 内运行 `npm run build` 会校验已钉住的预览发布，生成 `dist/theme-studio-config.json` 与 `dist/.nojekyll`，并把已验证的 Flutter Web + Rust/WASM 预览发布复制到 `dist/theme-preview/<rendererReleaseId>/`。`tools/theme/README.md:35`
- 生产编辑器发布于 `web.operit.app/theme/`。`tools/theme/README.md:37`
- 生产构建须给 `build_preview.py` 传 `--base-prefix /theme`，并在 `npm run build` 期间设置 `OPERIT_STUDIO_BASE_PREFIX=/theme`；预览的 Flutter base href 与编辑器的构建前缀必须一致。`tools/theme/README.md:37`
- 唯一的发布工作流是 Deploy Web Experience（`.github/workflows/deploy-web-experience.yml`），从 `main` 手动运行，同时构建并发布根路径 `/` 的主应用与 `/theme/` 的 Theme Studio。`tools/theme/README.md:39`
- 部署运行共享 `github-pages` 并发组，不取消正在运行的部署。`tools/theme/README.md:39`
- 该工作流用常规 push 更新已有的 `gh-pages` 分支并保留历史，然后以 `pages: write` 权限显式请求 GitHub Pages 构建。`tools/theme/README.md:39`
- GitHub Pages 必须已使用该分支作为发布源，并已配置 `web.operit.app` 为自定义域名。`tools/theme/README.md:39`
- 静态包输出到 `tools/theme/studio/dist/`，已验证的预览内核嵌套于 `dist/theme-preview/<release-id>/`。`tools/theme/studio/README.md:56`
- 生产构建前须先以 `--base-prefix /theme` 构建预览发布，再构建 Studio；Deploy Web Experience 从 `main` 一起发布应用与编辑器，Studio 位于 `web.operit.app/theme/`。`tools/theme/studio/README.md:58`

### Figma 交接

- Studio 的「导出 Figma」按钮创建可编辑的原生组件板，保留完整主题、资产与原始 ToolPkg 上下文。`tools/theme/README.md:43`
- 通过「导入 / Figma 回传」导入返回的 `.operit-design.json` 后，用 Flutter 预览并经现有 Rust 校验器导出。`tools/theme/README.md:43`
- 实际页面、展开的工具结果、Compose DSL 插件屏与 WebView UI 使用 opt-in 的运行时捕获工具；插件安装、捕获命令与映射边界见 `tools/figma/README.md`。`tools/theme/README.md:45`

## 关键符号

- `build_preview.py` — 把 Rust/WASM 校验器与 Flutter Web 预览内核编译进不可变的 `build/theme-preview/<rendererReleaseId>/` 目录。`tools/theme/README.md:8`
- `prepare_builtin_fonts.py` — 内置静态字体的可复现子集化配方。`tools/theme/README.md:7`
- `ThemeStudioMessagePort` — 版本化的浏览器 `MessagePort` 传输。`tools/theme/studio_message_port.ts:57`
- `StudioContractBridge` — Web Worker 客户端，把校验委托给 Rust/WASM。`tools/theme/studio_contract_bridge.ts:20`
- `ThemeContractBridge` — 向 Rust/WASM 校验器暴露 `normalizeDraft`、`validatePreview` 与 `exportPackage`。`tools/theme/studio_message_port.ts:39`
- `ThemePreviewAsset` — 预览资产，含 `path`、`mediaType`、`sha256` 与 `bytes`。`tools/theme/studio_message_port.ts:4`
- `ClientShellReceipt` — 帧收据，`scope` 为 `client-shell`。`tools/theme/studio_message_port.ts:14`
- `ThemeStudioProtocolError` — 协议错误，含错误码 `code`。`tools/theme/studio_message_port.ts:42`
- `exportWithContract` — 先调 `normalizeDraft` 验草稿，再调 `bridge.exportPackage` 导出。`tools/theme/studio_message_port.ts:431`
- `renderer-release.json` — 发布描述符，含 `rendererReleaseId`、`validatorVersion` 1、`fixtureSourceSha256`、`flutterRevision`、`engineRevision`、`coreCommit`、`sourceDirty` 与 `files`。`tools/theme/build_preview.py:96`
- `fixtureSourceSha256` — 描述符中的夹具源哈希键。`tools/theme/build_preview.py:95`
- `prepare_font` — 把可变 TrueType 源实例化为静态单色 TrueType。`tools/theme/prepare_builtin_fonts.py:63`
- `write_new_or_identical` — 已有资产字节永不被不同内容覆盖。`tools/theme/prepare_builtin_fonts.py:56`
- `catalog.v1.json` — 内置字体目录，格式版本 `formatVersion` 1。`tools/theme/prepare_builtin_fonts.py:152`
- `studio_message_port.test.ts` — Node TypeScript 测试套件，覆盖握手、修订排序、场景模式、帧捕获与二进制导出边界。`tools/theme/README.md:10`

## 调用链

1. 仓库根目录运行 `tools/theme/build_preview.py --renderer-release-id <id> --flutter-sdk <sdk> --wasm-bindgen <path>`，构建不可变的预览发布。`tools/theme/README.md:18`
2. `build_preview.py` 用 `cargo build` 以 `--features wasm`、`--target wasm32-unknown-unknown`、`--release`、`--locked` 编译 `operit-plugin-theme`。`tools/theme/build_preview.py:73`
3. `build_preview.py` 运行 `tools/prepare_flutter_web_fonts.py`，输出到 `tools/theme/preview/web/fonts`。`tools/theme/build_preview.py:76`
4. `build_preview.py` 用 `flutter build web` 构建预览内核，`base-href` 为 `<base-prefix>/theme-preview/<release-id>/`。`tools/theme/build_preview.py:80`
5. `build_preview.py` 用 wasm-bindgen 把 WASM 绑定输出到发布目录下的 `validator` 子目录。`tools/theme/build_preview.py:84` `tools/theme/build_preview.py:85`
6. `build_preview.py` 为发布目录下每个文件（除 `renderer-release.json` 自身外）记录相对路径、字节数与 SHA-256，写入 `renderer-release.json`。`tools/theme/build_preview.py:91`
7. 本地在 `tools/theme/studio` 下执行 `npm ci` 与 `npm run dev`。`tools/theme/README.md:27`
8. 本地 Studio 打开 `http://127.0.0.1:7474/`，同源挂载已钉住的预览发布并渲染实时帧。`tools/theme/README.md:31`
9. 点击「导出 ToolPkg」时自动确保渲染一帧新的 1280×800 浅色模式正常会话帧，从 Flutter `RepaintBoundary` 捕获 `preview.png`，再下载确定性的 `.toolpkg` 档案。`tools/theme/studio/README.md:26`
10. 生产：先以 `--base-prefix /theme` 构建预览发布，再构建 Studio；Deploy Web Experience 从 `main` 一起发布应用与编辑器。`tools/theme/studio/README.md:58`

## 来源

- 本页 seed 文件 100% 已读：`tools/theme/README.md`（45 行）、`tools/theme/studio/README.md`（60 行）、`tools/theme/build_preview.py`（107 行）、`tools/theme/studio_message_port.ts`（449 行），基线 AAswordman/Operit2 @ 364d1d594。
- 同一目录下直接相关的两个文件也已读：`tools/theme/prepare_builtin_fonts.py`（158 行，内置字体子集化配方）与 `tools/theme/studio_contract_bridge.ts`（55 行，校验工作器桥接）。
- 预览协议的完整细节由 [[theme-studio|Theme Studio 预览协议 v1]] 覆盖，本页只写工具侧接入摘要。
- 本页无全仓零命中类断言，无需写核验方法。
