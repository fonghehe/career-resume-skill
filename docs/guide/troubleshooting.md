# 常见问题

先运行 `python3 scripts/doctor.py` 查看公共资源与 Python / Git 状态；文档环境另用 `--docs`。该命令只检查环境，不会安装软件或读取个人档案正文。报告工具问题时可附脱敏的诊断输出。公共分发的完整自检是 `python3 scripts/check.py`，需要 Git，所有演示和测试产物都在临时目录。

## 安装后找不到技能

先用 `install_skill.py --dry-run` 检查目标位置；已有安装会报路径占用，这是保留已有文件的预期行为。Codex / Claude Code 检查是否选择了用户安装或当前项目安装，Trae 检查技能开关，WorkBuddy 检查是否上传并启用 ZIP。刷新或重新打开客户端后仍未发现时，可让它直接读取完整工作副本的 `SKILL.md`。其他宿主先确认本地目录、ZIP 或文件读取能力，再选入口。具体操作见[多智能体使用](using-skill.md)。

## 在别的目录执行脚本，却读到旧的资料

脚本默认使用自身所在的 Skill 根路径，不依据终端 cwd 自动切换资料。请运行私人工作副本里的脚本，或使用对应脚本支持的根目录参数；不要从共享安装路径调用默认读写个人资料的工具。创建新的完整空副本使用 `init_profile.py --workspace`，而不是只建立一个空 data 目录。

## 找不到 Python 或版本过低

先运行 `python3 --version`，确保版本至少 3.9。Windows 可能使用 `python` 或 `py -3`，后续采用对应命令。不要为了运行脚本安装与本项目无关的 Python 包。

## 缺少 profile、facts 或 timeline.json

在项目根目录执行 `python3 scripts/init_profile.py`。它从公共空模板补缺失文件；重复运行不会覆盖已有档案。不要手动把整个空模板目录覆盖到个人资料上。

## 智能体没有读取上传的简历

先确认客户端支持该附件类型及本地目录访问。提供可读文本、原文件路径或经过检查的提取结果。没有实际读取的来源标待补充；脚本本身不能解析 Word / PDF。

## Missing Markdown project card / Missing timeline project card

检查 `local/data/timeline.json` 的项目 ID，以及 `local/references/projects/` 中卡片第一行。例如 ID `P01` 对应 `# P01｜项目名称`，不是文件名匹配。确保同一 ID 唯一，项目索引链接了该卡片。

## Non-factual project must not be in the active timeline

展示数据只接收 `confirmed` 或 `resume-supported` 项目。待确认方案、假设和明确排除经历保留在事实库的相应区域，不通过改状态绕过检查。虚构材料只用于专门的教学夹具。

## needs both dates or neither / start is after end

起止必须成对并按先后排序。未知项目日期可都设为空字符串；进行中项目填写整理截止日期并标记 `ongoing: true`。只有月份时，先确认展示约定再使用完整日期。

仓库活动摘要必须有两端日期与正整数计数。Git 原时区保留，不能把 Author Date 与 Committer Date 混成一种日期。

## Timeline HTML is stale / project detail is stale

你已经修改 JSON 或 Markdown，但网页还是旧版本。先完成源数据修正，再执行：

```sh
python3 scripts/build_timeline.py
python3 scripts/validate.py
```

校验发现冲突时以最新确认的事实记录为准，不能反过来从生成 HTML 覆盖知识库。

## 文字履历仍是旧内容

`output/career/career.md` 是聚合文件。先把更正保存到对应档案 / 项目卡，再运行 `python3 scripts/build_career.py`。工具不从简历或网页反向推导事实。

若报“Refusing to replace a file that is not a generated career artifact”，说明目标是手写文件或生成标识缺失。保留该文件，在 `local/output/career/` 中使用新的 `--output` 路径生成；不要删除手写经历来绕过检查。

## 更新工具撤回了 JSON，文字却没有恢复

`update_profile.py --undo` 只针对展示 JSON，不能撤回单独修改的 Markdown 与原始附件。完整恢复需要相应源记录备份，然后重新聚合文字履历和所需网页。详见[履历维护](update-career.md)。

## 示例目录已存在

`create_demo.py` 故意拒绝覆盖已有演示目录。换一个新的 `--output local/output/demo-next`，或直接查看已经生成的示例；不要删除自己的项目卡来让演示运行。

## Git 采集没有记录

检查作者完整邮箱、本地 refs、仓库是否浅克隆和是否已有提交。没有匹配时 `repository` 是 `null`，不加入虚假摘要。采集不会联网同步远端，也不能自动判断不同邮箱是否属于你。

## 公开索引检查失败

阅读报错列出的路径。个人文件用 `git rm --cached -- <文件路径>` 移出索引并保留本地文件；新公共文件加入 `scripts/bundle.py` 清单。若模板误填个人信息，先把资料保存到私人路径，再恢复公共空模板。

检查的是索引版本，工作区修改但未重新暂存时，检查结果可能仍针对旧暂存内容。

## 文档依赖安装或构建失败

检查 Node.js 22+、pnpm 11 和网络是否能访问包仓库。运行 `pnpm install --frozen-lockfile`；不要先修改锁文件。项目通过 `pnpm-workspace.yaml` 指定 esbuild 构建脚本，避免每位使用者手工设置。

文档站打不开时看终端的实际地址和端口。`docs:preview` 需要先执行 `docs:build`。个人 HTML 生成独立于 Node / VitePress，仍可单独运行 Python 工具。

部署在子路径时资源 404，按[维护文档站](../maintainers/documentation.md)配置 `DOCS_BASE` 后重新构建。

## 要报告问题

提供命令、版本、脱敏报错和虚构复现材料。不要上传真实简历、个人采集报告或企业代码。格式问题可用[虚构示例](../example.md)复现。
