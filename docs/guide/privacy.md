# 个人资料怎样保存，公共代码怎样提交

每个人 Clone 后运行初始化脚本，在自己的本地副本生成档案。公共仓库提交规则、工具、空模板和虚构示例；本地个人资料持续保留。

## 目录边界

| 目录或文件 | 默认处理 |
|---|---|
| `assets/starter/` | 提交空模板；不能填个人信息 |
| `SKILL.md`、`scripts/`、`docs/` | 提交通用规则、工具和教程 |
| `assets/examples/` | 提交明确标注的虚构材料 |
| `references/` | 提交公共 Skill 规则；不填个人经历 |
| `local/` | 个人事实、来源、附件、网页、采集报告和备份统一存放，忽略 |
| 旧 `data/`、`showcase/`、`output/`、`private/`、`dist/` | 保留兼容忽略；新产物使用 `local/` |
| `node_modules/`、文档缓存和构建目录 | 本地产物，忽略 |
| `docs/public/demo/` | 构建时从虚构夹具生成，忽略 |
| 虚拟环境、测试缓存、日志、编辑器和智能体本地配置 | 忽略 |

PDF / Word 等附件以及 `.env` 也被忽略。纯文本简历应放在私人目录；放进公共教程的文字不会因为叫“简历”而自动排除。

## 提交前实际检查

修改通用代码或教程后，在项目根目录执行：

```sh
git status --short
git add .
python3 scripts/check_public_index.py
git diff --cached --stat
git diff --cached
```

索引检查读取真正将被提交的内容，阻止非公共路径和含个人数据的 JSON 模板。它不能检测公共 Markdown 或代码中所有手写个人信息，所以仍要阅读暂存差异。

确认只包含公共改动后，再自行提交：

```sh
git commit -m "docs: explain career knowledge base workflow"
```

不要用 `git add -f` 强制提交被忽略的档案。新增公开文件时，需要同步 `scripts/bundle.py` 的公共清单，否则提交检查会拒绝该路径。

## 已经跟踪过的资料

`.gitignore` 只阻止之后自动加入，不能移除已跟踪文件和旧历史。对于尚未提交或仅需移出当前索引的单个文件，可以使用：

```sh
git rm --cached -- references/profile.md
```

此命令保留本地文件；已经进入历史的内容仍在历史中。如果曾公开推送个人信息，需要单独处理公开历史和相关副本，不能把新增忽略规则当作完成清除。

## 公开导出与私人备份

```sh
python3 scripts/package.py
python3 scripts/package.py --include-personal
```

第一个默认生成空模板公开包；第二个生成私人备份。二者文件名不同，私人包不能上传作为 Release。

私人包只包含脚本选定目录中的 Markdown、JSON 和 HTML；不包含 `local/private/` 原始附件、`local/output/` 生成简历及任意新增文件。升级前还需单独备份这些目录，不能将结构化 ZIP 当成完整目录备份。

需要全新的公开目录时：

```sh
python3 scripts/package.py --public-dir /你的路径/新的公开目录
```

目标必须不存在。导出使用明确清单，不复制 Git 历史，也不删除当前个人数据。

## 文档站不会自动发布个人网页

VitePress 的 Markdown 来源固定为 `docs/`。示例构建读取 `assets/examples/career-demo/`，不读取你根目录下的个人时间线和项目卡。

个人 HTML 内嵌完整数据与项目卡原文；要公开作品集，先另做内容审查和公开副本。教程站没有自动部署配置，运行 `docs:build` 只在本地构建。

忽略与导出解决的是 Git / 发布文件边界。宿主智能体对附件和模型请求的处理由其设置决定。
