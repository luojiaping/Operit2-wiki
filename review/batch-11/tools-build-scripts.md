---
title: 构建脚本入口
module: tools
platforms: [android, windows, macos, linux, esp32]
sources: 10
date: 2026-11-11
---

## 概述

- 构建脚本是 Operit2 的 Python 构建入口集合，本地构建与 GitHub Actions 共用同一批 Python 入口。`tools/build_scripts/README.md:2`
- 脚本按 product、platform 或 operation 命名，不设 `_action.py` / `_local.py` 平台包装。`tools/build_scripts/README.md:3`
- 构建输出与临时日志位于 `tools/release/work` 与 `tools/release/dist`。`tools/build_scripts/README.md:7`
- 私有凭证位于 `tools/release/secrets`。`tools/build_scripts/README.md:8`
- 本页只依据 10 个 seed 文件；`build_scripts/` 共 38 个文件，其余 28 个不在本页覆盖范围内。`tools/build_scripts/README.md:47`

## AI 速览

- `release_asset_name` — 拼出版本化发布包文件名。`tools/build_scripts/release_artifacts.py:61`
- `release_version` — 读取并校验 App 与 CLI 共用的单一发布版本。`tools/build_scripts/release_artifacts.py:42`
- `validate_release_assets` — 拒绝文件名不在当前版本命名集合内的资产。`tools/build_scripts/release_artifacts.py:87`
- `build_local.py` 的 `main` — 当前宿主构建入口。`tools/build_scripts/build_local.py:98`
- `build_flutter_android.py` 的 `main` — Android 构建入口。`tools/build_scripts/build_flutter_android.py:118`
- `build_flutter_windows.py` 的 `main` — Windows Flutter 构建入口。`tools/build_scripts/build_flutter_windows.py:30`
- `build_cli_windows.py` 的 `main` — Windows CLI 构建入口。`tools/build_scripts/build_cli_windows.py:16`
- `build_esp32` — ESP32 固件构建与打包入口。`tools/build_scripts/build_esp32.py:137`
- `build_windows_msi` — Windows MSI 打包入口。`tools/build_scripts/build_windows_msi.py:103`
- `cargo_build_environment` — 为 Cargo 调用构造环境变量。`tools/build_scripts/cargo_build.py:15`
- `flutter_command` — 返回 FVM 配置锁定的 Flutter SDK 中的 `flutter`。`tools/build_scripts/common.py:155`
- 主入口函数为 `build_local.py` 的 `main`。`tools/build_scripts/build_local.py:98`
- 数据流向一句话：Android APK 以 `release_asset_name("app", "android", "arm64-v8a", "apk")` 命名发布到 `dist_dir`。`tools/build_scripts/build_flutter_android.py:111`

## 核心机制

### 命名规则

- 脚本按 product、platform 或 operation 命名。`tools/build_scripts/README.md:3`
- 本地构建与 GitHub Actions 共用同一批 Python 入口。`tools/build_scripts/README.md:2`
- 构建脚本不设 `_action.py` / `_local.py` 平台包装。`tools/build_scripts/README.md:4`
- 发布包文件名规则是 `operit2-<product>-<platform>-<architecture>-<release-version>.<extension>`。`tools/build_scripts/README.md:12`
- 发布包文件名由 `operit2-{product}-{platform}-{arch}{suffix}-{release_version()}.{extension}` 拼出。`tools/build_scripts/release_artifacts.py:74`
- `release_version` 读取并校验 App 与 CLI 共用的单一发布版本。`tools/build_scripts/release_artifacts.py:42`
- 发布版本的来源之一是 `core/crates/runtime/application/Cargo.toml`。`tools/build_scripts/release_artifacts.py:10`
- 发布版本的来源之二是 `apps/cli/Cargo.toml`。`tools/build_scripts/release_artifacts.py:11`
- `versions[0]` 与 `versions[1]` 不一致时抛错。`tools/build_scripts/release_artifacts.py:56`
- 支持的发布扩展名只有 `apk`、`hap`、`zip`、`tar.gz`、`pkg`、`ipa`、`msi`。`tools/build_scripts/release_artifacts.py:65`
- macOS App 的 `build_type` 缺省为 `sandbox`。`tools/build_scripts/release_artifacts.py:68`
- macOS App 的 `build_type` 只接受 `sandbox` 或 `unsandbox`。`tools/build_scripts/release_artifacts.py:69`
- `build_type` 只适用于 macOS App 包，其他产品传入 `build_type` 时抛错。`tools/build_scripts/release_artifacts.py:71`
- macOS App 包使用 `operit2-app-macos-universal-<sandbox|unsandbox>-<release-version>.zip`。`tools/build_scripts/README.md:15`
- 沙箱 App Store 安装器沿用同一命名规则，扩展名为 `.pkg`。`tools/build_scripts/README.md:16`
- macOS CLI 包保留目标架构并使用 `.tar.gz` 命名。`tools/build_scripts/README.md:17`
- 构建与校验脚本不得为发布包另写 `.sha256` 文件或 `SHA256SUMS` 清单。`tools/build_scripts/README.md:18`
- `validate_release_assets` 拒绝文件名不在当前版本命名集合内的资产。`tools/build_scripts/release_artifacts.py:87`
- `RELEASE_TARGETS` 列出发布资产的目标组合，含产品、平台、架构与扩展名。`tools/build_scripts/release_artifacts.py:13`

