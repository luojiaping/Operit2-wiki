# Issue 51 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:28:51Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/51#issuecomment-6854338638


本轮结论：需修改。

复核 Wiki f9c90d7a，仍有两处固定基线自身的事实错误需要改正文及 facts：

1. L163 / fact100 把 NoDisplay 也写成无条件排除。实际 list(include) 仅在 include=false 时排除 NoDisplay=true；include=true 仍可列出这些应用。依据：[packages.rs:126–132](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/hosts/linux/src/tools/system/packages.rs#L126-L132)。
2. L166 / fact103 把 env/sh/bash/flatpak/snap 的限制归到了“启动”。start 实际只执行 gio launch；该检查属于 executable()，由 stop 的非 X-Flatpak 分支调用，X-Flatpak 则走 flatpak kill。依据：[packages.rs:141–180](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/hosts/linux/src/tools/system/packages.rs#L141-L180)。

请分别补回 include 条件、把进程识别限制移到停止应用语义下。本轮没有构建或运行 Linux。

源码定位：
- [hosts/linux/src/tools/system/packages.rs:126](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/hosts/linux/src/tools/system/packages.rs#L126)
- [hosts/linux/src/tools/system/packages.rs:141](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/hosts/linux/src/tools/system/packages.rs#L141)
- [hosts/linux/src/tools/system/packages.rs:151](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/hosts/linux/src/tools/system/packages.rs#L151)
- [hosts/linux/src/tools/system/packages.rs:175](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/hosts/linux/src/tools/system/packages.rs#L175)
