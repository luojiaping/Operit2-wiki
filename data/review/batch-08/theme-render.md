---
title: 主题渲染与媒体校验
module: theme
platforms: [all]
sources: 6
date: 2026-11-11
---

## 概述

- 主题渲染与媒体校验指主题模板在交给 Flutter 渲染前经历的 L4 图片、SVG、字体与九宫格像素检查。`docs/theme-studio-protocol-v1.md:10`
- L4 检查在同源 Rust/WASM Worker 中独立执行，校验通过后才允许调用 Flutter 图片解码与 `FontLoader`。`docs/theme-studio-protocol-v1.md:10`
- 主题作者只提供声明式 JSON、PNG/JPEG、受限静态 SVG 与静态 TrueType 字节，不含可执行脚本。`docs/theme-studio-protocol-v1.md:7`
- theme crate 不做 I/O、Host 调用、运行时启动或主题应用。`core/crates/plugin/theme/src/lib.rs:3`
- 父页声称的 `themeSha256` 或素材 SHA-256 只用于一致性比对，不授予媒体解析权限。`docs/theme-studio-protocol-v1.md:9`

## AI 速览

- `validate_media_files` — 按 manifest 逐文件做 L4 媒体校验并出具收据。`core/crates/plugin/theme/src/media.rs:65`
- `validate_bubble_pixels` — 检查三处气泡与输入框图片的裁剪与九宫格切片像素。`core/crates/plugin/theme/src/media.rs:903`
- `validate_image` — 只接受 PNG 与 JPEG，做容器检查与完整解码。`core/crates/plugin/theme/src/media.rs:200`
- `validate_svg` — 对静态 SVG 子集做结构与引用检查。`core/crates/plugin/theme/src/media.rs:242`
- `validate_true_type` — 对静态 TrueType 字体做表结构、校验和与字形轮廓检查。`core/crates/plugin/theme/src/media.rs:765`
- `export_toolpkg_from_theme` — 导出主入口：校验草稿并生成确定性 Stored ZIP。`core/crates/plugin/theme/src/export.rs:44`
- `export_toolpkg_from_theme_transfer` — 导出传输入口：元数据 JSON 与二进制媒体分开传输。`core/crates/plugin/theme/src/export.rs:227`
- `normalize_draft` — 唯一给省略的创作 token 补版本化默认值的地方。`core/crates/plugin/theme/src/lib.rs:319`
- `parse_theme` — 用 schema 校验、规范化并检查视觉关系。`core/crates/plugin/theme/src/lib.rs:302`
- `check_theme_template_files` — 核对主题引用资产与 manifest 声明资产一致。`core/crates/plugin/theme/src/lib.rs:394`
- `ThemeMediaValidation` — 单个媒体文件的 L4 校验收据，不含资源字节。`core/crates/plugin/theme/src/media.rs:27`
- `ThemeValidationReceipt` — 单个模板的确定性渲染证据。`core/crates/plugin/theme/src/lib.rs:171`
- 主入口函数为 `export_toolpkg_from_theme`（导出）`core/crates/plugin/theme/src/export.rs:44`与 `validate_template`（模板全量校验）`core/crates/plugin/theme/src/lib.rs:439`。
- 数据流向一句话：主题 JSON 与资产字节先过契约与 L4 校验，再由导出写成确定性 Stored ZIP。`core/crates/plugin/theme/src/export.rs:90`

## 核心机制

### JSON 与契约

