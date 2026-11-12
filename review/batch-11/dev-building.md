---
title: 构建指南
module: dev
platforms: [all]
sources: 1
date: 2026-11-11
---

## 概述

- 本页讲 Operit2 从仓库根构建、运行与打包，seed 文件是 `BUILDING.md`。`BUILDING.md:3`
- `BUILDING.md` 写明 Rust 构建警告目前是预期的，以命令退出状态作为构建成功信号。`BUILDING.md:5`
- 仓库布局：`apps/cli` 是 Rust CLI/TUI 入口。`BUILDING.md:10`
- 仓库布局：`apps/flutter/app` 是 Flutter 应用入口。`BUILDING.md:11`
- 仓库布局：`core/crates` 是共享 Rust 运行时 crate。`BUILDING.md:12`
- 仓库布局：`hosts` 是原生宿主实现。`BUILDING.md:13`
- 仓库布局：`tools/release` 是发布构建与发布脚本。`BUILDING.md:14`
- 仓库布局：`docs/release-versioning.md` 定义版本、tag、通道与资产命名规则。`BUILDING.md:15`
- 构建脚本入口见 [[tools-build-scripts|构建脚本入口]]，发布流程见 [[tools-release|发布流程]]，tools 总览见 [[tools-overview|tools 总览]]。`BUILDING.md:3`

## AI 速览

- `build_release.py` — 直接构建发布脚本，本地完整发布的入口。`BUILDING.md:343`
- `release_interactive.py` — 交互式发布助手。`BUILDING.md:337`
- `build_local.py` — 当前宿主 App/CLI 构建，协作者一条命令构建当前宿主。`BUILDING.md:473`
- `publish_dist.py` — 把 `tools/release/dist` 中已构建的文件发布到 GitHub Release。`BUILDING.md:517`
- `download_action_artifacts.py` — 收集云端成功工作流运行的发布归档进 `tools/release/dist`。`BUILDING.md:465`
- `sync_plugin_packages.py` — 从 `plugins/packages/` 重新生成插件资产。`BUILDING.md:213`
- `build_cli_linux_debian12.py` — Debian 12 容器内构建 Linux CLI，链接 glibc 2.36。`BUILDING.md:267`
- `build_flutter_android.py` — Android 构建，运行插件打包、Rust 桥交叉构建与 Gradle `assembleRelease`。`BUILDING.md:643`
- `build_flutter_ohos.py` — OpenHarmony HAP 构建。`BUILDING.md:828`
- `tools/ios-runtime/arm64/build.sh` — iOS 运行时构建，产出宿主 CLI、设备/模拟器静态库与 `OperitArm64.xcframework`。`BUILDING.md:182`
- `wasm-bindgen-cli` 0.2.122 — Web 构建依赖，版本与桥的 `Cargo.lock` 匹配。`BUILDING.md:782`
- `RUST_TOOLCHAIN_VERSION` — Rust 工具链钉死版本的来源，位于 `.github/workflows/`。`BUILDING.md:140`
- `FVM_VERSION` — FVM 钉死版本的来源，位于 Flutter CI 工作流。`BUILDING.md:138`
- 主入口：本地完整发布是 `build_release.py`。`BUILDING.md:343`
- 主入口：当前宿主快捷构建是 `build_local.py`。`BUILDING.md:473`
- 数据流向：入口脚本 → 平台构建 → 发布包进 `tools/release/dist`。`BUILDING.md:368`

## 核心机制

### 前置要求

- 通用工具要求 Rust stable 工具链，经 `rustup` 安装。`BUILDING.md:23`
- 通用工具要求 Python 虚拟环境位于 `.venv`。`BUILDING.md:24`
- 通用工具要求 Node.js 24 且启用 Corepack。`BUILDING.md:25`
- `pnpm` 10.7.0 用于 `plugins/packages/buildin/workflow`。`BUILDING.md:26`
- 通用工具要求 Git。`BUILDING.md:27`
- Windows 桌面 CLI 构建要求 Visual Studio 2022 C++ 构建工具。`BUILDING.md:33`
- Windows 桌面 CLI 构建要求 MSVC x64 与 ARM64 组件。`BUILDING.md:34`
- Windows 桌面 CLI 构建要求 LLVM clang，位于 `C:\Program Files\LLVM\bin\clang.exe`。`BUILDING.md:35`
- `BUILDING.md` 写明 GNU 工具链不是受支持的替代方案。`BUILDING.md:38`
- Linux 桌面 App 构建要求 CMake、Ninja、pkg-config、clang 与 GTK 开发头文件。`BUILDING.md:44`
- Linux 桌面 App 构建的 GStreamer 开发头文件通过 pkg-config 提供 `gstreamer-1.0`、`gstreamer-app-1.0` 与 `gstreamer-audio-1.0`。`BUILDING.md:45`
- Linux 桌面 App 构建的 WebKitGTK 4.1 开发头文件提供 pkg-config 包 `webkit2gtk-4.1`。`BUILDING.md:47`
- Flutter 应用构建要求 Flutter SDK。`BUILDING.md:53`
- `apps/flutter/app/android/local.properties` 含 `flutter.sdk`。`BUILDING.md:54`
- Android 发布签名使用 `tools/release/secrets/android-signing.properties`。`BUILDING.md:55`
- GitHub 发布使用 `tools/release/secrets/github.env`。`BUILDING.md:61`
- `github.env` 的必需键是 `GITHUB_TOKEN` 与 `GITHUB_API_URL`。`BUILDING.md:66`

### 钉死的构建输入

