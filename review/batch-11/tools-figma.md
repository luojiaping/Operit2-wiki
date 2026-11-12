---
title: Figma 界面桥接工具
module: tools
platforms: [all]
sources: 3
date: 2026-11-11
---

## 概述

- 本页讲 tools/figma 的 Figma 界面桥接工具，当前为静态图层。`tools/figma/README.md:1`
- 目标是让设计同学在 Figma 中使用和编辑完整应用，包括页面导航、弹窗、工具结果以及插件内部 UI。当前实现尚未达到这个目标。`tools/figma/README.md:3`
- 本目录现有插件只能导入可编辑的界面图层，批量 ZIP 也是多个静态场景的集合。`tools/figma/README.md:5`
- 现有插件没有应用运行时，没有恢复原来的点击、输入、状态更新或插件事件，不能作为完整可交互软件交付。`tools/figma/README.md:5`
- 主题参数的回传不能代表任意软件界面修改已经应用。`tools/figma/README.md:5`
- 交互应用的验收标准、现有 Web 实现和需要解决的架构问题见 `INTERACTIVE_APP.md`，以下说明只描述已有静态工具。`tools/figma/README.md:7`
- 实时运行与编辑连接的启动方法、候选 Code layer 项目及未完成项见 `LIVE.md`，它与静态导入插件是不同入口，整软件的 Figma 验收尚未完成。`tools/figma/README.md:168`

## AI 速览

- `Operit · UI Design Bridge` — 静态图层 Figma 插件，文件交接导入可编辑图层并回传主题修改。`tools/figma/README.md:24`
- `.operit-design.json` — 两个入口共用的设计文件格式。`tools/figma/README.md:9`
- `capture.mjs` — VM Service 只读采集命令，采集运行中的 Flutter 渲染树与插件 WebView 的 DOM。`tools/figma/README.md:114`
- `OperitDesignRuntime` — 已接入真实 Flutter 输入与受支持的渲染属性修改的实时运行时。`tools/figma/INTERACTIVE_APP.md:25`
- `live.mjs` — 通过 VM Service 连接运行端的实时连接服务。`tools/figma/INTERACTIVE_APP.md:25`
- `src/bridge.ts` — 文件契约、主题 schema 校验、来源与图层变更。`tools/figma/README.md:111`
- `src/plugin.ts` — Figma 原生节点、组件、变量、素材导入与修改回传。`tools/figma/README.md:112`
- `src/theme_scene.ts` — 主题组件起点。`tools/figma/README.md:113`
- `build-live.mjs` — 生成候选 Code layer Web 项目。`tools/figma/INTERACTIVE_APP.md:25`
- 主入口一：主题组件稿，Theme Studio 导出 Figma，生成手机与桌面、浅色与深色的可编辑组件。`tools/figma/README.md:11`
- 主入口二：运行时页面，采集运行中的 Flutter 渲染树与插件 WebView 的 DOM。`tools/figma/README.md:12`
- 数据流向一句话：Theme Studio 或运行中应用产出 `.operit-design.json`，Figma 插件导入为原生图层，设计修改导出回传。`tools/figma/README.md:9`
- 实时入口另走 `live.mjs` 连接同一台电脑上的 debug 应用。`tools/figma/LIVE.md:20`
- 交付状态：`INTERACTIVE_APP.md` 的状态是需求与架构边界已确认，完整应用实现和真实 Figma 验收尚未完成，核查日期为 2026-10-30。`tools/figma/INTERACTIVE_APP.md:3`

## 核心机制

### 两个入口与共用格式

- 两个入口使用同一份 `.operit-design.json` 文件。`tools/figma/README.md:9`
- 主题组件稿入口由 Theme Studio 的导出 Figma 生成手机与桌面、浅色与深色的可编辑组件，绑定仓库的真实主题字段，它是组件起点，布局为示意，精确页面走运行时采集。`tools/figma/README.md:11`
- 运行时页面入口采集运行中的 Flutter 渲染树以及插件 WebView 的 DOM，覆盖深层工具结果、Compose DSL 插件、工作区嵌入面板和弹窗，无需给每个页面另写一套 Figma 模板。`tools/figma/README.md:12`
- 主题工作流见 [[tools-theme-studio|主题工具与 Web Studio]]，本页只写 Figma 一侧的交接。`tools/figma/README.md:47`

