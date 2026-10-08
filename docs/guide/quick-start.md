# 快速开始

你只需要一份可读写的完整工作副本和自己的经历材料。日常整理用 Python 3.9+；不需要启动文档站或先安装 Node.js，也不要求提供旧简历、JD 或代码仓库。

想回头整理多年的项目经历，可以先做前两步，再按[项目回顾教程](review-career.md)梳理具体工作与职责变化。简历在需要时生成，不必为了开始整理就先确定岗位。

## 1. 打开工作副本

如果这是你自己的 clone，直接用这个目录，个人资料放 `local/`。用智能体打开项目，然后发：

```text
请读取当前项目的 SKILL.md。
先检查是否已有个人履历，复用现有资料；缺少的空档案按需初始化。
本次个人资料和产物都保存在当前副本的 local/ 中。
```

智能体负责必要的初始化。想手动操作时，在工作副本根目录执行：

```sh
python3 scripts/doctor.py
python3 scripts/init_profile.py
```

初始化只补缺少文件，重复运行保留已有资料。`local/README.md` 是工作区说明；初始化完成不等于已经生成个人履历。

如果使用共享或只读安装，先创建**不存在的新路径**：

```sh
python3 /实际安装路径/scripts/init_profile.py --workspace /实际路径/my-career
```

随后打开 `my-career/`，读取其中的 `SKILL.md`，使用其中的工具。它是完整空白副本，不复制安装位置的个人材料。工具默认依据脚本所在目录选择资料库，不靠终端 cwd 切换。

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

提供岗位 JD 可生成定向版本。结果在 `local/output/resumes/YYYY-MM-DD-方向/`，正文为 `resume.zh-CN.md` 或 `resume.en.md`，报告为 `match-report.md`。详细标准见[根据履历生成简历](generate-resume.md)。

## 以后怎样用

- 想起一个项目细节：直接讲述，见[补充与更正履历](update-career.md)。
- 想看公司、项目与代码统计：按需[生成网页](generate-webpage.md)与[导入 Git](git-timeline.md)。
- 想确认文件放哪里：看[目录说明](../reference/directories.md)。
- 想先看效果：打开[完整虚构示例](../example.md)，或运行 `python3 scripts/create_demo.py` 查看本地网页演示。

Windows 可将 `python3` 换成实际可用的 `python` 或 `py -3`。宿主需要文件读写权限；只聊天时可以整理文本，但要由你手动保存。调用方式见[调用 Skill](using-skill.md)。
