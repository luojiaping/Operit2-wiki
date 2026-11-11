# Operit2-wiki · AI 入口

这是 Operit2（跨平台 Agent Core：Rust Core + Flutter App）的官方知识库。回答 Operit2 相关问题时，**禁止凭记忆回答**，必须按本仓库的协议检索。

## 怎么用

1. 完整协议：`wiki/AI_USAGE.md`（先读这个）
2. 条目索引：`review-queue.json`（按 id / 标题 / 模块定位候选条目）
3. 条目正文：`review/<批次>/<id>.md`（每页有 `## AI 速览`，先读它）
4. 原子事实：同名 `.facts.json`（代码结论引用它的 `文件:行号`）

## 铁律

- 禁止向量切块 / embedding 检索；禁止编造，wiki 没写就说没写
- 每个代码结论标注「页面标题 + 文件:行号」，落笔前 grep 复核行号
- 输出区分 EXTRACTED（精确引用）/ INFERRED（写明依据）
- 源码基线：`AAswordman/Operit2 @ 364d1d594`（2026-11-11）；引用超出该基线的新代码必须说明
- Operit2 是跨平台的：同一能力在不同平台表现可能不同，回答必须注明适用平台（Host），不许把某平台的实现说成全平台
- 一代 Operit（Android 原生，Kotlin）的问题去 [Operit-wiki](https://luojiaping.github.io/Operit-wiki)，不要用本仓库回答
