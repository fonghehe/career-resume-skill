# 多智能体安装与调用

同一份 `career-resume-skill` 按 Agent Skills 格式提供入口、规则、模板和工具。根据智能体的接入能力选择安装方式，新增客户端无需重写履历流程。Codex、Claude Code、WorkBuddy 和 Trae 是下文的示例，接入范围不以这些名称为限。

## 先准备个人工作副本

下载或 clone 完整项目。自己的副本可以直接使用；若拿到的是共享或只读安装，用下面的命令创建新副本：

```sh
python3 /实际安装路径/career-resume-skill/scripts/init_profile.py --workspace /实际路径/my-career
```

目标目录必须不存在；命令只复制公共内容与空模板。以后在智能体中打开 `/实际路径/my-career`，资料写入它的 `local/`。所有脚本也从该副本运行，因为脚本默认读写自身所在目录，单独切换终端 cwd 不会切换资料库。

下文 Python 安装命令在完整项目目录执行，使用 Python 3.9+ 标准库；Windows 可把 `python3` 换成 `py -3`。生态安装器另需 Node.js/npm 与网络，基础文件读取和 Python 安装不需要它。Skill 本身不要求 API Key 或 MCP 服务。

## 按智能体能力选择入口

| 接入能力 | 使用方式 | 新客户端怎么接入 |
|---|---|---|
| 生态安装器已支持 | 从干净公开副本运行 `npx skills add`，选择一个或多个智能体 | 使用安装器维护的客户端列表与路径 |
| 支持项目 `.agents/skills/` | `install_skill.py --project 工作副本` | 确认客户端支持并启用目录发现 |
| 支持其他本地技能目录 | `install_skill.py --skills-dir 技能父目录` | 指定客户端实际目录，不需要注册客户端名称 |
| 支持 ZIP 导入 | `install_skill.py --output 新的.zip` | 在客户端导入；核对包结构与平台元信息要求 |
| 能读取文件但无原生 Skill | 明确读取工作副本的 `SKILL.md` | 用项目规则、快捷指令或会话提示指向同一入口 |
| 自建 / 云端智能体 | 将公开包放入可访问的沙箱或资源服务 | 按元信息发现、按需读取规则与资源，见[集成说明](../reference/compatibility.md#自建与云端智能体) |

格式一致不代表所有客户端都扫描同一目录，也不代表它们都有文件写入、Python、附件解析或文档导出能力。[Agent Skills 规范](https://agentskills.io/specification)描述可复用格式，具体发现与执行由宿主实现。

### 生态安装器：一次选择多个智能体

先导出空白公开副本，再交给安装器；不直接从含真实履历的工作副本安装。

```sh
python3 scripts/package.py --public-dir local/dist/ecosystem/career-resume-skill
npx skills add ./local/dist/ecosystem/career-resume-skill --skill career-resume-skill --copy
```

第二条命令交互选择目标智能体；可以选择多个。`--copy` 使用独立安装副本，公开导出不会连到私人资料。导出目录必须不存在，升级时换新路径。安装到项目时，第二条命令应在目标工作副本目录执行，源路径换成导出的绝对路径；加 `--global` 可按安装器支持情况选择用户安装。

[skills CLI 的维护者说明](https://github.com/vercel-labs/skills)列出了 Cursor、OpenCode、GitHub Copilot、Gemini CLI、Cline、Windsurf、Kiro、OpenClaw 等客户端，并提供多目标选择。实际支持列表与路径会更新，以安装器当前帮助和客户端说明为准。本项目不复制整份第三方客户端注册表，也未将外部安装器的支持列表当成自己的实测声明。

对已确定的客户端可以传多个 `--agent` 参数；这些名称由生态安装器定义，与本项目快捷名称可能不同。安装器是可选工具，不能运行时使用下列 Python 入口。

### 通用目录：不限制智能体名称

```sh
python3 scripts/install_skill.py --skills-dir /实际客户端的技能目录
```

脚本会创建 `技能目录/career-resume-skill/`，保留完整资源，只复制公共内容。无需 `--agent`；即使客户端刚发布或尚未被安装器收录，也可以按其正式说明接入。不要猜目录位置。

支持 `.agents/skills/` 的项目宿主可用：

```sh
python3 scripts/install_skill.py --project /实际路径/my-career
```

该命令创建项目的 `.agents/skills/career-resume-skill/`；`--agent universal` 是相同的快捷方式。它不假设存在对所有宿主通用的全局技能目录。

### 通用 ZIP

```sh
python3 scripts/install_skill.py --output local/dist/career-resume-skill-import.zip
```

压缩包只有一个 `career-resume-skill/` 顶层目录，下面包含 `SKILL.md` 及完整资源。适合接收该结构的客户端；要求 ZIP 根层直接放 `SKILL.md` 或额外平台字段时，应按目标官方说明重新组织公开副本，而不是只上传入口、漏掉模板与工具。平台市场上架和云端资源挂载需另行配置。

## 常见客户端示例

| 客户端 | 推荐安装方式 | 如何引用 |
|---|---|---|
| Codex 本地客户端 | `--agent codex`，或加 `--project` 限定工作副本 | 在技能列表选择；CLI / IDE 可输入 `$career-resume-skill` |
| Claude Code | `--agent claude`，或加 `--project` | `/career-resume-skill` |
| WorkBuddy | `--agent workbuddy` 生成 ZIP，在技能页上传 | 选择已安装技能，或明确说使用 `career-resume-skill` |
| Trae / TraeCode | `--agent trae --project 工作副本` | 在技能面板启用，再明确说使用 `career-resume-skill` |

这些是根据官方说明适配的安装入口；本项目验证了通用目录、ZIP、已知快捷目录和包内容，尚未逐一实测各客户端的发现、模型行为与附件处理。原生发现不可用时，可用本页末尾的文件读取入口。

### Codex

跨项目使用，安装到 `~/.agents/skills/career-resume-skill/`：

```sh
python3 scripts/install_skill.py --agent codex
```

只在自己的履历工作副本中使用：

```sh
python3 scripts/install_skill.py --agent codex --project /实际路径/my-career
```

项目入口位于 `.agents/skills/career-resume-skill/SKILL.md`。打开工作副本，在 Skill 列表选择技能；CLI / IDE 可用 `/skills` 或 `$career-resume-skill`。未显示时刷新或重启客户端。发现位置与调用方式见 [OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills)。

```text
使用 $career-resume-skill。
个人工作副本是 /实际路径/my-career，请读取该副本的 SKILL.md 和已有资料。
所有履历读写和脚本执行都以该副本为准，先生成完整文字履历。
我的经历是：【口述经历或材料路径】。
```

### Claude Code

跨项目入口在 `~/.claude/skills/career-resume-skill/`：

```sh
python3 scripts/install_skill.py --agent claude
```

仅当前工作副本使用时，加 `--project /实际路径/my-career`，会安装到该目录的 `.claude/skills/`。然后在 Claude Code 中打开工作副本并调用：

```text
/career-resume-skill 个人工作副本是 /实际路径/my-career。请读取该副本的 SKILL.md，以它为准读写资料和执行脚本。先整理完整履历，我的经历是：【材料】。
```

本地目录安装面向 Claude Code。[官方说明](https://code.claude.com/docs/en/skills)也区分了 Claude Code、Cowork 与云端会话；后两者不会直接读取你机器上的 `~/.claude/skills/`，需按它们的账号技能入口导入，不应套用本地命令。

### WorkBuddy

生成可上传的公开包：

```sh
python3 scripts/install_skill.py --agent workbuddy
```

默认产物是 `local/dist/career-resume-skill-workbuddy.zip`，也可用 `--output /实际路径/import.zip` 指定新文件。打开 WorkBuddy 的技能页，选择“添加技能 → 上传技能”，导入 ZIP 并启用。操作依据见 [WorkBuddy 官方技能说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。界面入口以当前版本为准。

创建任务时选择自己的工作副本，并发送：

```text
请使用 career-resume-skill。
本次个人工作副本是 /实际路径/my-career，请读取它的 SKILL.md。
以该副本为准读写资料和执行脚本，先检查已有档案，再整理本次经历：【材料】。
```

ZIP 中有完整公共资源和空模板，不包含你的真实履历。这是本地导入包，尚未提交到技能市场；市场上架涉及额外元信息与平台审核，需另行处理。本教程不假设 WorkBuddy 会扫描某个未确认的磁盘目录。

### Trae / TraeCode

推荐项目安装，避免不同地区版本的全局路径差异：

```sh
python3 scripts/install_skill.py --agent trae --project /实际路径/my-career
```

入口在工作副本的 `.trae/skills/career-resume-skill/SKILL.md`。打开该副本，前往“设置 → 技能与命令”，检查技能已启用，再发送与 WorkBuddy 相同的自然语言提示词。也可以在界面导入包含完整资源的 ZIP。

若已经为 Codex 安装了项目 `.agents/skills/`，支持该功能的 TraeCode 可以在导入设置中开启“启用 .agents 技能目录”，复用同一目录，无需再装一份。存在同名 `.trae/skills/` 技能时，Trae 优先读取后者。目录、开关与自然语言调用见 [Trae 官方说明](https://docs.trae.cn/ide_skills)。

全局安装可显式指定客户端显示的技能目录，例如国内版的 `~/.trae-cn/skills/`：

```sh
python3 scripts/install_skill.py --agent trae --skills-dir ~/.trae-cn/skills
```

## 安装、预览与升级

安装命令只导出白名单公共文件，私人记录替换为空模板，不复制 Git 历史、原始附件或生成简历。默认拒绝覆盖已有安装或 ZIP，也拒绝向符号链接路径写入。安装副本与个人工作副本可以分别维护。

先看目标位置，再执行安装：

```sh
python3 scripts/install_skill.py --agent codex --project /实际路径/my-career --dry-run
```

`--skills-dir` 指定的是父目录，脚本会自动追加 `career-resume-skill/`。同一客户端避免重复安装同名技能。升级前备份个人工作副本的 `local/`，检查旧安装中是否有自己的改动；保留旧安装或移走后再安装新版本。脚本不自动删除、合并或迁移既有资料。

旧名安装升级后使用 `career-resume-skill`；已有个人工作副本继续使用，不需要重建经历。

## 通用文件读取入口

能读写文件的智能体也可以直接读取入口，不必原生安装。可将 `assets/templates/agent-entry-template.md` 中的短入口加入宿主项目规则或快捷指令，填好路径后重复引用；完整规则不用复制。也可以在会话中发送：

```text
请读取 /实际路径/my-career/SKILL.md，以该目录作为个人工作副本。
先检查 local/ 中的已有资料，再根据我本次提供的材料继续整理履历。
```

只支持聊天的宿主，可接收入口规则、模板和实际文本，并在对话中交付文字，由你保存；它不能声称已读本地文件、运行脚本或完成落盘。

## 检查是否生效

让智能体列出实际读取的 Skill 路径、个人工作副本、来源与写入文件。打开 `local/output/career/career.md` 和 `local/references/career/README.md`，确认经历与材料一致。不要只看“已完成”的回复。

然后发送“根据最新履历生成前端方向的通用简历，交付正文和独立依据报告”，确认产物在工作副本的 `local/output/resumes/`。不能读取的附件需提供可读文字，不猜测内容。

下一步：[生成第一份履历](first-library.md) · [根据履历生成简历](generate-resume.md) · [兼容与验收边界](../reference/compatibility.md)。
