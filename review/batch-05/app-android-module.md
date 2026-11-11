---
title: Android 模块应用
module: apps
platforms: [android]
sources: [apps/android-module/README.md, apps/android-module/src/Runtime.rs, apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt, apps/android-module/build.py, apps/android-module/package/module.prop, apps/android-module/package/customize.sh, apps/android-module/package/service.sh, apps/android-module/package/action.sh, apps/android-module/package/uninstall.sh, apps/android-module/package/operit-host-ctl]
date: 2026-11-11
---

## 概述

`apps/android-module` 是与 Flutter 等入口并列的一种应用类型，复用 Core、Android Host 与 Dart 界面，产物是模块文件夹（`apps/android-module/README.md:3`）。
模块具有 Root 执行环境，系统能力通过 Host 接口提供（`apps/android-module/README.md:3`）。
模块不在 Core 或 Dart 页面中添加模块专属平台判断（`apps/android-module/README.md:3`）。
Android 模块入口与 Flutter 客户端共享 `liboperit_flutter_bridge.so`（`apps/android-module/README.md:18`）。
模块应用不再构建或打包第二份 Core ELF（`apps/android-module/README.md:18`）。
模块目录是模块 App 的标准产物，不是另一层部署项目（`apps/android-module/README.md:50`）。
Android 平台能力的具体实现继续放在 `hosts/android`（`apps/android-module/README.md:18`）。
模块业务数据位于 `/data/adb/operit2`，更新模块时保留该目录（`apps/android-module/README.md:56`）。

## AI 速览

- `ModuleMain` — app_process 入口对象，校验 Root UID 后加载共享 JNI 库（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:8`）
- `ModuleMain` 的 `main` — 模块入口函数，要求恰好 5 个参数（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:11`）
- `runRuntime` — JNI 入口，启动特权 Core（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:30`）
- `Java_app_operit_ModuleMain_runRuntime` — Rust 侧 JNI 实现（`apps/android-module/src/Runtime.rs:26`）
- `run` — 特权生命周期入口（`apps/android-module/src/Runtime.rs:290`）
- `run_core` — 装配 Core、发布客户端凭证并提供服务（`apps/android-module/src/Runtime.rs:335`）
- `prepare_environment` — 校验 rootfs 并部署运行时环境（`apps/android-module/src/Runtime.rs:168`）
- `publish_client` — 向应用沙箱发布客户端凭证（`apps/android-module/src/Runtime.rs:108`）
- `private_dir` — 创建权限 0o700 的私有目录并拒绝符号链接（`apps/android-module/src/Runtime.rs:135`）
- `write_private` — 以 0o600 临时文件加 rename 提交控制文件（`apps/android-module/src/Runtime.rs:147`）
- `ModuleEndpoint` — 客户端连接端点，protocol 为 1（`apps/android-module/src/Runtime.rs:397`）
- PlatformRuntimeFactory 的 `startBridge` — 以特权元数据启动 Core（`apps/android-module/src/Runtime.rs:383`）
- `operit-host-ctl` — 模块 supervisor 与客户端控制脚本（`apps/android-module/package/service.sh:6`）
- customize.sh — 安装脚本，安装前校验 payload 校验和（`apps/android-module/package/customize.sh:21`）
- service.sh — 开机启动 supervisor（`apps/android-module/package/service.sh:6`）
- action.sh — 执行 operit-host-ctl open 打开 Flutter Activity（`apps/android-module/package/action.sh:4`）
- uninstall.sh — 仅调用 operit-host-ctl stop 停止 Core（`apps/android-module/package/uninstall.sh:4`）
- build.py — 模块构建器，默认输出 build/module-arm64-v8a/（`apps/android-module/build.py:22`）
- module.prop — 模块元数据，id 为 `operit2`（`apps/android-module/package/module.prop:1`）
- 主入口函数是 `ModuleMain` 的 `main`（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:11`）。
- Core 在回环地址监听临时端口（`apps/android-module/src/Runtime.rs:392`）。
- Flutter Activity 连接模块启动的 Core（`apps/android-module/README.md:58`）。

## 核心机制

### 与 Flutter APK 的关系

Android 模块入口与 Flutter 客户端共享 `liboperit_flutter_bridge.so`（`apps/android-module/README.md:18`）。
构建报告声明 `separateCoreExecutable` 为 False（`apps/android-module/build.py:158`）。
模块应用不再构建或打包第二份 Core ELF（`apps/android-module/README.md:18`）。
Android 平台能力的具体实现继续放在 `hosts/android`（`apps/android-module/README.md:18`）。
构建器以 `--android-project-arg=operitRuntime=module` 构建 APK（`apps/android-module/build.py:58`）。
构建器通过现有 Android 工程和 FVM 编译共享 Dart 页面与 JNI 库（`apps/android-module/README.md:28`）。
模块不在 Core 或 Dart 页面中添加模块专属平台判断（`apps/android-module/README.md:3`）。

