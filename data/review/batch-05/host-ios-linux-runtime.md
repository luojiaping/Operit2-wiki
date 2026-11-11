---
title: iOS 内嵌 ARM64 Linux 运行时（vendored）
module: hosts
platforms: [ios, macos]
sources: [hosts/ios/linux-runtime/README.md, hosts/ios/linux-runtime/docs/README.md, hosts/ios/linux-runtime/docs/completeness.md, hosts/ios/linux-runtime/docs/delivery-status.md, hosts/ios/linux-runtime/include/operit/arm64_runtime.h]
date: 2026-11-11
---

## 概述

Operit ARM64 Linux Runtime 是自研的 AArch64 Linux 用户态兼容运行时，目标是在 Apple ARM64 上提供可运行的 Linux 开发终端（`hosts/ios/linux-runtime/README.md:3`）。
该运行时核心为 C++17 解释器与 Linux 用户 ABI，独立构建，不链接 iSH（`hosts/ios/linux-runtime/README.md:3`）。
Guest 指令由解释器执行，固定函数替换与宿主库预先编译，不在运行时生成宿主机器码（`hosts/ios/linux-runtime/README.md:3`）。
生产代码已有 ELF 动态装载、进程 / 线程、fork/COW、exec/wait、信号与定时器、futex、并行 executor、文件 / 挂载、网络、proc/dev、PTY 与终端接口（`hosts/ios/linux-runtime/README.md:5`）。
Flutter / Rust / iOS 桥接以及外部 root 配置、目录 bookmark 和原位 rootfs 接入已落盘（`hosts/ios/linux-runtime/README.md:5`）。
构建、guest 行为、性能和模拟器验收分别记录在 docs/delivery-status.md（`hosts/ios/linux-runtime/README.md:5`）。
外部 root 由调用方提供，宿主路径权限来自调用方（`hosts/ios/linux-runtime/README.md:57`）。
每个 VM 持有独立的 guest 进程 / 任务、内存、FD 和解码状态（`hosts/ios/linux-runtime/README.md:66`）。

## AI 速览

`ort_arm64_create` — 创建 VM 实例（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:58`）。
`ort_arm64_bind` — 在 load 前将已获授权的宿主目录绑定到 guest 绝对路径，flags 支持 `ORT_ARM64_BIND_READ_ONLY`（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:65`）。
`ort_arm64_load` — 从 guest 绝对路径装载可执行文件，argv 须有 argv[0]（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:68`）。
`ort_arm64_run` — 以指令预算执行，预算耗尽保留任务状态（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:74`）。
`ORT_ARM64_WAITING` — 表示阻塞等待（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:37`）。
`ort_arm64_terminal_open` — 打开 guest 终端（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:78`）。
`ort_arm64_terminal_read` / `ort_arm64_terminal_write` — 终端字节输入与输出（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:79`）。
`ort_arm64_terminal_resize` / `ort_arm64_terminal_signal` / `ort_arm64_terminal_close` — 终端尺寸、信号与关闭（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:81`）。
`resident_memory_limit` — VM 配置中的常驻内存上限（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:20`）。
`enable_fixed_acceleration` — VM 配置中的固定函数加速开关（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:25`）。
`Machine::load` — ELF 接线的中央入口，CMake → `Machine::load` / exec 生命周期 → loader（`hosts/ios/linux-runtime/docs/completeness.md:35`）。
数据流向：调用方提供 root 与配置 → `ort_arm64_create` 建 VM（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:58`）→ `ort_arm64_bind` 绑定宿主目录（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:65`）→
`ort_arm64_load` 装载 guest 可执行文件 → 反复调用 `ort_arm64_run` 按指令预算执行（`hosts/ios/linux-runtime/README.md:66`）。

## 核心机制

### 实现、接线、验证三类状态

