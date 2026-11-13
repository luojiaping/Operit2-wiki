# Issue 58 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:29:20Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/58#issuecomment-6854350083


本轮复审结论：需修改。Wiki 固定 f9c90d7，对照声明基线 364d1d594 与最新上游 09249fb9。正文第25、72、150行及fact26仍把60秒注册期限写成已有终止保证；实际 JsEngine.rs:582 传入 unlimited，host-api/JavaScriptExecutionInterrupt.rs:57-58 明确无 deadline，旧基线也相同。另独立检查注册 call context、invoke/runJavaScriptJobs 及原生调度器等待，均未发现额外60秒截止时间。请明确这是格式指南要求，当前注册链路未执行该期限，不能声称同步死循环和超时异步注册都会被60秒截停。子包默认启用字段附近已说明脚本METADATA，本轮不将这处表述作为阻断项。已另核原生Wasm四标量ABI与i64字符串返回，未见问题；未运行构建、测试或插件。

源码定位：
- [core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:582](https://github.com/AAswordman/Operit2/blob/09249fb9ff3b660731b88f3846ebc26915ea89f7/core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs#L582)
