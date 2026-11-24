---
title: Provider——服务聚合
module: core
platforms: [all]
sources: 6
date: 2026-11-11
---

## 概述

- `services` 是当前聚合的 Provider crate，覆盖 LLM 供应商、对话供应商服务、STT/TTS、market、记忆辅助与 runtime support。（core/crates/provider/README.md:9）
- Provider 域拥有 AI 供应商集成与面向供应商的服务，覆盖远程 LLM 供应商、供应商对话编排、媒体供应商、market 服务、记忆供应商辅助与本地模型能力。（core/crates/provider/README.md:3）
- runtime 服务通过显式 handle 使用 Provider 域。（core/crates/provider/README.md:5）
- README 宣称的目标布局是把 services 拆成 `contracts`、`llm`、`chat`、`media`、`memory`、`market` 六个 crate，该拆分是目标不是现状。（core/crates/provider/README.md:14）
- 现状仍是单一 services crate，含 `chat`、`market`、`runtime_support`、`stt`、`tts` 五个公开模块。（core/crates/provider/services/src/lib.rs:3）
- STT、TTS、market 都挂在 services crate 的顶层模块下，与 `chat`、`runtime_support` 并列。（core/crates/provider/services/src/lib.rs:3）
- 本页讲三层：`AIService` 定义供应商接口，ClaudeProvider 是 Anthropic 协议的适配器实现，`EnhancedAIService` 编排对话、工具轮次与 token 用量，ProviderRuntimeSupport 把运行时能力交给 Provider 代码。（core/crates/provider/services/src/chat/EnhancedAIService.rs:84）
- 本页定位见 [[intro-overview|Operit2 是什么]]；对话在节点间交接时经 `resume` 恢复，见 [[arch-routing|路由与转发]]。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1572）

## AI 速览

- `AIService` — 全部模型供应商的公共异步接口。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:131）
- `SendMessageRequest` — 一次供应商请求的完整载荷。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:23）
- `TokenCounts` — 输入、缓存输入、输出三项 token 计数。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:38）
- `AiServiceError` — 供应商共享的错误类型。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:46）
- `SharedAiResponseStream` — 供应商响应流的类型别名。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:20）
- `ClaudeProvider` — Anthropic 协议的供应商适配器。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:31）
- `EnhancedAIService` — 对话编排服务。（core/crates/provider/services/src/chat/EnhancedAIService.rs:84）
- `MessageCancellationToken` — 每轮发送的取消门。（core/crates/provider/services/src/chat/EnhancedAIService.rs:219）
- `ChatGuidanceInbox` — 轮次间传递用户指导的收件箱。（core/crates/provider/services/src/chat/EnhancedAIService.rs:265）
- `SendMessageOptions` — 一次发送的全部控制参数。（core/crates/provider/services/src/chat/EnhancedAIService.rs:350）
- `SendMessageLifecycleStage` — 发送全流程的 22 个阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:525）
- `SendMessageRuntime` — 一次发送的运行时上下文。（core/crates/provider/services/src/chat/EnhancedAIService.rs:561）
- `ProviderRuntimeSupport` — Provider 代码向运行时索取能力的 trait。（core/crates/provider/services/src/runtime_support.rs:281）
- `ProviderRuntimeContext` — 持有 `ProviderRuntimeSupport` 实现的上下文。（core/crates/provider/services/src/runtime_support.rs:406）
- `ChatConfigurationResult` — 一次执行的参与者档案与执行快照。（core/crates/provider/services/src/runtime_support.rs:218）
- `ChatConfigurationRequest` — 解析聊天配置的请求。（core/crates/provider/services/src/runtime_support.rs:59）
- `ChatConfigurationPurpose` — Display 与 Execution 两种配置目的。（core/crates/provider/services/src/runtime_support.rs:48）
- `ProviderFunctionModelBinding` — providerId 与 modelId 的绑定。（core/crates/provider/services/src/runtime_support.rs:23）
- 主入口：EnhancedAIService 的 `sendMessage` — 用户消息经提示词、供应商、工具循环发送。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1463）
- 数据流向：用户消息 → 对话历史准备 → 提示词定稿 → 请求窗口估算 → 模型请求 → 响应流收集 → 工具调用提取 → 工具执行 → 工具结果续轮 → 回复定稿。（core/crates/provider/services/src/chat/EnhancedAIService.rs:525）

## 核心机制

### 聚合 crate 与目标拆分

- `services` 是当前聚合的 Provider crate，覆盖 LLM 供应商、对话供应商服务、STT/TTS、market、记忆辅助与 runtime support。（core/crates/provider/README.md:9）
- `local-model` 是独立 crate，负责本地模型目录、注册表、存储、下载、引擎清单与本地推理支持。（core/crates/provider/README.md:10）
- README 宣称的目标布局是把 services 拆成 `contracts`、`llm`、`chat`、`media`、`memory`、`market` 六个 crate。（core/crates/provider/README.md:14）
- 现状仍是单一 services crate，含 `chat`、`market`、`runtime_support`、`stt`、`tts` 五个公开模块，目标拆分的六个 crate 尚未出现。（core/crates/provider/services/src/lib.rs:3）
- lib.rs 把 `chat::llmprovider::AIService` 的全部公开项重导出到 crate 根。（core/crates/provider/services/src/lib.rs:7）
- lib.rs 把 `runtime_support` 的全部公开项重导出到 crate 根。（core/crates/provider/services/src/lib.rs:8）

### AIService：供应商公共接口

