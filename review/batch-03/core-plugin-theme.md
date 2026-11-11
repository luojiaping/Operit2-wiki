---
title: 插件——主题 v1 契约
module: core
platforms: [all]
sources: 3
date: 2026-11-11
---

## 概述

- 本 crate 是主题模板的纯契约 crate，只做内存内校验，不做 I/O、不调 Host、不启动运行时、不应用主题。(core/crates/plugin/theme/src/lib.rs:3)
- 两份 schema 以常量 `THEME_TEMPLATE_SCHEMA` 与 `THEME_SCHEMA_V1` 内嵌进 crate。(core/crates/plugin/theme/src/lib.rs:42)
- 校验通过不等于安装安全，也不等于渲染安全：`ContractCheckedTheme` 只检查契约与文件集合，不得用作媒体安全凭证、安装收据、官方徽章或 ZIP 校验证据。(core/crates/plugin/theme/src/lib.rs:144)
- 信任枚举 `ThemeTemplateTrust` 只有 `Untrusted` 一个变体，字节与结构校验不断言发布者身份与策展。(core/crates/plugin/theme/src/lib.rs:188)
- ToolPkg 加载、可执行保护与安装属于共享包系统的职责，不属于本 crate（加载侧见 [[core-tool-packages-mcp|工具系统——包、技能与 MCP]]）。(core/crates/plugin/theme/src/lib.rs:5)
- 本页只写契约，不写主题功能；主题的实际应用行为不在本页范围。(core/crates/plugin/theme/src/lib.rs:3)

## AI 速览

- `ThemeTemplateMetadata` — 模板清单元数据。(core/crates/plugin/theme/src/lib.rs:67)
- `ThemeSpecV1` — 校验过的视觉定义。(core/crates/plugin/theme/src/lib.rs:96)
- `ContractCheckedTheme` — 只验契约与文件集合的轻量结果。(core/crates/plugin/theme/src/lib.rs:147)
- `ValidatedThemeTemplate` — 带收据的完整校验结果。(core/crates/plugin/theme/src/lib.rs:157)
- `ThemeValidationReceipt` — 渲染器证据。(core/crates/plugin/theme/src/lib.rs:171)
- `ThemeTemplateTrust` — 信任枚举，只含 `Untrusted`。(core/crates/plugin/theme/src/lib.rs:188)
- `ThemeFileValidation` — 单文件校验记录。(core/crates/plugin/theme/src/lib.rs:194)
- `parse_theme` — 严格解析 theme.json。(core/crates/plugin/theme/src/lib.rs:302)
- `normalize_draft` — 草稿规范化，唯一补默认值处。(core/crates/plugin/theme/src/lib.rs:319)
- `check_theme_template_files` — 校验单个模板的文件集合。(core/crates/plugin/theme/src/lib.rs:394)
- `validate_theme_resource_path` — 资源路径白名单校验。(core/crates/plugin/theme/src/lib.rs:483)
- `THEME_SCHEMA_V1` — 内嵌的 v1 视觉 schema。(core/crates/plugin/theme/src/lib.rs:43)
- `THEME_TEMPLATE_SCHEMA` — 内嵌的模板声明 schema。(core/crates/plugin/theme/src/lib.rs:42)
- 主入口之一是 `parse_theme`，严格解析 theme.json。(core/crates/plugin/theme/src/lib.rs:302)
- 另一主入口是 `normalize_draft`，草稿规范化并补版本化默认值。(core/crates/plugin/theme/src/lib.rs:319)
- 数据流向：字节输入 → schema 校验 → 规范化 → 视觉关系检查 → 封存视觉定义。(core/crates/plugin/theme/src/lib.rs:303)
- 全程内存内、无 I/O。(core/crates/plugin/theme/src/lib.rs:3)

## 核心机制

### 两份 schema 约束什么

