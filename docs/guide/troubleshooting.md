# 常见问题

先运行 `python3 scripts/career.py doctor --smoke` 检查资源并自检核心工具。它只在临时空白副本中写入，不读取当前私人正文或覆盖已有产物。准备保存经历时，再用 `python3 scripts/career.py init` 补缺项；检查自己的资料使用 `python3 scripts/career.py validate`。

## 一键自检

`career.py doctor --smoke` 可在源码和已解压的运行包使用，不需要 Node.js 或 Git。它从公共规则与空模板创建临时运行副本，依次执行初始化、结构校验、文字履历聚合、空时间线与虚构演示生成，再校验结果；退出后清理临时副本。正常完成会显示 `Runtime self-check passed` 和实际执行的子命令。

不带 `--smoke` 只做资源及环境诊断。`INFO` 表示可选工具不可用或尚需初始化，例如缺少 `.gitignore`；`ERROR` 表示资源或操作失败。自检通过只说明这条空资料工具链可运行，不能证明个人事实、宿主发现、模型写作或 Word / PDF 排版已验收。

## 统一错误输出

所有日常 Python 工具（包括履历 / 网页生成、Git 采集、展示更新和分享导出）操作失败时，保留可搜索的原始错误，并给出恢复动作与本地帮助位置：

```text
ERROR: Output already exists: /example/existing.zip
CODE: 1004
NEXT: 选择不存在的新目标路径；保留已有安装、演示或导出包。
HELP: /example/career-resume-skill/docs/guide/troubleshooting.md
```

上述命令的操作或输入校验失败返回 `1`；命令行解析器识别的语法错误（如未知选项、互斥选项）返回 `2`。不要只看最后一句提示；先定位 `ERROR` 中的文件和原因，再按 `NEXT` 处理。坏编码应明确报文件位置，保留原件后提供 UTF-8 文字副本。

`CODE` 是独立于进程退出码的稳定诊断编号；可用于搜索或自动分类。多条校验错误按一次失败汇总，仍需逐条阅读 `ERROR`。

| CODE | 含义 | 恢复动作 |
|---|---|---|
| `1000` | 其他输入 / 操作错误，或多类校验错误 | 按原始原因检查输入 |
| `1001` | 文件权限不足 | 检查权限或创建可写副本 |
| `1002` | 文本编码不可读 | 保留原件，提供 UTF-8 文字副本 |
| `1003` | 符号链接被拒绝 | 改用真实路径 |
| `1004` | 目标已存在或被占用 | 选择新目标，保留原文件 |
| `1005` | 必需公共资源缺失 | 重新取得完整包 |
| `1006` | 私人资料模板缺失 | 在对应副本初始化补缺项 |
| `1007` | Git 读取超时 | 缩小采集范围，单独检查该仓库后重试 |

Git 普通读取每条命令限时 60 秒；README / 代码片段的读取与等待共用 30 秒期限，片段还限制字节数。单仓库超时返回失败且不写报告；文件夹采集将该仓库列入 `skipped`（含 `errorCode`），保留其余成功项，结果是部分报告。完整 Git 日志仍会读入内存，这些期限不代表任意规模仓库都已通过压力测试。

## 先按报错定位

