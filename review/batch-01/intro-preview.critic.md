# Critic：intro-preview.md / intro-preview.facts.json

- 核查对象：`review/batch-01/intro-preview.md` 与 `intro-preview.facts.json`（41 条）
- 真理源：`~/workspace/Operit2`，基线 364d1d594，只读；未做 git 操作，未联网
- 方法：逐条核对 ref 文件存在性、行号范围、ref 行 ±5 行内容与断言的语义一致性；另核查正文超出 facts 的断言、禁用词、单平台写成全平台问题
- 目录核实：`docs/release-notes/` 下确为 2 个文件（`2.0.0-preview.22-build28.md`、`2.0.0-preview.27-build33.md`）；`release-versioning.md` 全文 446 行已通读，无支持期限/EOL 相关表述

## 逐条结论（41 条）

- F01 | 当前处于 Preview Release 阶段 | README.md:4 | 支撑（第 4 行为 `Preview Release` 徽标行）
- F02 | 预览阶段底层结构、数据格式、插件契约、跨设备工作流仍会 breaking | README.md:14 | 支撑（原文逐词对应）
- F03 | 能力各平台不完全相同，是否可执行取决于目标节点 Host 描述、系统权限、已装服务与当前用户批准 | README.md:39 | 支撑（原文逐词对应）
- F04 | 不得用默认开发 token 对公网监听 | README.md:53 | 支撑（原文：`Do not listen on the public internet with the default development token`）
- F05 | 插件开发入口接口（Rust SDK、TypeScript 声明、codegen）仍在演进 | README.md:64 | 支撑（原文：`these interfaces are still evolving`）
- F06 | 运行时、Host 能力、权限、兼容版本与状态作用域声明将继续细化；跨设备可移植性仍是主要开发重点；插件及依赖须在目标平台验证 | README.md:66 | 支撑（原文逐句对应）
- F07 | Server 是未来的部署形态与 Host 方向，当前仓库没有可直接发布的完整 Server 产品 | README.md:103 | 支撑（原文表格行逐词对应）
- F08 | 仓库包含多平台 Host 适配路径，但能构建不等于跨设备互操作已验证 | README.md:105 | 支撑（原文逐词对应）
- F09 | 当前焦点是个人设备空间；数千节点调度未验证；企业组织治理不是产品目标；Rust 本身不保证无资源泄漏 | README.md:148 | 支撑（原文四分句逐一对应）
- F10 | 标记为 target、plan 或 direction of evolution 的架构文档不代表所有平台已实现；以源码、命令帮助输出、构建结果与目标平台运行时结果为准 | README.md:246 | 支撑（原文逐词对应）
- F11 | 版本格式兼容 SemVer：stable 2.0.0、preview 2.0.0-preview.1、rc 2.0.0-rc.1、dev 2.0.0-dev.20260619 | docs/release-versioning.md:10 | 支撑（第 10 行起的代码块四行逐一对应，ref 指块首行）
- F12 | Git tag 用同一版本加前缀 v，如 v2.0.0-preview.1 | docs/release-versioning.md:19 | 支撑（第 19 行为 `v2.0.0-preview.1`）
- F13 | Build metadata 允许存在且不改变更新顺序 | docs/release-versioning.md:24 | 支撑（原文逐词对应）
- F14 | 不得把 build metadata 用作发布计数器；公开 preview 构建用 prerelease 标识 | docs/release-versioning.md:30 | 支撑（原文逐词对应）
- F15 | 版本排序 dev < preview.1 < preview.2 < rc.1 < stable；同 major.minor.patch 下 stable 新于 prerelease | docs/release-versioning.md:37 | 支撑（第 37 行为排序链，第 39 行有 stable 新于 prerelease 的规则，在 ±5 行内）
- F16 | 更新通道由当前已装版本派生：stable 走 stable channel，prerelease 走 preview channel | docs/release-versioning.md:47 | 支撑（第 47–48 行逐一对应）
- F17 | Stable channel 只接受 stable releases；Preview channel 接受 prerelease 与 stable releases | docs/release-versioning.md:51 | 支撑（第 51、53 行逐一对应）
- F18 | Release tag 与 GitHub prerelease 标志必须一致：preview 与 rc 对应 true，stable 对应 false | docs/release-versioning.md:60 | 支撑（第 60–62 行逐一对应）
- F19 | Draft releases 被更新器忽略 | docs/release-versioning.md:65 | 支撑（原文逐词对应）
- F20 | 首次公开 preview 使用 v2.0.0-preview.1 | docs/release-versioning.md:69 | 支撑（第 69 行引言 + 第 71 行代码块）
- F21 | 首次 stable 发布使用 v2.0.0 | docs/release-versioning.md:75 | 支撑（第 75 行引言 + 第 77 行代码块）
- F22 | 发布包文件名格式 operit2-\<product\>-\<platform\>-\<architecture\>-\<release-version\>.\<extension\> | docs/release-versioning.md:87 | 支撑（原文逐词对应）
- F23 | 发布包不附带单独的 checksum 文件 | docs/release-versioning.md:113 | 支撑（原文逐词对应）
- F24 | 更新发现从最近 30 个 releases 懒加载，只在当前页无兼容包时加载更老页面 | docs/release-versioning.md:160 | 支撑（第 160–164 行逐句对应）
- F25 | 选中的版本只在新于已装版本时才提供，更新发现不降级已装应用 | docs/release-versioning.md:166 | 支撑（第 165–166 行逐词对应）
- F26 | 发布版本来源是两处 Cargo.toml 的 package.version，两值必须相同且不得含 build metadata；CLI 用其作 cliVersion，App 从 operit-runtime 暴露 coreVersion | docs/release-versioning.md:177 | 支撑（两处路径在第 173–174 行，规则在第 177 行，均在 ±5 行内）
- F27 | Flutter 平台版本与发布版本分离：pubspec.yaml 的 version 为 major.minor.patch+buildNumber | docs/release-versioning.md:182 | 支撑（原文逐词对应）
- F28 | Flutter major.minor.patch 必须与发布版本一致；buildNumber 只是 Android、Windows、Linux 与 macOS 构建的平台包元数据 | docs/release-versioning.md:191 | 支撑（原文逐词对应）
- F29 | App 与 full 构建成功后 buildNumber 加 1；CLI-only 构建不改 buildNumber | docs/release-versioning.md:193 | 支撑（原文逐词对应）
- F30 | 构建发布脚本是 tools/release/build_release.py | docs/release-versioning.md:209 | 支撑（第 209 行为该路径代码块行）
- F31 | publish_dist.py 只上传已 staged 在 tools/release/dist 的文件，不重新构建 | docs/release-versioning.md:239 | 支撑（第 239–240 行逐句对应；文件存在已核实）
- F32 | 更新器实现在 core/crates/foundation/util/src/GithubReleaseUtil.rs | docs/release-versioning.md:397 | 支撑（原文逐词对应；文件存在已核实）
- F33 | App/CLI 发布版本不控制 Core 或 Edge 的配对、路由与同步 | docs/release-versioning.md:444 | 支撑（原文逐词对应）
- F34 | release notes 之一是 2.0.0-preview.22 · Apple Build 28，对比基线为 Build 27 / 2.0.0-preview.21 | docs/release-notes/2.0.0-preview.22-build28.md:3 | 支撑（第 1 行为标题，第 3 行为对比基线行）
- F35 | preview.22 本次二进制提交为 72c6240b8abdb43235622c1c7891057783e6ef97，Apple 版本 2.0.0，Build 28 | docs/release-notes/2.0.0-preview.22-build28.md:4 | 支撑（原文逐词对应，提交哈希逐字核对一致）
- F36 | preview.22 的内容用于两端 TestFlight 的测试内容，不含 CI、测试维护及其他平台专属改动 | docs/release-notes/2.0.0-preview.22-build28.md:5 | 支撑（原文逐词对应）
- F37 | preview.22 附代码核对依据表，逐项列出变更对应的提交与文件 | docs/release-notes/2.0.0-preview.22-build28.md:79 | 支撑（第 79 行为“代码核对依据”标题，其后表格逐行列出提交与文件）
- F38 | release notes 之二是 Operit2 2.0.0-preview.27 · Apple build 33 | docs/release-notes/2.0.0-preview.27-build33.md:1 | 支撑（第 1 行为标题）
- F39 | preview.27 新增构建配置 OPERIT_ARM64_WASM，默认 OFF | docs/release-notes/2.0.0-preview.27-build33.md:4 | 支撑（原文逐词对应）
- F40 | preview.27 的 Wasm 关闭构建运行时 CTest 40/40 通过 | docs/release-notes/2.0.0-preview.27-build33.md:10 | 支撑（原文逐词对应）
- F41 | preview.27 声明上述结果不代表原始绘图脚本的完整耗时已得到验证 | docs/release-notes/2.0.0-preview.27-build33.md:15 | 支撑（原文逐词对应，文件共 15 行）