docs/completeness.md 保留原 24 组编号，核对日期为 2026-11-03（`hosts/ios/linux-runtime/docs/completeness.md:3`）。
completeness.md 不另设当前通过率，最新结果、证据来源和时序统一见 docs/delivery-status.md（`hosts/ios/linux-runtime/docs/completeness.md:3`）。
已实现 I 的计入条件是有实际执行体，处理参数、状态和失败路径，并列明已覆盖子范围（`hosts/ios/linux-runtime/docs/completeness.md:11`）。
已接线 W 的计入条件是实现进入构建，中央 / 公开入口实际调用，有状态行为接入 Machine / Scheduler / App 生命周期（`hosts/ios/linux-runtime/docs/completeness.md:12`）。
已验证 V 的计入条件是对应行为实际执行，保存命令、返回码、输出与代码适用范围（`hosts/ios/linux-runtime/docs/completeness.md:13`）。
本轮尚无统一冻结版本和逐组完整验收，不发布新的整组百分比，也不按代码行数估工时（`hosts/ios/linux-runtime/docs/completeness.md:17`）。
可运行开发终端与完整 Linux 用户态能力使用不同判据，不能把开发终端可用性写成完整 Linux 兼容百分比（`hosts/ios/linux-runtime/docs/completeness.md:26`）。
docs/delivery-status.md 是唯一最新事实记录，覆盖构建、测试、Worker、iOS 证据及尚待确认项（`hosts/ios/linux-runtime/docs/README.md:7`）。

### Guest 指令执行与 CPU

src/cpu/aarch64/ 负责寄存器、解码、块缓存、标量、FP/SIMD、独占访问（`hosts/ios/linux-runtime/README.md:17`）。
CPU / FP / SIMD 的 decoder/execute、vector_indexed/integer/widen、vector_fp_fixed/indexed 有执行体（`hosts/ios/linux-runtime/docs/completeness.md:36`）。
FPCR trap 请求仍不支持（`hosts/ios/linux-runtime/docs/completeness.md:36`）。
多核 executor 的实现体是 runtime/tasks/executor.cpp、runtime/parallel.cpp 与 per-task CPU 计账（`hosts/ios/linux-runtime/docs/completeness.md:45`）。
同一 VM 的公开调用须串行化，execution_threads=0 自动选择最多四个宿主执行线程（`hosts/ios/linux-runtime/README.md:68`）。
ort_arm64_config 的 execution_threads 为 0 时自动选择最多四个宿主执行线程（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:29`）。

### ELF 装载与进程

ELF / 动态解释器的实现体是 src/elf/loader.cpp、src/elf/initial_stack.cpp 与 runtime/process/image_loader.cpp（`hosts/ios/linux-runtime/docs/completeness.md:35`）。
ELF 接线路径为 CMake → Machine::load / exec 生命周期 → loader（`hosts/ios/linux-runtime/docs/completeness.md:35`）。
src/elf/ 负责 ELF64、PT_INTERP、初始栈与 auxv（`hosts/ios/linux-runtime/README.md:19`）。
process / pidfd 由 Machine 的 clone / exec / wait / exit 与 linux/process/pidfd.cpp 负责（`hosts/ios/linux-runtime/docs/completeness.md:42`）。
加载失败后销毁并重建 VM（`hosts/ios/linux-runtime/README.md:66`）。

### fork/COW 与内存

src/memory/ 负责 Guest 虚拟地址、权限、稀疏页、COW 与代码失效（`hosts/ios/linux-runtime/README.md:18`）。
生产代码已有 fork/COW（`hosts/ios/linux-runtime/README.md:5`）。
mremap / MAP_SHARED 已有实现（`hosts/ios/linux-runtime/docs/completeness.md:37`）。

### 文件、挂载与虚拟文件系统

文件 / FD / 内存 / 挂载的实现体包括 fs/descriptor_table 的共享 OpenDescription、fs/mount/*、syscall_io/path/mount/memory 与 memory/*（`hosts/ios/linux-runtime/docs/completeness.md:37`）。
src/fs/ 负责路径、FD / OpenDescription、挂载与虚拟节点（`hosts/ios/linux-runtime/README.md:20`）。
procfs / devfs 的实现体是 fs/virtual/procfs.cpp、fs/virtual/devfs.cpp 与 fs/virtual/node.cpp，cmdline / environ / auxv 按 guest 内存范围读（`hosts/ios/linux-runtime/docs/completeness.md:39`）。

### 信号、定时器与线程

signals / timers 的实现体是 linux/signals/* 与 timers/process_timers.cpp、timers/timer_file.cpp、timers/timer_service.cpp（`hosts/ios/linux-runtime/docs/completeness.md:43`）。
threads / futex 的实现体包括 syscall_threads.cpp、threads/futex_pi.cpp、threads/scheduling.h、Scheduler/task 与 robust owner-death（`hosts/ios/linux-runtime/docs/completeness.md:44`）。
FUTEX_WAIT_REQUEUE_PI / FUTEX_CMP_REQUEUE_PI 已接线，PI / robust PI 与新 sched_attr 未完成验收（`hosts/ios/linux-runtime/docs/completeness.md:44`）。
本轮独立 runtime 已接入并测试 rseq、新版 futex、受限 io_uring、POSIX MQ、System V IPC、ptrace、seccomp 和受限 namespace 调用（`hosts/ios/linux-runtime/docs/completeness.md:5`）。
namespace 不提供新 namespace 或容器隔离（`hosts/ios/linux-runtime/docs/completeness.md:5`）。
ptrace 支持受限自动 fork/clone 跟踪，跟踪期间回退串行（`hosts/ios/linux-runtime/docs/completeness.md:5`）。

### 网络

network / DNS / TLS 的实现体是 linux/network/socket.cpp、linux/network/message_batch.cpp、linux/network/unix_namespace.cpp、linux/network/resolver.cpp 与 syscall_socket*.cpp（`hosts/ios/linux-runtime/docs/completeness.md:53`）。
网络完整错误队列等未实现（`hosts/ios/linux-runtime/docs/completeness.md:53`）。

### PTY 与终端

PTY / termios 的实现体是 linux/terminal/manager.cpp、linux/terminal/termios.cpp 与 runtime/console/*（`hosts/ios/linux-runtime/docs/completeness.md:40`）。
ort_arm64_terminal_open、ort_arm64_terminal_read、ort_arm64_terminal_write、ort_arm64_terminal_resize、ort_arm64_terminal_signal、ort_arm64_terminal_close 提供 PTY 输入、输出、尺寸和信号接口（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:78`）。
宿主 PTY 初始化返回 EPERM/EACCES 时改用 socket 软件终端（`hosts/ios/linux-runtime/docs/delivery-status.md:21`）。

