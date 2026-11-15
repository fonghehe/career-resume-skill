<script setup>
import { withBase } from 'vitepress'
</script>

# 完整虚构示例：履历、简历与网页

两阶段文字示例保存在仓库的 `examples/resume-demo/`：`request.md` 经历输入 → `career.md` 完整履历 → `resume.zh-CN.md` 简历正文与 `match-report.md` 依据报告。它们来自独立的虚构工单项目，用于展示事实保留和岗位选材；下方网页演示另用一组虚构数据。

想看教师、设计师、销售、财务和软件工程师五种职业的完整履历、简历与个人网页，见[五个职业的示例](examples.md)。

## 文字示例：从完整记录到岗位版本

教学输入给出：示例候选人在示例软件公司任前端工程师，2024.01–2025.12，负责 React / TypeScript 工单页、筛选、表单校验和加载 / 失败状态；参与 Java 接口联调，没有本人服务端开发证据。未提供教育、联系方式或性能数字。

第一阶段履历保留全部事实、月份精度及职责边界：

| 条目 | 完整履历记录 | 状态 |
|---|---|---|
| E01 | 示例软件公司，前端工程师，2024.01–2025.12 | 教学输入明示，仅限虚构演示 |
| E01-A | 负责 React / TypeScript 工单页、筛选、表单校验和加载 / 失败状态 | confirmed，仅限虚构演示 |
| E01-B | 参与与 Java 后端接口联调，没有个人服务端开发证据 | confirmed，仅限虚构演示 |

第二阶段，面向 React / TypeScript 业务后台岗位，正文可以写：

> 使用 React 和 TypeScript 实现工单页筛选与表单校验，处理加载和失败状态；参与与后端接口联调。

依据报告解释选材与缺口：

| 正文或岗位要求 | 事实依据 | 处理 |
|---|---|---|
| React / TypeScript 与表单功能 | E01-A | 采用本人实现，不补性能数字 |
| 接口协作 | E01-B | 保留“参与”程度 |
| Java 服务端开发 | 只有项目环境，无本人开发证据 | 列为缺口，不列为个人技能 |
| AI 模型训练 | 没有证据 | 不写入简历 |

完整履历继续保留 E01-B 的边界，简历选材不会回写成新增事实。没有 JD 时也能生成通用版，报告说明使用方向；不伪造岗位要求或匹配分数。

实际使用见[生成第一份履历](guide/first-library.md)与[根据履历生成简历](guide/generate-resume.md)。

## 同一份虚构履历还能做什么

| 操作 | 示例结果 |
|---|---|
| 导出 Word | 生成中英文单栏 DOCX，保留章节顺序和虚构提示；中文用主题色版式，英文用黑白国际版式（`--layout international`）。见[英文简历与海外投递](guide/english-resume.md)。 |
| 回顾 2025 年第四季度 | E01 支持这段期间的任职。E01-A 未提供工单功能的完成月份，单列为日期待确认，待补功能发布记录。 |
| 检查更正影响 | 假设用户更正 E01 的正式职称，依据报告指向「工作经历」的任职条目，需要核对该标题。 |
| 比较两份 JD | React 工单后台岗位由 E01-A 直接支持；Java 后端岗位的独立服务端开发要求仍是缺口，E01-B 仅能支持联调协作。 |

运行 `python3 scripts/career.py demo` 后，在 `local/output/demo/resume/` 查看虚构输入、完整文字履历、依据报告、中英文 Word、季度回顾和岗位对比。再次运行可用 `--output 新目录`。

想试着编辑下面这些任职和项目，运行 `python3 scripts/career.py workbench --demo`。可以修改、保存、刷新检查，再从修改历史恢复。详见[网页编辑教程](guide/workbench.md)。

## 可选网页示例

另一组网页示例包含 2 家公司、3 个任职 / 职级阶段、3 个工程项目、3 个仓库和 14 条本人署名 Commit。公司、职级、阶段、SHA 和提交均为虚构演示，不是真实采集结果。

<a :href="withBase('/demo/timeline.html')" target="_blank" rel="noreferrer">打开完整项目履历 ↗</a>

<iframe :src="withBase('/demo/timeline.html')" title="虚构公司、职级、项目与本人 Commit 统计" style="width:100%;height:800px;border:1px solid #e5e7eb;border-radius:16px;margin-top:20px" loading="lazy"></iframe>

可以查看：

- 示例乙公司内 P5 → P6 的两个任职阶段，仍统计为同一家公司。
- 三个项目的关键阶段、本人职责、关联仓库与 Commit 数。
- 各仓库本人提交活动区间与数量。
- 展开具体提交，筛选项目或仓库，查看原始主题、SHA 和双日期。

[快速开始](guide/quick-start.md)可直接从口述材料生成文字履历；旧简历和代码目录按需提供。本地演示用 `python3 scripts/career.py demo` 生成 `local/output/demo/showcase/project-timeline.html`，不读取或改变个人档案。
