# 维护 VitePress 文档站

这个站点用于教人使用 skill，个人履历网页仍由 Python 生成。`ci.yml` 检查文档能否构建；`pages.yml` 在推送到 `main` 时构建并发布教程站到 GitHub Pages，也支持从 Actions 手动运行。个人履历不进入部署产物。

## 安装、开发与构建

项目锁定 VitePress 1.6.4，使用 Node.js 22+ 与 pnpm 11。安装方式参阅 [pnpm 官方安装说明](https://pnpm.io/installation)，站点结构参阅 [VitePress 1.x 官方文档](https://vuejs.github.io/vitepress/v1/)。

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

## 哪些文件属于这个站点

| 路径 | 用途 |
|---|---|
| `docs/.vitepress/config.mts` | 站点名称、导航、侧栏、搜索、来源目录 |
| `docs/index.md` | 首页 |
| `docs/guide/` | 逐步教程 |
| `docs/reference/` | 命令、数据约定和安装兼容 |
| `docs/maintainers/` | 构建、测试和公开导出 |
| `assets/examples/career-demo/` | 虚构网页夹具 |
| `assets/examples/resume-demo/` | 虚构经历、文字履历、简历与依据报告 |
| `scripts/create_demo.py --docs` | 生成文档中展示的虚构 HTML |

站点直接读取 `docs/`，教程、参考和维护说明各保留一份。`private-usage.md`、`private/` 和旧 `site/` 被配置排除；私人材料应放在项目的 `local/private/` 中。

`docs:dev` 和 `docs:build` 会先执行 `docs:demo`。它只读取指定虚构夹具，生成 `docs/public/demo/timeline.html`；不要把个人 HTML 手动放到公开静态资源目录。

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

## 新增一页怎样维护

1. 在 `docs/guide/` 或 `reference/` 写通用内容。
2. 更新配置中的侧栏，正文使用相对 Markdown 链接。
3. 在 `scripts/bundle.py` 公共清单中登记新文件。
4. 运行 Python 校验、测试和 `pnpm docs:build`，修复断链。
5. 阅读暂存差异，运行 `check_public_index.py` 再提交。

CI 包含 Python 工具检查和独立文档构建，文档步骤从干净 checkout 安装锁定依赖、生成虚构示例并检查页面链接。它验证可构建性，不替代对教程语义和个人资料边界的审查。