### 安装与静态插件包

- 安装 Figma 插件需要 Node.js 22.18 以上，推荐仓库当前使用的 Node.js 24，以及 Figma Design 桌面端。`tools/figma/README.md:16`
- 在 Figma 的 Plugins Development Import plugin from manifest 中选择本目录的 `manifest.json`，运行 `Operit · UI Design Bridge`，插件完全使用文件交接，不需要 Figma token、HTTP 服务器或额外上传服务。`tools/figma/README.md:24`
- `npm run package` 生成 `dist/operit-figma-designer.zip`，包含已编译的静态图层插件、范围说明以及用于验证插件的主题组件示例，它不包含可运行的整个应用。`tools/figma/README.md:35`

### 主题双向交接

- Theme Studio 点击导出 Figma 得到 `operit-theme.operit-design.json`。`tools/figma/README.md:42`
- 在 Figma 插件中点击导入设计文件后，文字、容器、气泡和输入框均为原生图层，主题组件生成 Component，颜色和显式标量参数生成 Variables。`tools/figma/README.md:43`
- `Light` 与 `Dark` 使用两个单模式集合，不依赖多模式付费功能。`tools/figma/README.md:44`
- 修改完整主题字段在插件的主题完整参数中编辑 JSON，然后点击更新主题参数，此处保留主题支持的全部字段，包括字体路径、气泡九宫格切片和样式枚举。`tools/figma/README.md:45`
- 选中导入的画板或其内部图层，点击导出修改与交接。`tools/figma/README.md:46`
- 回 Theme Studio 点击导入 / Figma 回传，选择导出的文件后，Studio 恢复主题、素材及包元数据，用真实 Flutter 组件预览，再按原有流程导出 `.toolpkg`。`tools/figma/README.md:47`
- 配色变量回传 `palette.light` 与 `palette.dark`，保留 alpha。`tools/figma/README.md:55`
- 圆角开关映射回现有 `roundedCorners` 布尔值，当前契约没有任意圆角数值。`tools/figma/README.md:58`
- 文字内容、自由布局、新增或删除组件、工具或插件视觉修改导出 `changes`、完整图层和 `source`，供开发实施。`tools/figma/README.md:61`
- 公共主题字段在多个画板中改成不同值时，插件报冲突，要求设计同学统一该字段，不会任意选择一张画板。`tools/figma/README.md:63`
- 自由布局和插件业务逻辑仍需要修改源代码，设计文件不会把这些修改伪装成已应用到运行中的程序。`tools/figma/README.md:63`

### 运行时采集