### 资源限制

limits / accounting 的实现体包括 linux/process/resource_limits.cpp、linux/process/limit_enforcement.cpp 与 runtime/process/accounting.cpp、runtime/process/observability.cpp（`hosts/ios/linux-runtime/docs/completeness.md:54`）。
RLIMIT_MEMLOCK 等仍未支持（`hosts/ios/linux-runtime/docs/completeness.md:54`）。

### 固定函数加速

src/acceleration/ 是摘要固定的预编译函数替换（`hosts/ios/linux-runtime/README.md:22`）。
固定函数替换默认关闭，enable_fixed_acceleration 可启用完整 ELF 摘要固定的 musl memcpy、memmove、memset、strlen（`hosts/ios/linux-runtime/README.md:70`）。

### iOS 桥接与验收边界

iOS root / UI / bridges 由 App 的 Arm64RootFilesystem.mm、Arm64TerminalBridge.mm、Dart 配置 service / UI 与 Rust bridge 组成（`hosts/ios/linux-runtime/docs/completeness.md:55`）。
最新完整 Runner / 模拟器 / 外部 root 断言未执行（`hosts/ios/linux-runtime/docs/completeness.md:55`）。
设备专项交付结论未建立，真机持续运行 / 恢复与指标验证链未完成（`hosts/ios/linux-runtime/docs/completeness.md:57`）。
中央调用可沿 src/linux/syscalls.cpp 跟进（`hosts/ios/linux-runtime/docs/completeness.md:61`）。

### 性能与验收状态

