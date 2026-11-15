# 能力、输入与交付

`career-resume-skill` 的主要流程是先建立完整履历，再据此生成求职材料。智能体负责读取材料、追问和写作，本地工具负责初始化、聚合、更新展示数据、校验与导出。仅运行脚本不会自动理解职业经历或岗位 JD。

## 核心能力

| 能力 | 你提供什么 | 实际交付 | 使用说明 |
|---|---|---|---|
| 生成完整履历 | 口述经历、旧简历、项目说明或已有档案 | 可维护的任职、教育、项目、技能与事实记录；`local/output/career/career.md` | [生成第一份履历](../guide/first-library.md) |
| 回顾多年项目 | 已有履历、项目卡与本人补充；不需要 JD | 完整履历及按请求生成的 `local/output/reviews/YYYY-MM-DD/review.md`，串联具体工作、职责变化与有依据的经验 | [项目与职业回顾](../guide/review-career.md) |
| 补充与更正 | 新事实、确认或明确纠正的字段 | 保留稳定编号、旧来源和职责边界，重建文字履历 | [履历维护](../guide/update-career.md) |
| 通用简历 | 最新履历、方向、语言或篇幅偏好；JD 可缺省 | 简历正文与独立 `match-report.md`，有事实依据映射 | [生成简历](../guide/generate-resume.md) |
| 岗位定向简历 | 最新履历与实际 JD | 相关经历选材、正文、要求映射及能力缺口，保留完整履历 | [生成简历](../guide/generate-resume.md) |
| 英文 / 海外投递简历 | 最新履历、目标地区与语言偏好 | `resume.en.md` + 黑白 ATS 友好 `resume.en.docx`，译名待确认项在报告中标注 | [英文简历与海外投递](../guide/english-resume.md) |
| 局部润色和翻译 | 指定条目或文本，以及事实边界 | 只修改指定范围，保留参与程度与确认状态 | [生成简历](../guide/generate-resume.md) |
| 技术案例和面试材料 | 已有项目卡、可采用的事实及本次目标 | 项目讲述、方案取舍、可能追问与事实依据；未知项单列 | [项目案例](../guide/project-cases.md)、[面试准备](../guide/prepare-interview.md) |
| 按月或季度回顾 | 现有履历与时间范围 | 有依据的进展、职责变化与待确认清单 | [定期回顾](../guide/review-career.md#按月或季度回顾) |
| 多 JD 横向对比 | 两份或更多岗位原文、最新履历 | 硬性条件、直接证据、可迁移经验与缺口 | [岗位对比](../guide/generate-resume.md#同时看几个岗位) |

## 本地工具与可选视图

| 能力 | 运行入口 | 结果与条件 |
|---|---|---|
| 多端安装与引用 | `career.py install` | 任意指定技能目录、共享项目目录、通用 ZIP 及常见客户端快捷方式；不复制个人资料，已有目标拒绝覆盖 |
| 初始化或独立工作副本 | `career.py init`，共享安装用 `--workspace` | 补缺失文件或创建完整空副本，保留已有资料 |
| 浏览器编辑与恢复 | `career.py workbench` | 任职、项目、原文、字段确认、修改历史、简历版本与局部 Agent 材料 |
| Word / PDF 导出 | `career.py export` | 中英文正文生成可编辑 DOCX，PDF 经本机 LibreOffice 转换；检查文本顺序，分页与字体另核对 |
| 版本差异与更正影响 | `career.py versions` | 比较两个同语言版本，或按更正的事实 ID 查依据报告 |
| 文字履历聚合 | `career.py build` | 从维护好的 Markdown 生成完整文字履历；无须 Git 或网页 |
| 本人 Git 统计与项目映射 | `career.py git` | 本地目录、本人邮箱和已确认映射 → 私人报告及去重活动；需 Git |
| 展示数据增量、冲突保护与撤回 | `career.py update` | 预览合并差异；`--apply` 保存；撤回仅覆盖展示 JSON |
| 项目来源、截图和附件 | 智能体整理，网页构建时处理 | 保存在私人库并关联项目；受支持格式与大小见公共规则 `references/enhancements.md` |
| 离线履历网页 | `career.py web` | 任职阶段、项目卡与本人代码统计，可离线筛选查看 |
| 选定范围分享 | `career.py share` 或网页下载按钮 | 单独 HTML 副本，默认去掉来源、仓库标识及提交明细 |
| 公开包与结构化私人备份 | `career.py package` | 空模板运行 ZIP 或明确选择的私人记录备份；源码维护另用 `release.py` 生成版本产物 |
| 结构、来源、链接及网页一致性 | `career.py validate` | 结构校验，不核实职业事实真实性；源码维护另用 `check.py` 在临时公共副本执行回归 |

完整参数见[工具命令](commands.md)。网页是附加视图，不代替文字履历；Git 活动不推导入离职日期、职称或业务成果。

## 需要宿主支持的部分

PDF / Word / 扫描件的文字提取由当前智能体宿主提供；附件不能读取时改用可读文字。DOCX 可用本地 Python 导出。Word 的字体和分页需要用编辑器核对，PDF 可用本机 LibreOffice 自动转换或在 Word 中另存，详见[导出教程](../guide/export-resume.md)。文件写入需要宿主访问工作副本，仅聊天时由使用者手动保存。

普通履历与 Markdown 简历流程不要求 Node.js、远端仓库访问或专用 API 密钥。只有教程站开发需要 Node / pnpm；模型及附件的处理方式取决于所选宿主。

## 怎样判断这次任务完成了

履历任务应给出文字履历和实际源记录；简历任务应给出正文与可回查的依据报告。先检查文件存在，再检查日期、归属、职责和来源是否符合材料。虚构示例只能用于演练，不能自动变成个人经历。

确定性工具的测试范围见[行为测试](https://fonghehe.github.io/career-resume-skill/maintainers/behavior-testing.html)。宿主的材料理解、追问、写作和 Word / PDF 排版需按具体产物验收，不能用 Python 测试结果替代。