- JSON 嵌套深度上限为 32。`core/crates/plugin/theme/src/json.rs:6`
- 非有限 JSON 数字被拒绝。`core/crates/plugin/theme/src/json.rs:34`
- 重复 JSON 键被拒绝。`core/crates/plugin/theme/src/json.rs:53`
- JSON 输入必须为 UTF-8。`core/crates/plugin/theme/src/json.rs:68`
- json 的 `parse` 在字节数超过上限时拒绝输入。`core/crates/plugin/theme/src/json.rs:63`
- json 的 `parse` 在反序列化后要求无多余尾随内容。`core/crates/plugin/theme/src/json.rs:62`
- `parse_theme` 用 schema 校验、规范化并检查视觉关系。`core/crates/plugin/theme/src/lib.rs:302`
- `normalize_draft` 是唯一给省略的创作 token 补版本化默认值的地方。`core/crates/plugin/theme/src/lib.rs:319`
- `validate_palette` 用与模板相同的完整颜色契约校验 palette。`core/crates/plugin/theme/src/lib.rs:312`
- `check_visual_relations` 要求用户气泡、AI 气泡、输入框图片的 slice 结束值至少比开始值大 0.01。`core/crates/plugin/theme/src/lib.rs:370`
- 资源路径为空、超过 128 字符、非 ASCII 或超过 4 段时拒绝。`core/crates/plugin/theme/src/lib.rs:487`
- 资源路径拒绝 con、prn、aux、nul、com1 至 com9、lpt1 至 lpt9 等 Windows 保留名。`core/crates/plugin/theme/src/lib.rs:503`
- 资源路径拼写由固定正则表达式限定，只接受 manifest.json、theme.json、preview.png、assets/images/、assets/fonts/、licenses/ 下的登记拼写。`core/crates/plugin/theme/src/lib.rs:513`
- 模板资源超过 24 个或字体超过 3 个时拒绝。`core/crates/plugin/theme/src/lib.rs:286`
- 模板必须包含 theme.json 与 preview.png。`core/crates/plugin/theme/src/lib.rs:292`
- `check_theme_template_files` 要求 theme.json 引用的资产集合等于 manifest 声明的资产集合。`core/crates/plugin/theme/src/lib.rs:394`
- `ContractCheckedTheme` 只证明契约与文件集合，不作为媒体安全凭证、安装回执、官方徽章或 ZIP 校验证据。`core/crates/plugin/theme/src/lib.rs:145`
- `canonical_bytes` 输出对象键已排序的紧凑 UTF-8 JSON。`core/crates/plugin/theme/src/lib.rs:109`
- ThemeSpecV1 的 `sha256` 对 `canonical_bytes` 求 SHA-256。`core/crates/plugin/theme/src/lib.rs:116`
- `asset_paths` 收集 background 与 chat 下的资产指针。`core/crates/plugin/theme/src/lib.rs:124`
- `asset_paths` 收集 input 与 typography 下的资产指针。`core/crates/plugin/theme/src/lib.rs:121`
- `asset_paths` 只收以 assets/ 开头的值。`core/crates/plugin/theme/src/lib.rs:121`
- `metadata_for_path` 给 manifest.json 定 application/json 与 64 KiB 上限，给 theme.json 定 application/json 与 256 KiB 上限，给 preview.png 定 image/png 与 4 MiB 上限。`core/crates/plugin/theme/src/lib.rs:529`
- `metadata_for_path` 给 assets/images/ 下的 png、jpg、jpeg 定 16 MiB 上限。`core/crates/plugin/theme/src/lib.rs:529`
- `metadata_for_path` 给 assets/images/ 下的 svg 定 image/svg+xml 与 1 MiB 上限。`core/crates/plugin/theme/src/lib.rs:529`
- `metadata_for_path` 给 assets/fonts/ 下的 ttf 定 font/ttf 与 32 MiB 上限。`core/crates/plugin/theme/src/lib.rs:529`
- `metadata_for_path` 给 licenses/ 下的 txt 定 text/plain 与 128 KiB 上限。`core/crates/plugin/theme/src/lib.rs:529`

### 预算总表