- `AIService` 是 `Send + Sync` 的异步 trait，是全部模型供应商的公共接口。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:131）
- `SendMessageRequest` 包含 `chat_history`、`model_parameters`、`thinking`、`stream`、`available_tools`、`preserve_think_in_history`、`enable_retry`、`on_non_fatal_error`、`on_tool_invocation`。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:28）
- `TokenCounts` 含 `input`、`cached_input`、`output` 三个 i64 计数。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:38）
- `AiServiceError` 有 `ProviderNotImplemented`、`RequestCancelled`、`FirstOutputTimeout`、`ConnectionFailed`、`RequestFailed`、`TokenCalculationFailed` 六个变体。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:48）（core/crates/provider/services/src/chat/llmprovider/AIService.rs:54）
- `AIService` 的 `input_token_count`、`cached_input_token_count`、`output_token_count` 默认实现都返回 0。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:131）（core/crates/provider/services/src/chat/llmprovider/AIService.rs:138）
- `AIService` 的 `provider_model` 默认返回 `"UNKNOWN:unknown"`。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:131）（core/crates/provider/services/src/chat/llmprovider/AIService.rs:148）
- `AIService` 的 `get_models_list` 默认实现返回 `ProviderNotImplemented` 错误。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:131）（core/crates/provider/services/src/chat/llmprovider/AIService.rs:159）
- `AIService` 的 `send_message` 默认实现返回 `ProviderNotImplemented` 错误。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:131）（core/crates/provider/services/src/chat/llmprovider/AIService.rs:166）
- `AIService` 的 `test_connection` 默认实现返回 `ProviderNotImplemented` 错误。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:131）（core/crates/provider/services/src/chat/llmprovider/AIService.rs:176）
- `AIService` 的 `calculate_input_tokens` 默认实现返回 `ProviderNotImplemented` 错误。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:131）（core/crates/provider/services/src/chat/llmprovider/AIService.rs:183）
- `SharedAiResponseStream` 是 `DelegatingRevisableSharedTextStream` 的类型别名。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:20）
- `response_stream_from_chunks` 用已收集的文本块构造可修订响应流。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:62）
- `ensure_response_completed` 在流有 terminal failure 时返回 `RequestFailed`，否则返回 `Ok`。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:85）
- `retry_error_text` 把 `FirstOutputTimeout` 映射为“AI 首字等待超过 120 秒”，其他超时映射为“连接超时”，把 DNS 与主机解析失败映射为“无法解析主机”。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:94）
- `retry_error_text` 把空的 `ConnectionFailed` 与 `RequestFailed` 映射为“网络中断”，把 `RequestCancelled` 映射为“请求已取消”。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:93）（core/crates/provider/services/src/chat/llmprovider/AIService.rs:112）
- `retry_message` 把错误文本格式化为“{错误}，正在进行第 N 次重试...”。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:124）

### ClaudeProvider：Anthropic 适配器

