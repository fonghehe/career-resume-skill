# 目录与文件怎么放

下载或 clone 的目录名称可以自定，例如 `career-resume-skill/` 或 `my-career/`。Skill 名称保持 `career-resume-skill`；日常使用以你打开的完整工作副本为准。

## 公共资源与私人工作区

```text
工作副本/
├── SKILL.md                     智能体入口与交付约定
├── README.md / README.en.md     使用介绍
├── agents/                     客户端展示信息
├── references/                 公共整理、维护与简历生成规则
├── assets/
│   ├── starter/                空白私人资料模板，初始化时使用
│   ├── templates/              履历、项目卡、简历与报告内容模板
│   └── examples/
│       ├── resume-demo/        虚构输入 → 文字履历 → 简历与依据报告
│       └── career-demo/        虚构任职、项目、Git 与附件网页夹具
├── scripts/                    可直接执行的 Python 工具及共享模块
├── tests/                      工具测试与宿主行为验收场景
├── docs/
│   ├── guide/                  用户操作教程
│   ├── reference/              目录、命令、数据和兼容说明
│   ├── maintainers/            文档开发、测试与发布
│   └── .vitepress/             站点配置与被忽略的构建产物
├── .github/                    社区规则与 CI
└── local/                      当前使用者的资料与产物，Git 忽略
```

根目录 `references/` 是公共规则；`local/references/` 是你的真实资料。`assets/starter/` 始终保持为空模板。初始化会创建需要的文件，项目卡、附件和产物目录随实际使用出现，不必先建所有空文件夹。

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
│   ├── questions-to-confirm.md 待确认事项
│   └── excluded/               明确排除的内容
├── data/timeline.json           可选网页展示摘要
├── output/
│   ├── career/career.md        完整文字履历
│   ├── resumes/                日期与方向分开的简历正文、依据报告
│   ├── interviews/             面试讲述、事实依据与待补充问题
│   ├── git-activity/           原始本地 Git 采集报告
│   ├── updates/                展示数据更新差异及撤回记录
│   ├── shares/                 用户选定范围的分享副本
│   └── demo/                   独立虚构网页演示
├── showcase/                    可选离线履历网页
└── dist/                        导出包与结构化备份
```

`references/role-matching.md`、`resume-modes.md`、`output.md` 等文件在私人工作区中是可调整的写作规则和偏好，不能当作新增职业事实。只用自然语言提供材料时，文件整理交给智能体即可。

## 材料放哪里，结果看哪里

| 你的操作 | 文件位置 |
|---|---|
| 放一份旧简历 | `local/private/resume.pdf` 或你提供的真实路径 |
| 直接口述经历 | 智能体保存到 `local/references/sources/`，记录本次陈述 |
| 补职责、结果、日期或纠正归属 | 对应档案、事实记录和项目卡，保留旧来源 |
| 看完整履历 | `local/output/career/career.md`，源记录入口为 `local/references/career/README.md` |
| 看求职简历 | `local/output/resumes/YYYY-MM-DD-方向/`；旧版本加后缀保留 |
| 看项目网页 | `local/showcase/project-timeline.html`，生成后可离线打开 |
| 升级或换电脑 | 先完整备份 `local/`，原始代码仓库另行备份 |

网页附件引用 `local/references/attachments/` 中的受支持副本；私人原件仍放 `local/private/`。数据里的相对路径从 `local/` 开始，例如 `references/sources/S1.md`；在使用说明里写完整位置时则为 `local/references/sources/S1.md`。

## 共享安装和已有旧目录

公共安装支持任意技能父目录与 ZIP；客户端快捷入口只是示例。能读取文件但没有原生 Skill 的宿主可以使用 `assets/templates/agent-entry-template.md` 配置短入口，见[多智能体安装](../guide/using-skill.md)。

自己的 clone 可直接用 `local/`。共享 / 只读安装先通过 `init_profile.py --workspace` 创建一个新的完整工作副本，随后打开新副本并使用其中的工具。工具依据脚本所在目录选择默认资料，单独改变终端 cwd 不会切换库。

旧版根目录中的 `references/profile.md`、`data/`、`output/`、`showcase/` 仍可读取。升级不自动搬运或覆盖这些资料，也不要同时创建旧版与新版两套活跃档案；遇到歧义先明确使用哪套。迁移前备份，目录选择说明见[安装与兼容](compatibility.md)。

下一步：[快速开始](../guide/quick-start.md)或[补充与更正履历](../guide/update-career.md)。