2026-11-08 原生数值优化后 Python 数学中位数 323.311 → 304.111 ms（5.94%），Node --jitless 数学 301.097 → 279.693 ms（7.11%），50 ms 仍未达到（`hosts/ios/linux-runtime/docs/delivery-status.md:7`）。
该轮最终完整 CTest 46/46（含生成器 37/37、ISA 5253/5253），iOS device arm64 fixture 静态库构建通过，未构建完整 App 或取得设备性能（`hosts/ios/linux-runtime/docs/delivery-status.md:9`）。
2026-11-08 PTY 后备轮次的完整 CTest 47/47 通过（`hosts/ios/linux-runtime/docs/delivery-status.md:23`）。
iPhone 18 Pro / iOS 27.0 诊断应用在 native 与测试注入 EPERM 两种模式下均通过终端创建、命令、宿主/客体文件读写、旧配置恢复与 rootfs 保留（`hosts/ios/linux-runtime/docs/delivery-status.md:25`）。
上述 iPhone 诊断结论未在受影响用户的真机上验证（`hosts/ios/linux-runtime/docs/delivery-status.md:25`）。
2026-11-06 多 agent 采样优化后原始 Python 循环中位数 1.318184 → 1.013432 s，五对全部变快（`hosts/ios/linux-runtime/docs/delivery-status.md:33`）。
0.5 秒目标未达到，当前仍需约 2.03 倍循环吞吐（`hosts/ios/linux-runtime/docs/delivery-status.md:37`）。
Node Worker 5 秒目标尚未达成，新引擎未编译或测量（`hosts/ios/linux-runtime/docs/delivery-status.md:173`）。
Worker 原脚本单核 wall 24.988s、四核 wall 32.540s，两档都触发 guest 超时（`hosts/ios/linux-runtime/docs/delivery-status.md:177`）。
2026-11-03 整合的独立 macOS Release runtime CTest 35/35 通过，该配置不包含 terminal / Alpine rootfs 集成项（`hosts/ios/linux-runtime/docs/delivery-status.md:140`）。
四项失败修复的最终统一验收为 19/19 CTest 通过，四项原失败各连续运行 10 次，40/40 通过（`hosts/ios/linux-runtime/docs/delivery-status.md:159`）。
Node 整体尚未通过，新 watcher guest 与当前源码回归未跑（`hosts/ios/linux-runtime/docs/completeness.md:46`）。
Python / SQLite 有历史探针通过，更多扩展 / 大项目与当前改动回归未证明（`hosts/ios/linux-runtime/docs/completeness.md:49`）。
GCC / Git 有对应两项历史工作流通过，大项目、Git 网络、长构建与本轮回归未验（`hosts/ios/linux-runtime/docs/completeness.md:52`）。
Node Worker 尚未达原时限（`hosts/ios/linux-runtime/docs/completeness.md:45`）。

## 关键符号

`ort_arm64_vm` — VM 实例的不透明类型（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:15`）。
`resident_memory_limit` — VM 配置中的常驻内存上限（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:20`）。
`enable_fixed_acceleration` — VM 配置中的固定函数加速开关（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:25`）。
`ort_arm64_config` 的 `execution_threads` — 为 0 时自动选择最多四个宿主执行线程（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:29`）。
`ort_arm64_run` 返回 `ort_arm64_result`（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:74`）。
`ort_arm64_create` — 创建 VM 实例（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:58`）。
`ort_arm64_bind` — 在 load 前将已获授权的宿主目录绑定到 guest 绝对路径，flags 支持 `ORT_ARM64_BIND_READ_ONLY`（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:65`）。
`ort_arm64_load` — 从 guest 绝对路径装载可执行文件，argv 须有 argv[0]（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:68`）。
`ort_arm64_run` — 以指令预算执行，预算耗尽保留任务状态（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:74`）。
`ort_arm64_terminal_open` — 打开 guest 终端（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:78`）。
`Machine::load` — ELF 接线的中央入口，CMake → `Machine::load` / exec 生命周期 → loader（`hosts/ios/linux-runtime/docs/completeness.md:35`）。
`src/linux/syscalls.cpp` — 中央调用可沿该文件跟进（`hosts/ios/linux-runtime/docs/completeness.md:61`）。
src/api/ — 负责 C ABI、实例生命周期与异常边界（`hosts/ios/linux-runtime/README.md:15`）。
src/runtime/ — 负责 Machine、进程、Scheduler、并行 executor、console（`hosts/ios/linux-runtime/README.md:16`）。
src/cpu/aarch64/ — 负责寄存器、解码、块缓存、标量、FP/SIMD、独占访问（`hosts/ios/linux-runtime/README.md:17`）。
src/memory/ — 负责 Guest 虚拟地址、权限、稀疏页、COW 与代码失效（`hosts/ios/linux-runtime/README.md:18`）。
src/elf/ — 负责 ELF64、PT_INTERP、初始栈与 auxv（`hosts/ios/linux-runtime/README.md:19`）。
src/fs/ — 负责路径、FD / OpenDescription、挂载与虚拟节点（`hosts/ios/linux-runtime/README.md:20`）。
src/linux/ — 负责 AArch64 ABI、syscall 分域、信号、网络、终端与限制（`hosts/ios/linux-runtime/README.md:21`）。
src/acceleration/ — 摘要固定的预编译函数替换（`hosts/ios/linux-runtime/README.md:22`）。
src/base/ — 负责宿主 I/O、RAII、随机数与摘要（`hosts/ios/linux-runtime/README.md:23`）。

