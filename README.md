<h1 align="center">Operit2-wiki</h1>
<p align="center">
  <a href="https://luojiaping.github.io/Operit2-wiki"><img src="https://img.shields.io/badge/📖-Operit2_Wiki-E8D5B5?style=flat-square&labelColor=3a3026&color=E8D5B5" alt="Wiki"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/MIT-license-5a6e5c?style=flat-square&labelColor=3a3026" alt="license"></a>
</p>

<p align="center">Operit2 的知识库：<strong>既是正式 wiki 站，也是 AI 答疑的知识源头</strong>。</p>

👉 **在线阅读：https://luojiaping.github.io/Operit2-wiki**

- 知识页面按 [SCHEMA.md](SCHEMA.md) 由 AI agent 生成与维护，源码版本钉住 `364d1d594`（2026-11-11，见 [PIPELINE.md](PIPELINE.md)）
- 每个事实断言都带 `file:line` 引用，可机器验证
- 定位：跨平台 Agent Core（Rust Core + Flutter App），不是 Operit 一代的 Android 原生应用；一代的 wiki 在 [Operit-wiki](https://luojiaping.github.io/Operit-wiki)

## AI 使用（推荐：拉到本地）

```bash
git clone https://github.com/luojiaping/Operit2-wiki.git
```

1. 先读 `AGENTS.md`（入口，一页纸）
2. 完整检索协议见 `wiki/AI_USAGE.md`：索引 → grep → 限量精读 → facts 引用
3. 条目索引：`review-queue.json`（id / 标题 / 模块）
4. 条目正文：`review/<批次>/<id>.md`，原子事实：同名 `.facts.json`

不许把页面打碎做向量切块 / embedding 检索；wiki 没写的就说没写。

## 参与：提交改动与意见

- **内容勘误 / 补充 / 意见**：直接在 [GitHub 提 Issue](https://github.com/luojiaping/Operit2-wiki/issues/new)，注明页面标题和正确内容（代码类请带源码 `file:line`）。
- **评审中的条目**：每条目有专属 `[评审]` Issue，在网站条目页评论区留言即同步到 Issue；评论"通过"即批准（只认 luojiaping 本人）。
- **直接改代码 / 网站**：欢迎提 PR（MIT 协议）；网站改动请先跑 `python3 scripts/build_queue.py` 验证构建。

## 目录结构

```
Operit2-wiki/
├── AGENTS.md          # AI 入口：怎么用这个仓库（一页纸）
├── SCHEMA.md          # 条目规范与引用铁律（宪法）
├── PIPELINE.md        # 全量流水线（分片 → 阅读 → critic → 评审 → 发布）
├── outline/           # 大纲（outline-v1.yaml，版本化）
├── wiki/AI_USAGE.md   # AI 检索协议全文（索引→grep→限量精读→引用铁律）
├── review-queue.json  # 全库索引（id / 标题 / 模块 / 状态）
├── review/            # 全部条目正文（按批次）
│   └── <batch-id>/
│       ├── <entry>.md          # 条目正文
│       ├── <entry>.facts.json  # 原子事实（每条带 file:line）
│       └── <entry>.status.json # 状态（approved / review-pending）
├── site/              # 网站源码（正式 wiki / 知识图谱）
├── scripts/           # lint、构建、部署工具
└── tracking/          # 阅读状态、分片、反馈水位
```

## 源码基线

- 上游：`AAswordman/Operit2`，大纲 v1 钉住 `364d1d594`（2026-11-11）
- 规模（该提交）：6335 个 tracked 文件；Rust 1236、Dart 1455、TypeScript 516
- 顶层：`apps/`（android-module、cli、flutter、server）、`core/`（11 个 Rust crate）、`hosts/`（android、ios、macos、windows、linux、web、ohos、apple、unix 等）、`plugins/`（内置 19、外置 31）、`edge/`（厂商 SDK 与板子）、`tools/`、`docs/`
- Operit2 仍在 Preview，底层结构、数据格式、插件契约可能有 breaking 变更；wiki 按提交号钉版本，过期页由 `scripts/check_staleness.py` 标 STALE 重核。

## License

MIT