- 采集以 debug 模式启动应用并显式启用桥接，macOS 示例使用 `--dart-define=OPERIT_DESIGN_BRIDGE=true`。`tools/figma/README.md:72`
- Windows 上使用 `fvm flutter run -d windows`，移动设备使用对应设备 ID，手机的服务地址需要沿用 Flutter 建立的端口转发。`tools/figma/README.md:76`
- `capture.mjs` 接受 `--vm-service-file`、`--name` 和 `--out`，示例输出 `/tmp/plugin-settings.operit-design.json`。`tools/figma/README.md:81`
- `capture.mjs` 也支持直接传 `--vm-url` 地址并用 `--list` 列出已挂载的采集根，用 `--scope` 选择根。`tools/figma/README.md:95`
- 主应用、独立聊天窗口、桌面小组件及救援或启动错误窗口均已接入采集，独立窗口属于另一个 VM Service 时需使用对应进程地址。`tools/figma/README.md:95`
- 每次采集生成一份可编辑图层以及一张锁定的真实渲染参考图，不同页面、展开或折叠状态、滚动位置和插件路由分别采集、分别导入，采集不会触发业务操作或自动遍历未知插件。`tools/figma/README.md:97`
- 工具结果采集遍历实际渲染树，保留已展开的文本、容器和图片，附带 `kind: tool-result`、工具名称和展开状态。`tools/figma/README.md:101`
- Compose DSL 插件采集使用生产渲染器采集实际原生控件，附带包名、路由、节点类型、稳定的逻辑 `composeId` 与当前挂载路径。`tools/figma/README.md:102`
- WebView 插件通过已挂载 WebView controller 执行只读 DOM 采集，提取可见容器、文字、输入框、SVG 和可读图片，支持同源嵌套 iframe 和 shadow DOM，插件可加 `data-operit-design-id` 提供稳定的设计标识。`tools/figma/README.md:103`
- 自定义绘制中装饰与 CustomPaint 独立采集成图片并继续递归其内容子树，Canvas、视频、图标字体和部分平台视图保留为可替换图片。`tools/figma/README.md:104`
- 懒加载、未展开及视口外内容需要先显示再采集，跨域 iframe、受限图片、CSS 伪元素在导出文件和插件中显示明确说明，平台 WebView 不一定出现在 Flutter 的参考截图中，DOM 图层仍可单独编辑。`tools/figma/README.md:105`
- 桥接默认关闭，release 构建不会注册采集入口，采集保存用户当前实际可见的内容，密码输入导出遮罩文字。`tools/figma/README.md:107`

### 交互应用的目标与差距

- 交付目标是设计同学打开一个 Figma 文件，在里面使用整套软件，进入页面、返回、展开工具结果、打开弹窗、输入内容，以及进入插件自己的页面和子页面，到达任意界面后修改其中的控件、文字、布局和视觉样式，再继续交互并看到修改。`tools/figma/INTERACTIVE_APP.md:8`
- `src/plugin.ts` 导入 Figma 原生图层、导出修改及来源，没有运行 Operit 的路由、状态和事件。`tools/figma/INTERACTIVE_APP.md:16`
- `capture.mjs` 与 `software.mjs` 提供单场景或批量静态界面导出，场景之间没有真实行为，覆盖候选清单不代表全部界面可运行。`tools/figma/INTERACTIVE_APP.md:17`
- `src/theme_scene.ts` 提供主题组件示例，不代表软件完整 UI。`tools/figma/INTERACTIVE_APP.md:18`
- `apps/flutter/app/web/` 是 Flutter Web 启动入口及浏览器宿主，不能据此认定 Figma 已能运行、选中并编辑每个控件。`tools/figma/INTERACTIVE_APP.md:19`
- `OperitDesignRuntime` 已接入真实 Flutter 输入与受支持的渲染属性修改，WebView 表面可把请求交给实际插件 DOM，`live.mjs` 通过 VM Service 连接运行端，`src/live_client.ts` 和 `src/live_main.ts` 提供持续更新的 DOM 客户端及受支持属性编辑，`build-live.mjs` 生成候选 Code layer Web 项目。`tools/figma/INTERACTIVE_APP.md:25`
- 实时客户端仍依赖本机运行的原生应用，尚不能作为自包含的整个软件交付，真实 Figma 内的交互与原生编辑、全入口覆盖以及设计修改回到原始源文件仍待完成。`tools/figma/INTERACTIVE_APP.md:27`

### 已确认的 Web 运行基础与容器边界

