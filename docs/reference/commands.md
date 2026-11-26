# 本地工具与命令

Release / 市场包保留日常工具，省略源码测试、发布和文档构建环境；维护命令单列于文末。下面的 Python 命令在工作副本根目录执行，个人数据与产物默认读写 `local/`，只需要 Python 标准库；采集 Git 另需系统 Git。脚本不是常驻后端，事实提取与追问由智能体完成。

日常命令统一通过 `scripts/career.py` 执行。该入口默认使用脚本所属完整副本，可用命令前的 `--workspace /实际完整副本` 选择资料库：

```sh
python3 scripts/career.py init
python3 scripts/career.py init --new /新的完整私人副本
python3 scripts/career.py build --web
python3 scripts/career.py web
python3 scripts/career.py validate
python3 scripts/career.py workbench --demo
python3 scripts/career.py export "实际版本/resume.en.md" --format all
python3 scripts/career.py doctor --smoke
```

`build --web` 复用已维护的展示摘要，不从自然语言自动推断摘要；要先让智能体同步。`export` 中相对文件路径按所选副本解析。全部参数见 `python3 scripts/career.py --help` 和对应子命令的 `--help`。

| 命令 | 输入与结果 | 关键边界 |
|---|---|---|
| `python3 scripts/career.py doctor` | 公共资源与运行环境 → 诊断 | 不读取个人正文；`--docs` 仅检查完整源码的文档环境 |
| `python3 scripts/career.py workbench` | 当前资料库 → 本地编辑工作台，浏览器自动打开 | `--workspace` 选完整副本，`--demo` 用临时虚构资料，Ctrl+C 结束 |
| `python3 scripts/career.py doctor --smoke` | 临时空白运行副本 → 初始化、聚合、网页、演示与校验 | 不读取当前私人正文或覆盖已有产物；运行包可直接使用，不需 Git / Node |
| `python3 scripts/career.py init --new ../my-career` | 公共资源 → 完整空资料副本 | 目标目录须不存在，源安装的个人资料不复制 |
| `python3 scripts/career.py init` | 空模板 → 本地资料文件 | 只补缺失文件，不覆盖已填资料 |
| `python3 scripts/career.py demo` | 虚构夹具 → `local/output/demo/` | 不读个人资料，已存在目录拒绝覆盖 |
| `python3 scripts/career.py build` | 已维护的 Markdown → `local/output/career/career.md` | 聚合文字履历，不解析附件或代写简历；不需要展示 JSON 或 Git |
| `python3 scripts/career.py export 正文.md` | 简历正文 → 同名 DOCX；`--output` 可选新路径，`--theme` 选中文主题色 | 单栏模板，校验 DOCX 和文本顺序，已有文件保留 |
| `python3 scripts/career.py export resume.en.md` | 英文正文 → 黑白 ATS 友好 DOCX；`--page a4` 切换 A4（默认 US Letter） | 国际版忽略主题色；标准版默认 A4，行为不变 |
| `python3 scripts/career.py export 正文.md --format all` | Markdown → 同名 DOCX 与 PDF；`--format pdf` 只保留 PDF | 本机 LibreOffice；已有 DOCX 可加 `--format pdf` 直接转换；见[导出教程](../guide/export-resume.md) |
| `python3 scripts/career.py versions compare 旧目录 新目录` | 两份同语言正文与依据报告 → 正文差异和事实 ID 增减 | 英文加 `--language en`，相对目录按所选工作副本解析 |
| `python3 scripts/career.py versions impact --fact E01-T P01-A` | 已有依据报告 → 匹配事实 ID 的版本与主张 | 只读，缺少或无法解析的映射需人工核对 |
| `python3 scripts/career.py web` | 个人 JSON、项目卡 → `local/showcase/project-timeline.html` | 更新生成 HTML，不修改来源；内嵌完整项目卡 |
| `python3 scripts/career.py validate` | 本地资料 → 结构、链接、来源与网页一致性检查 | 不能核实职业事实 |
| `python3 scripts/career.py git …` | 本地仓库、本人邮箱 → 私人 JSON | 不 fetch、不改仓库，映射待本人确认 |
| `python3 scripts/career.py git --folder … --author-email …` | 项目文件夹 → 多仓库报告与逐提交事件 | 递归读取本地仓库，跳过依赖目录和目录链接；同名仓库以相对路径区分 |
| `python3 scripts/career.py update --delta …` | 增量资料 → 合并预览 | 默认不写入；`--apply` 保存，确认字段冲突需本人处理 |
| `python3 scripts/career.py share --project P01` | 已选项目 → 离线分享 HTML | 默认隐藏来源、仓库标识和提交明细，不自动发布 |
| `python3 scripts/career.py package` | 询问版本 → `local/dist/career-resume-skill-输入版本.zip` | 运行包白名单与空模板；自动化加 `--version X.Y.Z`；不含仓库维护文件或 Git 历史 |
| `python3 scripts/career.py package --include-personal` | 选定资料 → `local/dist/career-resume-skill-personal.zip` | 敏感结构化备份；不含 private 附件、output 简历，不是完整目录备份 |

`scripts/career_resume/bundle.py` 是内部文件清单模块，`scripts/career_resume/career_data.py` 提供共享统计与路径校验，一般不单独执行。完整的增量更新、撤回和分享约定保存在 `references/enhancements.md`，由智能体按需读取。源码中的 `tests/` 用于验证导出、初始化、Git 活动与虚构示例的关键行为，不随运行包分发。

## 安装到智能体

