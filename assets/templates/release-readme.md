# career-resume-skill

先整理完整、带来源的职业履历，再按需生成简历、依据报告和面试材料。

这是可独立运行的 Skill 包，入口为 `SKILL.md`。解压后用智能体打开本目录，提供口述经历或旧简历即可开始；个人材料与产物保存在 `local/`。

先在解压目录执行（Python 3.9+，仅需标准库）：

```sh
python3 scripts/doctor.py
python3 scripts/init_profile.py
python3 scripts/validate.py
```

初始化只补缺失文件，并在私人工作副本生成 `.gitignore`；已有资料不覆盖。共享或只读安装使用 `python3 scripts/init_profile.py --workspace /新的私人目录`，随后打开新目录并使用其中的脚本。

虚构演示：`python3 scripts/create_demo.py`，结果为 `local/output/demo/showcase/project-timeline.html`。演示不读取个人经历，已有演示目录拒绝覆盖。

可用 `python3 scripts/install_skill.py --skills-dir /宿主技能父目录` 安装到其他客户端，或用 `--output /新的导入包.zip` 导出 ZIP。现有目标保留，不能覆盖安装。

教程在 `docs/guide/`，命令与数据说明在 `docs/reference/`。常见问题统一从 `docs/guide/troubleshooting.md` 查找。离线教程可直接作为 Markdown 阅读。

本包仅包含运行所需规则、脚本、模板、虚构示例与教程，不携带仓库版本文件、Git 忽略文件、测试、CI 或文档站构建环境。版本见下载文件名或市场版本记录。开发、测试和发布请获取[源码仓库](https://github.com/fonghehe/career-resume-skill)，完整在线说明见[文档站](https://fonghehe.github.io/career-resume-skill/)。

许可见 `LICENSE`。私人资料不自动上传、发布或投递。
