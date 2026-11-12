---
title: 性能场景与基准
module: tools
platforms: [windows, macos, ios]
sources: 6
date: 2026-11-11
---

## 概述

- 本页覆盖 `tools/link-perf/` 的端到端 Link 性能场景与 `tools/benchmarks/` 的 macOS/iOS 基准脚本。`tools/link-perf/README.md:3` `tools/link-perf/run_link_perf.ps1:5` `tools/benchmarks/macos_idle.py:4`
- 协议-only 基准不在本页范围，保留在 `core/crates/foundation/link/benches`。`tools/link-perf/README.md:4`
- 工具总览见 [[tools-overview|tools 总览]]。

## AI 速览

- `CoreNodeRouter -> PeerLink -> CoreNode` — 跨节点性能场景的目标链路。`tools/link-perf/README.md:16`
- `run_link_perf.ps1` — Link 性能运行脚本（Windows），只记录场景元数据。`tools/link-perf/run_link_perf.ps1:56`
- `macos_idle.py` — macOS 进程空闲采样，不挂接 profiler。`tools/benchmarks/macos_idle.py:2`
- `macos_trace_summary.py` — macOS xctrace thread-state 导出汇总。`tools/benchmarks/macos_trace_summary.py:2`
- `ios_cpu_flamegraph.py` — iOS 模拟器 CPU 火焰图合并。`tools/benchmarks/ios_cpu_flamegraph.py:2`
- `markdown_pipeline.py` — Markdown 原生管线基准（macOS，文档见 `markdown_pipeline.md`）。`tools/benchmarks/markdown_pipeline.md:7`
- 主入口：`run_link_perf.ps1 -Scenario <场景 JSON>`（Windows）；`python3 tools/benchmarks/macos_idle.py PID --seconds 30 --output idle.json`（macOS）。`tools/link-perf/README.md:22` `tools/benchmarks/macos_idle.py:4`
- 数据流向：场景 JSON → 六字段报告 JSON；进程采样 → JSON 汇总；xctrace 导出 → 线程统计；模拟器采样 → 火焰图。`tools/link-perf/run_link_perf.ps1:59`

## 核心机制