```sh
# 无须预先注册智能体名称
python3 scripts/career.py install --skills-dir /实际客户端的技能父目录
python3 scripts/career.py install --output local/dist/career-resume-skill-import.zip
# 支持项目 .agents/skills/ 的宿主
python3 scripts/career.py install --project /实际路径/my-career
# 查看内置快捷入口，它们不是接入范围上限
python3 scripts/career.py install --list-agents
```

输入为公共白名单，输出为完整技能目录或 ZIP；私人档案始终来自空模板。`--dry-run` 只预览；ZIP 导出询问本次完整版本号，自动化加 `--version X.Y.Z`，不改源码 VERSION；已有目标拒绝覆盖。`--agent codex|claude|claude-code|trae|workbuddy` 保留常见快捷方式；其他名称搭配 `--skills-dir` 或 `--output` 同样可用，不猜未注册客户端的默认路径。原有 `--agent workbuddy` 默认 ZIP 路径保持兼容。

生态批量安装先通过 `career.py package --runtime --public-dir` 导出运行空副本，再交给 `npx skills add` 选择多个宿主；第三方安装器另需 Node.js/npm 与网络。具体用法见[多智能体安装](../guide/using-skill.md)。

## 常用可选参数

```sh
python3 scripts/career.py demo --output local/output/demo-another
python3 scripts/career.py web --output local/output/my-timeline.html
python3 scripts/career.py --workspace /你的路径/另一份完整资料目录 validate
python3 scripts/career.py git --repo /你的路径/仓库 --author-email you@example.test --project-id P01 --output local/output/git-activity/P01-first.json
python3 scripts/career.py package --public-dir /你的路径/新的公开目录
python3 scripts/career.py package --output local/dist/public-next.zip
python3 scripts/career.py export local/output/resumes/2026-11-14-方向/resume.en.md --layout international
python3 scripts/career.py export local/output/resumes/2026-11-14-方向/resume.en.md --layout international --page a4
python3 scripts/career.py export local/output/resumes/2026-11-14-方向/resume.zh-CN.md --theme sky --output local/output/resumes/2026-11-14-方向/resume-sky.docx
```

演示目录、Git 采集文件与公开导出目录必须是新路径。ZIP 已存在时默认拒绝，只有明确要覆盖对应包才使用 `--overwrite`。`career.py web` 默认更新生成 HTML。

## 文字履历与简历

```sh
python3 scripts/career.py build
python3 scripts/career.py --workspace /你的路径/完整私人资料副本 build
python3 scripts/career.py build --output local/output/career/another.md
```

文字履历读取入口、个人档案、事实、项目索引、来源索引、待确认问题和当前项目卡，也递归收录 `local/references/career/` 下的 Markdown 技术案例、教育与能力记录，保留事实状态与原始日期精度。输出只允许放在该资料库的 `output/` 中；默认可以重建已有生成文件，拒绝覆盖手写文件或源记录。正文中的相对链接转换到输出位置。工具不读取旧简历产物，不把展示 JSON 的完整日期当作精确任职日期。

先让智能体整理源记录，再运行聚合；空模板聚合只能证明工具可运行，不算真实履历完成。生成简历由智能体读取最新事实、选材和写作，目前没有自动理解 JD 或代写简历的 Python 命令。正文与依据报告交付见[生成简历](../guide/generate-resume.md)。

## 源码维护命令

以下命令只在[完整源码工程](https://github.com/fonghehe/career-resume-skill)中提供，运行包用户无需执行：

| 命令 | 作用与条件 |
|---|---|
| `python3 tools/check.py` | 临时公共源码导出 → 完整测试、演示与校验；另需 Git。`--local` 会读取个人资料，只按需使用 |
| `python3 tools/check_public_index.py` | 检查实际 Git 索引路径与空白 JSON starter，不识别所有手写个人信息 |
| `pnpm package` / `python3 tools/release.py --skillhub` | 每次询问完整版本号，生成 SkillHub ZIP、校验和与预算报告；成功后才更新 Git 忽略的本地 VERSION |
| `pnpm package --version 1.1.0` | 显式指定版本的自动化入口；不询问、不上传，已有产物不覆盖 |
| `pnpm package:runtime` | 询问版本后生成通用运行 ZIP；`pnpm package:source /新目录` 导出完整源码目录，不询问版本 |
| `python3 scripts/career.py package --public-dir /新目录` | 从源码导出完整公共工程；从运行包导出时保持运行布局 |
| `python3 scripts/career.py package --runtime --public-dir /新目录` | 显式导出精简运行目录，适合交给生态安装器 |
| `python3 tools/build_site.py --output /临时目录` | 五个职业的公共虚构源 → 个人网页、履历 / 简历阅读页、画廊与履历时间线。只读取 `examples/professions/`，不读取 `local/`；产物不提交 |

### 文档站命令

```sh
pnpm install --frozen-lockfile
pnpm docs:dev
pnpm docs:build
pnpm docs:preview
```

`pnpm docs:demo` 只重新生成公开虚构网页，不构建整站：原有的 `docs/public/demo/timeline.html`，以及由 `build_site.py` 生成的 `docs/public/demo/professions/`（五个职业的个人网页、履历 / 简历阅读页、画廊与履历时间线）。两者都从 `examples/` 的虚构夹具重建，被 Git 忽略，不读取 `local/`。`docs:dev` 与 `docs:build` 已包含它。

### 提交与回归检查（源码）

```sh
python3 -B tools/check.py
pnpm docs:build
# 仅明确暂存本次修改的公共文件后检查
python3 -B tools/check_public_index.py
git diff --cached --check
git diff --cached --stat
```

测试使用临时资料和临时仓库，不把虚构人物混入你的事实库。读完暂存差异再自行提交；[隐私说明](../guide/privacy.md)解释忽略规则的范围。