- 归档总字节上限 `MAX_ARCHIVE_BYTES` 为 64 MiB。`core/crates/plugin/theme/src/lib.rs:44`
- 展开总字节上限 `MAX_EXPANDED_BYTES` 为 128 MiB。`core/crates/plugin/theme/src/lib.rs:45`
- manifest 上限 `MAX_MANIFEST_BYTES` 为 64 KiB。`core/crates/plugin/theme/src/lib.rs:46`
- 主题 JSON 上限 `MAX_THEME_BYTES` 为 256 KiB。`core/crates/plugin/theme/src/lib.rs:47`
- 资源上限 `MAX_RESOURCES` 为 24，字体上限 `MAX_FONTS` 为 3。`core/crates/plugin/theme/src/lib.rs:48`
- 单张图片上限 `MAX_IMAGE_BYTES` 为 16 MiB。`core/crates/plugin/theme/src/lib.rs:50`
- SVG 上限 `MAX_SVG_BYTES` 为 1 MiB。`core/crates/plugin/theme/src/lib.rs:51`
- 字体上限 `MAX_FONT_BYTES` 为 32 MiB。`core/crates/plugin/theme/src/lib.rs:52`
- 协议文本上限 `MAX_LICENSE_BYTES` 为 128 KiB，预览图上限 `MAX_PREVIEW_BYTES` 为 4 MiB。`core/crates/plugin/theme/src/lib.rs:53`
- 单图边长上限 `MAX_IMAGE_DIMENSION` 为 4096，单图像素上限 `MAX_IMAGE_PIXELS` 为 16,777,216。`core/crates/plugin/theme/src/lib.rs:55`
- 像素总计上限 `MAX_TOTAL_IMAGE_PIXELS` 为 64,000,000。`core/crates/plugin/theme/src/lib.rs:57`
- 预览图尺寸 `PREVIEW_WIDTH` 为 1280，`PREVIEW_HEIGHT` 为 800。`core/crates/plugin/theme/src/lib.rs:58`
- 字体表上限 `MAX_FONT_TABLES` 为 64，字形上限 `MAX_FONT_GLYPHS` 为 65,535。`core/crates/plugin/theme/src/lib.rs:60`
- `MAX_VALIDATOR_MEMORY_BYTES` 声明为 512 MiB，基线中无执行消费者，未接入校验器内存执行约束。`core/crates/plugin/theme/src/lib.rs:62`
- `MAX_VALIDATOR_TASK_MILLIS` 声明为 15,000，Rust 侧无执行消费者。`core/crates/plugin/theme/src/lib.rs:63`
- Worker 契约任务由 `MAX_TASK_MILLIS` 计时，超时关闭通道。`tools/theme/preview/web/theme_contract_client.js:72`

### 图片校验

- `validate_media_files` 跳过 application/json 与 text/plain，拒绝未登记的声明媒体类型。`core/crates/plugin/theme/src/media.rs:65`
- `ThemeMediaValidation` 有 Image、TrueTypeFont、SvgImage 三个变体且不含资源字节。`core/crates/plugin/theme/src/media.rs:27`
- 媒体校验缓存键由路径、媒体类型、字节长度与 SHA-256 组成。`core/crates/plugin/theme/src/media.rs:87`
- 媒体校验缓存最多保留 32 条，满时淘汰最旧一条。`core/crates/plugin/theme/src/media.rs:152`
- preview.png 必须恰好为 1280×800。`core/crates/plugin/theme/src/media.rs:163`
- 全部图片与 SVG 的像素总数不得超过 64,000,000。`core/crates/plugin/theme/src/media.rs:169`
- `validate_image` 只接受 image/png 与 image/jpeg。`core/crates/plugin/theme/src/media.rs:200`
- 解码器识别出的格式必须与声明的媒体类型一致。`core/crates/plugin/theme/src/media.rs:208`
- 解码器限制为宽高各至多 4096 与单次分配至多 192 MiB。`core/crates/plugin/theme/src/media.rs:214`
- 解码后宽高非零且至多 4096，像素数至多 16,777,216。`core/crates/plugin/theme/src/media.rs:222`
- 解码尺寸必须与容器头记录的尺寸一致。`core/crates/plugin/theme/src/media.rs:228`
- `validate_image` 返回的帧数为 1。`core/crates/plugin/theme/src/media.rs:197`
- PNG 签名无效时拒绝。`core/crates/plugin/theme/src/media.rs:644`
- PNG 块数上限为 4096。`core/crates/plugin/theme/src/media.rs:654`
- PNG 逐块校验 CRC，且首块必须为 IHDR。`core/crates/plugin/theme/src/media.rs:666`
- PNG 的 IDAT 块必须连续。`core/crates/plugin/theme/src/media.rs:680`
- PNG 的 IEND 必须长度为 0、唯一、位于 IDAT 之后且为文件末尾。`core/crates/plugin/theme/src/media.rs:685`
- PNG 拒绝 acTL、fcTL、fdAT 动画块。`core/crates/plugin/theme/src/media.rs:683`
- PNG 拒绝 iCCP、zTXt、iTXt 压缩元数据并拒绝未知关键块。`core/crates/plugin/theme/src/media.rs:688`
- PNG 缺少 IHDR、IDAT 或 IEND 时拒绝。`core/crates/plugin/theme/src/media.rs:696`
- JPEG 必须以 SOI 标记 0xFFD8 开头。`core/crates/plugin/theme/src/media.rs:701`
- JPEG 拒绝 MPF、Exif、ICC_PROFILE 的 APP 段。`core/crates/plugin/theme/src/media.rs:725`
- JPEG 扫描头要求已有 SOF、组件数 1 至 4 且扫描总数至多 128。`core/crates/plugin/theme/src/media.rs:730`
- JPEG 只接受 SOF 标记 0xc0 与 0xc2、8 位采样、组件数 1 至 4。`core/crates/plugin/theme/src/media.rs:735`

