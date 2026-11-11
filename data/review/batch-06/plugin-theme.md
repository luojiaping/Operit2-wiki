---
title: 主题即插件（theme-as-ToolPkg）
module: plugins
platforms: [all]
sources: 5
date: 2026-11-11
---

## 概述

- 主题是 ToolPkg 的一种能力：ToolPkg 的 manifest 通过 `themes` 数组声明多个主题模板，与 `main`、`subpackages`、`resources`、`workspace_templates` 等能力共存。(docs/theme-v1-contract.md:3)
- 主题模板的发行格式只有 `.toolpkg`，安装、作用域、同步、更新和卸载全部由现有包管理系统负责。(docs/theme-v1-contract.md:3)
- 模板只是创建源：应用模板时烘焙成独立命名的 ThemeConfig，后续渲染只读配置与已复制的外观资源，不再依赖来源插件是否安装。(docs/theme-v1-contract.md:51)
- 模板的视觉定义由 `theme-v1.schema.json` 约束，模板声明由 `theme-template.schema.json` 约束。(docs/theme-v1-contract.md:5)
- 本页写 manifest 用法与安装同步，schema 本身的约束细节见 [[core-plugin-theme|插件——主题 v1 契约]]，包管理总貌见 [[plugin-toolpkg-overview|插件——ToolPkg 总览]]。(docs/theme-v1-contract.md:5)
- 内置例子包含 `moss` 模板。(plugins/packages/external/moss_atelier/manifest.json:29)
- 内置例子还包含 `dune` 模板。(plugins/packages/external/moss_atelier/manifest.json:45)

## AI 速览

- `themes` — manifest 中声明主题模板的数组。(docs/theme-v1-contract.md:3)
- `ToolPkgArchiveParser::readThemeTemplates` — 通过普通 ToolPkg manifest 解析器枚举模板，再调用 `validate_declared_theme_templates` 校验其资源。(docs/theme-v1-contract.md:37)
- `validate_declared_theme_templates` — 校验已声明模板的资源。(docs/theme-v1-contract.md:37)
- `ValidatedThemeTemplate` — 对应模板的渲染校验结果。(docs/theme-v1-contract.md:35)
- `ThemeValidationReceipt` — 对应模板的渲染校验收据，`trust` 为 `Untrusted`。(docs/theme-v1-contract.md:35)
- `packageManager().getToolPkgContainerRuntimes()` — 新建对话框每次打开时动态读取模板来源。(docs/theme-v1-contract.md:45)
- `previewToolPkgTheme(packageName, templateId)` — 读取当前注册包，验证模板和媒体，返回规范化视觉 JSON 与资源。(docs/theme-v1-contract.md:47)
- `ThemeTemplateService` — 把模板图片和字体复制到 `runtime/data/user_assets/theme` 资源池并替换引用。(docs/theme-v1-contract.md:47)
- `ThemeConfigManager.create` 与 `apply` — 创建并选中独立配置的原有入口。(docs/theme-v1-contract.md:47)
- `themePaletteJson` — 保存完整明暗配色的可选外观字段。(docs/theme-v1-contract.md:49)
- `export_toolpkg_from_theme_transfer` — Studio 创建包含模板的普通 ToolPkg 的入口。(docs/theme-v1-contract.md:39)
- `normalizeThemeDraft` — 校验并展开编辑态草稿默认值，返回 `canonicalThemeJson` 与 `themeSha256`。(docs/theme-studio-protocol-v1.md:73)
- `exportToolPkgFromTheme` — 生成确定性 Stored ZIP（`.toolpkg`）的 WASM 绑定。(docs/theme-studio-protocol-v1.md:75)
- `validateAuthoredToolPkg` — 导出已有 ToolPkg 时对合并后归档的所有模板执行校验。(docs/theme-studio-protocol-v1.md:76)
- `operit.theme.preview.load.v1` — Studio 向预览核加载规范化主题草稿的消息。(docs/theme-studio-protocol-v1.md:37)
- `operit.theme.preview.rendered.v1` — 真实 Flutter 帧绘制完成后发出的回执。(docs/theme-studio-protocol-v1.md:54)
- 主入口是 `previewToolPkgTheme` 与 `ThemeTemplateService`，另一主入口是 Studio 的 `exportToolPkgFromTheme`。(docs/theme-v1-contract.md:47)
- 数据流向：manifest 声明模板 → 包管理安装 → 新建时读取模板 → 预览校验 → 复制资源并烘焙成独立 ThemeConfig → 配置随 Space 同步 → 渲染只读配置与资源。(docs/theme-v1-contract.md:51)

