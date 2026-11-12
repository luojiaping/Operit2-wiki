---
title: 发布流程
module: tools
platforms: [all]
sources: 6
date: 2026-11-11
---

## 概述

Operit2 的发布流程由文档与脚本组成，覆盖版本定义、资产构建、云端收集与 GitHub 发布四个环节。`tools/release/RELEASE_SPEC.md:3`

版本、GitHub tag、更新通道与包资产规则由 `docs/release-versioning.md` 定义。`tools/release/RELEASE_SPEC.md:3`

`docs/release-versioning.md` 是 Operit2 app 与 CLI 发布版本的事实来源。`docs/release-versioning.md:3`

`tools/release/build_release.py` 必须遵循 `docs/release-versioning.md`。`tools/release/RELEASE_SPEC.md:9`

构建发布脚本是 `tools/release/build_release.py`。`docs/release-versioning.md:209`

`build_release.py` 只构建发布资产，`publish_dist.py` 上传已暂存于 `tools/release/dist` 的文件。`docs/release-versioning.md:239`

## AI 速览

- `docs/release-versioning.md` — 版本、tag、通道与包资产规则的事实来源。`docs/release-versioning.md:3`
- `tools/release/build_release.py` — 构建发布资产的主入口，校验版本、构建各平台资产。`docs/release-versioning.md:209`
- `tools/release/publish_dist.py` — 上传已暂存于 `tools/release/dist` 的文件，不重建。`docs/release-versioning.md:351`
- `tools/release/download_action_artifacts.py` — 从成功的 GitHub Actions run 收集发布资产进 `tools/release/dist`。`docs/release-versioning.md:314`
- `tools/release/release_interactive.py` — 交互式拼出 build_release.py 命令并执行。`tools/release/release_interactive.py:117`
- `release_version()` — 读取 CLI 与 runtime 的 Cargo 版本并校验一致。`tools/release/build_release.py:429`
- `publish_release()` — 创建或复用 GitHub 发布并上传 dist 资产。`tools/release/build_release.py:1193`
- `cli_package_path()` — 用 `release_asset_name()` 生成版本化归档路径。`tools/release/build_release.py:694`
- `GithubReleaseUtil.rs` — 更新器实现，位于 `core/crates/foundation/util/src/GithubReleaseUtil.rs`。`docs/release-versioning.md:397`
- 主入口：`build_release.py` 的 `main()`，`--scope` 默认值为 “full”。`tools/release/build_release.py:1304`
- 数据流向：Cargo 与 pubspec 版本 → `build_release.py` 校验与构建 → `tools/release/dist` 暂存资产 → `publish_dist.py` 上传到 GitHub Release → 更新器按通道与精确文件名发现更新。`docs/release-versioning.md:239`

## 核心机制

### 版本与 tag

发布版本使用 SemVer 兼容格式：稳定版 `2.0.0`、预览版 `2.0.0-preview.1`、rc 版 `2.0.0-rc.1`、开发版 `2.0.0-dev.20260619`。`docs/release-versioning.md:11`

Git tag 在版本号前加 `v`，例如 `v2.0.0-preview.1`、`v2.0.0-rc.1`、`v2.0.0`。`docs/release-versioning.md:19`

构建元数据允许出现，且不改变更新顺序，例如 `2.0.0+20260619.shaabcdef`。`docs/release-versioning.md:25`

不得把构建元数据用作发布计数器，公开预览构建使用 prerelease 标识。`docs/release-versioning.md:29`

版本顺序为 `2.0.0-dev.20260619` < `2.0.0-preview.1` < `2.0.0-preview.2` < `2.0.0-rc.1` < `2.0.0`。`docs/release-versioning.md:37`

稳定版比同 major、minor、patch 的预发布版更新。`docs/release-versioning.md:39`

首个公开预览版使用 `v2.0.0-preview.1`。`docs/release-versioning.md:72`

首个稳定版使用 `v2.0.0`。`docs/release-versioning.md:78`

首次公开预览的版本值为：两个 `Cargo.toml` 均为 `2.0.0-preview.1`，`pubspec.yaml` 为 `2.0.0+1`，GitHub tag 为 `v2.0.0-preview.1`。`docs/release-versioning.md:386`

### 版本来源

发布版本来源是 `apps/cli/Cargo.toml` 与 `core/crates/runtime/application/Cargo.toml` 的 `package.version`，两个值必须相同且不得包含构建元数据。`docs/release-versioning.md:177`

CLI 用 Cargo 包版本作为 `cliVersion`。`docs/release-versioning.md:177`