### SVG 校验

- SVG 字节为空或超过 1 MiB 时拒绝。`core/crates/plugin/theme/src/media.rs:242`
- SVG 在调用 XML 解析器前拒绝 DTD 与实体声明。`core/crates/plugin/theme/src/media.rs:250`
- SVG 根元素必须为标准命名空间下的 svg 且必须带 viewBox。`core/crates/plugin/theme/src/media.rs:287`
- SVG 元素数至多 512，嵌套深度至多 32。`core/crates/plugin/theme/src/media.rs:338`
- SVG 只接受 svg、g、defs、path、rect、circle、ellipse、line、polyline、polygon、linearGradient、radialGradient、stop、clipPath、title、desc 元素。`core/crates/plugin/theme/src/media.rs:343`
- SVG 文本只允许出现在 title 或 desc 节点内且至多 512 字符。`core/crates/plugin/theme/src/media.rs:397`
- SVG 的本地 paint 或 clip 引用必须解析到已声明的 id。`core/crates/plugin/theme/src/media.rs:407`
- SVG 固有宽高各自至多 4096。`core/crates/plugin/theme/src/media.rs:313`
- SVG 路径数据为空或超过 65,536 字符时拒绝。`core/crates/plugin/theme/src/media.rs:565`
- SVG 路径 token 数上限为 16,384。`core/crates/plugin/theme/src/media.rs:605`
- 协议文档规定 SVG 最大 1 MiB、512 个元素、32 层深、4096×4096 且至多 16,777,216 像素，拒绝 DTD/实体、脚本、事件属性、CSS/style、外链、foreignObject、滤镜、动画、嵌入式文档与未知属性。`docs/theme-studio-protocol-v1.md:11`

### 字体校验

- 字体只接受 sfnt 版本 0x00010000 的静态 TrueType 轮廓。`core/crates/plugin/theme/src/media.rs:765`
- 字体表数量为 0 或超过 64 时拒绝。`core/crates/plugin/theme/src/media.rs:767`
- 字体表标签必须升序排列、逐表校验和通过且表之间不重叠。`core/crates/plugin/theme/src/media.rs:778`
- 字体整文件校验和必须等于 0xb1b0_afba 且表间与尾部不得有非零未登记字节。`core/crates/plugin/theme/src/media.rs:786`
- 字体拒绝 CFF、CFF2、COLR、CPAL、SVG、sbix、CBDT、CBLC、EBDT、EBLC、fvar、gvar、avar、HVAR、MVAR、VVAR、cvar 共 17 类表。`core/crates/plugin/theme/src/media.rs:787`
- 字体必须包含 head、maxp、hhea、hmtx、loca、glyf、cmap 共 7 张必需表。`core/crates/plugin/theme/src/media.rs:789`
- 字体 units_per_em 取值范围为 16 至 16384，loca 格式只接受 0 或 1。`core/crates/plugin/theme/src/media.rs:799`
- 字体字形数为 0 或超过 65,535 时拒绝。`core/crates/plugin/theme/src/media.rs:801`
- 字体 cmap 子表数为 0 或超过 64 时拒绝。`core/crates/plugin/theme/src/media.rs:869`
- 字体 cmap 必须包含 Unicode 子表。`core/crates/plugin/theme/src/media.rs:876`
- 字形轮廓遍历按单个字形至多 32,768 事件、总计至多 8,000,000 事件设限。`core/crates/plugin/theme/src/media.rs:863`