- `ClaudeProvider` 的字段含 `api_endpoint`、`key_getter`、`model_name`、`provider_type`、`enable_tool_call`、`custom_headers`，以及默认关闭的 `enable_claude_1h_prompt_cache`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:35）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:41）
- ClaudeProvider 的 `new` 默认关闭 1 小时提示缓存。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:53）
- `with_claude_1h_prompt_cache` 是 builder 方法，用于开启 1 小时提示缓存。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:75）
- `create_request_body` 写入 `model`、`messages`、`stream`，`system` 非空时才写入，`max_tokens` 未指定时补默认值。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:175）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:184）
- 只有 `enable_tool_call` 为真且 `available_tools` 非空时，请求体才带 `tools`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:189）
- 请求体经 `ThinkingDialect::Anthropic` 应用思考方言，再加已启用的模型参数。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:196）
- `fit_max_tokens_to_thinking_budget` 在思考预算不小于 `max_tokens` 时，若用户显式设置了 `max_tokens` 则返回错误，否则把 `max_tokens` 扩为 budget 加 `DEFAULT_MAX_TOKENS`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1262）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1282）
- `DEFAULT_MAX_TOKENS` 是 4096。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1255）
- `build_serialized_history` 先经 `StructuredToolCallBridge::compileHistoryForProvider` 编译历史。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:222）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:231）
- SYSTEM 轮拼进 `system` 提示词，SUMMARY 与 USER 轮映射为 user 角色消息。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:242）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:251）
- ASSISTANT 与 TOOL_CALL 轮映射为 assistant 角色消息，`enable_tool_call` 为真时走 `build_assistant_content_blocks` 解析工具调用。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:253）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:261）
- TOOL_RESULT 轮映射为 user 角色消息，`enable_tool_call` 为真时走 `build_tool_result_blocks`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:265）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:273）
- assistant 边界上未配对的工具调用由 `missing_tool_result_blocks` 补成 user 消息。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:237）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:244）
- `missing_tool_result_blocks` 生成 `is_error` 为真的 `tool_result` 块，绑定原调用的 `tool_use_id`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:493）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:500）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:508）
- 历史末尾仍有未配对的工具调用时，同样由 `missing_tool_result_blocks` 补一条 user 消息。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:274）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:281）
- `system` 提示词为空时 `system` 字段为 Null，否则为单个 text 块数组。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:286）
- `cache_control_object` 在开启 1 小时缓存时带 ttl 为 `"1h"`，否则只有 type 为 ephemeral。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:288）
- `apply_stable_cache_breakpoints` 给 `tools` 与 `system` 数组的最后一个块补 `cache_control`，已有的 `cache_control` 不被覆盖。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:296）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:303）
- `apply_stable_cache_breakpoints` 给最后一条消息的最后一个内容块补 `cache_control`，已有的 `cache_control` 不被覆盖。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:322）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:344）
- `build_tool_definitions_for_claude` 把每个 `ToolPrompt` 转为 `name`、`description`、`input_schema`，参数 JSON 解析失败时用空对象 schema 兜底。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:397）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:403）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:409）
- `build_content_array` 把文本中的图片链接转为 base64 image 内容块。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:417）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:431）
- 文本与图片均为空时，`build_content_array` 返回 `"[Empty]"` 文本块。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:451）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:464）
- `add_parameters` 只写入 `isEnabled` 的模型参数。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:562）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:568）
- 请求头固定为 `application/json` 与 `anthropic-version` 2023-06-01。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:583）
- `x-api-key` 请求头改由 `key_getter` 在 `sendHttpRequest` 里经 `KeyAuthentication::Header` 附加，`headers` 只拼固定头与 `custom_headers`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:128）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:584）
- OpenAI 兼容口径下，`prompt_tokens` 需减去缓存 token 才得到 `input_base`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:684）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:715）
- Anthropic 口径下 `input_tokens` 本身不含缓存读与缓存创建，缓存创建 token 另行加回 `input`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:697）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:720）
- `cached_input` 取 `cache_read_input_tokens`，依次回退到 `prompt_tokens_details/cached_tokens`、`input_tokens_details/cached_tokens`、`cached_tokens`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:652）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:655）
- 无 `usage` 字段时，token 计数回退到 `TokenCacheManager` 的本地状态。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:49）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:628）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:635）
- `ClaudeProvider` 的 `provider_model` 返回以冒号拼接的 `provider_type` 与 `model_name`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:752）
- `reset_token_counts` 清零 `TokenCacheManager` 与三项 token 计数。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:49）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:758）
- `cancel_streaming` 把 `cancelled` 置为真。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:765）
- `send_message` 流式时经 Host 任务调度器以后台任务 `"claude-response-stream"` 发送，`RequestCancelled` 不视为终端失败，其他错误写入终端失败。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:767）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:782）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:797）
- `send_message` 非流式时返回冷流，只在首次收集时执行一次请求。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:770）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:816）
- `calculate_input_tokens` 用与发送时相同的序列化内容做预估，且不更新已存储的 token 计数。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:835）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:841）
- `send_streaming_message` 在发送前发出 savepoint 修订。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:847）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:855）
- 流式重试时发出 rollback 修订并重置 token 计数。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:898）
- 流式重试要求 `request.enable_retry` 为真且未达 `LlmRetryPolicy::MAX_RETRY_ATTEMPTS`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:888）
- 非流式重试同样要求 `enable_retry` 为真且未达 `MAX_RETRY_ATTEMPTS`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:912）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:942）
- 非流式响应按有无 `choices` 字段区分 OpenAI 兼容与 Anthropic 两种解析：有 `choices` 按 OpenAI 口径算 `usage`，否则按 Anthropic 口径。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:953）
- 非流式响应由 `parse_anthropic_non_streaming` 生成内容，包成单块流返回。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:959）
- `process_streaming_response` 对 JSON 媒体类型直接按非流式解析，否则按 SSE 解码。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:968）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:976）
- `"[DONE]"` 事件标志流式响应完成。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1058）
- `message_stop` 事件标志流式响应完成。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1191）
- 流在完成前结束时返回 `ConnectionFailed`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1040）
- `content_block_start` 的 `tool_use` 块仅在 `enable_tool_call` 为真时处理，转为随机标签名的 XML 工具调用标记。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1099）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1106）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1115）
- `thinking` 内容块转为 `<think>` 标记包裹的思考文本。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1125）
- `parse_anthropic_non_streaming` 把 `text` 与 `thinking` 块拼成文本，`thinking` 包在 `<think>` 标记内。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1199）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1218）
- `parse_anthropic_non_streaming` 的 `tool_use` 块仅在 `enable_tool_call` 为真时转为随机标签名的 XML 标记。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1199）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1225）
- 无 `content` 数组时，`parse_anthropic_non_streaming` 回退读取 `choices/0/message/content`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1203）

### EnhancedAIService：对话编排

