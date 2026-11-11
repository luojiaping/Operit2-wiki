---
title: 预览版与破坏性变更
module: intro
platforms: [all]
sources: [README.md, docs/release-versioning.md, docs/release-notes/2.0.0-preview.22-build28.md, docs/release-notes/2.0.0-preview.27-build33.md, apps/cli/src/cli/mod.rs]
date: 2026-11-11
---

# 预览版与破坏性变更

## 概述

Operit2 当前处于 `Preview Release` 阶段（`README.md:4`）。

预览阶段，底层结构（`underlying structure`）、数据格式（`data formats`）、插件契约（`plugin contracts`）与跨设备工作流（`cross-device workflows`）尚未冻结（`README.md:14`）。

本页回答大纲的四个问题：预览阶段哪些东西会发生 breaking 变更、版本号规则是什么、现有 release notes 覆盖到哪个版本、用户如何判断自己用的版本是否受支持。版本号规则适用于全部平台；能力是否可用按平台区分，见 [[intro-overview|Operit2 是什么]]。

## AI 速览

- `2.0.0-preview.1` — 第一个公开 preview 的版本号（`docs/release-versioning.md:69`）
- `v2.0.0-preview.1` — 对应的 Git tag（`docs/release-versioning.md:19`）
- `cliVersion` — CLI 暴露的 Cargo package version（`docs/release-versioning.md:177`）
- `coreVersion` — App 从 operit-runtime 暴露的版本（`docs/release-versioning.md:177`）
- `buildNumber` — Flutter 平台包元数据，App/full 构建成功后加 1（`docs/release-versioning.md:193`）
- `OPERIT_ARM64_WASM` — preview.27 新增的构建配置，默认 OFF（`docs/release-notes/2.0.0-preview.27-build33.md:4`）
- `GithubReleaseUtil.rs` — 更新器的实现文件（`docs/release-versioning.md:397`）
- `build_release.py` — 构建发布脚本（`docs/release-versioning.md:209`）
- `publish_dist.py` — 发布已 staged 文件的脚本（`docs/release-versioning.md:239`）
- `tools/build_scripts/release_artifacts.py` — 共享的发布包命名实现（`docs/release-versioning.md:90`）

检查命令：`operit2 cli update check`，无参数时自动用 `CARGO_PKG_VERSION` 作当前版本（`apps/cli/src/cli/mod.rs:531`）。

带参形式：`operit2 cli update check <current-version>`，显式参数名为 `current_version`，覆盖版本比较基准（`apps/cli/src/cli/mod.rs:559`）。

只检查不下载：`cli update check` 只检查是否有可用更新，不下载（`docs/release-versioning.md:419`）。

数据流向：已装版本 → 派生更新通道 → 更新发现按通道选出更新版本 → 下载安装（`docs/release-versioning.md:47`）。

## 核心机制

### 预览阶段意味着什么

插件开发入口接口（Rust SDK、TypeScript 声明、`codegen`）仍在演进（`README.md:64`）。

运行时、Host 能力、权限、兼容版本与状态作用域声明将继续细化；跨设备可移植性仍是主要开发重点，插件及依赖须在目标平台验证（`README.md:66`）。

Server 是未来的部署形态与 Host 方向，当前仓库没有可直接发布的完整 Server 产品（`README.md:103`）。

仓库包含多平台 Host 适配路径，但能构建不等于跨设备互操作已验证（`README.md:105`）。

当前焦点是个人设备空间；数千节点调度未验证，企业组织治理不是产品目标；Rust 本身不保证无资源泄漏（`README.md:148`）。

标记为 target、plan 或 direction of evolution 的架构文档不代表所有平台已实现；以源码、命令帮助输出、构建结果与目标平台运行时结果为准（`README.md:246`）。

能力在各平台不完全相同：是否可执行取决于目标节点的 Host 描述、系统权限、已装服务与当前用户批准（`README.md:39`）。

### 版本号规则

版本格式兼容 `SemVer`：stable 为 `2.0.0`、preview 为 `2.0.0-preview.1`、rc 为 `2.0.0-rc.1`、dev 为 `2.0.0-dev.20260619`（`docs/release-versioning.md:10`）。