### 九宫格像素检查与预览门禁

- `validate_bubble_pixels` 检查 chat/user、chat/ai、input 三处图片。`core/crates/plugin/theme/src/media.rs:903`
- 气泡裁剪后每轴至少保留 3 个源像素。`core/crates/plugin/theme/src/media.rs:918`
- 九宫格切片要求 slice_start 至少为 1、slice_end 大于 slice_start 且小于裁剪后长度。`core/crates/plugin/theme/src/media.rs:924`
- 校验通过后才允许调用 Flutter 图片解码与 `FontLoader`。`docs/theme-studio-protocol-v1.md:10`
- 单次 Worker 契约操作超时为 15 秒，首次 Flutter Web 场景帧等待上限为 60 秒。`docs/theme-studio-protocol-v1.md:29`
- 预览核调用 Flutter `RepaintBoundary` 的 `toImage`（pixelRatio: 1）截取真实渲染帧并返回 `pngBytes` 与 `pngSha256`。`docs/theme-studio-protocol-v1.md:66`
- Studio 导出时若处于暗色、非 1280×800 视口、空白会话或有未重新渲染的草稿改动，会自动切换至亮色、1280×800 桌面视口、正常对话场景完成渲染与捕获后再导出。`docs/theme-studio-protocol-v1.md:67`

### 导出为二进制

- `export_toolpkg_from_theme` 先 `normalize_draft` 再 `validate_export_metadata`。`core/crates/plugin/theme/src/export.rs:44`
- 导出在写 ZIP 前先跑 `check_theme_template_files`，且文件总字节超过 64 MiB 时拒绝。`core/crates/plugin/theme/src/lib.rs:394`
- 导出 ZIP 用 Stored 压缩、固定 DOS 时间戳 1980-01-01 00:00:00 与 Unix 权限 0o100644。`core/crates/plugin/theme/src/export.rs:72`
- 导出 ZIP 按 manifest.json、theme.json、preview.png、assets/、licenses/ 的顺序写条目。`core/crates/plugin/theme/src/export.rs:78`
- 导出在返回前用 `validate_toolpkg_theme_templates` 对生成的归档字节做完整自检。`core/crates/plugin/theme/src/export.rs:90`
- 导出元数据要求 toolpkg_id 非空、协议文本至多 128 KiB、资产至多 24 个、预览图非空且至多 4 MiB。`core/crates/plugin/theme/src/export.rs:98`
- 导出资产路径必须以 assets/ 开头、媒体类型必须与路径推导的类型一致、字节非空且在上限内。`core/crates/plugin/theme/src/export.rs:111`
- 导出总字节超过 128 MiB 或字体超过 3 个时拒绝。`core/crates/plugin/theme/src/export.rs:128`
- 导出拒绝 theme.json 未引用的资产。`core/crates/plugin/theme/src/export.rs:165`
- 导出要求 theme.json 引用的每个资产恰好提供一次。`core/crates/plugin/theme/src/export.rs:173`
- 导出 manifest 的 theme_id 为 toolpkg_id 加 :default，template_id 为 default，path 为 theme.json，preview 为 preview.png。`core/crates/plugin/theme/src/export.rs:196`
- 导出 manifest 仅在协议文本非空时把 license 记为 licenses/agreement.txt。`core/crates/plugin/theme/src/export.rs:205`
- 导出传输把元数据 JSON 与二进制媒体分开传输，不把整个字体序列化为 JSON 整数数组。`core/crates/plugin/theme/src/export.rs:227`
- `export_toolpkg_from_theme_transfer` 要求预览图非空且至多 4 MiB。`core/crates/plugin/theme/src/export.rs:228`
- 协议文档列出的 Rust/WASM 绑定包括 `normalizeThemeDraft`、`validateThemePreviewDraft`、`exportToolPkgFromTheme`、`validateAuthoredToolPkg`。`docs/theme-studio-protocol-v1.md:74`

