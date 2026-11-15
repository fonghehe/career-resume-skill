# 提交公共代码与发布

## 日常提交

Clone 后运行 `python3 scripts/career.py init`，本地资料从 `assets/starter/` 生成。公共代码和空模板受 Git 管理；个人档案、来源、项目、时间线、上传附件与生成产物被 `.gitignore` 排除。

```sh
python3 tools/check.py
# 只明确暂存本次修改的公共文件
git add -- 本次修改的公共文件路径
python3 tools/check_public_index.py
git diff --cached --stat
git commit -m "feat: initialize career experience knowledge base"
```

检查失败先修复再提交。索引检查读取暂存内容而非仅检查工作文件，拒绝公共清单外的路径，以及被填入个人档案 / 活动记录的 JSON starter。它不能识别手写进公共 README、代码或截图中的所有个人信息，所以仍需查看实际 diff。不要用 `git add -f` 强制加入私人文件。

如果私人文件已经被跟踪或暂存，需按实际文件执行 `git rm --cached -- 文件路径`，目录使用 `git rm -r --cached -- 目录路径`；这些命令只取消跟踪，不删除本地资料。已经提交的历史需要单独处理，修改忽略规则不会清除历史。不要把整个 references 目录盲目取消跟踪：`references/career-workflow.md` 是公共规则。

配置自己的远程仓库后再推送；本地 Python 工具不自动提交或上传，版本标签会触发下方的草稿发布工作流。公开模板改动保留在 `assets/starter/`，自己的履历继续留在根目录的忽略文件中。

## 导出与复核

需要独立副本或 Release 时：

```sh
python3 scripts/career.py package --public-dir /tmp/career-resume-skill-public
python3 scripts/career.py --workspace /tmp/career-resume-skill-public validate
```

目标目录必须不存在，目录导出拒绝覆盖。公开 ZIP 每次询问版本号，默认输出 `local/dist/career-resume-skill-输入版本.zip`，使用独立的运行资源白名单，以 starter 替换资料和时间线。`--public-dir` 从源码导出完整公共工程，供维护与测试；加 `--runtime` 只导出可安装的运行目录。从已安装运行包导出时始终保留运行布局。二者都不复制 Git 历史或私人资料。

默认不会复制真实项目卡、原始来源快照、确认记录、企业证据、旧投递示例、个人时间线 HTML、output、Git 历史以及个人专用说明 / 校验器。公共文件新增时同步 `scripts/career_resume/bundle.py` 清单。

检查所有导出文件：个人资料和记录应为空，示例明确标为虚构；公共许可使用项目贡献者署名。分别检查历史、截图、附件及 Release 包。运行结构和测试不代表经历真实、ATS 或智能体客户端行为已验证。

## 个人备份与维护

个人资料保留在本地；运行 `python3 scripts/career.py package --include-personal` 显式生成私人结构化备份，不能上传到公开 Release。该包不包含 private 原始附件、output 简历或全部自定义文件，这些另行备份。重复初始化不会覆盖已有档案；具体迁移见[上手指南](../guide/first-library.md)。旧版原作者专用说明和校验器不再由公共工具加载或打包，遗留路径继续保持忽略。

## 发布设置

由维护者选择仓库地址和公开信息，启用 Actions、Issues 与私密漏洞报告；只发布公共 ZIP。建议为默认分支配置 PR 检查，将版本标签写入权限限制给维护者。确认兼容性后再声明实测客户端，不以 CI 通过代替[行为验收](behavior-testing.md)。不要将原简历、内部仓库代码或联系人资料上传到 Issue / PR。

当前目录若是无 Git 元数据的导出副本，先在独立公开目录建立仓库，再配置远程。初始化时只提交 `scripts/career_resume/bundle.py` 的公共清单；不要把原私人仓库的历史直接作为首次开源历史。

## 版本与本地产物

可选的本地 `VERSION` 记录最近一次成功打包的发布版本，格式为 `MAJOR.MINOR.PATCH`，不带 v。它被 Git 忽略，不进入公共源码或运行包；新 clone 没有此文件也可正常校验和打包。每次打包由使用者输入完整版本号，工具不猜测该升级哪一位，也不自动递增。修复问题改最后一位；兼容的新功能改中间一位；不兼容变更改第一位，改动前一位后后面的位归零。

推荐使用：

```sh
pnpm package
# 显示当前版本，然后询问：请输入本次打包版本号（例如 1.1.0；留空取消）
```

该命令生成 SkillHub 包，默认放入 `local/dist/skillhub/输入版本/`。通用运行包使用 `pnpm package:runtime`，同样每次询问，默认放入 `local/dist/releases/输入版本/`。不使用 Node / pnpm 时，可以直接运行 `python3 -B tools/release.py --skillhub` 或 `python3 -B tools/release.py`。