### Flutter 构建入口

- `build_flutter_<platform>.py` 覆盖 Android、iOS、Linux、macOS、OpenHarmony、Windows 六个平台的 Flutter 构建。`tools/build_scripts/README.md:23`
- `build_flutter_macos.py` 缺省为 `sandbox`。`tools/build_scripts/README.md:158`
- Android 构建执行 `flutter build apk --release --split-per-abi`。`tools/build_scripts/build_flutter_android.py:133`
- Android 构建限定 `--target-platform android-arm64`。`tools/build_scripts/build_flutter_android.py:139`
- Android 构建传入 `--android-project-arg=operitRuntime=app`。`tools/build_scripts/build_flutter_android.py:140`
- Android 构建产物为 `app-arm64-v8a-release.apk`。`tools/build_scripts/build_flutter_android.py:154`
- 普通 Android App 发布包不得包含 `operit-android-module.json`。`tools/build_scripts/build_flutter_android.py:86`
- Android APK 以 `release_asset_name("app", "android", "arm64-v8a", "apk")` 命名发布。`tools/build_scripts/build_flutter_android.py:111`
- `--impeller-backend` 只接受 `vulkan` 或 `opengles`。`tools/build_scripts/build_flutter_android.py:72`
- `ensure_android_signing` 在缺失 Android 签名属性时抛错。`tools/build_scripts/build_flutter_android.py:25`
- `ensure_android_signing` 读取 `RELEASE_DIR` 下 `secrets/android-signing.properties`。`tools/build_scripts/build_flutter_android.py:26`
- `configure_android_flutter_sdk` 把 FVM 选定的 Flutter SDK 写入 `ANDROID_LOCAL_PROPERTIES`。`tools/build_scripts/build_flutter_android.py:45`
- Windows Flutter 构建执行 `flutter build windows --release --no-pub`。`tools/build_scripts/build_flutter_windows.py:33`
- Windows 发布目录为 `build/windows/x64/runner/Release`。`tools/build_scripts/build_flutter_windows.py:38`
- Windows App 归档默认名为 `release_asset_name("app", "windows", "x86_64", "zip")`。`tools/build_scripts/build_flutter_windows.py:40`
- Windows MSI 路径缺省为归档路径换 `.msi` 后缀。`tools/build_scripts/build_flutter_windows.py:41`
- Windows Flutter 构建调用 `build_windows_msi` 生成安装器。`tools/build_scripts/build_flutter_windows.py:42`

### CLI 构建入口

- `build_cli_<platform>.py` 覆盖 Linux、macOS、Windows 三个平台的 CLI 构建。`tools/build_scripts/README.md:25`
- `build_cli_current.py` 构建当前宿主平台的 CLI。`tools/build_scripts/README.md:26`
- `build_cli_linux_debian12.py` 在 Debian 12 容器内构建 glibc 2.36 兼容的 Linux CLI。`tools/build_scripts/README.md:27`
- `build_cli_windows.py` 的 `--arches` 缺省为 `host`，可选 `host`、`all`、`x86_64`、`aarch64`。`tools/build_scripts/build_cli_windows.py:11`
- `build_cli_windows.py` 的 `main` 调用 `build_cli_platform("windows", parse_cli_arch_mode(args.arches))`。`tools/build_scripts/build_cli_windows.py:18`

### ESP32 构建入口