## 核心机制

### manifest 如何声明主题模板

- 模板声明 schema 只约束 `themes` 的一项，不定义另一份包 manifest。(docs/theme-v1-contract.md:5)
- 模板声明必填 `id`、`path`、`preview`、`files` 四项。(core/crates/plugin/theme/schema/theme-template.schema.json:50)
- 模板声明项的 `id` 在同一个包中唯一，节点选择使用 `toolpkg_id:template_id` 身份。(docs/theme-v1-contract.md:27)
- `path` 和 `preview` 是 manifest 所在目录的相对路径。(docs/theme-v1-contract.md:27)
- 资源清单中的 `theme.json`、`preview.png` 对应 `path` 与 `preview` 两个显式引用。(docs/theme-v1-contract.md:27)
- `assets/images/*` 和 `assets/fonts/*` 相对于视觉定义所在目录解析，校验回执中的资源路径是渲染器使用的模板内路径。(docs/theme-v1-contract.md:27)
- 模板的 `files` 数组最少 2 项、最多 63 项。(core/crates/plugin/theme/schema/theme-template.schema.json:7)
- 资源清单每项必填 `path` 与 `mediaType`。(core/crates/plugin/theme/schema/theme-template.schema.json:32)
- 模板资源路径只允许 `theme.json`、`preview.png`、`licenses/*.txt`、`assets/images/*` 图片与 `assets/fonts/*.ttf` 五类路径。(core/crates/plugin/theme/schema/theme-template.schema.json:17)
- 资源清单的 `mediaType` 只允许 `application/json`、`image/png`、`image/jpeg`、`image/svg+xml`、`font/ttf`、`text/plain` 六种。(core/crates/plugin/theme/schema/theme-template.schema.json:22)
- `files` 只登记该模板引用的资源路径和媒体类型，无需填写字节数或 SHA-256。(docs/theme-v1-contract.md:29)
- 旧包残留的 `bytes`、`sha256` 字段会被忽略，文件大小限制根据实际资源检查，内部缓存摘要由系统自动计算。(docs/theme-v1-contract.md:29)
- 模板校验只读取 `files` 登记的资源，包内其他脚本、模板、协议文本和资源不受主题文件白名单限制。(docs/theme-v1-contract.md:29)
- 模板及视觉定义不包含平台列表、协议字段、主题 API 版本或最低／最高应用版本。(docs/theme-v1-contract.md:31)
- 包的 `api_version` 和 `version` 沿用 ToolPkg 本身的含义，主题模块不增加版本格式要求。(docs/theme-v1-contract.md:31)
- 可选的包级 `license` 引用包内协议原文，使用普通安全相对路径，不要求 SPDX 枚举或每个图片、字体另附协议。(docs/theme-v1-contract.md:31)

### 视觉定义长什么样

- 视觉定义顶层必填 `palette`、`background`、`surfaces`、`chat`、`input`、`typography` 六个分区。(core/crates/plugin/theme/schema/theme-v1.schema.json:1063)
- 配色 `light` 与 `dark` 两套均必填。(core/crates/plugin/theme/schema/theme-v1.schema.json:765)
- 配色值是 8 位十六进制颜色字符串，格式为 `^#[0-9A-F]{8}$`。(core/crates/plugin/theme/schema/theme-v1.schema.json:17)
- 视觉 schema 的逐项约束与校验函数见 [[core-plugin-theme|插件——主题 v1 契约]]，本页不重复展开。(docs/theme-v1-contract.md:5)

### 模板如何校验