只有成功生成 ZIP、校验和及预算报告后，才原子创建或写回本地 `VERSION`。留空、Ctrl+C、输入结束、格式错误、缺少资源、目标目录已存在或写入失败时，既有版本和产物保留。重复打包同一版本需显式选新的 `--output-dir`，不会覆盖已有包。

自动化流程必须显式传入完整版本号，例如：

```sh
pnpm package --version 1.1.0
python3 -B tools/release.py --version 1.1.0
```

显式传入 `--version` 代表本次版本已经确定，因此不再询问。标签发布 CI 从已验证的 Git 标签提取版本；普通回归 CI 使用明确的虚构测试版本 `0.0.0`，不上传；不提供版本且没有可读输入时立即报错。旧 `--bump` 参数已移除，避免自动替使用者决定版本级别。工具不提交、打标签、推送或上传。创建 Git 标签前先核对本次选择的版本及打包结果，标签为 `v` 加该版本；本地 `VERSION` 不提交。

打包前验证：

```sh
python3 -B tools/check.py
pnpm install --frozen-lockfile
pnpm docs:build
pnpm package
```

以输入 `1.1.0` 后生成的通用运行包为例，产物是 `local/dist/releases/1.1.0/career-resume-skill-1.1.0.zip` 与同目录 `SHA256SUMS`、`PACKAGE-INFO.json`。ZIP 顶层为 `career-resume-skill/`，不携带 `VERSION` 文件。包内保留日常运行脚本、规则、模板、最小虚构演示和六份操作指南；空档案在使用时从 starter 创建；不含 `.gitignore`、`AGENTS.md`、`.github/`、`tests/`、维护脚本、维护文档和 Node / VitePress 构建配置。`examples/professions/` 与 `tools/build_site.py` 只服务于源码仓库和文档站，不进入运行包，以保留 SkillHub 的文件数预算。根 README 使用精简运行说明。

运行包将源码 `LICENSE` 原文导出为 `LICENSE.md`，将 `assets/starter/gitignore.template` 原文导出为 `assets/starter/gitignore.txt`；不再携带无扩展名许可或 `.template` 文件。只有使用者运行 `career.py init` 或创建私人工作副本时才生成 `.gitignore`，不覆盖已有规则。运行包里的 `career.py doctor` / `career.py validate` 按运行资源清单检查，不再要求源码维护文件。

