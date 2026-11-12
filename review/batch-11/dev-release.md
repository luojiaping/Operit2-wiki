---
title: 版本与发布
module: dev
platforms: [all]
sources: 3
date: 2026-11-11
---

## 概述

`docs/release-versioning.md` 是 Operit2 app 与 CLI 发布版本的事实来源。`docs/release-versioning.md:3`
本页回答版本号命名规则、release notes 的覆盖范围与发布流程由哪些 workflow 负责，发布脚本侧的细节见 [[tools-release|发布流程]]。
Operit2 使用与 SemVer 兼容的版本。`docs/release-versioning.md:7`

## AI 速览

- `docs/release-versioning.md` — 版本、tag、通道与包资产规则的事实来源。`docs/release-versioning.md:3`
- `tools/release/build_release.py` — 构建发布资产的主入口。`docs/release-versioning.md:209`
- `tools/release/publish_dist.py` — 上传已暂存于 `tools/release/dist` 的文件。`docs/release-versioning.md:239`
- `tools/release/download_action_artifacts.py` — 从成功的 run 收集发布资产进 `tools/release/dist`。`docs/release-versioning.md:314`
- `tools/build_scripts/release_artifacts.py` — 共享的发布包命名实现。`docs/release-versioning.md:90`
- `core/crates/foundation/util/src/GithubReleaseUtil.rs` — 更新器实现。`docs/release-versioning.md:397`
- `cliVersion` — CLI 以其 Cargo 包版本作为该值。`docs/release-versioning.md:177`
- `coreVersion` — App 从 `operit-runtime` 暴露该值。`docs/release-versioning.md:177`
- 主入口：`build_release.py`，`--scope` 接受 `cli`、`app`、`full`。`docs/release-versioning.md:233`
- 数据流向：Cargo 与 pubspec 版本 → `build_release.py` 校验与构建 → `tools/release/dist` 暂存资产 → `publish_dist.py` 上传到 GitHub Release → 更新器按通道与精确文件名发现更新。`docs/release-versioning.md:239`

## 核心机制

### 版本号命名规则

Operit2 的 stable 版本形式为 `2.0.0`。`docs/release-versioning.md:10`
Operit2 的 preview 版本形式为 `2.0.0-preview.1`。`docs/release-versioning.md:11`
Operit2 的 rc 版本形式为 `2.0.0-rc.1`。`docs/release-versioning.md:12`
Operit2 的 dev 版本形式为 `2.0.0-dev.20260619`。`docs/release-versioning.md:13`
Git tag 使用同一版本号并加前导 `v`，例如 `v2.0.0-preview.1`。`docs/release-versioning.md:19`
构建元数据被允许且不改变更新顺序，例如 `2.0.0+20260619.shaabcdef`。`docs/release-versioning.md:27`
不得把构建元数据用作发布计数器，公开预览构建使用 prerelease 标识符。`docs/release-versioning.md:30`
版本顺序为 `2.0.0-dev.20260619 < 2.0.0-preview.1 < 2.0.0-preview.2 < 2.0.0-rc.1 < 2.0.0`。`docs/release-versioning.md:37`
相同 major、minor、patch 的 stable 版本比 prerelease 版本更新。`docs/release-versioning.md:40`
首个公开 Operit2 预览版使用 `v2.0.0-preview.1`。`docs/release-versioning.md:72`
首个 stable Operit2 发布使用 `v2.0.0`。`docs/release-versioning.md:78`

### 更新通道与 GitHub Release

更新器通道由当前已安装版本推导：stable 版本走 stable channel，prerelease 版本走 preview channel。`docs/release-versioning.md:47`
stable channel 只接受 stable GitHub release。`docs/release-versioning.md:51`
preview channel 接受 prerelease 和 stable GitHub release。`docs/release-versioning.md:53`
发布 tag 与 GitHub prerelease 标志必须一致：`v2.0.0-preview.1` 对应 true，`v2.0.0-rc.1` 对应 true，`v2.0.0` 对应 false。`docs/release-versioning.md:60`
Draft release 被更新器忽略。`docs/release-versioning.md:65`
发布脚本从 tag 版本推导 GitHub prerelease 标志，prerelease tag 发布为 GitHub prerelease，stable tag 发布为 stable GitHub release。`docs/release-versioning.md:67`

