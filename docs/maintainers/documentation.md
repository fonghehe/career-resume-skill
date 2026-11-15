# 维护 VitePress 文档站

这个站点用于教人使用 skill，个人履历网页仍由 Python 生成。`ci.yml` 检查文档能否构建；`pages.yml` 在推送到 `main` 时构建并发布教程站到 GitHub Pages，也支持从 Actions 手动运行。个人履历不进入部署产物。

## 安装、开发与构建

项目锁定 VitePress 1.6.4，使用 Node.js 24.x 与 pnpm 11.16.0，`@types/node` 对齐 Node 24。`packageManager` 锁定 pnpm，`engines` 与工作区严格检查阻止版本不符的工具链；CI 同样使用 Node 24。安装方式参阅 [pnpm 官方安装说明](https://pnpm.io/installation)，站点结构参阅 [VitePress 1.x 官方文档](https://vuejs.github.io/vitepress/v1/)。

```sh
pnpm install --frozen-lockfile
pnpm docs:dev
```

构建并预览：

```sh
pnpm docs:build
pnpm docs:preview
```

默认预览地址为 `http://localhost:4173/career-resume-skill/`；端口被占用时以实际终端输出为准。构建目录为 `docs/.vitepress/dist/`，缓存和构建产物由 Git 忽略。

## package.json 的命令分工

| 命令 | 用途 |
|---|---|
| `pnpm career <子命令>` | 履历工具统一入口，例如 `pnpm career init`、`pnpm career export 实际路径.md` |
| `pnpm workbench` / `pnpm workbench:demo` | 打开私人资料工作台 / 临时虚构演示 |
| `pnpm doctor` / `pnpm doctor:smoke` | 环境诊断 / 临时空白运行包自检；文档环境用 `pnpm doctor --docs` |
| `pnpm test` | 在当前完整副本执行工具测试；推荐公共维护使用下面的 `check` |
| `pnpm check` / `pnpm check:public-index` | 临时公共副本回归 / 公共 Git 索引检查 |
| `pnpm package` | 询问版本后生成 SkillHub 包 |
| `pnpm package:runtime` | 询问版本后生成通用运行包 |
| `pnpm package:source /新目录` | 导出公共源码目录，不询问发布版本 |
| `pnpm docs:dev` / `pnpm docs:build` / `pnpm docs:preview` | 开发、构建、预览教程站 |
| `pnpm docs:demo` | 单独重建文档中的虚构示例 |

原先 `profile:init`、`profile:update`、`career:build`、`timeline:build`、`resume:export`、`git:import`、`share:export`、`skill:install` 等别名统一使用 `pnpm career` 对应子命令；原 `release` / `release:skillhub` 改用 `package:runtime` / `package`。全部 Python 命令仍可脱离 pnpm 使用。

## 哪些文件属于这个站点

| 路径 | 用途 |
|---|---|
| `docs/.vitepress/config.mts` | 站点名称、导航、侧栏、搜索、来源目录 |
| `docs/index.md` | 首页 |
| `docs/guide/` | 逐步教程 |
| `docs/reference/` | 命令、数据约定和安装兼容 |
| `docs/maintainers/` | 构建、测试和公开导出 |
| `docs/examples.md` | 五个职业的在线示例总览与入口 |
| `examples/career-demo/` | 虚构网页夹具 |
| `examples/resume-demo/` | 虚构经历、文字履历、简历与依据报告 |
| `examples/professions/` | 五个职业的虚构源记录、履历、简历、依据报告与展示数据 |
| `scripts/career.py demo --docs` | 生成文档中展示的虚构 HTML |
| `tools/build_site.py` | 从多职业示例源重建个人网页、阅读页、画廊与履历时间线 |

站点直接读取 `docs/`，教程、参考和维护说明各保留一份。`private-usage.md`、`private/`、旧 `site/` 和生成的 `public/demo/**` 被配置排除；私人材料应放在项目的 `local/private/` 中。

`docs:dev` 和 `docs:build` 会先执行 `docs:demo`。它只读取指定虚构夹具，生成 `docs/public/demo/timeline.html`，再由 `tools/build_site.py` 从 `examples/professions/` 生成 `docs/public/demo/professions/`；两处产物都被 Git 忽略。`public/demo/**` 已加入 `srcExclude`，避免生成的 `.md` 源文件被当成站点页面做死链检查。不要把个人 HTML 手动放到公开静态资源目录。

## 仓库与部署路径

仓库地址为 [fonghehe/career-resume-skill](https://github.com/fonghehe/career-resume-skill)，GitHub Pages 文档站地址为 [https://fonghehe.github.io/career-resume-skill/](https://fonghehe.github.io/career-resume-skill/)。默认 `base` 已设为 `/career-resume-skill/`，运行 `pnpm docs:build` 即可生成适用于该地址的页面和资源链接；配置地址不代表已经部署成功。

托管到其他子路径或域名根路径时，可以覆盖默认值。例如部署在域名根路径：

```sh
DOCS_BASE=/ pnpm docs:build
```

这是 macOS / Linux 的环境变量写法。子路径要以 `/` 开头和结尾；根据实际托管地址填写。配置遵循 [VitePress 的 base 与 srcDir 约定](https://vuejs.github.io/vitepress/v1/reference/site-config)。

部署前检查 `docs/.vitepress/dist/` 的内容，确保只有教程、站点资源和虚构示例。将构建目录交给你选择的托管服务，个人 `local/showcase/` 不属于教程站发布目录。

## 首次启用 GitHub Pages

1. 打开仓库的 [Settings → Pages](https://github.com/fonghehe/career-resume-skill/settings/pages)。
2. 将 **Build and deployment → Source** 设为 **GitHub Actions**。
3. 将公共改动推送到 `main`，在 [Actions](https://github.com/fonghehe/career-resume-skill/actions) 中查看 **Deploy documentation to Pages**。
4. 确认 `build` 和 `deploy` 两个任务都成功，再访问文档站。仅有 **Validate skill** 成功表示构建检查通过，不能证明页面已发布。

工作流使用 `configure-pages` 获取 Pages 配置，构建 `docs/.vitepress/dist/`，通过 `upload-pages-artifact` 上传该目录，再由 `deploy-pages` 发布。构建任务只有读取权限，发布任务使用 `pages: write` 与 `id-token: write`，不提交生成文件或改写仓库分支。默认 `github-pages` 环境若设置了审批或分支限制，需要按仓库规则完成审批并允许 `main`。

如果显示找不到 Pages 站点，先检查上述 Source 设置；如果卡在环境审批，查看 `github-pages` 环境；如果构建失败，按日志修复依赖或断链。站点首页 404 与页面已打开但资源 404 应分别检查部署任务和 `base`。完整配置依据见 [VitePress 1.x 部署说明](https://vuejs.github.io/vitepress/v1/guide/deploy#github-pages)和 [GitHub Pages 工作流说明](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## 下载链接与页面跳转

DOCX 等静态附件链接必须设置 `download` 属性。当前 VitePress 1.6.4 的客户端路由未将 `.docx` 列为静态扩展名；缺少 `download` 时会把它改为 `.docx.html`，即使构建目录中 Word 文件存在，点击仍会失败。示例总览使用带文件名的下载属性，独立示例网页也显式标为下载。

验证时先用 `pnpm docs:build` 生成实际附件，再通过 `pnpm docs:preview` 打开示例页，点击中英文 Word，确认触发文件下载、正文页 URL 保持不变。仅检查文件存在或构建成功不能覆盖客户端路由错误；线上站点须部署这次构建后再核验。

## 新增一页怎样维护

1. 在 `docs/guide/` 或 `reference/` 写通用内容。
2. 更新配置中的侧栏，正文使用相对 Markdown 链接。
3. 在 `scripts/career_resume/bundle.py` 公共清单中登记新文件。
4. 运行 Python 校验、测试和 `pnpm docs:build`，修复断链。
5. 阅读暂存差异，运行 `check_public_index.py` 再提交。

CI 包含 Python 工具检查和独立文档构建，文档步骤从干净 checkout 安装锁定依赖、生成虚构示例并检查页面链接。它验证可构建性，不替代对教程语义和个人资料边界的审查。
