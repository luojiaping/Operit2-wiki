# Critic 评审：core-foundation（基础层——共享契约与数据模型）

- 评审对象：`review/batch-02/core-foundation.md` + `review/batch-02/core-foundation.facts.json`（250 条 facts）
- 评审 Issue：#13
- 源码基线：`~/workspace/Operit2` HEAD 已核实为 `364d1d594`，与钉住 commit 一致
- 评审人：独立 critic（未参与写作，全新 session）
- 日期：2026-11-11

## 结论：需修改

250 条 facts 中支撑 242 条、不支撑 5 条、存疑 3 条。问题集中在三处系统性毛病：

1. **“其余字段”式穷尽表述写错两次**（事实 16、162）——所列字段之外还有未提及的字段；
2. **字段名抄错 / 条件抄反**（事实 30、53）——`operations` 写成 `operation`、空列表不报错写成报错；
3. **序号 off-by-one**（事实 185）——0-based 下标被写成 1-based“第 N 段”。

另有 3 条存疑（事实 118、153、163）与若干正文结构问题（重复行、错位行、frontmatter 平台缺两项）。均属局部修改，不构成打回重写。

## 核查方法

- lint：`python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-02`，硬失败 0、警告 0（全批 10 页）。
- 机械核查：250 条 facts 的引用文件存在、行号在范围内、断言符号名出现在引用行 ±5 行内，0 条异常。
- 逐条实质核查：250 条分三路并行复核，每条对照引用行 ±7 行源码窗口；凡判定不支撑/存疑的，均由评审人用 `sed`/`muse.read` 亲眼复核源码原文后再定（下文“代码实际”均为亲眼所见的行内容）。
- 正文核查：正文 292 处引用全部落在 facts 覆盖内，250 条 facts 在正文中均至少被引用一次；无禁用词；结构为概述 / AI 速览 / 核心机制 / 关键符号 / 调用链 / 来源，符合 SCHEMA §9.2。

## 不支撑的事实（5 条，facts 与正文须同步改）

### 事实 16 — “其余字段”不成立

- 原文：`capabilities、structuredCapabilities、onboardingRequirements、workspaceRoots 是环境描述符的其余字段。`（`core/crates/foundation/host-api/src/lib.rs:109`）
- 代码实际：`HostEnvironmentDescriptor`（`lib.rs:96-112`）共 15 个字段。事实 15 列出 5 个（id、displayName、platform、privilege、isolation），事实 16 列出 4 个，之外还有 6 个字段未被提及：`pathStyleDescriptionEn:102`、`pathStyleDescriptionCn:103`、`examplePaths:104`、`usesEnvironmentParameter:105`、`environmentParameterDescriptionEn:106`、`environmentParameterDescriptionCn:107`。
- 怎么改：去掉“其余”二字，改为“capabilities、structuredCapabilities、onboardingRequirements、workspaceRoots 也是环境描述符的字段”；或补齐上述 6 个字段后再称“其余字段”。
- 正文同错：正文第 206 行同一句话须同步改。

### 事实 30 — 字段名抄错，`operation` 字段不存在

- 原文：`HostCapability 的字段包括 id、scope、operation。`（`core/crates/foundation/host-api/src/lib.rs:525`）
- 代码实际：`lib.rs:525-530`，`HostCapability` 的字段为 `pub id: String`、`pub displayName: String`、`pub scope: CapabilityScope`、`pub operations: Vec<CapabilityOperation>`。字段名是复数 `operations`，不存在名为 `operation` 的字段；同时漏了 `displayName`。
- 怎么改：改为“HostCapability 的字段包括 id、displayName、scope、operations（`Vec<CapabilityOperation>`）”。
- 正文同错：正文第 220 行同一句话须同步改。另注意 AI 速览“HostCapability — 能力 id、范围与操作”只是概念 gloss，不算错，不必改。

### 事实 53 — 条件抄反：空列表不报错

- 原文：`文件保存请求的校验在 extensions 为空时报错。`（`core/crates/foundation/host-api/src/lib.rs:1326`）
- 代码实际：`lib.rs:1325-1326`，条件为 `request.options.extensions.iter().any(|extension| extension.is_empty() || !extension.chars().all(|value| value.is_ascii_alphanumeric()))`。空列表上 `.any()` 为 false，不报错；报错的是任一 extension token 为空串或含非字母数字字符时。
- 怎么改：改为“文件保存请求的校验在任一 extensions token 为空串或含非字母数字字符时报错；extensions 为空列表时不报错”。
- 正文同错：正文第 239 行同一句话须同步改。