### 包资产与 MSI（Windows）

全部发布包在扩展名之前紧跟完整发布版本（含 prerelease 标识符），命名模板为 `operit2-<product>-<platform>-<architecture>-<release-version>.<extension>`。`docs/release-versioning.md:87`
共享命名实现是 `tools/build_scripts/release_artifacts.py`。`docs/release-versioning.md:90`
Windows App 构建从同一 Flutter 发布目录产出便携 ZIP 与中文 MSI 安装器。`docs/release-versioning.md:116`
MSI 为当前用户安装到 `%LOCALAPPDATA%\Programs\Operit2`，创建桌面与开始菜单快捷方式，并在 Windows 设置中注册修复与卸载。`docs/release-versioning.md:118`
MSI 的三段版本号编码为 `major.minor.(patch * 1000 + revision)`。`docs/release-versioning.md:142`
MSI 的 revision 取值：dev 为 1–199，preview 为 201–399，rc 为 401–599，stable 为 999。`docs/release-versioning.md:143`
MSI 计数器超过 199、不支持的 prerelease 标识符与 MSI 字段溢出都会显式失败。`docs/release-versioning.md:144`
发布文件名中的版本与 Git tag 一致，但去掉前导 `v`。`docs/release-versioning.md:148`
更新器按每个 release 自身的 tag 与请求的 product、platform、architecture 构建精确文件名。`docs/release-versioning.md:149`

### 版本来源

发布版本的来源是 `apps/cli/Cargo.toml` 与 `core/crates/runtime/application/Cargo.toml` 的 `package.version`，两个值必须相同。`docs/release-versioning.md:173`
两个 Cargo 版本值不得包含构建元数据，CLI 以其 Cargo 包版本作为 `cliVersion`，App 从 `operit-runtime` 暴露 `coreVersion`。`docs/release-versioning.md:177`
Flutter 平台元数据与 Operit2 发布版本分离，`apps/flutter/app/pubspec.yaml` 的版本形式为 `major.minor.patch+buildNumber`。`docs/release-versioning.md:182`
`2.0.0-preview.1` 对应的 Flutter 平台版本为 `2.0.0+1`。`docs/release-versioning.md:188`
Flutter 的 `major.minor.patch` 必须与 Operit2 发布版本一致，`buildNumber` 只是 Android、Windows、Linux 与 macOS 构建的平台包元数据。`docs/release-versioning.md:191`
App 与 full 运行先用当前 Flutter `buildNumber` 构建，全部所选 App 资产成功后再把 `apps/flutter/app/pubspec.yaml` 的 `buildNumber` 加 1；CLI-only 运行不改变 Flutter `buildNumber`。`docs/release-versioning.md:193`
Android 的 `module.prop` 使用共享的完整发布版本，并以同一 Flutter `buildNumber` 作为 `versionCode`；两种 Android 形态都成功后，App/full 发布才把 build number 加 1。`docs/release-versioning.md:197`

### 更新发现

更新发现从最近 30 个 release 开始惰性加载 release 页面。`docs/release-versioning.md:160`
更新发现跳过没有精确 platform 与 architecture 包或超出已安装版本通道的 release，某页含兼容包时选取该页最高 SemVer 并停止请求更旧页面。`docs/release-versioning.md:163`
选中的版本仅在比已安装版本新时才提供，更新发现不降级已安装应用。`docs/release-versioning.md:165`

### 发布脚本与校验规则

