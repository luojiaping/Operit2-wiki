---
title: Skills 机制
module: plugins
platforms: [all]
sources: [core/crates/tool/services/src/tools/skill/SkillManager.rs, core/crates/tool/services/src/tools/skill/SkillPackage.rs, core/crates/tool/services/src/tools/skill/mod.rs, core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs, core/crates/tool/services/src/tools/skill_runtime/mod.rs, core/crates/persistence/store/src/ExtensionStore.rs]
date: 2026-11-11
---

## 概述

Skill 是以目录为单位的扩展包，一个 Skill 目录以 `SKILL.md` 为入口文件（`core/crates/tool/services/src/tools/skill/SkillManager.rs:127`）。
Skill 的载体是 SKILL.md 目录，`SkillPackage` 只记录名、描述、目录与 SKILL.md 路径四个字段（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:6`）。
Skill 是独立的扩展类型，不是 ToolPkg 插件的同义词（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:6`）。
本页同时覆盖 Agent 回路的 Skills 主题，不再单立 agent-skills 页。
`SkillManager` 持有 `RuntimeStorePaths` 与 `VisualFileSystem`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:18`）。
`SkillRepository` 是管理已安装与导入 Skill 的门面（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:14`）。

## AI 速览

- 核心符号：`SkillPackage` — 一个已安装 Skill 的记录，含名、描述、目录与 SKILL.md 路径（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:6`）。
- 核心符号：`SkillManager` — 扫描、安装、删除 Skill 并生成激活提示的管理器（`core/crates/tool/services/src/tools/skill/SkillManager.rs:18`）。
- 核心符号：`SkillRepository` — 对外暴露 Skill 管理操作的仓库门面（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:14`）。
- 核心符号：`refreshAvailableSkills` — 按 space 先行、属主记录定胜负的顺序扫描 device 与 space 两个位置并返回有效 Skill 与错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:53`）。
- 核心符号：`getSkillSystemPrompt` — 生成 Skill 激活时用的系统提示片段（`core/crates/tool/services/src/tools/skill/SkillManager.rs:434`）。
- 核心符号：`importBundledExternalSkill` — 安装或原地更新一个随包外部 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:288`）。
- 核心符号：`importSkillFromGitHubRepo` — 从 GitHub 仓库下载 zip 导入 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:174`）。
- 核心符号：`importSkillFromDirectInput` — 用文本内容直接创建一个 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:214`）。
- 核心符号：`getAiVisibleSkillPackages` — 只返回对 AI 包激活可见的 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:101`）。
- 主入口函数：`SkillRepository` 的 `getInstance`（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:31`）。
- 数据流向一句话：Skill 目录经扫描成为 SkillPackage，激活时 `SKILL.md` 全文拼进系统提示片段交给 Agent 运行时（`core/crates/tool/services/src/tools/skill/SkillManager.rs:462`）。

## 核心机制

### Skill 的形态与元数据

Skill 目录的入口文件也可以是小写 `skill.md`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:130`）。
`SkillPackage` 的 `name` 字段保存 Skill 名（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:7`）。
`SkillPackage` 的 `description` 字段保存 Skill 描述（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:8`）。
SkillPackage 的 `directory` 字段保存 Skill 所在的目录路径（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:13`）。
SkillPackage 的 `skillFile` 字段保存 SKILL.md 文件路径（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:18`）。
内容首行是 `---` 时按行调用 `parseMetadataLine` 解析 frontmatter（`core/crates/tool/services/src/tools/skill/SkillManager.rs:713`）。
frontmatter 缺 `name` 或 `description` 时回退扫描前 40 行（`core/crates/tool/services/src/tools/skill/SkillManager.rs:719`）。
`parseMetadataLine` 解析一行元数据并写入 `name` 或 `description`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:728`）。

### 扫描与安装位置

