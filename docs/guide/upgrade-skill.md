# 更新旧版本并保留个人资料

更新有两处：客户端安装的 Skill，以及你日常维护履历的完整工作副本。只更新客户端入口，不会更新另一目录中的规则和脚本。先确认实际入口与资料目录，再选择下面的方式。

新版初始化不再预建服务端能力表、技术难点候选、独立排除表和重复的简历写作规则。通用事实、能力边界、更正与排除记在 `local/references/facts.md`，待核实事项记在 `questions-to-confirm.md`，写作规则以公共流程为准。旧工作区已有的记录和个人偏好继续保留，不自动搬运或删除。

新版目录将运行实现收拢到 `scripts/career_resume/`，源码维护工具放入 `tools/`，虚构示例独立到 `examples/`。日常只调用 `scripts/career.py` 子命令，例如旧 `scripts/init_profile.py` 改用 `scripts/career.py init`，旧 `scripts/export_resume.py` 改用 `scripts/career.py export`。已有 `local/` 的路径和资料格式保持原样。

## 更新前确认

1. 关闭旧版工作台，保存未完成草稿。记下实际 Skill 路径、工作副本路径和已安装版本；本地打包记录看可选的 `VERSION`，源码发布版看 Git 标签，运行包看 ZIP 文件名 / 市场版本记录。
2. 给旧完整副本做一次私人备份，至少包含整个 `local/`：来源、附件、事实、展示数据、历史、简历和自定义写作偏好都在其中。不要用公开导出包替代私人备份。
3. 获取需要的新版完整源码或运行包，解压到新目录。不要只下载 `SKILL.md`，也不要先删除旧目录。

更新不会自动取得维护者尚未发布的工作区改动；以你实际取得的完整包为准。

## 日常工作副本：推荐在新目录更新

适用于已使用 `local/` 布局的旧版。新目录必须是刚取得的完整新版，尚无个人资料。将旧 `local/` 整体复制过去，旧记录优先于新版的空模板；原目录保留以便回退。下面路径都要换成自己的实际路径：

```sh
python3 - <<'PY'
from pathlib import Path
import shutil

previous = Path('/实际路径/旧工作副本/local')
updated = Path('/实际路径/新版完整副本/local')
if not previous.is_dir() or not (updated.parent / 'SKILL.md').is_file():
    raise SystemExit('检查旧 local/ 与新版完整目录；不要在不明确的路径执行复制。')
# 只对刚解压且没有个人资料的新版执行；不覆盖另一个人的资料。
shutil.copytree(previous, updated, dirs_exist_ok=True, symlinks=True)
PY
python3 /实际路径/新版完整副本/scripts/career.py init
python3 /实际路径/新版完整副本/scripts/career.py doctor --smoke
python3 /实际路径/新版完整副本/scripts/career.py build
python3 /实际路径/新版完整副本/scripts/career.py validate
```

复制保留旧来源、事实 ID、字段状态、排除项、偏好和已有简历；初始化仅补缺项，不把空模板覆盖回旧资料。符号链接按原样保留，不跟随复制到其他目录；若工具因链接或旧格式报错，保留旧副本，按具体报错修复，不删除资料绕过检查。个人偏好与新版公共流程冲突时，按本轮要求核对后逐项调整，不把旧偏好全部重置。

需要网页时再从源记录同步展示并重建网页。最后让智能体列出实际使用的新入口与新脚本路径，打开文字履历，确认任职 / 项目数量、来源和旧简历仍在。确认新副本可用后再切换日常入口；旧副本和备份可继续保留。

很早的版本可能把个人记录放在根目录 `references/`、`data/`、`output/`。这类目录同时混有公共规则，**不要整体覆盖新版根目录**。保留旧完整副本，让智能体先识别旧履历入口和来源，再把私人记录迁入新副本 `local/`，逐项校验路径与 ID；未经识别不要套用上面的 `local/` 复制命令。

## 客户端目录安装：替换入口副本

本项目 `career.py install` 拒绝覆盖已有安装。重复安装后看到 `Destination already exists` 表示旧文件受到保护，不表示已经更新。

先用新版脚本 `--dry-run` 看实际目标。将旧的 `career-resume-skill/` 移到技能扫描目录之外的私人备份位置，再运行新版安装命令。不要把旧目录改个名字留在同一技能扫描目录中，以免客户端同时发现两份入口。

```sh
python3 /实际路径/新版完整副本/scripts/career.py install --skills-dir /实际客户端技能目录 --dry-run
# 在文件管理器把旧技能目录移到扫描目录之外，保留其中可能存在的 local/。
python3 /实际路径/新版完整副本/scripts/career.py install --skills-dir /实际客户端技能目录
```

安装只写新版公共资源和空模板，不能迁移旧个人经历。旧安装中若有真实资料，先按上一节转入新的私人工作副本，再切换。重新载入 / 启用客户端技能，明确指定新的完整工作副本；不要继续调用旧目录脚本。

## ZIP 或市场安装

在原市场支持的版本更新入口选择新版本；手动 ZIP 导入则从新版完整副本生成新的公开包，再按宿主界面替换旧技能：

```sh
python3 /实际路径/新版完整副本/scripts/career.py install --output /实际路径/career-resume-skill-new.zip
```

具体更新按钮随宿主而异，本项目不假设统一命令。若宿主没有替换功能，先备份并移出旧入口，再导入完整新版 ZIP；私人履历不放进公开 ZIP。市场 / ZIP 更新后，个人工作副本仍需单独更新。

## Git 源码副本

先 `git status --short` 检查公共代码是否有本地修改。工作树干净、已备份 `local/` 且远端正确时，可在该源码副本 `git pull --ff-only`，再初始化补缺项、自检、重建文字履历并校验。有改动或无法快进时先保留工作，不使用 reset / clean；可以采用上面的新目录更新方式。

旧名 `resume-skill` 的资料可以保留原目录名；新版技能名称使用 `career-resume-skill`。切换成功以实际新入口、脚本和文件核验为准，不以安装命令没有报错或技能列表名称相同为准。