- `BUILDING.md` 把下列值称为仓库构建契约（repository build contract），基线于 2026 年 9 月 27 日验证通过；后续依赖变更仍需各自的平台构建与运行时冒烟测试。`BUILDING.md:131`
- 钉死的 Flutter SDK 是 AAswordman/flutter-ohos 的 3.41.10-ohos-0.0.2-beta.operit.1，来源是 `apps/flutter/app/.fvmrc`，经 FVM 安装。`BUILDING.md:137`
- 钉死的 FVM 是 4.3.0，来源是 Flutter CI 工作流中的 `FVM_VERSION`。`BUILDING.md:138`
- 钉死的 Dart SDK 是 `^3.10.8`，来源是 `apps/flutter/app/pubspec.yaml`，由钉死的 Flutter SDK 提供。`BUILDING.md:139`
- 钉死的 Rust 工具链是 1.95.0，来源是 `.github/workflows/` 中的 `RUST_TOOLCHAIN_VERSION`，经 rustup 安装。`BUILDING.md:140`
- 钉死的 Node.js 是 24，来源是 CI 工作流中的 `actions/setup-node`。`BUILDING.md:141`
- 钉死的 Java 是 Temurin 17，来源是 `.github/workflows/android-flutter-build.yml` 中的 `actions/setup-java`。`BUILDING.md:142`
- 钉死的 Gradle 是 8.14，来源是 `apps/flutter/app/android/gradle/wrapper/gradle-wrapper.properties`。`BUILDING.md:143`
- 钉死的工作流包管理器是 pnpm 10.7.0，来源是 `plugins/packages/buildin/workflow/package.json`。`BUILDING.md:144`
- Dart 依赖版本与托管包校验和记录在 `apps/flutter/app/pubspec.lock`；托管包使用 `https://pub.dev`。`BUILDING.md:149`
- 本地 Dart 包从 `apps/flutter/thirdparty` 解析；Git Dart 包使用 `pubspec.yaml` 与 `pubspec.lock` 中记录的仓库 URL 与提交。`BUILDING.md:151`
- 工作流 JavaScript 依赖由 `package.json` 钉死、由 `plugins/packages/buildin/workflow/pnpm-lock.yaml` 解析；生成的许可清单 `resources/THIRD_PARTY_NOTICES.txt` 从该 lockfile 重新生成，不得手工编辑。`BUILDING.md:155`
- 原生运行时源归档由其获取/构建脚本以一个上游 URL 与 SHA-256 值声明；脚本与校验和是下载产物的事实来源。`BUILDING.md:158`
- CI 运行器镜像属于构建环境：`ubuntu-24.04`、`windows-2025` 与 `macos-15`，按 `.github/workflows/` 声明。`BUILDING.md:160`
- 依赖或工具链变更时，在同一改动中更新其 lockfile 或钉死的来源条目以及本文档。`BUILDING.md:163`
- 生成的 lockfile 中的合并冲突同时保留依赖图变更与仓库的来源策略。`BUILDING.md:165`

### 终端 Node.js 版本

- Android、iOS/ARM64、OpenHarmony 与 Web 运行时构建器以 Alpine v3.23 的 Node.js 24 为目标，并拒绝装有其他 Node 主版本的已安装 APK 数据库。`BUILDING.md:170`
- 终端 Node.js 大版本变更后，生成的 rootfs/initramfs 产物重新构建；CI `setup-node` 只选择构建宿主的 Node。`BUILDING.md:172`
- 桌面终端使用用户的系统 shell 与 Node 安装，不使用应用内嵌的 Node 运行时；这些宿主上使用 Node.js 24，CI 配置本身无法升级最终用户机器。`BUILDING.md:174`

### iOS 运行时钉死

- iOS 运行时由 `hosts/ios/linux-runtime` 下独立的 C++ 源码构建，没有 iSH 或外部 ARM64 模拟器依赖。`BUILDING.md:180`
- `tools/ios-runtime/arm64/build.sh` 构建宿主 CLI、iOS 设备/模拟器静态库与 `OperitArm64.xcframework`；Runner 通过 `apps/flutter/app/ios/build_arm64_runtime.sh` 调用同一构建。`BUILDING.md:182`
- iOS 运行时钉死为仓库源码、C++17，来源是 `hosts/ios/linux-runtime/CMakeLists.txt`。`BUILDING.md:187`
- Alpine minirootfs 钉死为 3.23.6、aarch64，归档 URL 与 SHA-256 在 `tools/ios-runtime/arm64/rootfs.json`。`BUILDING.md:188`
- Alpine 包钉死为 v3.23 main/community、aarch64，由 `tools/ios-runtime/arm64/build_rootfs_linux.sh` 安装已签名的 APK 包。`BUILDING.md:189`
- iOS 运行时 Node.js 钉死为主版本 24，由 `tools/runtime/verify_alpine_node24.py` 检查已安装 APK 数据库。`BUILDING.md:190`
- 在 Linux 上用 `sudo bash tools/ios-runtime/arm64/build_rootfs_linux.sh` 构建完整开发根；脚本支持原生 AArch64 Linux 与配置了 qemu-user-static/binfmt 的 x86_64 Linux。`BUILDING.md:193`
- QEMU 是构建工具，不内嵌进 iOS 应用；产物 `Runner/arm64-rootfs.tar.gz` 与 SHA-256 sidecar 由 iOS 工作流消费，`package_rootfs.py` 在发布到 Runner 前校验外部提供的 AArch64 归档。`BUILDING.md:195`
- iOS 工作流使用 `macos-15`、Xcode 的 iOS SDK、CMake 与 Apple Clang 编译器；构建命令与 `.github/workflows/ios-flutter-build.yml`、`ios-app-package-build.yml` 与 `ios-arm64-runtime.yml` 保持同步。`BUILDING.md:200`

### 生成的插件资产与内置工作流插件

- `core/crates/runtime/application/assets/plugins/{buildin,external}` 在构建时生成且被 git 忽略；`operit-runtime` 的 `build.rs` 把这些文件内嵌进每个二进制，因此编译前从 `plugins/packages/` 重新生成。`BUILDING.md:208`
- 重新生成插件资产的命令是 `python3 plugins/tools/sync_plugin_packages.py --source runtime --no-hot-reload`。`BUILDING.md:213`
- Flutter 平台构建通过原生构建钩子自动运行该同步；CLI 构建脚本（`build_cli_*.py`、`tools/release/build_release.py`）在 `cargo build` 之前运行它。`BUILDING.md:217`
- 手工运行 `cargo build --release` 而不做该步骤时，资产缺失或过期会在 `build.rs` 中失败；调试用的 `cargo check` 只警告；CLI 打包还会拒绝遗漏任一生成资产名的二进制。`BUILDING.md:219`
- 不得在机器之间复制插件资产目录：过期快照构建出的 binary 其插件集与源码树静默不一致。`BUILDING.md:221`
- 内置工作流插件是 pnpm 项目，其 `package.json` 把包管理器钉死为 pnpm 10.7.0；本地命令使用 Corepack 以遵守该钉死版本。`BUILDING.md:227`
- pnpm lockfile 是依赖的事实来源；该包内不使用 npm。`BUILDING.md:228`
- 工作流包目录下的命令是 `corepack pnpm --version`、`corepack pnpm install --frozen-lockfile`、`corepack pnpm run pack:toolpkg` 与 `corepack pnpm run test:web`。`BUILDING.md:234`
- `plugins/tools/sync_plugin_packages.py` 通过 Corepack 调用该包构建，因此自动化同步使用 `package.json` 中钉死的版本。`BUILDING.md:239`