App 从 `operit-runtime` 暴露 `coreVersion`。`docs/release-versioning.md:177`

Flutter 平台版本在 `apps/flutter/app/pubspec.yaml` 中为 `major.minor.patch+buildNumber`，`2.0.0-preview.1` 对应 Flutter 平台版本 `2.0.0+1`。`docs/release-versioning.md:188`

构建与发布脚本对 Git tag 与更新器元数据使用完整 Operit2 SemVer，Flutter `major.minor.patch` 必须与 Operit2 发布版本一致，`buildNumber` 仅是 Android、Windows、Linux、macOS 构建的平台包元数据。`docs/release-versioning.md:191`

App 与 full 运行先用当前 Flutter `buildNumber` 构建，全部所选 App 资产成功后再把 `pubspec.yaml` 的 `buildNumber` 加 1，仅 CLI 运行不改变 Flutter `buildNumber`。`docs/release-versioning.md:193`

Android 模块安装器 ZIP 是独立的 `module` 发布产品，`module.prop` 使用共享完整发布版本，并用同一 Flutter `buildNumber` 作为 `versionCode`，两种 Android 形态都成功后 App/full 发布才一次性递增 build number。`docs/release-versioning.md:196`

App/CLI 发布版本不控制 Core 或 Edge 的配对、路由或同步，协议版本见 `peer-protocol-versioning.md`。`docs/release-versioning.md:444`

### 更新通道

更新通道由当前已安装版本导出：当前稳定版走 stable channel，当前预发布版走 preview channel。`docs/release-versioning.md:47`

stable channel 只接受 stable GitHub release。`docs/release-versioning.md:51`

preview channel 接受 prerelease 与 stable GitHub release。`docs/release-versioning.md:53`

发布 tag 与 GitHub prerelease 标志必须一致：`v2.0.0-preview.1` 与 `v2.0.0-rc.1` 对应 `prerelease=true`，`v2.0.0` 对应 `prerelease=false`。`docs/release-versioning.md:60`

Draft release 被更新器忽略。`docs/release-versioning.md:65`

更新发现从最近 30 个发布开始懒加载页面，跳过没有精确平台与架构包或超出已安装版本通道的发布。`docs/release-versioning.md:160`

一页包含兼容包时选中该页最高 SemVer 并停止请求更旧页面，仅当当前页没有兼容包时才加载更旧页面。`docs/release-versioning.md:162`

选中的版本仅在比已安装版本新时才提供，发现过程不降级已安装应用。`docs/release-versioning.md:166`

更新器实现规则为：严格解析 `major.minor.patch[-prerelease][+build]`，比较时忽略构建元数据，按更新通道选择发布，按精确的产品、平台、架构与完整发布 tag 版本匹配资产，拒绝不匹配的 GitHub prerelease 标志。`docs/release-versioning.md:402`

### 包资产规则

包资产命名格式为 `operit2-<product>-<platform>-<architecture>-<release-version>.<extension>`。`docs/release-versioning.md:87`

共享命名实现是 `tools/build_scripts/release_artifacts.py`，它读取 App 运行时与 CLI 的 Cargo manifest、校验两个版本一致，Flutter 平台元数据保持独立。`docs/release-versioning.md:90`

CLI Windows x86_64 包名为 `operit2-cli-windows-x86_64-2.0.0-preview.16.zip`。`docs/release-versioning.md:95`

App Android 包名为 `operit2-app-android-arm64-v8a-2.0.0-preview.16.apk`，Android 模块包名为 `operit2-module-android-arm64-v8a-2.0.0-preview.16.zip`。`docs/release-versioning.md:101`

固件包名为 `operit2-firmware-esp32-2432s028-2.0.0-preview.16.zip`。`docs/release-versioning.md:110`

发布包不附带单独的校验和文件。`docs/release-versioning.md:113`

CLI 归档包含可执行文件、安装脚本、卸载脚本与 README。`docs/release-versioning.md:114`

文件名中的版本与 Git tag 一致但去掉前导 `v`，更新器按每个发布自身的 tag 与请求的产品、平台、架构拼出精确文件名。`docs/release-versioning.md:148`

macOS App 包在 Intel 与 Apple Silicon 上都使用 universal ZIP，CLI macOS 包保留各自架构与 `tar.gz` 扩展名。`docs/release-versioning.md:150`

一个 GitHub Release 可以只含所选 scope 的资产，App 客户端不把仅 CLI 的发布当作 App 更新。`docs/release-versioning.md:154`

### Windows MSI

Windows App 构建从同一 Flutter 发布目录产出便携 ZIP 与中文 MSI 安装器。`docs/release-versioning.md:116`

