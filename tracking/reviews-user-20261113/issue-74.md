# Issue 74 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:30:32Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/74#issuecomment-6854378523


本轮复核正文与159条facts，需修改一组新发现的时态混淆。第40、239、253行写Full Core afterJoined直接等待synchronizeReachablePeer，第48行写独立facade不共享gate；这些来自seed文档开头“现有链路与问题”，是后文方案修复前的问题，不是本页当前调用链。声明基线364d1d594及最新09249fb9的RuntimeRemoteLinkService.rs:1389-1390均仅scheduleSynchronization，和本页第39行不等待业务同步一致。请给旧行为及facts48/57明确历史限定并从当前调用链移除。另核了3秒加工作量门槛、pending标识并集、文件200ms节流及完成条件，未见问题。历史联调均按其日期范围理解，未执行构建或测试。

源码定位：
- [core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1389](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/RuntimeRemoteLinkService.rs#L1389)