- `apps/flutter/app/web/index.html` 先加载浏览器数据维护入口，再加载 `operit_runtime_bridge.js`，同时启动 Flutter。`tools/figma/INTERACTIVE_APP.md:33`
- `apps/flutter/app/lib/core/bridge/PlatformCoreProxyWeb.dart` 选择 `WebWasmCoreProxy`，`WebWasmCoreProxy.dart` 通过浏览器中的运行时 API 派发调用、控制消息和流式订阅。`tools/figma/INTERACTIVE_APP.md:35`
- `apps/flutter/app/web/runtime/src/operit_runtime_bridge.ts` 提供浏览器宿主、Worker、存储和其他能力。`tools/figma/INTERACTIVE_APP.md:37`
- Code layers 可以在 Design 画布中运行 Web 前端项目，支持播放交互、Point and edit、提取原生设计图层以及向代码层推送修改，该功能正在以 open beta 逐步开放，它支持 Web 应用，不能直接运行原生移动或桌面项目。`tools/figma/INTERACTIVE_APP.md:43`
- Code layer 是候选运行容器，而不是普通文件导入插件，这不证明当前 Operit Flutter Web 已兼容它。`tools/figma/INTERACTIVE_APP.md:45`
- 本仓库锁定的 Flutter 工具链在 `packages/flutter_tools/lib/src/web/compile.dart` 中使用 CanvasKit 与 skwasm Web 渲染模式，现有 Flutter 控件不是可直接修改 CSS 的 DOM 控件，将 Flutter Web 构建产物放进容器即使能够运行，也不能据此承诺设计同学能逐个选中、调整并回写所有控件，需要实际验证。`tools/figma/INTERACTIVE_APP.md:47`
- 还必须验证资产体积、WASM 和 Worker 加载、浏览器存储及子页面在容器中的能力，现有 Web 宿主的本地语音路径要求跨源隔离响应头，这属于相关能力的额外条件，不能把它误写成所有应用启动都必然失败的原因。`tools/figma/INTERACTIVE_APP.md:49`
- 如果现有 Flutter Web 无法提供所需的逐控件编辑能力，可行的候选方向是增加一套 DOM 设计前端，复用运行时协议、插件程序和资源，并显式适配原生 UI，它是一项界面运行层工程，不能通过增加采集次数完成。`tools/figma/INTERACTIVE_APP.md:60`

### 需要实现的应用层

- 主应用需要有实际路由和状态，覆盖聊天、包管理、市场、设置以及它们的面板、菜单、弹窗和独立界面入口，DOM 界面要实现对应的视图与事件适配，不能只列出路由名便算覆盖，也不能假定任意 Dart Widget 可以自动变成 HTML。`tools/figma/INTERACTIVE_APP.md:80`
- 工具结果应通过真正的结果类型选择相应渲染器，展开、折叠、分页、链接和后续操作仍有事件语义，流式内容和状态变化要持续驱动界面，导出当前展开状态的文字和边框不能替代这层行为。`tools/figma/INTERACTIVE_APP.md:84`
- Compose DSL 插件应实现同一 DSL 程序的 DOM 渲染宿主，接入原有节点事务、状态更新和事件派发，插件点击后继续运行相应程序并更新当前界面，包括动态增删节点、条件分支、弹窗和子路由，生产 Flutter 实现在 `apps/flutter/app/lib/ui/features/packages/screens/compose_dsl/renderer.dart`，其中包含保留节点、依赖订阅及事件目标解析，只翻译最初一帧 JSON 会丢失这些行为。`tools/figma/INTERACTIVE_APP.md:88`
- Web 插件应加载实际页面与资源，并适配它依赖的宿主 API、路由和消息事件，要单独验证嵌套 iframe 的运行与编辑边界，跨域页面能显示不等于其中控件可以被 Figma 编辑，不能用一张图片掩盖不支持的情况。`tools/figma/INTERACTIVE_APP.md:92`
- 设计修改应有稳定的来源标识，并明确区分修改落在 DOM 设计前端、插件源文件还是 Flutter 源文件，修改 DOM 并不会自动改写任意 Flutter Widget，要实现这一点还需要源代码映射与实施过程，并在真实应用中复核。`tools/figma/INTERACTIVE_APP.md:96`

### 完成标准