构建发布脚本是 `tools/release/build_release.py`。`docs/release-versioning.md:209`
GitHub 发布凭证存放在 `tools/release/secrets/github.env`，该目录被 git 忽略。`docs/release-versioning.md:215`
`build_release.py` 只构建发布资产，`publish_dist.py` 上传已暂存于 `tools/release/dist` 的文件。`docs/release-versioning.md:239`
构建发布脚本的 `--scope` 接受 `cli`、`app`、`full` 三个取值。`docs/release-versioning.md:233`
`download_action_artifacts.py` 在把发布资产复制进 `tools/release/dist` 之前，验证每个请求的 run 都以 `success` 结论完成。`docs/release-versioning.md:314`
默认发布仓库是 `AAswordman/Operit2`。`docs/release-versioning.md:364`
构建与发布脚本必须拒绝 CLI 与 runtime 发布版本不一致的情况。`docs/release-versioning.md:373`
构建与发布脚本必须拒绝包含构建元数据的 Cargo 与 runtime 发布版本。`docs/release-versioning.md:374`
构建与发布脚本必须从发布版本推导 GitHub prerelease 标志。`docs/release-versioning.md:377`
构建与发布脚本必须在 App/full 资产构建成功后把 Flutter `buildNumber` 加 1。`docs/release-versioning.md:379`
构建与发布脚本必须在上传暂存文件前检查已有 GitHub release 的 prerelease 标志。`docs/release-versioning.md:381`

### 云端构建 workflow

云端发布构建可组合，全部可用的平台 workflow 都是手动 `workflow_dispatch` 入口。`docs/release-versioning.md:278`
macOS 与 iOS 的 workflow 还能通过 `workflow_call` 由 Apple Release Build 复用。`docs/release-versioning.md:279`
Apple Release Build 覆盖 macOS App、macOS CLI 与未签名的 iOS App。`docs/release-versioning.md:282`
macOS Flutter Build 覆盖 macOS App 和/或 CLI。`docs/release-versioning.md:283`
iOS Flutter Build 覆盖未签名的 iOS App。`docs/release-versioning.md:284`
Windows Release Build 覆盖 Windows App 和/或 CLI。`docs/release-versioning.md:285`
Linux Release Build 覆盖 Linux App 和/或 CLI。`docs/release-versioning.md:286`
Android Flutter Build 覆盖已签名的 Android APK 与 module 安装器 ZIP。`docs/release-versioning.md:287`
Android Flutter Build 要求仓库 secret `ANDROID_RELEASE_KEYSTORE_BASE64`、`ANDROID_RELEASE_STORE_PASSWORD`、`ANDROID_RELEASE_KEY_ALIAS`、`ANDROID_RELEASE_KEY_PASSWORD`。`docs/release-versioning.md:293`
Android keystore secret 必须经过 Base64 编码。`docs/release-versioning.md:299`
OpenHarmony 仍是本地构建，因为仓库没有其 SDK 与命令行工具的可复现分发地址。`docs/release-versioning.md:300`
在外部工具链来源与签名 secret 配置好之前，不得把 OpenHarmony 视为可用的云端构建。`docs/release-versioning.md:302`

### release notes 覆盖情况

