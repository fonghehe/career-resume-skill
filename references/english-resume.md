# 英文简历与国际版式

用户要求英文简历、海外投递版本、中英双语简历，或明确要按欧美 / ATS 习惯排版时读取。中文默认版式见[简历版式](resume-style.md)，选材与事实依据仍按[简历流程](resume-workflow.md)执行，本文件只补充语言与版式规则。适用于各行业职业，模块按职业选择见[按职业组织](profession-workflow.md)。

## 先确认的范围

- 目标国家或地区：默认按英语国家通用的单栏 ATS 友好版式；用户提供具体国家 / 公司要求时按其要求调整，并在报告中说明差异。美国 / 加拿大默认 US Letter，英国、欧洲及其他 A4 地区用 `--page a4`。
- 语言与拼写：全篇统一美式或英式拼写，不混用；日期、标点和大小写风格保持一致。用户未指定时按目标地区选择并在报告注明假设。
- 英文正文与中文正文是同一事实库的两个版本，不是新事实。文件名用 `resume.en.md` / `resume.en.docx`，与 `resume.zh-CN.md` 分开保存，旧版本不覆盖。依据报告仍逐条映射稳定事实 ID。

## 写作规则

- 结构：`# 姓名` → 联系方式一行 → 标准分节标题。常用 `Professional Summary`、`Skills`、`Professional Experience`、`Education`、`Selected Projects`、`Certifications`、`Publications`。按职业增删、改名、合并，不保留空栏目；没有代码仓库证据不要出现开源模块。
- Summary 两到三行，只写已支持的领域、职责范围和最有力的证据；不写 "years of experience" 除非档案能算出且任职不重叠。资历较浅时可用 Education 前置。
- 每条 bullet 用动词开头（Built / Maintained / Coordinated / Analyzed / Taught / Designed），一到两行，写清本人动作、机制和有依据的结果；不写 "Responsible for"、第三人称自述或空泛形容词。当前任职用现在时，过去任职用过去时。
- 项目先写业务背景与真实难点，再写本人动作和结果；求职简历各项目模块合计通常最多 3–4 个；保留全部任职不等于罗列全部项目，规则同中文版。技术栈只写本人实际使用且与岗位相关的部分，不堆关键词，不把项目环境写成个人能力。
- 量化数字、上线责任、团队规模、语言等级、签证 / 工作许可、海外经历、推荐人，一律只在源记录支持时写；缺失就写具体功能或定性结果。没有 "Fluent English" 之类默认主张。
- 日期写成 `Mon YYYY – Mon YYYY` 或 `Mon YYYY – Present`（`Jan 2024 – Dec 2025`）。中文 `2024.01–2025.12` 转英文月份属于格式转换；原记录只有年份或只有年月时保留原精度（如 `2018 – 2022`），不补月份、不推断 `Present`。精确到日的短期区间可保留 `2020.08.03 – 2020.08.21` 数字格式以免丢精度，并在报告说明这一例外。日期区间必须是条目 `|` 分隔后的最后一段，导出时才会右对齐。
- 名称翻译：优先用户提供的官方英文名。没有官方名时公司、学校、项目名按常见译法或拼音写出，并在依据报告标注「译名未确认，待本人核对」，不编造英文公司名、不擅自改动职称含义。只有“本科”依据时写 bachelor’s degree，不推定 B.S. / B.Eng. 等未确认的学位类别。地名按目标地区习惯写城市与国家，例如 `Shenzhen, China`、`Hong Kong, China`。
- 不写照片、出生日期、性别、婚姻状况、国籍、薪资期望、"Objective"、"References available upon request" 或推荐人信息，除非目标国家惯例或用户明确要求；不把个人信息放进页眉页脚。
- 篇幅以一到两页为目标：早期职业一页，资深经历最多两页。Markdown 没有分页概念，实际页数只能从渲染后的 DOCX / PDF 检查，不能靠删任职凑页数。

## 国际版式（固定参数）

正文保存为 `resume.en.md` 时，`python3 scripts/career.py export 正文路径` 自动使用国际版式；其他文件名显式加 `--layout international`。主题色在国际版被忽略。

| 项 | 值 |
|---|---|
| 页面 | 默认 US Letter（8.5 × 11 in，12240 × 15840 twips）；`--page a4` 切到 11906 × 16838 |
| 页边距 | 四边 0.75 in（1080 twips）；页眉页脚不放关键信息 |
| 字体 | Arial 全篇（ascii / hAnsi / eastAsia 一致），无中文衬线混排 |
| 字号 | 姓名 20 pt；分节标题 11 pt 加粗；正文、条目、列表 10.5 pt；联系方式 10 pt |
| 颜色 | 姓名 / 分节标题 `#000000`，正文 `#333333`；无任何主题色、底色或色条 |
| 分节标题 | `w:caps` 视觉全大写（提取文本仍为原标题）+ 底部 0.75 pt 黑色细线；单栏，左对齐 |
| 条目 | 名称加粗，角色常规字重，末尾日期用右对齐制表位；不使用表格实现对齐 |
| 列表 | 标准 `•` 加制表符与悬挂缩进，无图标、图形或文本框 |
| 行距 | 姓名 24 pt，其余所有段落统一 14.4 pt 精确行距（`line=288`、`lineRule=exact`）；`snapToGrid=0`、无 `docGrid`、无内联行距覆盖 |
| 禁用 | 双栏、表格、图片、图标、文本框、背景色、页眉页脚中的联系方式、手动空行凑页 |

标准中文版式（`--layout standard`，非 `.en.md` 文件的默认值）不受影响：A4、主题色色条、正文 16.8 pt 精确行距，行为保持向下兼容。`--theme` 在国际版仍会校验取值但不参与着色。

## 导出与核对

```sh
python3 scripts/career.py export "local/output/resumes/2026-11-14-方向/resume.en.md" --layout international
python3 scripts/career.py export "…/resume.en.md" --layout international --page a4
```

在同目录生成 `resume.en.docx`。本地工作台按文件名识别 `resume.en.md`，下载 DOCX 时自动用国际版式（可在下载接口传 `page: a4`），主题选择只对中文版生效；英文版本的 `style.json` 记录 `layout` / `page` 而不记录主题色。正文用 `assets/templates/resume-en-template.md` 的结构；`###` 条目用 `|` 分隔字段，未知日期整段省略。导出脚本仍校验包完整性和文本顺序，并检查邮箱格式与日期倒序（含英文月份）。版本目录的 `style.json` 记录 `layout: international` 与 `page`，不记录主题色。

逐条核对：英文表述是否保持了中文版的参与程度、责任边界与日期精度；公司 / 职称 / 项目译名是否标注待确认；是否无意加入未支持的能力或数字；联系方式是否完整且只在正文；同类段落行距是否一致、日期是否未被挤压、有无孤行标题。PDF 从该 DOCX 转换，不用其他排版源重新转换，转换后逐页抽查。

在报告中记录实际做的文本检查与渲染检查。本项目能校验 DOCX 的 XML 结构与文本顺序，但**没有实测任何第三方 ATS 系统的解析结果**，也不声称已通过某公司的筛选；如需 ATS 验收，在目标系统导入导出的 PDF / DOCX 后单独记录结果。

需要 Word 和 PDF 两份文件时加 `--format all`，PDF 经本机 LibreOffice 从同一 DOCX 转换；已有 DOCX 用 `--format pdf`。具体失败处理与路径约定见[导出教程](../docs/guide/export-resume.md)。