- 完成标准要求在真实 Figma 文件中打开应用，连续走通页面导航、输入、弹窗、返回和状态保留，导入文件成功不算通过。`tools/figma/INTERACTIVE_APP.md:102`
- 完成标准要求在一条连续流程里进入聊天，展开真实类型的工具结果，打开 Compose DSL 插件并改变其状态，再进入 Web 插件及其子页面。`tools/figma/INTERACTIVE_APP.md:103`
- 完成标准要求在主界面、工具和两类插件中分别选中控件修改布局或文字，继续交互，验证修改不会因重绘或页面返回而丢失。`tools/figma/INTERACTIVE_APP.md:104`
- 完成标准要求所有交付范围内的主入口、工具渲染类型和插件都具备对应的运行和编辑实现，有明确未支持项时，交付状态保持未完成。`tools/figma/INTERACTIVE_APP.md:105`
- 完成标准要求将一项普通布局修改和一项插件内部修改回到对应源文件，在实际应用中复核，不能用主题参数回传代替这项验收。`tools/figma/INTERACTIVE_APP.md:106`
- 当前这些完成标准尚未通过，下一步应先验证一个包含主页面、工具和两类插件的连续流程能否同时运行与编辑，再决定渲染层方案，这个验证只是架构验证，不等于最终整软件交付。`tools/figma/INTERACTIVE_APP.md:108`

### 实时运行客户端初版

- `LIVE.md` 的实时客户端是连接真实 Operit 的 Web 客户端初版，它持续接收当前界面，把点击、滚动、输入及受支持的设计修改交回真实 Flutter 或插件渲染器，它需要同一台电脑上的 debug Operit，当前还不能作为一份自包含的完整软件交给设计同学。`tools/figma/LIVE.md:3`
- 实时客户端启动先在 VS Code 中选择 `Operit2: Figma design`，或用 flutter run -d macos 并加 `--dart-define=OPERIT_DESIGN_BRIDGE=true` 与 `--vmservice-out-file`。`tools/figma/LIVE.md:12`
- 实时客户端启动随后执行 `npm --prefix tools/figma run build:live`，再执行 `node tools/figma/live.mjs --vm-service-file /tmp/operit-design-vm.txt`。`tools/figma/LIVE.md:19`
- 实时连接服务仅监听 `127.0.0.1`，请求使用 Authorization 头，地址中的口令保留在 URL 片段中，客户端连接成功后清除地址栏片段，请勿把完整连接地址提交到仓库、上传到 Figma 代码文件或公开分享。`tools/figma/LIVE.md:23`
- 进入实时客户端后可以直接操作软件，点击选中编辑选择控件，右侧仅显示真实运行端支持的属性，撤销该控件修改恢复业务最新值，保存设计修改导出带来源选择器的修改清单，尚不自动改写原始 Dart 或插件源文件。`tools/figma/LIVE.md:25`
- `build:live` 生成 `dist/live/index.html` 本机预览客户端、`dist/live-code-layer/` 不含账号业务数据和连接口令的独立 Web 前端项目，以及 `dist/operit-live-code-layer.zip` 候选导入包。`tools/figma/LIVE.md:31`
- 候选项目包含入口、启动和构建脚本，以及 Figma 要求的四个可执行生命周期脚本 `.figma/make/install`、`dev`、`deploy-preview`、`deploy`，ZIP 保留脚本的 Unix 执行权限，开发服务器读取 `PORT` 和 `FIGMA_DEV_SERVER_HOST` 环境变量，它不包含 Operit 原生程序。`tools/figma/LIVE.md:35`
- 导入真实 Figma Code layer 后，仍需在同一台电脑上运行 Operit，并在客户端粘贴本机连接地址。`tools/figma/LIVE.md:35`
- 远程预览来源需要明确允许，`--allow-origin` 只接受精确 Origin，不接受通配符，Figma 的 CSP、HTTPS 页面到本机 HTTP 的访问、浏览器本地网络权限和沙箱限制都需要在真实容器中验证，不能把浏览器 fixture 测试视为 Figma 验收。`tools/figma/LIVE.md:44`
- 2026-10-30 通过 Figma 官方远程 MCP 的 `send_code_to_figma`，实际创建了 Make 文件并导入生成的项目，服务返回 `status: imported`，在已登录的 Figma Make 编辑器中预览显示 `Running`，文件面板中可打开 `index.html`，编辑器显示可写输入区，当前账号未开通 Design Code Layer，因此本次使用独立 Make 文件。`tools/figma/LIVE.md:48`
- 上述导入结果只证明真实 Figma 中的源码导入和客户端启动，真实 Operit 连接、完整软件交互、Figma 原生可视化编辑与原始源码回写仍需分别验收，不能以导入回执替代。`tools/figma/LIVE.md:50`
- `test:live` 使用受控 VM 与 HTTP fixture，验证方法选择、事件传递、请求顺序和访问限制，`test:live:browser` 使用界面 fixture，验证真实浏览器内的点击、输入确认、焦点保留、编辑及撤销，两者都不证明全软件覆盖或真实 Figma 兼容。`tools/figma/LIVE.md:63`
- 尚未满足的交付条件包括真实 Figma 文件内的连续运行和原生 Point and edit 仍待验收。`tools/figma/LIVE.md:67`
- 实时客户端目前转发 tap、scroll、input，拖动、键盘快捷键、长按等交互还没有完整实现。`tools/figma/LIVE.md:68`
- 实时客户端只对运行端声明的属性提供编辑，自定义绘制内部、跨域 iframe 等不能逐控件编辑。`tools/figma/LIVE.md:69`
- 有稳定来源标识的控件可跨重建保留修改，没有标识的控件只在其存活期间保留。`tools/figma/LIVE.md:70`
- 设计修改自动回到原始业务源文件尚未实现，整软件交付标准仍以 `INTERACTIVE_APP.md` 为准。`tools/figma/LIVE.md:71`

