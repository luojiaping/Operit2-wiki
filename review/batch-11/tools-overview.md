---
title: tools 总览
module: tools
platforms: [all]
sources: 1
date: 2026-11-11
---

## 概述

- 本页只覆盖 tools/build_scripts/ 的构建脚本入口与规则，seed 文件是 `tools/build_scripts/README.md`。`tools/build_scripts/README.md:1`
- 本地构建与 GitHub Actions 使用同一批 Python 入口。`tools/build_scripts/README.md:3`
- 脚本按产品、平台或操作命名，不设单独的 `_action.py` 与 `_local.py` 平台包装。`tools/build_scripts/README.md:5`
- 构建产物与临时日志归入 `tools/release/work` 与 `tools/release/dist`。`tools/build_scripts/README.md:7`
- 私密凭据归入 `tools/release/secrets`。`tools/build_scripts/README.md:8`
- `tools/release/work`、`tools/release/dist`、`tools/release/secrets` 是被忽略的目录，不用于存放可复用的构建脚本。`tools/build_scripts/README.md:9`
- 发布包文件名使用 `operit2-<product>-<platform>-<architecture>-<release-version>.<extension>` 规则。`tools/build_scripts/README.md:12`
- 构建脚本的入口细节见 [[tools-build-scripts|构建脚本入口]]，发布流程见 [[tools-release|发布流程]]。`tools/build_scripts/README.md:1`

## AI 速览

- `build_flutter_<platform>.py` — Flutter 构建入口，覆盖 Android、iOS、Linux、macOS、OpenHarmony、Windows。`tools/build_scripts/README.md:23`
- `build_cli_<platform>.py` — CLI 构建入口，覆盖 Linux、macOS、Windows。`tools/build_scripts/README.md:25`
- `build_cli_current.py` — 当前宿主平台的 CLI 构建。`tools/build_scripts/README.md:26`
- `build_cli_linux_debian12.py` — Debian 12 容器内 glibc 2.36 兼容的 Linux CLI 构建。`tools/build_scripts/README.md:27`
- `build_local.py` — 当前宿主 App/CLI/ESP32 分发器。`tools/build_scripts/README.md:28`
- `build_apple_release.py` — Apple 发布产物分发器。`tools/build_scripts/README.md:29`
- `build_esp32.py` — ESP32 固件构建器。`tools/build_scripts/README.md:30`
- `build_android_module.py` — 转发给 `apps/android-module/build.py` 的 Android 模块构建。`tools/build_scripts/README.md:31`
- `build_android_module_release.py` — Android 模块发布打包，产出安装器 ZIP。`tools/build_scripts/README.md:32`
- `check_build_environment.py` — 本地与 CI 共用的环境检查器。`tools/build_scripts/README.md:33`
- `common.py`、`cli_common.py`、`appstore_connect_common.py` — 共享辅助模块。`tools/build_scripts/README.md:34`
- `release_artifacts.py` — 校验共享的 App 运行时版本与 CLI 版本。`tools/build_scripts/README.md:13`
- `prepare_plugin_assets()` — 生成并同步 ToolPkg 资产。`tools/build_scripts/README.md:70`
- `verify_cli_plugin_assets()` — 校验打包 CLI 的资产完整性。`tools/build_scripts/README.md:73`
- `run_cli.py` — 本地运行 CLI 并恢复已配置的签名身份。`tools/build_scripts/README.md:319`
- `sign_macos.py` — macOS 沙箱与非沙箱应用签名。`tools/build_scripts/README.md:141`
- 主入口：本地分发是 `build_local.py`。`tools/build_scripts/README.md:28`
- 数据流向：入口脚本 → 平台构建 → 中间产物进 `tools/release/work`，发布包进 `tools/release/dist`，凭据进 `tools/release/secrets`。`tools/build_scripts/README.md:7`

## 核心机制