### Rust 目标与 Debian 12 容器

- Windows CLI 发布构建使用 `rustup target add x86_64-pc-windows-msvc` 与 `aarch64-pc-windows-msvc`。`BUILDING.md:247`
- Fedora WSL Linux CLI 发布构建使用 `rustup target add x86_64-unknown-linux-musl` 与 `aarch64-unknown-linux-gnu`，并用 dnf 安装 `musl-gcc`、`musl-devel`、`musl-libc-static`、`gcc-aarch64-linux-gnu` 与 `sysroot-aarch64-fc43-glibc`。`BUILDING.md:254`
- aarch64 Linux CLI 发布要求 `aarch64-linux-gnu-gcc` 交叉 C 编译器与 Fedora 的 `/usr/aarch64-redhat-linux/sys-root/fc43` sysroot。`BUILDING.md:259`
- 构建发布脚本在编译 C 依赖时注入该 sysroot 的 `limits.h`，因为 Fedora 的交叉编译器构建时不带目标头文件。`BUILDING.md:261`
- `build_cli_linux_debian12.py` 在 Debian 12 容器内构建 Linux CLI；二进制链接 Debian 12 的 glibc（2.36）并要求 GCC 12 C++ 运行时（`GLIBCXX_3.4.30`）。`BUILDING.md:267`
- Debian 12 容器构建的二进制运行于 Debian 12、Ubuntu 22.04 及更新的发行版；打包、安装器文件、内嵌插件资产与产物命名与 `build_cli_linux.py` 一致，发布标准的 x86_64 musl 构建仍保留在后者。`BUILDING.md:268`
- 驱动拒绝引用新于 glibc 2.36 的符号的已打包二进制。`BUILDING.md:272`
- Debian 12 容器构建的前提是 podman（无根，优先）或 docker；镜像通过在临时容器中运行 `containers/debian12/image-setup.sh` 并提交来制备。`BUILDING.md:275`
- 受限网络下 Debian 12 构建可指定 `--base-image`、`--apt-mirror` 与 `--rebuild-image`，并导出 `RUSTUP_DIST_SERVER` 与 `RUSTUP_UPDATE_ROOT` 指向 rustup 镜像。`BUILDING.md:290`
- 慢速 npm 下载时把 `--env npm_config_registry=https://registry.npmmirror.com` 转发进容器。`BUILDING.md:297`
- 驱动在 git 忽略的 `tools/release/work/debian12/` 下制备 rustup（工具链版本取自 `RUST_TOOLCHAIN_VERSION`，默认发布钉死的 1.95.0）、cargo 缓存与 pnpm store，因此镜像重建不重新下载工具链或 crate。`BUILDING.md:303`
- aarch64 目标用 `gcc-aarch64-linux-gnu` 交叉编译，不需要额外 sysroot；`--shell` 以相同挂载打开容器用于调试。`BUILDING.md:306`

### 发布脚本与云端构建

- 交互式发布助手是 `.\.venv\Scripts\python.exe tools\release\release_interactive.py`。`BUILDING.md:337`
- 直接构建发布脚本是 `.\.venv\Scripts\python.exe tools\release\build_release.py`。`BUILDING.md:343`
- 仅做环境检查的命令是 `tools\build_scripts\build_local.py --products all --cli-arches host --check` 与 `tools\release\build_release.py --scope full --cli-arches all --check-environment`。`BUILDING.md:349`
- `build_release.py` 的 scope 包括 cli、app、full 与 none（none 配 `--no-wsl`）。`BUILDING.md:356`
- `tools/release/dist` 是本地、SSH 收集与 GitHub Actions 资产共用的 staging 目录；`build_release.py` 保留已有的 staging 文件以便组合平台构建。`BUILDING.md:368`
- 用 `--scope cli --clean-dist` 开始一组新的 staging 文件。`BUILDING.md:373`
- 本地 Windows `build_release.py` 构建 Android、OpenHarmony、Windows App、Windows CLI 与 WSL Linux 资产；选择 WSL Linux 资产时要求 Windows 构建工具、Android/OpenHarmony 签名文件与 Fedora WSL。`BUILDING.md:380`
- 本地 `build_local.py` 在检查当前宿主需求后只构建当前宿主的 App 和/或 CLI；macOS 可用 `--include-ios` 增加未签名的 iOS。`BUILDING.md:385`
- 云端构建入口是手工的 `workflow_dispatch` 入口：Apple Release Build、macOS Flutter Build、iOS Flutter Build、Windows Release Build、Linux Release Build 与 Android Flutter Build。`BUILDING.md:424`
- 云端产物用 `download_action_artifacts.py` 收集进 `tools/release/dist`。`BUILDING.md:390`
- 云端构建组合的步骤是：触发所需平台工作流，等每个选定工作流成功，每个运行各用一个 `--run-id` 收集进 `tools/release/dist`，只在收集的文件就绪可发布时运行 `publish_dist.py`。`BUILDING.md:400`
- 成功的 App 与 full 构建在资产打包后推进 `apps/flutter/app/pubspec.yaml` 中的 Flutter build number；仅 CLI 的构建不改变它。`BUILDING.md:404`
- Windows 上 `--cli-arches all` 构建 `operit2-cli-windows-x86_64-<release-version>.zip`、`operit2-cli-windows-aarch64-<release-version>.zip`、`operit2-cli-linux-x86_64-<release-version>.tar.gz` 与 `operit2-cli-linux-aarch64-<release-version>.tar.gz`。`BUILDING.md:418`
- 云端工作流是独立的手工 `workflow_dispatch` 入口；Apple 聚合工作流调用可复用的 macOS 与 iOS 工作流，其余工作流各只构建一个平台族。`BUILDING.md:424`
- Apple Release Build 覆盖 macOS App、macOS CLI 与未签名的 iOS App；macOS Flutter Build 覆盖 macOS App 和/或 CLI；iOS Flutter Build 覆盖未签名的 iOS App；Windows Release Build 覆盖 Windows App 和/或 CLI；Linux Release Build 覆盖 Linux App 和/或 CLI；Android Flutter Build 构建已签名的 Android APK。`BUILDING.md:429`
- Android Flutter Build 运行前要求仓库 secret `ANDROID_RELEASE_KEYSTORE_BASE64`、`ANDROID_RELEASE_STORE_PASSWORD`、`ANDROID_RELEASE_KEY_ALIAS` 与 `ANDROID_RELEASE_KEY_PASSWORD`。`BUILDING.md:440`
- `ANDROID_RELEASE_KEYSTORE_BASE64` 是 Android 发布 keystore 的 Base64 编码；工作流只在运行器内部写入签名材料。`BUILDING.md:446`
- OpenHarmony 尚无 GitHub Actions 工作流；其 SDK 与命令行工具目前没有本仓库可用的可复现 URL 分发，因此云端工作流无法制备有效工具链，本地 OpenHarmony 流程仍是受支持的构建路径。`BUILDING.md:449`
- 触发云端构建的 `gh workflow run` 命令覆盖 Apple Release Build、macOS Flutter Build、iOS Flutter Build、Windows Release Build、Linux Release Build 与 Android Flutter Build。`BUILDING.md:456`
- `download_action_artifacts.py` 只接受已完成且成功的工作流运行，并把其发布归档复制进已有的 `tools/release/dist` staging 目录。`BUILDING.md:465`
- 协作者用一条 Python 命令在仓库根构建当前宿主：Windows 用 `.\.venv\Scripts\python.exe tools\build_scripts\build_local.py --products all --cli-arches host`；macOS 与 Linux 用 `python3 tools/build_scripts/build_local.py --products all --cli-arches host`。`BUILDING.md:473`
- 本地 Apple 构建要求 macOS 宿主上有 Xcode、Rust、FVM、Node/npm 与 Python 3。`BUILDING.md:481`
- 本地 Apple 构建产物包括 `operit2-app-macos-universal-<release-version>.zip`、`operit2-app-ios-arm64-<release-version>.zip`、`operit2-cli-macos-x86_64-<release-version>.tar.gz` 与 `operit2-cli-macos-aarch64-<release-version>.tar.gz`。`BUILDING.md:485`
- 本地 Apple 构建的输出目录是 `tools/release/dist`。`BUILDING.md:494`
- 每个 CLI 归档包含 `operit2` 或 `operit2.exe`、`install.sh` 或 `install.bat`、`uninstall.sh` 或 `uninstall.bat` 与 `README.txt`。`BUILDING.md:501`
- `--no-wsl` 跳过 WSL Linux 打包。`BUILDING.md:509`
- 发布已构建文件到 GitHub Release 的命令是 `.\.venv\Scripts\python.exe tools\release\publish_dist.py`。`BUILDING.md:517`
- `publish_dist.py --check-only` 只校验 staging 文件与 GitHub 凭据而不上传。`BUILDING.md:523`
- `publish_dist.py --draft` 以草稿形式发布 staging 文件。`BUILDING.md:529`
- 构建发布脚本从 `apps/cli/Cargo.toml`、`core/crates/operit-runtime/Cargo.toml` 与 `apps/flutter/app/pubspec.yaml` 读取版本。`BUILDING.md:535`
- 版本、tag、构建号与更新器资产规则定义在 `docs/release-versioning.md`。`BUILDING.md:543`