### 事实 162 — “其余字段”不成立

- 原文：`provider、modelName、inputTokens、outputTokens、cachedInputTokens 是消息的其余字段。`（`core/crates/foundation/model/src/ChatMessage.rs:22`）
- 代码实际：`ChatMessage` 共 21 个字段（`ChatMessage.rs:13-36`）。事实 161 的 5 个字段与事实 162 的 5 个字段之间还漏了 `selectedVariantIndex:19`、`variantCount:20`；`cachedInputTokens:25` 之后仍有 9 个字段：`sentAt:26`、`outputDurationMs:27`、`waitDurationMs:28`、`completedAt:29`、`completedExecutionGeneration:31`、`displayMode:32`、`isFavorite:33`、`isVariantPreview:35`、`contentStream:36`。
- 怎么改：删“其余”二字，改为“provider、modelName、inputTokens、outputTokens、cachedInputTokens 是消息的提供方与 token 计数字段”；或补全全部剩余字段。
- 正文同错：正文第 105 行同一句话须同步改。

### 事实 185 — 序号 off-by-one：下标 17 是第 18 段，下标 5 是第 6 段

- 原文：`list_models 操作的 requiresApiKey 在行内第 17 段，balance 操作的在第 5 段。`（`core/crates/foundation/model/src/ModelCatalog.rs:281`）
- 代码实际：`requiresApiKeyPartIndex` 返回 0-based 下标（`ModelCatalog.rs:281-287`：`"list_models" => 17, "balance" => 5`），调用处用 `parts.get(index)` 取值（同文件 `:316-325`）；操作串按冒号切分。实际目录行：`list_models:GET:/v1/models:$.data:$.id:::::::::::::true`（同文件 `:23`，OPENAI_RESPONSES_GENERIC 行）共 18 段，`true` 是第 18 段（下标 17）；`balance:GET:/user/balance:$.balance_infos[0].total_balance:$.balance_infos[0].currency:true`（同文件 `:40`，DEEPSEEK 行）共 6 段，`true` 是第 6 段（下标 5）。按中文常规“第 N 段”（1-based 计数），两处都差一段。
- 怎么改：改为“list_models 操作的 requiresApiKey 在操作串冒号切分后的索引 17（第 18 段），balance 操作的在索引 5（第 6 段）”；若本页约定“第 N 段”即指 0-based 下标，应在页内明说，否则读者按行文本数段会数错。
- 正文同错：正文第 131 行同一句话须同步改。

## 存疑的事实（3 条）

### 事实 118 — “识别屏幕文本”超出签名证据

- 原文：`captureScreenshot 与 recognizeText 分别截屏与识别屏幕文本。`（`core/crates/foundation/host-api/src/lib.rs:3284`）
- 代码实际：`recognizeText(&self, imagePath: &str, language: OCRLanguage, quality: OCRQuality) -> HostResult<String>`（同文件 `:3285-3290`），该方法无文档注释；入参是任意图片路径而非屏幕，是图片 OCR，不是“屏幕文本”本身。`captureScreenshot` 部分无误（同文件 `:3284`）。
- 怎么改：改为“captureScreenshot 截屏；recognizeText 对指定图片路径做 OCR 识别文本”。
- 正文同错：正文第 304 行同一句话须同步改。

### 事实 153 — “均为”不成立：结构体另有 2 个例外字段

- 原文：`HostManager 的宿主能力字段均为 Option<Arc<dyn 对应 Host trait>> 类型。`（`core/crates/foundation/host-api/src/HostManager.rs:140`）
- 代码实际：`HostManager` 结构体（`:139-176`）中 34 个宿主能力字段确为 `Option<Arc<dyn …Host>>`，但同结构体另有 `hostEnvironment: HostEnvironmentDescriptor`（`:174`，非 Option）与 `coreCommandExecutor: Option<CoreCommandExecutor>`（`:175`，`CoreCommandExecutor` 是 `Arc<dyn Fn…>` 回调别名，非 Host trait）。按“全部字段”读则不成立。
- 怎么改：限定范围，改为“34 个宿主能力字段均为 Option<Arc<dyn 对应 Host trait>>；hostEnvironment 与 coreCommandExecutor 除外”。
- 正文同错：正文第 92 行同一句话须同步改。

