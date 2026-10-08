---
layout: home
hero:
  name: career-resume-skill
  text: 先生成履历，再生成简历
  tagline: 把散落在旧简历、项目文档和记忆里的工作经历整理清楚，持续补充，需要时再生成简历。
  actions:
    - theme: brand
      text: 快速开始
      link: /guide/quick-start
    - theme: alt
      text: 根据履历生成简历
      link: /guide/generate-resume
features:
  - title: 从经历得到完整履历
    details: 口述、旧简历或项目材料都能开始，整理任职、教育、职责与成果，未知可留空。
  - title: 回顾这些年的项目
    details: 从一个记得清楚的项目开始，看各阶段做过什么、职责如何变化，每项经验都有记录可回查。
  - title: 同一履历，多个简历版本
    details: 按通用方向或岗位 JD 选择事实，正文与依据报告分别交付，完整履历继续保留。
  - title: 本人的 Git 记录
    details: 读取本地项目目录，匹配本人邮箱，按仓库和 SHA 去重统计。
  - title: 每条内容有依据
    details: 保留来源、确认状态和本人贡献边界，简历报告说明选材、删减及能力缺口。
  - title: 本地资料与离线页面
    details: 不需要后端，个人资料留在自己的目录，公开示例独立使用虚构数据。
---

## 先整理，再选材

提供经历或材料，让智能体交付完整文字履历与可维护记录。随后补充事实，或根据最新履历生成通用 / 岗位简历；网页和 Git 统计按需添加。

写了多年代码，旧简历可能只留下项目名和技术栈。把当时的问题、约束、本人工作与方案选择重新记下来，可以慢慢看清不同项目之间的联系。暂时没有求职打算，也可以先做一次[项目与职业回顾](guide/review-career.md)。

[快速开始](guide/quick-start.md) · [能力与交付](reference/capabilities.md) · [目录说明](reference/directories.md) · [根据履历生成简历](guide/generate-resume.md) · [完整示例](example.md) · [工具参考](reference/commands.md)

## 三步使用

1. 打开自己的完整工作副本，让智能体读取 `SKILL.md`；个人资料集中在 `local/`。
2. 提供口述经历、旧简历或项目材料，先查看生成的完整文字履历；后续补充事实继续用同一份档案。
3. 先回顾各阶段的工作；需要求职时给出方向或岗位 JD，生成简历正文与独立依据报告。

日常不需要编辑 JSON 或启动教程站。网页、Git 与文档格式按实际需求添加。
