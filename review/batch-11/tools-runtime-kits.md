---
title: 各平台运行时工具包
module: tools
platforms: [android, ios, ohos, web]
sources: 5
date: 2026-11-11
---

## 概述

Android 运行时工具包为 Android 手机准备运行时二进制文件。`tools/android-runtime/README.md:3`
iOS 运行时工具包的活动终端后端是独立的 AArch64 Linux 运行时。`tools/ios-runtime/README.md:3`
OpenHarmony 运行时工具包产出 OpenHarmony PC 终端运行时。`tools/ohos-runtime/README.md:3`
Web 运行时工具包产出面向 Web 宿主的 32 位 Buildroot V86 运行时套件。`tools/web-runtime/README.md:3`
Android 运行时工具包的构建说明在 `BUILDING.md`。`tools/android-runtime/README.md:12`

## AI 速览

`BusyBox 1.38.0` — Android 运行时二进制之一。`tools/android-runtime/README.md:5`
`Termux PRoot v5.1.107.78` — Android 运行时二进制之一。`tools/android-runtime/README.md:6`
`talloc 2.4.3` — PRoot 的依赖库。`tools/android-runtime/README.md:7`
`build_android_tools_wsl.sh` — Android 构建脚本，保持补丁与可编辑源码树同步。`tools/android-runtime/README.md:25`
`arm64` — iOS 的 Rust 终端实现标识符。`tools/ios-runtime/README.md:13`
`ios/build_arm64_runtime.sh` — 构建 iOS 的 ARM64 静态库。`tools/ios-runtime/README.md:9`
`build.sh` — iOS 的 ARM64 构建脚本，负责 host、iOS device、iOS Simulator 与 XCFramework。`tools/ios-runtime/arm64/README.md:7`
`qemu-harmonix-aarch64` — OpenHarmony 的 QEMU-vroot 可执行文件。`tools/ohos-runtime/README.md:5`
`build_vroot_hnp_linux.sh` — OpenHarmony 的 HNP 构建脚本。`tools/ohos-runtime/README.md:34`
`build_alpine_rootfs_linux.sh` — OpenHarmony 的 Alpine rootfs 构建脚本。`tools/ohos-runtime/README.md:35`
`build_v86_runtime_wsl.sh` — Web 的 V86 运行时构建脚本。`tools/web-runtime/README.md:15`
`publish_v86_runtime_r2.py` — Web 的 V86 运行时发布脚本。`tools/web-runtime/README.md:26`
`v86_runtime_smoke.mjs` — Web 的 V86 运行时冒烟测试。`tools/web-runtime/README.md:61`
Android 的构建入口是 `build_android_tools_wsl.sh`。`tools/android-runtime/README.md:25`
iOS 的 ARM64 构建入口是 `build.sh`。`tools/ios-runtime/arm64/README.md:7`
OpenHarmony 的构建入口是 `build_vroot_hnp_linux.sh` 与 `build_alpine_rootfs_linux.sh`。`tools/ohos-runtime/README.md:34`
Web 的构建入口是 `build_v86_runtime_wsl.sh`。`tools/web-runtime/README.md:15`
Android 产物去向是 `apps/flutter/app/android/app/src/main/jniLibs/<abi>/` 与 `apps/flutter/app/android/app/src/main/assets/android-runtime/<abi>/`。`tools/android-runtime/README.md:44`
iOS 产物去向是 `Runner/arm64-rootfs.tar.gz`，导入持久的 ARM64 根目录。`tools/ios-runtime/README.md:10`
OpenHarmony 的 HNP 产物去向是 `apps/flutter/app/ohos/entry/hnp/arm64-v8a/`。`tools/ohos-runtime/README.md:20`
OpenHarmony 的 Alpine 产物去向是 `apps/flutter/app/ohos/entry/src/main/resources/rawfile/ohos-vroot/`。`tools/ohos-runtime/README.md:26`
Web 产物去向是 `apps/flutter/app/web/runtime/generated/v86/`，再发布到 R2。`tools/web-runtime/README.md:24`

## 核心机制

### Android：为 Android 手机准备运行时二进制