- 本地构建与 GitHub Actions 共用同一批 Python 入口，脚本按产品、平台或操作命名。`tools/build_scripts/README.md:3`
- `release_artifacts.py` 校验共享的 App 运行时版本与 CLI 版本，并保留预发布标识符与复合扩展名。`tools/build_scripts/README.md:13`
- macOS App 包使用 `operit2-app-macos-universal-<sandbox|unsandbox>-<release-version>.zip` 命名。`tools/build_scripts/README.md:15`
- 沙箱 App Store 安装器沿用同一命名规则，后缀为 `.pkg`。`tools/build_scripts/README.md:16`
- macOS CLI 包保留目标架构与 `.tar.gz` 命名。`tools/build_scripts/README.md:17`
- 构建与校验脚本不得为发布包另写单独的 `.sha256` 文件或 `SHA256SUMS` 列表。`tools/build_scripts/README.md:18`
- 校验结果可以在已有的构建清单里包含哈希。`tools/build_scripts/README.md:19`
- App/完整发布运行与 GitHub Actions 的 Android Flutter Build 同时包含普通 Android APK 与 Android 模块 ZIP。`tools/build_scripts/README.md:36`
- 两者串行构建，使用同一平台构建名/构建号与各自的 `operitRuntime` 值。`tools/build_scripts/README.md:38`
- 模块的 `module.prop` 使用共享的 Cargo 发布版本与 Flutter 构建号作为 `versionCode`。`tools/build_scripts/README.md:40`
- 模块文件夹保留在 `tools/release/work/android-module/module-arm64-v8a`，只有安装器 ZIP 暂存到 `tools/release/dist`。`tools/build_scripts/README.md:41`
- 模块文件夹根目录直接包含 `module.prop`。`tools/build_scripts/README.md:42`
- 仅构建模块发布包时使用 `build_android_module_release.py --enforce-lockfile`。`tools/build_scripts/README.md:47`
- 该命令要求与普通 APK 相同的 Android 签名材料与构建前置条件，且只构建包、不安装到手机。`tools/build_scripts/README.md:50`
- Windows App ZIP/MSI 与 CLI ZIP 包内含校验和锁定的 PortableGit 运行时，位于 `bash/` 目录，包含上游许可证。`tools/build_scripts/README.md:55`
- Windows 宿主在可执行文件旁启动 `bash/bin/bash.exe`，不要求系统安装 Git 或 Git 在 PATH 上。`tools/build_scripts/README.md:57`
- x86_64 与 aarch64 的 CLI 包各自暂存对应的运行时。`tools/build_scripts/README.md:58`
- Flutter 的常规 Windows CMake 构建为 Debug、Profile 与 Release 暂存该运行时，包括 `fvm flutter run -d windows`。`tools/build_scripts/README.md:60`
- Dart-only 构建不重新复制完整运行时，也不为准备 Bash 而重新构建 Rust。`tools/build_scripts/README.md:61`
- 缺失必需的运行时文件会再次触发准备。`tools/build_scripts/README.md:62`
- 同一准备脚本可以用 `windows_bash.py --destination <binary-directory>` 为独立开发二进制暂存运行时。`tools/build_scripts/README.md:64`
- 每次 App/CLI 构建把从 `plugins/packages/` 生成的 ToolPkg 资产嵌入 `core/crates/runtime/application/assets/plugins/{buildin,external}`。`tools/build_scripts/README.md:68`
- `common.py` 里的 `prepare_plugin_assets()` 运行 `plugins/tools/sync_plugin_packages.py --source runtime --no-hot-reload`。`tools/build_scripts/README.md:70`
- CLI 入口在 `cargo build` 之前调用 `prepare_plugin_assets()`，Flutter 构建从原生钩子触发它。`tools/build_scripts/README.md:72`
- `verify_cli_plugin_assets()` 拒绝打包后二进制缺失任一已生成资产名的 CLI。`tools/build_scripts/README.md:73`
- 不得提交或跨机器复用陈旧的资产目录。`tools/build_scripts/README.md:74`
- HAP 构建使用 OHOS 工程 `local.properties` 里配置的 API 18 原生 SDK 与 PATH 上的当前 `ld.lld`。`tools/build_scripts/README.md:79`
- V8 的 Chromium 编译器产生 ELF CREL 重定位，SDK 自带的 LLD 15 无法读取。`tools/build_scripts/README.md:81`
- 最终 Rust 链接使用选定的 LLD 与 SDK sysroot 及编译器内置库，并拒绝未定义符号。`tools/build_scripts/README.md:82`
- 通过 `RUSTY_V8_ARCHIVE` 与 `RUSTY_V8_SRC_BINDING_PATH` 为选定目标提供 V8 归档及其匹配的已生成 Rust 绑定。`tools/build_scripts/README.md:87`
- `RUSTY_V8_ARCHIVE_SHA256` 设为该归档的 SHA-256。`tools/build_scripts/README.md:88`
- 两件产物必须来自锁定的 V8 版本并针对 OHOS sysroot 构建；Android 与 GNU/Linux 产物是不同的 ABI。`tools/build_scripts/README.md:89`
- 本地原生源码缓存可通过 `OPERIT_LLAMA_SOURCE`、`OPERIT_MNN_SOURCE` 与 `OPERIT_KLEIDIAI_SOURCE` 提供（KleidiAI 1.16.0 对应 MNN 3.6.1）。`tools/build_scripts/README.md:92`
- 这些路径使用 CMake 风格的正斜杠。`tools/build_scripts/README.md:94`
- OHOS 引擎使用 SDK 的 C++ 头文件，把命名空间与 SDK 的 `__n1` ABI 对齐，并用 `sched_setaffinity` 设置推理线程亲和性。`tools/build_scripts/README.md:95`
- OHOS 静态 C++ 运行时保持私有，仅通过三个导出的推理 C 函数暴露。`tools/build_scripts/README.md:96`
- 打包同时包含 `liboperit_flutter_bridge.so` 与 `liboperit_local_llm.so`。`tools/build_scripts/README.md:97`
- 入口模块启用 `compressNativeLibs`，使 HAP 以压缩方式存放共享库。`tools/build_scripts/README.md:100`
- 签名前终端打包在两个已声明包里保留 `qemu-harmonix-aarch64`、其传递 `DT_NEEDED` 库与 HNP 元数据。`tools/build_scripts/README.md:101`
- 依赖检查排除操作系统提供的 `libc.so`，并拒绝缺失或 ELF 架构与选定目标不符的打包库。`tools/build_scripts/README.md:103`
- 全系统模拟器、x86 客户程序与 QEMU-vroot 未引用的库不进入 HAP；离线 Alpine 工具仓库仍为终端、OCR 与 PDF 能力打包。`tools/build_scripts/README.md:104`
- ARM64 设备用 `build_flutter_ohos.py --target-platform ohos-arm64 --enforce-lockfile`。`tools/build_scripts/README.md:112`
- x86_64 模拟器用 `build_flutter_ohos.py --target-platform ohos-x64 --enforce-lockfile`。`tools/build_scripts/README.md:115`
- ARM64 仍是默认目标；每个目标选择各自的 Rust triple、Flutter 引擎 HAR、CMake ABI、打包原生库、HNP 目录与输出文件名。`tools/build_scripts/README.md:118`
- Hvigor 插件读取 Flutter 的 `TARGET_PLATFORM` 参数并在内存中设置原生 ABI 过滤器。`tools/build_scripts/README.md:120`
- 两个引擎依赖保持在清单中声明；切换目标不重写架构设置，也不删除已缓存的库。`tools/build_scripts/README.md:121`
- 签名前构建检查全部必需原生库存在且每个打包的 ELF 与选定 ABI 匹配。`tools/build_scripts/README.md:123`
- 同一选择在 `apps/flutter/app` 下用 `fvm flutter build hap --target-platform ohos-x64` 也可用，前提是已暂存所需的 Rust 库、HAR 与终端包。`tools/build_scripts/README.md:125`
- x86_64 宿主 HNP 仍通过 `qemu-harmonix-aarch64` 运行共享的 ARM64 Alpine 客户机。`tools/build_scripts/README.md:128`
- 模拟器构建需在 `apps/flutter/app/ohos/entry/hnp/x86_64/` 下提供两个 HNP 文件。`tools/build_scripts/README.md:130`
- `build_flutter_macos.py` 默认类型为 `sandbox`。`tools/build_scripts/README.md:158`
- 每个 App 保留在 `tools/release/work/macos/<type>/Operit2.app`；签名读取该类型的保留 App 并写入 `tools/release/work/macos-sign/<type>/`。`tools/build_scripts/README.md:160`
- 不得改签另一类型的 App 来代替重新构建。`tools/build_scripts/README.md:162`
- 沙箱签名使用 App Store 配置文件与分发/安装器证书；非沙箱签名使用 Developer ID Application、Hardened Runtime 且不用 App Store 配置文件。`tools/build_scripts/README.md:163`
- 未传 `--notary-profile` 时，已签名的非沙箱归档尚未公证。`tools/build_scripts/README.md:165`
- 直接 `flutter run`、VS Code Run（含 profile/release）与 Xcode Runner 构建默认使用 `unsandbox`。`tools/build_scripts/README.md:168`
- 发布脚本通过临时的 `XCODE_XCCONFIG_FILE` 覆盖自定义 Runner 设置，不编辑工程，也不给 CocoaPods 框架强加应用权限。`tools/build_scripts/README.md:168`
- 已有的 xcconfig 覆盖在选定类型之前被包含。`tools/build_scripts/README.md:170`
- CI 与发布方构建两种类型；其他平台与 CLI 名称不变。`tools/build_scripts/README.md:171`
- `macos/flutter_assemble.sh` 把 `lipo` 兼容包装器限制在 Flutter assemble 内，因 Xcode 27 拒绝 Flutter 的多架构 `-verify_arch` 调用而逐个验证请求的架构。`tools/build_scripts/README.md:174`
- 除此之外的 `lipo` 命令直通选定的 Xcode 工具链；SDK 本身不变。`tools/build_scripts/README.md:176`
- 应用从运行进程签名读取隔离状态。`tools/build_scripts/README.md:179`
- 非沙箱宿主注册原生 zsh/bash 登录 PTY（带控制终端作业控制），并通过 VFS `/virtual/macos` 暴露原生 `/` 文件系统。`tools/build_scripts/README.md:180`
- 沙箱宿主保留无控制 TTY 的 PTY 适配器与文件夹书签。`tools/build_scripts/README.md:182`
- AI 权限模式与审批同时适用于两者；非沙箱仍受当前账号与 macOS 隐私权限约束。`tools/build_scripts/README.md:183`
- App Store Connect 脚本读取被忽略的文件 `tools/release/secrets/appstoreconnect/appstoreconnect.env`。`tools/build_scripts/README.md:187`
- 跟踪的构建脚本里不存放凭据。`tools/build_scripts/README.md:188`
- iOS Rust 桥在编译 Rust 之前运行 `prepare_ios_v8.py`，从源码构建桥的 `Cargo.lock` 里锁定的 V8 版本。`tools/build_scripts/README.md:192`
- 内嵌启动快照来自同一次构建，避免此前预编译 iOS 归档里不兼容的快照。`tools/build_scripts/README.md:194`
- iOS 构建使用编译期 jitless 模式，禁用 Sparkplug、Maglev 与 TurboFan；WebAssembly 通过 V8 的 DrumBrake 解释器运行。`tools/build_scripts/README.md:198`
- `patches/v8-152.2.0-ios-wasm-interpreter.patch` 在无指针压缩下支持全宽引用。`tools/build_scripts/README.md:200`
- 该辅助脚本拒绝未经评审的 V8 版本或补丁源码的意外改动；补丁摘要是缓存标识的一部分。`tools/build_scripts/README.md:203`
- 显式 DrumBrake 内存边界检查已启用，避免依赖进程级信号陷阱处理器与 8 GiB Wasm 内存保护区预留。`tools/build_scripts/README.md:207`
- iOS 上指针压缩、沙箱与 cppgc caged heap 保持禁用。`tools/build_scripts/README.md:209`
- Intl 保持启用；Temporal 被禁用，因已发布的源码 crate 省略了它的 Rust vendor 依赖。`tools/build_scripts/README.md:211`
- 当前运行时插件不使用 Temporal；这些设置属于 iOS 构建层，公共 JavaScript 调度器没有 Apple 专用的运行时分支。`tools/build_scripts/README.md:213`
- macOS 上用 `brew install llvm@23 lld@23` 安装源码构建前置条件；辅助脚本把 Homebrew 的 LLVM/libclang 与 Xcode 的 iOS 编译器运行时组合成本地工具链覆盖层。`tools/build_scripts/README.md:216`
- 辅助脚本从 V8 的 DEPS 里的确切修订版下载缺失的 ICU 数据。`tools/build_scripts/README.md:219`
- 每个 iOS 架构的首次构建耗时明显更长；后续构建复用 `tools/release/work/ios-v8/<v8-version>/<rust-target>/` 下的缓存。`tools/build_scripts/README.md:220`
- 库、绑定与 GN 参数在复用前对照配置清单与 SHA-256 哈希检查。`tools/build_scripts/README.md:221`
- 准备失败会停止构建，而不是下载旧归档；CI 缓存完整产物集并使用同一辅助脚本。`tools/build_scripts/README.md:223`
- 手动构建 iOS V8：`prepare_ios_v8.py --target aarch64-apple-ios --env-file tools/release/work/ios-v8/device.env`。`tools/build_scripts/README.md:229`
- Debug 使用常规可执行文件并做死代码剥离，禁用导出全部全局符号；已用的 WebAssembly 入口点与 Swift 引用的 Rust 桥入口点保持链接。`tools/build_scripts/README.md:233`
- iSH 运行时为其内核 `printf`/`scanf` 函数加命名空间，使宿主 V8 调用继续使用 Darwin libc；该原生回归见 `tools/ios-runtime/ish/README.md`。`tools/build_scripts/README.md:235`
- iOS V8 构建/缓存检查使用 `tools/tests` 下的 `test_ios_v8_build.py` 与 `test_apple_plugin_build.py`。`tools/build_scripts/README.md:240`
- 引擎冒烟检查使用生产宿主 JavaScript 运行时、ToolPkg WASM API、真实 USearch 模块与角色记忆适配器。`tools/build_scripts/README.md:246`
- 引擎冒烟检查覆盖标量与 i64 调用、JS 回调、SIMD、内存增长、边界陷阱、GC 引用、包导出权限与重复 realm/进程创建。`tools/build_scripts/README.md:247`
- 匹配的模拟器 V8 缓存与已启动的 iOS 模拟器是引擎冒烟检查的前提。`tools/build_scripts/README.md:249`
- `--target aarch64-apple-ios` 检查设备交叉编译与原生链接；已签名的设备执行是另一项检查。`tools/build_scripts/README.md:250`
- 运行 `run_ios_wasm_engine_smoke.py --baseline-node` 与不带该标志的版本各做一次检查。`tools/build_scripts/README.md:242`
- Android Cargo 任务使用 Android SDK 的 `cmake;3.22.1` 包提供 CMake 与 Ninja。`tools/build_scripts/README.md:256`
- Gradle 设置 `CMAKE` 并把该包的 `bin` 目录加入 Cargo 任务的 PATH；嵌入式本地推理引擎不需要全局 PATH 改动。`tools/build_scripts/README.md:258`
- 本地推理 CMake 工作树位于仓库根的 `target/local-llm/<build-id>/`；构建 ID 对完整 Cargo `OUT_DIR` 做哈希。`tools/build_scripts/README.md:262`
- 共享引擎仍落在 Cargo 桥产物旁边，供已有的打包任务使用。`tools/build_scripts/README.md:265`
- `rusty_v8` 不为 Android 目标发布预编译静态库，crate 的默认 GitHub 下载会 404 失败。`tools/build_scripts/README.md:268`
- Android Gradle 构建在编译 Rust 之前运行 `prepare_android_v8.py`，并把 `RUSTY_V8_ARCHIVE`、`RUSTY_V8_ARCHIVE_SHA256` 与 `RUSTY_V8_SRC_BINDING_PATH` 写入 env 文件，由 Cargo 编译任务应用。`tools/build_scripts/README.md:270`
- Android V8 缓存复用位置为 `tools/release/work/android-v8/<v8-version>/<rust-target>/`。`tools/build_scripts/README.md:276`
- 与 iOS 不同，Android 保留 JIT 并启用 WebAssembly；沙箱、指针压缩与 cppgc caged heap 保持禁用，以使两个移动构建使用同一内存布局。`tools/build_scripts/README.md:278`
- NDK API 级别默认为 24（与应用的 `minSdkVersion` 一致），可用 `OPERIT_ANDROID_V8_API_LEVEL` 提高；该值是缓存标识的一部分。`tools/build_scripts/README.md:282`
- Gradle 任务把选定的 `android.ndkDirectory` 作为 `OPERIT_ANDROID_V8_NDK` 传给辅助脚本。`tools/build_scripts/README.md:285`
- 独立调用要求 NDK r23+，从 `OPERIT_ANDROID_V8_NDK`、`ANDROID_NDK_HOME`、`$ANDROID_HOME/ndk` 或 `~/Android/ndk` 检测（最新匹配胜出）。`tools/build_scripts/README.md:288`
- Linux 上辅助脚本回退为下载 `rusty_v8` 构建脚本锁定的 NDK。`tools/build_scripts/README.md:290`
- 检测到的 NDK 在 crate 源码内暴露在构建脚本守卫与 GN `android_ndk_root` 默认值期望的位置，因此即使 crate 会取 Linux 专用归档也不再额外下载。`tools/build_scripts/README.md:291`
- Linux 需要 libclang 21.1+ 与 `ld.lld`；macOS 使用 Homebrew LLVM（`brew install llvm@23 lld@23`）。`tools/build_scripts/README.md:294`
- Windows 上把 `OPERIT_LIBCLANG_DIR` 设为包含 `libclang.dll` 的目录（Gradle 构建已代劳）。`tools/build_scripts/README.md:297`
- 辅助脚本在缓存下提供锁定的 `gn` 与 `ninja` 并经 `GN`/`NINJA` 传入，因 crate 自带的下载器打开直连而绕过代理环境设置。`tools/build_scripts/README.md:299`
- `armv7-linux-androideabi` 不受支持：`rusty_v8` 的构建脚本只映射 x86_64 与 aarch64 两个 Android 目标。`tools/build_scripts/README.md:301`
- Android V8 构建/缓存检查使用 `tools/tests` 下的 `test_android_v8_build.py`。`tools/build_scripts/README.md:306`
- 手动构建 Android V8：`prepare_android_v8.py --target aarch64-linux-android --env-file tools/release/work/android-v8/aarch64-linux-android.env`。`tools/build_scripts/README.md:312`
- 本地运行器 `run_cli.py` 在运行 CLI 前构建并恢复 CLI 已配置的签名身份。`tools/build_scripts/README.md:319`
- `run_cli.py --release -- cli chat list --json` 以发布模式运行 CLI。`tools/build_scripts/README.md:324`
- `run_cli.py --no-build` 不重新构建，直接签名/运行已有二进制。`tools/build_scripts/README.md:326`
- macOS 上通过 `OPERIT_MACOS_SIGNING_IDENTITY`、`run_cli.py --identity` 或 Git 忽略的 `tools/build_scripts/cli_macos_signing.local` 文件选择已有的真实签名身份。`tools/build_scripts/README.md:330`
- 本地运行器与 macOS CLI 打包使用固定标识符 `com.operit.cli`。`tools/build_scripts/README.md:337`
- README 指出，直接 `cargo build` 不执行构建后签名步骤，能把受信任产物替换为新的临时签名二进制。`tools/build_scripts/README.md:338`
- 此类构建后重新运行本地运行器。`tools/build_scripts/README.md:340`
- 新签名 CLI 的 Keychain 访问须在核对请求程序后才点 Always Allow 批准。`tools/build_scripts/README.md:340`
- 辅助脚本不导出证书/私钥、不保存密码、不改 Keychain ACL、不禁用加密偏好设置。`tools/build_scripts/README.md:343`
- 显式配置的签名失败会停止构建，而不是回退到临时签名。`tools/build_scripts/README.md:345`
- 本地签名不是公开的发布公证；公开 macOS 分发仍需合适的分发身份及其发布工作流。`tools/build_scripts/README.md:346`
- 角色卡 CLI 验收测试使用一次性配置文件；其可选 AI 夹具运行在回环地址上，并把每个功能模型（含标题与记忆生成）绑定到该端点。`tools/build_scripts/README.md:349`
- 该测试用 `python3 tools/tests/character_cards_cli_smoke.py --mock-ai` 运行。`tools/build_scripts/README.md:354`
- Flutter 直接 `build macos` 与 `run -d macos` 可通过可选的 Git 忽略文件 `apps/flutter/app/macos/Runner/Configs/Signing.local.xcconfig` 使用已有的稳定证书。`tools/build_scripts/README.md:360`
- `Signing.local.xcconfig` 设置 `CODE_SIGN_IDENTITY`、`OPERIT_CODE_SIGN_STYLE = Manual` 与 `DEVELOPMENT_TEAM`。`tools/build_scripts/README.md:364`
- 该配置保留应用自身的 bundle 标识符与选定的分发权限。`tools/build_scripts/README.md:369`
- 直接运行选择 `unsandbox`；打包脚本选择各自显式的类型。`tools/build_scripts/README.md:370`
- 没有该本地文件时保留工程已有的临时签名行为。`tools/build_scripts/README.md:371`
- 此前未授权的证书首次 Keychain 访问仍须用户批准，该配置无法绕过这一权限。`tools/build_scripts/README.md:373`
- `sign_macos.py --type sandbox` 为 App Store Connect 签名沙箱应用（`.pkg`）。`tools/build_scripts/README.md:141`
- `sign_macos.py --type unsandbox` 用 Developer ID 签名非沙箱应用（`.zip`）。`tools/build_scripts/README.md:144`
- `sign_macos.py --type unsandbox --notary-profile OperitDeveloperID` 使用已存入钥匙串的凭据做公证。`tools/build_scripts/README.md:146`
- `build_local.py --products app --macos-type unsandbox` 只构建不受限的 macOS 应用。`tools/build_scripts/README.md:149`
- `build_apple_release.py` 默认构建两种 macOS 类型。`tools/build_scripts/README.md:151`
- `validate_appstore.py` 校验 `.ipa`/`.pkg`。`tools/build_scripts/README.md:154`
- `upload_appstore.py` 上传 `.ipa`/`.pkg`。`tools/build_scripts/README.md:155`