| 现象 / 报错 | 处理入口 |
|---|---|
| `Missing or invalid release file` / `Missing required file` | [运行包缺文件](#运行包缺文件)；若只缺 `local/` 档案则[初始化补缺项](#缺少-profile、facts-或-timeline-json) |
| `Destination already exists` / `Output already exists` | [安装路径](#安装后找不到技能)或[已有示例](#示例目录已存在)，改用新目标路径 |
| `Refusing a symlink` | 使用没有符号链接的真实源目录和目标路径，保留原目录 |
| 缺少 profile / facts / timeline | 见“缺少 profile、facts 或 timeline.json” |
| 资料写到了旧目录 | [工作副本选择](#在别的目录执行脚本-却读到旧的资料) |
| 项目卡、日期或生成内容过期 | 见下方对应英文报错与重建步骤 |
| 附件读不到 / 没有 Word 或 PDF 工具 | 见“智能体没有读取上传的简历”；提供可读文字，先交付 Markdown |

## 运行包缺文件

Release / 市场 ZIP 只携带日常运行资源，主动省略 `VERSION`、`.gitignore`、`AGENTS.md`、测试、CI、维护脚本与文档站构建配置。这些文件缺少是预期行为；版本见 ZIP 文件名或市场版本记录。`career.py doctor` 和 `career.py validate` 会按运行包检查必要脚本、空模板及完整虚构演示资源。

若诊断报缺少模板、示例附件或运行脚本，先备份 `local/`，重新下载完整 ZIP 并解压到新目录，再自检；不要靠创建同名空文件绕过检查。安装导出也必须使用完整运行包，不能只复制 `SKILL.md`。

运行包用 `career.py doctor --smoke` 自检。`check.py`、`check_public_index.py`、`release.py` 和 `pnpm docs:*` 用于维护源码，需从[源码仓库](https://github.com/fonghehe/career-resume-skill)获取完整工程，详情见[源码维护命令](../reference/commands.md#源码维护命令)。`career.py doctor --docs` 同样只适用于源码工程。

## 常见误用

| 容易出错的做法 | 正确处理 |
|---|---|
| 把整个私人工作目录当作公开包上传 | 用受控公共导出，只上传生成的公开 ZIP；私人备份不用于发布 |
| 用同名空文件补齐缺失依赖 | 重新取得完整包，在新目录自检，保留原有 `local/` |
| 删除已有安装或资料来绕过路径占用 | 改用新目标；升级前备份并检查旧目录中的个人改动 |
| 修改生成的履历或 HTML，忽略源记录 | 更正源档案与项目卡，再重建相应产物 |
| 把 Git 日期、提交量或团队结果写成本人任职与业绩 | 只采用来源支持的字段，未知保留待确认状态 |
| 把空模板或工具测试通过当作真实履历完成 | 检查实际文字产物及事实来源；模型行为和排版另行验收 |

## 安装后找不到技能

先用 `career.py install --dry-run` 检查目标位置；已有安装会报路径占用，这是保留已有文件的预期行为。Codex / Claude Code 检查是否选择了用户安装或当前项目安装，Trae 检查技能开关，WorkBuddy 检查是否上传并启用 ZIP。刷新或重新打开客户端后仍未发现时，可让它直接读取完整工作副本的 `SKILL.md`。其他宿主先确认本地目录、ZIP 或文件读取能力，再选入口。具体操作见[多智能体使用](using-skill.md)。

## 在别的目录执行脚本，却读到旧的资料

脚本默认使用自身所在的 Skill 根路径，不依据终端 cwd 自动切换资料。请运行私人工作副本里的脚本，或使用对应脚本支持的根目录参数；不要从共享安装路径调用默认读写个人资料的工具。创建新的完整空副本使用 `career.py init --new`，而不是只建立一个空 data 目录。

## 找不到 Python 或版本过低

先运行 `python3 --version`，确保版本至少 3.9。Windows 可能使用 `python` 或 `py -3`，后续采用对应命令。不要为了运行脚本安装与本项目无关的 Python 包。

## 缺少 profile、facts 或 timeline.json

在项目根目录执行 `python3 scripts/career.py init`。它从公共空模板补缺失文件；重复运行不会覆盖已有档案。不要手动把整个空模板目录覆盖到个人资料上。

## 智能体没有读取上传的简历

先确认客户端支持该附件类型及本地目录访问。提供可读文本、原文件路径或经过检查的提取结果。没有实际读取的来源标待补充；脚本本身不能解析 Word / PDF。

## Missing Markdown project card / Missing timeline project card

检查 `local/data/timeline.json` 的项目 ID，以及 `local/references/projects/` 中卡片第一行。例如 ID `P01` 对应 `# P01｜项目名称`，不是文件名匹配。确保同一 ID 唯一，项目索引链接了该卡片。

## Non-factual project must not be in the active timeline

展示数据只接收 `confirmed` 或 `resume-supported` 项目。待确认方案、假设和明确排除经历保留在事实库的相应区域，不通过改状态绕过检查。虚构材料只用于专门的教学夹具。

## needs both dates or neither / start is after end

起止必须成对并按先后排序。未知项目日期可都设为空字符串；进行中项目填写整理截止日期并标记 `ongoing: true`。只有月份时，先确认展示约定再使用完整日期。

仓库活动摘要必须有两端日期与正整数计数。Git 原时区保留，不能把 Author Date 与 Committer Date 混成一种日期。

## 打开个人网页时项目是 0 条

`local/showcase/project-timeline.html` 显示的是你的展示数据。已经导入经历时，请智能体从已有履历同步任职和项目摘要，再重新生成网页。只有初始化空档案时，先[整理第一份履历](first-library.md)。

想先看带项目的虚构演示，运行 `python3 scripts/career.py demo`，再打开 `local/output/demo/showcase/project-timeline.html`。已有默认演示时，重新生成个人页后也可以从空页提示打开它。

## Timeline HTML is stale / project detail is stale

你已经修改 JSON 或 Markdown，但网页还是旧版本。先完成源数据修正，再执行：

```sh
python3 scripts/career.py web
python3 scripts/career.py validate
```

校验发现冲突时以最新确认的事实记录为准，不能反过来从生成 HTML 覆盖知识库。

网页输出必须是 `.html`，会拒绝符号链接及覆盖没有生成标识的手写 HTML。若报 `not a generated timeline artifact`，保留该文件，改用新的输出文件名。履历和网页在同目录临时文件写入完整后才替换旧产物；普通写入或替换失败时保留旧版本，修复权限或磁盘问题后重跑即可。

## 文字履历仍是旧内容

`output/career/career.md` 是聚合文件。先把更正保存到对应档案 / 项目卡，再运行 `python3 scripts/career.py build`。工具不从简历或网页反向推导事实。

若报“Refusing to replace a file that is not a generated career artifact”，说明目标是手写文件或生成标识缺失。保留该文件，在 `local/output/career/` 中使用新的 `--output` 路径生成；不要删除手写经历来绕过检查。

初始化、Git 采集、分享或 ZIP 导出若在新文件写入中失败，会清理仍属于本次写入的未完成文件；已有资料、快照及其他写入者替换的新结果会保留。初始化已经完整创建的缺项会保留，重跑时只补仍缺少的文件。此机制不自动猜测、回滚或恢复事实记录；展示 JSON 的历史撤回仍按下节处理。

## 更新工具撤回了 JSON，文字却没有恢复

`career.py update --undo` 只针对展示 JSON，不能撤回单独修改的 Markdown 与原始附件。完整恢复需要相应源记录备份，然后重新聚合文字履历和所需网页。详见[履历维护](update-career.md)。

## 示例目录已存在

`career.py demo` 故意拒绝覆盖已有演示目录。换一个新的 `--output local/output/demo-next`，或直接查看已经生成的示例；不要删除自己的项目卡来让演示运行。

## Git 采集没有记录

检查作者完整邮箱、本地 refs、仓库是否浅克隆和是否已有提交。没有匹配时 `repository` 是 `null`，不加入虚假摘要。采集不会联网同步远端，也不能自动判断不同邮箱是否属于你。

## 公开索引检查失败（源码）

阅读报错列出的路径。个人文件用 `git rm --cached -- <文件路径>` 移出索引并保留本地文件；新公共文件加入 `scripts/career_resume/bundle.py` 清单。若模板误填个人信息，先把资料保存到私人路径，再恢复公共空模板。

检查的是索引版本，工作区修改但未重新暂存时，检查结果可能仍针对旧暂存内容。

## 文档依赖安装或构建失败（源码）

只有完整源码工程需要 Node.js 24.x 与锁定的 pnpm。安装、端口、子路径和 Pages 部署排错统一见[文档站维护](https://fonghehe.github.io/career-resume-skill/maintainers/documentation.html)，不要为此改动私人资料或随意更新锁文件。运行包可直接阅读 Markdown；个人离线 HTML 独立于文档站构建。

## 要报告问题

提供命令、版本、脱敏报错和虚构复现材料。不要上传真实简历、个人采集报告或企业代码。格式问题可用[虚构示例](../example.md)复现。

## PDF 导出失败或已有 Word 文件

- 提示找不到 LibreOffice：运行 `python3 scripts/career.py doctor` 查看发现结果；安装在自选位置时用 `--converter /实际路径/soffice`。也可只生成 DOCX，在 Word 中另存 PDF。
- 提示文件已存在：已有 Word、尚无 PDF 时，用 `export 实际路径.docx --format pdf`；重建两份文件选择新版本目录或 `--output 新名称.pdf`。
- 转换超时或失败：原稿保留，`all` 模式已生成的 DOCX 路径会在错误中说明。先手动打开该 DOCX 检查，不把失败结果记为完成。
- 英文导出套了中文版式：文件命名为 `resume.en.md`，或显式加 `--layout international`。自动选择依据文件名，不判断语言内容。

完整命令见[导出中英文简历](export-resume.md)。
