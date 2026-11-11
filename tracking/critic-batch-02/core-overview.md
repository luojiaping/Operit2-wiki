# Critic 结论：core-overview（Core 总览与 crate 边界）

- 页：`review/batch-02/core-overview.md`（224 行）+ `review/batch-02/core-overview.facts.json`（101 条）
- 评审 Issue：#12
- 基线：`AAswordman/Operit2 @ 364d1d594`（本地 `~/workspace/Operit2`，只读核对）
- 批评时间：2026-11-11
- **结论：需修改**

## 结论说明

101 条 facts 中 100 条支撑、1 条不支撑；正文另有 2 处措辞问题。问题都小、都局部，不需要打回重写。改完 3 处（第 52 条事实 + 正文 85 行、第 4 步调用链 185 行、"四处不一致"小节标题）后可进入评审。

核查方法：101 条 facts 的 ref 全部机械核验（文件存在 + 行号在范围内）0 坏；逐条取 ref 行 ±7 行窗口与断言对照；29 个 workspace 成员、15 个未列入项、38 个 sources、7 个 schemaRoots、15 个 revisions 全部用脚本独立重算；每份 Cargo.toml 的完整 `[dependencies]` operit-* 列表逐个提取，与正文枚举逐项比对；lint 全批（batch-02 共 10 页）硬失败 0、警告 0；正文无禁用词。

## 逐条判定（101 条）

- [0]–[14]：支撑。29 个 members 独立计数确认；11 个一级目录（除 README.md 文件外 11 个子目录）确认；resolver 2、edition 2021、license MIT、publish false 均在 `core/Cargo.toml:33–38`。
- [15]：支撑。29 个成员路径在磁盘上各有 `Cargo.toml` 与 `src` 目录，脚本逐个核对无缺失。
- [16]：支撑。缺 `README.md` 的恰是所列 5 个目录（`node/peer-link`、`persistence/rescue`、`plugin/sdk-ipc`、`plugin/sdk-ipc-bridge`、`plugin/sdk-macros`），其余 24 个成员目录都有。
- [17]–[32]：支撑。16 个 crate 定义逐字对照 `CRATE_BOUNDARIES.md` 第 9–57 行原文。
- [33][34]：支撑。包名在各自 `Cargo.toml:2`；不在 core 工作区内由 members 清单（无 `edge/` 路径）核实。
- [35]：支撑。`CRATE_BOUNDARIES.md` Crates 一节共 16 项，其中 14 项是 core 工作区成员；29 − 14 = 15，所列 15 个名字与集合差逐个核对无误。
- [36][37]：支撑。依赖方向与"runtime 可依赖全部子 crate、子 crate 不得依赖 operit-runtime"均为文档 :63/:66 原文。
- [38]–[40]：支撑。各 `[dependencies]` 的 operit-* 列表与断言逐项一致（store 的 model 是可选，见 `:24`）。
- [41]：支撑。`plugin-sdk` 的 `[dependencies]` 确有 4 个内部 crate（`:13` sdk-macros、`:14` theme、`:18` host-api、`:19` util）；文档 :74 原文"depends only on public ecosystem crates"已核对。
- [42]：支撑。`plugin-theme` 的 `[dependencies]` 无 operit-* 依赖。
- [43]：支撑。`operit-tools` 的 9 个内部依赖与断言逐项一致；`[dev-dependencies]` 另有 `operit-js-bridge`，不在本事实断言范围内。
- [44][45][46]：支撑。local-model（host-api、util）、providers（7 个）、js-bridge（4 个）与完整 `[dependencies]` 一致，且均无 `operit-runtime`。
- [47][48][49]：支撑。三条合起来覆盖 `operit-runtime` 的全部 14 个 `[dependencies]`（8 + 4 + js-bridge 可选 + edge-contract），无遗漏。
- [50]：支撑。`operit-runtime` 的 `[dependencies]` 中确实没有所列 15 个；文档 :88 原文"depends on all child crates"已核对。
- [51]：支撑。`node/runtime/Cargo.toml:35` 确为 `operit-runtime = { path = "../../runtime/application", default-features = false, features = ["javascript"], optional = true }`，与文档 :66 规则冲突。
- **[52]：不支撑（见问题 1）。**
- [53][54][55]：支撑。三条合起来覆盖 `operit-proxy-local` 的全部 17 个主 `[dependencies]`，无遗漏。
- [56][57]：支撑。command-core 8 个、core-application 10 个，与完整 `[dependencies]` 一致。
- [58][59][60]：支撑。edge-node 4 个、edge-proxy 3 个、edge-contract 1 个，与完整 `[dependencies]` 一致。
- [61][62]：支撑。`edge/sdk/node/Cargo.toml:10` 确依赖 `operit-node-runtime`；文档 :90–91、:92 原文已核对，确实未列出。
- [63]–[75]：支撑。`ToolRuntimeSupport`（:417）、`ProviderRuntimeSupport`（:281）、`LocalModelRuntimeSupport`（:7）、`GitHubTokenSource`（:512）、`JsExecutionHost`（:213）、`JsExecutionProvider`（:435）、`JsPackageExecutor`（:426）、`JsExecutionEngine`（:653）的 trait 定义行，以及 `RuntimeToolSupport`（:137）、`RuntimeProviderSupport`（:443）、`AIToolHandler`（:1224）、`HostJsExecutionProvider`（:91）的实现行，逐行核对无误。
- [76]：支撑。实现结构体是 `HostJsExecutionProvider`（`:16`），文档 :128 写到的 `QuickJsExecutionProvider` 已核对原文；该名字在 js-bridge 源码中无命中。
- [77]：支撑。`HostManager` 结构体在 `:139`；"活动宿主能力集与面向生命周期的宿主句柄"与 `CRATE_BOUNDARIES.md:140–141` 原文一致。
- [78]–[83]：支撑。六条边界归属逐字对照文档 :140、:150、:157、:163、:171、:181 原文。
- [84]–[87]：支撑。`sources` 38 个、revisions 15 个（version 1–15）、最新 v15 hash `6e1cd345…952e80d`、schemaRoots 7 个，全部独立重算确认。
- [88]–[95]：支撑。八条协议版本/指纹断言逐字对照 `docs/peer-protocol-versioning.md` 第 3–53 行原文。
- [96]：支撑。38 个 sources 按路径分组确为 core 的 Link（1）、节点（21）、持久化（10）、运行时（2）、rslink（1）与 edge 的 contract、node、proxy 各 1。
- [97]：支撑。38 个 sources 路径与 7 个 schemaRoots 在基线磁盘上全部存在。
- [98][99][100]：支撑。逐字对照文档 :19、:28、:39–40 原文。