- theme-v1.schema.json 遵循 JSON Schema draft 2020-12，`$id` 为 `urn:operit2:theme-visual:1`。(core/crates/plugin/theme/schema/theme-v1.schema.json:1070)
- 根对象必填 `palette`、`background`、`surfaces`、`chat`、`input`、`typography` 六节。(core/crates/plugin/theme/schema/theme-v1.schema.json:1063)
- 根对象 `additionalProperties` 为 `false`，拒绝未定义顶层字段。(core/crates/plugin/theme/schema/theme-v1.schema.json:3)
- `palette` 是 theme-v1 schema 根对象的必填节。(core/crates/plugin/theme/schema/theme-v1.schema.json:1063)
- palette 的 required 列表为 `light` 与 `dark`。(core/crates/plugin/theme/schema/theme-v1.schema.json:764)
- `light` 是 palette 的必填调色板。(core/crates/plugin/theme/schema/theme-v1.schema.json:764)
- light 调色板的 required 列表含 46 个颜色 token，首项为 `primary`。(core/crates/plugin/theme/schema/theme-v1.schema.json:336)
- `dark` 是 palette 的必填调色板。(core/crates/plugin/theme/schema/theme-v1.schema.json:764)
- dark 调色板的 required 列表含 46 个颜色 token，与 light 逐项相同。(core/crates/plugin/theme/schema/theme-v1.schema.json:713)
- light 与 dark 的 required 颜色 token 列表逐项相同（已逐项核对）。(core/crates/plugin/theme/schema/theme-v1.schema.json:336)
- 颜色 token 为 9 字符大写十六进制字符串，格式为 `^#[0-9A-F]{8}$`。(core/crates/plugin/theme/schema/theme-v1.schema.json:17)
- background 节的 `asset` 只接受 `assets/images` 下的 png、jpg、jpeg、svg 或 null，默认 null。(core/crates/plugin/theme/schema/theme-v1.schema.json:774)
- background 节的 `fit` 只允许 `cover`。(core/crates/plugin/theme/schema/theme-v1.schema.json:784)
- `alignment` 只允许 `center`。(core/crates/plugin/theme/schema/theme-v1.schema.json:790)
- background 节的 `opacity` 范围 0–1，默认 0.3。(core/crates/plugin/theme/schema/theme-v1.schema.json:797)
- background 的 blur 节：`enabled` 默认 `false`，`radius` 范围 0–40，默认 12。(core/crates/plugin/theme/schema/theme-v1.schema.json:810)
- `surfaces` 只有 `transparent` 一个开关，默认 `false`。(core/crates/plugin/theme/schema/theme-v1.schema.json:838)
- chat 节的 `style` 只允许 `cursor` 或 `bubble`，默认 `cursor`。(core/crates/plugin/theme/schema/theme-v1.schema.json:852)
- chat 节的 `showAvatar` 默认 `true`。(core/crates/plugin/theme/schema/theme-v1.schema.json:864)
- chat 节的 `avatarShape` 只允许 `circle` 或 `square`，默认 `circle`。(core/crates/plugin/theme/schema/theme-v1.schema.json:870)
- `avatarCornerRadius` 范围 0–32，默认 8。(core/crates/plugin/theme/schema/theme-v1.schema.json:876)
- `chat` 是 theme-v1 schema 根对象的必填节。(core/crates/plugin/theme/schema/theme-v1.schema.json:1063)
- chat 的 required 列表含 `style`、`wideLayout`、`showAvatar`、`avatarShape`、`avatarCornerRadius`、`cursorUserColor`、`user`、`ai`。(core/crates/plugin/theme/schema/theme-v1.schema.json:901)
- input 节的 `style` 只允许 `classic` 或 `agent`，默认 `agent`。(core/crates/plugin/theme/schema/theme-v1.schema.json:916)
- `input` 是 theme-v1 schema 根对象的必填节。(core/crates/plugin/theme/schema/theme-v1.schema.json:1063)
- input 的 required 列表为 `style` 与 `floating`。(core/crates/plugin/theme/schema/theme-v1.schema.json:1018)
- input 节的 `settingsAsset` 只接受 `assets/images` 路径或 null。(core/crates/plugin/theme/schema/theme-v1.schema.json:944)
- input 节的 `settingsAssetSize` 范围 12–44，默认 18。(core/crates/plugin/theme/schema/theme-v1.schema.json:953)
- input 节的 `micAssetSize` 范围 12–48，默认 26。(core/crates/plugin/theme/schema/theme-v1.schema.json:983)
- typography 节的 `global` 默认 `noto-sans-sc`，只接受 `noto-sans-sc`、`cascadia-mono` 或 `assets/fonts` 下的 `.ttf`。(core/crates/plugin/theme/schema/theme-v1.schema.json:1028)
- `typography` 是 theme-v1 schema 根对象的必填节。(core/crates/plugin/theme/schema/theme-v1.schema.json:1063)
- typography 的 required 列表为 `global`、`user`、`ai`。(core/crates/plugin/theme/schema/theme-v1.schema.json:1054)
- bubbleImage 的 `asset` 必填且须为 `assets/images` 路径，`renderMode` 只允许 `tiled_nine_slice` 或 `nine_patch`，默认 `tiled_nine_slice`。(core/crates/plugin/theme/schema/theme-v1.schema.json:1085)
- bubbleImage 节的 `crop` 四边取值范围均为 0–0.45，默认 0。(core/crates/plugin/theme/schema/theme-v1.schema.json:1097)
- bubbleImage 节 slice 的 `xStart` 范围 0.05–0.9，默认 0.35；`xEnd` 范围 0.06–0.95，默认 0.65。(core/crates/plugin/theme/schema/theme-v1.schema.json:1140)
- bubbleImage 节 slice 的 `yStart` 范围 0.05–0.9，默认 0.35；`yEnd` 范围 0.06–0.95，默认 0.65。(core/crates/plugin/theme/schema/theme-v1.schema.json:1152)
- bubbleImage 节的 `scale` 范围 0.25–3，默认 1。(core/crates/plugin/theme/schema/theme-v1.schema.json:1168)
- `bubbleImage` 是 theme-v1 schema 的 $defs 定义之一。(core/crates/plugin/theme/schema/theme-v1.schema.json:1073)
- bubbleImage 的 required 列表含 `asset`、`renderMode`、`crop`、`slice`、`scale`。(core/crates/plugin/theme/schema/theme-v1.schema.json:1176)
- `bubble` 是 theme-v1 schema 的 $defs 定义之一。(core/crates/plugin/theme/schema/theme-v1.schema.json:1184)
- bubble 的 required 列表含 `color`、`textColor`、`image`、`roundedCorners`、`padding`。(core/crates/plugin/theme/schema/theme-v1.schema.json:1239)
- bubble 节 padding 的 `left` 范围 0–32，默认 12。(core/crates/plugin/theme/schema/theme-v1.schema.json:1219)
- theme-template.schema.json 遵循 JSON Schema draft 2020-12，`$id` 为 `urn:operit2:theme-template`。(core/crates/plugin/theme/schema/theme-template.schema.json:56)
- 模板声明必填 `id`、`path`、`preview`、`files`。(core/crates/plugin/theme/schema/theme-template.schema.json:50)
- 模板声明的 `files` 数组至少 2 项、至多 63 项。(core/crates/plugin/theme/schema/theme-template.schema.json:7)
- `files` 是 theme-template schema 根对象的必填字段。(core/crates/plugin/theme/schema/theme-template.schema.json:50)
- files 每项的 required 列表为 `path` 与 `mediaType`。(core/crates/plugin/theme/schema/theme-template.schema.json:31)
- files 每项 `mediaType` 只允许 `application/json`、`image/png`、`image/jpeg`、`image/svg+xml`、`font/ttf`、`text/plain` 六种。(core/crates/plugin/theme/schema/theme-template.schema.json:22)
- files 的 `path` 只接受 theme.json、preview.png、`licenses` 下的 `.txt`、`assets/images` 下的图片或 `assets/fonts` 下的 `.ttf`。(core/crates/plugin/theme/schema/theme-template.schema.json:13)