### Root 执行环境

模块具有 Root 执行环境，系统能力通过 Host 接口提供（`apps/android-module/README.md:3`）。
`ModuleMain` 的 `main` 校验进程 UID 为 0，否则拒绝启动（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:13`）。
特权生命周期入口要求进程 euid 为 0，否则拒绝启动（`apps/android-module/src/Runtime.rs:297`）。
Android Host 以真实 Root UID 装配 Core（`apps/android-module/README.md:58`）。
Root Core 由模块服务启动（`apps/android-module/README.md:54`）。
模块安装需要已有启用的 KernelSU mounting metamodule，安装后重启（`apps/android-module/README.md:52`）。
customize.sh 未找到 mounting metamodule 时中止安装（`apps/android-module/package/customize.sh:14`）。
KernelSU 默认的“卸载模块”策略会让应用进程看不到挂载的系统 APK（`apps/android-module/README.md:54`）。
安装后为 `app.operit` 选择自定义配置并关闭“卸载模块”（`apps/android-module/README.md:54`）。

### 构建

默认构建输出目录是 apps/android-module/build/module-arm64-v8a（`apps/android-module/build.py:22`）。
模块应用构建产物是目录，不接受 ZIP 输出（`apps/android-module/build.py:80`）。
输出目录已存在时构建器拒绝构建（`apps/android-module/build.py:82`）。
APK 模块标记为 runtime external、protocol 1、app android-module、bootstrap app_process（`apps/android-module/build.py:26`）。
APK 缺少模块标记时构建器拒绝该 APK（`apps/android-module/build.py:97`）。
APK 的 dex 中缺少 `Lapp/operit/ModuleMain;` 时构建器拒绝该 APK（`apps/android-module/build.py:100`）。
旧 trial APK 不含新的模块 JVM/JNI 入口，构建器明确拒绝复用它伪造本版产物（`apps/android-module/README.md:34`）。
旧入口 `tools/build_scripts/build_android_module.py` 仅转发到应用自己的构建器（`apps/android-module/README.md:34`）。
构建器没有独立 Core 输入，不接收 ZIP 输出（`apps/android-module/README.md:34`）。
模块要求 8 个原生库，包括 `liboperit_flutter_bridge.so`、`libflutter.so` 与 `libapp.so`（`apps/android-module/build.py:104`）。
`liboperit_flutter_bridge.so` 缺少 Java_app_operit_ModuleMain_runRuntime 入口时构建器拒绝该 APK（`apps/android-module/build.py:114`）。
APK 内 rootfs 与其 sha256 标记不一致时构建器拒绝（`apps/android-module/build.py:121`）。
构建产物 `deployment-manifest.json` 声明 format 3、moduleProtocol 1、abi arm64-v8a（`apps/android-module/build.py:138`）。
构建器在输出目录旁写与输出目录同名、后缀为 `.verification.json` 的文件（`apps/android-module/build.py:159`）。

### 发布

App 与全量发布以及 GitHub Actions 的 Android Flutter Build 同时生成普通 APK 与模块安装 ZIP（`apps/android-module/README.md:38`）。
模块发布 ZIP 的根部直接是 `module.prop`（`apps/android-module/README.md:46`）。
模块 `version` 使用共享 Cargo 发布版本（`apps/android-module/README.md:46`）。
模块 `versionCode` 使用本次 Flutter build number（`apps/android-module/README.md:46`）。
普通 APK 与模块使用相同的签名材料和平台版本（`apps/android-module/README.md:46`）。
发布脚本不向手机安装模块（`apps/android-module/README.md:46`）。
发布时 `module.prop` 的 `version` 与 `versionCode` 分别改写为发布版本与 build number，name 改写为 Operit2 Android Module（`apps/android-module/build.py:135`）。
模块 id 为 `operit2`（`apps/android-module/package/module.prop:1`）。
仓库内 module.prop 的 `version` 为 0.1.0-trial.3，`versionCode` 为 3（`apps/android-module/package/module.prop:3`）。
模块描述声明需要 mounting metamodule 与重启，且无重复 Core 可执行文件、不执行 `pm install`（`apps/android-module/package/module.prop:6`）。

### 安装

模块目录根部包含 `module.prop`、`customize.sh`、`service.sh`、`action.sh`、`uninstall.sh`、`bin/operit-host-ctl` 与 `payload/`（`apps/android-module/README.md:50`）。
模块安装仅支持 ARM64 Android（`apps/android-module/package/customize.sh:3`）。
安装前校验 `payload/archive.sha256`（`apps/android-module/package/customize.sh:21`）。
安装器从 APK 展开原生库到 system/app/Operit/lib/arm64（`apps/android-module/package/customize.sh:27`）。
安装器从 APK 展开 `rootfs.tar.gz` 到 `runtime/assets/rootfs.tar.gz`（`apps/android-module/package/customize.sh:29`）。
安装器把 APK 移到 system/app/Operit/Operit.apk（`apps/android-module/package/customize.sh:31`）。
安装后校验 `payload/installed.sha256`（`apps/android-module/package/customize.sh:32`）。
模块安装不执行 `pm install`（`apps/android-module/README.md:52`）。

### 启动与运行

service.sh 以 operit-host-ctl start 启动模块 supervisor，日志写入 `/data/adb/operit2/users/0/logs/supervisor.log`（`apps/android-module/package/service.sh:6`）。
`supervise` 等待 `sys.boot_completed` 为 1 后再启动 Core（`apps/android-module/package/operit-host-ctl:61`）。
`supervise` 等待 `sys.user.0.ce_available` 为 true 后再启动 Core（`apps/android-module/package/operit-host-ctl:65`）。
`resolve_client` 校验系统客户端已挂载，并用 `pm path` 确认 `app.operit` 指向系统 APK（`apps/android-module/package/operit-host-ctl:16`）。
`supervise` 用 `/system/bin/app_process` 以 `app.operit.ModuleMain` 启动模块入口（`apps/android-module/package/operit-host-ctl:75`）。
ModuleMain 的 `main` 要求恰好 5 个参数：deployment、data root、model、language 与 client UID（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:14`）。
模块入口从部署目录加载 `system/app/Operit/lib/arm64/liboperit_flutter_bridge.so`（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:17`）。
入口调用 JNI `runRuntime` 启动 Core，失败时以 `exitProcess(1)` 退出（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:20`）。
`run` 要求 model 与 language 均非空（`apps/android-module/src/Runtime.rs:300`）。
`run` 要求数据根目录为绝对路径（`apps/android-module/src/Runtime.rs:305`）。
`run` 以 `run/core.lock` 的排他锁保证同一模块 Core 只运行一份（`apps/android-module/src/Runtime.rs:316`）。
模块默认创建 `identity-module` 身份，bootstrap 的 confirmed 为 true，activeIdentityId 指向该身份（`apps/android-module/src/Runtime.rs:355`）。
身份 id 必须以 `identity-` 开头且仅含小写字母、数字与连字符（`apps/android-module/src/Runtime.rs:366`）。
bootstrap 的 `runtimeRoot` 与 `workspaceRoot` 与派生路径不一致时拒绝启动（`apps/android-module/src/Runtime.rs:373`）。
Core 经 PlatformRuntimeFactory 的 `startBridge` 以 `StartupMetadata::AndroidPrivileged` 启动（`apps/android-module/src/Runtime.rs:383`）。
特权启动元数据包含 model、language 与 secrets 目录（`apps/android-module/src/Runtime.rs:389`）。
无 rootfs 标记且已存在未提交 rootfs 时拒绝安装（`apps/android-module/src/Runtime.rs:202`）。
打包的 rootfs 校验和不匹配时拒绝安装（`apps/android-module/src/Runtime.rs:215`）。
rootfs 用模块自带的 `liboperit_busybox.so` 解压（`apps/android-module/src/Runtime.rs:219`）。
运行时可执行文件 busybox、bash、proot、loader 以符号链接指向模块库目录中的对应 .so（`apps/android-module/src/Runtime.rs:235`）。
环境变量 `OPERIT_ANDROID_RUNTIME_DIR` 指向运行时目录（`apps/android-module/src/Runtime.rs:268`）。
Core 监听回环地址 127.0.0.1 的临时端口（`apps/android-module/src/Runtime.rs:392`）。
客户端 token 由 `OsRng` 生成 32 字节随机数并编码为十六进制（`apps/android-module/src/Runtime.rs:394`）。
`ModuleEndpoint` 的 protocol 为 1（`apps/android-module/src/Runtime.rs:397`）。
`publish_client` 仅在 UID 属于 10000..100000 且拥有 `/data/user/0/app.operit` 沙箱时发布客户端凭证（`apps/android-module/src/Runtime.rs:111`）。
客户端凭证写入 /data/user/0/app.operit/files/host-runtime/client.json（`apps/android-module/src/Runtime.rs:123`）。
运行中的模块拒绝修改 `runtimeRoot`、`workspaceRoot`、`activeIdentityId` 与 `confirmed`（`apps/android-module/src/Runtime.rs:417`）。
Core 注册 SIGTERM 与 SIGINT 信号处理为 `terminate`（`apps/android-module/src/Runtime.rs:462`）。
Core 就绪后状态为 ready，说明独立模块 Core 正在回环上监听（`apps/android-module/src/Runtime.rs:467`）。
Core 由 LocalRuntimeTransport 的 `serve` 提供服务（`apps/android-module/src/Runtime.rs:471`）。
Core 退出时调用 `application.shutdownNow()`（`apps/android-module/src/Runtime.rs:478`）。
`run` 退出时删除 `run/client.json`、客户端凭证与 `run/core.pid`（`apps/android-module/src/Runtime.rs:328`）。
`private_dir` 创建权限 0o700 的私有目录并拒绝符号链接（`apps/android-module/src/Runtime.rs:135`）。
`write_private` 以 0o600 临时文件加 rename 提交控制文件（`apps/android-module/src/Runtime.rs:147`）。
状态写入数据根目录的 `run/status.json`（`apps/android-module/src/Runtime.rs:158`）。
Core 退出后 `supervise` 最多重试 5 次（`apps/android-module/package/operit-host-ctl:74`）。
重试间隔按尝试次数递增，为 ATTEMPT * 2 秒（`apps/android-module/package/operit-host-ctl:82`）。
action.sh 执行 operit-host-ctl open 打开 Flutter Activity（`apps/android-module/package/action.sh:4`）。
`open` 子命令启动 `app.operit/.MainActivity`（`apps/android-module/package/operit-host-ctl:87`）。
Flutter Activity 连接模块启动的 Core（`apps/android-module/README.md:58`）。