Android 运行时工具包准备 BusyBox 1.38.0。`tools/android-runtime/README.md:5`
Android 运行时工具包准备 Termux PRoot v5.1.107.78。`tools/android-runtime/README.md:6`
Android 运行时工具包准备 talloc 2.4.3，talloc 用于 PRoot。`tools/android-runtime/README.md:7`
Android 运行时工具包准备 Bash 5.3 源码归档。`tools/android-runtime/README.md:8`
Android 运行时工具包准备 Android NDK r29-beta4，用于 WSL 构建。`tools/android-runtime/README.md:9`
Android 运行时工具包准备 Alpine v3.23 minirootfs，内含 bash、python3、Node.js 24、npm、uv、pnpm 和 ca-certificates。`tools/android-runtime/README.md:10`
Android 打包的 rootfs 内含 `/etc/resolv.conf`，其中 `nameserver` 为 223.5.5.5。`tools/android-runtime/README.md:14`
Android 的 resolv.conf 配置让新安装的 PRoot 环境解析终端命令与 MCP 进程的域名。`tools/android-runtime/README.md:15`
Android 的 resolv.conf 配置随 rootfs 生成，不对已有环境应用迁移。`tools/android-runtime/README.md:16`
Android 的 PRoot 修改位于 `tools/android-runtime/sources/termux-proot-operit` 可编辑源码树。`tools/android-runtime/README.md:22`
Android 的 `build_android_tools_wsl.sh` 在编译前保持 `patches/termux-proot-operit-android.patch` 与可编辑源码树同步。`tools/android-runtime/README.md:25`
Android 构建时补丁存在而可编辑源码树未创建，脚本从干净的 Termux PRoot 创建可编辑树并应用补丁。`tools/android-runtime/README.md:28`
Android 构建时补丁与可编辑源码树都存在，脚本从可编辑树重新生成补丁。`tools/android-runtime/README.md:29`
Android 构建时补丁不存在，脚本从干净的 Termux PRoot 创建可编辑树后写入新补丁。`tools/android-runtime/README.md:30`
Android 构建中修改 PRoot 的方式是编辑可编辑源码树，然后运行常规 PRoot 构建。`tools/android-runtime/README.md:32`
Android 构建的中间文件写在 Fedora WSL 下的 `~/.cache/operit-android-runtime/build/assistance2`。`tools/android-runtime/README.md:38`
Android 编译出的 `liboperit_busybox.so`、`liboperit_proot.so`、`liboperit_loader.so` 复制到 `apps/flutter/app/android/app/src/main/jniLibs/<abi>/`。`tools/android-runtime/README.md:44`
Android 的 `rootfs.tar.gz.bin` 与 `rootfs.tar.gz.bin.sha256` 复制到 `apps/flutter/app/android/app/src/main/assets/android-runtime/<abi>/`。`tools/android-runtime/README.md:47`

### iOS：独立的 AArch64 Linux 运行时，不是 V86

iOS 的活动终端后端是位于 `hosts/ios/linux-runtime` 的独立 AArch64 Linux 运行时。`tools/ios-runtime/README.md:3`
iOS 的 `arm64/` 负责构建、固定的 Alpine 输入、已验证的归档导入、完整开发根目录生成、静态库与 XCFramework。`tools/ios-runtime/README.md:5`
iOS 生产环境的 CPU 与 Linux 兼容代码属于宿主运行时树。`tools/ios-runtime/README.md:7`
iOS 的 ARM64 运行时实现归 `hosts/ios/linux-runtime/`，tools/ios-runtime/arm64/ 仅负责构建、下载、输入校验与可重建产物。`tools/ios-runtime/arm64/README.md:3`
iOS 的 ARM64 默认根目录固定为 Alpine 3.23.6 aarch64。`tools/ios-runtime/arm64/README.md:31`
iOS 的 Flutter Runner 通过 `ios/build_arm64_runtime.sh` 构建 ARM64 静态库。`tools/ios-runtime/README.md:9`
iOS 的 Flutter Runner 把 `Runner/arm64-rootfs.tar.gz` 导入持久的 ARM64 根目录。`tools/ios-runtime/README.md:10`
iOS 的原生桥接提供真实 PTY、流式输出、中断、窗口尺寸、共享宿主目录与 shell 会话。`tools/ios-runtime/README.md:11`
iOS 的 Rust 终端实现标识符是 `arm64`。`tools/ios-runtime/README.md:13`
iOS 运行时实现细节见 [[host-ios-linux-runtime|iOS 内嵌 ARM64 Linux 运行时（vendored）]]，活动后端是 `hosts/ios/linux-runtime` 的独立 AArch64 Linux 运行时。`tools/ios-runtime/README.md:3`
Web 的 V86 运行时套件面向 Web 宿主，是 32 位 Buildroot 套件。`tools/web-runtime/README.md:3`
iOS 原先的 iSH x86 桥接、源码获取与构建脚本、补丁与 CI 构建已被移除。`tools/ios-runtime/README.md:15`
iOS 的 `ish/` 没有活动的构建目标。`tools/ios-runtime/README.md:16`
iOS 被忽略的缓存与既往用户数据予以保留。`tools/ios-runtime/README.md:16`
iOS 的新运行时对 iSH 及其 ARM64 分支没有源码依赖或链接依赖。`tools/ios-runtime/README.md:17`
tools/web-runtime/README.md 写 iOS 使用带 Alpine rootfs 的 iSH，而不是该 V86 套件。`tools/web-runtime/README.md:10`
该 iSH 说法与 iOS 工具包的现状描述不一致：iSH x86 桥接已被移除，新运行时对 iSH 没有源码依赖或链接依赖。`tools/ios-runtime/README.md:15`
iOS 在已启动的 ARM64 模拟器上运行 `python3 tools/tests/run_arm64_simulator_smoke.py`，演练生产安装器与桥接。`tools/ios-runtime/README.md:20`
iOS 更广泛的运行时命令与当前限制见 ARM64 工具指南与运行时状态文档。`tools/ios-runtime/README.md:22`