### 严格解析与草稿规范化

- `parse_theme` 要求包内含完整展开的视觉状态，缺失 token 即拒绝，即使草稿编辑器对该 token 有 schema 默认值。(core/crates/plugin/theme/src/lib.rs:301)
- `parse_theme` 以 `MAX_THEME_BYTES` 解析 theme.json，再做严格 schema 校验、规范化与视觉关系检查。(core/crates/plugin/theme/src/lib.rs:303)
- `validate_palette` 用同一套完整颜色契约校验持久化调色板。(core/crates/plugin/theme/src/lib.rs:312)
- `normalize_draft` 是唯一为省略的作者 token 补版本化默认值的地方，显式非法值、未知字段与坏资源路径仍是错误。(core/crates/plugin/theme/src/lib.rs:318)
- 气泡图 slice 的 `end` 必须至少比 `start` 大 0.01，否则报 contract 错误。(core/crates/plugin/theme/src/lib.rs:382)
- `canonical_bytes` 是 v1 规范表示：对象键排序、紧凑 UTF-8 JSON，整数视觉 token 以整数表示（含 -0）。(core/crates/plugin/theme/src/lib.rs:108)
- `sha256` 对规范字节做 SHA-256 摘要。(core/crates/plugin/theme/src/lib.rs:116)
- ThemeSpecV1 的 `as_json` 返回校验过的视觉定义。(core/crates/plugin/theme/src/lib.rs:102)
- `asset_paths` 收集 12 条 JSON 指针指向的资源引用。(core/crates/plugin/theme/src/lib.rs:126)
- 只有以 `assets/` 开头的引用会被保留。(core/crates/plugin/theme/src/lib.rs:138)