release notes 文件 `2.0.0-preview.27-build33.md` 覆盖 `2.0.0-preview.27`，Apple build 33。`docs/release-notes/2.0.0-preview.27-build33.md:1`
另一份 release notes 文件覆盖 `2.0.0-preview.22`，Apple Build 28。`docs/release-notes/2.0.0-preview.22-build28.md:1`
`2.0.0-preview.22` 的对比基线是 Build 27 / `2.0.0-preview.21`，提交 `1e712b3de6f1642539f39e63035544069c3e9fa9`。`docs/release-notes/2.0.0-preview.22-build28.md:3`
`2.0.0-preview.22` 的本次二进制提交是 `72c6240b8abdb43235622c1c7891057783e6ef97`，Apple 版本 `2.0.0`，Build `28`。`docs/release-notes/2.0.0-preview.22-build28.md:4`
`2.0.0-preview.22` 的内容用于两端 TestFlight 的测试内容，不包含 CI、测试维护及其他平台专属改动。`docs/release-notes/2.0.0-preview.22-build28.md:5`
`2.0.0-preview.22` 包含 `IOS · zh-Hans` 小节。`docs/release-notes/2.0.0-preview.22-build28.md:7`
`2.0.0-preview.22` 包含 `MAC_OS · zh-Hans` 小节。`docs/release-notes/2.0.0-preview.22-build28.md:45`
代码核对表只覆盖 Build 27 基线之后、构建提交之前的变更，合并提交按实际差异核对。`docs/release-notes/2.0.0-preview.22-build28.md:81`
`2.0.0-preview.27` 中 Apple ARM64 Linux 终端默认使用原生执行器，避免短命令承担 WebKit/Wasm 的启动和传输成本。`docs/release-notes/2.0.0-preview.27-build33.md:3`
`2.0.0-preview.27` 新增构建配置 `OPERIT_ARM64_WASM`，默认 `OFF`；开发者用 `-DOPERIT_ARM64_WASM=ON` 开启 Wasm 后端，iOS/macOS 打包脚本支持同名环境变量，默认包保持关闭。`docs/release-notes/2.0.0-preview.27-build33.md:4`
`2.0.0-preview.27` 在 macOS ARM64 终端运行时开启 Thin LTO。`docs/release-notes/2.0.0-preview.27-build33.md:5`
Wasm 关闭构建中运行时 CTest 40/40 通过。`docs/release-notes/2.0.0-preview.27-build33.md:10`
Wasm 开启构建中 40 项原生回归通过，Wasm 集成首次因与构建并发触及 60 秒时限，单独复测于 47.73 秒通过。`docs/release-notes/2.0.0-preview.27-build33.md:11`
macOS 原生桥接冒烟测试通过，覆盖 PTY、流式输出、命令取消和重启持久化。`docs/release-notes/2.0.0-preview.27-build33.md:12`
扩展目录与市场安装状态测试 24 项通过。`docs/release-notes/2.0.0-preview.27-build33.md:13`
该文件注明上述结果不代表原始绘图脚本的完整耗时已得到验证。`docs/release-notes/2.0.0-preview.27-build33.md:15`

## 关键符号

- `docs/release-versioning.md` — 版本、tag、通道与包资产规则的事实来源。`docs/release-versioning.md:3`
- `tools/release/build_release.py` — 构建发布资产。`docs/release-versioning.md:209`
- `tools/release/publish_dist.py` — 上传已暂存于 `tools/release/dist` 的文件。`docs/release-versioning.md:239`
- `tools/release/download_action_artifacts.py` — 从成功的 run 收集发布资产进 `tools/release/dist`。`docs/release-versioning.md:314`
- `tools/build_scripts/release_artifacts.py` — 共享的发布包命名实现。`docs/release-versioning.md:90`
- `core/crates/foundation/util/src/GithubReleaseUtil.rs` — 更新器实现。`docs/release-versioning.md:397`
- `cliVersion` — CLI 以其 Cargo 包版本作为该值。`docs/release-versioning.md:177`
- `coreVersion` — App 从 `operit-runtime` 暴露该值。`docs/release-versioning.md:177`
- `OPERIT_ARM64_WASM` — 新增构建配置，默认 `OFF`。`docs/release-notes/2.0.0-preview.27-build33.md:4`
- `module.prop` — 使用共享的完整发布版本，并以同一 Flutter `buildNumber` 作为 `versionCode`。`docs/release-versioning.md:197`
- `buildNumber` — Flutter 平台包元数据，App/full 成功后加 1。`docs/release-versioning.md:193`
- `tools/release/secrets/github.env` — GitHub 发布凭证存放位置。`docs/release-versioning.md:215`

