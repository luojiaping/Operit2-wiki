# Issue 113 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:33:14Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/113#issuecomment-6854440695


本轮全量重审结论：需修改一处枚举范围。Wiki `f9c90d7`，源码基线 `364d1d594`；另对照最新上游 `09249fb9`。

[P3] 第86、147行和 fact 42 把 `build_release.py --scope` 写成接受 cli/app/full“三个取值”，但原基线 `tools/release/build_release.py:109-113` 的 `ReleaseScope` 已含第四个 `NONE = "none"`，`:1304` 的 argparse choices 来自整个枚举。当前 main 也仍是四值。`docs/release-versioning.md:228-236` 只是展示三个构建示例，不能由示例推出枚举仅三项。请补上 none（只检查版本/脚本入口的流程见相关交互脚本），或明确改成“此文档展示 cli/app/full 三种构建示例”，同步正文和 fact 42；AI速览第25行可一起对齐。无需重写版本与发布章节。

已另核对版本来源、精确资产匹配、惰性更新发现与双Android产物共用构建号规则，未发现其他阻断。未执行测试、构建、发布或CI。

源码定位：
- [tools/release/build_release.py:109](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/tools/release/build_release.py#L109)
- [tools/release/build_release.py:1304](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/tools/release/build_release.py#L1304)
