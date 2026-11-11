## luojiaping @ 2026-11-11T07:08:13Z (https://github.com/luojiaping/Operit2-wiki/issues/4#issuecomment-6789484272)

审查结论：**需修改**。

核对基线：wiki `b75bcad9`，上游 `AAswordman/Operit2` 最新 `main` 已确认是 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与 wiki 标注一致。以下是静态源码审查意见。

1. **[P2] 明确 update check 参数是“当前版本”，并展示日常无参数用法。** [正文第 32 行](https://github.com/luojiaping/Operit2-wiki/blob/b75bcad9d63959f0108f81193119e372eca38f4a/review/batch-01/intro-preview.md#L32)写 `operit2 cli update check <version>`，容易被理解为目标版本。[apps/cli/src/cli/mod.rs:526–536](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/apps/cli/src/cli/mod.rs#L526) 已支持 `operit2 cli update check`，自动使用 `CARGO_PKG_VERSION`；[同文件:558–569](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/apps/cli/src/cli/mod.rs#L558) 的显式参数命名为 `current_version`。建议主示例改成无参数命令，带参形式标成 `<current-version>` 并解释为覆盖版本比较基准。此项为**源码直引、wiki 未覆盖**，请补入 facts/来源。

2. **[P2] 为 AI 速览的事实断言补齐就近引用。** [正文第 21 行](https://github.com/luojiaping/Operit2-wiki/blob/b75bcad9d63959f0108f81193119e372eca38f4a/review/batch-01/intro-preview.md#L21)起的速览列出了首次 preview、buildNumber 增长、Wasm 开关默认值、脚本职责和命令行为，但这一节没有 `file:line` 引用。SCHEMA 要求每个事实断言附引用，AI 使用协议又允许只读取速览，因此正文后半部分的引用不能代替速览本身的可追溯性。可复用已有证据，例如 [docs/release-versioning.md:193](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/docs/release-versioning.md#L193) 和 [preview.27 发布说明:4](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/docs/release-notes/2.0.0-preview.27-build33.md#L4)。

已抽查更新通道与排序、不降级规则、发布版本来源、协议版本独立及 preview.27 Wasm 开关说明，并核对 update check 实现；本轮未发现这些版本机制的实质矛盾。本页 42 条 facts 引用路径均存在且行号未越界。未执行编译、构建或测试；发布说明中的历史验证结果仅核对其文字记录。