## 正文超出 facts 的断言核查

- M01 | 正文“主入口：`operit2 cli update check <version>`，检查是否有可用更新而不下载” | 支撑。`apps/cli/Cargo.toml` 的 `[[bin]]` 名确为 `operit2`；`docs/release-versioning.md:419` 给出 `cli update check` 命令及“Check whether a release is available without downloading”说明。但文档未将其定为“主入口”，该词为 writer 的定性措辞，建议改为中性表述（如“检查命令：”）。
- M02 | 正文调用链第 4 步“同页内选最高的、与产品、平台、架构与完整 tag 版本精确匹配的包”仅引 `:166` | 存疑（引用不全，非事实错误）。“同页内选最高”与“只在新于已装版本时提供”由 :160–166 支撑；但“与产品、平台、架构与完整 tag 版本精确匹配”出自 `docs/release-versioning.md:405`（Runtime Implementation 规则：`Match assets by exact product, platform, architecture, and full release tag version`），未被引用。建议该句补引 `:405`。
- M03 | 正文“`docs/release-notes/` 下只有两份文件”引 `preview.22:1`；“覆盖缺口：preview.21 与 preview.23–26 的 note 缺失”引 `preview.22:3` | 支撑（事实为真），但引用方式存疑。两个“只有/缺失”断言是目录级事实，单文件行号本身不能证明；经 `ls docs/release-notes/` 核实确为仅有的两份文件，缺口断言为真。建议在 facts.json 中补一条目录级事实（ref 为目录清单），或将 inline 引用改为指向目录核实记录。
- M04 | 正文“release-versioning.md 没有写明版本的支持期限；它只定义了通道与更新发现规则” | 支撑。全文 446 行已通读，无支持期限/EOL 相关表述；通道与更新发现规则确为该文档定义的全部机制。
- M05 | 正文“preview.27 只有 4 条改动加一节验证，没有对比基线行，没有双语分节” | 支撑。文件共 15 行：4 条改动 + 一节“验证”，无对比基线行，无 zh-Hans/en-US 双语分节。
- M06 | 正文“数据流向：已装版本 → 派生更新通道 → 更新发现按通道选出更新版本 → 下载安装” | 支撑。流程各环节均有文档依据（:47 通道派生、:160–166 更新发现、:425 下载、:431 完整更新路径），属忠实概括，无超出支撑的发挥。
- M07 | 正文 AI 速览与关键符号中的 `release_artifacts.py — 共享的发布包命名实现（:90）` | 存疑（路径缺失，非事实错误）。`docs/release-versioning.md:90` 原文给出的是 `tools/build_scripts/release_artifacts.py`，文件存在已核实；正文只写文件名不写路径，读者会在 `tools/release/` 下找不到该文件（该目录下无此文件）。建议补全路径为 `tools/build_scripts/release_artifacts.py`。
- M08 | 调用链第 5–7 步（`cli update check/download/run`，引 :419/:425/:431） | 支撑。各命令形式与“只检查不下载 / 下载不安装 / 完整更新路径含安装覆盖”的说明均与文档 Update Testing 节逐句对应。