MSI 为当前用户安装到 `%LOCALAPPDATA%\Programs\Operit2`，创建桌面与开始菜单快捷方式，并在 Windows 设置中注册修复与卸载。`docs/release-versioning.md:117`

升级替换应用文件并保留独立的用户数据目录，ZIP 仍是更新器的下载格式，两种包都包含构建工具链的 Visual C++ 运行时 DLL。`docs/release-versioning.md:119`

MSI 打包需要 .NET 8 SDK 或更新版本，构建从 NuGet 恢复固定的 WiX 4.0.6 工具与 DTF 自定义 UI 依赖。`docs/release-versioning.md:124`

MSI 内嵌带自定义标题栏的 WPF 界面，Windows 10 1809 x64 或更新版本包含其 .NET Framework 4.7.2 运行时。`docs/release-versioning.md:125`

静默 MSI 安装继续使用 `/qn`，不打开界面。`docs/release-versioning.md:127`

安装器源码与品牌位于 `tools/windows-installer`，无障碍矢量界面用 WPF 实现于 `ui/` 下。`docs/release-versioning.md:140`

MSI 三段版本号编码为 `major.minor.(patch * 1000 + revision)`。`docs/release-versioning.md:142`

MSI 修订号区间为 dev 1–199、preview 201–399、rc 401–599、stable 999，超 199 的计数器、不支持的 prerelease 标识与 MSI 字段溢出会显式失败。`docs/release-versioning.md:143`

MSI 描述与发布文件名保留完整 SemVer，大版本升级阻止降级，同一发布重建可以替换已安装的 MSI。`docs/release-versioning.md:145`

### 构建与发布脚本必须执行的规则

构建与发布脚本必须执行的规则包括：用 TOML 解析读 Cargo 包版本，从 `pubspec.yaml` 读 Flutter 平台构建元数据。`docs/release-versioning.md:371`

构建与发布脚本必须执行的规则包括：拒绝 CLI 与 runtime 版本不一致，拒绝含构建元数据的版本，拒绝 Flutter `major.minor.patch` 与 Cargo 发布版本不一致，拒绝与 Cargo 发布版本不同的 `--tag`。`docs/release-versioning.md:373`

构建与发布脚本必须执行的规则包括：从发布版本导出 GitHub prerelease 标志，只构建所选 `--scope` 的资产，App/full 资产成功后 Flutter `buildNumber` 加 1，用 `GITHUB_TOKEN` 经 GitHub REST API 发布暂存文件，上传前检查既有 GitHub 发布的 prerelease 标志。`docs/release-versioning.md:377`

### 发布 scope 与架构

发布 scope 有三档：`--scope cli` 仅 CLI/TUI，`--scope app` 仅 App，`--scope full` 为 App 与 CLI/TUI。`docs/release-versioning.md:233`

CLI 架构选择：`--cli-arches host` 仅当前主机架构，`--cli-arches all` 为当前桌面平台的 x86_64 与 aarch64。`docs/release-versioning.md:254`

Windows 上 `--cli-arches all` 在本地构建 Windows x86_64 与 aarch64，Linux x86_64 与 aarch64 经 WSL 构建，Windows aarch64 需要 Rust target、Visual Studio ARM64 构建工具与 LLVM clang。`docs/release-versioning.md:260`

本地发布构建前按所选 scope 运行环境检查，命令含 `--check-environment`。`docs/release-versioning.md:265`

`tools/release/dist` 累积本地构建、SSH 收集与 GitHub Actions 下载的资产，仅在开始新的暂存发布集时才对 `build_release.py` 用 `--clean-dist`。`docs/release-versioning.md:242`

GitHub 发布凭证位于 `tools/release/secrets/github.env`，该目录被 git 忽略。`docs/release-versioning.md:215`

发布脚本从 `tools/release/secrets/github.env` 读取 GitHub 凭证，必需键为 `GITHUB_TOKEN` 与 `GITHUB_API_URL`。`docs/release-versioning.md:341`

默认发布仓库为 `AAswordman/Operit2`，可用 `--repo owner/name` 发布到其他仓库。`docs/release-versioning.md:364`

Windows 默认发布命令是 `.\.venv\Scripts\python.exe tools\release\publish_dist.py`。`docs/release-versioning.md:223`

### 云端构建与收集

云端发布构建可组合，全部平台工作流均为手动 `workflow_dispatch` 入口，macOS 与 iOS 还可通过 Apple Release Build 的 `workflow_call` 复用。`docs/release-versioning.md:277`

