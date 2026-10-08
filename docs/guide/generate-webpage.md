# 一步一步生成自己的履历网页

完整文字履历是第一阶段的基础交付，网页按需追加；文字履历生成见[简单开始](first-library.md)。想手动操作时，个人网页读取 `local/data/timeline.json` 和 `local/references/projects/*.md`，生成单个 `local/showcase/project-timeline.html`。它展示公司任职、职级变化、项目阶段、仓库统计及可展开的本人 Commit 明细；Git 事件可按项目和仓库筛选，在项目详情中也能查看。

## 1. 先准备事实

完成简历导入，至少确认一段任职或一个项目。来源、贡献与待确认信息保存在 Markdown 中，JSON 只保存用于展示的数据。没有管理经历时 `leadership` 保持空数组，不为了页面填上管理人数。

对智能体发送：

```text
请根据当前事实库准备 local/data/timeline.json，用于生成个人履历网页。
不要修改原始事实，也不要读取虚构示例给我填空。
项目 ID 必须对应已有项目卡；技术标签区分个人使用和项目后端环境。
日期只有月份时先问我展示约定；未知项目起止同时留空。
没有已确认 Git 活动时 repositories 保持空数组。
请先检查日期、归属、个人贡献和待确认状态，再生成网页。
```

## 2. 理解最小数据

下面是可用于理解格式的虚构数据。**不要把它当作自己的经历。** 完整虚构样例可通过快速开始的 `create_demo.py` 运行。

```json
{
  "meta": {
    "title": "我的职业时间线",
    "subtitle": "持续维护的职业事实与项目记录",
    "updatedAt": "2025-07-01",
    "dateConvention": "下列日期仅为虚构教学示例。",
    "repositoryNote": "暂未导入仓库活动。"
  },
  "profile": {
    "name": "示例使用者（虚构）",
    "englishName": "",
    "careerStart": "2024-01-01",
    "careerEnd": "2024-12-31",
    "headline": "前端开发"
  },
  "leadership": {
    "phases": [], "metrics": [], "responsibilities": [],
    "boundary": "暂无已确认管理经历。", "copilot": []
  },
  "career": [
    {
      "id": "E01", "organization": "示例公司（虚构）",
      "role": "前端开发", "start": "2024-01-01", "end": "2024-12-31",
      "summary": "参与内部业务页面。"
    }
  ],
  "projects": [
    {
      "id": "P01", "name": "示例项目（虚构）", "nature": "company",
      "organization": "示例公司（虚构）", "category": "业务前端",
      "status": "resume-supported", "start": "", "end": "",
      "tech": ["TypeScript"], "highlights": ["具体实现和结果待补充"]
    }
  ],
  "repositories": []
}
```

`projects` 中有 `P01` 时，必须有以 `# P01｜` 开头的项目卡。不能只复制 JSON 后忽略卡片；示例中项目日期为空，因此只出现项目卡，不画项目区间。

## 3. 项目卡与索引配套

你的项目卡可以放在 `local/references/projects/my-project.md`，第一行写 `# P01｜你的项目名称`。文件名不必等于 ID，但同一 ID 只能有一张卡。

在 `local/references/project-index.md` 加入指向 `projects/my-project.md` 的链接，并保留事实状态。卡片使用项目模板，包含背景、角色、实现、问题、结果、个人贡献和证据。

初次构建前检查：

```sh
python3 scripts/validate.py
```

如果已有 HTML 而此次更新了数据，校验可能报告网页过期。完成源数据修正后重新构建，再校验即可；不要把旧网页内容复制回事实库。

## 4. 构建与查看

```sh
python3 scripts/build_timeline.py
python3 scripts/validate.py
```

打开 `local/showcase/project-timeline.html`。macOS 可以执行：

```sh
open local/showcase/project-timeline.html
```

其他系统用文件管理器或浏览器打开。默认构建会更新这个生成文件，原始 JSON 与项目卡不会被改写。无需启动 Python 服务或安装 VitePress。

## 5. 做一次人工检查

- 任职时间与本人记录一致，展示日期约定已写明。
- 每个项目属于正确公司或个人项目类别。
- 搜索能找到项目；点击后看到对应卡片及待确认信息。
- 项目采用的后端技术没有变成未经确认的个人后端贡献。
- 没有为填满页面而添加用户量、性能比例、管理人数或仓库次数。

结构校验只能证明格式和文件关系符合约定，不能证明这些经历真实。

## 6. 以后怎样更新

```text
我补充了 P01 的一个真实技术问题，请保存新的确认与证据。
先更新项目卡和事实库，再同步必要的展示摘要到 local/data/timeline.json。
重新构建时间线并校验，列出本轮改动和剩余待确认信息。
```

网页内嵌 JSON 和完整项目卡原文。即使页面摘要没有展示某些文字，它们仍在 HTML 中。默认生成网页供自己使用；要公开个人网页时，另行选择可公开事实、审查内容并生成公开副本，不直接部署私人 HTML。

下一步：[补充 Git 活动](git-timeline.md)；更多字段见[数据模型](../reference/data-model.md)。