## 正文核查

- 结构：frontmatter 齐全（title、module core、platforms [all]、sources [32]、date）；六节齐全且顺序符合 SCHEMA §9.2（概述 / AI 速览 / 核心机制 / 关键符号 / 调用链 / 来源），AI 速览为固定第二小节。
- 引用：lint 全批硬失败 0、警告 0；正文全部 `(file:line)` 引用均落在 facts 覆盖内，符号在 ref 行 ±5 行内。
- 禁用词：无（可能/大概/似乎/应该/也许 0 命中）。
- 来源：`## 来源` 列出 32 个文件，与 frontmatter `sources: [32]` 一致，32 个文件在基线磁盘上全部存在。
- 条目间链接：`[[arch-overview|架构总览]]`、`[[arch-corenode|CoreNode]]`、`[[arch-sync|多设备同步]]` 三个目标页均存在于 batch-01。
- 关键符号小节：`operit-node-runtime`（`core/Cargo.toml:21`）、`operit-peer-link`（`:22`）、`operit-data-rescue`（`:8`）、`operit-core-application`（`application/core/Cargo.toml:2`，包名行）行号逐个核对无误。

## 问题 1（事实错误）：第 52 条事实与正文 85 行漏了 `operit-runtime` 可选依赖

- 事实原文（[52]，`core/crates/node/runtime/Cargo.toml:33`）：
  > operit-node-runtime 依赖 operit-peer-link、operit-host-api、operit-link，以及可选的 operit-rslink-runtime、operit-store、operit-tools、operit-util。