Android Flutter Build 需要 `ANDROID_RELEASE_KEYSTORE_BASE64`、`ANDROID_RELEASE_STORE_PASSWORD`、`ANDROID_RELEASE_KEY_ALIAS`、`ANDROID_RELEASE_KEY_PASSWORD` 四个仓库 secret。`docs/release-versioning.md:293`

Android keystore secret 必须 Base64 编码，OpenHarmony 仍为本地构建，因仓库没有其 SDK 与命令行工具的可复现分发 URL。`docs/release-versioning.md:299`

云端构建流程为：用 `gh workflow run` 触发 Apple、macOS、iOS、Windows、Linux、Android 构建后，用 `download_action_artifacts.py --run-id <run-id>` 收集各 run 的资产。`docs/release-versioning.md:311`

`download_action_artifacts.py` 在把发布资产复制进 `tools/release/dist` 前验证每个请求的 run 以 `success` 结论完成。`docs/release-versioning.md:314`

收集完成后在发布集完整时通过 `publish_dist.py` 发布收集到的文件。`docs/release-versioning.md:316`

### 本地构建与 ESP32

协作方用 `python3 tools/build_scripts/build_local.py --products all --cli-arches host` 在本地构建当前主机，`--products app` 可加 `--include-ios`，`--products esp32` 构建 ESP32。`docs/release-versioning.md:324`

ESP32 本地构建需要 ESP-IDF Rust 工具链、`espflash`、`ldproxy` 与 `EMSDK` 环境变量。`docs/release-versioning.md:329`

ESP32 固件包写入 `tools/release/dist/operit2-firmware-esp32-2432s028-<release-version>.zip`，包含完整 4 MiB 初始刷机镜像、拆分刷机镜像、`partitions.csv` 与带已验证偏移量和 SHA-256 摘要的 manifest。`docs/release-versioning.md:331`

### 更新测试

更新测试命令 `cargo run --manifest-path apps/cli/Cargo.toml -- cli update target` 显示当前桌面 CLI 的更新目标。`docs/release-versioning.md:413`

更新测试命令 `cargo run --manifest-path apps/cli/Cargo.toml -- cli update check 0.0.0-preview.0` 检查是否有发布可用而不下载。`docs/release-versioning.md:419`

更新测试命令 `cargo run --manifest-path apps/cli/Cargo.toml -- cli update download 0.0.0-preview.0` 下载匹配资产并显示进度而不安装。`docs/release-versioning.md:425`

更新测试命令 `cargo run --manifest-path apps/cli/Cargo.toml -- cli update run 0.0.0-preview.0` 走完整 CLI 更新路径，当前目标匹配时含安装覆盖。`docs/release-versioning.md:431`

测试命令 `cargo run --manifest-path apps/cli/Cargo.toml -- tui --update-current-version 0.0.0-preview.0` 用测试当前版本强制触发 TUI 启动更新提示。`docs/release-versioning.md:437`

用 `0.0.0-preview.0` 这类 prerelease 当前版本测试预览发布，`0.0.0` 这类稳定当前版本选择 stable channel 并忽略 GitHub prereleases。`docs/release-versioning.md:439`

## 关键符号

`SemanticVersion` 含 `text`、`major`、`minor`、`patch`、`prerelease`、`build` 六个字段。`tools/release/build_release.py:57`

`SemanticVersion.is_prerelease` 在 `prerelease` 元组非空时为真。`tools/release/build_release.py:69`

`SEMVER_RE` 匹配 major.minor.patch[-prerelease][+build]。`tools/release/build_release.py:40`

`FLUTTER_PLATFORM_VERSION_RE` 的模式要求版本号后跟 `+` 与首位非零的数字。`tools/release/build_release.py:47`

`ReleaseScope` 取值为 “cli”、“app”、“full”、“none”。`tools/release/build_release.py:109`

`CLI_RUST_TARGETS` 覆盖 Windows、Linux、macOS 的 `x86_64` 与 `aarch64` 共六个目标。`tools/release/build_release.py:128`

`DIST_DIR` 为 `tools/release/dist`，`WORK_DIR` 为 `tools/release/work`，`SECRETS_DIR` 为 `tools/release/secrets`。`tools/release/build_release.py:24`

`CLI_MANIFEST` 为 `apps/cli/Cargo.toml`，`RUNTIME_MANIFEST` 为 `core/crates/runtime/application/Cargo.toml`。`tools/release/build_release.py:31`

`DEFAULT_GITHUB_ENV` 为 `tools/release/secrets/github.env`，`DEFAULT_RELEASE_REPO` 为 `AAswordman/Operit2`。`tools/release/build_release.py:38`

