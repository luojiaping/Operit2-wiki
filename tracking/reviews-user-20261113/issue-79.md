# Issue 79 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:31:02Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/79#issuecomment-6854390462


本轮重新核对正文与56条facts，需修改一处直接矛盾的版本表述：第114行“插件侧是v1/v2”和第206行“withSchema（v1/v2）”暗示v2已存在，同页第108行却明确没有v2。声明基线364d1d594及最新09249fb9的docs/plugin-storage.md:55只确认首个插件schema为v1、不存在v2格式与v1到v2迁移。请统一改为“插件schema（当前v1）与用户偏好文件format 0–5是两套体系”。withMigration(5)、3分支旧主题迁移、4分支聊天样式拆分及Space偏好owner校验已另核，未见问题。Wiki固定f9c90d7；未执行构建、测试或同步。

源码定位：
- [docs/plugin-storage.md:55](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/docs/plugin-storage.md#L55)