- `build_esp32.py` 是 ESP32 固件构建器。`tools/build_scripts/README.md:30`
- ESP32 固件默认归档名为 `release_asset_name("firmware", "esp32", "2432s028", "zip")`。`tools/build_scripts/build_esp32.py:18`
- `IMAGE_SPECS` 定义四张镜像及其烧录偏移。`tools/build_scripts/build_esp32.py:19`
- `operit-esp32-4mb-full.bin` 烧录于 `0x000000`。`tools/build_scripts/build_esp32.py:20`
- `bootloader.bin` 烧录于 `0x001000`。`tools/build_scripts/build_esp32.py:21`
- `partition-table.bin` 烧录于 `0x008000`。`tools/build_scripts/build_esp32.py:22`
- `operit-esp32.bin` 烧录于 `0x010000`。`tools/build_scripts/build_esp32.py:23`
- ESP32 构建要求 `EMSDK` 指向已安装的 Emscripten SDK，否则抛错。`tools/build_scripts/build_esp32.py:46`
- `npm run build:firmware` 在 `EDITOR_DIR` 执行。`tools/build_scripts/build_esp32.py:54`
- 固件清单的 `firmwareBuilt` 必须为 `True`，否则抛错。`tools/build_scripts/build_esp32.py:63`
- `package_manifest` 的 `format` 为 `operit2-esp32-firmware`，`board` 为 `ESP32-2432S028`。`tools/build_scripts/build_esp32.py:93`

### Windows MSI 打包

- MSI 打包细节见 [[tools-windows-installer|Windows MSI 安装器与卸载数据清理]]。`tools/build_scripts/build_windows_msi.py:103`
- `msi_version` 把 SemVer 通道映射为严格递增的 Windows Installer 版本。`tools/build_scripts/build_windows_msi.py:32`
- 预发布计数器 `counter` 不超过 199。`tools/build_scripts/build_windows_msi.py:40`
- `build_windows_msi` 独立入口的默认目标为 `release_asset_name("app", "windows", "x86_64", "msi")`。`tools/build_scripts/build_windows_msi.py:146`
- `REQUIRED_FILES` 列出 MSI 载荷的必需文件。`tools/build_scripts/build_windows_msi.py:23`
- `build_windows_msi.py` 的 `main` 以共享发布资产命名打包选定的发布目录。`tools/build_scripts/build_windows_msi.py:144`

### 当前宿主分发器

- `build_local.py` 是当前宿主的 App/CLI/ESP32 分发器。`tools/build_scripts/README.md:28`
- `PRODUCT_CHOICES` 为 `app`、`cli`、`esp32`、`all`。`tools/build_scripts/build_local.py:14`
- `MACOS_TYPES` 为 `sandbox`、`unsandbox`。`tools/build_scripts/build_local.py:15`
- `build_local.py` 的 `--products` 缺省为 `all`。`tools/build_scripts/build_local.py:22`
- `build_local.py` 的 `--macos-type` 缺省为 `sandbox`。`tools/build_scripts/build_local.py:24`
- `build_script` 按 `{name}_{platform_name}.py` 拼出平台构建脚本路径。`tools/build_scripts/build_local.py:32`
- Windows 本地 App 归档为 `release_asset_name("app", "windows", architecture, "zip")`。`tools/build_scripts/build_local.py:39`
- Linux 本地 App 归档为 `release_asset_name("app", "linux", architecture, "tar.gz")`。`tools/build_scripts/build_local.py:41`
- macOS 本地 App 归档为 `release_asset_name("app", "macos", "universal", "zip", macos_type)`。`tools/build_scripts/build_local.py:43`
- `--include-ios` 只在 macOS 宿主上可用。`tools/build_scripts/build_local.py:100`
- `--include-ios` 要求 `args.products` 为 `app`。`tools/build_scripts/build_local.py:102`
- `args.products` 为 `esp32` 时调用 `build_esp32()`。`tools/build_scripts/build_local.py:117`
- `main` 用 `host_platform()` 判定当前宿主平台。`tools/build_scripts/build_local.py:99`
- `check_local_environment` 调用 `check_build_environment.py` 检查本地环境。`tools/build_scripts/build_local.py:83`
- `RUSTFLAGS` 被设为 `-Awarnings`。`tools/build_scripts/build_local.py:109`

### 共享 helper 与 Cargo 环境