`load_env_file()` 逐行读 env 文件，跳过空行与 `#` 注释行。`tools/release/build_release.py:263`

`load_env_file()` 遇到不含 `=` 的行时报错 `Invalid env line`。`tools/release/build_release.py:263`

`github_auth()` 要求 `GITHUB_TOKEN` 非空，否则报错 `GITHUB_TOKEN is empty`。`tools/release/build_release.py:283`

`github_auth()` 要求 `GITHUB_API_URL` 非空，否则报错 `GITHUB_API_URL is empty`。`tools/release/build_release.py:287`

`cargo_package_version()` 用 `tomllib.load()` 解析 manifest，读取 `package.version`。`tools/release/build_release.py:374`

`parse_semver()` 在 `allow_tag` 为真时剥离前导 `v`，为假时拒绝前导 `v`。`tools/release/build_release.py:386`

数字 `prerelease` 标识含前导零时会被拒绝。`tools/release/build_release.py:400`

`validate_product_release_version()` 拒绝含构建元数据的版本。`tools/release/build_release.py:416`

`release_version()` 分别读取 CLI 与 runtime 的 Cargo 包版本并校验两者无构建元数据。`tools/release/build_release.py:429`

`release_version()` 在 CLI 与 runtime 发布版本不同时报错 `CLI and runtime release versions differ`。`tools/release/build_release.py:441`

`flutter_platform_version()` 要求 `pubspec.yaml` 版本符合 `major.minor.patch+buildNumber`，否则报错。`tools/release/build_release.py:450`

`validate_flutter_platform_version()` 要求 Flutter `build_name` 与发布版本的 `major.minor.patch` 一致。`tools/release/build_release.py:463`

`increment_flutter_platform_build_number()` 把平台版本的 `build_number` 加 1 并写回 `pubspec.yaml`。`tools/release/build_release.py:472`

`ensure_android_signing()` 要求 `tools/release/secrets/android-signing.properties` 存在。`tools/release/build_release.py:481`

ensure_android_signing() 把 `RELEASE_STORE_FILE` 与签名口令、别名装入本地属性。`tools/release/build_release.py:488`

随后把本地属性写回 android/local.properties。`tools/release/build_release.py:497`

`android_release_store_file()` 对相对路径相对 signing properties 所在目录解析，keystore 文件不存在时报错。`tools/release/build_release.py:506`

`compress_zip()` 把构建目录压成 ZIP 归档。`tools/release/build_release.py:522`

`compress_tar_gz()` 把构建目录压成 tar.gz 归档。`tools/release/build_release.py:530`

`write_windows_cli_installer_files()` 生成 Windows CLI 包的 `install.bat`。`tools/release/build_release.py:548`

write_windows_cli_installer_files() 生成 Windows CLI 包的 `uninstall.bat`。`tools/release/build_release.py:564`

write_windows_cli_installer_files() 生成 Windows CLI 包的 `README.txt`。`tools/release/build_release.py:580`

`write_unix_cli_installer_files()` 生成 Unix CLI 包的 `install.sh`。`tools/release/build_release.py:598`

write_unix_cli_installer_files() 生成 Unix CLI 包的 `uninstall.sh`。`tools/release/build_release.py:611`

`write_cli_installer_files()` 按平台分发：Windows 用 `write_windows_cli_installer_files()`，其余平台用 `write_unix_cli_installer_files()`。`tools/release/build_release.py:642`

`host_platform()` 把 “darwin” 映射为 macOS，把 Windows 与 Linux 分别映射为对应平台。`tools/release/build_release.py:652`

`host_arch()` 把 `amd64`/`x86_64` 映射为 `x86_64`，把 `arm64`/`aarch64` 映射为 `aarch64`。`tools/release/build_release.py:660`

`cli_binary_name()` 在 Windows 上为 `operit2.exe`，其余平台为 `operit2`。`tools/release/build_release.py:680`

`cli_archive_extension()` 在 Windows 上为 “zip”，其余平台为 `tar.gz`。`tools/release/build_release.py:684`

`cli_package_path()` 用 `release_asset_name()` 生成 `DIST_DIR` 下的版本化归档路径。`tools/release/build_release.py:694`

`parse_github_repo()` 要求仓库参数为 `owner/name` 格式，否则报错。`tools/release/build_release.py:712`

`github_request()` 发请求时带 `"User-Agent": "Operit2-Release"` 与 `"X-GitHub-Api-Version": "2022-11-28"`。`tools/release/build_release.py:726`

