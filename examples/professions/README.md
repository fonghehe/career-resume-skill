# 五个职业的履历、简历与个人网页示例

> 虚构教学示例：全部人物、单位、经历、案例、资格、邮箱和代码记录均为虚构设定，不属于使用者，不可用于真实投递。邮箱只使用 `example.com`，单位名称一律带「示例」前缀。

这组示例展示同一条链路在五种职业上的结果：**源记录 → 完整文字履历 → 岗位简历 → 个人网页与时间线**。它不在 `local/` 里，属于公共仓库内容，可以提交、可以在 [文档站的多职业示例页](../../docs/examples.md) 在线查看。

| 职业 | 虚构人物 | 主题 |
|---|---|---|
| 小学语文教师 | 林知夏 | sage · 鼠尾草绿 |
| 产品设计师 | 许望舒 | lavender · 雾紫 |
| 企业客户销售 | 陈予安 | peach · 杏桃橙 |
| 财务会计 | 周清禾 | sea · 海盐青 |
| 软件工程师 | 沈亦川 | sky · 晴空蓝 |

## 每个职业有什么

以 `engineer/` 为例：

| 路径 | 内容 |
|---|---|
| `source/references/profile.md` | 完整职业档案：任职、教育、能力 |
| `source/references/facts.md` | 稳定事实 ID、状态与来源 |
| `source/references/projects/P01.md` … `P03.md` | 三张项目 / 案例卡：背景、本人行动、结果与边界 |
| `source/references/sources/SYN01.md` | 虚构来源快照，`manifest.json` 标记 `type: synthetic` |
| `source/data/timeline.json` | 网页展示数据，`meta.synthetic: true`，带职业模块 `presentation` |
| 构建目录的 `output/career/career.md` | 构建时从源记录聚合，保留来源状态与未知项；不在源目录重复提交 |
| `resume.zh-CN.md` / `resume.en.md` | 按方向精简后的中文简历正文 |
| `match-report.md` | 简历每条主张回指事实 ID，并列明未确认项 |
| `source/demo-code/` | 仅软件工程师示例：虚构本地 Git 演示记录 |

`examples.json` 保存网页设定与主题名称，颜色统一来自 `assets/themes/palette.json`；简历选材直接以正文和依据报告为准，不再保留一份重复的选材 JSON。简历不反向修改完整履历源记录，这些示例均不是新增真实事实。

## 在线怎么看

- **文档站**：[多职业示例总览](../../docs/examples.md) 列出五个职业，可进入各自的个人网页、完整履历、简历正文、依据报告和履历时间线。
- **仓库里**：上面表格中的 `.md` 文件可在 GitHub 直接阅读，是唯一需要维护的正文。
- **本地生成**：`pnpm docs:demo` 或 `pnpm docs:build` 会用 `scripts/career.py demo --docs` 与 `tools/build_site.py` 从这些源数据生成 `docs/public/demo/professions/` 下的网页。

## 为什么没有 PDF、DOCX 和 HTML

PDF、DOCX 与网页都是**导出产物**，不是事实来源。仓库只提交源记录、文字履历、简历和展示数据；二进制文件与生成网页由脚本从这些源数据重建，避免正文出现两份、修改后不同步。`.gitignore` 已忽略 `*.pdf` / `*.docx` 与 `docs/public/demo/`。

需要 Word / PDF 版本时，用 `scripts/career.py export` 从 `resume.zh-CN.md` / `resume.en.md` 导出 DOCX；PDF 从该 DOCX 转换并逐页检查。示例网页本身不依赖外部字体或脚本，可离线打开。

## 事实边界

- 五份 `timeline.json` 都设置 `meta.synthetic: true`，网页会显示虚构提示。
- 所有状态是模拟的 `resume-supported` / `confirmed`，只在示例内部有效，不代表本人确认或外部核实。
- 不虚构量化营收、提分、节省成本或性能提升；团队结果与本人贡献分开记录。
- 这组数据从未读取、修改或复制使用者的 `local/` 私人履历。

五个职业均提供中英文正文，共用同一份虚构事实映射；英文机构译名仅为示例。`pnpm docs:demo` 同时生成英文阅读页及两种语言的 Word 下载文件，生成文件不提交。PDF 使用本机 LibreOffice 按导出教程转换，不是文档站的构建依赖。

完整文字履历由 `build_site.py` 调用 `build_career.py` 当次聚合，不复制已生成的履历。源目录过去生成的 `source/output/` 可保留本地查看，已从公共清单排除并忽略，不是构建输入。