Git tag 使用同一版本加前缀 `v`，例如 `v2.0.0-preview.1`（`docs/release-versioning.md:19`）。

Build metadata 允许存在且不改变更新顺序（`docs/release-versioning.md:24`）。

不得把 build metadata 用作发布计数器；公开 preview 构建用 prerelease 标识（`docs/release-versioning.md:30`）。

版本排序为 `2.0.0-dev.20260619` < `2.0.0-preview.1` < `2.0.0-preview.2` < `2.0.0-rc.1` < `2.0.0`；同 `major.minor.patch` 下 stable 新于 prerelease（`docs/release-versioning.md:37`）。

更新通道由当前已装版本派生：stable 版本走 `stable channel`，prerelease 版本走 `preview channel`（`docs/release-versioning.md:47`）。

`stable channel` 只接受 stable GitHub releases；`preview channel` 接受 prerelease 与 stable GitHub releases（`docs/release-versioning.md:51`）。

Release tag 与 GitHub `prerelease` 标志必须一致：preview 与 rc 对应 `true`，stable 对应 `false`（`docs/release-versioning.md:60`）。

`Draft` releases 被更新器忽略（`docs/release-versioning.md:65`）。

首次公开 preview 使用 `v2.0.0-preview.1`（`docs/release-versioning.md:69`）。

首次 stable 发布使用 `v2.0.0`（`docs/release-versioning.md:75`）。

发布包文件名格式为 `operit2-<product>-<platform>-<architecture>-<release-version>.<extension>`（`docs/release-versioning.md:87`）。

发布包不附带单独的 `checksum` 文件（`docs/release-versioning.md:113`）。

### 版本来源

发布版本来源是 `apps/cli/Cargo.toml` 与 `core/crates/runtime/application/Cargo.toml` 的 `package.version`，两值必须相同且不得含 build metadata；CLI 用该值作 `cliVersion`，App 从 `operit-runtime` 暴露 `coreVersion`（`docs/release-versioning.md:177`）。

Flutter 平台版本与发布版本分离：`apps/flutter/app/pubspec.yaml` 的 `version` 为 `major.minor.patch+buildNumber`（`docs/release-versioning.md:182`）。

Flutter 的 `major.minor.patch` 必须与 Operit2 发布版本一致；`buildNumber` 只是 Android、Windows、Linux 与 macOS 构建的平台包元数据（`docs/release-versioning.md:191`）。

App 与 full 构建成功后 `buildNumber` 加 1；CLI-only 构建不改 `buildNumber`（`docs/release-versioning.md:193`）。

### 更新发现与更新器

更新发现从最近 30 个 releases 懒加载；只在当前页无兼容包时加载更老页面（`docs/release-versioning.md:160`）。

选中的版本只在新于已装版本时才提供；更新发现不降级已装应用（`docs/release-versioning.md:166`）。

更新器实现在 `core/crates/foundation/util/src/GithubReleaseUtil.rs`（`docs/release-versioning.md:397`）。

App/CLI 发布版本不控制 Core 或 Edge 的配对、路由与同步（`docs/release-versioning.md:444`）。

### 发布流程

构建发布脚本是 `tools/release/build_release.py`（`docs/release-versioning.md:209`）。

`publish_dist.py` 只上传已 staged 在 `tools/release/dist` 的文件，不重新构建（`docs/release-versioning.md:239`）。

### release notes 的实际覆盖

`docs/release-notes/` 下只有两份文件：`2.0.0-preview.22` 与 `2.0.0-preview.27`（`docs/release-notes/2.0.0-preview.22-build28.md:1`）。

preview.22 对比基线是 Build 27 / `2.0.0-preview.21`，本次二进制提交为 `72c6240b8abdb43235622c1c7891057783e6ef97`，Apple 版本 `2.0.0`，Build `28`（`docs/release-notes/2.0.0-preview.22-build28.md:4`）。

preview.22 的内容用于两端 `TestFlight` 的测试内容，不含 CI、测试维护及其他平台专属改动（`docs/release-notes/2.0.0-preview.22-build28.md:5`）。

preview.22 附代码核对依据表，逐项列出变更对应的提交与文件（`docs/release-notes/2.0.0-preview.22-build28.md:79`）。