- `normalize_draft` 按视觉 schema 展开编辑态默认值，`parse_theme` 校验完整视觉状态。(docs/theme-v1-contract.md:33)
- 显式非法值、未知视觉字段、远程资源路径及非法九宫格切片会报错。(docs/theme-v1-contract.md:33)
- Rust `operit-plugin-theme` 为每个模板检查资源存在性、实际大小、视觉关系、PNG/JPEG 解码、受限静态 SVG、九宫格像素范围及静态 TrueType 字体结构。(docs/theme-v1-contract.md:35)
- `ValidatedThemeTemplate` 和 `ThemeValidationReceipt` 只表示对应模板的渲染校验结果，`trust` 为 `Untrusted`。(docs/theme-v1-contract.md:35)
- `ToolPkgArchiveParser::readThemeTemplates` 通过普通 ToolPkg manifest 解析器枚举模板，再调用 `validate_declared_theme_templates` 校验其资源。(docs/theme-v1-contract.md:37)
- 没有 `themes` 的普通包调用 `readThemeTemplates` 返回空集合。(docs/theme-v1-contract.md:37)
- 主题模块不独立寻找 manifest，也不执行脚本、安装包或创建独立归档存储。(docs/theme-v1-contract.md:37)
- `validate_toolpkg_theme_templates` 和 `validate_toolpkg_theme_template` 用于检查 Studio 明确生成的根目录 manifest 输出。(docs/theme-v1-contract.md:37)

### 模板与 ThemeConfig 的关系

- 客户端沿用原有外观设置和命名配置管理，外观页面只有配置选择、新建、重命名、删除，以及主题、背景、气泡、交互四个编辑分区。(docs/theme-v1-contract.md:43)
- 新建配置时可选择默认外观、当前外观、继承已有配置，或者使用已安装 ToolPkg 声明的模板。(docs/theme-v1-contract.md:45)
- 模板来源每次打开新建对话框时通过 `packageManager().getToolPkgContainerRuntimes()` 动态读取。(docs/theme-v1-contract.md:45)
- 选择模板后，`previewToolPkgTheme(packageName, templateId)` 读取当前注册包，验证模板和媒体，返回规范化视觉 JSON 与资源。(docs/theme-v1-contract.md:47)
- `ThemeTemplateService` 将模板图片和字体复制到既有 `runtime/data/user_assets/theme` 资源池，把包内相对引用替换为外观资源引用。(docs/theme-v1-contract.md:47)
- 模板应用通过原有 `ThemeConfigManager.create` 和 `apply` 创建并选中独立配置，模板只是创建源，不是运行时主题本身。(docs/theme-v1-contract.md:47)
- 从模板创建配置不会修改继承来源或此前选中的命名配置。(docs/theme-v1-contract.md:49)
- 新配置的颜色、背景、字体、输入样式和气泡都可以继续编辑。(docs/theme-v1-contract.md:49)
- 完整明暗配色作为可选的 `themePaletteJson` 外观字段保存，用户重新选择配色时清除完整配色，使用原有种子配色逻辑。(docs/theme-v1-contract.md:49)

### 安装、作用域、同步、更新与卸载

- 主题模板的安装、卸载、更新和 device / space 归属由普通插件管理系统负责，主题模块不另设安装流程。(docs/theme-v1-contract.md:45)
- 配置和复制后的资源沿用原有 Space 同步。(docs/theme-v1-contract.md:51)
- 后续渲染读取配置与外观资源，不再依赖来源插件是否安装，也不会随来源模板更新而改写配置。(docs/theme-v1-contract.md:51)
- 主题没有独立主题库、共享模板选择、只读锁定、主题专用卸载约束或模板恢复页面。(docs/theme-v1-contract.md:51)
- 普通 ToolPkg 的 `themes` 声明、模板校验、共享 Flutter 渲染，以及 Studio 编辑和导出继续保留。(docs/theme-v1-contract.md:53)
- 外观资源或配色加载失败时，客户端展示明确错误及“重试”“重置外观”操作，重试读取原有值。(docs/theme-v1-contract.md:55)
- 重置外观只由用户点击触发，保留头像与已保存配置，并显式选中自定义外观，错误不会触发自动替换。(docs/theme-v1-contract.md:55)
- 应用旧版配置时清除其没有声明的新增外观字段，避免沿用此前模板的输入框样式。(docs/theme-v1-contract.md:55)