## 关键符号

- `build_flutter_<platform>.py` — Flutter 构建入口。`tools/build_scripts/README.md:23`
- `build_cli_<platform>.py` — CLI 构建入口。`tools/build_scripts/README.md:25`
- `build_cli_current.py` — 当前宿主平台 CLI 构建。`tools/build_scripts/README.md:26`
- `build_cli_linux_debian12.py` — Debian 12 容器内 glibc 2.36 兼容 Linux CLI 构建。`tools/build_scripts/README.md:27`
- `build_local.py` — 当前宿主 App/CLI/ESP32 分发器。`tools/build_scripts/README.md:28`
- `build_apple_release.py` — Apple 发布产物分发器。`tools/build_scripts/README.md:29`
- `build_esp32.py` — ESP32 固件构建器。`tools/build_scripts/README.md:30`
- `build_android_module.py` — 转发给 `apps/android-module/build.py`。`tools/build_scripts/README.md:31`
- `build_android_module_release.py` — Android 模块安装器 ZIP 打包。`tools/build_scripts/README.md:32`
- `check_build_environment.py` — 本地与 CI 共用的环境检查器。`tools/build_scripts/README.md:33`
- `common.py` — 共享辅助模块，内含 `prepare_plugin_assets()`。`tools/build_scripts/README.md:70`
- `cli_common.py` — 共享辅助模块。`tools/build_scripts/README.md:34`
- `appstore_connect_common.py` — 共享辅助模块。`tools/build_scripts/README.md:34`
- `release_artifacts.py` — 发布包命名与版本校验。`tools/build_scripts/README.md:13`
- `prepare_plugin_assets()` — 运行 `plugins/tools/sync_plugin_packages.py --source runtime --no-hot-reload`。`tools/build_scripts/README.md:70`
- `verify_cli_plugin_assets()` — 拒绝资产缺失的打包 CLI。`tools/build_scripts/README.md:73`
- `prepare_ios_v8.py` — iOS V8 源码构建准备。`tools/build_scripts/README.md:192`
- `prepare_android_v8.py` — Android V8 源码构建准备。`tools/build_scripts/README.md:270`
- `run_cli.py` — 本地 CLI 运行器与签名恢复。`tools/build_scripts/README.md:319`
- `sign_macos.py` — macOS 应用签名与公证。`tools/build_scripts/README.md:141`
- `validate_appstore.py` — `.ipa`/`.pkg` 校验。`tools/build_scripts/README.md:154`
- `upload_appstore.py` — `.ipa`/`.pkg` 上传。`tools/build_scripts/README.md:155`
- `windows_bash.py` — Windows PortableGit 运行时准备。`tools/build_scripts/README.md:64`
- `RUSTY_V8_ARCHIVE` — V8 归档路径环境变量。`tools/build_scripts/README.md:87`
- `RUSTY_V8_SRC_BINDING_PATH` — V8 生成 Rust 绑定路径环境变量。`tools/build_scripts/README.md:87`
- `RUSTY_V8_ARCHIVE_SHA256` — V8 归档 SHA-256 环境变量。`tools/build_scripts/README.md:88`
- `OPERIT_ANDROID_V8_API_LEVEL` — Android V8 的 NDK API 级别。`tools/build_scripts/README.md:282`
- `OPERIT_ANDROID_V8_NDK` — Android V8 的 NDK 位置。`tools/build_scripts/README.md:285`
- `OPERIT_MACOS_SIGNING_IDENTITY` — macOS CLI 签名身份。`tools/build_scripts/README.md:330`
- `com.operit.cli` — 本地运行器与 macOS CLI 打包的固定标识符。`tools/build_scripts/README.md:337`