- 正文 85 行同样写法：
  > `operit-node-runtime` 依赖 `operit-peer-link`、`operit-host-api`、`operit-link`，以及可选的 `operit-rslink-runtime`、`operit-store`、`operit-tools`、`operit-util`（`core/crates/node/runtime/Cargo.toml:33`）
- 代码实际内容：`core/crates/node/runtime/Cargo.toml` 的 `[dependencies]` 中 operit-* 依赖共 8 个——`operit-peer-link`（:28）、`operit-host-api`（:32）、`operit-link`（:33）、`operit-rslink-runtime`（:34，可选）、`operit-runtime`（:35，可选，`features = ["javascript"]`）、`operit-store`（:36，可选）、`operit-tools`（:37，可选）、`operit-util`（:38，可选）。第 52 条漏了 `operit-runtime`。
- 为什么严重：这正是本页事实 [51] 揭出的文档规则冲突项（子 crate 不得依赖 operit-runtime）。单独检索第 52 条的 AI 会得出"node-runtime 不依赖 operit-runtime"的结论，与第 51 条直接冲突——batch-01 的同类教训（旧保证以独立事实保留）。
- 怎么改：事实 [52] 与正文 85 行都补上"以及可选的 operit-runtime（features 为 javascript）"。ref 可保持 `:33`（:35 在 ±5 行内），或改引 `:35`。改完后 facts 仍为 101 条。

## 问题 2（标题错误）："文档与实现的四处不一致"实际是六处

- 正文小节标题（核心机制第三节）：
  > ### 文档与实现的四处不一致（以 Cargo.toml 为准）
- 实际内容：该小节共 7 条——6 条不一致（plugin-sdk :74、runtime :88、node-runtime 可选 runtime、node-edge :90–91、proxy-edge :92、QuickJs :126–128）+ 1 条一致确认（plugin-theme 的 `[dependencies]` 只有公开生态 crate，文档该句与实现一致）。
- 怎么改：标题改为"### 文档与实现的六处不一致（以 Cargo.toml 为准）"，并把第 7 条（plugin-theme 一致）移出该小节（例如并入上一节末尾），或在该条行首注明"一致对照"。只改标题不移条目也可以接受，但"六处"标题下挂一条"一致"仍别扭，建议二选一。

## 问题 3（措辞存疑）：调用链第 4 步的无条件断言与 [51] 的例外冲突

- 正文 185 行：
  > 4. 子 crate 通过 trait 对象调用父级服务，子 crate 不直接依赖 `operit-runtime` 的内部实现（`core/CRATE_BOUNDARIES.md:98`）
- 代码实际内容：`:98` 只讲 trait 机制（子 crate 定义 trait、消费 trait 对象，父级实现并安装）；"子 crate 不直接依赖 operit-runtime 的内部实现"这个全称判断在 :98 ±5 行内无依据，且与事实 [51] 的例外（node-runtime 以可选依赖引用 operit-runtime）相抵触。
- 怎么改：限定范围，例如改为"按 trait 机制，子 crate 通过 trait 对象调用父级服务，不直接依赖 `operit-runtime` 的内部实现（`operit-node-runtime` 的 javascript 可选依赖除外，见不一致小节）"，或把引用改为 `:66`（文档规则）与 `:98` 并列。措辞小修，不涉及 facts。

## 可选建议（非必需）

- `operit-proxy-local` 在非 wasm32 目标上还有一个 `operit-command-core` 依赖（`core/crates/proxy/local/Cargo.toml` 的 `target.cfg(not(target_arch = "wasm32"))` 一节）。事实 [53]–[55] 只覆盖主 `[dependencies]` 表的 17 个，本身无错；如追求穷尽，可在正文依赖一节加一句说明。

## 附注

- `core-overview.quality.json` 的 7 条走查发现（plugin-sdk :74、QuickJs :128、runtime :88、node-runtime :66、node-edge :90、proxy-edge :92、5 个缺 README）与本页"不一致"小节内容一一对应，均已核实属实；按 SCHEMA §8，quality.json 不在 critic 评审范围内，此处仅作一致性注记。
- 本批评只读了本页 .md、.facts.json 与 facts 引用的源码行，未改任何 review 文件，未提交推送，未发 Issue 留言。
