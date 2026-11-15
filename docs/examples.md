<script setup>
import { withBase } from 'vitepress'

const sites = [
  { slug: 'teacher', name: '林知夏', role: '小学语文教师', theme: '鼠尾草绿',
    intro: '整本书阅读、习作与形成性评价，案例围绕课堂任务与学习档案展开。' },
  { slug: 'designer', name: '许望舒', role: '产品设计师', theme: '雾紫',
    intro: '企业服务与预约服务的信息结构、状态设计和交付协作。' },
  { slug: 'sales', name: '陈予安', role: '企业客户销售', theme: '杏桃橙',
    intro: '需求澄清、方案边界与交付衔接，团队结果不归为个人独立贡献。' },
  { slug: 'finance', name: '周清禾', role: '财务会计', theme: '海盐青',
    intro: '应收核对、月结支持与费用流程，强调口径一致和可复核底稿。' },
  { slug: 'engineer', name: '沈亦川', role: '软件工程师', theme: '晴空蓝',
    intro: '订单状态、实时事件与共享组件，项目环境与本人贡献分开记录。' },
]
</script>

# 五个职业的履历、简历与个人网页

> **全部为虚构教学示例。** 人物、单位、经历、案例、资格、邮箱和代码记录均为设定，不属于使用者，不可用于真实投递；邮箱只用 `example.com`，单位名称一律带「示例」前缀。五份展示数据都设置了 `meta.synthetic: true`，网页会显示虚构提示。

这组示例把同一条链路跑了五遍：**带来源的事实记录 → 完整文字履历 → 中英文岗位简历 → 面向访客的个人网页与履历时间线**。职业不同，网页模块和配色也不同；简历只从履历中选材，不反向改写履历源记录。

## 在线浏览

<a :href="withBase('/demo/professions/index.html')" target="_blank" rel="noreferrer">打开五个职业的示例集（新窗口）↗</a>

每个示例都含 2 段任职、3 个可展开的案例、职业专属模块与固定 HEX 配色，并且都能从个人网页跳到完整履历、简历、依据报告和履历时间线。

<div v-for="site in sites" :key="site.slug" style="margin:14px 0;padding:14px 16px;border:1px solid var(--vp-c-divider);border-radius:10px">
  <strong>{{ site.name }} · {{ site.role }}</strong>
  <span style="color:var(--vp-c-text-2);font-size:13px;margin-left:8px">{{ site.theme }}</span>
  <p style="margin:6px 0 10px;color:var(--vp-c-text-2);font-size:14px">{{ site.intro }}</p>
  <a :href="withBase('/demo/professions/' + site.slug + '/index.html')" target="_blank" rel="noreferrer">个人网页 ↗</a> ·
  <a :href="withBase('/demo/professions/' + site.slug + '/career.html')" target="_blank" rel="noreferrer">完整履历 ↗</a> ·
  <a :href="withBase('/demo/professions/' + site.slug + '/resume.html')" target="_blank" rel="noreferrer">中文简历 ↗</a> ·
  <a :href="withBase('/demo/professions/' + site.slug + '/resume.en.html')" target="_blank" rel="noreferrer">英文简历 ↗</a> ·
  <a :href="withBase('/demo/professions/' + site.slug + '/resume.zh-CN.docx')" :download="site.slug + '-resume.zh-CN.docx'">中文 Word ↓</a> ·
  <a :href="withBase('/demo/professions/' + site.slug + '/resume.en.docx')" :download="site.slug + '-resume.en.docx'">英文 Word ↓</a> ·
  <a :href="withBase('/demo/professions/' + site.slug + '/report.html')" target="_blank" rel="noreferrer">依据报告 ↗</a> ·
  <a :href="withBase('/demo/professions/' + site.slug + '/timeline.html')" target="_blank" rel="noreferrer">履历时间线 ↗</a>
</div>

**三种产物不要混为一谈**：[完整履历](guide/first-library.md)保留全部事实、来源状态与未知项；[简历](guide/generate-resume.md)按方向精简，每条主张要能回到稳定事实 ID；个人网页面向访客，只展示已确认、可公开的内容。[生成离线履历网页](guide/generate-webpage.md)说明了职业模块如何随职业变化。

## 仓库里的源文件

示例正文提交在 `examples/professions/`，可在 GitHub 上直接阅读 Markdown：

- [示例设定与目录说明](https://github.com/fonghehe/career-resume-skill/blob/main/examples/professions/README.md)
- [五个职业的网页设定 `examples.json`](https://github.com/fonghehe/career-resume-skill/blob/main/examples/professions/examples.json)
- 每个职业目录下：`source/references/`（档案、事实、案例卡、虚构来源）、`source/data/timeline.json`（展示数据）、`resume.zh-CN.md`、`resume.en.md`（中英文简历）、`match-report.md`（依据与边界）。

完整文字履历从 `source/references/` 在构建时聚合；源目录不重复提交生成的 `source/output/`。仓库**不提交** PDF、DOCX 和生成网页：它们是导出产物，正文只保留一份，避免两处不同步。`tools/build_site.py` 从这些源数据重建页面，`pnpm docs:demo`（`docs:build` 会自动先执行）生成到被 Git 忽略的 `docs/public/demo/professions/`。构建同时生成中英文 Word 下载文件，英文为国际版式。PDF 可按[导出教程](guide/export-resume.md)从对应正文或 DOCX 本地转换，不要求文档构建环境安装 LibreOffice。

## 自己照着做

1. 用[快速开始](guide/quick-start.md)在 `local/` 建立带来源的事实记录，先生成[完整文字履历](guide/first-library.md)。
2. 按[根据履历生成简历](guide/generate-resume.md)选材，正文与依据报告一起另存。
3. 需要网页时读[生成离线履历网页](guide/generate-webpage.md)，从展示摘要生成时间线；要公开个人网页，先筛选可公开事实、审查内容并另做公开副本，**不要直接部署私人 HTML**。

另有一组更小的[两阶段文字示例](example.md)：从虚构输入到履历、简历、依据报告和可选网页，适合先看最小链路。

<iframe :src="withBase('/demo/professions/index.html')" title="五个虚构职业的示例集" style="width:100%;height:620px;border:1px solid var(--vp-c-divider);border-radius:12px;margin-top:24px" loading="lazy"></iframe>
