# 本地工具与命令

下面的 Python 命令在项目根目录执行，个人数据与产物默认读写 `local/`，只需要 Python 标准库；采集 Git 另需系统 Git。脚本不是常驻后端，事实提取与追问由智能体完成。

| 命令 | 输入与结果 | 关键边界 |
|---|---|---|
| `python3 scripts/doctor.py` | 公共资源与运行环境 → 诊断 | `--docs` 检查可选文档环境，不读取个人档案正文 |
| `python3 scripts/check.py` | 临时公开导出 → 测试、演示与空时间线检查 | 需要 Git；`--local` 附加本地资料、`--index` 附加 Git 索引检查 |
| `python3 scripts/init_profile.py --workspace ../my-career` | 公共资源 → 完整空资料副本 | 目标目录须不存在，源安装的个人资料不复制 |
| `python3 scripts/release.py` | VERSION → 带版本公开 ZIP 与 SHA256SUMS | 本地构建，拒绝已有产物，不上传 |
| `python3 scripts/init_profile.py` | 空模板 → 本地资料文件 | 只补缺失文件，不覆盖已填资料 |
| `python3 scripts/create_demo.py` | 虚构夹具 → `local/output/demo/` | 不读个人资料，已存在目录拒绝覆盖 |
| `python3 scripts/build_career.py` | 已维护的 Markdown → `local/output/career/career.md` | 聚合文字履历，不解析附件或代写简历；不需要展示 JSON 或 Git |
| `python3 scripts/build_timeline.py` | 个人 JSON、项目卡 → `local/showcase/project-timeline.html` | 更新生成 HTML，不修改来源；内嵌完整项目卡 |
| `python3 scripts/validate.py` | 本地资料 → 结构、链接、来源与网页一致性检查 | 不能核实职业事实 |
| `python3 scripts/import_git_activity.py …` | 本地仓库、本人邮箱 → 私人 JSON | 不 fetch、不改仓库，映射待本人确认 |
| `python3 scripts/import_git_activity.py --folder … --author-email …` | 项目文件夹 → 多仓库报告与逐提交事件 | 递归读取本地仓库，跳过依赖目录和目录链接；同名仓库以相对路径区分 |
| `python3 scripts/update_profile.py --delta …` | 增量资料 → 合并预览 | 默认不写入；`--apply` 保存，确认字段冲突需本人处理 |
| `python3 scripts/export_share.py --project P01` | 已选项目 → 离线分享 HTML | 默认隐藏来源、仓库标识和提交明细，不自动发布 |
| `python3 scripts/check_public_index.py` | Git 索引 → 公共路径与 JSON 空模板检查 | 不能识别所有手写个人文字 |
| `python3 scripts/package.py` | 公共清单 → `local/dist/career-resume-skill-public.zip` | 用空模板替换个人档案，不带 Git 历史 |
| `python3 scripts/package.py --include-personal` | 选定资料 → `local/dist/career-resume-skill-personal.zip` | 敏感结构化备份；不含 private 附件、output 简历，不是完整目录备份 |

`scripts/bundle.py` 是内部文件清单模块，`scripts/career_data.py` 提供共享统计与路径校验，一般不单独执行。完整的增量更新、撤回和分享约定保存在 `references/enhancements.md`，由智能体按需读取。`tests/` 用于验证导出、初始化、Git 活动与虚构示例的关键行为。

## 安装到智能体

```sh
# 无须预先注册智能体名称
python3 scripts/install_skill.py --skills-dir /实际客户端的技能父目录
python3 scripts/install_skill.py --output local/dist/career-resume-skill-import.zip
# 支持项目 .agents/skills/ 的宿主
python3 scripts/install_skill.py --project /实际路径/my-career
# 查看内置快捷入口，它们不是接入范围上限
python3 scripts/install_skill.py --list-agents
```

输入为公共白名单，输出为完整技能目录或 ZIP；私人档案始终来自空模板。`--dry-run` 只预览，已有目标拒绝覆盖。`--agent codex|claude|claude-code|trae|workbuddy` 保留常见快捷方式；其他名称搭配 `--skills-dir` 或 `--output` 同样可用，不猜未注册客户端的默认路径。原有 `--agent workbuddy` 默认 ZIP 路径保持兼容。

生态批量安装先通过 `package.py --public-dir` 导出空副本，再交给 `npx skills add` 选择多个宿主；第三方安装器另需 Node.js/npm 与网络。具体用法见[多智能体安装](../guide/using-skill.md)。

## 常用可选参数

```sh
python3 scripts/create_demo.py --output local/output/demo-another
python3 scripts/build_timeline.py --output local/output/my-timeline.html
python3 scripts/validate.py /你的路径/另一份完整资料目录
python3 scripts/import_git_activity.py --repo /你的路径/仓库 --author-email you@example.test --project-id P01 --output local/output/git-activity/P01-first.json
python3 scripts/package.py --public-dir /你的路径/新的公开目录
python3 scripts/package.py --output local/dist/public-next.zip
```

演示目录、Git 采集文件与公开导出目录必须是新路径。ZIP 已存在时默认拒绝，只有明确要覆盖对应包才使用 `--overwrite`。`build_timeline.py` 默认更新生成 HTML。

`validate.py` 的 `--personal` 只服务于原作者旧资料的专用约束，普通 Clone 使用者无需使用。

## 文字履历与简历

```sh
python3 scripts/build_career.py
python3 scripts/build_career.py /你的路径/完整私人资料副本
python3 scripts/build_career.py --output local/output/career/another.md
```

文字履历读取入口、个人档案、事实、项目索引、来源索引、待确认问题和当前项目卡，也递归收录 `local/references/career/` 下的 Markdown 技术案例、教育与能力记录，保留事实状态与原始日期精度。输出只允许放在该资料库的 `output/` 中；默认可以重建已有生成文件，拒绝覆盖手写文件或源记录。正文中的相对链接转换到输出位置。工具不读取旧简历产物，不把展示 JSON 的完整日期当作精确任职日期。

先让智能体整理源记录，再运行聚合；空模板聚合只能证明工具可运行，不算真实履历完成。生成简历由智能体读取最新事实、选材和写作，目前没有自动理解 JD 或代写简历的 Python 命令。正文与依据报告交付见[生成简历](../guide/generate-resume.md)。

## 文档站命令

```sh
pnpm install --frozen-lockfile
pnpm docs:dev
pnpm docs:build
pnpm docs:preview
```

`pnpm docs:demo` 只重新生成公开虚构网页，不构建整站。`docs:dev` 与 `docs:build` 已包含它。

## 提交与回归检查

```sh
python3 scripts/init_profile.py
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
pnpm docs:build
git add .
python3 scripts/check_public_index.py
git diff --cached --stat
```

测试使用临时资料和临时仓库，不把虚构人物混入你的事实库。读完暂存差异再自行提交；[隐私说明](../guide/privacy.md)解释忽略规则的范围。