### moss_atelier：两套模板的例子

- `moss_atelier` 的 `toolpkg_id` 为 `com.operit.moss_atelier`，`version` 为 `0.1.0`，`api_version` 为 `2.0.0`。(plugins/packages/external/moss_atelier/manifest.json:4)
- `moss_atelier` 的中文显示名为苔庭，英文显示名为 Moss Atelier。(plugins/packages/external/moss_atelier/manifest.json:8)
- `moss_atelier` 的中文描述为苔绿与暖砂两套外观模板，配有完整明暗配色、柔和背景与悬浮输入框。(plugins/packages/external/moss_atelier/manifest.json:12)
- 示例包的 `enabled_by_default` 为 false。(plugins/packages/external/moss_atelier/manifest.json:18)
- 示例包的 `themes` 包含 `moss` 模板。(plugins/packages/external/moss_atelier/manifest.json:29)
- 第二套模板的 `id` 为 `dune`。(plugins/packages/external/moss_atelier/manifest.json:45)
- `moss` 模板的 `path` 为 `templates/moss/theme.json`，`preview` 为 `templates/moss/preview.png`。(plugins/packages/external/moss_atelier/manifest.json:30)
- 模板资源清单登记 `theme.json`（`application/json`）、`preview.png`（`image/png`）、`assets/images/ambient.png`（`image/png`）三项。(plugins/packages/external/moss_atelier/manifest.json:38)
- `dune` 模板的 `path` 为 `templates/dune/theme.json`，`preview` 为 `templates/dune/preview.png`。(plugins/packages/external/moss_atelier/manifest.json:46)
- 第二套模板的资源清单也是 `theme.json`、`preview.png`、`assets/images/ambient.png` 三项。(plugins/packages/external/moss_atelier/manifest.json:56)

### Studio 预览与导出协议

