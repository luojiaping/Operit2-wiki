# Issue 102 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:32:36Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/102#issuecomment-6854425959


本轮全量重审结论：需修改。Wiki `f9c90d7`；声明源码基线 `364d1d594`，另对照最新上游 `09249fb9`。

[P2] 正文第153行与 fact 75 把 `ValidateRoot` 的目录包含方向写反了。`tools/windows-installer/shared/UserDataCleanup.cs:149` 是 `protectedPaths.Any(path => IsWithin(path, root))`，而 `:169-171` 的参数顺序是 `IsWithin(path, root)`，因此拒绝的是“清理根等于或包含受保护路径”（受保护位置本身及其祖先），不是“受保护路径包含的所有子目录”。例如 UserProfile/AppData 本来就在 protectedPaths 中，但其下的 Operit2 默认数据目录仍是合法清理目标；按现有正文会误读成这些目录都被禁止。`:150` 才另行拒绝 Windows 目录及其子树。请同步修正文和 fact 75，明确这两个方向不同的检查。该问题在原基线就存在，不是后续接口漂移。

另核对了清理计划冻结/复核、凭据先于目录删除及 MSI 生命周期条件。后续增加 Update、自动退出应用与日志诊断属于版本变化，不作为本条阻断理由。仅静态审查，未执行卸载、清理、测试或构建。

源码定位：
- [tools/windows-installer/shared/UserDataCleanup.cs:149](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/tools/windows-installer/shared/UserDataCleanup.cs#L149)
- [tools/windows-installer/shared/UserDataCleanup.cs:169](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/tools/windows-installer/shared/UserDataCleanup.cs#L169)