`close_release_processes()` 只在 Windows 主机上关闭占用发布目录的进程。`tools/release/build_release.py:183`

`build_wsl_linux_app()` 要求 WSL 内 PATH 上有 `dart` 与 `fvm`。`tools/release/build_release.py:810`

`build_wsl_linux()` 只在 Windows 主机上执行，未找到 `wsl.exe` 时报错。`tools/release/build_release.py:939`

`build_android_app()` 调用 `build_flutter_android.py`，并传 `--build-name`、`--build-number`、`--enforce-lockfile`。`tools/release/build_release.py:960`

`build_android_module()` 调用 `build_android_module_release.py`，并传 `--build-name`、`--build-number`、`--enforce-lockfile` 与 `--dist-dir`。`tools/release/build_release.py:975`

`build_ohos_app()` 调用 `build_flutter_ohos.py` 构建 OpenHarmony 应用包。`tools/release/build_release.py:987`

build_ohos_app() 的输出文件名为 `release_asset_name("app", "ohos", "arm64", "hap")`。`tools/release/build_release.py:998`

`build_host_app()` 在 Windows 分支调用 `build_flutter_windows.py`。`tools/release/build_release.py:1007`

build_host_app() 在 Linux 分支调用 `build_flutter_linux.py`。`tools/release/build_release.py:1027`

build_host_app() 在 macOS 分支对 “sandbox” 与 “unsandbox” 两种类型各调用一次 `build_flutter_macos.py`。`tools/release/build_release.py:1044`

`build_cli_target()` 构建前调用 `prepare_plugin_assets()` 生成 ToolPkg 资产。`tools/release/build_release.py:1112`

build_cli_target() 构建后用 `verify_cli_plugin_assets()` 校验 CLI 二进制。`tools/release/build_release.py:1142`

`build_host_cli()` 调用 `build_cli_current.py` 并传 `--arches`。`tools/release/build_release.py:1156`

`check_release_environment()` 按所选产品映射 `environment_products`：App 与 CLI 都选则为 “all”，仅 App 为 “app”，仅 CLI 为 “cli”。`tools/release/build_release.py:1170`

check_release_environment() 把环境检查委托给 `check_build_environment.py`。`tools/release/build_release.py:1180`

`publish_release()` 先校验 `DIST_DIR` 内文件，为空时报错 `No release assets were produced`。`tools/release/build_release.py:1193`

`publish_release()` 在既有 GitHub 发布存在且 `prerelease` 标志不一致时报错。`tools/release/build_release.py:1193`

publish_release() 创建新发布时 `tag_name` 与 `name` 均为 tag，`body` 为 `Operit2 {tag}`，`draft` 与 `prerelease` 按参数传入。`tools/release/build_release.py:1217`

publish_release() 上传每个资产前先删除同名既有资产，再调用 `upload_release_asset()` 上传。`tools/release/build_release.py:1233`

`verify_github_publish_access()` 对目标仓库发 GET 请求做发布前检查，失败时报 GitHub publish preflight failed。`tools/release/build_release.py:1237`

`delete_existing_release_asset()` 按资产 id 发 DELETE 请求删除同名既有 GitHub 发布资产，资产 id 非整数时报错。`tools/release/build_release.py:1253`

`upload_release_asset()` 以 `application/octet-stream` 把资产字节 POST 到上传地址，期望返回 201。`tools/release/build_release.py:1272`

`products_for_scope()` 拒绝把 `--products` 与 `--scope app`、`--scope cli` 或 `--scope none` 联用。`tools/release/build_release.py:1282`

products_for_scope() 拒绝把 `--products none` 与 “app” 或 “cli” 联用。`tools/release/build_release.py:1297`

`main()` 中 `--scope` 默认值为 “full”。`tools/release/build_release.py:1304`

`main()` 中 `--wsl-distro` 默认值为 `FedoraLinux-43`。`tools/release/build_release.py:1306`

main() 提供 `--check-environment` 选项，检查发布构建需求后退出。`tools/release/build_release.py:1313`

main() 中 `--cli-arches` 默认值为 “host”。`tools/release/build_release.py:1314`

main() 设置环境变量 `RUSTFLAGS` 为 `-Awarnings`。`tools/release/build_release.py:1317`

`publish_dist.py` 从 `build_release` 导入 `DEFAULT_GITHUB_ENV`、`DEFAULT_RELEASE_REPO`、`DIST_DIR`、`github_auth`、`load_env_file`、`parse_semver`、`publish_release` 与 `release_version`。`tools/release/publish_dist.py:11`

