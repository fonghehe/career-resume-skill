# 快速开始

适用于不同职业与职业阶段，不需要选择预设职业模板；职业未明确、没有项目或代码资料也能开始。你只需要一份可读写的完整工作副本和自己的经历材料。日常整理用 Python 3.9+；不需要启动文档站或先安装 Node.js，也不要求提供旧简历、JD 或代码仓库。

想回头整理多年的项目经历，可以先做前两步，再按[项目回顾教程](review-career.md)梳理具体工作与职责变化。简历在需要时生成，不必为了开始整理就先确定岗位。

| 你现在想做什么 | 从哪里开始 |
|---|---|
| 先看效果 | [打开带内容的虚构示例](../example.md)，或在工作副本运行 `python3 scripts/career.py demo` |
| 第一次导入或口述经历 | 从下方第 1 步开始 |
| 想在网页里直接维护 | [启动本地工作台](workbench.md) |
| 已导入，想生成网页 | [复制生成网页指令](generate-webpage.md) |
| 已有履历，想求职 | [生成简历、导出 Word 或比较岗位](generate-resume.md) |
| 平时想记录进展 | [按月或季度回顾](review-career.md#按月或季度回顾) |

也可以直接用日常说法，无需记住流程名称：

| 你的请求 | 本轮处理范围 |
|---|---|
| “先记一下，我今天维护了工单筛选页面，以后写简历再用。” | 保存本次来源和工作事实，更新文字履历 |
| “之前写成独立负责不准确，其实是参与，只改这一项。” | 更正对应字段，保留旧来源与其他字段状态 |
| “用已有经历给我一份前端通用简历，暂时没有 JD。” | 复用履历，另存正文和依据报告 |
| “这句话帮我翻成英文就行：参与页面维护。” | 仅翻译指定句子，保留参与程度 |

以上是调用表达示例，不是你的个人经历，也不证明每个客户端都能自动触发。未自动调用时，让智能体读取完整工作副本的 `SKILL.md` 即可。

## 1. 打开工作副本

### 怎么选目录

| 你拿到的目录 | 使用哪个工作副本 |
|---|---|
| 自己的可写下载 / clone 副本，包括已有履历资料的副本 | 直接继续使用当前目录，资料放在它的 `local/`，无需再复制 |
| 共享、只读或全局 Skill 安装目录 | 用下方命令创建一次独立副本，随后一直打开并使用新目录 |

共享安装的创建命令如下，目标必须是不存在的新路径：

```sh
python3 /实际安装路径/scripts/career.py init --new /实际路径/my-career
```

它只复制公共资源与空模板，不迁移安装目录中任何人的个人材料。新副本含完整入口和工具，不是单独的数据目录。

选好后，用智能体打开这个工作副本并发送：

```text
请读取当前项目的 SKILL.md。
先检查是否已有个人履历，复用现有资料；档案或根目录 .gitignore 缺失时先运行初始化。
本次个人资料和产物都保存在当前副本的 local/ 中。
```

智能体负责必要的初始化。想手动操作时，在工作副本根目录执行：

```sh
python3 scripts/career.py doctor --smoke
python3 scripts/career.py init
```

初始化只补缺少文件，重复运行保留已有资料和忽略规则。Release / 市场包不带 `.gitignore`，即使已有空档案，也应先初始化再保存经历。`local/README.md` 是工作区说明；初始化完成不等于已经生成个人履历。

`--smoke` 在临时空白副本验证核心工具，不读取当前私人正文；具体检查范围和错误处理统一见[常见问题](troubleshooting.md)。

以后始终使用这个副本的 `SKILL.md` 和脚本；只改变终端 cwd 不会切换脚本的默认资料库。

## 2. 提供经历，生成履历

旧简历可放 `local/private/resume.pdf`，也可以直接讲述：

```text
我的经历材料是【实际路径或口述内容】。
请先整理完整履历，记录任职、教育、本人项目职责、技能与有依据的成果。
未知先留空，保留来源和确认状态，交付文字履历与可维护的记录。
```

完成后查看 `local/output/career/career.md`。源记录入口是 `local/references/career/README.md`。你不需要编辑 JSON；不能读取的附件改用可读文字。具体材料保存见[生成第一份履历](first-library.md)。

## 3. 根据履历生成简历

```text
请根据当前最新履历生成【方向】的【中文 / 英文】通用简历，目前没有 JD。
交付完整正文和独立的依据报告，保留完整履历和已有简历版本。
```

提供岗位 JD 可生成定向版本。要中英两份正文，明确说「生成中英文简历，各附依据报告」。要文件，在指令里加「同时导出 Word 和 PDF，说明实际排版检查结果」。Word 只需 Python；自动转换 PDF 还需本机 LibreOffice。结果在 `local/output/resumes/YYYY-MM-DD-方向/`，正文为 `resume.zh-CN.md` 或 `resume.en.md`，报告为 `match-report.md`。英文版用黑白国际版式，见[英文简历与海外投递](english-resume.md)。详细标准见[根据履历生成简历](generate-resume.md)。

## 4. 添加和维护新经历

直接说：“补充【经历】，只更正【字段】，保留其他事实与来源。”智能体先更新源记录，再重建文字履历。可以用 `python3 scripts/career.py workbench` 在本地网页中编辑，或按[补充与更正](update-career.md)使用自然语言。

## 5. 生成个人网页或导出文件

```text
请把最新履历做成适合【我的职业】的离线个人网页。
先核对展示范围，选择适合的任职、案例、教育或资格模块；不用填满所有栏目。
```

网页在 `local/showcase/project-timeline.html`，双击即可打开。[网页教程](generate-webpage.md)说明如何更新展示摘要；[导出教程](export-resume.md)说明中英文 Word / PDF 的命令和排版检查。生成网页不包含上传或部署。

已有正文时可直接运行：

```sh
python3 scripts/career.py export "local/output/resumes/实际版本/resume.zh-CN.md" --format all
python3 scripts/career.py export "local/output/resumes/实际版本/resume.en.md" --format all
```

## 以后怎样用

- 想起一个项目细节：直接讲述，见[补充与更正履历](update-career.md)。
- 想看公司、项目与代码统计：按需[生成网页](generate-webpage.md)与[导入 Git](git-timeline.md)。
- 想确认文件放哪里：看[目录说明](../reference/directories.md)。
- 想先看效果：打开[完整虚构示例](../example.md)，或运行 `python3 scripts/career.py demo` 生成离线网页和中英文 Word 示例。

Windows 可将 `python3` 换成实际可用的 `python` 或 `py -3`。宿主需要文件读写权限；只聊天时可以整理文本，但要由你手动保存。调用方式见[调用 Skill](using-skill.md)，旧版本升级见[更新到新版本](upgrade-skill.md)。