- `tools/link-perf/` 用于跨 app 或 host 边界的端到端 Link 性能运行。`tools/link-perf/README.md:3` `tools/link-perf/run_link_perf.ps1:5`
- 协议-only 基准保留在 `core/crates/foundation/link/benches`，不放在 `link-perf/`。`tools/link-perf/README.md:4` `tools/link-perf/run_link_perf.ps1:5`
- `link-perf` 测量 CLI、host 与 access-layer 三类嵌入 `operit-link` 的路径。`tools/link-perf/README.md:8` `tools/link-perf/run_link_perf.ps1:5`
- Link 性能场景输入保存在 `scenarios/` 下，作为稳定的 JSON 文件。`tools/link-perf/README.md:9`
- Link 性能运行生成的输出写到 `reports/` 下。`tools/link-perf/README.md:10`
- 每份 Link 性能报告记录 machine、build profile、command、sample count、payload size 五项。`tools/link-perf/README.md:11`
- 跨节点性能场景必须针对 `CoreNodeRouter -> PeerLink -> CoreNode` 编写。`tools/link-perf/README.md:16`
- 旧的应用层 HTTP RPC 场景已经删除，避免把本地 Proxy 链路误当成 Space 链路。`tools/link-perf/README.md:16`
- Link 性能运行忽略 Rust warnings。`tools/link-perf/README.md:25`
- `run_link_perf.ps1` 记录 commands 与 timestamps，具体进程接线归属所选 scenario。`tools/link-perf/README.md:25`
- `run_link_perf.ps1` 的 Scenario 参数必填，ReportsDir 默认 `tools/link-perf/reports`。`tools/link-perf/run_link_perf.ps1:5`
- 脚本设置 `$ErrorActionPreference = "Stop"`，出错即停。`tools/link-perf/run_link_perf.ps1:8`
- `Resolve-ScenarioPath` 把场景路径解析为绝对路径。`tools/link-perf/run_link_perf.ps1:12`
- `New-ReportPath` 创建报告目录，报告文件名为 `<场景名>-<yyyyMMdd-HHmmss>.json`。`tools/link-perf/run_link_perf.ps1:21`
- 场景读取用 `Get-Content` 与 `ConvertFrom-Json`，经 `Read-Scenario` 封装。`tools/link-perf/run_link_perf.ps1:43`
- 报告记录 scenario（取自场景文件的 name）与 kind。`tools/link-perf/run_link_perf.ps1:51`
- 报告记录 scenarioPath（绝对路径）与 createdAt（ISO "o" 格式）。`tools/link-perf/run_link_perf.ps1:53`
- 报告记录 command（取自场景文件的 command）。`tools/link-perf/run_link_perf.ps1:55`
- 报告的 notes 字段写明只捕获了场景元数据，进程执行待 scenario command 定稿后在脚本内接线。`tools/link-perf/run_link_perf.ps1:56`
- 报告只含 scenario、kind、scenarioPath、createdAt、command、notes 六个字段，不含 machine、build profile、sample count、payload size。`tools/link-perf/run_link_perf.ps1:51`
- 报告以 JSON Depth 8、UTF8 写出，终端打印 "link perf report: <路径>"。`tools/link-perf/run_link_perf.ps1:59`
- `macos_idle.py` 在 macOS 上采样进程，不挂接 profiler。`tools/benchmarks/macos_idle.py:2`
- `macos_idle.py` 的用法是 `python3 tools/benchmarks/macos_idle.py PID --seconds 30 --output idle.json`。`tools/benchmarks/macos_idle.py:4`
- `macos_idle.py` 的 CPU 百分比以单核为 100%，wakeups 是进程计数器而非瓦特。`tools/benchmarks/macos_idle.py:5`
- `macos_idle.py` 的 --seconds 默认 30，--output 必填，--seconds 小于 1 时报错。`tools/benchmarks/macos_idle.py:24`
- `macos_idle.py` 通过 ctypes 调 libSystem 的 `mach_timebase_info` 做 mach absolute tick 到纳秒的换算。`tools/benchmarks/macos_idle.py:32`
- `macos_idle.py` 通过 ctypes 调 libproc 的 `proc_pid_rusage`（flavor 2）读取进程 rusage。`tools/benchmarks/macos_idle.py:40`
- `macos_idle.py` 按 --seconds 的秒数每秒采样一次。`tools/benchmarks/macos_idle.py:46`
- `macos_idle.py` 每条样本记录 elapsed_seconds、cpu_percent_one_core、interrupt_wakeups_per_second、package_idle_wakeups_per_second、footprint_mib。`tools/benchmarks/macos_idle.py:50`
- `macos_idle.py` 的汇总记录 cpu_percent_median（各样本中位数）与 cpu_percent_max_1s（单秒最大值）。`tools/benchmarks/macos_idle.py:64`
- `macos_idle.py` 的汇总记录 disk_read_bytes 与 disk_write_bytes（采样起止的 diskio 差值）。`tools/benchmarks/macos_idle.py:69`
- `macos_idle.py` 输出 JSON {summary, samples}，写到 --output 并打印 summary。`tools/benchmarks/macos_idle.py:72`
- `macos_trace_summary.py` 汇总单个已连接进程的 xctrace thread-state XML 导出。`tools/benchmarks/macos_trace_summary.py:2`
- `macos_trace_summary.py` 的导出命令是 `xcrun xctrace export --input recording.trace --xpath '/trace-toc/run[@number="1"]/data/table[@schema="thread-state"]' --output thread-state.xml`。`tools/benchmarks/macos_trace_summary.py:4`
- `macos_trace_summary.py` 声明调度切换不是 `proc_pid_rusage` 的 interrupt-wakeup 计数器。`tools/benchmarks/macos_trace_summary.py:9`
- `macos_trace_summary.py` 声明 "made runnable by" 线程是调度线索，不是完整因果 trace。`tools/benchmarks/macos_trace_summary.py:10`
- `macos_trace_summary.py` 要求导出表包含 start、duration、thread、state、made-runnable-by-thread 五列，缺失则报错。`tools/benchmarks/macos_trace_summary.py:37`
- `macos_trace_summary.py` 把 Running 状态的时长按线程累计为 `runningNs`。`tools/benchmarks/macos_trace_summary.py:54`
- `macos_trace_summary.py` 每线程统计 runnableTransitions，kernel（pid 0）与 securityd 引起的分别计数为 `kernelCausedRunnableTransitions` 与 `securitydCausedRunnableTransitions`。`tools/benchmarks/macos_trace_summary.py:57`
- `macos_trace_summary.py` 输出线程按 runnableTransitions 降序排列。`tools/benchmarks/macos_trace_summary.py:73`
- `macos_trace_summary.py` 输出 notes 声明 attached tracing 会改变执行，idle 计数器需单独测量。`tools/benchmarks/macos_trace_summary.py:79`
- `ios_cpu_flamegraph.py` 合并模拟器 Time Profiler XML、Dart CPU 采样与进程 CPU 计数器。`tools/benchmarks/ios_cpu_flamegraph.py:2`
- `ios_cpu_flamegraph.py` 只用真实 running 线程采样，阻塞栈不算 CPU 工作。`tools/benchmarks/ios_cpu_flamegraph.py:3`
- `ios_cpu_flamegraph.py` 要求源录制与 stage 报告的 wall-clock 边界匹配。`tools/benchmarks/ios_cpu_flamegraph.py:4`
- `ios_cpu_flamegraph.py` 的 stage 报告来自 current-collector.json，原生采样来自 stacks-native.xml 与 stacks-toc.xml。`tools/benchmarks/ios_cpu_flamegraph.py:105`
- `ios_cpu_flamegraph.py` 的数据来自模拟器、Flutter debug、Apple M5 宿主，不是物理 iPhone 的功耗或温度测量。`tools/benchmarks/ios_cpu_flamegraph.py:109`
- `ios_cpu_flamegraph.py` 的 CPU 百分比覆盖全部应用线程，单核占满为 100%，峰值窗口约 100 ms。`tools/benchmarks/ios_cpu_flamegraph.py:110`
- `ios_cpu_flamegraph.py` 的 Dart 与 native 百分比的分母不同，inclusive 帧重叠，不得相加。`tools/benchmarks/ios_cpu_flamegraph.py:111`
- `ios_cpu_flamegraph.py` 声明单次 tool call 太短，100 ms CPU 或栈百分比不可靠，用明确标注的 batch200 stage。`tools/benchmarks/ios_cpu_flamegraph.py:112`
- `ios_cpu_flamegraph.py` 每 stage 输出 meanPercent、peak100msPercent、nativeSampleCount，-single stage 的 meanPercent 为 None。`tools/benchmarks/ios_cpu_flamegraph.py:129`
- `ios_cpu_flamegraph.py` 输出 iphone-cpu-stacks.json、iphone-profiles.speedscope.json、iphone-flamegraphs.html。`tools/benchmarks/ios_cpu_flamegraph.py:161`
- Markdown 管线基准在仓库根目录的 macOS 上运行，需装好项目 Flutter 依赖，命令是 `python3 tools/benchmarks/markdown_pipeline.py`。`tools/benchmarks/markdown_pipeline.md:7`
- Markdown 管线基准的 runner 以 Rust release 模式构建原生 fixture，以 profile/AOT 模式启动 Flutter 集成基准。`tools/benchmarks/markdown_pipeline.md:9`
- Markdown 管线基准的报告记录 Rust release 与 profile/AOT 两种模式，runner 拒绝其他模式的结果。`tools/benchmarks/markdown_pipeline.md:10`
- Markdown 管线基准每个 case 预热一次，报告五次运行的中位数并附每次样本。`tools/benchmarks/markdown_pipeline.md:11`
- Markdown 管线基准测量路径第 1 步以固定 UTF-8 Markdown 输入与 Unicode 字符 chunk 大小打开 watch。`tools/benchmarks/markdown_pipeline.md:16`
- Markdown 管线基准测量路径第 2 步用 `MarkdownRenderEventStream` 解析 chunk，含 EOF flush。`tools/benchmarks/markdown_pipeline.md:17`
- Markdown 管线基准测量路径第 3 步每个语义事件用 `toCoreValue` 转 `CoreEvent` 入队，如 `MessageProcessingDelegate`，只有 root completion 终止 transport。`tools/benchmarks/markdown_pipeline.md:18`
- Markdown 管线基准测量路径第 4 步 fixture 直接包含生产源文件 `BridgeTransport`、`BridgeCodec`、`FfiTransport`，不复制其实现。`tools/benchmarks/markdown_pipeline.md:21`
- Markdown 管线基准测量路径第 5 步经生产 `FfiCoreTransport`、`FfiCoreProxy`、`ProxyCoreRuntimeBridge.openEmbeddedCoreStream` 与生成的 `MarkdownStreamEvent.fromMessagePack` 接收。`tools/benchmarks/markdown_pipeline.md:24`
- Markdown 管线基准测量路径第 6 步事件应用到 `StreamMarkdownRendererState`，完成 node builder 并创建最终稳定 root node snapshot。`tools/benchmarks/markdown_pipeline.md:27`
- Markdown 管线基准的 fixture 替换模型生成、网络耗时、会话存储与应用启动，不替换 transport、parser、codec、root node builder。`tools/benchmarks/markdown_pipeline.md:30`
- Markdown 管线基准的计时包含 watch 打开与输入请求编解码，连接建立先预热。`tools/benchmarks/markdown_pipeline.md:32`
- Markdown 管线基准的计时在流完成与最终 root node snapshot 后停止。`tools/benchmarks/markdown_pipeline.md:37`
- Markdown 管线基准的源码内容相等性、语义事件计数、原生指标请求与状态清理在计时区外检查。`tools/benchmarks/markdown_pipeline.md:37`
- Markdown 管线基准的单独诊断 pass 检测原生解析与 CoreValue 转换，并发阶段时间不得相加估算 wall time。`tools/benchmarks/markdown_pipeline.md:39`
- Markdown 管线基准测量突发输入流。`tools/benchmarks/markdown_pipeline.md:43`
- Markdown 管线基准不测量模型 token 延迟、周期 widget 快照、嵌套 quote/table widget 消费者、layout、painting、动画、设备 FPS。`tools/benchmarks/markdown_pipeline.md:43`
- Markdown 管线基准的实际 `StreamMarkdownRenderer` 及其嵌套消费者另行挂载作正确性 smoke check。`tools/benchmarks/markdown_pipeline.md:46`
- `markdown_parse_bench` 仍是 parser-only 微基准，其数字不是原生管线计时。`tools/benchmarks/markdown_pipeline.md:47`
- Markdown 管线基准默认输出到 `apps/flutter/app/build/markdown_benchmark/`，含 markdown_pipeline.json、flutter_profile.log、native_build.log，--output 可改目录。`tools/benchmarks/markdown_pipeline.md:50`

