# career-resume-skill · 履历与简历

中文 · [English](README.en.md) · [文档站](https://fonghehe.github.io/career-resume-skill/) · [GitHub](https://github.com/fonghehe/career-resume-skill) · [MIT](LICENSE)

**一个通用的职业履历 Skill：添加和维护履历、生成个人网页、生成并导出中英文简历。**

使用同一个 Skill 添加和维护工作、学习与实践记录，生成个人网页、中英文简历，并导出 Word / PDF。模块由本人材料和当前目标决定，不需要先选择职业模板；没有项目或代码经历也能使用。任职、服务、资格、作品、课程、研究等记录都按同一套来源和事实规则维护，跨职业或尚未确定求职方向也可以开始。

| 想做什么 | 直接告诉智能体 | 结果看哪里 |
|---|---|---|
| 添加履历 | “我是【职业】，请把以下经历加入履历，未知留空。” | `local/references/`、`local/output/career/career.md` |
| 维护履历 | “把这段职责从负责更正为参与，保留来源和其他事实。” | 同一份源记录及重建的完整履历 |
| 生成个人网页 | “根据履历生成适合我的职业的离线网页，只展示允许公开的内容。” | `local/showcase/project-timeline.html` |
| 生成中英文简历 | “按【目标岗位】生成中英文简历，各附依据报告，保留旧版。” | `local/output/resumes/` 下的独立版本 |
| 导出简历 | “把这两份简历导出 Word 和 PDF，检查文本与分页。” | 版本目录中的 `.docx`、`.pdf` |

[快速开始](docs/guide/quick-start.md) · [教学示例](docs/examples.md) · [导出 Word / PDF](docs/guide/export-resume.md) · [安装与调用](docs/guide/using-skill.md)

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
请根据最新履历生成【我的目标职业 / 岗位】的中英文通用简历，目前没有 JD。
两种语言分别交付正文和依据报告，并导出 Word；需要时再导出 PDF。
保留完整履历及已有简历版本，英文翻译不改变事实和本人贡献。
```

结果放在 `local/output/resumes/YYYY-MM-DD-方向/`：正文为 `resume.zh-CN.md` 或 `resume.en.md`，报告为 `match-report.md`。提供 JD 可生成岗位版本；只改一条或翻译一段时按指定范围处理。

[快速开始](docs/guide/quick-start.md) · [补充与更正](docs/guide/update-career.md) · [生成简历](docs/guide/generate-resume.md) · [教学示例](docs/examples.md) · [两阶段文字示例](docs/example.md)

## 多智能体接入

入口遵循 Agent Skills 格式，可通过生态安装器选择多个客户端，也可指定任意本地技能目录、导入 ZIP 或直接读取 `SKILL.md`。新增客户端无需改写 Skill。

```sh
# 交给生态安装器选择一个或多个智能体（另需 Node.js/npm 与网络）
python3 scripts/career.py package --runtime --public-dir local/dist/ecosystem/career-resume-skill
npx skills add ./local/dist/ecosystem/career-resume-skill --skill career-resume-skill --copy

# 任意支持本地 Skill 的宿主：指定其实际技能父目录
python3 scripts/career.py install --skills-dir /实际客户端的技能目录

# 任意接收此结构的宿主：生成通用导入 ZIP
python3 scripts/career.py install --output local/dist/career-resume-skill-import.zip
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
│   ├── themes/             网页与简历共用配色
│   └── workbench/          本地工作台界面
├── examples/               虚构履历、简历与网页教学示例
├── scripts/
│   ├── career.py           日常命令唯一入口
│   └── career_resume/      内部实现模块
├── tools/                  源码检查、发布和文档示例构建
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

自己的 clone 可以直接使用。共享 / 只读安装用 `scripts/career.py init --new` 创建新的完整工作副本，再打开新目录；不能仅改变终端 cwd 来切换脚本默认资料库。旧布局继续兼容，初始化不覆盖已有材料。

## 在网页里直接编辑

在自己的完整工作副本运行 `python3 scripts/career.py workbench`，浏览器会打开本地履历工作台。可以编辑任职、项目与案例，确认事实，查看和恢复历史，并另存简历或下载中英文 DOCX / PDF。

想先试用有内容的示例，运行 `python3 scripts/career.py workbench --demo`。示例使用临时虚构资料库，结束时清理。详细步骤见[网页编辑教程](docs/guide/workbench.md)。

## 一个命令入口

以下命令在自己的完整工作副本运行，Python 不负责理解材料或代写简历；这些工作由智能体按 Skill 完成。

```sh
python3 scripts/career.py init                 # 只补缺项，保留已有资料
python3 scripts/career.py build                # 从源记录重建完整履历
python3 scripts/career.py web                  # 从已同步的摘要生成个人网页
python3 scripts/career.py workbench            # 本地网页编辑履历、下载简历
python3 scripts/career.py export "实际版本/resume.en.md" --format all
python3 scripts/career.py validate
```

英文文件名 `resume.en.md` 自动使用黑白国际版式；中文使用单栏主题版式。PDF 需要本机 LibreOffice。切换资料库用 `python3 scripts/career.py --workspace /实际完整副本路径 命令`，相对导出路径按该副本解析。原先分散的脚本统一改用 `career.py` 子命令，完整参数见[命令参考](docs/reference/commands.md)。

## 可选能力与环境

基础工具使用 Python 3.9+ 标准库。DOCX 导出无需第三方 Python 库；PDF 从该 DOCX 经本机 LibreOffice 转换，没有转换器时可在 Word 中另存 PDF。附件解析由宿主提供。已有履历时，还可以按月或季度回顾、比较多个 JD，或检查更正过的事实是否影响旧简历。

[导出 Word、比较岗位和版本](docs/guide/generate-resume.md) · [月度或季度回顾](docs/guide/review-career.md#按月或季度回顾)

网页可展示任职、教育、资格、代表案例和自定义经历模块；确有代码资料时可附本人代码活动。数据不会据此推断任职日期、职称或独立成果。本地虚构网页演示：

```sh
python3 scripts/career.py demo
```

打开 `local/output/demo/showcase/project-timeline.html` 查看任职和项目，在同级 `demo/resume/` 查看中英文 DOCX、文字履历及依据报告。已有演示目录可用 `--output 新目录` 重新生成。

若干不同背景的完整履历、简历、依据报告和个人网页可在[文档站的示例页](docs/examples.md)在线查看，源文件提交在 `examples/professions/`，全部为虚构教学数据；这些示例不是职业名单或能力限制。示例网页由 `tools/build_site.py` 从这些源数据重建，不提交 PDF、DOCX 或生成 HTML。

[能力与交付](docs/reference/capabilities.md) · [面试准备](docs/guide/prepare-interview.md) · [工具命令](docs/reference/commands.md) · [调用方式](docs/guide/using-skill.md) · [Git 统计](docs/guide/git-timeline.md) · [网页生成](docs/guide/generate-webpage.md)

## 打包到 SkillHub

使用运行包上传，完整源码工程留作维护：

```sh
pnpm package
# 终端会询问本次版本号，例如 1.1.0；留空取消
# 不使用 pnpm 时：python3 -B tools/release.py --skillhub
```

版本由你每次输入，不自动递增；自动化可用 `pnpm package --version 1.1.0`。成功后才更新被 Git 忽略的本地 `VERSION`，产物放在 `local/dist/skillhub/输入版本/`，已有目录不覆盖。生成的 ZIP 最多 200 个文件、解压后最多 10 MiB，保留日常功能和教程。命令会显示文件数及剩余额度，同目录的 `PACKAGE-INFO.json` 可复核实际统计。只上传 ZIP，源码、报告和校验和不要重新压到包里。详细范围见[发布与文件上限](docs/maintainers/releasing.md)。

## 资料保存与维护

架构分工见[架构与扩展](docs/reference/directories.md#运行流程与扩展)。公共模板保持空白，示例明确标注虚构；个人材料集中在 `local/`，不提交到公开仓库。忽略规则不能清除已跟踪文件或历史。升级前备份完整 `local/`；结构化私人 ZIP 不包含全部原始附件与简历产物。

Release / 市场 ZIP 只携带运行资源与用户教程，不含 `VERSION`、`.gitignore`、仓库维护配置和测试。首次初始化会生成工作副本的忽略规则；版本见下载文件名或市场记录。诊断、演示、安装和校验均可直接在解压目录运行。

运行 `python3 scripts/career.py doctor --smoke` 可在临时空白副本自检核心工具，不读取当前私人正文。错误恢复与常见误用统一见[排错说明](docs/guide/troubleshooting.md)。

需要开发教程站或维护公共工具时，先获取完整源码，再运行：

```sh
python3 tools/check.py
pnpm install --frozen-lockfile
pnpm docs:build
```

文档站另需 Node.js 24.x 与项目锁定的 pnpm；日常使用无需启动站点。工具测试不代替附件解析、模型行为或 Word / PDF 排版验收。

[隐私与备份](docs/guide/privacy.md) · [贡献指南](.github/CONTRIBUTING.md) · [安全报告](.github/SECURITY.md) · [发布说明](docs/maintainers/releasing.md)

通用代码与模板采用 MIT，个人资料和第三方材料不因此获得公开授权。
