import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'zh-CN',
  title: 'career-resume-skill',
  description: '先从经历与材料生成完整职业履历，再按方向或岗位生成有依据的简历。',
  srcExclude: ['private-usage.md', 'private/**', 'site/**'],
  base: process.env.DOCS_BASE || '/career-resume-skill/',
  ignoreDeadLinks: false,
  themeConfig: {
    socialLinks: [
      { icon: 'github', link: 'https://github.com/fonghehe/career-resume-skill' },
    ],
    editLink: {
      pattern: 'https://github.com/fonghehe/career-resume-skill/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页',
    },
    nav: [
      { text: '快速开始', link: '/guide/quick-start' },
      { text: '生成简历', link: '/guide/generate-resume' },
      { text: '完整示例', link: '/example' },
      { text: '目录与工具', link: '/reference/directories' },
    ],
    sidebar: [
      {
        text: '开始使用',
        items: [
          { text: '快速开始：履历到简历', link: '/guide/quick-start' },
          { text: '多智能体安装与调用', link: '/guide/using-skill' },
          { text: '完整虚构示例', link: '/example' },
        ],
      },
      {
        text: '日常使用',
        items: [
          { text: '生成第一份履历', link: '/guide/first-library' },
          { text: '回顾多年项目与经历', link: '/guide/review-career' },
          { text: '补充、更正与维护', link: '/guide/update-career' },
          { text: '根据履历生成简历', link: '/guide/generate-resume' },
          { text: '准备面试材料', link: '/guide/prepare-interview' },
        ],
      },
      {
        text: '可选能力',
        collapsed: false,
        items: [
          { text: '导入旧简历', link: '/guide/import-resume' },
          { text: '补充项目与技术案例', link: '/guide/project-cases' },
          { text: '本地 Git 证据与统计', link: '/guide/git-timeline' },
          { text: '生成离线履历网页', link: '/guide/generate-webpage' },
        ],
      },
      {
        text: '参考与排查',
        items: [
          { text: '能力与交付', link: '/reference/capabilities' },
          { text: '目录与文件位置', link: '/reference/directories' },
          { text: '工具命令', link: '/reference/commands' },
          { text: '数据与事实状态', link: '/reference/data-model' },
          { text: '安装与兼容', link: '/reference/compatibility' },
          { text: '隐私、分享与备份', link: '/guide/privacy' },
          { text: '常见问题', link: '/guide/troubleshooting' },
        ],
      },
      {
        text: '维护项目',
        collapsed: true,
        items: [
          { text: '文档站开发与构建', link: '/maintainers/documentation' },
          { text: '行为测试', link: '/maintainers/behavior-testing' },
          { text: '公开导出与发布', link: '/maintainers/releasing' },
        ],
      },
    ],
    search: { provider: 'local' },
    outline: { level: [2, 3], label: '本页内容' },
    docFooter: { prev: '上一页', next: '下一页' },
    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '教程目录',
    darkModeSwitchLabel: '主题',
    footer: { message: '公共教程与虚构示例 · 个人资料保存在使用者本地' },
  },
})
