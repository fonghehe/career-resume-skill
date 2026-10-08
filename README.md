# career-resume-skill · 履历与简历

中文 · [English](README.en.md) · [文档站](https://fonghehe.github.io/career-resume-skill/) · [GitHub](https://github.com/fonghehe/career-resume-skill) · [MIT](LICENSE)

**先把经历整理成完整履历，再根据履历生成通用或岗位定向简历。**

履历保留完整任职、教育、项目职责、技能与成果，以及它们的来源和待确认信息。简历从中选择真实事实，形成不同求职方向的版本。口述经历、旧简历或项目说明都可以作为起点；没有 JD 和代码仓库也能开始。

写了多年代码，项目经历可能散在旧简历、仓库、文档和记忆里。可以先选一个还记得清楚的项目，逐步整理当时的问题、职责和技术判断，再回看不同阶段做过什么、哪些经验还能继续用。暂时不找工作，也可以把它当作一份持续补充的职业记录。

[回顾这些年做过的项目](docs/guide/review-career.md) · [多智能体接入](docs/guide/using-skill.md)

## 三步使用

**1. 打开自己的工作副本。** 下载或 clone 完整项目，用能读写文件的智能体打开，然后说：

```text
请读取当前项目的 SKILL.md，先检查已有资料。
个人资料和产物统一保存在当前副本的 local/ 中。
缺少的空档案按需初始化，已有事实继续使用。
```

**2. 提供经历，生成履历。** 旧简历可放 `local/private/resume.pdf`，也可以直接讲述：

```text
我的经历材料是【口述内容或实际材料路径】。
先生成完整文字履历，整理任职、教育、项目职责、技能与成果。
保留来源、确认状态和本人贡献边界，未知先留空。
交付文字履历和源记录入口，只问少量关键问题。
```

查看 `local/output/career/career.md`，源记录入口是 `local/references/career/README.md`。以后打开同一目录，说“补充这个项目的职责”或“更正这段任职日期”即可。

**3. 根据履历生成简历。**

```text
请根据最新履历生成前端方向的中文通用简历，目前没有 JD。
交付完整正文和独立依据报告，保留完整履历及已有简历版本。
```

结果放在 `local/output/resumes/YYYY-MM-DD-方向/`：正文为 `resume.zh-CN.md` 或 `resume.en.md`，报告为 `match-report.md`。提供 JD 可生成岗位版本；只改一条或翻译一段时按指定范围处理。

[快速开始](docs/guide/quick-start.md) · [补充与更正](docs/guide/update-career.md) · [生成简历](docs/guide/generate-resume.md) · [完整虚构示例](docs/example.md)

## 多智能体接入

入口遵循 Agent Skills 格式，可通过生态安装器选择多个客户端，也可指定任意本地技能目录、导入 ZIP 或直接读取 `SKILL.md`。新增客户端无需改写 Skill。

```sh
# 交给生态安装器选择一个或多个智能体（另需 Node.js/npm 与网络）
python3 scripts/package.py --public-dir local/dist/ecosystem/career-resume-skill
npx skills add ./local/dist/ecosystem/career-resume-skill --skill career-resume-skill --copy

# 任意支持本地 Skill 的宿主：指定其实际技能父目录
python3 scripts/install_skill.py --skills-dir /实际客户端的技能目录

# 任意接收此结构的宿主：生成通用导入 ZIP
python3 scripts/install_skill.py --output local/dist/career-resume-skill-import.zip
```

安装只复制公共资源与空模板，已有目标拒绝覆盖；加 `--dry-run` 可预览。支持项目 `.agents/skills/` 的宿主可以直接用 `--project /工作副本路径`。Codex、Claude Code、Trae、WorkBuddy 的快捷入口继续保留，作为常见示例。

始终指定个人工作副本，让智能体使用其中的规则、资料与脚本。安装方式、生态工具、常见客户端和自建智能体说明见[多智能体接入教程](docs/guide/using-skill.md)；具体发现与执行能力须在目标宿主验收。

## 目录怎么分

```text
工作副本/
├── SKILL.md / agents/       智能体入口与展示信息
├── references/             公共 Skill 规则
├── assets/
│   ├── starter/            空白私人资料模板
│   ├── templates/          履历、项目卡、简历与报告模板
│   └── examples/
│       ├── resume-demo/    虚构履历到简历的完整文字示例
│       └── career-demo/    虚构网页与 Git 示例
├── scripts/                本地工具
├── tests/                  工具测试与行为场景
├── docs/                   教程、参考与维护说明
└── local/                  当前使用者资料，Git 忽略
    ├── README.md           工作区使用入口
    ├── private/            原始简历与附件
    ├── references/         事实、来源、项目卡与个人写作偏好
    ├── data/               可选网页展示数据
    ├── output/             完整文字履历、简历版本与报告
    ├── showcase/           可选离线网页
    └── dist/               导出包与结构化备份
```

日常主要关注 `local/private/`、`local/references/` 和 `local/output/`。项目卡、附件及产物目录随使用创建；目录名可以自定，Skill 调用名称保持 `career-resume-skill`。完整说明见[目录与文件位置](docs/reference/directories.md)。

自己的 clone 可以直接使用。共享 / 只读安装用 `scripts/init_profile.py --workspace` 创建新的完整工作副本，再打开新目录；不能仅改变终端 cwd 来切换脚本默认资料库。旧布局继续兼容，初始化不覆盖已有材料。

## 可选能力与环境

基础工具使用 Python 3.9+ 标准库；Git 统计另需系统 Git。附件解析、Word / PDF 取决于宿主的实际工具。简历写作由智能体读取事实后完成，Python 工具负责聚合、校验和导出。无文档工具时交付 Markdown，并说明实际格式。

网页可展示公司内职级阶段、项目历程与本人署名 Commit；数据不会据此推断任职日期、职称或独立成果。本地虚构网页演示：

```sh
python3 scripts/create_demo.py
```

打开 `local/output/demo/showcase/project-timeline.html`。演示与私人资料隔离，已有演示目录拒绝覆盖。

[能力与交付](docs/reference/capabilities.md) · [面试准备](docs/guide/prepare-interview.md) · [工具命令](docs/reference/commands.md) · [调用方式](docs/guide/using-skill.md) · [Git 统计](docs/guide/git-timeline.md) · [网页生成](docs/guide/generate-webpage.md)

## 资料保存与维护

公共模板保持空白，示例明确标注虚构；个人材料集中在 `local/`，不提交到公开仓库。忽略规则不能清除已跟踪文件或历史。升级前备份完整 `local/`；结构化私人 ZIP 不包含全部原始附件与简历产物。

需要开发教程站或维护公共工具时，再运行：

```sh
python3 scripts/check.py
pnpm install --frozen-lockfile
pnpm docs:build
```

文档站另需 Node.js 22+ 与项目锁定的 pnpm；日常使用无需启动站点。工具测试不代替附件解析、模型行为或 Word / PDF 排版验收。

[隐私与备份](docs/guide/privacy.md) · [贡献指南](.github/CONTRIBUTING.md) · [安全报告](.github/SECURITY.md) · [发布说明](docs/maintainers/releasing.md)

通用代码与模板采用 MIT，个人资料和第三方材料不因此获得公开授权。