### OpenHarmony：QEMU-vroot 与 HNP 包

OpenHarmony 运行时工具包产出 OpenHarmony PC 终端运行时。`tools/ohos-runtime/README.md:3`
OpenHarmony 运行时工具包产出 `qemu-harmonix-aarch64`，即从 Harmonix 构建的 QEMU-vroot 可执行文件。`tools/ohos-runtime/README.md:5`
OpenHarmony 运行时工具包产出一个 HNP 包，内含 QEMU-vroot 可执行文件及其 OpenHarmony 库。`tools/ohos-runtime/README.md:6`
OpenHarmony 运行时工具包产出 Alpine 3.23.6 aarch64 基础镜像，外加离线 APK 仓库与校验和。`tools/ohos-runtime/README.md:7`
OpenHarmony 终端属主通过 apk 安装 bash、python3、nodejs（Node.js 24）、npm、uv、pnpm、证书、curl、Git、SSH、Tesseract 语言数据、Poppler 与字体。`tools/ohos-runtime/README.md:8`
OpenHarmony 的软件包升级保留用户的 rootfs 与已安装软件包数据库。`tools/ohos-runtime/README.md:10`
OpenHarmony 的原始资产（`Raw assets`）在校验和（`checksum`）变化时按有界分块（`bounded chunks`）复制。`tools/ohos-runtime/README.md:12`
OpenHarmony 的解压（`Extraction`）与软件包安装（`package installation`）在首次使用终端时发生，安装成功后移除暂存区（`staging`）与已解压的 APK 仓库（`APK repository`）。`tools/ohos-runtime/README.md:13`
OpenHarmony 的活动网络 DNS 来自 OHOS 属主。`tools/ohos-runtime/README.md:14`
OpenHarmony 的 `OCR` 与 `PDF preview` 共享该终端环境（`terminal environment`）。`tools/ohos-runtime/README.md:15`
OpenHarmony 生成的 HNP 文件复制到 `apps/flutter/app/ohos/entry/hnp/arm64-v8a/`。`tools/ohos-runtime/README.md:20`
OpenHarmony 生成的 Alpine 文件复制到 `apps/flutter/app/ohos/entry/src/main/resources/rawfile/ohos-vroot/`。`tools/ohos-runtime/README.md:26`
OpenHarmony 的 HNP 输出位置与 Alpine 输出位置都是构建输出，且被 Git 忽略。`tools/ohos-runtime/README.md:29`
OpenHarmony 在 Windows 上安装 OpenHarmony SDK 后从 Fedora WSL 构建。`tools/ohos-runtime/README.md:31`
OpenHarmony 的 `build_vroot_hnp_linux.sh` 在调用时传入 `OHOS_SDK_HOME`。`tools/ohos-runtime/README.md:34`
OpenHarmony 的 `build_alpine_rootfs_linux.sh` 以 root 身份运行。`tools/ohos-runtime/README.md:35`
OpenHarmony 的 `build_vroot_hnp_linux.sh` 检出 Harmonix 提交 `2d671a26d2f049af12c3583da6403b77c3b66023`，并使用其已发布的 QEMU-vroot 补丁系列。`tools/ohos-runtime/README.md:38`
OpenHarmony 的 Harmonix 是 MIT 许可，捆绑的 QEMU 源码仍为 GPL-2.0-or-later。`tools/ohos-runtime/README.md:40`
OpenHarmony 的 rootfs 构建器要求 root 身份，使归档属主与可执行模式正确。`tools/ohos-runtime/README.md:42`
OpenHarmony 的 ARM64 集成检查在安装 qemu-user 后用 `test_rootfs_linux.sh` 运行。`tools/ohos-runtime/README.md:46`
OpenHarmony 的集成检查覆盖离线安装（`offline installation`）、用户软件包与数据保留（`user package/data preservation`）、运行时启动（runtime startup）、PDF 页序与缩放（`PDF page order/scale`），以及实际 OCR 输出（`actual OCR output`）。`tools/ohos-runtime/README.md:49`
OpenHarmony 的集成检查不模拟 OHOS 的 HNP 安装或其进程沙箱，那两项需要已连接的设备。`tools/ohos-runtime/README.md:50`