### 模板文件集合校验

- `check_template_metadata` 拒绝重复的模板资源路径。(core/crates/plugin/theme/src/lib.rs:267)
- 声明的 `media_type` 必须与路径推导出的媒体类型一致，否则报 contract 错误。(core/crates/plugin/theme/src/lib.rs:275)
- 资源超 24 或字体超 3 时报 `template exceeds resource budget`。(core/crates/plugin/theme/src/lib.rs:286)
- 模板必须包含 `theme.json` 与 `preview.png`，缺失即报 `required template resource is missing`。(core/crates/plugin/theme/src/lib.rs:293)
- 声明的模板文件必须存在、非空且不超单文件上限，展开总量超 `MAX_EXPANDED_BYTES` 即报错。(core/crates/plugin/theme/src/lib.rs:410)
- 文本资源必须为 UTF-8。(core/crates/plugin/theme/src/lib.rs:415)
- theme.json 引用的资源必须与模板声明的资源完全一致。(core/crates/plugin/theme/src/lib.rs:426)
- `ThemeValidationReceipt` 的 `validator_version` 为 1。(core/crates/plugin/theme/src/lib.rs:450)
- 收据的 `trust` 恒为 `ThemeTemplateTrust::Untrusted`。(core/crates/plugin/theme/src/lib.rs:468)
- 收据的 `files` 逐项记录已校验清单中每个文件的路径、字节数与 SHA-256。(core/crates/plugin/theme/src/lib.rs:461)
- `file_bytes` 只返回收据已覆盖路径的字节。(core/crates/plugin/theme/src/lib.rs:231)
- `metadata_for_path` 按路径返回媒体类型与字节上限，`theme.json` 为 `application/json` 且上限 256 KiB。(core/crates/plugin/theme/src/lib.rs:533)
- 完整性错误码为 `theme-package-integrity-invalid`，阶段为 `ValidationStage::Integrity`。(core/crates/plugin/theme/src/lib.rs:559)

### 资源预算上限

- 压缩包上限 `MAX_ARCHIVE_BYTES` 为 64 MiB，展开后总量上限 `MAX_EXPANDED_BYTES` 为 128 MiB。(core/crates/plugin/theme/src/lib.rs:44)
- 清单上限 `MAX_MANIFEST_BYTES` 为 64 KiB，theme.json 上限 `MAX_THEME_BYTES` 为 256 KiB。(core/crates/plugin/theme/src/lib.rs:46)
- 模板资源数上限 `MAX_RESOURCES` 为 24，字体数上限 `MAX_FONTS` 为 3。(core/crates/plugin/theme/src/lib.rs:48)
- 图片上限 `MAX_IMAGE_BYTES` 为 16 MiB，SVG 上限 `MAX_SVG_BYTES` 为 1 MiB，字体上限 `MAX_FONT_BYTES` 为 32 MiB，许可证上限 `MAX_LICENSE_BYTES` 为 128 KiB，预览图上限 `MAX_PREVIEW_BYTES` 为 4 MiB。(core/crates/plugin/theme/src/lib.rs:50)
- 图片边长上限 `MAX_IMAGE_DIMENSION` 为 4096，单图像素上限 `MAX_IMAGE_PIXELS` 为 16,777,216，总像素上限 `MAX_TOTAL_IMAGE_PIXELS` 为 64,000,000。(core/crates/plugin/theme/src/lib.rs:55)
- 预览尺寸 `PREVIEW_WIDTH` 为 1280，`PREVIEW_HEIGHT` 为 800。(core/crates/plugin/theme/src/lib.rs:58)
- 字体表上限 `MAX_FONT_TABLES` 为 64，字形上限 `MAX_FONT_GLYPHS` 为 65,535。(core/crates/plugin/theme/src/lib.rs:60)