## 关键符号

- `CoreNodeRouter` — 跨节点性能场景目标链路的第一段。`tools/link-perf/README.md:16`
- `PeerLink` — 跨节点性能场景目标链路的中间段。`tools/link-perf/README.md:16`
- `CoreNode` — 跨节点性能场景目标链路的末段。`tools/link-perf/README.md:16`
- `operit-link` — Link 性能场景测量的三类路径所嵌入的库。`tools/link-perf/README.md:8`
- `Resolve-ScenarioPath` — 场景路径转绝对路径。`tools/link-perf/run_link_perf.ps1:12`
- `Read-Scenario` — 场景 JSON 读取。`tools/link-perf/run_link_perf.ps1:43`
- `New-ReportPath` — 带时间戳的报告路径生成。`tools/link-perf/run_link_perf.ps1:21`
- `proc_pid_rusage` — macOS 空闲采样的 rusage 读取入口。`tools/benchmarks/macos_idle.py:40`
- `mach_timebase_info` — mach absolute tick 到纳秒的换算入口。`tools/benchmarks/macos_idle.py:32`
- `runningNs` — xctrace 汇总里每线程 Running 状态累计时长。`tools/benchmarks/macos_trace_summary.py:54`
- `runnableTransitions` — xctrace 汇总里每线程进入 Runnable 的次数。`tools/benchmarks/macos_trace_summary.py:57`
- `MarkdownRenderEventStream` — Markdown 管线基准的 chunk 解析器。`tools/benchmarks/markdown_pipeline.md:17`
- `toCoreValue` — 语义事件到 CoreEvent 的转换。`tools/benchmarks/markdown_pipeline.md:18`
- `BridgeTransport` — Markdown 管线基准直接包含的生产源文件之一。`tools/benchmarks/markdown_pipeline.md:21`
- `FfiCoreTransport` — Markdown 管线基准的生产接收端之一。`tools/benchmarks/markdown_pipeline.md:24`
- `ProxyCoreRuntimeBridge.openEmbeddedCoreStream` — Markdown 管线基准的生产接收端之一。`tools/benchmarks/markdown_pipeline.md:24`
- `StreamMarkdownRendererState` — Markdown 事件的应用目标。`tools/benchmarks/markdown_pipeline.md:27`
- `markdown_parse_bench` — parser-only 微基准，不是原生管线计时。`tools/benchmarks/markdown_pipeline.md:47`
- `meanPercent` — iOS 火焰图每 stage 的 CPU 均值百分比。`tools/benchmarks/ios_cpu_flamegraph.py:129`
- `peak100msPercent` — iOS 火焰图每 stage 的 100 ms 峰值 CPU 百分比。`tools/benchmarks/ios_cpu_flamegraph.py:129`