### Web：32 位 Buildroot V86 运行时套件

Web 运行时构建器产出面向 Web 宿主的 32 位 Buildroot V86 运行时套件。`tools/web-runtime/README.md:3`
Web 的 V86 内核提供 BusyBox 命令，压缩的 initramfs 提供 `node` 与 `python3` 及其运行时库。`tools/web-runtime/README.md:4`
Web 的 V86 客体内 Node 的固定离线软件包是 `lodash`、`dayjs`、`zod` 与 `uuid`。`tools/web-runtime/README.md:6`
Web 的 V86 客体内 Python 的固定离线软件包是 `requests`、`rich`、`click`、`packaging` 与 `python-dateutil`，外加其纯 Python 依赖。`tools/web-runtime/README.md:7`
Web 的 V86 客人有意不提供 `npm`、`npx`、`pip` 与 `pip3`。`tools/web-runtime/README.md:8`
Web 的 V86 串行代理在启动请求的解释器进程前传输工作区内容。`tools/web-runtime/README.md:9`
Web 的 V86 运行时通过 Fedora WSL 用 `build_v86_runtime_wsl.sh` 构建。`tools/web-runtime/README.md:15`
Web 的 V86 构建要求 Fedora 镜像安装原生 i686 工具链与 ELF 依赖解析器，含 gcc、glibc-devel.i686、patchelf、cpio 与 unzip。`tools/web-runtime/README.md:21`
Web 的 V86 构建命令把内核、压缩的 initramfs 与哈希清单写入 `apps/flutter/app/web/runtime/generated/v86/`。`tools/web-runtime/README.md:24`
Web 的 V86 运行时经验证后通过 `publish_v86_runtime_r2.py` 发布到 Web 宿主消费的不可变 R2 位置。`tools/web-runtime/README.md:26`
Web 的 V86 发布要求 `CLOUDFLARE_API_TOKEN` 对 `operit-model-assets` 有写权限。`tools/web-runtime/README.md:32`
Web 的浏览器通过 `https://models.operit.app` 读取带版本的发布，不可变响应缓存使已发布运行时 URL 不变时不再传输另一份镜像。`tools/web-runtime/README.md:34`
Web 的 V86 发布在 Fedora WSL 中使用 `assistance_web` 保存的 token，且不在 shell 命令中暴露该 token。`tools/web-runtime/README.md:37`
Web 的 V86 构建器把已验证的 Buildroot 内核、Alpine Node rootfs、Python 源码与已编译的 i686 Python 安装保存在 `~/.cache/operit-v86-runtime/buildroot-suite/`。`tools/web-runtime/README.md:44`
Web 的 V86 重复构建复用已保存的产物，不再下载或重新编译运行时。`tools/web-runtime/README.md:46`
Web 的 V86 构建在设置 `OPERIT_RUNTIME_REFRESH=1` 后有意刷新套件源码。`tools/web-runtime/README.md:51`
Web 的 V86 套件中 Node 及其 musl 依赖来自 Alpine v3.23 x86。`tools/web-runtime/README.md:56`
Web 的 V86 套件中 Node ELF 使用私有 RPATH，而不是全局 `LD_LIBRARY_PATH`。`tools/web-runtime/README.md:57`
Web 的 V86 构建器在打包前检查已安装的 Node 主版本，不回退到旧的 Node 20 镜像。`tools/web-runtime/README.md:58`
Web 的 V86 构建完成后在发布前运行 `node tools/web-runtime/v86_runtime_smoke.mjs`。`tools/web-runtime/README.md:61`
Web 的 V86 冒烟测试覆盖 Node 24、一次真实的 `node:sqlite` 查询、派生另一个 Node 进程，以及派生 glibc Python 运行时。`tools/web-runtime/README.md:62`
Web 已发布的运行时在新镜像构建、测试与发布完成前不变化。`tools/web-runtime/README.md:63`