## 调用链

1. 本地构建与 GitHub Actions 调用同一批 Python 入口。`tools/build_scripts/README.md:3`
2. CLI 入口在 `cargo build` 之前调用 `prepare_plugin_assets()` 生成 ToolPkg 资产，Flutter 构建从原生钩子触发它。`tools/build_scripts/README.md:72`
3. iOS 构建在编译 Rust 之前运行 `prepare_ios_v8.py` 准备 V8。`tools/build_scripts/README.md:192`
4. Android Gradle 构建在编译 Rust 之前运行 `prepare_android_v8.py` 准备 V8。`tools/build_scripts/README.md:270`
5. 各平台构建产出 App、CLI 或固件，中间产物留在 `tools/release/work`。`tools/build_scripts/README.md:7`
6. 发布包按命名规则暂存到 `tools/release/dist`，凭据只放在 `tools/release/secrets`。`tools/build_scripts/README.md:8`
7. macOS 签名读取 `tools/release/work/macos/<type>/Operit2.app`，写入 `tools/release/work/macos-sign/<type>/`。`tools/build_scripts/README.md:160`
8. App Store Connect 脚本读取 `tools/release/secrets/appstoreconnect/appstoreconnect.env`。`tools/build_scripts/README.md:187`

## 来源

- seed 文件：`tools/build_scripts/README.md`，全文 374 行，已读完。`tools/build_scripts/README.md:1`
- 本页只读了该 seed 文件；该文件只说明 build_scripts 的入口与规则，未给出 `tools/` 全树的分类表，正文因此不写 `tools/` 其他子目录的分类。`tools/build_scripts/README.md:1`
- 源码基线：AAswordman/Operit2 @ `364d1d594`。`tools/build_scripts/README.md:1`
- 构建脚本入口细节见 [[tools-build-scripts|构建脚本入口]]，发布流程见 [[tools-release|发布流程]]，Windows 安装器见 [[tools-windows-installer|Windows MSI 安装器与卸载数据清理]]。`tools/build_scripts/README.md:1`