### 本地 CLI 检查

- 本地 CLI 检查在仓库根运行 `cargo check --manifest-path apps/cli/Cargo.toml`。`BUILDING.md:314`
- 本地 CLI 版本检查命令是 `cargo run --manifest-path apps/cli/Cargo.toml --bin operit2 -- cli version`。`BUILDING.md:315`
- TUI 用 `cargo run --manifest-path apps/cli/Cargo.toml --bin operit2 -- tui` 启动。`BUILDING.md:321`
- 更新检查命令包括 `cli update target`、`cli update check 0.0.0-preview.0` 与 `tui --update-current-version 0.0.0-preview.0`。`BUILDING.md:327`

### Flutter 应用

- 构建发布脚本通过 Flutter 构建应用包；本地检查在 `apps/flutter/app` 下运行 `fvm install --skip-pub-get` 与 `fvm dart pub get --enforce-lockfile`。`BUILDING.md:552`
- `lib/core/proxy/generated/*.g.dart` 在构建时生成且被 git 忽略。`BUILDING.md:558`
- 应用构建脚本 `build_flutter_android.py`、`build_flutter_ios.py` 与 `build_flutter_macos.py` 在 `pub get` 之前重新生成代理代码。`BUILDING.md:559`
- 直接的 Windows 与 macOS Flutter 构建在 Flutter 组装 Dart 之前先构建 Rust 桥，因此 `flutter run -d macos` 与 `flutter build macos` 自动生成代理代码。`BUILDING.md:561`
- 在干净检出上做 `flutter analyze`、`fvm dart pub get` 或脚本之外的其他平台构建前先生成代理代码，以免出现 `uri_has_not_been_generated` 错误；生成命令是 `cargo check --manifest-path core/crates/proxy/local/Cargo.toml --quiet`，从仓库根运行。`BUILDING.md:565`
- Windows 应用发布构建命令是 `fvm flutter build windows --release --no-pub --build-name 2.0.0 --build-number 1`。`BUILDING.md:577`
- Android 发布构建要求签名值在 `tools/release/secrets/android-signing.properties`；Android 发布 keystore（`tools/release/secrets/operit2-release.keystore`）与该 properties 文件保存在 git 之外并备份。`BUILDING.md:589`

### Android 本地构建