按 [SkillHub 当前官方网页上传器](https://skillhub.cn/tutorials)的要求，上传内容最多 200 个文件、合计不超过 10 MiB，不能依赖会被跳过的二进制附件。运行包仅使用本项目所需的 `.md`、`.txt`、`.py`、`.json`、`.yaml` / `.yml` 文本资源；打包前检查扩展名、文件数量和总大小。源码中的虚构 PNG 阶段示意图在运行包改用 `demo-phases.md` 文字附件，示例数据与演示脚本同步切换，避免上传器过滤图片后演示失效。源码与文档站继续使用原图片演示。

### 200 文件上限与该上传哪一份

上限统计的是 **ZIP 内解压后的文件数量**，不是把整个工程压成一个 ZIP 就算一个文件。本项目保留两种导出用途：

| 用途 | 生成方式 | 是否用于 SkillHub 上传 |
|---|---|---|
| 完整公共源码 | `career.py package --public-dir /新目录` | 否；含测试、构建环境和五职业教学源，可能超过 200 文件 |
| 日常运行 Skill | `career.py package` 或 `release.py` | 控制在 200 文件 / 10 MiB 内；通用包不一定有市场元数据 |
| SkillHub 运行 Skill | `release.py --skillhub` | 是；只在包内补齐市场元数据 |

功能工具、职业规则、空模板、工作台和日常教程保留；测试、CI、文档站构建环境、五职业整套教学源和生成网页留在源码仓库与在线文档。不要通过删除脚本依赖或个人证据来凑文件数，也不要上传整个工作副本。

打包器在生成前、内容转换后及 ZIP 写完后检查预算。最后一层直接统计实际 ZIP 中的文件条目，目录不计入文件数；超过 200 文件或 10 MiB 会在发布产物前报错。命令输出实际文件数、总大小和剩余额度。

每次 `release.py` 额外生成同目录的 `PACKAGE-INFO.json`，记录实际文件数、剩余额度、ZIP 大小、解压后总字节数、版本与 SHA256。该报告和 `SHA256SUMS` 都在 ZIP 外，不占 200 个名额；**上传时仅选择版本 ZIP，不要把三份文件再次压缩成一个包**。

官方发布入口另要求 `slug`、`displayName`、SemVer `version`，见[官方发布说明](https://skillhub.cn/ai/release.md)。2026-11-15 核对的[官方网页上传器](https://cloudcache.tencent-cloud.com/qcloud/tea/app/skillhub/assets/skill-hub.dc3cj3ht.js?max_age=31536000)中，文件数上限为 200，总字节数上限为 10485760；图片、Office 文档等二进制资源会被过滤。导出的 DOCX / PDF 属于使用者的本地产物，不作为 Skill 安装资源上传。

SkillHub 默认使用交互式打包：

```sh
pnpm package
# 不使用 pnpm 也可直接运行，仍会询问版本号
python3 -B tools/release.py --skillhub
```

已确定版本的自动化调用使用 `pnpm package --version 1.1.0`。目标目录必须不存在；复核同版本包时可加 `--output-dir local/dist/skillhub/1.1.0-review`。

`--skillhub` 按[官方发布说明](https://skillhub.cn/ai/release.md)，仅在包内 `SKILL.md` 追加 `slug`、`displayName`、本次选择的 `version` 和 `license: MIT`，保留通用名称、描述和正文。源码入口保持通用格式。网页上传时版本信息须与包内一致。脚本不会登录或上传；本地结构检查不代表市场审核通过。

普通 `career.py package` 和 `career.py install --output` 导出 ZIP 也询问版本，可显式传入 `--version` 供自动化使用；这两种导出只将版本写入包内，不改源码 `VERSION`。`package --public-dir` 是源码 / 运行目录导出，`package --include-personal` 是私人备份，都不属于版本发布，不询问或接受发布版本号。`install --dry-run` 只预览，不询问版本。

`release.py` 校验导出结构，但不自动执行整个测试套件，所以上方检查仍是发布前提。`check.py` 在临时公共工程中运行回归，包含真正解压 Release 后执行诊断、校验、演示、独立工作副本、重新安装和重新打包，以及缺失演示资源的失败检查。重复目录拒绝覆盖，另指定 `--output-dir local/dist/releases/1.0.1-review` 可以重新复核。

解压到新目录，运行 `python3 scripts/career.py doctor --smoke`，可在临时空白副本自检核心工具，不读取已有私人正文。`INFO` 提醒尚需初始化等事项，失败则按 `ERROR`、`NEXT` 和本地 `HELP` 路径处理；具体范围统一见[排错说明](../guide/troubleshooting.md)。下载者可在产物目录运行跨平台校验：

```sh
python3 - <<'PY'
import hashlib
from pathlib import Path
for line in Path('SHA256SUMS').read_text().splitlines():
    expected, filename = line.split()
    actual = hashlib.sha256(Path(filename).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit('Checksum mismatch: ' + filename)
    print('OK:', filename)
PY
```

这是 macOS / Linux 的 heredoc 写法，Windows 可将内部 Python 保存为脚本执行。校验和检验下载内容完整性，不证明作者身份；从项目自己的发布页面获取。

## GitHub 草稿 Release

确认公共提交和本次发布版本后，由维护者自行执行（版本示例）：

```sh
git tag -a v1.0.1 -m "career-resume-skill 1.0.1"
git push origin v1.0.1
```

**推送标签会触发 `.github/workflows/release.yml`。** 工作流校验标签中的完整版本号、实际 Git 索引、干净公开导出和全部回归测试，再构建文档和公开发布 ZIP。验证任务仅有读取权限；独立草稿任务下载产物后用写权限创建 draft，不自动发布或部署网页。草稿复核附件、说明和隐私边界后，维护者在 GitHub 点击 Publish release。

草稿创建使用 [GitHub CLI 的 `gh release create --verify-tag --draft`](https://cli.github.com/manual/gh_release_create)。构建失败先修复并以新版本发布；若草稿步骤失败但构建通过，可从 Actions 下载 `public-release` 产物，按 [GitHub 的产物下载说明](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts) 取出 ZIP 与校验和再手动建立草稿。已有同标签 Release 时先核对状态，不覆盖或删除已经公开的版本。

本地只能验证工具和配置；首次云端工作流、仓库权限、下载地址及各客户端行为，须在真正的托管仓库中验收后记录。

## 分发给更多智能体

发布同一个完整运行 Skill 包，保持 `SKILL.md` 名称与相对资源路径稳定，不为每个宿主复制一套履历流程。当前根目录入口可被 skills CLI 的根目录发现机制读取；本地先用 `career.py package --runtime --public-dir` 从白名单导出空副本再交给安装器，不能让安装器复制带私人材料的源工作区。操作见[多智能体教程](../guide/using-skill.md)。

托管仓库或 Release 公开后，再以实际地址验证远程安装。新增客户端优先通过生态安装器、通用目录、ZIP 或短入口接入；仅在路径与平台契约经过核对后增加快捷方式。测试记录应区分“可安装”“可发现”“可运行”和附件/文档能力，不把客户端名称加入快捷列表当成实测通过。

运行包不重复携带 `local/` 空档案；首次运行 `career.py init` 或工作台时从 `assets/starter/` 创建。已有资料照常保留，部分缺失的资料仍由校验发现。可选教程链接指向文档站，操作必需的六份指南继续离线可用。