`publish_dist.py` 从 build_release 导入 `verify_github_publish_access` 与 `validate_release_assets`。`tools/release/publish_dist.py:17`

`publish_dist.py` 的 `--repo` 默认值为 `DEFAULT_RELEASE_REPO`。`tools/release/publish_dist.py:26`

`publish_dist.py` 的 `--check-only` 校验认证、tag 与 dist 资产而不上传。`tools/release/publish_dist.py:34`

`publish_dist.py` 的 `release_assets()` 在 `DIST_DIR` 不存在或为空时报错。`tools/release/publish_dist.py:39`

`publish_dist.py` 的 `release_assets()` 调用 `validate_release_assets()` 校验 dist 内文件。`tools/release/publish_dist.py:45`

`publish_dist.py` 的 `release_tag()` 在未传 `--tag` 时默认使用 `v{version.text}`。`tools/release/publish_dist.py:50`

`publish_dist.py` 的 `release_tag()` 在 `--tag` 与发布版本不一致时报错。`tools/release/publish_dist.py:53`

`publish_dist.py` 在 `--prerelease` 用于稳定发布版本时报错。`tools/release/publish_dist.py:64`

`publish_dist.py` 在 --check-only 时打印 `Publish check passed` 并返回 0，不上传。`tools/release/publish_dist.py:80`

`publish_dist.py` 的 `main()` 调用 `publish_release()` 上传 dist 资产。`tools/release/publish_dist.py:83`

`release_interactive.py` 的 `RELEASE_SCRIPT` 指向同目录的 `build_release.py`。`tools/release/release_interactive.py:12`

`release_interactive.py` 的 `choose()` 提示用户输入序号，输入无效时打印“输入无效，请重新选择。”并重新提问。`tools/release/release_interactive.py:42`

`release_interactive.py` 的交互选择 CLI/TUI 对应 `--scope cli`。`tools/release/release_interactive.py:62`

`release_interactive.py` 的交互选择 App 对应 `--scope app`，App 含 Android APK、Android 模块、OpenHarmony 与当前桌面平台。`tools/release/release_interactive.py:63`

`release_interactive.py` 的交互选择全量对应 `--scope full`，即 App（含 Android 模块）加 CLI/TUI。`tools/release/release_interactive.py:64`

`release_interactive.py` 的交互选择只检查版本和脚本入口对应 `--scope none --no-wsl`。`tools/release/release_interactive.py:65`

`release_interactive.py` 在 CLI 或全量时追加架构选择，当前主机架构对应 `--cli-arches host`。`tools/release/release_interactive.py:75`

`release_interactive.py` 在 CLI 或全量时追加架构选择，全量桌面架构对应 `--cli-arches all`，覆盖 Windows、Linux、macOS 的 x86_64 与 aarch64。`tools/release/release_interactive.py:76`

`release_interactive.py` 在非检查项时追加 Linux WSL 构建选择，关闭对应 `--no-wsl`。`tools/release/release_interactive.py:85`

`release_interactive.py` 的 `main()` 在 `RELEASE_SCRIPT` 不存在时打印“发布脚本不存在”并返回 1。`tools/release/release_interactive.py:96`

`release_interactive.py` 在确认步骤选择取消时打印“已取消。”并返回 0。`tools/release/release_interactive.py:113`

`release_interactive.py` 用 `subprocess.run()` 在仓库根目录执行拼出的发布命令，并返回其退出码。`tools/release/release_interactive.py:117`

`download_action_artifacts.py` 的 `--run-id` 可重复传入且为必填参数。`tools/release/download_action_artifacts.py:22`

`download_action_artifacts.py` 的 `--dist-dir` 默认值为 `tools/release/dist`，`--work-dir` 默认值为 tools/release/work/github-actions。`tools/release/download_action_artifacts.py:23`

`download_action_artifacts.py` 的 `require_successful_run()` 用 `gh run view --json status,conclusion` 检查，要求 run 状态为 `completed` 且结论为 `success`。`tools/release/download_action_artifacts.py:35`

`download_action_artifacts.py` 的 `release_assets()` 只保留名字在 `release_asset_names()` 中的文件。`tools/release/download_action_artifacts.py:51`

`download_action_artifacts.py` 的 `download_run()` 先调用 `require_successful_run()` 校验 run 成功。`tools/release/download_action_artifacts.py:61`

`download_action_artifacts.py` 的 `download_run()` 用 `gh run download` 把 run 的产物下载到工作目录。`tools/release/download_action_artifacts.py:62`

`download_action_artifacts.py` 的 `collect_run()` 在 run 中未找到发布资产文件时报错。`tools/release/download_action_artifacts.py:76`