- 在 CI 之外构建 Android APK 需要 CI 运行器隐式提供的额外前提。`BUILDING.md:595`
- Windows 本地 Android 构建要求开启 Developer Mode：FVM 为钉死的 SDK 创建目录符号链接（`.fvm/flutter_sdk`），无此权限时 `fvm install` 以 `errno 1314` 失败；目录 junction 不是替代品，staging 检查使用 `Path.is_symlink()`。`BUILDING.md:598`
- 构建依赖 crate（`tree-sitter-*`、`ring`）在 `cargo build` 期间为主机编译 C 代码；rustup 自带的 `gcc.exe` 不能编译 C。`BUILDING.md:602`
- Windows 本地 Android 构建安装完整 MinGW 工具链（例如 `scoop install mingw-winlibs`）或 MSVC Build Tools，并使其在 Gradle 守护进程启动之前位于 PATH 上；守护进程缓存启动时的环境，改 PATH 后重启它（对 `java` 做 `Stop-Process`）。`BUILDING.md:605`
- 插件同步钩子调用 `corepack pnpm`，项目把 `packageManager` 钉死为 `pnpm@10.7.0`；PATH 上其他 pnpm 安装（scoop/npm shim）会遮蔽 corepack 并以版本检查失败中止。`BUILDING.md:608`
- 工作流插件依赖在 Gradle 插件同步钩子运行前安装：在 `plugins\packages\buildin\workflow` 目录运行 `corepack pnpm install --frozen-lockfile`。`BUILDING.md:616`
- Android 运行时（rootfs）产物 `liboperit_busybox.so`、`liboperit_proot.so` 与 `rootfs.tar.gz.bin` 由 CI 经 `tools/android-runtime/build_alpine_rootfs_wsl.sh` 产生且要求 WSL；缺失时 Gradle 检查 `requiredOperitAndroidRuntimeLibraries` 失败。`BUILDING.md:620`
- Rust 桥构建为 `aarch64-linux-android` 运行 bindgen（`rquickjs-sys` 带 `bindgen` 特性），在构建时加载 `libclang.dll`；CI 从 nuget.org 把它制备进 `target/operit-build-tools`。`BUILDING.md:625`
- 没有 libclang 时桥构建以 "Unable to find libclang" 失败。`BUILDING.md:631`
- 桥链接的 V8 是源码构建的，`rusty_v8` 不发布预构建的 Android 产物；Gradle 构建自动运行 `tools/build_scripts/prepare_android_v8.py`，首次构建耗时明显更长并要求 NDK r23+ 安装。`BUILDING.md:633`
- NDK 从 `OPERIT_ANDROID_V8_NDK`、`ANDROID_NDK_HOME`、`$ANDROID_HOME/ndk` 或 `~/Android/ndk` 检测，绑定生成还要求 libclang 21.1+。`BUILDING.md:635`
- Windows 本地 Android 构建命令是 `python tools\build_scripts\build_flutter_android.py --build-name 2.0.0 --build-number 11`；该命令运行完整链（插件打包、Rust 桥交叉构建、Gradle `assembleRelease`）并写入 `tools/release/dist/operit2-app-android-arm64-v8a-<release-version>.apk`。`BUILDING.md:643`
- APK 文件名使用完整发布版本（例如 2.0.0-preview.16），含任何预发布标识符。`BUILDING.md:650`
- NDK 由 Android Gradle Plugin 自动制备；Rust 桥仍要求 `rustup target add aarch64-linux-android`。`BUILDING.md:651`
- Android Gradle 按 Android 构建变体选择 Rust 桥 profile：debug 用 Cargo 的 dev profile 与 `target/<rust-target>/debug` 输出；profile 与 release 用 `cargo build --release` 与 `target/<rust-target>/release` 输出。`BUILDING.md:654`
- JNI 库按变体分阶段为变体专属的生成源码；`src/main/jniLibs` 中的缓存桥被排除在这些源码之外，因此 Release APK 不会打包此前的 Debug 桥。`BUILDING.md:657`
- Linux 宿主用 NDK 的 `linux-x86_64` 预构建工具链（`*-clang` 与 `llvm-ar`，无 Windows 的 `.cmd`/`.exe` 后缀）构建同一链。`BUILDING.md:661`
- Linux 上 Rust 桥默认把 `LIBCLANG_PATH` 绑定到 `/usr/lib`；libclang 在别处时设置 `OPERIT_LIBCLANG_DIR` 覆盖。`BUILDING.md:665`
- Linux Android 构建同样适用源码构建 V8 的要求：安装 libclang 21.1+ 与 `ld.lld`（Debian/Ubuntu 用 `apt install llvm-21-dev lld`），并保证 NDK r23+ 可发现（`~/Android/ndk`、`$ANDROID_HOME/ndk` 或 `ANDROID_NDK_HOME`）；宿主编译器自动获取。`BUILDING.md:671`
- Linux 宿主用同一命令 `python tools/build_scripts/build_flutter_android.py --build-name 2.0.0 --build-number 11` 构建 Android。`BUILDING.md:677`

### OpenHarmony

- OpenHarmony 构建要求 OpenHarmony Flutter SDK，位于 `https://github.com/AAswordman/flutter-ohos.git`。`BUILDING.md:685`
- 全部平台使用钉死的 Operit fork 发布 3.41.10-ohos-0.0.2-beta.operit.1，在 `apps/flutter/app/.fvmrc` 中配置；FVM 把带标签的源码安装到 `.fvm/flutter_sdk`。`BUILDING.md:688`
- 检出后在 `apps/flutter/app` 运行 `fvm install --skip-pub-get` 与 `fvm flutter precache --web --ohos`。`BUILDING.md:692`
- 用户环境提供 FVM 4.3.0（经 Pub 缓存 bin 目录在 PATH 上）、经 Flutter 或 Dart SDK bin 目录在 PATH 上的 `dart`、指向 OpenHarmony SDK 根的 `OHOS_SDK_HOME`，以及在 PATH 上供 `hdc` 使用的所选 OpenHarmony SDK `toolchains` 目录。`BUILDING.md:697`
- 更改用户环境变量后重启终端或 IDE，使新进程继承它们。`BUILDING.md:703`
- Windows 本地 OpenHarmony 构建的用户环境保持 `HOS_SDK_HOME`、`OHOS_SDK_HOME` 与 `DEVECO_SDK_HOME` 稳定，均指向 `%USERPROFILE%\harmony-tools\harmonyos-sdk`。`BUILDING.md:710`
- 用户 PATH 增加 `%USERPROFILE%\harmony-tools\commandline-tools-2.0.0.2\command-line-tools\bin`、`%USERPROFILE%\harmony-tools\ohcommandline-tools-2.0.0.2\oh-command-line-tools\bin` 与 `%LOCALAPPDATA%\Pub\Cache\bin`。`BUILDING.md:718`
- 项目本地 OpenHarmony 属性文件 `apps/flutter/app/ohos/local.properties` 指向同一 SDK（`hwsdk.dir`）与 FVM 选定的 Flutter SDK（`flutter.sdk`）。`BUILDING.md:727`
- SDK 根包含带全部构建组件的数字 API 目录；当前验证的布局是 `harmonyos-sdk\18` 下的 `ets`、`js`、`native`、`previewer` 与 `toolchains`。`BUILDING.md:736`
- 不得把项目指向 `%USERPROFILE%\harmony-tools\openharmony-sdk\9`；该旧 SDK 与当前 OpenHarmony API 18 项目文件不匹配。`BUILDING.md:743`
- FVM 选定的 SDK 暴露 `ohos` 平台与 `hap` 构建命令。`BUILDING.md:746`
- `fvm flutter doctor -v` 报告 Flutter 与 OpenHarmony 两个工具链。`BUILDING.md:757`
- OpenHarmony 应用模块用选定的 SDK 生成一次：在 `apps\flutter\app` 目录运行 `fvm flutter create --platforms ohos .`。`BUILDING.md:763`
- Rust 工具链使用原生 OpenHarmony 目标 `rustup target add aarch64-unknown-linux-ohos`。`BUILDING.md:822`
- HAP 通过仓库构建脚本从仓库根构建：`.\.venv\Scripts\python.exe tools\build_scripts\build_flutter_ohos.py --enforce-lockfile`。`BUILDING.md:828`
- 构建脚本暂存 Rust 桥、复制 OpenHarmony Flutter 引擎 HAR 文件、为本地 API 18 SDK 表面修补 embedding HAR、清除解包的 `ohpm` embedding 包，并运行 `flutter build hap`。`BUILDING.md:831`
- 构建脚本用 `tools/release/secrets/ohos-signing/ohos-signing.properties` 中的项目 OpenHarmony 发布签名材料签署未签名的 HAP。`BUILDING.md:834`
- OpenHarmony 发布签名文件（`operit-ohos-release-app.p12`、`operit-ohos-release-app.cer`、`operit-ohos-release-profile.p12`、`operit-ohos-release-profile.cer`、`ohos-signing.properties`）保存在 git 之外并备份。`BUILDING.md:843`
- 生成的按构建区分的 profile 文件写入 `apps/flutter/app/ohos/signing`，该目录被 git 忽略并视为本地构建输出。`BUILDING.md:853`
- 已签名的构建输出复制到 `tools/release/dist/operit2-app-ohos-arm64-<release-version>.hap`。`BUILDING.md:861`
- Flutter 命令报告 `Can't load Kernel binary` 时，清除该应用过期的 FVM 或 Flutter 快照状态，在 `apps/flutter/app` 运行 `fvm install --skip-pub-get`，再从仓库根重新运行 OpenHarmony 构建脚本。`BUILDING.md:864`