### 数据保留

模块业务数据位于 `/data/adb/operit2`，更新模块时保留该目录（`apps/android-module/README.md:56`）。
模块业务数据根目录为 `/data/adb/operit2`（`apps/android-module/package/operit-host-ctl:4`）。
替换数据分区的同包名 App 前备份其私有数据并卸载旧 App（`apps/android-module/README.md:56`）。
已安装 rootfs 与模块校验和不一致时拒绝安装并保留已有环境（`apps/android-module/src/Runtime.rs:196`）。
uninstall.sh 仅调用 operit-host-ctl stop 停止 Core（`apps/android-module/package/uninstall.sh:4`）。
`stop` 完成后报告系统客户端挂载与用户数据均保留（`apps/android-module/package/operit-host-ctl:103`）。
`status` 子命令输出 `/data/adb/operit2/run/status.json`（`apps/android-module/package/operit-host-ctl:107`）。

## 关键符号

- `ModuleMain` — app_process 入口对象（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:8`）
- `ModuleMain` 的 `main` — 入口函数，要求 5 个参数（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:11`）
- `runRuntime` — JNI 入口声明，参数为 deployment、dataRoot、model、language、clientUid（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:30`）
- `Java_app_operit_ModuleMain_runRuntime` — Rust 侧 JNI 实现（`apps/android-module/src/Runtime.rs:26`）
- `run` — 特权生命周期入口（`apps/android-module/src/Runtime.rs:290`）
- `run_core` — Core 装配与服务入口（`apps/android-module/src/Runtime.rs:335`）
- `prepare_environment` — rootfs 校验与运行时环境部署（`apps/android-module/src/Runtime.rs:168`）
- `publish_client` — 客户端凭证发布（`apps/android-module/src/Runtime.rs:108`）
- `private_dir` — 私有目录创建（`apps/android-module/src/Runtime.rs:135`）
- `write_private` — 控制文件原子提交（`apps/android-module/src/Runtime.rs:147`）
- `status` — 生命周期状态写入（`apps/android-module/src/Runtime.rs:158`）
- `terminate` — 信号处理函数，置位 STOPPING（`apps/android-module/src/Runtime.rs:103`）
- `ModuleEndpoint` — 客户端连接端点（`apps/android-module/src/Runtime.rs:397`）
- PlatformRuntimeFactory 的 `startBridge` — Core 启动（`apps/android-module/src/Runtime.rs:383`）
- `StartupMetadata::AndroidPrivileged` — 特权启动元数据（`apps/android-module/src/Runtime.rs:386`）
- LocalRuntimeTransport 的 `serve` — Core 服务循环（`apps/android-module/src/Runtime.rs:471`）
- `APP_MARKER` — APK 模块标记（`apps/android-module/build.py:26`）
- `APP_JNI` — 模块 JNI 入口名常量（`apps/android-module/build.py:27`）
- `DEFAULT_OUTPUT` — 默认构建输出目录（`apps/android-module/build.py:22`）
- `assemble` — 模块目录组装（`apps/android-module/build.py:75`）
- `build_apk` — 共享 APK 构建（`apps/android-module/build.py:48`）
- `deployment-manifest.json` — 模块部署清单（`apps/android-module/build.py:138`）
- module.prop — 模块元数据（`apps/android-module/package/module.prop:1`）
- customize.sh — 安装脚本（`apps/android-module/package/customize.sh:21`）
- service.sh — 开机 supervisor 启动脚本（`apps/android-module/package/service.sh:6`）
- action.sh — 打开 Flutter Activity 的脚本（`apps/android-module/package/action.sh:4`）
- uninstall.sh — 停止 Core 的卸载脚本（`apps/android-module/package/uninstall.sh:4`）
- `operit-host-ctl` — supervisor 与客户端控制脚本（`apps/android-module/package/service.sh:6`）
- `/data/adb/operit2` — 模块业务数据根目录（`apps/android-module/package/operit-host-ctl:4`）
- `/system/app/Operit/Operit.apk` — 挂载的系统客户端 APK 路径（`apps/android-module/package/operit-host-ctl:6`）
- `liboperit_flutter_bridge.so` — Flutter 客户端与模块共享的 JNI 库（`apps/android-module/README.md:18`）

## 调用链

1. 构建器以 `operitRuntime=module` 构建共享 APK（`apps/android-module/build.py:58`）。
2. 构建器校验 APK 模块标记（`apps/android-module/build.py:97`）。
3. 构建器校验 dex 含 `ModuleMain` 入口（`apps/android-module/build.py:100`）。
4. 构建器组装模块目录（`apps/android-module/build.py:75`）。
5. 构建器写 `deployment-manifest.json`，声明 format 3、moduleProtocol 1、abi arm64-v8a（`apps/android-module/build.py:138`）。
6. 发布脚本把模块目录归档为 ZIP，根部为 `module.prop`（`apps/android-module/README.md:46`）。
7. KernelSU 安装时 customize.sh 校验 mounting metamodule（`apps/android-module/package/customize.sh:14`）。
8. customize.sh 校验 `payload/archive.sha256`（`apps/android-module/package/customize.sh:21`）。
9. customize.sh 从 APK 展开原生库与 rootfs（`apps/android-module/package/customize.sh:27`）。
10. customize.sh 把 APK 移到 system/app/Operit/Operit.apk（`apps/android-module/package/customize.sh:31`）。
11. 开机 service.sh 启动 operit-host-ctl start（`apps/android-module/package/service.sh:6`）。
12. `supervise` 等待 `sys.boot_completed` 与 `sys.user.0.ce_available` 就绪（`apps/android-module/package/operit-host-ctl:61`）。
13. `supervise` 用 `app_process` 启动 `ModuleMain`（`apps/android-module/package/operit-host-ctl:75`）。
14. 模块入口加载 `liboperit_flutter_bridge.so` 并调用 `runRuntime`（`apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt:17`）。
15. 特权生命周期入口校验进程 euid 为 0（`apps/android-module/src/Runtime.rs:297`）。
16. `run` 以 `run/core.lock` 加排他锁（`apps/android-module/src/Runtime.rs:316`）。
17. run_core 经 `prepare_environment` 部署 rootfs 与运行时环境（`apps/android-module/src/Runtime.rs:168`）。
18. run_core 经 `startBridge` 启动 Core（`apps/android-module/src/Runtime.rs:383`）。
19. Core 在回环地址监听临时端口（`apps/android-module/src/Runtime.rs:392`）。
20. 客户端凭证写入应用沙箱的 `client.json`（`apps/android-module/src/Runtime.rs:123`）。
21. Flutter Activity 连接模块启动的 Core（`apps/android-module/README.md:58`）。
22. `stop` 向 Core 发 SIGTERM（`apps/android-module/package/operit-host-ctl:95`）。
23. `stop` 完成后报告系统客户端挂载与用户数据均保留（`apps/android-module/package/operit-host-ctl:103`）。

## 来源

- `apps/android-module/README.md`
- `apps/android-module/src/Runtime.rs`
- `apps/android-module/android/src/main/kotlin/app/operit/ModuleMain.kt`
- `apps/android-module/build.py`
- `apps/android-module/package/module.prop`
- `apps/android-module/package/customize.sh`
- `apps/android-module/package/service.sh`
- `apps/android-module/package/action.sh`
- `apps/android-module/package/uninstall.sh`
- `apps/android-module/package/operit-host-ctl`