## 调用链

1. 场景 JSON 经 `Resolve-ScenarioPath` 解析为绝对路径。`tools/link-perf/run_link_perf.ps1:46`
2. `Read-Scenario` 读取场景 JSON。`tools/link-perf/run_link_perf.ps1:45`
3. `New-ReportPath` 生成带时间戳的报告路径。`tools/link-perf/run_link_perf.ps1:48`
4. 报告以 JSON 写出，终端打印报告路径。`tools/link-perf/run_link_perf.ps1:59`
5. macOS 空闲采样：PID 经 `proc_pid_rusage` 每秒采样一次。`tools/benchmarks/macos_idle.py:46`
6. macOS 空闲采样输出 JSON {summary, samples}，写到 --output 并打印 summary。`tools/benchmarks/macos_idle.py:72`
7. Markdown 管线基准：watch 打开 → `MarkdownRenderEventStream` 解析 → `toCoreValue` 转 `CoreEvent`。`tools/benchmarks/markdown_pipeline.md:18`
8. Markdown 管线基准：生产 transport 接收后，事件应用到 `StreamMarkdownRendererState`，完成 node builder 并创建最终稳定 root node snapshot。`tools/benchmarks/markdown_pipeline.md:27`
9. Markdown 管线基准的计时在流完成与最终 root node snapshot 后停止。`tools/benchmarks/markdown_pipeline.md:37`

## 来源

- seed 文件：`tools/link-perf/README.md`、`tools/link-perf/run_link_perf.ps1`、`tools/benchmarks/macos_idle.py`、`tools/benchmarks/markdown_pipeline.md`。`tools/link-perf/README.md:3`
- 直接相关的同目录文件（回答大纲第三问 macOS/iOS traces 各测什么）：`tools/benchmarks/macos_trace_summary.py`、`tools/benchmarks/ios_cpu_flamegraph.py`。`tools/benchmarks/macos_trace_summary.py:2`
- 基线：AAswordman/Operit2 @ 364d1d594。
- 大纲问题称性能报告记录四项，README 原文列出 machine、build profile、command、sample count、payload size 五项，正文按 README 原文写五项。`tools/link-perf/README.md:11`
- 否定性核验：本页无全仓零命中类结论；“脚本不执行场景 command”的判断依据是 `run_link_perf.ps1:56` 的 notes 字段原文（进程执行待 scenario command 定稿后接线）与该脚本 60 行全文通读，command 只被记入报告，未被调用。`tools/link-perf/run_link_perf.ps1:56`