### Web

- Web 前端是 `apps/flutter/app/web` 下的标准 Flutter Web 项目；专用的 `Deploy Web Experience` GitHub Actions 工作流构建该前端并把 `apps/flutter/app/build/web` 发布到 `gh-pages` 分支，供 `web.operit.app` 使用。`BUILDING.md:767`
- 从干净检出准备 Web 构建依赖：在仓库根运行 `python -m venv .venv` 与 `npm install --prefix .ci-tools/typescript --no-audit --no-fund typescript@5.9.3`。`BUILDING.md:776`
- Web 构建依赖准备还包括在 `plugins/packages/buildin/workflow` 运行 `corepack pnpm install --frozen-lockfile`、`rustup target add wasm32-unknown-unknown`，以及 `cargo install wasm-bindgen-cli --version 0.2.122 --locked`。`BUILDING.md:779`
- `wasm-bindgen` CLI 版本与桥的 `Cargo.lock` 匹配。`BUILDING.md:785`
- Web 构建钩子下载钉死的 WASI SDK 与浏览器 guest 资产；首次构建要求联网；后续构建在再次校验钉死的 SHA-256 摘要后才复用缓存的 BIOS 资源。`BUILDING.md:786`
- 本地 Web 构建使用与 GitHub Actions 相同的命令：在 `apps/flutter/app` 运行 `fvm flutter build web --release --no-wasm-dry-run --base-href /`。`BUILDING.md:795`
- 更快的纯 Rust 检查需要同时运行两条命令，因为宿主 crate 不编译全部 Flutter Web ABI 适配器。`BUILDING.md:798`
- 纯 Rust 检查的两条命令是 `cargo check --locked --manifest-path hosts/web/Cargo.toml --target wasm32-unknown-unknown` 与 `cargo check --locked --manifest-path apps/flutter/native/operit-flutter-bridge/Cargo.toml --target wasm32-unknown-unknown`。`BUILDING.md:800`
- 手工触发 GitHub Pages 部署的命令是 `gh workflow run "Deploy Web Experience"`。`BUILDING.md:809`
- 原生应用与 CLI 发布构建不编译、不复制、不打包 Web 前端 bundle；它们只暴露 Link Access 服务，用户打开 `https://web.operit.app/?accessUrl=...&token=...`。`BUILDING.md:812`

### Windows GNU 工具链排障

- Windows 需求要求 MSVC 工具链；改用 GNU 工具链（`x86_64-pc-windows-gnu`）会遇到一连串失败，且错误信息不指向修复方法。`BUILDING.md:74`
- GNU 排障小节的症状与修复记录自一次真实构建会话（rustup `stable-x86_64-pc-windows-gnu`），且该小节只覆盖 x86_64。`BUILDING.md:76`
- rustup GNU 工具链自带的 self-contained 目录缺少可用的汇编器，`ld.exe` 与 `dlltool.exe` 存在。`BUILDING.md:83`
- 经过 `dlltool` 生成的导入库的链接步骤会失败。`BUILDING.md:84`
- 修复方法是把 MSYS2 `mingw-w64-x86_64-binutils` 包的 `as.exe` 与 `ar.exe` 复制进 self-contained 目录。`BUILDING.md:86`
- self-contained 目录由 rustup 管理，每次 `rustup update` 后重新应用该修复。`BUILDING.md:88`
- 自带目录同时提供 `gcc.exe` 与 `x86_64-w64-mingw32-gcc.exe`，两者是同一链接器驱动。`BUILDING.md:93`
- 自带 `gcc.exe` 的内置提示写明它只用作链接器，不能用于编译 C 文件。`BUILDING.md:97`
- 通过 `cc` 编译 C 代码的 crate 因此失败，即使两个名字下都存在 GCC 二进制。`BUILDING.md:102`
- 修复方法是把 `cc` 指向真正的 MinGW 或 Cygwin GCC（例如把 MSYS2 `mingw64\bin` 目录前置到 PATH 或设置 `CC`），或改用 MSVC 工具链。`BUILDING.md:106`
- 若把 `as.exe` 复制进 self-contained 目录而非使用 PATH 上的 MSYS2 `mingw64\bin`，它仍会因依赖 `libintl-8.dll` 而启动失败，`libintl-8.dll` 又依赖 `libiconv-2.dll`；`zlib1.dll` 与 `libzstd.dll` 也有类似缺口。`BUILDING.md:113`
- 修复方法是复制匹配的 MSYS2 包提供的运行时 DLL（`mingw-w64-x86_64-gettext-runtime`、`mingw-w64-x86_64-libiconv`、`mingw-w64-x86_64-zlib`、`mingw-w64-x86_64-zstd`），包括 `libcharset-1.dll` 与 `libasprintf-0.dll` 等传递依赖。`BUILDING.md:117`
- 枚举二进制 DLL 导入的方法是运行 `llvm-objdump --private-headers <file>`；rustup 工具链在 self-contained 上一级目录提供 `llvm-objdump.exe`。`BUILDING.md:121`
- DLL 修复同样在每次 `rustup update` 后重新应用。`BUILDING.md:122`
- `BUILDING.md` 写明 MSVC 工具链避免整类问题，仍是 Windows 构建受支持的配置。`BUILDING.md:125`