SkillManager 的 `getSkillsDirectoryPath` 返回用户已安装 Skill 的存放目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:45`）。
SkillManager 的 `getSkillsRootDir` 返回 RuntimeStorePaths 的 `skills_dir`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:683`）。
SkillManager 的 `refreshAvailableSkills` 扫描 device 与 space 两个位置（`core/crates/tool/services/src/tools/skill/SkillManager.rs:53`）。
各 scope 的扫描按 `sourceFilter` 过滤，未登记或被遮蔽的来源被跳过（`core/crates/tool/services/src/tools/skill/SkillManager.rs:69`）。
扫描只处理 `isDirectory` 为真的子项（`core/crates/tool/services/src/tools/skill/SkillManager.rs:75`）。
缺少 `SKILL.md` 的目录记入 `Missing SKILL.md` 加载错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:134`）。
`SKILL.md` 元数据的 `name` 为空时 Skill 名回退为目录名（`core/crates/tool/services/src/tools/skill/SkillManager.rs:137`）。
扫描中出现与已加载 Skill 同名的 Skill 时记入 `Duplicate scanned skill name` 加载错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:99`）。
同名 Skill 同时存在于 space 与 device 时，属主记录所在的 scope 胜出，另一 scope 的同名 Skill 被静默跳过（`core/crates/tool/services/src/tools/skill/SkillManager.rs:83`）。
扫描到无属主记录的 Skill 时调用 `registerDevice` 登记为 device 属主（`core/crates/tool/services/src/tools/skill/SkillManager.rs:90`）。
扫描时按属主记录校验位置与来源名，来源名不符时报错 `Skill content does not match its registered location`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:87`）。
SkillManager 的 `getAvailableSkills` 返回当前已安装的全部有效 Skill 包（`core/crates/tool/services/src/tools/skill/SkillManager.rs:174`）。
SkillManager 的 `getAvailableSkillsSnapshot` 同时返回有效 Skill 包与加载错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:180`）。
SkillManager 的 `getSkillLoadErrors` 返回扫描 Skill 目录的加载错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:188`）。
`readSkillDirectory` 读取单个 Skill 目录，`SKILL.md` 优先、skill.md 兜底，不注册也不执行其内容（`core/crates/tool/services/src/tools/skill/SkillManager.rs:126`）。

### 打包、安装与按需导入

SkillManager 的 `getBundledExternalSkillCandidates` 列出尚未安装的随包外部 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:212`）。
getBundledExternalSkillCandidates 不再列出内置 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:229`）。
随包 Skill 候选的描述取自其 `SKILL.md` 的元数据（`core/crates/tool/services/src/tools/skill/SkillManager.rs:242`）。
importBundledExternalSkill 在同名 Skill 已安装时原地更新，保留其位置与设置（`core/crates/tool/services/src/tools/skill/SkillManager.rs:311`）。
importBundledExternalSkill 先把随包资产写入暂存的 prepared 目录，再把旧版移入 previous、把新版移入原位（`core/crates/tool/services/src/tools/skill/SkillManager.rs:321`）。
importBundledExternalSkill 用 `writeFileBytes` 把随包资产写入暂存的 prepared 目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:328`）。
`normalizeAssetRelativePath` 拒绝含非普通路径段的随包资产路径（`core/crates/tool/services/src/tools/skill/SkillManager.rs:757`）。
importBundledExternalSkill 校验随包 SKILL.md 的 name 与请求的 Skill 名一致，不一致则报错 `Bundled skill identity mismatch`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:335`）。
`ensureBuiltinSkills` 安装缺失的内置 Skill，安装后对 AI 隐藏，保留已有安装与开关（`core/crates/tool/services/src/tools/skill/SkillManager.rs:194`）。
`bundledSkillNeedsUpdate` 逐文件比对随包资产与已安装 Skill，无随包更新源时返回 None（`core/crates/tool/services/src/tools/skill/SkillManager.rs:262`）。
`importSkillArchiveBytes` 把 zip 字节解到临时目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:482`）。
临时目录名以 `.import_tmp_` 开头（`core/crates/persistence/store/src/ExtensionStore.rs:35`）。
`importSkillArchiveBytes` 在导入完成后删除临时目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:514`）。
importSkillArchiveBytesInner 调用 `unzipBytesToDirectory` 解压 zip（`core/crates/tool/services/src/tools/skill/SkillManager.rs:527`）。
zip 解压用 `enclosed_name` 校验条目，指向目标目录外的条目被拒绝（`core/crates/tool/services/src/tools/skill/SkillManager.rs:824`）。
zip 只有唯一子目录时 `singleChildDirectory` 返回该子目录作为解压根目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:849`）。
导入时调用 `findSkillFiles` 在包内递归查找全部 SKILL.md，不限数量（`core/crates/tool/services/src/tools/skill/SkillManager.rs:553`）。
zip 导入会导入包内找到的全部 Skill，单个失败不阻塞其他，汇总返回 Imported N skills; failed: M（`core/crates/tool/services/src/tools/skill/SkillManager.rs:591`）。
zip 内找不到 `SKILL.md` 时导入返回 `No SKILL.md found in the imported zip`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:558`）。
importSkillDirectory 调用 `parseSkillMetadata` 解析导入 Skill 的元数据（`core/crates/tool/services/src/tools/skill/SkillManager.rs:612`）。
导入的 Skill 名优先取 SKILL.md 元数据的 name（`core/crates/tool/services/src/tools/skill/SkillManager.rs:615`）。
元数据无 name 且解压根目录就是临时目录时导入的 Skill 名取 zip 文件名主干（`core/crates/tool/services/src/tools/skill/SkillManager.rs:617`）。
同名 Skill 已安装时 zip 导入返回 `Skill already exists in an installation location`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:641`）。
zip 导入对非 `.zip` 文件返回 `Only .zip files are supported`（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:167`）。
`importSkillFromGitHubRepo` 从 GitHub 仓库下载 zip 导入 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:174`）。
GitHub 导入未指定分支时调用 `getGithubDefaultBranch` 查询默认分支（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:181`）。
importSkillFromGitHubRepo 从 `codeload.github.com` 下载仓库 zip（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:193`）。
`parseGitHubSkillTarget` 解析 GitHub Skill 目标地址（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:403`）。
parseGitHubSkillTarget 接受 `raw.githubusercontent.com` 地址（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:462`）。
importSkillFromDirectInput 要求 Skill id 非空（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:228`）。
`isValidSkillId` 只接受字母、数字、点、下划线与连字符组成的 Skill id（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:351`）。
importSkillFromDirectInput 通过 `buildDirectSkillMarkdown` 生成带 name 与 description frontmatter 的 SKILL.md（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:297`）。
importSkillFromDirectInput 把附件复制到 Skill 目录下的 `assets` 子目录（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:303`）。
importSkillFromDirectInput 写入失败时删除已创建的 Skill 目录（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:274`）。
SkillManager 的 `deleteSkill` 调用 `ExtensionStore` 的 `delete` 注销 Skill 并返回布尔结果（`core/crates/tool/services/src/tools/skill/SkillManager.rs:475`）。

### PackageBuilder 随包 Skill

`PackageBuilder` 是随包 Skill 的名称（`core/crates/tool/services/src/tools/skill/SkillManager.rs:14`）。
`ensureQuickPluginCreatorBundledSkill` 在 `QUICK_PLUGIN_CREATOR_SKILL_NAME` 已安装时直接返回已安装的 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:409`）。
该 Skill 未安装时调用 `importBundledExternalSkill` 导入（`core/crates/tool/services/src/tools/skill/SkillManager.rs:417`）。
`ensureQuickPluginCreatorSkillVisible` 在安装快速插件创建 Skill 后调用 `setSkillVisibleToAi` 将其设为可见（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:135`）。

### 与 Agent 运行时的交互

SkillManager 的 `readSkillContent` 读取一个已安装 Skill 的 SKILL.md 内容（`core/crates/tool/services/src/tools/skill/SkillManager.rs:424`）。
SkillManager 的 `getSkillSystemPrompt` 生成 Skill 激活时用的系统提示片段（`core/crates/tool/services/src/tools/skill/SkillManager.rs:434`）。
提示以 `Using package (Skill):` 加 Skill 名开头（`core/crates/tool/services/src/tools/skill/SkillManager.rs:442`）。
执行策略要求优先使用 Skill 提供的指令与随包脚本并用终端相关工具完成任务（`core/crates/tool/services/src/tools/skill/SkillManager.rs:445`）。
getSkillSystemPrompt 的提示包含 `SKILL.md` 路径（`core/crates/tool/services/src/tools/skill/SkillManager.rs:450`）。
提示包含 Skill 目录结构文本（`core/crates/tool/services/src/tools/skill/SkillManager.rs:457`）。
getSkillSystemPrompt 的提示末尾附上 `SKILL.md` 全文（`core/crates/tool/services/src/tools/skill/SkillManager.rs:462`）。
SkillRepository 的 `getAiVisibleSkillPackages` 只返回对 AI 包激活可见的 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:101`）。
SkillRepository 的 `isSkillVisibleToAi` 查询一个 Skill 是否对 AI 包激活可见（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:123`）。
SkillRepository 的 `setSkillVisibleToAi` 设置一个 Skill 对 AI 包激活的可见性（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:129`）。
`SkillRepository` 的 `getInstance` 要求 `HostManager` 提供 VFS（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:32`）。

## 关键符号

- `SkillPackage` — 一个已安装 Skill 的记录（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:6`）。
- `SkillManager` — 扫描、安装、删除 Skill 并生成激活提示的管理器（`core/crates/tool/services/src/tools/skill/SkillManager.rs:17`）。
- `SkillRepository` — 对外暴露 Skill 管理操作的仓库门面（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:13`）。
- `SkillManager` 的 `fromDefaultPaths` — 用默认运行时存储路径创建管理器（`core/crates/tool/services/src/tools/skill/SkillManager.rs:31`）。
- SkillManager 的 `refreshAvailableSkills` — 按 space 先行、属主记录定胜负的顺序扫描 device 与 space 两个位置并返回有效 Skill 与错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:53`）。
- `readSkillDirectory` — 读取单个 Skill 目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:126`）。
- `ensureBuiltinSkills` — 安装缺失的内置 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:194`）。
- `bundledSkillNeedsUpdate` — 比对随包资产与已安装 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:262`）。
- `readSkillDisplayName` — 读 SKILL.md 的 display_name（`core/crates/tool/services/src/tools/skill/SkillManager.rs:156`）。
- SkillManager 的 `getAvailableSkills` — 返回当前已安装的全部有效 Skill 包（`core/crates/tool/services/src/tools/skill/SkillManager.rs:174`）。
- SkillManager 的 `getSkillSystemPrompt` — 生成 Skill 激活时用的系统提示片段（`core/crates/tool/services/src/tools/skill/SkillManager.rs:434`）。
- SkillManager 的 `importBundledExternalSkill` — 安装或原地更新一个随包外部 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:288`）。
- SkillManager 的 `importSkillArchiveBytes` — 从 zip 字节导入包内全部 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:482`）。
- SkillManager 的 `ensureQuickPluginCreatorBundledSkill` — 安装随包的 PackageBuilder Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:409`）。
- SkillRepository 的 `getAiVisibleSkillPackages` — 只返回对 AI 包激活可见的 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:101`）。
- SkillRepository 的 `importSkillFromGitHubRepo` — 从 GitHub 仓库下载 zip 导入 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:174`）。
- SkillRepository 的 `importSkillFromDirectInput` — 用文本内容直接创建一个 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:214`）。
- `QUICK_PLUGIN_CREATOR_SKILL_NAME` — 值为 `PackageBuilder` 的随包 Skill 名常量（`core/crates/tool/services/src/tools/skill/SkillManager.rs:14`）。

## 调用链

1. `SkillRepository` 的 `getInstance` 用 `HostManager` 的 VFS 创建 `SkillManager`（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:32`）。
2. SkillManager 的 `refreshAvailableSkills` 扫描 device 与 space 两个位置（`core/crates/tool/services/src/tools/skill/SkillManager.rs:53`）。
3. `readSkillDirectory` 在每个 Skill 目录里找 `SKILL.md` 并解析元数据（`core/crates/tool/services/src/tools/skill/SkillManager.rs:126`）。
4. 解析出的 `name` 与 `description` 连同目录与 SKILL.md 路径装进 `SkillPackage`（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:6`）。
5. 随包安装时 `importBundledExternalSkill` 把资产写入暂存目录，确认身份后把新版移入原位（`core/crates/tool/services/src/tools/skill/SkillManager.rs:288`）。
6. zip 导入时调用 `findSkillFiles` 在包内递归查找全部 SKILL.md，不限数量，逐个导入并汇总成功与失败数（`core/crates/tool/services/src/tools/skill/SkillManager.rs:553`）。
7. GitHub 导入时 importSkillFromGitHubRepo 从 `codeload.github.com` 下载仓库 zip 再走 zip 导入（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:193`）。
8. 激活时 getSkillSystemPrompt 把 `SKILL.md` 全文、目录结构与执行策略拼进系统提示片段（`core/crates/tool/services/src/tools/skill/SkillManager.rs:462`）。
9. `getAiVisibleSkillPackages` 按 `isSkillVisibleToAi` 过滤出对 AI 包激活可见的 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:101`）。

## 来源

- core/crates/tool/services/src/tools/skill/SkillManager.rs
- core/crates/tool/services/src/tools/skill/SkillPackage.rs
- core/crates/tool/services/src/tools/skill/mod.rs
- core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs
- core/crates/tool/services/src/tools/skill_runtime/mod.rs
- core/crates/persistence/store/src/ExtensionStore.rs