## 关键符号

- `src/bridge.ts` — 文件契约、主题 schema 校验、来源与图层变更。`tools/figma/README.md:111`
- `src/plugin.ts` — Figma 原生节点、组件、变量、素材导入与修改回传。`tools/figma/README.md:112`
- `src/theme_scene.ts` — 主题组件起点。`tools/figma/README.md:113`
- `capture.mjs` — VM Service 只读采集命令。`tools/figma/README.md:114`
- `../theme/studio/src/figma_bridge.ts` — Studio 双向文件交接及原包保留。`tools/figma/README.md:115`
- `OperitDesignRuntime` — 已接入真实 Flutter 输入与受支持的渲染属性修改的实时运行时。`tools/figma/INTERACTIVE_APP.md:25`
- `live.mjs` — 通过 VM Service 连接运行端的实时连接服务。`tools/figma/INTERACTIVE_APP.md:25`
- `src/live_client.ts` — 与 `src/live_main.ts` 一起提供持续更新的 DOM 客户端及受支持属性编辑。`tools/figma/INTERACTIVE_APP.md:25`
- `build-live.mjs` — 生成候选 Code layer Web 项目。`tools/figma/INTERACTIVE_APP.md:25`
- `WebWasmCoreProxy` — `PlatformCoreProxyWeb.dart` 选择的 Web 核心代理，通过浏览器中的运行时 API 派发调用、控制消息和流式订阅。`tools/figma/INTERACTIVE_APP.md:35`
- `operit_runtime_bridge.js` — `web/index.html` 在启动 Flutter 的同时加载的浏览器运行时桥接脚本。`tools/figma/INTERACTIVE_APP.md:33`
- `composeId` — Compose DSL 采集附带的稳定逻辑标识。`tools/figma/README.md:102`
- `data-operit-design-id` — WebView 插件可加的稳定设计标识。`tools/figma/README.md:103`
- `kind: tool-result` — 工具结果采集附带的种类标识。`tools/figma/README.md:101`
- `roundedCorners` — 圆角开关映射回的现有布尔值，当前契约没有任意圆角数值。`tools/figma/README.md:58`
- `source.figmaAppearance` — 复杂填充、阴影和 Auto Layout 等设计参数的保留位置，供开发交接。`tools/figma/README.md:155`