### 清理

- 清理发布输出的命令是 `Remove-Item -Recurse -Force tools\release\dist, tools\release\work`。`BUILDING.md:874`
- 清理 CLI 的 Rust 构建输出的命令是 `Remove-Item -Recurse -Force apps\cli\target`。`BUILDING.md:880`
- 清理命令只用于构建产物（build artifacts）。`BUILDING.md:882`

## 关键符号

- `build_release.py` — 直接构建发布脚本，见 `tools/release/build_release.py`。`BUILDING.md:343`
- `release_interactive.py` — 交互式发布助手，见 `tools/release/release_interactive.py`。`BUILDING.md:337`
- `build_local.py` — 当前宿主构建，见 `tools/build_scripts/build_local.py`。`BUILDING.md:349`
- `publish_dist.py` — 发布 staging 文件到 GitHub Release，见 `tools/release/publish_dist.py`。`BUILDING.md:517`
- `download_action_artifacts.py` — 收集云端成功运行的发布归档，见 `tools/release/download_action_artifacts.py`。`BUILDING.md:465`
- `sync_plugin_packages.py` — 重新生成插件资产，见 `plugins/tools/sync_plugin_packages.py`。`BUILDING.md:213`
- `build_cli_linux_debian12.py` — Debian 12 容器内 Linux CLI 构建，见 `tools/build_scripts/build_cli_linux_debian12.py`。`BUILDING.md:286`
- `build_flutter_android.py` — Android 构建，见 `tools/build_scripts/build_flutter_android.py`。`BUILDING.md:643`
- `build_flutter_ohos.py` — OpenHarmony HAP 构建，见 `tools/build_scripts/build_flutter_ohos.py`。`BUILDING.md:828`
- `build_flutter_android.py`、`build_flutter_ios.py`、`build_flutter_macos.py` — 应用构建脚本，在 `pub get` 前重新生成 Dart 代理代码。`BUILDING.md:559`
- `tools/ios-runtime/arm64/build.sh` — iOS 运行时构建脚本。`BUILDING.md:182`
- `build_arm64_runtime.sh` — Runner 调用 iOS 运行时构建的脚本，见 `apps/flutter/app/ios/build_arm64_runtime.sh`。`BUILDING.md:182`
- `build_rootfs_linux.sh` — iOS 开发根构建脚本，见 `tools/ios-runtime/arm64/build_rootfs_linux.sh`。`BUILDING.md:193`
- `verify_alpine_node24.py` — 检查 iOS 运行时已安装 APK 数据库的 Node.js 主版本，见 `tools/runtime/verify_alpine_node24.py`。`BUILDING.md:190`
- `package_rootfs.py` — 校验外部提供的 AArch64 归档再发布到 Runner。`BUILDING.md:197`
- `prepare_android_v8.py` — Gradle 构建自动运行的源码构建 V8 准备脚本，见 `tools/build_scripts/prepare_android_v8.py`。`BUILDING.md:633`
- `build_cli_linux.py` — Debian 12 容器构建对齐打包与命名规则的参照脚本。`BUILDING.md:268`
- `operit-runtime` 的 `build.rs` — 把生成的插件资产内嵌进每个二进制。`BUILDING.md:208`
- `core/crates/proxy/local/Cargo.toml` — 生成 Dart 代理代码的检查入口。`BUILDING.md:568`
- `hosts/web/Cargo.toml` — Web 纯 Rust 检查的宿主 crate 清单。`BUILDING.md:800`
- `apps/flutter/native/operit-flutter-bridge/Cargo.toml` — Web 纯 Rust 检查的桥 crate 清单。`BUILDING.md:800`
- `GITHUB_TOKEN` 与 `GITHUB_API_URL` — `github.env` 的必需键。`BUILDING.md:66`
- `RUST_TOOLCHAIN_VERSION` — Rust 工具链钉死版本的来源键，位于 `.github/workflows/`。`BUILDING.md:140`
- `FVM_VERSION` — FVM 钉死版本的来源键，位于 Flutter CI 工作流。`BUILDING.md:138`
- `OHOS_SDK_HOME` — 指向 OpenHarmony SDK 根的环境变量。`BUILDING.md:700`
- `HOS_SDK_HOME` 与 `DEVECO_SDK_HOME` — Windows 本地 OpenHarmony 构建保持稳定的环境变量。`BUILDING.md:710`
- `OPERIT_LIBCLANG_DIR` — Linux 上覆盖默认 `LIBCLANG_PATH`（`/usr/lib`）的环境变量。`BUILDING.md:665`
- `OPERIT_ANDROID_V8_NDK` — 检测 Android V8 构建用 NDK 的环境变量之一。`BUILDING.md:635`
- `ANDROID_RELEASE_KEYSTORE_BASE64` — Android Flutter Build 要求的仓库 secret 之一。`BUILDING.md:440`
- `apps/flutter/app/.fvmrc` — Flutter SDK 钉死版本的来源文件。`BUILDING.md:137`
- `apps/flutter/app/pubspec.lock` — Dart 依赖版本与托管包校验和的记录文件。`BUILDING.md:149`
- `plugins/packages/buildin/workflow/pnpm-lock.yaml` — 工作流 JavaScript 依赖的解析来源。`BUILDING.md:155`
- `resources/THIRD_PARTY_NOTICES.txt` — 从工作流 lockfile 重新生成的许可清单，不得手工编辑。`BUILDING.md:155`
- `tools/ios-runtime/arm64/rootfs.json` — Alpine minirootfs 归档 URL 与 SHA-256 的记录文件。`BUILDING.md:188`
- `apps/flutter/app/android/gradle/wrapper/gradle-wrapper.properties` — Gradle 钉死版本的来源文件。`BUILDING.md:143`
- `tools/release/secrets/android-signing.properties` — Android 发布签名文件。`BUILDING.md:55`
- `tools/release/secrets/operit2-release.keystore` — Android 发布 keystore，保存在 git 之外并备份。`BUILDING.md:589`
- `tools/release/secrets/ohos-signing/ohos-signing.properties` — OpenHarmony 发布签名材料。`BUILDING.md:837`
- `docs/release-versioning.md` — 版本、tag、构建号与更新器资产规则的定义文件。`BUILDING.md:543`
- `requiredOperitAndroidRuntimeLibraries` — 缺失 Android 运行时产物时失败的 Gradle 检查。`BUILDING.md:620`
- `liboperit_busybox.so`、`liboperit_proot.so`、`rootfs.tar.gz.bin` — CI 产生且要求 WSL 的 Android 运行时产物。`BUILDING.md:620`
- `OperitArm64.xcframework` — iOS 运行时构建产物之一。`BUILDING.md:182`
- `Runner/arm64-rootfs.tar.gz` — iOS 开发根构建产物，由 iOS 工作流消费。`BUILDING.md:195`