### 构建说明在哪个 BUILDING.md

Android 的构建说明在 `BUILDING.md`。`tools/android-runtime/README.md:12`
iOS 的构建命令与当前限制见 `arm64/README.md`（ARM64 工具指南）与运行时状态文档。`tools/ios-runtime/README.md:22`
OpenHarmony 的构建步骤写在 tools/ohos-runtime/README.md，构建命令为 `build_vroot_hnp_linux.sh` 与 `build_alpine_rootfs_linux.sh`。`tools/ohos-runtime/README.md:34`
Web 的构建步骤写在 tools/web-runtime/README.md，构建命令为 `build_v86_runtime_wsl.sh`。`tools/web-runtime/README.md:15`
iOS、OpenHarmony、Web 三个目录下不存在 BUILDING.md，核验方法见 ## 来源。

## 关键符号

`BusyBox 1.38.0` — Android 运行时二进制之一。`tools/android-runtime/README.md:5`
`Termux PRoot v5.1.107.78` — Android 运行时二进制之一。`tools/android-runtime/README.md:6`
`talloc 2.4.3` — PRoot 的依赖库。`tools/android-runtime/README.md:7`
`Android NDK r29-beta4` — Android 的 WSL 构建工具链。`tools/android-runtime/README.md:9`
`BUILDING.md` — Android 运行时工具包的构建说明。`tools/android-runtime/README.md:12`
`build_android_tools_wsl.sh` — Android 构建脚本，保持补丁与可编辑源码树同步。`tools/android-runtime/README.md:25`
`patches/termux-proot-operit-android.patch` — Android 的 PRoot 补丁。`tools/android-runtime/README.md:25`
`liboperit_busybox.so` — Android 编译出的 BusyBox 动态库。`tools/android-runtime/README.md:44`
`liboperit_proot.so` — Android 编译出的 PRoot 动态库。`tools/android-runtime/README.md:44`
`liboperit_loader.so` — Android 编译出的加载器动态库。`tools/android-runtime/README.md:44`
`rootfs.tar.gz.bin` — Android 打包的 rootfs 产物。`tools/android-runtime/README.md:47`
`arm64` — iOS 的 Rust 终端实现标识符。`tools/ios-runtime/README.md:13`
`ios/build_arm64_runtime.sh` — 构建 iOS 的 ARM64 静态库。`tools/ios-runtime/README.md:9`
`Runner/arm64-rootfs.tar.gz` — iOS 导入持久 ARM64 根目录的归档。`tools/ios-runtime/README.md:10`
`run_arm64_simulator_smoke.py` — iOS 的 ARM64 模拟器冒烟测试。`tools/ios-runtime/README.md:20`
`build.sh` — iOS 的 ARM64 构建脚本。`tools/ios-runtime/arm64/README.md:7`
`qemu-harmonix-aarch64` — OpenHarmony 的 QEMU-vroot 可执行文件。`tools/ohos-runtime/README.md:5`
`build_vroot_hnp_linux.sh` — OpenHarmony 的 HNP 构建脚本。`tools/ohos-runtime/README.md:34`
`build_alpine_rootfs_linux.sh` — OpenHarmony 的 Alpine rootfs 构建脚本。`tools/ohos-runtime/README.md:35`
`test_rootfs_linux.sh` — OpenHarmony 的 ARM64 集成检查脚本。`tools/ohos-runtime/README.md:46`
`OHOS_SDK_HOME` — OpenHarmony 构建时传入的 SDK 位置。`tools/ohos-runtime/README.md:34`
`build_v86_runtime_wsl.sh` — Web 的 V86 运行时构建脚本。`tools/web-runtime/README.md:15`
`publish_v86_runtime_r2.py` — Web 的 V86 运行时发布脚本。`tools/web-runtime/README.md:26`
`publish_v86_runtime_r2_fedora.sh` — Web 的 V86 运行时 Fedora 发布脚本。`tools/web-runtime/README.md:41`
`v86_runtime_smoke.mjs` — Web 的 V86 运行时冒烟测试。`tools/web-runtime/README.md:61`
`CLOUDFLARE_API_TOKEN` — Web 的 V86 发布所需的写权限 token。`tools/web-runtime/README.md:32`
`operit-model-assets` — Web 的 V86 发布目标 R2 存储桶。`tools/web-runtime/README.md:32`
`OPERIT_RUNTIME_REFRESH` — 置 1 时有意刷新 Web 的 V86 套件源码。`tools/web-runtime/README.md:51`