### 路径白名单

- `validate_theme_resource_path` 逐字拒绝路径，不做规范化、清理或磁盘解析，唯一例外是 `.operit/market-install.seal`。(core/crates/plugin/theme/src/lib.rs:484)
- 资源路径限 128 字符、最多 4 段，且须通过 `is_ascii` 检查，超限报 `path exceeds v1 naming budget`。(core/crates/plugin/theme/src/lib.rs:488)
- 路径组件不许为空、`.`、`..` 或以点结尾，只允许小写字母、数字、`_`、`-`、`.`。(core/crates/plugin/theme/src/lib.rs:495)
- Windows 保留名 `con`、`prn`、`aux`、`nul`、`com1`–`com9`、`lpt1`–`lpt9` 命中任意路径组件的主干即拒绝，例如 assets/images/con.png、assets/fonts/nul.ttf 均被拒绝，虽然路径首段是 assets；该检查没有平台条件，在所有 Host 上执行。(core/crates/plugin/theme/src/lib.rs:506)
- 路径拼写必须命中白名单正则，否则报 `unregistered path spelling`。(core/crates/plugin/theme/src/lib.rs:520)

### 为什么不做 I/O、不做主题应用

- crate 文档声明：不做 I/O、不调 Host、不启动运行时、不应用主题。(core/crates/plugin/theme/src/lib.rs:3)
- lib.rs 的 use 列表只含 `regex`、`serde`、`serde_json`、`sha2` 与标准库集合、`OnceLock`，无文件系统与 Host 导入。(core/crates/plugin/theme/src/lib.rs:37)
- `parse_theme` 接收 `&[u8]` 字节输入。(core/crates/plugin/theme/src/lib.rs:302)
- `check_theme_template_files` 接收 `BTreeMap<String, Vec<u8>>` 文件映射。(core/crates/plugin/theme/src/lib.rs:394)
- ToolPkg 加载、可执行保护与安装属于共享包系统的职责。(core/crates/plugin/theme/src/lib.rs:5)

### 校验通过不等于安装/渲染安全

- `ContractCheckedTheme` 只检查契约与文件集合，不得用作媒体安全凭证、安装收据、官方徽章或 ZIP 校验证据。(core/crates/plugin/theme/src/lib.rs:144)
- 信任枚举 `ThemeTemplateTrust` 只有 `Untrusted` 一个变体，字节与结构校验不断言发布者身份与策展。(core/crates/plugin/theme/src/lib.rs:188)
- 收据的 `trust` 恒为 `ThemeTemplateTrust::Untrusted`。(core/crates/plugin/theme/src/lib.rs:468)
- 核实信任是未在本 crate 落地的设计约束（架构文档定义，运行时实现尚未确认）：代码注释称由 origin-policy 与 attestation 层另行提供。(core/crates/plugin/theme/src/lib.rs:185)
- lib.rs 的模块列表为 `error`、`export`、`json`、`media`、`preview`、`schema`、`toolpkg`，无 origin-policy 与 attestation 模块。(core/crates/plugin/theme/src/lib.rs:12)

## 关键符号