## 调用链

1. 环境检查：`build_local.py --products all --cli-arches host --check` 或 `build_release.py --scope full --cli-arches all --check-environment`。`BUILDING.md:349`
2. 本地完整发布构建的资产进 `tools/release/dist`；`build_release.py` 保留已有的 staging 文件以便组合平台构建。`BUILDING.md:368`
3. 发布：`publish_dist.py` 把 `tools/release/dist` 中已构建的文件发布到 GitHub Release。`BUILDING.md:517`
4. 发布校验：`publish_dist.py --check-only` 只校验 staging 文件与 GitHub 凭据而不上传。`BUILDING.md:523`
5. 草稿发布：`publish_dist.py --draft` 以草稿形式发布 staging 文件。`BUILDING.md:529`
6. 云端组合：触发所需平台工作流 → 等每个选定工作流成功 → 每个运行各用一个 `--run-id` 经 `download_action_artifacts.py` 收集进 `tools/release/dist` → 只在文件就绪可发布时运行 `publish_dist.py`。`BUILDING.md:397`
7. Android 本地链前提：在 CI 之外构建 Android APK 需要 CI 运行器隐式提供的额外前提。`BUILDING.md:595`
8. Android 本地链构建：`build_flutter_android.py --build-name 2.0.0 --build-number 11` 运行插件打包、Rust 桥交叉构建与 Gradle `assembleRelease`，并写入 `tools/release/dist/operit2-app-android-arm64-v8a-<release-version>.apk`。`BUILDING.md:643`
9. OpenHarmony 链准备：检出后在 `apps/flutter/app` 运行 `fvm install --skip-pub-get` 与 `fvm flutter precache --web --ohos`。`BUILDING.md:692`
10. OpenHarmony 链目标：Rust 工具链使用原生 OpenHarmony 目标 `rustup target add aarch64-unknown-linux-ohos`。`BUILDING.md:822`
11. OpenHarmony 链构建：`build_flutter_ohos.py --enforce-lockfile` 暂存 Rust 桥、复制引擎 HAR、修补 embedding HAR 并运行 `flutter build hap`。`BUILDING.md:831`
12. OpenHarmony 链签名：构建脚本用 `tools/release/secrets/ohos-signing/ohos-signing.properties` 中的项目 OpenHarmony 发布签名材料签署未签名的 HAP。`BUILDING.md:834`
13. OpenHarmony 链输出：已签名的构建输出复制到 `tools/release/dist/operit2-app-ohos-arm64-<release-version>.hap`。`BUILDING.md:861`
14. Web 链准备：在仓库根运行 `python -m venv .venv` 与 `npm install --prefix .ci-tools/typescript --no-audit --no-fund typescript@5.9.3`。`BUILDING.md:776`
15. Web 链依赖：在 `plugins/packages/buildin/workflow` 运行 `corepack pnpm install --frozen-lockfile`，再加 `rustup target add wasm32-unknown-unknown` 与 `cargo install wasm-bindgen-cli --version 0.2.122 --locked`。`BUILDING.md:779`
16. Web 链构建：在 `apps/flutter/app` 运行 `fvm flutter build web --release --no-wasm-dry-run --base-href /`。`BUILDING.md:795`
17. Web 链发布：`Deploy Web Experience` 工作流把 `apps/flutter/app/build/web` 发布到 `gh-pages` 分支，供 `web.operit.app` 使用。`BUILDING.md:767`
18. iOS 运行时链根：`sudo bash tools/ios-runtime/arm64/build_rootfs_linux.sh` 构建完整开发根；产物 `Runner/arm64-rootfs.tar.gz` 与 SHA-256 sidecar 由 iOS 工作流消费。`BUILDING.md:193`
19. iOS 运行时链构建：`tools/ios-runtime/arm64/build.sh` 构建宿主 CLI、设备/模拟器静态库与 `OperitArm64.xcframework`。`BUILDING.md:182`
20. GNU 排障链汇编器：复制 `as.exe` 与 `ar.exe` 进 self-contained 目录。`BUILDING.md:86`
21. GNU 排障链汇编器维护：`as.exe` 修复在每次 `rustup update` 后重新应用。`BUILDING.md:88`
22. GNU 排障链编译器：把 `cc` 指向真正的 MinGW 或 Cygwin GCC，或改用 MSVC 工具链。`BUILDING.md:106`
23. GNU 排障链 DLL：复制匹配的 MSYS2 包提供的运行时 DLL。`BUILDING.md:117`
24. GNU 排障链排查：运行 `llvm-objdump --private-headers <file>` 枚举二进制 DLL 导入追查缺失项。`BUILDING.md:121`
25. GNU 排障链 DLL 维护：DLL 修复在每次 `rustup update` 后重新应用。`BUILDING.md:122`
26. 插件资产链生成：`python3 plugins/tools/sync_plugin_packages.py --source runtime --no-hot-reload` 从 `plugins/packages/` 重新生成资产。`BUILDING.md:213`
27. 插件资产链内嵌：`operit-runtime` 的 `build.rs` 把生成的插件资产内嵌进每个二进制。`BUILDING.md:208`
28. 插件资产链打包：CLI 打包拒绝遗漏任一生成资产名（generated asset name）的二进制。`BUILDING.md:219`

## 来源

- seed 文件：`BUILDING.md`（标题 Building Operit2）。`BUILDING.md:1`
- 本页全部事实来自 `BUILDING.md` 的文档陈述；钉死值的来源文件（`.fvmrc`、`pubspec.yaml`、CI 工作流、`gradle-wrapper.properties` 等）本页未逐项复核，表中的来源列转述文档表格。`BUILDING.md:137`
- `BUILDING.md` 中的钉死值、命令与流程是文档记载的 repository build contract（仓库构建契约），本页按文档原样转述，未把文档声明写成已验证的实现行为。`BUILDING.md:130`
- 本页未作全仓零命中类否定结论；唯一否定性表述（OpenHarmony 尚无 GitHub Actions 工作流）直接转述文档原文。`BUILDING.md:449`
