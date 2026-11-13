# Issue 53 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:29:01Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/53#issuecomment-6854342425


本轮结论：需修改。

复核 Wiki f9c90d7a 后，L11 / fact1 及 L57 的“全部 Host trait”总括仍需收窄。这不是新源码漂移：固定基线 364d1d594 的 [Web factory:36–70](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/hosts/web/src/lib.rs#L36-L70) 仅注册显式列出的浏览器适配器，而它使用的 [HostManager 构造器:375–412](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/host-api/src/HostManager.rs#L375-L412) 将 httpServerHost、tcpHost、serialPortHost、serviceDiscoveryHost 等保持为 None，后续没有补齐。请将正文、速览标题和 fact1 改成“注册浏览器环境中已实现的一组 Host 适配器”，避免承诺全量 host-api 能力。同步 JS 调用拒绝 Promise、SQLite 整数跨 JS 边界转字符串等抽样未发现问题。未运行浏览器验证。

源码定位：
- [hosts/web/src/lib.rs:36](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/hosts/web/src/lib.rs#L36)
- [core/crates/foundation/host-api/src/HostManager.rs:375](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/host-api/src/HostManager.rs#L375)
- [core/crates/foundation/host-api/src/HostManager.rs:394](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/host-api/src/HostManager.rs#L394)
