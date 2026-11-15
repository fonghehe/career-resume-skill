# career-resume-skill

通用职业履历 Skill：添加和维护完整履历、生成个人网页、生成并导出中英文简历。无需选择职业模板，也不要求有项目或代码经历。

这是可独立运行的 Skill 包，入口为 `SKILL.md`。解压后用智能体打开本目录，提供口述经历或旧简历即可开始；个人材料与产物保存在首次初始化后创建的 `local/`，安装包不重复携带一套空档案。

先在解压目录自检（Python 3.9+，仅需标准库）：

```sh
python3 scripts/career.py doctor --smoke
```

自检只操作临时空白副本，不读取当前私人正文。准备保存经历时运行 `python3 scripts/career.py init`，只补缺项并生成 `.gitignore`；已有资料不覆盖。共享或只读安装使用 `python3 scripts/career.py init --new /新的私人目录`，随后打开新目录并使用其中的脚本。检查自己的资料使用 `python3 scripts/career.py validate`。

运行 `python3 scripts/career.py demo`，在 `local/output/demo/showcase/project-timeline.html` 看任职和项目，在 `local/output/demo/resume/` 看中英文 DOCX 与依据报告。已有演示目录可用 `--output 新目录`。不同背景的虚构履历、简历和个人网页在[在线示例](https://fonghehe.github.io/career-resume-skill/examples)中展示，仅用于说明流程，不限制适用职业。源数据在源码仓库的 `examples/professions/`。

可用 `python3 scripts/career.py install --skills-dir /宿主技能父目录` 安装到其他客户端，或用 `--output /新的导入包.zip` 导出 ZIP。每次导出公开 ZIP 会询问完整版本号；无人值守调用需显式加 `--version X.Y.Z`，留空或无输入会取消。现有目标保留，不能覆盖安装。

包内保留快速开始、网页、工作台、导出、排错与数据格式六份直接操作指南；详细教程在文档站，避免随 Skill 重复分发整套教程。常见问题统一从 `docs/guide/troubleshooting.md` 查找。离线教程可直接作为 Markdown 阅读。

网页编辑：`python3 scripts/career.py workbench`；临时虚构试用：加 `--demo`。操作见 `docs/guide/workbench.md`。

本包仅包含运行所需规则、脚本、模板、虚构示例与教程，不携带仓库版本文件、Git 忽略文件、测试、CI 或文档站构建环境。版本见下载文件名或市场版本记录。开发、测试和发布请获取[源码仓库](https://github.com/fonghehe/career-resume-skill)，完整在线说明见[文档站](https://fonghehe.github.io/career-resume-skill/)。

许可见 `LICENSE.md`。运行包中的演示使用纯文字附件，源码工程另保留图片演示。私人资料不自动上传、发布或投递。

目录分工：`references/` 是公共流程，`assets/` 是空模板、主题和工作台资源，`examples/` 是最小虚构演示，`docs/` 是离线操作指南。`scripts/career.py` 是唯一日常入口，`scripts/career_resume/` 为内部实现；无需进入内部目录执行文件。私人内容只在初始化后的 `local/` 中维护。

## 日常命令入口

```sh
python3 scripts/career.py init
python3 scripts/career.py build
python3 scripts/career.py web
python3 scripts/career.py workbench
python3 scripts/career.py export "实际版本/resume.en.md" --format all
python3 scripts/career.py validate
```

`resume.en.md` 自动使用国际版式；Word 只需 Python，PDF 需要本机 LibreOffice。导出时已有文件一律保留。添加经历、选材和中英写作由智能体按 Skill 完成，工具只聚合、校验和转换。切换副本使用命令前的 `--workspace /完整副本路径`。详见 `docs/guide/quick-start.md` 和 `docs/guide/export-resume.md`。

任职、教育、资格、作品、课程、服务或研究等材料按实际需要组织；自定义详细记录放在 `local/references/career/`，网页模块可自由命名。工作台可从任职、模块或源记录准备材料，无需先创建项目。