- `common.py`、`cli_common.py` 与 `appstore_connect_common.py` 是共享 helper。`tools/build_scripts/README.md:34`
- `check_build_environment.py` 是本地与 CI 共用的环境检查器。`tools/build_scripts/README.md:33`
- `common.py` 的 `DIST_DIR` 指向 `RELEASE_DIR` 下的 `dist` 目录。`tools/build_scripts/common.py:19`
- `common.py` 的 `FLUTTER_APP_DIR` 指向 `apps/flutter/app`。`tools/build_scripts/common.py:17`
- `common.py` 的 `REPO_ROOT` 是脚本目录的上两级。`tools/build_scripts/common.py:16`
- `host_platform` 把 `darwin` 映射为 `macos`，`windows` 映射为 `windows`，`linux` 映射为 `linux`。`tools/build_scripts/common.py:112`
- `host_arch` 把 `amd64`/`x86_64` 映射为 `x86_64`，把 `arm64`/`aarch64` 映射为 `aarch64`。`tools/build_scripts/common.py:121`
- `flutter_command` 返回 FVM 配置锁定的 Flutter SDK 中的 `flutter`。`tools/build_scripts/common.py:155`
- `prepare_plugin_assets` 先调用 `prepare_python_command` 再执行同步脚本。`tools/build_scripts/common.py:284`
- `PLUGIN_SYNC_SCRIPT` 以 `--source runtime --no-hot-reload` 参数运行。`tools/build_scripts/common.py:292`
- `prepare_plugin_assets` 在 `common.py` 中运行，CLI 入口在 `cargo build` 前调用它，Flutter 构建从原生钩子触发它。`tools/build_scripts/README.md:70`
- `verify_cli_plugin_assets` 在打包的 CLI 二进制缺失已生成插件资产时抛错。`tools/build_scripts/common.py:325`
- `compress_zip` 把目录压缩为 ZIP。`tools/build_scripts/common.py:90`
- `compress_tar_gz` 以 `"w:gz"` 模式把目录压缩为 tar.gz 归档。`tools/build_scripts/common.py:102`
- `flutter_pub_get` 用 `fvm flutter pub get` 解析依赖，支持 `--enforce-lockfile`。`tools/build_scripts/common.py:360`
- `generate_dart_proxy_artifacts` 先 `cargo check` proxy 本地 crate 再校验生成的 Dart 代理文件存在。`tools/build_scripts/common.py:341`
- `cargo_build_environment` 为 Cargo 调用构造环境变量。`tools/build_scripts/cargo_build.py:15`
- 路径映射以 `--remap-path-prefix` 标志加入 `flags`。`tools/build_scripts/cargo_build.py:64`
- 映射后的标志写入 `CARGO_ENCODED_RUSTFLAGS` 并删除 `RUSTFLAGS`。`tools/build_scripts/cargo_build.py:67`
- `cargo_build.py` 的 `main` 要求至少一个命令行参数，否则打印用法并退出。`tools/build_scripts/cargo_build.py:72`

### 其他入口

- `build_android_module.py` 转发到 `apps/android-module/build.py`，其规范输出是一个模块文件夹。`tools/build_scripts/README.md:31`
- `build_android_module_release.py` 把模块文件夹构建并打包为 `operit2-module-android-arm64-v8a-<release-version>.zip`。`tools/build_scripts/README.md:32`
- `build_apple_release.py` 是 Apple 发布资产分发器。`tools/build_scripts/README.md:29`

## 关键符号