## 调用链

1. 主题稿链路：Theme Studio 点击导出 Figma，得到 `operit-theme.operit-design.json`。`tools/figma/README.md:42`
2. 主题稿链路：在 Figma 插件中点击导入设计文件，文字、容器、气泡和输入框成为原生图层，主题组件生成 Component，颜色和显式标量参数生成 Variables。`tools/figma/README.md:43`
3. 主题稿链路：选中导入的画板或其内部图层，点击导出修改与交接。`tools/figma/README.md:46`
4. 主题稿链路：回 Theme Studio 点击导入 / Figma 回传，选择导出的文件，Studio 恢复主题、素材及包元数据，用真实 Flutter 组件预览，再按原有流程导出 `.toolpkg`。`tools/figma/README.md:47`
5. 运行时采集链路：以 debug 模式启动应用并显式启用桥接，macOS 示例使用 `--dart-define=OPERIT_DESIGN_BRIDGE=true`。`tools/figma/README.md:72`
6. 运行时采集链路：在应用中打开需要设计的页面，展开工具结果或进入插件子页面，再执行 `capture.mjs`，示例输出 `/tmp/plugin-settings.operit-design.json`。`tools/figma/README.md:81`
7. 运行时采集链路：把采集文件交给设计同学在同一个 Figma 插件中导入，每次采集生成一份可编辑图层以及一张锁定的真实渲染参考图。`tools/figma/README.md:97`
8. 实时链路：启动 debug 应用后执行 `npm --prefix tools/figma run build:live`，再执行 `node tools/figma/live.mjs --vm-service-file /tmp/operit-design-vm.txt`，打开命令输出的本机连接地址。`tools/figma/LIVE.md:19`
9. 实时链路：进入实时客户端后可以直接操作软件，点击选中编辑选择控件，右侧仅显示真实运行端支持的属性，保存设计修改导出带来源选择器的修改清单，尚不自动改写原始 Dart 或插件源文件。`tools/figma/LIVE.md:25`
10. 验证链路：`tools/figma` 的验证命令是 `npm run typecheck`、`npm test` 和 `npm run build`。`tools/figma/README.md:122`
11. 验证链路：最后一项 Flutter 测试使用真实工具结果组件和真实 Compose DSL 渲染器，验证深层文字导出及所属包与工具标识，并生成 `.dart_tool/figma-deep-capture.operit-design.json` 供检查。`tools/figma/README.md:144`
12. 验证链路：`npm run test:runtime` 将真实 Flutter 采集文件送入插件导入器，在原生文字图层上修改文字和位置，再验证导出的变更及所属插件信息。`tools/figma/README.md:152`
13. 验证链路：`npm run test:package` 解压实际 ZIP，检查 manifest 引用，执行编译后的插件，在 API 模拟宿主里验证示例组件可编辑、主题颜色可回传和文字差异可导出，仍不替代实际 Figma 的视觉验收。`tools/figma/README.md:164`

## 来源

- `tools/figma/README.md`：静态工具说明、两个入口、主题双向交接、运行时采集、代码入口与验证。`tools/figma/README.md:1`
- `tools/figma/INTERACTIVE_APP.md`：交互应用的交付目标、现有能力差距、Web 运行基础、Code layer 容器边界、需要实现的应用层与完成标准。`tools/figma/INTERACTIVE_APP.md:3`
- `tools/figma/LIVE.md`：实时运行与编辑连接的启动方法、候选 Code layer 项目、已验证的 Figma 导入阶段与尚未满足的交付条件。`tools/figma/LIVE.md:3`
- 本页未对 seed 之外的文件做全仓 grep 零命中核查，本页的否定性断言依据是三份 seed 文档的原文表述。`tools/figma/README.md:5`