- `EnhancedAIService` 持有 `multi_service_manager`、`conversation_service`、`tool_handler`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:89）
- `EnhancedAIService` 持有 `provider_runtime_context` 与共享状态 `shared_state`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:84）（core/crates/provider/services/src/chat/EnhancedAIService.rs:96）
- 共享状态记录 `turn_token_usage`、`request_window_estimate`、`active_execution_contexts` 与 `execution_generation`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:109）
- 共享状态记录 `last_reply_content`、`last_provider_model`、`last_turn_model_identity` 与 `pendingRouteChange`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:113）（core/crates/provider/services/src/chat/EnhancedAIService.rs:117）
- `createExecutionContext` 在 generation 不匹配或取消令牌已取消时返回 `RequestCancelled`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:129）（core/crates/provider/services/src/chat/EnhancedAIService.rs:136）
- `invalidateExecutionContexts` 把 `execution_generation` 加一，并把全部活动执行上下文标为不活跃。（core/crates/provider/services/src/chat/EnhancedAIService.rs:165）
- `beginTurn` 在后台响应任务开始前记录选定的模型：`last_provider_model` 与 `last_turn_model_identity`，其中 `providerName` 取 `config.providerName`，`modelName` 取 `config.modelId`，并清空上一轮的回复与 token 用量。（core/crates/provider/services/src/chat/EnhancedAIService.rs:174）（core/crates/provider/services/src/chat/EnhancedAIService.rs:185）
- `SendMessageCallbacks` 只有 `onNonFatalError` 与 `onTokenLimitExceeded` 两个必需方法，均无默认实现；工具调用回调仍由 `SendMessageOptions` 的 `onToolInvocation` 字段承载。（core/crates/provider/services/src/chat/EnhancedAIService.rs:191）（core/crates/provider/services/src/chat/EnhancedAIService.rs:350）（core/crates/provider/services/src/chat/EnhancedAIService.rs:375）
- `MessageCancellationToken` 用共享的 `MessageCancellationState` 做取消门（`AtomicBool` 取消标志加 `Notify` 唤醒信号），`cancel` 置真并唤醒等待者，`isCancelled` 读取，新增异步 `cancelled` 等待取消。（core/crates/provider/services/src/chat/EnhancedAIService.rs:223）（core/crates/provider/services/src/chat/EnhancedAIService.rs:236）
- `ChatGuidanceInbox` 的 `enqueue` 拒绝空消息与已关闭的回合。（core/crates/provider/services/src/chat/EnhancedAIService.rs:285）（core/crates/provider/services/src/chat/EnhancedAIService.rs:287）
- `drainOrClose` 在无待处理指导时关闭收件箱，之后 `enqueue` 全部拒绝；有待处理指导时返回全部条目且保持开放。（core/crates/provider/services/src/chat/EnhancedAIService.rs:315）
- `SendMessageOptions` 默认 `maxTokens` 0、`tokenUsageThreshold` 0.0。（core/crates/provider/services/src/chat/EnhancedAIService.rs:389）（core/crates/provider/services/src/chat/EnhancedAIService.rs:396）
- `SendMessageOptions` 默认 `functionType` 与 `promptFunctionType` 都是 CHAT，`enableThinking` 为 false。（core/crates/provider/services/src/chat/EnhancedAIService.rs:389）（core/crates/provider/services/src/chat/EnhancedAIService.rs:403）
- `SendMessageOptions` 默认 `stream` 为 true。（core/crates/provider/services/src/chat/EnhancedAIService.rs:389）（core/crates/provider/services/src/chat/EnhancedAIService.rs:417）
- PreparedRequestWindow 的 `completeHistory` 只在历史长度等于请求时的长度时补一条助手回复，且同一轮最多补一次；空回复不产生合成回合。（core/crates/provider/services/src/chat/EnhancedAIService.rs:506）
- `SendMessageLifecycleStage` 列出从 `SetProcessingState` 到 `UnregisterExecutionContext` 的 22 个发送阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:526）（core/crates/provider/services/src/chat/EnhancedAIService.rs:538）（core/crates/provider/services/src/chat/EnhancedAIService.rs:547）
- `SendMessageRuntime` 含 `modelConfig`、`modelParameters`、`availableTools` 与 `aiService`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:561）（core/crates/provider/services/src/chat/EnhancedAIService.rs:578）（core/crates/provider/services/src/chat/EnhancedAIService.rs:581）
- `RuntimePromptHistoryHooks` 把 `HistoryHookContext` 转为 `PromptHookContext` 分发历史钩子，并要求钩子保留 `prompt_function_type` 与 `processed_input`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:697）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3872）
- `RuntimeSystemPromptComposer` 从 `tool_handler` 的 Host 环境与运行时存储 Host 解析工作区路径，每次请求重新解析。（core/crates/provider/services/src/chat/EnhancedAIService.rs:732）（core/crates/provider/services/src/chat/EnhancedAIService.rs:733）
- 系统提示词组合从 `provider_runtime_context` 取 `aiVisibleSkillPackages`，取不到时 panic。（core/crates/provider/services/src/chat/EnhancedAIService.rs:797）（core/crates/provider/services/src/chat/EnhancedAIService.rs:799）
- 启用的包列表排除 ToolPkg 容器包。（core/crates/provider/services/src/chat/EnhancedAIService.rs:779）
- EnhancedAIService 的 `new` 用 `provider_runtime_context` 创建 `ConversationService`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:850）
- `MultiServiceManager::from_runtime_context` 要求 runtime support 提供 data 目录，否则 panic。（core/crates/provider/services/src/chat/EnhancedAIService.rs:856）
- `getAIServiceForFunction` 直接返回 `runtime.aiService`，忽略 `functionType` 与 provider/model 覆盖参数。（core/crates/provider/services/src/chat/EnhancedAIService.rs:882）（core/crates/provider/services/src/chat/EnhancedAIService.rs:889）
- `getProviderAndModelForFunction` 在第一个冒号处切分 `providerModel`，无冒号时 panic。（core/crates/provider/services/src/chat/EnhancedAIService.rs:892）
- `getModelConfigForFunction` 直接返回 `runtime.modelConfig`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:902）（core/crates/provider/services/src/chat/EnhancedAIService.rs:909）
- `refreshServiceForFunction` 在刷新失败时 panic。（core/crates/provider/services/src/chat/EnhancedAIService.rs:916）
- `refreshAllServices` 在刷新失败时 panic。（core/crates/provider/services/src/chat/EnhancedAIService.rs:923）
- `estimatePreparedRequestWindow` 调服务句柄的 `calculate_input_tokens` 估算请求窗口，`publishEstimate` 为真时发布估算值。（core/crates/provider/services/src/chat/EnhancedAIService.rs:942）（core/crates/provider/services/src/chat/EnhancedAIService.rs:952）
- `prepareConversationHistory` 从模型配置能力取 `toolCall`、`directImage`、`directAudio`、`directVideo`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1012）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1036）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1037）
- `prepareConversationHistory` 把执行上下文的 `chatId` 与 `participantId` 交给系统提示词组合器。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1012）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1046）
- `prepareConversationHistory` 完成后把附件路径改写为相对路径。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1012）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1091）
- `generateSummary` 经 `ConversationService` 与 `multi_service_manager` 生成摘要。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1097）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1103）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1172）
- `generateConversationTitle` 经 `ConversationService` 与 `multi_service_manager` 生成标题。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1172）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1203）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1211）
- `generateSummaryForConfiguration` 在已选定的原生参与者下运行摘要，并走 `ToolExposureMode::Full` 的工具运行时上下文。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1166）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1177）
- `getAvailableToolsForFunction` 在 `runtime.availableTools` 非空时直接返回，否则在 `functionType` 不是 CHAT 或模型不支持 `toolCall` 时返回空列表。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1215）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1225）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1228）
- Cli 暴露模式下工具列表由 `CliToolModeSupport::buildCliPublicToolPrompts` 生成。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1233）
- Full 暴露模式下工具列表取系统工具分类中已在 `tool_handler` 注册的工具，再追加 `package_proxy` 代理工具。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1236）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1264）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3312）
- `estimateRequestWindowFromMemory` 先用 `prepareConversationHistory` 准备历史，再用 `getAvailableToolsForFunction` 取工具。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1293）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1309）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1318）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1281）
- `estimateRequestWindowFromMemory` 调用 `estimatePreparedRequestWindow` 估算已准备请求的窗口大小。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1293）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1372）
- `registerExecutionContext` 与 `unregisterExecutionContext` 把执行上下文登记进或移出共享状态。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1381）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1387）
- `invalidateAllExecutionContexts` 使全部活动执行上下文失效。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1417）
- `isExecutionContextActive` 要求上下文仍活跃、取消令牌未取消、且共享状态中仍登记为活跃。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1440）
- `startAssistantResponseRound` 开新一轮并清空 `streamBuffer`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1444）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1446）
- `sendMessage` 先检查取消令牌，再解析聊天配置，最后走 `sendMessageWithConfiguration`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1463）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1480）
- `sendMessageWithConfiguration` 先校验 `ChatConfigurationResult`，失败返回 `RequestFailed`；再把 `participantName`、`executionParticipantId`、`chatConfiguration` 写进 options。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1483）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1494）
- `chatConfigurationRequestForOptions` 要求 provider 与 model 覆盖必须同时设置，否则返回 `RequestFailed`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1503）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1524）
- 未设覆盖时，默认模型绑定取 `support` 的 `modelBindingForChat`，传聊天 id 与 `functionType`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1521）
- `resolveChatConfigurationForOptions` 经 `provider_runtime_context` 的 `support()` 再调 `resolveChatConfiguration` 解析执行配置。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1544）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1549）
- `resume` 直接复用 `sendMessage`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1572）
- `requestCoreRouteChange` 转给 `tool_handler` 的 `runtimeSupport()` 再调 `requestCoreRouteChange`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1587）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1593）
- `createSendMessageRuntime` 先校验配置，再按 `profile.modelBinding` 取服务包，得到 `modelConfig`、`modelParameters` 与 `aiService`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1601）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1610）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1643）
- `createSendMessageRuntime` 把 `disableUserPreferenceDescription` 固定为 false，注释说明插件执行档案已应用持久化的 USER.md 策略。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1601）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1628）
- `createSendMessageRuntime` 的识别标志 `hasImageRecognition`、`hasAudioRecognition`、`hasVideoRecognition` 由 `multi_service_manager` 的 `hasImageRecognitionConfigured`、`hasAudioRecognitionConfigured`、`hasVideoRecognitionConfigured` 判定；直连标志 `chatModelHasDirectImage`、`chatModelHasDirectAudio`、`chatModelHasDirectVideo` 与 `useToolCallApi` 仍取模型能力。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1601）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1630）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1633）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1636）
- `createSendMessageRuntime` 按 `modelConfig.apiProviderType` 解析工具暴露模式，分为 CLI 与 Full。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1601）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1638）
- `sendMessageWithRuntime` 在调度前捕获 `execution_generation`，并用它创建执行上下文。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1650）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1657）
- `sendMessageWithRuntime` 把响应任务以 `"enhanced-ai-response"` 为名交给 Host 任务调度器异步执行。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1650）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1671）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1686）
- 响应任务出错时，取消或 generation 已变的错误不写入终端失败、不改输入处理状态；其他错误写入终端失败并把输入处理状态置为 Error。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1711）
- `executeSendMessageWithRuntime` 在准备历史前记录 `PrepareConversationHistory` 阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1749）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1818）
- `executeSendMessageWithRuntime` 在发模型请求前记录 `SendMessageRequest` 阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1749）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2016）
- `executeSendMessageWithRuntime` 在收流时记录 `CollectResponseStream` 阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1749）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2081）
- `executeSendMessageWithRuntime` 在落 token 用量时记录 `PersistTokenUsage` 阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1749）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2174）
- `executeSendMessageWithRuntime` 在处理流完成时记录 `ProcessStreamCompletion` 阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1749）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2219）
- `executeSendMessageWithRuntime` 在注销执行上下文时记录 `UnregisterExecutionContext` 阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1749）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2320）
- `processToolResults` 在工具结果消息为空白时返回 `RequestFailed`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2346）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2375）
- `processToolResults` 在 `guidanceInbox` 有待处理指导时暂停，不发下一轮模型请求，返回 false。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2346）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2445）
- `processToolResults` 在 `maxTokens` 大于 0 且当前 token 用量占比达到 `tokenUsageThreshold` 时触发超限。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2346）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2509）
- token 超限时触发 `onTokenLimitExceeded` 回调并使执行上下文失效，返回 false。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2528）
- `processToolResults` 的续轮模型请求设置 `enable_retry` 为 true。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2536）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2580）
- 首次模型请求同样设置 `enable_retry` 为 true。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2054）
- `processStreamCompletion` 循环处理模型轮次与工具轮次：无工具调用时完成，有工具调用时执行工具并把结果送回模型，任一环节返回停止信号时结束。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2707）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2721）
- `completeResponseRound` 在内容为空且 `disableWarning` 为真时直接定稿助手回复并结束；`disableWarning` 为假时发出空回复警告并继续一轮。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2802）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2806）
- 纯思考回复且 `disableWarning` 为真时，`completeResponseRound` 直接定稿。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2802）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2851）
- 纯思考回复且 `disableWarning` 为假时，`completeResponseRound` 发出纯思考警告并继续一轮。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2802）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2851）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2864）
- `completeResponseRound` 先用 `enhanceToolDetection` 规范化工具调用 XML。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2802）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2875）
- 无工具调用时，`completeResponseRound` 定稿助手回复并结束。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2802）
- `handleToolInvocation` 要求至少一次调用，空列表返回 `RequestFailed`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2959）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2976）
- `handleToolInvocation` 对每次调用触发 `onToolInvocation` 回调，显示名经 `resolveToolDisplayName` 解析。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2959）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3001）
- `handleToolInvocation` 经 `ToolExecutionManager::executeInvocations` 执行整批工具调用，并传入 `extensionOwner` 与 `executionData`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2959）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3020）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3030）
- 工具批产生 `routeChangeIntent` 时，`handleToolInvocation` 把意图存入 `pendingRouteChange` 并暂停本轮。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2959）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3042）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3046）
- `finalizeAssistantResponse` 只保存最后回复内容。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3140）
- `cancelConversation` 使全部执行上下文失效、取消全部流式发送、结束当前 token 请求，并把输入处理状态置回 Idle。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3145）
- `beginRequestTokenUsage` 在上下文不活跃或已取消时返回 `RequestCancelled`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3210）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3220）
- `setCurrentTurnTokenCounts` 把负数 token 计数钳制为 0。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3241）
- `apply_finalized_current_user_turn` 在末轮 USER 内容与定稿相同时不改，与原文相同时替换为定稿内容（定稿为空时把该轮清空）；定稿为空且不命中前两种情况时返回历史，不追加新轮。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3281）
- `apply_finalized_current_user_turn` 在其他情况下追加一个新的 USER 轮。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3281）
- `resolveToolDisplayName` 把 `package_proxy` 与 `proxy` 解析为 `tool_name` 参数值，其他工具直接用工具名。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3311）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3317）
- `package_proxy` 有 `tool_name` 参数，类型 string，必填。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3326）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3335）
- `package_proxy` 有 `params` 参数，类型 object，必填。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3326）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3339）
- `toolRuntimeContextForConfiguration` 先校验 `ChatConfigurationResult`，再构建 `ToolRuntimeContext`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3579）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3587）
- 工具运行时上下文含 `callerParticipantId`（取配置 `profile.id`）、`extensionOwner` 与 `executionData`，暴露模式 Full 映射 FULL、Cli 映射 CLI。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3590）（core/crates/provider/services/src/chat/EnhancedAIService.rs:3598）
- `function_type_name` 覆盖 CHAT、SUMMARY、TITLE_GENERATION、MEMORY、UI_CONTROLLER、TRANSLATION、GREP、ROLE_RESPONSE_PLANNER、IMAGE_RECOGNITION、AUDIO_RECOGNITION、VIDEO_RECOGNITION 共 11 种功能类型。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3605）
- `prompt_function_type_name` 只有 CHAT 与 VOICE 两种。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3621）
- `resolve_workspace_path_mappings` 经 `VisualFileSystem` 校验并规范化路径，按规范化后的 vfs 路径去重，返回 `WorkspacePathMapping` 列表。（core/crates/provider/services/src/chat/EnhancedAIService.rs:3690）