- `release_asset_name` — 拼出版本化发布包文件名。`tools/build_scripts/release_artifacts.py:61`
- `release_version` — 读取并校验 App 与 CLI 共用的单一发布版本。`tools/build_scripts/release_artifacts.py:42`
- `validate_release_assets` — 拒绝文件名不在当前版本命名集合内的资产。`tools/build_scripts/release_artifacts.py:87`
- `RELEASE_TARGETS` — 列出发布资产的目标组合，含产品、平台、架构与扩展名。`tools/build_scripts/release_artifacts.py:13`
- `main`（`build_local.py`）— 当前宿主构建的入口。`tools/build_scripts/build_local.py:98`
- `build_script` — 按 `{name}_{platform_name}.py` 拼出平台构建脚本路径。`tools/build_scripts/build_local.py:32`
- `ensure_android_signing` — 在缺失 Android 签名属性时抛错。`tools/build_scripts/build_flutter_android.py:25`
- `configure_android_flutter_sdk` — 把 FVM 选定的 Flutter SDK 写入 `ANDROID_LOCAL_PROPERTIES`。`tools/build_scripts/build_flutter_android.py:45`
- `verify_android_runtime_assets` — 校验 APK 运行时资产与请求 ABI 一致。`tools/build_scripts/build_flutter_android.py:83`
- `publish_android_apk` — 把 APK 复制到 `dist_dir` 并以共享命名发布。`tools/build_scripts/build_flutter_android.py:110`
- `build_windows_msi` — 把 Windows 发布目录打包为 MSI。`tools/build_scripts/build_windows_msi.py:103`
- `msi_version` — 把 SemVer 通道映射为严格递增的 Windows Installer 版本。`tools/build_scripts/build_windows_msi.py:32`
- `build_esp32` — 依次执行固件构建、清单校验与归档打包。`tools/build_scripts/build_esp32.py:137`
- `image_metadata` — 校验镜像文件存在且非空并返回包元数据。`tools/build_scripts/build_esp32.py:70`
- `write_archive` — 把镜像、分区表与清单写入固件归档。`tools/build_scripts/build_esp32.py:108`
- `sha256_file` — 计算单个固件包文件的 SHA-256 摘要。`tools/build_scripts/build_esp32.py:35`
- `host_platform` — 把 `darwin` 映射为 `macos`，`windows` 映射为 `windows`，`linux` 映射为 `linux`。`tools/build_scripts/common.py:112`
- `host_arch` — 把 `amd64`/`x86_64` 映射为 `x86_64`，把 `arm64`/`aarch64` 映射为 `aarch64`。`tools/build_scripts/common.py:121`
- `flutter_command` — 返回 FVM 配置锁定的 Flutter SDK 中的 `flutter`。`tools/build_scripts/common.py:155`
- `prepare_plugin_assets` — 先调用 `prepare_python_command` 再执行同步脚本。`tools/build_scripts/common.py:284`
- `verify_cli_plugin_assets` — 在打包的 CLI 二进制缺失已生成插件资产时抛错。`tools/build_scripts/common.py:325`
- `cargo_build_environment` — 为 Cargo 调用构造环境变量。`tools/build_scripts/cargo_build.py:15`
- `run` — 执行一条构建命令。`tools/build_scripts/common.py:30`
- `require_command` — 在命令不可用时抛错。`tools/build_scripts/common.py:69`
- `copy_required_file` — 在源文件缺失时抛错并复制文件。`tools/build_scripts/common.py:82`

## 调用链

1. `build_local.py` 的 `main` 用 `host_platform()` 判定当前宿主平台。`tools/build_scripts/build_local.py:99`
2. `build_local.py` 的 `main` 是当前宿主构建的入口。`tools/build_scripts/build_local.py:98`
3. `build_script` 按 `{name}_{platform_name}.py` 拼出平台构建脚本路径。`tools/build_scripts/build_local.py:32`
4. Android 构建执行 `flutter build apk --release --split-per-abi`。`tools/build_scripts/build_flutter_android.py:133`
5. `verify_android_runtime_assets` 校验 APK 运行时资产与请求 ABI 一致。`tools/build_scripts/build_flutter_android.py:83`
6. `publish_android_apk` 把 APK 复制到 `dist_dir` 并以共享命名发布。`tools/build_scripts/build_flutter_android.py:110`
7. Windows Flutter 构建调用 `build_windows_msi` 生成安装器。`tools/build_scripts/build_flutter_windows.py:42`
8. `args.products` 为 `esp32` 时调用 `build_esp32()`。`tools/build_scripts/build_local.py:117`
9. `build_esp32` 依次执行固件构建、清单校验与归档打包。`tools/build_scripts/build_esp32.py:137`
10. 映射后的标志写入 `CARGO_ENCODED_RUSTFLAGS` 并删除 `RUSTFLAGS`。`tools/build_scripts/cargo_build.py:67`

## 来源

- `tools/build_scripts/README.md`
- `tools/build_scripts/build_flutter_android.py`
- `tools/build_scripts/build_flutter_windows.py`
- `tools/build_scripts/build_cli_windows.py`
- `tools/build_scripts/build_windows_msi.py`
- `tools/build_scripts/build_esp32.py`
- `tools/build_scripts/build_local.py`
- `tools/build_scripts/cargo_build.py`
- `tools/build_scripts/common.py`
- `tools/build_scripts/release_artifacts.py`
