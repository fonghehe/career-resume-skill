# 资料与事实状态

完整事实保存在 `local/references/` 的 Markdown 中，展示摘要保存在 `local/data/timeline.json`。本文 JSON 里的路径相对个人资料目录 `local/`，例如 `references/sources/S1.md`，不加 local 前缀。二者冲突时，以最新本人确认及相应来源为准，再更新展示数据。

## 事实状态不等于熟练程度

| 状态 | 含义 | 使用方式 |
|---|---|---|
| `confirmed` | 本人明确陈述或确认，有原话 / 日期记录 | 仍需说明个人责任、时间与来源 |
| `resume-supported` | 原简历有明确记载，尚未重新确认 | 保留原表述，不扩充具体实现与成果 |
| `pending` | 信息缺失或待本人确认 | 不能作为已确认贡献 |
| `proposed-to-verify` | 整理者提出的合理假设或可探索问题 | 标【推测，待确认】，只用于后续追问 |
| `fabricated-excluded` | 已确认不是本人经历或虚构内容 | 不进入真实项目库和派生内容 |
| `synthetic-draft` | 隔离的演练草稿 | 只用于教学或练习，不当作职业事实 |
| `legacy-only` | 只有旧记录，尚未纳入当前事实 | 不进入当前简历正文 |
| `superseded` | 已被新确认更正或撤回 | 保留历史来源，不采用旧结论 |
| `git` | 本人匹配的代码活动证据 | 不能单独证明职称、上线或个人成果 |

具体“做过 / 参与过 / 接触过 / 学习过”另行记录。`confirmed` 可以确认“只学习过某技术”，不能因此变成“具备生产经验”。

## 项目卡与证据

项目卡放在 `references/projects/`，标题为 `# P01｜项目名称` 或开源类 `# O01｜项目名称`。编号稳定且唯一，贡献条目如 `P01-A` 与所属项目一致。索引链接每张活动卡片。

每个重要事实尽量关联来源 ID、代码 / PR / 文档等证据及本人确认日期。暂无外部证据就明确记录，不能编造仓库链接、上线截图或绩效材料。

技术案例、能力地图、业务领域、领导协作、架构、AI、移动端、开源、工程效率与职业成长均以这些事实为依据。尚未验证的领域保留为空或待补充，不能因模板里有栏目就填经历。

## 来源 manifest

空资料库使用 `{"sources": []}`。已导入文本记录示例：

```json
{
  "sources": [{
    "id": "S1",
    "filename": "my-resume.txt",
    "extracted_text": "references/sources/S1.md",
    "imported_on": "2026-10-01"
  }]
}
```

`id` 唯一，`extracted_text` 是相对 skill 根目录的已有文本快照。PDF 来源可附 `sha256`（原文件 SHA-256）和 `pages`（正整数）；有页码时，快照以 `## Page 1` 等按顺序分节。脚本只检查哈希格式与页码，不拥有原 PDF 时不会证明哈希与原文件一致。

## 时间线

顶层字段：`meta`、`profile`、`leadership`、`career`、`projects`、`repositories`。空模板见 `assets/starter/data/timeline.json`。

- `meta`：`title`、`subtitle`、`updatedAt`、`dateConvention`、`repositoryNote`。
- `profile`：`name`、`englishName`、`careerStart`、`careerEnd`、`headline`。
- `leadership`：数组 `phases`（period/value/label）、`metrics`（value/label）、`responsibilities`、`copilot`，字符串 `boundary`；没有管理经历可保持空数组。
- `career`：`id`、`organization`、`role`、`start`、`end`、`summary`；可附 `level`、`groupOrganization`，将已确认属于同一公司体系的内部阶段合并为一段工作经历。
- `projects`：`id`、`name`、`nature`、`organization`、`category`、`status`、`start`、`end`、`ongoing`、`tech`、`highlights`；可附 `url`、`projectBackend`、`backendParticipation`、`collaboration`。
- `repositories`：`name`、`group`、`projectId`、`start`、`end`、`count`、`tech`、`note`。次数代表署名活动记录，不代表独立成果。

Git 采集报告独立保存在私人 `local/output/git-activity/`：`records` 保留 SHA、Author Date、Committer Date、作者邮箱和主题；`repository` 是区间摘要，无匹配则为 null，`timelineEvents` 是可整理为网页 Git 足迹的逐提交事件。`mappingStatus` 默认 pending，不自动成为个人项目事实。`--folder` 的 schemaVersion 2 报告在 `reports` 下保存各仓库及 `relativePath`，另列 `skipped`。同名仓库用相对目录区分。

## 职级、项目阶段与提交明细（可选）

字段由智能体维护，使用者通过补充事实更新即可；旧资料不必补齐。

- career.level：有来源的正式职级字符串，未知留空；role 仍保存正式职称。groupOrganization 合并同公司阶段，不机械推断晋升。
- projects.milestones：阶段列表，每项 title 必填字符串，date 与 summary 可选。日期可以保留月份精度或为空，只作阶段标签，不替代横轴起止日期。
- gitEvents：id、repository、完整 sha、subject、含时区 authorDate 与 committerDate，以及可选 projectId。repository 必须关联摘要，projectId 为已有项目或空；作者时间在摘要区间，同仓库同 SHA 不重复。
- meta.synthetic：虚构演示设 true，页面显示明确提示。

项目本人 Commit 总数优先使用仓库 `projectCounts` 中该项目的计数；单项目旧数据兼容使用仓库 count。关联仓库数按仓库条目统计，不把未映射的仓库强行分配给项目。完整库的总数不因只展开部分明细而减少；按公司或年份筛选时，明细不完整的统计标记为“已载入”。

旧资料中的其他附加字段保留在文件中，生活片段不作为项目履历页的展示内容；待确认问题保存在 references/questions-to-confirm.md。

仓库活动总数可以大于网页挑选的事件数；列表先显示最近三十条，可继续展开。每条 Git 事件保留原始主题、SHA 和两种时间，不只展示总结标题。项目详情可直接查看与它关联的提交。

日期使用 ISO 格式；项目日期可以都为空，但不能只给一端。进行中项目仍填写资料整理截止日期，并标 `ongoing: true`。未知日期不从任职或 Git 记录推算。时间线项目 ID 必须能找到对应 Markdown 卡片；不要求包含所有档案项目。URL 仅接受 `http://` 或 `https://`，不使用 `javascript:` / `data:`。

构建会内嵌数据和 Markdown 原文。修改资料后重新构建；结构校验会检查已有网页是否过期。

## 可选增强字段（旧库无需迁移）

- 任职 / 项目：`confirmedFields: ["summary", "milestones"]`；`sources: [{"field":"summary","label":"本人补充","status":"confirmed","excerpt":"负责前端","path":"references/sources/note.md"}]`，path 可省略。
- 项目：`careerIds` 关联任职阶段；`attachments: [{"label":"项目截图","path":"references/attachments/ui.png"}]`；milestones 的 `status: pending` 表示待确认。
- 仓库 / Git event：`projectIds` 支持多个归属，兼容原 `projectId`。仓库 `projectCounts` 是按项目去重的提交次数，同一提交可以涉及多个项目，因此不能相加冒充仓库总数。
- Git event：`files` 记录实际变更文件。仓库 `activity` 包含 `monthly`、`modules`、`types`、`activeMonths`；模块计数是涉及该模块的 Commit 数，可重叠。月份沿用 Author Date 原时区，所有月份计数之和等于仓库总数。

增量更新与分享的工具用法见[命令参考](commands.md)，详细规则保存在 `references/enhancements.md`。