- `ThemeTemplateMetadata` — 模板清单元数据，含主题标识、包标识与文件清单。(core/crates/plugin/theme/src/lib.rs:67)
- `Author` — 作者，只含 `name`。(core/crates/plugin/theme/src/lib.rs:84)
- `ManifestFile` — 清单文件项，含 `path` 与 `media_type`。(core/crates/plugin/theme/src/lib.rs:90)
- `ThemeSpecV1` — 校验过的视觉定义。(core/crates/plugin/theme/src/lib.rs:96)
- `ContractCheckedTheme` — 只验契约与文件集合的轻量结果。(core/crates/plugin/theme/src/lib.rs:147)
- `ValidatedThemeTemplate` — 带收据的完整校验结果。(core/crates/plugin/theme/src/lib.rs:157)
- `ThemeValidationReceipt` — 渲染器证据。(core/crates/plugin/theme/src/lib.rs:171)
- `ThemeTemplateTrust` — 信任枚举，只含 `Untrusted`。(core/crates/plugin/theme/src/lib.rs:188)
- `ThemeFileValidation` — 单文件校验记录。(core/crates/plugin/theme/src/lib.rs:194)
- `parse_theme` — 严格解析 theme.json。(core/crates/plugin/theme/src/lib.rs:302)
- `normalize_draft` — 草稿规范化。(core/crates/plugin/theme/src/lib.rs:319)
- `validate_palette` — 校验持久化调色板。(core/crates/plugin/theme/src/lib.rs:312)
- `check_theme_template_files` — 校验单个模板的文件集合。(core/crates/plugin/theme/src/lib.rs:394)
- `validate_theme_resource_path` — 资源路径白名单校验。(core/crates/plugin/theme/src/lib.rs:483)
- `metadata_for_path` — 按路径返回媒体类型与字节上限。(core/crates/plugin/theme/src/lib.rs:529)
- `sha256_hex` — 计算精确字节的小写 SHA-256 摘要。(core/crates/plugin/theme/src/lib.rs:252)
- `THEME_SCHEMA_V1` — 内嵌的 v1 视觉 schema。(core/crates/plugin/theme/src/lib.rs:43)
- `THEME_TEMPLATE_SCHEMA` — 内嵌的模板声明 schema。(core/crates/plugin/theme/src/lib.rs:42)
- `MAX_ARCHIVE_BYTES` — 压缩包上限 64 MiB。(core/crates/plugin/theme/src/lib.rs:44)
- `MAX_EXPANDED_BYTES` — 展开总量上限 128 MiB。(core/crates/plugin/theme/src/lib.rs:45)
- `MAX_THEME_BYTES` — theme.json 上限 256 KiB。(core/crates/plugin/theme/src/lib.rs:47)
- `MAX_RESOURCES` — 模板资源数上限 24。(core/crates/plugin/theme/src/lib.rs:48)
- `MAX_FONTS` — 字体数上限 3。(core/crates/plugin/theme/src/lib.rs:49)
- `MAX_IMAGE_BYTES` — 图片上限 16 MiB。(core/crates/plugin/theme/src/lib.rs:50)
- `MAX_PREVIEW_BYTES` — 预览图上限 4 MiB。(core/crates/plugin/theme/src/lib.rs:54)
- `MAX_IMAGE_DIMENSION` — 图片边长上限 4096。(core/crates/plugin/theme/src/lib.rs:55)
- `PREVIEW_WIDTH` — 预览宽 1280。(core/crates/plugin/theme/src/lib.rs:58)
- `PREVIEW_HEIGHT` — 预览高 800。(core/crates/plugin/theme/src/lib.rs:59)

## 调用链

1. `parse_theme` 以 `MAX_THEME_BYTES` 解析 theme.json 字节。(core/crates/plugin/theme/src/lib.rs:303)
2. `schema::validate` 做严格校验。(core/crates/plugin/theme/src/lib.rs:305)
3. `schema::normalize` 规范化。(core/crates/plugin/theme/src/lib.rs:306)
4. `check_visual_relations` 检查 slice 关系。(core/crates/plugin/theme/src/lib.rs:307)
5. `finish_spec` 校验资源拼写并封存视觉定义。(core/crates/plugin/theme/src/lib.rs:308)
6. `normalize_draft` 先以非严格模式校验，再规范化，再以严格模式校验。(core/crates/plugin/theme/src/lib.rs:322)
7. `check_theme_template_files` 先调 `check_template_metadata` 校验清单。(core/crates/plugin/theme/src/lib.rs:399)
8. 逐文件校验存在、大小与 UTF-8。(core/crates/plugin/theme/src/lib.rs:410)
9. `parse_theme` 解析 theme.json。(core/crates/plugin/theme/src/lib.rs:418)
10. 比对 theme 引用资源与声明资源。(core/crates/plugin/theme/src/lib.rs:426)
11. 返回 `ContractCheckedTheme`。(core/crates/plugin/theme/src/lib.rs:431)
12. `validate_template` 在此基础上做媒体校验并生成收据。(core/crates/plugin/theme/src/lib.rs:444)
13. 收据 `validator_version` 为 1。(core/crates/plugin/theme/src/lib.rs:450)
14. 收据 `trust` 为 `Untrusted`。(core/crates/plugin/theme/src/lib.rs:468)

## 来源

- core/crates/plugin/theme/src/lib.rs
- core/crates/plugin/theme/schema/theme-v1.schema.json
- core/crates/plugin/theme/schema/theme-template.schema.json