preview.27 只有 4 条改动加一节验证，没有对比基线行，没有双语分节（`docs/release-notes/2.0.0-preview.27-build33.md:1`）。

preview.27 新增构建配置 `OPERIT_ARM64_WASM`，默认 `OFF`（`docs/release-notes/2.0.0-preview.27-build33.md:4`）。

preview.27 的 Wasm 关闭构建运行时 `CTest` 40/40 通过（`docs/release-notes/2.0.0-preview.27-build33.md:10`）。

preview.27 声明上述结果不代表原始绘图脚本的完整耗时已得到验证（`docs/release-notes/2.0.0-preview.27-build33.md:15`）。

覆盖缺口：preview.22 的对比基线提到的 `2.0.0-preview.21` 在 docs/release-notes/ 下没有对应的 note；preview.23 至 preview.26 的 note 同样缺失（`docs/release-notes/2.0.0-preview.22-build28.md:3`）。

### 用户如何判断版本是否受支持

release-versioning.md 没有写明版本的支持期限；它只定义了通道与更新发现规则（`docs/release-versioning.md:47`）。

用户可核对的三件事：当前已装版本派生的通道（`docs/release-versioning.md:47`）；更新发现只提供新于已装版本的包、不降级（`docs/release-versioning.md:166`）；App/CLI 发布版本不控制 Core 或 Edge 的配对、路由与同步，协议兼容另见 peer-protocol-versioning.md（`docs/release-versioning.md:444`）。

## 关键符号

- `2.0.0-preview.1` — 第一个公开 preview 的版本号（`docs/release-versioning.md:69`）
- `v2.0.0-preview.1` — 对应的 Git tag（`docs/release-versioning.md:19`）
- `cliVersion` — CLI 暴露的 Cargo package version（`docs/release-versioning.md:177`）
- `coreVersion` — App 从 operit-runtime 暴露的版本（`docs/release-versioning.md:177`）
- `buildNumber` — Flutter 平台包元数据（`docs/release-versioning.md:191`）
- `OPERIT_ARM64_WASM` — preview.27 新增的构建配置，默认 OFF（`docs/release-notes/2.0.0-preview.27-build33.md:4`）
- `GithubReleaseUtil.rs` — 更新器的实现文件（`docs/release-versioning.md:397`）
- `build_release.py` — 构建发布脚本（`docs/release-versioning.md:209`）
- `publish_dist.py` — 发布已 staged 文件的脚本（`docs/release-versioning.md:239`）
- `tools/build_scripts/release_artifacts.py` — 共享的发布包命名实现（`docs/release-versioning.md:90`）

## 调用链

1. 读取已装版本：CLI 取 `apps/cli/Cargo.toml` 的 `package.version` 作 `cliVersion`；App 取 `operit-runtime` 暴露的 `coreVersion`（`docs/release-versioning.md:177`）。
2. 派生更新通道：stable 版本走 `stable channel`，prerelease 版本走 `preview channel`（`docs/release-versioning.md:47`）。
3. 更新发现：从最近 30 个 releases 懒加载，按通道筛选，只在当前页无兼容包时加载更老页面（`docs/release-versioning.md:160`）。
4. 选出更新版本：同页内选最高的、与产品、平台、架构与完整 tag 版本精确匹配的包；只在新于已装版本时才提供，不降级（`docs/release-versioning.md:166`；精确匹配规则见 `docs/release-versioning.md:405`）。
5. 检查可用更新：`cli update check` 只检查不下载（`docs/release-versioning.md:419`）。
6. 下载匹配资产：`cli update download` 下载匹配资产并显示进度而不安装（`docs/release-versioning.md:425`）。
7. 走完整更新路径：`cli update run` 含当前目标匹配时的安装覆盖（`docs/release-versioning.md:431`）。

发布侧调用链：`tools/release/build_release.py` 按 `--scope` 构建发布资产（`docs/release-versioning.md:209`）；资产 staged 到 `tools/release/dist` 后，`tools/release/publish_dist.py` 通过 GitHub REST API 上传，不重新构建（`docs/release-versioning.md:239`）。

## 来源

- README.md
- docs/release-versioning.md
- docs/release-notes/2.0.0-preview.22-build28.md
- docs/release-notes/2.0.0-preview.27-build33.md
- apps/cli/src/cli/mod.rs