- 主题作者只提供声明式 JSON、PNG/JPEG、受限静态 SVG 和静态 TrueType（`.ttf`）字节，不含任何可执行脚本。(docs/theme-studio-protocol-v1.md:7)
- 预览核在自身同源 Rust/WASM Worker 中独立执行闭合 JSON Schema/语义校验以及与客户端导入完全一致的 L4 图片/SVG/字体/九宫格像素检查。(docs/theme-studio-protocol-v1.md:13)
- 预览核校验通过后才允许调用 Flutter 图片解码与 `FontLoader`。(docs/theme-studio-protocol-v1.md:13)
- SVG 仅支持标准命名空间下的路径、基本图形、分组、渐变和本地 clip/paint 引用，最大 1 MiB、512 个元素、32 层深、4096×4096 且不超过 16,777,216 像素。(docs/theme-studio-protocol-v1.md:11)
- SVG 拒绝 DTD/实体、脚本、事件属性、CSS/style、外链、`foreignObject`、滤镜、动画、嵌入式文档和未知属性。(docs/theme-studio-protocol-v1.md:11)
- 握手第一步：Studio 加载部署生成的 `theme-studio-config.json` / `renderer-release.json`，获取固定的 `rendererReleaseId`、`fixtureVersion` 与 `fixtureSourceSha256`，并先订阅 `window.message`。(docs/theme-studio-protocol-v1.md:15)
- 预览核在自身 Rust/WASM Worker 启动就绪后，向 `window.parent` 发送 `operit.theme.preview.available.v1`。(docs/theme-studio-protocol-v1.md:17)
- Studio 通过 `operit.theme.studio.connect.v1` 向子页转移唯一一个 `MessagePort`。(docs/theme-studio-protocol-v1.md:18)
- 子页核对 exact origin、`window.parent` 消息源、相同协议头、单一端口且无既有连接后，在私有端口返回 `operit.theme.preview.ready.v1` 与 `nextRevision`。(docs/theme-studio-protocol-v1.md:19)
- 所有协议消息均携带固定头部：`protocolVersion: 1`、`nonce`（16～128 个 URL-safe 字符，由 Studio 用加密安全随机源生成）、`rendererReleaseId`。(docs/theme-studio-protocol-v1.md:25)
- 初始内置样例占用 revision 1，Studio 从 `nextRevision` 开始递增，通道不可重复握手或在致命协议错误后复用。(docs/theme-studio-protocol-v1.md:29)
- 单次 Worker 契约操作超时为 15 秒，首次 Flutter Web 场景帧等待上限为 60 秒。(docs/theme-studio-protocol-v1.md:29)
- `operit.theme.preview.load.v1` 的 `canonicalThemeJson` 是 Rust `normalizeThemeDraft` 输出的完整规范化 JSON 字符串。(docs/theme-studio-protocol-v1.md:37)
- 预览的 `brightness` 为 `light` 或 `dark`，是预览环境亮暗模式，不写入 theme.json。(docs/theme-studio-protocol-v1.md:39)
- 预览的 `viewport` 逻辑像素整数取 1280×800 / 390×844 / 768×1024 / 1440×900 四档。(docs/theme-studio-protocol-v1.md:40)
- 预览的 `showConversation` 是固定场景对话开关，Studio 默认开启 true，不写入 theme.json。(docs/theme-studio-protocol-v1.md:41)
- 预览素材通过 structured clone 的 `Uint8Array` 传输，不使用 base64 或 JSON 整数数组。(docs/theme-studio-protocol-v1.md:45)
- 新 revision 一经接收立即撤销旧回执。(docs/theme-studio-protocol-v1.md:45)
- `loaded.v1` 仅表示资源准备完成，`rendered.v1` 在真实 Flutter 帧绘制完成后发出。(docs/theme-studio-protocol-v1.md:54)
- 预览核注册 6 个可检视部件目标：`background`、`navigation.sidebar`、`chat.topBar`、`chat.userMessage`、`chat.aiMessage`、`chat.composer`。(docs/theme-studio-protocol-v1.md:59)
- `operit.theme.preview.sceneMode.v1` 在不改 `theme.json` 的前提下切换正常对话与空白会话，并等待真实帧结束后刷新 `rendered.v1` 回执。(docs/theme-studio-protocol-v1.md:61)
- 帧捕获 `operit.theme.preview.capture.v1` 要求当前未处于 Inspector 高亮描边状态，且 revision / viewport / showConversation 与当前 `rendered.v1` 回执完全一致。(docs/theme-studio-protocol-v1.md:65)
- 预览核调用 Flutter `RepaintBoundary.toImage(pixelRatio: 1)` 截取真实渲染帧，通过 `operit.theme.preview.captured.v1` 返回 `pngBytes` 与 `pngSha256`。(docs/theme-studio-protocol-v1.md:66)
- 导出 `.toolpkg` 时若当前处于暗色、非 1280×800 视口、空白会话或存在未重新渲染的草稿改动，Studio 自动切换至亮色 + 1280×800 桌面视口 + 正常对话场景完成真实帧渲染与 `preview.png` 捕获。(docs/theme-studio-protocol-v1.md:67)
- `exportToolPkgFromTheme` 生成固定顺序、固定 DOS 时间戳与权限的 Stored ZIP（`.toolpkg`），并在返回前立刻用导入校验器 `validate_toolpkg_theme_templates` 对生成字节执行完整自检。(docs/theme-studio-protocol-v1.md:75)
- `validateAuthoredToolPkg` 导出已有 ToolPkg 时对合并后归档的所有模板执行校验，校验失败时不提供下载。(docs/theme-studio-protocol-v1.md:76)
- Studio 通过 `export_toolpkg_from_theme_transfer` 创建包含模板的普通 ToolPkg。(docs/theme-v1-contract.md:39)
- 编辑既有包时 Studio 保留其他 manifest 能力、其他模板及原有资源，导出只更新所选模板及用户修改的包元数据。(docs/theme-v1-contract.md:39)
- 编辑既有 ToolPkg 时，Studio 将所选模板的渲染结果写回对应声明，保留其他脚本、资源和模板，原包及所选模板 ID 随本地草稿一起保存在 IndexedDB。(docs/theme-studio-protocol-v1.md:93)
- 协议与契约测试入口为 `cargo test -p operit-plugin-theme` 与 `node --experimental-strip-types --test tools/theme/studio_message_port.test.ts`。(docs/theme-studio-protocol-v1.md:89)