## 禁用词与平台口径核查

- 禁用词：正文全文 grep `可能|大概|似乎|应该|也许`，0 命中。
- 平台口径：未发现把单平台实现写成全平台结论。版本号规则按全平台表述有文档依据；preview.22/preview.27 均明确标注为 Apple Build / TestFlight 内容，未泛化为全平台；`buildNumber` 的平台范围（Android、Windows、Linux、macOS）与文档一致，未把 iOS 包含在内；frontmatter `platforms: [all]` 与“能力是否可用按平台区分，见 intro-overview”的分工表述一致。

## 总结论：需修改

- 41 条 facts：41 条支撑，0 条不支撑，0 条存疑。
- 需修改项（均为正文引用/措辞精度问题，无事实错误，不必打回重写）：
  1. M07：`release_artifacts.py` 补全路径为 `tools/build_scripts/release_artifacts.py`（AI 速览与关键符号两处）。
  2. M02：调用链第 4 步“精确匹配”分句补引 `docs/release-versioning.md:405`。
  3. M03：“只有两份文件”与“覆盖缺口”两处断言，建议在 facts.json 中补一条目录级事实（`docs/release-notes/` 仅含 preview.22 与 preview.27 两份文件），或调整 inline 引用方式。
  4. M01：“主入口”改为中性表述（如“检查命令：”），文档未将其定为主入口。
- 修改完成后无需重新全文核查，只需确认上述 4 处改动。
