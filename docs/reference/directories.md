# 目录与文件怎么放

下载或 clone 的目录名称可以自定，例如 `career-resume-skill/` 或 `my-career/`。Skill 名称保持 `career-resume-skill`；日常使用以你打开的完整工作副本为准。

Release / 市场 ZIP 为运行布局，省略下图中的 `tools/`、`tests/`、`docs/maintainers/`、`docs/.vitepress/`、`.github/` 及其他仓库维护文件；根 README 为运行说明。脚本、模板、最小虚构演示及六份操作指南保留；完整教程留在文档站。`career.py init` 会在使用时生成工作副本 `.gitignore`。

## 公共资源与私人工作区（源码布局）

```text
工作副本/
├── SKILL.md                     智能体入口与交付约定
├── README.md / README.en.md     使用介绍
├── agents/                     客户端展示信息
├── references/                 公共整理、维护与简历生成规则
├── assets/
│   ├── starter/                空白私人资料模板，初始化时使用
│   ├── templates/              履历、项目卡、简历与报告内容模板
│   ├── themes/                 网页与简历共用配色
│   └── workbench/              本地工作台界面资源
├── examples/
│   ├── resume-demo/            虚构履历 → 简历与依据报告
│   ├── career-demo/            虚构网页、Git 与附件数据
│   └── professions/            不同职业的完整虚构教学案例
├── scripts/
│   ├── career.py               日常命令唯一入口，--help 查看子命令
│   └── career_resume/          内部实现与公共资源打包清单
├── tools/                      源码检查、发布打包和文档示例构建
├── tests/                      工具测试与宿主行为验收场景
├── docs/
│   ├── guide/                  用户操作教程
│   ├── reference/              目录、命令、数据和兼容说明
│   ├── maintainers/            文档开发、测试与发布
│   └── .vitepress/             站点配置与被忽略的构建产物
├── .github/                    社区规则与 CI
└── local/                      当前使用者的资料与产物，Git 忽略
```

根目录 `references/` 是公共规则；`local/references/` 是你的真实资料。`assets/starter/` 始终保持为空模板，`examples/professions/` 是明确标注虚构、可提交的公共示例，与私人资料无关。初始化会创建需要的文件，项目卡、附件和产物目录随实际使用出现，不必先建所有空文件夹。

## 日常关注这几个位置

```text
local/
├── README.md                    工作区使用入口
├── private/                     原始简历、项目说明和附件
├── references/
│   ├── career/README.md         履历阅读入口
│   ├── profile.md              完整任职、教育与技能范围
│   ├── facts.md                稳定事实编号、确认与更正
│   ├── project-index.md        项目索引
│   ├── projects/               项目卡：背景、本人工作、结果与证据
│   ├── sources.md              来源索引
│   ├── sources/                来源文字快照与 manifest.json
│   ├── attachments/            已关联的项目截图 / 发布说明
│   └── questions-to-confirm.md 待确认事项
├── data/timeline.json           可选网页展示摘要
├── output/
│   ├── career/career.md        完整文字履历
│   ├── resumes/                各版本的简历正文、依据报告与可选 DOCX
│   ├── reviews/                职业回顾和按期回顾草稿
│   ├── job-comparisons/        多个岗位的依据与缺口对照
│   ├── interviews/             面试讲述、事实依据与待补充问题
│   ├── git-activity/           原始本地 Git 采集报告
│   ├── workbench/history/     网页修改历史与恢复快照
│   ├── updates/                展示数据更新差异及撤回记录
│   ├── shares/                 用户选定范围的分享副本
│   └── demo/                   独立虚构网页和中英文简历演示
├── showcase/                    可选离线履历网页
└── dist/                        导出包与结构化备份
```

初始化只创建通用档案、事实、项目索引、来源和待确认记录；能力边界、更正与排除统一记录在 `facts.md`，详细案例按实际需要建立。岗位选材、经历覆盖与交付规则统一维护在公共 `references/resume-workflow.md`，不再复制成每个私人工作区的规则文件。旧工作区已有的 `role-matching.md`、`resume-modes.md`、`output.md` 等个人写作偏好仍可按需读取，不能当作新增职业事实；升级不会删除这些旧文件。

## 材料放哪里，结果看哪里

| 你的操作 | 文件位置 |
|---|---|
| 放一份旧简历 | `local/private/resume.pdf` 或你提供的真实路径 |
| 直接口述经历 | 智能体保存到 `local/references/sources/`，记录本次陈述 |
| 补职责、结果、日期或纠正归属 | 对应档案、事实记录和项目卡，保留旧来源 |
| 看完整履历 | `local/output/career/career.md`，源记录入口为 `local/references/career/README.md` |
| 看求职简历 | `local/output/resumes/YYYY-MM-DD-方向/`；旧版本加后缀保留 |
| 看项目网页 | `local/showcase/project-timeline.html`，生成后可离线打开 |
| 看公共多职业示例 | `docs/examples.md` 在线总览；`examples/professions/` 是提交在仓库里的虚构源记录、履历与简历 |
| 升级或换电脑 | 先完整备份 `local/`，原始代码仓库另行备份 |

网页附件引用 `local/references/attachments/` 中的受支持副本；私人原件仍放 `local/private/`。数据里的相对路径从 `local/` 开始，例如 `references/sources/S1.md`；在使用说明里写完整位置时则为 `local/references/sources/S1.md`。

## 共享安装和已有旧目录

公共安装支持任意技能父目录与 ZIP；客户端快捷入口只是示例。能读取文件但没有原生 Skill 的宿主可以使用 `assets/templates/agent-entry-template.md` 配置短入口，见[多智能体安装](../guide/using-skill.md)。

选择或创建个人工作副本，按[快速开始的目录选择](../guide/quick-start.md#怎么选目录)操作；已有资料继续在同一副本维护。

旧版根目录中的 `references/profile.md`、`data/`、`output/`、`showcase/` 仍可读取。升级不自动搬运或覆盖这些资料，也不要同时创建旧版与新版两套活跃档案；遇到歧义先明确使用哪套。迁移前备份，目录选择说明见[安装与兼容](../guide/using-skill.md)。

下一步：[快速开始](../guide/quick-start.md)或[补充与更正履历](../guide/update-career.md)。

## 运行流程与扩展

源记录始终在 `local/references/`：先由智能体整理事实与来源，再由工具聚合文字履历；中英文简历从同一事实基线选材写作，导出 Word / PDF；网页只读取按展示范围同步的摘要。输出不反向升级事实。

新增职业不需要注册或新增脚本。任职、教育、资格、作品、研究和服务等记录按材料命名，案例与代码资料可选；网页模块通过 `presentation` 自由组织。`scripts/career.py` 是统一使用入口，其余 Python 文件是被调用的工具或共享模块。

运行包只保留直接执行需要的离线指南，详细教程、站点开发和维护说明留在文档站。空模板只保留 `assets/starter/` 一份，`local/` 在首次初始化时创建。可重建产物和私人资料不随运行包分发。

目录调整后，原先的 `scripts/init_profile.py`、`scripts/export_resume.py` 等直接脚本命令改用 `python3 scripts/career.py init`、`python3 scripts/career.py export` 等子命令；不需要进入内部实现目录。维护者使用 `python3 tools/check.py` 检查源码、`python3 tools/release.py --skillhub` 生成市场包。旧版升级步骤见[保留资料更新](../guide/upgrade-skill.md)。