## 调用链

Android：`build_android_tools_wsl.sh` 同步补丁与可编辑源码树后编译。`tools/android-runtime/README.md:25`
Android：编译产物复制到 `apps/flutter/app/android/app/src/main/jniLibs/<abi>/`，rootfs 产物复制到 `apps/flutter/app/android/app/src/main/assets/android-runtime/<abi>/`。`tools/android-runtime/README.md:44`
Android：新安装的 PRoot 环境用 rootfs 内含的 resolv.conf 解析终端命令与 MCP 进程的域名。`tools/android-runtime/README.md:15`
iOS：`build.sh` 构建 host、iOS device、iOS Simulator 与 XCFramework。`tools/ios-runtime/arm64/README.md:7`
iOS：Flutter Runner 通过 `ios/build_arm64_runtime.sh` 构建 ARM64 静态库，并把 `Runner/arm64-rootfs.tar.gz` 导入持久的 ARM64 根目录。`tools/ios-runtime/README.md:9`
iOS：原生桥接提供真实 PTY、流式输出、中断、窗口尺寸、共享宿主目录与 shell 会话。`tools/ios-runtime/README.md:11`
iOS：在已启动的 ARM64 模拟器上运行 `python3 tools/tests/run_arm64_simulator_smoke.py`，演练生产安装器与桥接。`tools/ios-runtime/README.md:20`
OpenHarmony：`build_vroot_hnp_linux.sh` 与 `build_alpine_rootfs_linux.sh` 从 Fedora WSL 构建。`tools/ohos-runtime/README.md:34`
OpenHarmony：生成的 HNP 文件复制到 `apps/flutter/app/ohos/entry/hnp/arm64-v8a/`。`tools/ohos-runtime/README.md:20`
OpenHarmony：生成的 Alpine 文件复制到 `apps/flutter/app/ohos/entry/src/main/resources/rawfile/ohos-vroot/`。`tools/ohos-runtime/README.md:26`
OpenHarmony：解压（`Extraction`）与软件包安装（`package installation`）在首次使用终端时发生，安装成功后移除暂存区（`staging`）与已解压的 APK 仓库（`APK repository`）。`tools/ohos-runtime/README.md:13`
OpenHarmony：`OCR` 与 `PDF preview` 共享该终端环境（`terminal environment`）。`tools/ohos-runtime/README.md:15`
Web：`build_v86_runtime_wsl.sh` 在 Fedora WSL 构建。`tools/web-runtime/README.md:15`
Web：构建产物（内核、压缩的 initramfs 与哈希清单）写入 `apps/flutter/app/web/runtime/generated/v86/`。`tools/web-runtime/README.md:24`
Web：构建完成后运行 `node tools/web-runtime/v86_runtime_smoke.mjs`，再发布。`tools/web-runtime/README.md:61`
Web：`publish_v86_runtime_r2.py` 把已验证的发布推到 Web 宿主消费的不可变 R2 位置。`tools/web-runtime/README.md:26`
Web：浏览器通过 `https://models.operit.app` 读取带版本的发布。`tools/web-runtime/README.md:34`
Web：串行代理在启动请求的解释器进程前传输工作区内容。`tools/web-runtime/README.md:9`

## 来源

- `tools/android-runtime/README.md`
- `tools/ios-runtime/README.md`
- `tools/ios-runtime/arm64/README.md`
- `tools/ohos-runtime/README.md`
- `tools/web-runtime/README.md`
- 源码基线：AAswordman/Operit2 @ `364d1d594`（2026-11-11）。
- 否定性结论核验方法：2026-11-12 对基线 `364d1d594` 的本地 checkout 执行 `ls tools/android-runtime/BUILDING.md tools/ios-runtime/BUILDING.md tools/ohos-runtime/BUILDING.md tools/web-runtime/BUILDING.md`，仅 `tools/android-runtime/BUILDING.md` 存在，其余三个目录下无 BUILDING.md。
