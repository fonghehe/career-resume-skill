# 提交公共代码与发布

## 日常提交

Clone 后运行 `python3 scripts/init_profile.py`，本地资料从 `assets/starter/` 生成。公共代码和空模板受 Git 管理；个人档案、来源、项目、时间线、上传附件与生成产物被 `.gitignore` 排除。

```sh
python3 scripts/check.py
git add .
python3 scripts/check_public_index.py
git diff --cached --stat
git commit -m "feat: initialize career experience knowledge base"
```

检查失败先修复再提交。索引检查读取暂存内容而非仅检查工作文件，拒绝公共清单外的路径，以及被填入个人档案 / 活动记录的 JSON starter。它不能识别手写进公共 README、代码或截图中的所有个人信息，所以仍需查看实际 diff。不要用 `git add -f` 强制加入私人文件。

如果私人文件已经被跟踪或暂存，需按实际文件执行 `git rm --cached -- 文件路径`，目录使用 `git rm -r --cached -- 目录路径`；这些命令只取消跟踪，不删除本地资料。已经提交的历史需要单独处理，修改忽略规则不会清除历史。不要把整个 references 目录盲目取消跟踪：`references/career-workflow.md` 是公共规则。

配置自己的远程仓库后再推送；本地 Python 工具不自动提交或上传，版本标签会触发下方的草稿发布工作流。公开模板改动保留在 `assets/starter/`，自己的履历继续留在根目录的忽略文件中。

## 导出与复核

需要独立副本或 Release 时：

```sh
python3 scripts/package.py --public-dir /tmp/career-resume-skill-public
python3 scripts/validate.py /tmp/career-resume-skill-public
```

目标目录必须不存在，目录导出拒绝覆盖。ZIP 默认输出 `local/dist/career-resume-skill-public.zip`，使用受控公共文件清单，以 starter 替换资料和时间线，不复制 `.git`。导出中的空资料文件同样被忽略，首次提交只跟踪 starter，使用者 clone 后本地初始化。

默认不会复制真实项目卡、原始来源快照、确认记录、企业证据、旧投递示例、个人时间线 HTML、output、Git 历史以及个人专用说明 / 校验器。公共文件新增时同步 `scripts/bundle.py` 清单。

检查所有导出文件：个人资料和记录应为空，示例明确标为虚构；公共许可使用项目贡献者署名。分别检查历史、截图、附件及 Release 包。运行结构和测试不代表经历真实、ATS 或智能体客户端行为已验证。

## 个人备份与维护

个人资料保留在本地；运行 `python3 scripts/package.py --include-personal` 显式生成私人结构化备份，不能上传到公开 Release。该包不包含 private 原始附件、output 简历或全部自定义文件，这些另行备份。重复初始化不会覆盖已有档案；具体迁移见[上手指南](../guide/first-library.md)。原作者专用说明和校验器保持忽略，不进入公开文件清单。

## 发布设置

由维护者选择仓库地址和公开信息，启用 Actions、Issues 与私密漏洞报告；只发布公共 ZIP。建议为默认分支配置 PR 检查，将版本标签写入权限限制给维护者。确认兼容性后再声明实测客户端，不以 CI 通过代替[行为验收](behavior-testing.md)。不要将原简历、内部仓库代码或联系人资料上传到 Issue / PR。

当前目录若是无 Git 元数据的导出副本，先在独立公开目录建立仓库，再配置远程。初始化时只提交 `scripts/bundle.py` 的公共清单；不要把原私人仓库的历史直接作为首次开源历史。

## 版本与本地产物

`VERSION` 是发布版本的唯一来源，格式为 `MAJOR.MINOR.PATCH`，不带 v。Git 标签为 `v` 加相同值。数据格式如有不兼容变化，应提供迁移步骤，避免覆盖既有私人资料。

```sh
python3 scripts/check.py
pnpm install --frozen-lockfile
pnpm docs:build
python3 scripts/release.py
```

以当前 `0.1.0` 为例，产物是 `local/dist/releases/0.1.0/career-resume-skill-0.1.0.zip` 与同目录 `SHA256SUMS`。ZIP 顶层为 `career-resume-skill/`，包含 VERSION 和空档案，无 Git 历史和私人记录。`release.py` 会校验导出结构，但不会自动执行整个测试套件，所以上方检查仍是发布前提。重复目录拒绝覆盖，另指定 `--output-dir local/dist/releases/0.1.0-review` 可以重新复核。

解压到新目录，运行 `doctor.py`、`validate.py` 和虚构演示。下载者可在产物目录运行跨平台校验：

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

确认公共提交和 VERSION 后，由维护者自行执行（当前版本示例）：

```sh
git tag -a v0.1.0 -m "career-resume-skill 0.1.0"
git push origin v0.1.0
```

**推送标签会触发 `.github/workflows/release.yml`。** 工作流检查标签与 VERSION 一致、实际 Git 索引、干净公开导出和全部回归测试，再构建文档和公开发布 ZIP。验证任务仅有读取权限；独立草稿任务下载产物后用写权限创建 draft，不自动发布或部署网页。草稿复核附件、说明和隐私边界后，维护者在 GitHub 点击 Publish release。

草稿创建使用 [GitHub CLI 的 `gh release create --verify-tag --draft`](https://cli.github.com/manual/gh_release_create)。构建失败先修复并以新版本发布；若草稿步骤失败但构建通过，可从 Actions 下载 `public-release` 产物，按 [GitHub 的产物下载说明](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts) 取出 ZIP 与校验和再手动建立草稿。已有同标签 Release 时先核对状态，不覆盖或删除已经公开的版本。

本地只能验证工具和配置；首次云端工作流、仓库权限、下载地址及各客户端行为，须在真正的托管仓库中验收后记录。

## 分发给更多智能体

发布同一个完整公开 Skill 包，保持 `SKILL.md` 名称与相对资源路径稳定，不为每个宿主复制一套履历流程。当前根目录入口可被 skills CLI 的根目录发现机制读取；本地先从白名单导出空副本再交给安装器，不能让安装器复制带私人材料的源工作区。操作见[多智能体教程](../guide/using-skill.md)。

托管仓库或 Release 公开后，再以实际地址验证远程安装。新增客户端优先通过生态安装器、通用目录、ZIP 或短入口接入；仅在路径与平台契约经过核对后增加快捷方式。测试记录应区分“可安装”“可发现”“可运行”和附件/文档能力，不把客户端名称加入快捷列表当成实测通过。