### 事实 163 — 时间字段分组不完整

- 原文：`sentAt、outputDurationMs、waitDurationMs、completedAt 是消息的时间相关字段。`（`core/crates/foundation/model/src/ChatMessage.rs:27`）
- 代码实际：所列 4 个字段确实存在（`:26-29`），但 `timestamp: i64`（`:16`）同样是时间字段，未被涵盖。本句字面未称“全部”，但与事实 161/162 的字段分组连读时会被读作穷尽式分组。
- 怎么改：改为“sentAt、outputDurationMs、waitDurationMs、completedAt 是发送/耗时/完成时间字段（另有 timestamp: i64）”，或去掉分组式表述。
- 正文同错：正文第 107 行同一句话须同步改。

## 正文结构问题（与事实问题分开计，均须改）

1. **重复行**：`HostManager 的 withServiceDiscoveryHost 等链式方法逐个安装宿主能力。` 在正文出现 3 次——第 99 行（HostManager 小节，正确）、第 103 行（**聊天消息**小节开头，错位重复，应删）、第 343 行（调用链第 2 步，合理复用，可保留）。
2. **错位行**：`displayMode 的默认值为 ChatMessageDisplayMode::NORMAL。` 在第 119 行，位于“模型目录”小节下；它是 `ChatMessage` 的字段，应移到“聊天消息”小节（第 101–116 行之间）。
3. **错位行**：`OPENAI_CODEX 的固定模型含 gpt-5.5、…。` 在第 331 行，位于“link 导出”小节下；它是 ModelCatalog 的事实，应移到“模型目录”小节或关键符号的 model 部分。
4. **frontmatter 平台缺两项**：`platforms: [android, ohos, windows, linux, web, esp32]`，但正文事实 25 明确 `HostPlatform` 有九个变体，含 Macos、Ios。host-api 定义了这两个平台变体，frontmatter 却未列出。建议补 `macos, ios`，或在页内说明本页未覆盖 macos/ios 宿主。
5. **调用链不是链**：`## 调用链` 第 1–13 步分别是 HostManager（1–6）、ModelCatalog（7–8）、Link（9–13）三组互不衔接的操作罗列，步骤之间没有数据流或调用关系。建议改为“关键操作序列”或按真实链路重组（例如 HostManager 组装 → ModelCatalog 查 provider → Link 发起调用三段），否则读者会误以为 13 步是同一条调用链。

## 非阻断建议（可随改动顺手修，不堵评审）

- 事实 179、181 的“不足 N 段报错”表述不完整：代码是 `parts.len() != 5 / != 15`（`ModelCatalog.rs:84`、`:154`），多于 N 段同样报错。“不足报错”本身为真，不列为问题；求严谨可补“多于 N 段同样报错”。
- 事实 176 的“只返回没有模型列表端点的 provider 的固定模型”在实现上并非靠端点检查，而是靠数据本身（固定模型行仅有 OPENAI_CODEX 的行，且其 provider 行无 `list_models` 操作），结论成立，不列为问题。

## 确认无误的要点

- lint 全批硬失败 0、警告 0；250 条 facts 引用文件存在、行号在范围内、符号名在引用行 ±5 行内，0 条异常。
- 正文 292 处引用全部落在 facts 覆盖内，250 条 facts 在正文中均至少被引用一次；无禁用词。
- 大纲备注的警示已遵守：事实 7 明确 contracts crate“当前基线目录下没有该 crate”，`core/crates/foundation/` 下实测只有 README.md、host-api、link、model、util，无 contracts 目录。
- 逐条复核确认无误的高风险点（抽样）：36 行 provider 目录行全部恰为 5 个竖线段、20 行固定模型行全部恰为 15 个竖线段；OPENAI_CODEX 六个模型 ID 均在固定模型行中真实存在；`fixedModels` 实际只对 OPENAI_CODEX 返回非空；HostManager 两类全局默认取回（返回 HostResult 错误 vs `expect` panic）的区分与代码一致；`ohosOnboardingRequirements()` 实际只返回 ohos.location 与 ohos.bluetooth 两项，与事实 42 的单测断言一致；`fromMappedReceiver` 全文件无 `spawn`，`withOnClose` 有对应的 `Drop` 实现；事实 51 的 Directory 报错分支确实嵌在 `maxContentBytes` 条件内。
- `core-foundation.quality.json` 的 3 条走查按 SCHEMA §8 不属于 critic 评审范围，未评审。