## 关键符号

- `ThemeSpecV1` `core/crates/plugin/theme/src/lib.rs:96` — 校验后的主题视觉定义，`canonical_bytes` 输出对象键已排序的紧凑 UTF-8 JSON。`core/crates/plugin/theme/src/lib.rs:109`
- ThemeSpecV1 的 `sha256` — 对 `canonical_bytes` 求 SHA-256。`core/crates/plugin/theme/src/lib.rs:116`
- `ThemeMediaValidation` — 单个媒体文件的 L4 校验收据，不含资源字节。`core/crates/plugin/theme/src/media.rs:27`
- `ThemeValidationReceipt` — 单个模板的确定性渲染证据，validator_version 为 1。`core/crates/plugin/theme/src/lib.rs:171`
- `ThemeValidationReceipt` 的 trust 字段为 Untrusted。`core/crates/plugin/theme/src/lib.rs:171`
- 校验收据逐文件记录 path、字节数与 SHA-256。`core/crates/plugin/theme/src/lib.rs:460`
- `ThemeTemplateTrust` — 只有 `Untrusted` 一个变体。`core/crates/plugin/theme/src/lib.rs:188`
- `ContractCheckedTheme` — 只证明契约与文件集合的中间结果。`core/crates/plugin/theme/src/lib.rs:145`
- `parse_theme` — 用 schema 校验、规范化并检查视觉关系。`core/crates/plugin/theme/src/lib.rs:302`
- `normalize_draft` — 唯一给省略的创作 token 补版本化默认值的地方。`core/crates/plugin/theme/src/lib.rs:319`
- `validate_palette` — 用与模板相同的完整颜色契约校验 palette。`core/crates/plugin/theme/src/lib.rs:312`
- `check_visual_relations` — 要求三处图片的 slice 结束值至少比开始值大 0.01。`core/crates/plugin/theme/src/lib.rs:370`
- `check_theme_template_files` — 要求 theme.json 引用的资产集合等于 manifest 声明的资产集合。`core/crates/plugin/theme/src/lib.rs:394`
- `validate_template` — 先跑 `validate_media_files` `core/crates/plugin/theme/src/media.rs:65`再跑 `validate_bubble_pixels` `core/crates/plugin/theme/src/media.rs:903`，出具校验收据。`core/crates/plugin/theme/src/lib.rs:439`
- `validate_media_files` — 按 manifest 逐文件做 L4 媒体校验。`core/crates/plugin/theme/src/media.rs:65`
- `validate_image` — 只接受 PNG 与 JPEG，做容器检查与完整解码。`core/crates/plugin/theme/src/media.rs:200`
- `validate_svg` — 对静态 SVG 子集做结构与引用检查。`core/crates/plugin/theme/src/media.rs:242`
- `validate_true_type` — 对静态 TrueType 字体做表结构、校验和与字形轮廓检查。`core/crates/plugin/theme/src/media.rs:765`
- `validate_bubble_pixels` — 检查三处气泡与输入框图片的裁剪与九宫格切片像素。`core/crates/plugin/theme/src/media.rs:903`
- `validate_theme_resource_path` — 资源路径为空、超过 128 字符、非 ASCII 或超过 4 段时拒绝。`core/crates/plugin/theme/src/lib.rs:487`
- `metadata_for_path` — 返回模板本地资源的渲染媒体类型与字节上限。`core/crates/plugin/theme/src/lib.rs:529`
- `export_toolpkg_from_theme` — 导出主入口：校验草稿并生成确定性 Stored ZIP。`core/crates/plugin/theme/src/export.rs:48`
- `export_toolpkg_from_theme_transfer` — 导出传输入口：元数据 JSON 与二进制媒体分开传输。`core/crates/plugin/theme/src/export.rs:227`
- `MAX_VALIDATOR_TASK_MILLIS` — 声明为 15,000，Rust 侧无执行消费者。`core/crates/plugin/theme/src/lib.rs:63`

