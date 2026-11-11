# 修订 brief：agent-hooks（Issue #41，batch-04）

- 只改 `review/batch-04/agent-hooks.facts.json` 与 `review/batch-04/agent-hooks.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：**原有事实偏差**（基线本身就错了，1 项）。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查版本：wiki `66baaf09`；对照上游最新 main `053c6686`，并检查相对条目原基线 `364d1d594` 的变化。

**[P2] 共用 functionName/functionSource 的结论应限定为 hook 注册，不能包含 AI Provider 注册。** 正文第 55 行和 fact 第 **18** 条称“除菜单对话框子结构外，所有注册结构都有 containerPackageName、functionName 与可选 functionSource”。

实际同页已列出的 ToolPkgHooks.rs:144 没有通用 functionName/functionSource；它包含四组独立方法字段：listModelsFunctionName/Source、sendMessageFunctionName/Source、testConnectionFunctionName/Source、calculateInputTokensFunctionName/Source。

请把范围改为“14 个 hook 注册结构具有这些共用字段”，将菜单对话框与 AI Provider 按各自契约说明。这也与正文第 54 行、fact 第 14 条“AI Provider 注册不是 hook 注册”的区分一致。该问题在原基线和最新源码均存在。

其余已核对 1–60 秒 pre-hook 超时限制及阶段名单、同一分发链共享总截止时间、通知 hook 单项失败后继续循环，以及摘要 hook 按序应用变更和传播错误，见 ToolPkgPreHookTimeout.rs:20、ToolPkgChatRuntimeHookBridge.rs:102、SummaryHookRegistry.rs:78。这些抽查项与正文一致。

本轮核对正文、同名 `.facts.json` 和固定提交实现，语义结论限于所述重点抽查范围；未运行编译、构建、测试或实机实验。修订时请同步更新正文及对应原子事实，并重核源码引用。

## 核实结论（已重钉行号）

- 基线与上游实测一致：`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:144` 为 `pub struct ToolPkgAiProviderRegistration {`（基线与 `053c6686` 同行），其后是四组独立方法字段：`listModelsFunctionName/Source`、`sendMessageFunctionName/Source`、`testConnectionFunctionName/Source`、`calculateInputTokensFunctionName/Source`，**没有**通用 `functionName`/`functionSource`（落笔时重钉四组字段的确切行号）。
- 结论：评审属实。共用字段的结论只适用于 14 个 hook 注册结构；菜单对话框子结构与 AI Provider 注册各按其契约。

## 改法

- fact 第 18 条与正文第 55 行同步改：范围收窄为“14 个 hook 注册结构具有这些共用字段（`containerPackageName`、`functionName` 与可选 `functionSource`）”，并把菜单对话框子结构与 AI Provider 注册按各自契约说明——AI Provider 注册（`ToolPkgHooks.rs:144`）是四组独立方法字段，无通用 `functionName`/`functionSource`。
- 改完核对正文第 54 行与 fact 第 14 条（“AI Provider 注册不是 hook 注册”），确认全页口径一致、无矛盾。
- 改前按断言原文逐条再钉一次行号，不要只按编号。

## 验收

- facts 总数预计不变（以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-04`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果。