### ProviderRuntimeSupport：向运行时索取能力

- `ProviderRuntimeSupport` 是 `Send + Sync` 的 trait，向 Provider 代码提供运行时拥有的数据与插件操作。（core/crates/provider/services/src/runtime_support.rs:281）
- `ProviderRuntimeSupport` 的 `generateLocalLlm` 默认实现返回错误，提示本地 LLM 运行时支持不可用。（core/crates/provider/services/src/runtime_support.rs:285）
- `ProviderRuntimeSupport` 要求实现方提供 `updateTokensForProviderModel`。（core/crates/provider/services/src/runtime_support.rs:281）（core/crates/provider/services/src/runtime_support.rs:291）
- `ProviderRuntimeSupport` 要求实现方提供 `disableUserPreferenceDescription` 与 `defaultTtsConfigId`。（core/crates/provider/services/src/runtime_support.rs:281）（core/crates/provider/services/src/runtime_support.rs:301）
- `ProviderRuntimeSupport` 要求实现方提供 `resolveChatConfiguration` 与 `aiVisibleSkillPackages`。（core/crates/provider/services/src/runtime_support.rs:281）（core/crates/provider/services/src/runtime_support.rs:309）
- `ProviderRuntimeSupport` 要求实现方提供 `modelBindingForFunction` 与 `resolvedModelConfig`。（core/crates/provider/services/src/runtime_support.rs:281）（core/crates/provider/services/src/runtime_support.rs:318）（core/crates/provider/services/src/runtime_support.rs:328）
- `ProviderRuntimeSupport` 要求实现方提供 `providerProfile`。（core/crates/provider/services/src/runtime_support.rs:356）（core/crates/provider/services/src/runtime_support.rs:407）
- `loadCodexTokens` 默认实现返回错误，要求 Codex 授权。（core/crates/provider/services/src/runtime_support.rs:338）
- `saveCodexTokens` 默认实现返回错误，Codex 授权无法保存。（core/crates/provider/services/src/runtime_support.rs:345）
- `ProviderRuntimeSupport` 提供 `hasToolPkgAiProvider` 与 `toolPkgAiProvider` 查询 ToolPkg AI 供应商注册。（core/crates/provider/services/src/runtime_support.rs:369）（core/crates/provider/services/src/runtime_support.rs:407）
- `ProviderRuntimeSupport` 提供 `runToolPkgAiProviderHook` 调用 ToolPkg AI 供应商函数。（core/crates/provider/services/src/runtime_support.rs:375）（core/crates/provider/services/src/runtime_support.rs:407）
- `ProviderRuntimeSupport` 提供 `decodeToolPkgHookResult` 解码 ToolPkg 钩子结果。（core/crates/provider/services/src/runtime_support.rs:390）（core/crates/provider/services/src/runtime_support.rs:407）
- `ProviderRuntimeSupport` 提供 `messageTimingNow` 取时间快照与 `logMessageTiming` 写时间日志。（core/crates/provider/services/src/runtime_support.rs:393）（core/crates/provider/services/src/runtime_support.rs:407）
- `ProviderRuntimeContext` 用 `Arc` 持有任意一个 `ProviderRuntimeSupport` 实现。（core/crates/provider/services/src/runtime_support.rs:407）
- `ProviderRuntimeContext` 提供 `support` 取引用与 `shared_support` 取共享 `Arc`。（core/crates/provider/services/src/runtime_support.rs:412）（core/crates/provider/services/src/runtime_support.rs:422）
- `ProviderFunctionModelBinding` 含 `providerId` 与 `modelId`。（core/crates/provider/services/src/runtime_support.rs:24）
- `ProviderMessageTiming` 只含 `startedAtMs`。（core/crates/provider/services/src/runtime_support.rs:35）
- `ProviderPackageInfo` 含 `name` 与 `description`。（core/crates/provider/services/src/runtime_support.rs:41）
- `ChatConfigurationPurpose` 分 Display 与 Execution：Display 只解析展示，不选执行档案；Execution 解析已认证参与者与执行快照。（core/crates/provider/services/src/runtime_support.rs:51）
- `ChatConfigurationRequest` 含 `purpose`、`chatId`、`chatExtension`、`participantId`、`promptFunctionType`、`defaultModelBinding`、`defaultTtsConfigId`。（core/crates/provider/services/src/runtime_support.rs:64）
- `requirePurpose` 拒绝跨目的调用；Display 目的不接受 execution participant。（core/crates/provider/services/src/runtime_support.rs:77）
- `ChatConfigurationDisplayResult` 只含展示数据与显式初始消息，不含可执行档案。（core/crates/provider/services/src/runtime_support.rs:117）
- ChatConfigurationDisplayResult 的 `validate` 要求 `extensionOwner` 已认证。（core/crates/provider/services/src/runtime_support.rs:130）
- ChatConfigurationDisplayResult 的 `validate` 要求 `contextKey` 与 `identity` 要么同时绑定、要么同时为空；无绑定时不得声明参与者或初始消息。（core/crates/provider/services/src/runtime_support.rs:134）
- ChatConfigurationDisplayResult 的 validate 要求参与者 `id` 与 `name` 非空且不重复，初始消息作者必须是已声明参与者。（core/crates/provider/services/src/runtime_support.rs:150）
- `ChatResourceRoute` 含 `key`、`readable`、`writable`。（core/crates/provider/services/src/runtime_support.rs:171）
- `ChatToolAccess` 含 `enabled`、`allowedBuiltinTools`、`allowedPackages`、`allowedSkills`、`allowedMcpServers`。（core/crates/provider/services/src/runtime_support.rs:182）
- `ChatParticipantProfile` 含 `id`、`name`、`avatarUri`、`introPrompt`、`userPreferencesText`、`openingStatement`、`modelBinding`、`ttsConfigId`、`toolAccess`、`resources`。（core/crates/provider/services/src/runtime_support.rs:192）（core/crates/provider/services/src/runtime_support.rs:198）
- `ChatHistoryPolicy` 含 `isolateParticipants` 与 `labelUserMessages`。（core/crates/provider/services/src/runtime_support.rs:210）
- `ChatConfigurationResult` 含 `contextKey`、`historyPolicy`、`profile`、`participants`、`executionData`、`extensionOwner`。（core/crates/provider/services/src/runtime_support.rs:218）（core/crates/provider/services/src/runtime_support.rs:224）
- ChatConfigurationResult 的 `validate` 要求 `contextKey` 非空、`extensionOwner` 已认证、`participants` 非空、`executionData` 非空。（core/crates/provider/services/src/runtime_support.rs:237）
- ChatConfigurationResult 的 validate 要求每位参与者的 `modelBinding` 的 `providerId` 与 `modelId` 以及 `ttsConfigId` 非空，资源路由 `key` 非空且不重复。（core/crates/provider/services/src/runtime_support.rs:255）（core/crates/provider/services/src/runtime_support.rs:264）
- ChatConfigurationResult 的 validate 要求选定的 `profile` 必须是已声明参与者中的精确一项。（core/crates/provider/services/src/runtime_support.rs:272）