`download_action_artifacts.py` 的 `main()` 逐个处理每个 --run-id，并打印收集进 dist 的资产。`tools/release/download_action_artifacts.py:87`

## 调用链

本地构建链路按以下顺序执行。`tools/release/build_release.py:1319`

1. main() 调用 `release_version()` 与 `flutter_platform_version()`，再校验 Flutter 平台版本与所选产品。`tools/release/build_release.py:1319`
2. main() 在 --check-environment 时调用 `check_release_environment()` 后直接返回。`tools/release/build_release.py:1323`
3. main() 在 --clean-dist 时清空 `DIST_DIR`，否则只确保 `DIST_DIR` 存在。`tools/release/build_release.py:1327`
4. main() 每次运行清空 `WORK_DIR`。`tools/release/build_release.py:1331`
5. main() 按 `build_android_app()`、`build_android_module()`、`build_ohos_app()`、`build_host_app()` 的顺序构建 App 资产。`tools/release/build_release.py:1333`
6. main() 在 CLI 在所选产品内时调用 `build_host_cli()`。`tools/release/build_release.py:1339`
7. main() 在未传 --no-wsl 且产品不为 “none” 时调用 `build_wsl_linux()`。`tools/release/build_release.py:1342`
8. main() 在 App 在所选产品内时调用 `increment_flutter_platform_build_number()` 递增平台版本的 build number。`tools/release/build_release.py:1352`

云端收集链路按以下顺序执行。`docs/release-versioning.md:311`

1. 用 `gh workflow run` 触发 Apple、macOS、iOS、Windows、Linux、Android 构建。`docs/release-versioning.md:311`
2. `download_action_artifacts.py` 验证每个请求的 run 以 `success` 结论完成，再把发布资产复制进 `tools/release/dist`。`docs/release-versioning.md:314`
3. 收集完成后在发布集完整时通过 `publish_dist.py` 发布收集到的文件。`docs/release-versioning.md:316`

发布链路按以下顺序执行。`tools/release/publish_dist.py:83`

1. `publish_dist.py` 的 `release_tag()` 解析并校验 tag 与发布版本一致。`tools/release/publish_dist.py:53`
2. `publish_dist.py` 的 `release_assets()` 列出 `DIST_DIR` 内文件并校验。`tools/release/publish_dist.py:45`
3. `publish_dist.py` 加载 `github.env`、取 `github_auth()`、调用 `verify_github_publish_access()` 做发布前检查。`tools/release/publish_dist.py:17` `tools/release/build_release.py:38`
4. `publish_dist.py` 的 `main()` 调用 `publish_release()` 上传 dist 资产。`tools/release/publish_dist.py:83`

交互式链路按以下顺序执行。`tools/release/release_interactive.py:58`

1. `release_interactive.py` 的 `build_command()` 先问处理目标，再按目标问架构与 WSL 选项，拼出 build_release.py 命令。`tools/release/release_interactive.py:58`
2. `release_interactive.py` 的 main() 打印待执行命令并要求确认，取消时打印“已取消。”并返回 0。`tools/release/release_interactive.py:113`
3. 确认后 `release_interactive.py` 用 `subprocess.run()` 在仓库根目录执行命令，并返回其退出码。`tools/release/release_interactive.py:117`

## 来源

- `tools/release/RELEASE_SPEC.md`（9 行）：版本、tag、通道与包资产规则的定义指向与 `build_release.py` 的遵循要求。`tools/release/RELEASE_SPEC.md:3`
- `docs/release-versioning.md`（446 行）：版本格式、通道、包资产、版本来源、构建与发布规则、云端构建、更新测试。`docs/release-versioning.md:3`
- `tools/release/build_release.py`（1371 行）：构建发布资产的主脚本，分段读完。`tools/release/build_release.py:1302`
- `tools/release/publish_dist.py`（92 行）：上传已暂存资产的发布脚本。`tools/release/publish_dist.py:60`
- `tools/release/release_interactive.py`（122 行）：交互式发布入口。`tools/release/release_interactive.py:95`
- `tools/release/download_action_artifacts.py`（103 行）：大纲第三问点名、与本页流程直接相关的同目录文件，已全读；它不在大纲 seed_files 列表中。`tools/release/download_action_artifacts.py:35`

本页关于 `tools/build_scripts/release_artifacts.py` 与 `core/crates/foundation/util/src/GithubReleaseUtil.rs` 的断言来自 `docs/release-versioning.md` 的陈述，未逐项核验其实现。`docs/release-versioning.md:90`