## 调用链

1. 调用方提供 root，宿主路径权限来自调用方（`hosts/ios/linux-runtime/README.md:57`）。
2. 零初始化 `ort_arm64_config` 后设置 root 并创建 VM：`ort_arm64_create` 创建 VM 实例（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:58`）。
3. `ort_arm64_bind` 在 load 前将已获授权的宿主目录绑定到 guest 绝对路径，flags 支持 `ORT_ARM64_BIND_READ_ONLY`（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:65`）。
4. `ort_arm64_load` 从 guest 绝对路径装载可执行文件，argv 须有 argv[0]（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:68`）。
5. ELF 接线路径为 CMake → Machine::load / exec 生命周期 → loader（`hosts/ios/linux-runtime/docs/completeness.md:35`）。
6. 反复调用 `ort_arm64_run` 按指令预算执行，预算耗尽保留任务状态（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:74`）。
7. 阻塞等待返回 `ORT_ARM64_WAITING`（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:37`）。
8. PTY 会话经 `ort_arm64_terminal_open` 打开，输入输出走 `ort_arm64_terminal_read` 与 `ort_arm64_terminal_write`（`hosts/ios/linux-runtime/include/operit/arm64_runtime.h:78`）。
9. 同一 VM 的公开调用须串行化，内部 executor 使用多个宿主执行线程（`hosts/ios/linux-runtime/README.md:68`）。
10. 加载失败后销毁并重建 VM（`hosts/ios/linux-runtime/README.md:66`）。

## 来源

- `hosts/ios/linux-runtime/README.md`（76 行，通读）
- `hosts/ios/linux-runtime/docs/README.md`（26 行，通读）
- `hosts/ios/linux-runtime/docs/completeness.md`（98 行，通读）
- `hosts/ios/linux-runtime/docs/delivery-status.md`（350 行，通读）
- `hosts/ios/linux-runtime/include/operit/arm64_runtime.h`（91 行，通读）
- `hosts/ios/linux-runtime/src/` 各子目录结构抽查（只列模块目录与入口文件名，未通读 C++ 实现）：`src/api/`、`src/runtime/`（含 `console/`、`process/`、`tasks/`）、`src/cpu/aarch64/`、`src/memory/`、`src/elf/`、`src/fs/`（含 `mount/`、`virtual/`）、`src/linux/`（含 `network/`、`terminal/`、`signals/`、`process/`、`threads/`、`timers/`、`files/`、`events/`）、`src/acceleration/`、`src/base/`

覆盖边界：本页事实全部来自上述 5 个 seed 文件的通读与公共头文件；C++ 实现只抽查了目录结构，未通读实现代码；性能与验收数字以 docs/delivery-status.md 为准，completeness.md 的 24 组矩阵为 2026-11-03 核对口径，不发布新的整组百分比（`hosts/ios/linux-runtime/docs/completeness.md:17`）。