## 关键符号

- `AIService` — 全部模型供应商的公共异步接口。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:131）
- `SendMessageRequest` — 一次供应商请求的完整载荷。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:23）
- `TokenCounts` — 输入、缓存输入、输出三项 token 计数。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:38）
- `AiServiceError` — 供应商共享的错误类型。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:46）
- `SharedAiResponseStream` — 供应商响应流的类型别名。（core/crates/provider/services/src/chat/llmprovider/AIService.rs:20）
- `ClaudeProvider` — Anthropic 协议的供应商适配器。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:31）
- `EnhancedAIService` — 对话编排服务。（core/crates/provider/services/src/chat/EnhancedAIService.rs:84）
- `MessageCancellationToken` — 每轮发送的取消门。（core/crates/provider/services/src/chat/EnhancedAIService.rs:219）
- `ChatGuidanceInbox` — 轮次间传递用户指导的收件箱。（core/crates/provider/services/src/chat/EnhancedAIService.rs:265）
- `SendMessageOptions` — 一次发送的全部控制参数。（core/crates/provider/services/src/chat/EnhancedAIService.rs:350）
- `SendMessageRuntime` — 一次发送的运行时上下文。（core/crates/provider/services/src/chat/EnhancedAIService.rs:561）
- `SendMessageLifecycleStage` — 发送全流程的 22 个阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:525）
- `ProviderRuntimeSupport` — Provider 代码向运行时索取能力的 trait。（core/crates/provider/services/src/runtime_support.rs:281）
- `ProviderRuntimeContext` — 持有 `ProviderRuntimeSupport` 实现的上下文。（core/crates/provider/services/src/runtime_support.rs:406）
- `ChatConfigurationResult` — 一次执行的参与者档案与执行快照。（core/crates/provider/services/src/runtime_support.rs:218）
- `ChatConfigurationPurpose` — Display 与 Execution 两种配置目的。（core/crates/provider/services/src/runtime_support.rs:48）
- `ProviderFunctionModelBinding` — `providerId` 与 `modelId` 的绑定。（core/crates/provider/services/src/runtime_support.rs:23）
- `DEFAULT_MAX_TOKENS` — 未指定 `max_tokens` 时的默认值 4096。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:1255）
- `ChatToolAccess` — 工具来源策略：内置工具、包、技能、MCP 服务器的允许清单。（core/crates/provider/services/src/runtime_support.rs:182）
- `ChatParticipantProfile` — 一位执行参与者的完整档案：身份、提示词、模型绑定、语音配置、工具访问、资源路由。（core/crates/provider/services/src/runtime_support.rs:192）（core/crates/provider/services/src/runtime_support.rs:198）