## 关键符号

- `themes` — manifest 的主题模板数组，每项含 `id`、`path`、`preview`、`files`。(docs/theme-v1-contract.md:3)
- `ToolPkgArchiveParser::readThemeTemplates` — 枚举并校验包内主题模板的入口。(docs/theme-v1-contract.md:37)
- `validate_declared_theme_templates` — 校验已声明模板资源的函数。(docs/theme-v1-contract.md:37)
- `validate_toolpkg_theme_templates` — 检查 Studio 生成的根目录 manifest 输出的函数。(docs/theme-v1-contract.md:37)
- `ValidatedThemeTemplate` — 对应模板的渲染校验结果。(docs/theme-v1-contract.md:35)
- `ThemeValidationReceipt` — 对应模板的渲染校验收据。(docs/theme-v1-contract.md:35)
- `previewToolPkgTheme(packageName, templateId)` — 读取注册包并验证模板与媒体的函数。(docs/theme-v1-contract.md:47)
- `ThemeTemplateService` — 复制模板资源并替换引用的服务。(docs/theme-v1-contract.md:47)
- `ThemeConfigManager.create` — 创建独立命名配置的原有入口。(docs/theme-v1-contract.md:47)
- `ThemeConfigManager.apply` — 选中独立配置的原有入口。(docs/theme-v1-contract.md:47)
- `themePaletteJson` — 保存完整明暗配色的可选外观字段。(docs/theme-v1-contract.md:49)
- `export_toolpkg_from_theme_transfer` — Studio 创建含模板 ToolPkg 的入口。(docs/theme-v1-contract.md:39)
- `normalizeThemeDraft` — WASM 绑定，校验并展开编辑态草稿默认值。(docs/theme-studio-protocol-v1.md:73)
- `exportToolPkgFromTheme` — WASM 绑定，生成确定性 Stored ZIP（`.toolpkg`）。(docs/theme-studio-protocol-v1.md:75)
- `validateAuthoredToolPkg` — WASM 绑定，校验合并后归档的全部模板。(docs/theme-studio-protocol-v1.md:76)
- `packageManager().getToolPkgContainerRuntimes()` — 新建对话框动态读取模板来源的调用。(docs/theme-v1-contract.md:45)

## 调用链

1. 包管理安装 `.toolpkg`：主题模板的安装、作用域、同步、更新和卸载全部由现有包管理系统负责。(docs/theme-v1-contract.md:3)
2. 用户打开外观新建对话框：模板来源通过 `packageManager().getToolPkgContainerRuntimes()` 动态读取。(docs/theme-v1-contract.md:45)
3. 用户选择模板：`previewToolPkgTheme(packageName, templateId)` 读取当前注册包，验证模板和媒体，返回规范化视觉 JSON 与资源。(docs/theme-v1-contract.md:47)
4. 烘焙：`ThemeTemplateService` 将模板图片和字体复制到 `runtime/data/user_assets/theme` 资源池，把包内相对引用替换为外观资源引用。(docs/theme-v1-contract.md:47)
5. 建配置：原有 `ThemeConfigManager.create` 和 `apply` 创建并选中独立配置，模板只是创建源。(docs/theme-v1-contract.md:47)
6. 同步与渲染：配置和复制后的资源沿用原有 Space 同步，后续渲染读取配置与外观资源，不再依赖来源插件是否安装。(docs/theme-v1-contract.md:51)
7. Studio 导出：草稿经 `normalizeThemeDraft` 规范化后由 `operit.theme.preview.load.v1` 加载，真实帧渲染后经 `operit.theme.preview.capture.v1` 捕获 `preview.png`，再由 `exportToolPkgFromTheme` 生成确定性 Stored ZIP（`.toolpkg`）。(docs/theme-studio-protocol-v1.md:67)

## 来源

- `core/crates/plugin/theme/schema/theme-v1.schema.json`（1247 行）
- `core/crates/plugin/theme/schema/theme-template.schema.json`（58 行）
- `docs/theme-v1-contract.md`（55 行）
- `docs/theme-studio-protocol-v1.md`（93 行）
- `plugins/packages/external/moss_atelier/manifest.json`（66 行）
