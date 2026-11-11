作者：luojiaping
时间：2026-11-11T08:51:39Z UTC
comment_id：6791469198

审查结论：**需修改**。

审查版本：wiki `f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50`；已核实上游 `AAswordman/Operit2` 最新 `main` 为 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与条目标注一致。

1. **[P2] 依赖调用的 main 限制写到了错误角色上。** [正文第 166 行](https://github.com/luojiaping/Operit2-wiki/blob/f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50/review/batch-02/core-tool-packages-mcp.md#L166)及 [facts 第 108 条（第 431 行）](https://github.com/luojiaping/Operit2-wiki/blob/f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50/review/batch-02/core-tool-packages-mcp.facts.json#L431)写“依赖调用方必须是……main 运行时”。实际 [ToolJsRuntime.rs:348–351](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/tool/services/src/tools/ToolJsRuntime.rs#L348)检查 `!isMainTarget || callerName == packageTarget`，要求的是**被调用提供方的目标为 main，且提供方包不同于调用方包**，没有要求调用方自身为 main。

[JsEngine.rs:2065–2078](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs#L2065)也只要求调用方绑定 ToolPkg context，并把请求的目标 runtime 设为 `"main"`。建议正文和 facts 同步更正调用方/提供方，保留后续依赖声明、版本范围和公开 API 校验；否则会误导开发者以为 UI/provider 等绑定上下文均被此分支禁止。

2. **[P2] 技能激活不能套用冒号工具命名规则。** [正文第 15 行](https://github.com/luojiaping/Operit2-wiki/blob/f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50/review/batch-02/core-tool-packages-mcp.md#L15)称三类入口都以冒号分段；包工具和 MCP 工具使用该命名空间，技能激活入口是 `use_package` 的 `package_name` 参数。[ToolRegistration.rs:83](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/tool/services/src/tools/ToolRegistration.rs#L83)读取参数，[RuntimePackageManager.rs:959–972](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/tool/services/src/tools/packTool/RuntimePackageManager.rs#L959)处理技能并返回 `getSkillSystemPrompt` 生成的提示词。

建议改为“包工具和 MCP 工具以冒号分隔命名空间；技能使用 use_package(package_name=技能名) 激活并返回指令提示词”，并补充实际激活调用链，避免让读者尝试不存在的 skillName:toolName 格式。

另已核对包工具命名校验、技能双位置扫描、MCP 参数/图片结果以及依赖契约检查。

本轮为正文、对应 facts 和所列实现分支的静态核对，未执行编译、构建或测试。结论限于上述核对范围。