## 调用链

1. `sendMessage` 检查取消令牌，再解析聊天配置，最后走 `sendMessageWithConfiguration`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1463）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1480）
2. `sendMessageWithConfiguration` 校验 `ChatConfigurationResult`，把参与者信息写进 options。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1483）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1493）
3. `createSendMessageRuntime` 按 `profile.modelBinding` 取服务包，得到 `modelConfig`、`modelParameters` 与 `aiService`。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1601）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1610）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1643）
4. `sendMessageWithRuntime` 捕获 `execution_generation`，创建执行上下文。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1650）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1657）
5. `sendMessageWithRuntime` 把响应任务以 `"enhanced-ai-response"` 为名交给 Host 任务调度器异步执行。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1650）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1671）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1686）
6. `executeSendMessageWithRuntime` 准备对话历史，记录 `PrepareConversationHistory` 阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1749）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1818）
7. 执行 `before_finalize_prompt` 与 `before_send_to_model` 两轮提示词定稿钩子。（core/crates/provider/services/src/chat/EnhancedAIService.rs:678）（core/crates/provider/services/src/chat/EnhancedAIService.rs:1951）
8. 估算已准备请求的窗口大小，记录 `EstimatePreparedRequestWindow` 阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1988）
9. 向 `AIService` 发模型请求，记录 `SendMessageRequest` 阶段，`enable_retry` 为 true。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1912）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2016）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2054）
10. 收集响应流，记录 `CollectResponseStream` 阶段，落 token 用量时记录 `PersistTokenUsage` 阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2081）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2174）
11. `processStreamCompletion` 循环：`completeResponseRound` 定稿或返回工具动作，`handleToolInvocation` 执行工具，`processToolResults` 把工具结果送回模型。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2707）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2747）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2753）（core/crates/provider/services/src/chat/EnhancedAIService.rs:2773）
12. 无工具调用时定稿助手回复，注销执行上下文，记录 `UnregisterExecutionContext` 阶段。（core/crates/provider/services/src/chat/EnhancedAIService.rs:2320）
- ClaudeProvider 的 `send_message` 流式时经 Host 任务调度器以后台任务 `"claude-response-stream"` 发送，`RequestCancelled` 不视为终端失败，其他错误写入终端失败。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:770）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:785）
14. `create_request_body` 组装 Anthropic 请求体：`model`、`messages`、`stream`、`system`、`max_tokens`、条件 `tools`。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:171）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:179）（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:186）
15. `process_streaming_response` 对 JSON 媒体类型按非流式解析，否则按 SSE 解码事件流。（core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs:965）
16. `resume` 在目标 CoreNode 上同步历史后直接复用 `sendMessage` 恢复模型处理，见 [[arch-routing|路由与转发]]。（core/crates/provider/services/src/chat/EnhancedAIService.rs:1572）

## 来源

- core/crates/provider/README.md
- core/crates/provider/services/src/lib.rs
- core/crates/provider/services/src/chat/EnhancedAIService.rs
- core/crates/provider/services/src/chat/llmprovider/AIService.rs
- core/crates/provider/services/src/chat/llmprovider/ClaudeProvider.rs
- core/crates/provider/services/src/runtime_support.rs