## 调用链

### 模板全量校验

1. `parse_theme` 用 schema 校验、规范化并检查视觉关系。`core/crates/plugin/theme/src/lib.rs:302`
2. `check_theme_template_files` 要求 theme.json 引用的资产集合等于 manifest 声明的资产集合。`core/crates/plugin/theme/src/lib.rs:394`
3. `validate_template` 先跑 `validate_media_files` `core/crates/plugin/theme/src/media.rs:65`再跑 `validate_bubble_pixels` `core/crates/plugin/theme/src/media.rs:903`。`core/crates/plugin/theme/src/lib.rs:439`
4. `validate_media_files` 跳过 application/json 与 text/plain，拒绝未登记的声明媒体类型。`core/crates/plugin/theme/src/media.rs:65`
5. `validate_bubble_pixels` 检查 chat/user、chat/ai、input 三处图片。`core/crates/plugin/theme/src/media.rs:903`
6. 校验收据的 validator_version 为 1。`core/crates/plugin/theme/src/lib.rs:450`
7. 校验收据的 trust 为 Untrusted。`core/crates/plugin/theme/src/lib.rs:468`

### 导出为二进制 ToolPkg

1. `export_toolpkg_from_theme` 先 `normalize_draft` 再 `validate_export_metadata`。`core/crates/plugin/theme/src/export.rs:48`
2. 写 ZIP 前先跑 `check_theme_template_files`，且文件总字节超过 64 MiB 时拒绝。`core/crates/plugin/theme/src/lib.rs:394`
3. 导出 ZIP 用 Stored 压缩、固定 DOS 时间戳 1980-01-01 00:00:00 与 Unix 权限 0o100644。`core/crates/plugin/theme/src/export.rs:72`
4. 导出 ZIP 按 manifest.json、theme.json、preview.png、assets/、licenses/ 的顺序写条目。`core/crates/plugin/theme/src/export.rs:78`
5. 导出在返回前用 `validate_toolpkg_theme_templates` 对生成的归档字节做完整自检。`core/crates/plugin/theme/src/export.rs:90`

## 来源

- docs/theme-studio-protocol-v1.md（93 行）
- core/crates/plugin/theme/src/media.rs（950 行）
- core/crates/plugin/theme/src/lib.rs（564 行）
- core/crates/plugin/theme/src/export.rs（288 行）
- core/crates/plugin/theme/src/json.rs（74 行）
- tools/theme/preview/web/theme_contract_client.js（133 行）
- 以上 6 份 seed 共 2102 行，2026-11-12 对基线 AAswordman/Operit2 @ 364d1d594 全文读完；tools/theme/preview/web/theme_contract_client.js 于 2026-11-13 按评审意见补读 133 行；阅读记录见 tracking/read-batch-08/theme-render.txt。
- 协议文档中的主张（Rust/WASM 绑定名、握手与超时、帧捕获、导出前自动切换场景）在正文中表述为协议文档规定，未当作代码实现引用；对应代码文件 src/wasm.rs 与 src/preview.rs 不在本页 seed 清单内，未读未引。
- frontmatter platforms [all] 的依据：2026-11-12 对基线 364d1d594 的 5 份 seed 执行 grep -rn "cfg(target_os|cfg(target_family|cfg(windows|cfg(unix"，零命中。
- 主题快照字段数：本页不写具体数字；5 份 seed 全文读完未见以字段数为口径的快照定义，不沿用未经核实的数字。