## 调用链

1. 构建与发布脚本读取 `apps/cli/Cargo.toml` 与 `core/crates/runtime/application/Cargo.toml` 的 `package.version`，要求两个值相同且不含构建元数据。`docs/release-versioning.md:173`
2. `build_release.py` 的 `--scope` 接受 `cli`、`app`、`full` 三个取值。`docs/release-versioning.md:233`
3. `build_release.py` 只构建发布资产。`docs/release-versioning.md:239`
4. 云端 run 的资产由 `download_action_artifacts.py` 在每个请求的 run 都以 `success` 结论完成后收集进 `tools/release/dist`。`docs/release-versioning.md:314`
5. ESP32 本地构建把板级 ZIP 包写入 `tools/release/dist/operit2-firmware-esp32-2432s028-<release-version>.zip`，包内含完整 4 MiB 初始刷机镜像、拆分刷机镜像、`partitions.csv` 与带已验证偏移量和 SHA-256 摘要的 manifest。`docs/release-versioning.md:331`
6. App/full 资产全部成功后，Flutter `buildNumber` 加 1；CLI-only 运行不改变 `buildNumber`。`docs/release-versioning.md:193`
7. `publish_dist.py` 上传 `tools/release/dist` 中已暂存的文件。`docs/release-versioning.md:239`
8. 上传前检查已有 GitHub release 的 prerelease 标志。`docs/release-versioning.md:381`
9. 更新器 `GithubReleaseUtil.rs` 按更新器通道选择 release，并按精确的 product、platform、architecture 与完整发布 tag 版本匹配资产。`docs/release-versioning.md:402`
10. 更新器拒绝 GitHub prerelease 标志不一致的情况。`docs/release-versioning.md:406`
11. 更新发现从最近 30 个 release 开始惰性加载页面，仅当选中的版本比已安装版本新时才提供，不降级已安装应用。`docs/release-versioning.md:165`
12. 更新测试用 `cli update check 0.0.0-preview.0` 在不下载的情况下检查是否有 release 可用。`docs/release-versioning.md:419`
13. 更新测试用 `cli update run 0.0.0-preview.0` 走完整 CLI 更新路径，当前目标匹配时包含安装覆盖。`docs/release-versioning.md:431`

## 来源

- `docs/release-versioning.md`（446 行）：版本、tag、通道、包资产、版本来源、发布脚本、更新器与 workflow 分工的事实来源。`docs/release-versioning.md:3`
- `docs/release-notes/2.0.0-preview.22-build28.md`（96 行）：`2.0.0-preview.22` 的 Apple Build 28 更新日志。`docs/release-notes/2.0.0-preview.22-build28.md:1`
- `docs/release-notes/2.0.0-preview.27-build33.md`（15 行）：`2.0.0-preview.27` 的 Apple build 33 更新日志。`docs/release-notes/2.0.0-preview.27-build33.md:1`
- 范围限定：本页 workflow 相关内容只写 `docs/release-versioning.md` 中记载的 workflow 名称与分工，本轮未读 `.github/workflows` 下的 workflow 文件，未核对 workflow 文件本身的触发方式与步骤。`docs/release-versioning.md:278`
- 覆盖核验：2026-11-12 对基线 `364d1d594` 的本地 checkout 执行 `ls docs/release-notes/`，仅返回 `2.0.0-preview.22-build28.md` 与 `2.0.0-preview.27-build33.md` 两个文件；10 月“没有更新日志”的结论不再成立，release notes 现有两份，最高覆盖到 `2.0.0-preview.27`，中间版本 preview.23 至 preview.26 没有对应的 release notes 文件，覆盖不全。
- App/CLI 发布版本不控制 Core 或 Edge 的配对、路由或同步，Core/Edge 协议版本是独立的整数协议版本，细节见 `peer-protocol-versioning.md`，本页未展开。`docs/release-versioning.md:444`
