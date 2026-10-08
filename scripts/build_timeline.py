#!/usr/bin/env python3
"""Build the standalone project and career timeline webpage."""

import argparse
import base64
import copy

from career_data import checked_local, parse_iso_datetime, project_ids
from html import escape
import json
from urllib.parse import urlsplit
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = ROOT / "references/projects"


HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <meta name="description" content="公司任职、职级变化、项目统计与本人提交">
  <title>__PAGE_TITLE__</title>
  <style>
    :root {
      --ink: #14213d;
      --muted: #64748b;
      --soft: #eef3f8;
      --line: #d9e2ec;
      --panel: #ffffff;
      --bg: #f8f5ef;
      --blue: #2563eb;
      --navy: #183b65;
      --teal: #0f766e;
      --orange: #c15b20;
      --purple: #7c3aed;
      --green: #15803d;
      --red: #b42318;
      --shadow: 0 18px 48px rgba(29, 48, 75, .08);
      --radius: 18px;
      --section-gap: 16px;
      --card-gap: 12px;
      --page-gutter: clamp(12px, 1.5vw, 24px);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 88% 0%, rgba(37, 99, 235, .09), transparent 28rem),
        linear-gradient(180deg, #f8fafc 0, var(--bg) 34rem);
      font: 14px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    button, input, select { font: inherit; }
    a { color: inherit; }
    .page { display: grid; gap: var(--section-gap); width: calc(100% - 2 * var(--page-gutter)); margin: 0 auto; padding: 28px 0 36px; }
    .page > * { min-width: 0; }
    .hero { display: grid; grid-template-columns: minmax(0, 1fr) minmax(220px, 320px); gap: 16px; align-items: end; }
    .eyebrow { margin: 0 0 8px; color: var(--blue); font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
    h1 { margin: 0; max-width: 980px; font-size: clamp(28px, 3vw, 40px); line-height: 1.22; letter-spacing: -.02em; }
    .lead { margin: 8px 0 0; color: var(--muted); font-size: 15px; }
    .updated { text-align: right; color: var(--muted); overflow-wrap: anywhere; }
    .updated strong { display: block; color: var(--ink); font-size: 14px; text-wrap: balance; }
    .stats { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: var(--card-gap); }
    .stat, .panel { background: rgba(255,255,255,.94); border: 1px solid rgba(216,226,236,.9); box-shadow: var(--shadow); }
    .stat { padding: 14px 16px; border-radius: 14px; }
    .stat strong { display: block; font-size: 28px; line-height: 1.15; letter-spacing: -.035em; }
    .stat span { display: block; margin-top: 4px; color: var(--muted); }
    .panel { border-radius: var(--radius); padding: 20px; }
    .section-head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 14px; }
    .section-head h2 { margin: 0; font-size: 24px; letter-spacing: -.02em; }
    .section-head p { margin: 4px 0 0; color: var(--muted); max-width: 800px; }
    .legend { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
    .pill { display: inline-flex; gap: 7px; align-items: center; padding: 6px 10px; border: 1px solid var(--line); border-radius: 999px; background: #fff; color: #526277; white-space: nowrap; font-size: 12px; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
    .filters { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 14px; }
    .control { min-width: 0; max-width: 100%; min-height: 44px; border: 1px solid var(--line); border-radius: 10px; background: #fff; padding: 10px 12px; color: var(--ink); }
    .search { min-width: 0; flex: 1 1 280px; width: 100%; }
    .check { display: inline-flex; align-items: center; gap: 8px; padding: 0 12px; border: 1px solid var(--line); border-radius: 10px; background: #fff; color: #526277; }
    .check input { accent-color: var(--blue); }
    .timeline-shell { overflow-x: auto; padding-bottom: 8px; }
    .timeline { min-width: 1050px; }
    .axis, .timeline-row { display: grid; grid-template-columns: 238px minmax(760px, 1fr); gap: 18px; }
    .axis { position: sticky; top: 0; z-index: 5; background: rgba(255,255,255,.97); }
    .axis-track { position: relative; height: 40px; border-bottom: 1px solid var(--line); }
    .tick { position: absolute; bottom: 0; height: 13px; border-left: 1px solid #cbd5e1; color: var(--muted); font-size: 11px; }
    .tick span { position: absolute; left: 4px; bottom: 13px; }
    .timeline-row { min-height: 56px; padding: 6px 0; align-items: center; border-bottom: 1px solid #edf1f5; }
    .timeline-row:last-child { border-bottom: 0; }
    .row-label strong, .row-label span { display: block; }
    .row-label strong { margin-bottom: 4px; font-size: 13px; }
    .row-label span { color: var(--muted); font-size: 11px; }
    .track { position: relative; min-height: 38px; background-image: linear-gradient(to right, rgba(203,213,225,.52) 1px, transparent 1px); background-size: 10% 100%; }
    .bar { position: absolute; top: 8px; height: 24px; min-width: 5px; border-radius: 7px; box-shadow: inset 0 0 0 1px rgba(255,255,255,.28); overflow: visible; }
    .bar::after { content: attr(data-label); position: absolute; left: 8px; top: 2px; color: #fff; font-size: 11px; font-weight: 700; line-height: 20px; white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,.2); }
    .bar.short::after { left: calc(100% + 7px); color: var(--ink); text-shadow: none; }
    .bar:not(.short)::after { max-width: calc(100% - 16px); overflow: hidden; text-overflow: ellipsis; }
    .project-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--card-gap); margin-top: 16px; }
    .project-card { display: flex; flex-direction: column; gap: 8px; min-width: 0; position: relative; padding: 16px; border: 1px solid var(--line); border-radius: 14px; background: #fff; cursor: pointer; overflow-wrap: anywhere; transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease; }
    .project-card:hover, .project-card:focus-within { transform: translateY(-2px); border-color: #9bb7df; box-shadow: 0 12px 28px rgba(37,99,235,.1); outline: none; }
    .project-card h3 { margin: 0; font-size: 18px; line-height: 1.45; }
    .project-card p { margin: 0; color: #526277; }
    .project-link { display: inline-flex; margin-top: 10px; color: var(--blue); font-weight: 700; text-decoration: none; }
    .project-link:hover { text-decoration: underline; }
    .detail-link { display: inline-flex; margin-top: 12px; padding: 0; border: 0; background: transparent; color: var(--blue); font-weight: 800; cursor: pointer; }
    .project-card .meta { margin: 0 !important; }
    .project-card .chips { margin: 0; }
    .project-card .detail-link { align-self: flex-start; margin-top: auto; padding-top: 4px; text-align: left; }
    .card-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; color: var(--muted); font-size: 11px; }
    .tag { display: inline-flex; padding: 3px 8px; border-radius: 999px; background: var(--soft); color: var(--navy); font-weight: 700; }
    .tag.confirmed { color: var(--green); background: #edf9f0; }
    .tag.resume-supported { color: var(--purple); background: #f4f0ff; }
    .tag.synthetic-draft { color: var(--red); background: #fff0ee; }
    .meta { margin-top: 10px !important; color: var(--muted) !important; font-size: 12px; }
    .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
    .chip { padding: 3px 7px; border: 1px solid #dde6ee; border-radius: 6px; color: #45566c; background: #fafcff; font-size: 11px; }
    .career-list { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--card-gap); }
    .career-item { display: grid; grid-template-columns: 116px minmax(0, 1fr); gap: 12px; padding: 14px; border: 1px solid var(--line); border-radius: 12px; background: #fff; overflow-wrap: anywhere; }
    .career-date { color: var(--blue); font-weight: 800; font-size: 12px; }
    .career-item h3 { margin: 0; font-size: 15px; }
    .career-item p { margin: 2px 0 0; color: var(--muted); }
    .career-company { grid-column: 1 / -1; display: block; padding: 16px; }
    .career-company-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
    .career-company-head h3 { font-size: 18px; }
    .career-company-head .career-date { white-space: nowrap; }
    .career-phases { margin: 12px 0 0; padding: 0 0 0 20px; list-style: none; border-left: 2px solid var(--line); }
    .career-phase { position: relative; display: grid; grid-template-columns: 190px minmax(0, 1fr); gap: 12px; padding: 0 0 12px; }
    .career-phase:last-child { padding-bottom: 0; }
    .career-phase::before { content: ''; position: absolute; left: -26px; top: 7px; width: 10px; height: 10px; border: 2px solid #fff; border-radius: 50%; background: var(--blue); }
    .career-phase time { color: var(--muted); font-size: 12px; font-variant-numeric: tabular-nums; }
    .career-phase h4 { margin: 0; font-size: 14px; }
    .career-phase p { font-size: 13px; }
    .impact-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
    .impact-card { padding: 17px; border: 1px solid var(--line); border-radius: 12px; background: #fff; }
    .impact-card strong { display: block; font-size: 23px; letter-spacing: -.02em; }
    .impact-card span { color: var(--muted); font-size: 12px; }
    .leadership-phases { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
    .copilot-flow { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; margin-top: 18px; }
    .responsibility-row { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; margin-bottom: 16px; }
    .flow-arrow { color: #94a3b8; }
    .repo-group { margin: 18px 0 7px; color: var(--navy); font-size: 13px; font-weight: 800; }
    .repo-table-wrap { overflow-x: auto; margin-top: 16px; }
    table { width: 100%; border-collapse: collapse; min-width: 940px; }
    th, td { padding: 11px 10px; border-bottom: 1px solid #e8edf2; vertical-align: top; text-align: left; }
    th { color: var(--muted); background: #f8fafc; font-size: 11px; letter-spacing: .04em; text-transform: uppercase; }
    td { font-size: 12px; }
    td strong { display: block; color: var(--ink); }
    td small { display: block; max-width: 360px; color: var(--muted); line-height: 1.45; }
    .count { font-variant-numeric: tabular-nums; font-weight: 800; color: var(--blue); }
    .scope-details > summary { cursor: pointer; font-weight: 700; }
    .scope-details .method { margin-top: 12px; }
    .method { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
    .method article { padding: 17px; border-radius: 12px; background: #f7f9fc; }
    .method h3 { margin: 0 0 5px; font-size: 14px; }
    .method p { margin: 0; color: var(--muted); font-size: 12px; }
    .bar[data-project-id] { cursor: pointer; }
    .bar[data-project-id]:focus-visible { outline: 3px solid rgba(37,99,235,.35); outline-offset: 3px; }
    body.modal-open { overflow: hidden; }
    .detail-modal[hidden] { display: none; }
    .detail-modal { position: fixed; inset: 0; z-index: 100; display: grid; grid-template-columns: minmax(0,1fr); align-items: stretch; }
    .modal-backdrop { position: absolute; inset: 0; border: 0; background: rgba(15,23,42,.54); backdrop-filter: blur(3px); cursor: pointer; }
    .detail-drawer { position: relative; justify-self: end; width: min(860px, 94vw); height: 100%; overflow: auto; padding: 24px; background: #f8fafc; box-shadow: -18px 0 60px rgba(15,23,42,.2); }
    .modal-close { position: sticky; top: 0; z-index: 2; float: right; width: 40px; height: 40px; border: 1px solid var(--line); border-radius: 50%; background: #fff; color: var(--ink); font-size: 24px; line-height: 1; cursor: pointer; box-shadow: var(--shadow); }
    .detail-head { padding-right: 54px; }
    .detail-head h2 { margin: 8px 0 12px; font-size: 30px; line-height: 1.3; }
    .detail-head p { margin: 0; color: var(--muted); }
    .capability-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 14px; margin: 16px 0 0; }
    .capability-box { padding: 18px; border: 1px solid var(--line); border-radius: 12px; background: #fff; }
    .capability-box h3 { margin: 0 0 10px; font-size: 14px; }
    .capability-box .empty-capability { color: var(--muted); font-size: 12px; }
    .markdown-panel { clear: both; margin-top: 18px; }
    .project-record { margin: 16px 0; padding: 18px; border: 1px solid var(--line); border-radius: 14px; background: #fffdf8; font-size: 15px; line-height: 1.7; overflow-wrap: anywhere; }
    .project-record h3 { margin: 20px 0 8px; font-size: 19px; line-height: 1.4; }
    .project-record h4 { margin: 16px 0 8px; line-height: 1.4; }
    .project-record p { margin: 8px 0; white-space: pre-line; }
    .project-record ul { margin: 8px 0; padding-left: 22px; }
    .project-record li { margin: 4px 0; }
    .project-record > :first-child { margin-top: 0; }
    .project-record > :last-child { margin-bottom: 0; }
    .project-record pre { overflow: auto; white-space: pre-wrap; }
    .project-extra { margin: 16px 0 0; padding-top: 12px; border-top: 1px solid var(--line); color: var(--muted); }
    .project-extra > summary { cursor: pointer; padding: 4px 0; }
    .markdown-panel h3 { margin: 0; font-size: 17px; }
    .markdown-path { margin: 4px 0 12px; color: var(--muted); font-size: 12px; }
    .markdown-source { max-height: none; overflow: auto; margin: 0; padding: 18px; border: 1px solid #cad5e2; border-radius: 12px; background: #101827; color: #dbeafe; white-space: pre-wrap; overflow-wrap: anywhere; font: 12px/1.65 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
    .empty { padding: 28px; color: var(--muted); text-align: center; border: 1px dashed var(--line); border-radius: 12px; }
    .git-events { list-style: none; margin: 12px 0 0; padding: 0 0 0 22px; border-left: 2px solid var(--line); }
    .git-event { position: relative; padding: 0 0 16px 12px; overflow-wrap: anywhere; }
    .git-event:last-child { padding-bottom: 0; }
    .git-event::before { content: ''; position: absolute; left: -29px; top: 7px; width: 10px; height: 10px; border-radius: 50%; background: var(--teal); box-shadow: 0 0 0 4px #eaf3ee; }
    .git-event time { color: var(--muted); font-size: 12px; }
    .git-event h3 { margin: 8px 0; font-size: 16px; line-height: 1.5; }
    .git-event p { margin: 8px 0 0; white-space: pre-line; line-height: 1.75; }
    .git-event details { margin-top: 12px; color: var(--muted); font-size: 12px; }
    .git-event summary { cursor: pointer; }
    .git-event code { overflow-wrap: anywhere; }
    .event-project { padding: 0; border: 0; background: transparent; color: var(--blue); cursor: pointer; }
    .demo-notice { padding: 10px 14px; border: 1px solid #e6cda4; border-radius: 12px; background: #fff5df; color: #785c2c; }
    #gitHistory { margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--line); }
    #gitRecords > summary { cursor: pointer; font-weight: 700; }
    #gitHistory .filters { margin-top: 12px; margin-bottom: 12px; }
    .project-metrics { display: flex; flex-wrap: wrap; gap: 12px; padding: 8px 0; border-block: 1px solid var(--line); color: var(--muted); font-size: 12px; }
    .project-metrics strong { color: var(--ink); font-size: 16px; }
    .project-milestones { list-style: none; margin: 0; padding: 0; }
    .project-milestones li { display: grid; grid-template-columns: 70px minmax(0,1fr); gap: 8px; padding: 6px 0; }
    .project-milestones time { color: var(--muted); font-size: 12px; }
    .project-milestones p { margin: 4px 0 0; color: var(--muted); font-size: 12px; }
    #detailOverview { margin-top: 16px; }
    #gitEventCount { margin: 0 !important; }
    #gitMore, #detailGitMore { margin-top: 20px; }
    #detailGit > h3 { margin: 0; }
    [hidden] { display: none !important; }
    .global-filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .global-filters label { display: flex; gap: 6px; align-items: center; }
    .filter-note { color: var(--muted); font-size: 12px; }
    .source-details { margin-top: 8px; font-size: 12px; color: var(--muted); }
    .source-details summary { cursor: pointer; color: var(--blue); }
    .source-details article { margin-top: 10px; padding: 10px; background: var(--soft); border-radius: 8px; }
    .source-details p { white-space: pre-wrap; margin: 4px 0; }
    .source-details pre { white-space: pre-wrap; overflow-wrap: anywhere; font: inherit; }
    .attachments { display: grid; gap: 12px; margin-top: 16px; }
    .attachments figure { margin: 0; }
    .attachments img { display: block; width: 100%; max-height: 420px; object-fit: contain; border: 1px solid var(--line); border-radius: 10px; background: #fff; }
    .attachments figcaption { margin-top: 4px; color: var(--muted); font-size: 12px; }
    .share-preview { width: 100%; height: 420px; border: 1px solid var(--line); border-radius: 10px; margin-top: 10px; background: white; }
    .activity-details { margin-top: 14px; }
    .activity-details > summary { cursor: pointer; font-weight: 700; }
    .activity-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 16px; margin-top: 12px; }
    .activity-grid h3 { margin: 0 0 8px; font-size: 14px; }
    .activity-row { display: grid; grid-template-columns: minmax(76px,1fr) minmax(0,2fr) 40px; gap: 8px; align-items: center; margin: 6px 0; font-size: 12px; overflow-wrap: anywhere; }
    .activity-row meter { width: 100%; height: 12px; }
    footer { padding: 4px; color: var(--muted); font-size: 12px; text-align: center; }
    @media (max-width: 1050px) {
      .stats { grid-template-columns: repeat(3, 1fr); }
      .project-grid { grid-template-columns: repeat(2, 1fr); }
      .hero { grid-template-columns: 1fr; }
      .updated { text-align: left; }
    }
    @media (max-width: 700px) {
      :root { --section-gap: 14px; --card-gap: 10px; }
      .page { padding: 20px 0 28px; }
      .hero { gap: 10px; }
      .lead { font-size: 15px; line-height: 1.75; }
      .stats { grid-template-columns: repeat(2, 1fr); }
      .stat { padding: 12px; }
      .stat strong { font-size: 25px; }
      .panel { padding: 16px; }
      .section-head { margin-bottom: 12px; }
      .section-head h2 { font-size: 22px; line-height: 1.4; }
      .section-head { display: block; }
      .legend { justify-content: flex-start; margin-top: 10px; }
      .filters { gap: 8px; margin-bottom: 12px; }
      .timeline { min-width: 760px; }
      .axis, .timeline-row { grid-template-columns: 164px minmax(520px, 1fr); gap: 12px; }
      .row-label { padding-right: 4px; overflow-wrap: anywhere; }
      .project-card { padding: 14px; }
      .project-grid, .career-list, .method, .leadership-phases, .impact-grid { grid-template-columns: 1fr; }
      .career-item { grid-template-columns: 1fr; gap: 12px; }
      .career-company { padding: 14px; }
      .career-company-head { flex-direction: column; gap: 8px; }
      .career-phase { grid-template-columns: minmax(0, 1fr); gap: 4px; }
      .detail-drawer { width: 100%; padding: 16px; }
      .detail-head h2 { font-size: 26px; }
      .project-record { padding: 16px; }
      .capability-grid, .activity-grid { grid-template-columns: 1fr; }
    }
    @media print {
      body { background: #fff; }
      .page { display: block; width: 100%; padding: 0; }
      .page > * { margin-bottom: 20px; }
      .filters { display: none; }
      .panel, .stat { box-shadow: none; break-inside: avoid; }
      .timeline-shell, .repo-table-wrap { overflow: visible; }
      .timeline { min-width: 0; }
      .axis, .timeline-row { grid-template-columns: 190px 1fr; }
    }
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <div>
        <p class="eyebrow">Career overview · 项目履历</p>
        <h1 id="title"></h1>
        <p class="lead" id="subtitle"></p>
      </div>
      <div class="updated"><strong id="headline"></strong>资料更新：<span id="updatedAt"></span></div>
    </header>

    <aside class="demo-notice" id="demoNotice" hidden>这是一份虚构演示：公司、职级、项目和 Git 提交都是为展示功能编写的，不属于任何人的真实经历。</aside>

    <nav class="global-filters" aria-label="整页筛选">
      <label>公司 <select class="control" id="companyFilter" aria-label="按公司筛选整页"><option value="">所有公司与独立项目</option></select></label>
      <label>时间 <select class="control" id="yearFilter" aria-label="按年份筛选整页"><option value="">全部年份</option></select></label>
      <button class="control" id="resetFilters" type="button">重置</button>
      <button class="control" id="downloadShare" type="button">下载当前范围分享页</button>
      <label class="filter-note"><input type="checkbox" id="shareCompanies">保留公司名称</label>
      <label class="filter-note"><input type="checkbox" id="shareAttachments">包含已检查的项目附件</label>
      <span class="filter-note" id="scopeNote">公司、项目和代码记录同步筛选</span>
      <span class="filter-note">分享页保留项目名称、职责、阶段和任职摘要；下载后检查文字与可选附件再分享。</span>
    </nav>

    <section id="shareResult" hidden aria-live="polite">
      <a id="shareDownload" download="career-share.html">分享页已生成 · 下载 HTML</a>
      <details><summary>预览分享内容</summary><iframe class="share-preview" id="sharePreview" title="分享内容预览" sandbox="allow-scripts"></iframe></details>
    </section>

    <section class="stats" id="stats" aria-label="概览统计"></section>

    <section class="panel" id="career">
      <div class="section-head">
        <div><h2>公司任职与职级变化</h2><p>按公司汇总任职，内部部门、职位和职级变化保留为阶段。</p></div>
      </div>
      <div class="career-list" id="careerList"></div>
    </section>

    <section class="panel" id="projects">
      <div class="section-head">
        <div><h2>项目历程</h2><p>按项目查看职责、关键阶段、关联仓库和本人提交统计。</p></div>
        <div class="legend">
          <span class="pill" style="color:var(--green)"><i class="dot"></i>我已确认</span>
          <span class="pill" style="color:var(--purple)"><i class="dot"></i>来自简历</span>
          <span class="pill" style="color:var(--red)"><i class="dot"></i>独立项目</span>
        </div>
      </div>
      <div class="filters">
        <input class="control search" id="search" type="search" placeholder="搜索项目、公司或技术栈" aria-label="搜索项目">
        <select class="control" id="category" aria-label="按类别筛选"><option value="">全部类别</option></select>
      </div>
      <div class="timeline-shell"><div class="timeline" id="projectTimeline"></div></div>
      <div class="project-grid" id="projectGrid"></div>
    </section>

    <section class="panel" id="repositories">
      <div class="section-head">
        <div><h2>仓库与本人 Commit</h2><p id="repositoryNote">按本人署名统计本地仓库活动，提交日期只表示代码活动。</p></div>
        <div class="legend" id="repoLegend"></div>
      </div>
      <div class="timeline-shell"><div class="timeline" id="repoTimeline"></div></div>
      <div class="repo-table-wrap">
        <table>
          <thead><tr><th>仓库</th><th>次数</th><th>首次记录</th><th>最后记录</th><th>活动跨度</th></tr></thead>
          <tbody id="repoTable"></tbody>
        </table>
      </div>
      <details class="activity-details" id="activityDetails"><summary>每月活动与主要修改模块</summary><div id="activityCharts" class="activity-grid"></div><p class="filter-note" id="activityNote"></p></details>
      <div id="gitHistory" hidden>
        <details id="gitRecords"><summary id="gitRecordsSummary">查看本人提交记录</summary>
        <div class="filters">
          <select class="control" id="gitProject" aria-label="按项目查看代码足迹"><option value="">所有项目</option></select>
          <select class="control" id="gitRepository" aria-label="按仓库查看代码足迹"><option value="">所有仓库</option></select>
          <input class="control search" id="gitSearch" type="search" placeholder="搜索提交主题、项目或仓库" aria-label="搜索代码记录">
        </div>
        <p id="gitEventCount" class="meta"></p>
        <ol class="git-events" id="gitEvents"></ol>
        <button class="control" type="button" id="gitMore" hidden>加载更多提交</button>
        </details>
      </div>
    </section>

    <details class="panel scope-details"><summary>统计口径</summary><p class="meta">任职、职级、项目与提交分别记录，各类日期和数量保留来源。</p>
      <div class="method">
        <article><h3>项目时间</h3><p>采用用户确认或无冲突的简历支持时间。缺少时间的项目保留项目卡，但不进入横轴。</p></article>
        <article><h3>仓库活动</h3><p>首末提交仅表示仓库活动范围；不能据此推断任职时间、项目上线时间或个人贡献比例。同一提交可涉及多个项目，各项目计数不可相加当总贡献。</p></article>
        <article><h3>职责与职级</h3><p>职级使用本人提供或简历记载的正式信息；技术负责职责不自动等于正式职称或晋升。</p></article>
      </div>
    </details>
    <footer>由 career-resume-skill 的 data/timeline.json 生成 · 可离线打开 · 不加载外部资源</footer>
  </main>

  <div class="detail-modal" id="projectDetail" hidden aria-hidden="true">
    <button class="modal-backdrop" type="button" data-close-detail aria-label="关闭项目详情"></button>
    <aside class="detail-drawer" role="dialog" aria-modal="true" aria-labelledby="detailTitle">
      <button class="modal-close" id="detailClose" type="button" data-close-detail aria-label="关闭">×</button>
      <header class="detail-head">
        <p class="eyebrow" id="detailId"></p>
        <h2 id="detailTitle"></h2>
        <p id="detailMeta"></p>
      </header>
      <section id="detailOverview" aria-label="项目阶段与统计"></section>
      <section id="detailSources" aria-label="项目事实来源"></section>
      <section class="attachments" id="detailAttachments" aria-label="项目附件"></section>
      <section class="project-record" id="detailRecord" aria-label="项目记录"></section>
      <section id="detailGit" hidden><h3>这个项目的代码足迹</h3><ol class="git-events" id="detailGitEvents"></ol><button class="control" type="button" id="detailGitMore">查看这个项目的全部记录</button></section>
      <details class="project-extra"><summary>技术与协作信息</summary><div class="capability-grid" id="detailCapabilities"></div></details>
      <details class="markdown-panel project-extra">
        <summary>查看保存的项目原文</summary>
        <p class="markdown-path" id="detailPath"></p>
        <pre class="markdown-source" id="detailMarkdown"></pre>
      </details>
    </aside>
  </div>

  <script id="timeline-data" type="application/json">__TIMELINE_DATA__</script>
  <script id="fact-source-details" type="application/json">__SOURCE_DETAILS__</script>
  <script id="project-details" type="application/json">__PROJECT_DETAILS__</script>
  <script>
    const DATA = JSON.parse(document.getElementById('timeline-data').textContent);
    const SOURCE_DETAILS = JSON.parse(document.getElementById('fact-source-details').textContent);
    const PROJECT_DETAILS = JSON.parse(document.getElementById('project-details').textContent);
    const DAY = 86400000;
    const statusText = {confirmed: '我已确认', 'resume-supported': '来自简历', 'synthetic-draft': '演示草稿'};
    const palette = ['#2563eb','#0f766e','#7c3aed','#c15b20','#0369a1','#15803d','#be185d','#4f46e5'];
    const $ = (id) => document.getElementById(id);
    const date = (s) => s ? new Date(s.includes('T') ? s : s + 'T00:00:00Z') : null;
    const fmt = (s, withDay = true) => {
      if (!s) return '时间待定';
      const original = typeof s === 'string' && s.match(/^(\d{4})-(\d{2})-(\d{2})/);
      if (original) return withDay ? `${original[1]}.${original[2]}.${original[3]}` : `${original[1]}.${original[2]}`;
      const d = date(s);
      return withDay
        ? `${d.getUTCFullYear()}.${String(d.getUTCMonth()+1).padStart(2,'0')}.${String(d.getUTCDate()).padStart(2,'0')}`
        : `${d.getUTCFullYear()}.${String(d.getUTCMonth()+1).padStart(2,'0')}`;
    };
    const rangeEnd = (item) => item.ongoing ? '至今' : fmt(item.end);
    const days = (a, b) => Math.max(1, Math.round((date(b) - date(a)) / DAY) + 1);
    const duration = (a, b) => {
      const value = days(a, b);
      if (value < 60) return `${value} 天`;
      const months = Math.round(value / 30.44);
      if (months < 24) return `${months} 个月`;
      const years = value / 365.25;
      return `${years.toFixed(1)} 年`;
    };
    const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
    const hashColor = (value) => palette[[...value].reduce((n,c) => n + c.charCodeAt(0), 0) % palette.length];

    const projectIds = item => [...new Set([...(item.projectIds || []), ...(item.projectId ? [item.projectId] : [])])];
    const companyOf = item => item.groupOrganization || item.organization;
    const inYear = item => !$('yearFilter').value || !item.start || !item.end ||
      (item.start.slice(0,4) <= $('yearFilter').value && item.end.slice(0,4) >= $('yearFilter').value);
    const eventInYear = item => !$('yearFilter').value || item.authorDate.slice(0,4) === $('yearFilter').value;
    function viewProjects() {
      const company = $('companyFilter').value;
      return DATA.projects.filter(p => inYear(p) && (!company || companyOf(p) === company ||
        (p.careerIds || []).some(id => DATA.career.some(c => c.id === id && companyOf(c) === company))));
    }
    function viewEvents() {
      const ids = new Set(viewProjects().map(p => p.id));
      return (DATA.gitEvents || []).filter(e => eventInYear(e) &&
        (!$('companyFilter').value || projectIds(e).some(id => ids.has(id))));
    }
    function viewRepositories() {
      const ids = new Set(viewProjects().map(p => p.id));
      const year = $('yearFilter').value;
      return DATA.repositories.filter(r => inYear(r) && (!$('companyFilter').value ||
        [...projectIds(r), ...Object.keys(r.projectCounts || {})].some(id => ids.has(id)))).map(r => {
        const loaded = (DATA.gitEvents || []).filter(e => e.repository === r.name);
        const matched = viewEvents().filter(e => e.repository === r.name);
        let count = r.count, countLabel = '';
        if (year || $('companyFilter').value) {
          if (loaded.length === r.count) count = matched.length;
          else if (year && !$('companyFilter').value && r.activity?.monthly) {
            count = Object.entries(r.activity.monthly).filter(([month]) => month.startsWith(year + '-')).reduce((n,[,v]) => n+v,0);
          } else if (!year && $('companyFilter').value && projectIds(r).length === 1) {
            count = r.projectCounts?.[projectIds(r)[0]] ?? r.count;
          } else { count = matched.length; countLabel = '已载入'; }
        }
        const scoped = year || $('companyFilter').value;
        const ordered = [...matched].sort((a,b)=>date(a.authorDate)-date(b.authorDate));
        const range = scoped && loaded.length === r.count && ordered.length ? {
          start:ordered[0].authorDate,end:ordered.at(-1).authorDate,
          firstMessage:ordered[0].subject,lastMessage:ordered.at(-1).subject
        } : {};
        return {...r, ...range, count, countLabel};
      });
    }
    function sourcesMarkup(sources = []) {
      if (!sources.length) return '';
      const labels = {confirmed:'本人确认', 'resume-supported':'简历记载', git:'Git 证据', pending:'待确认'};
      const fields = {start:'开始时间', end:'结束时间', role:'职位', level:'职级', summary:'职责 / 概述', milestones:'项目阶段'};
      return `<details class="source-details"><summary>查看事实来源（${sources.length}）</summary>${sources.map(source =>
        `<article><strong>${escapeHtml(fields[source.field] || source.field)} · ${escapeHtml(labels[source.status])}</strong>
        <p>${escapeHtml(source.label)}</p>${source.excerpt ? `<p>${escapeHtml(source.excerpt)}</p>` : ''}
        ${SOURCE_DETAILS[source.path] ? `<details><summary>查看来源文字</summary><pre>${escapeHtml(SOURCE_DETAILS[source.path])}</pre></details>` : ''}</article>`).join('')}</details>`;
    }
    function renderActivity() {
      const monthly = Object.create(null), modules = Object.create(null), types = Object.create(null);
      const events = viewEvents();
      const year = $('yearFilter').value, company = $('companyFilter').value;
      let covered = 0, total = 0;
      for (const repo of viewRepositories()) {
        const records = events.filter(e => e.repository === repo.name);
        const complete = (DATA.gitEvents || []).filter(e => e.repository === repo.name).length === DATA.repositories.find(r => r.name === repo.name).count;
        const stats = complete || company ? activityFromEvents(records) : repo.activity || activityFromEvents(records);
        for (const [month, count] of Object.entries(stats.monthly || {})) if (!year || month.startsWith(year + '-')) monthly[month] = (monthly[month] || 0) + count;
        // Aggregate module/type histograms have no date/project partition; filter from records instead.
        const scoped = year || company ? activityFromEvents(records) : stats;
        for (const [name,count] of Object.entries(scoped.modules || {})) modules[name] = (modules[name] || 0) + count;
        for (const [name,count] of Object.entries(scoped.types || {})) types[name] = (types[name] || 0) + count;
        covered += records.filter(e => Array.isArray(e.files)).length;
        total += repo.count;
      }
      const chart = (title, histogram) => {
        const entries = Object.entries(histogram);
        const max = Math.max(1,...entries.map(([,n])=>n));
        return `<article><h3>${escapeHtml(title)}</h3>${entries.length ? entries.map(([label,n])=>
          `<div class="activity-row"><span>${escapeHtml(label)}</span><meter min="0" max="${max}" value="${n}" aria-label="${escapeHtml(label)}：${n} 次"></meter><span>${n}</span></div>`).join('') : '<p class="filter-note">暂无采集数据</p>'}</article>`;
      };
      $('activityCharts').innerHTML = chart('每月本人 Commit', Object.fromEntries(Object.entries(monthly).sort())) + chart('主要修改模块 · 涉及提交数', Object.fromEntries(Object.entries(modules).sort((a,b)=>b[1]-a[1]).slice(0,8))) + chart('提交类型 · 按原始主题分类',types);
      $('activityNote').textContent = `活跃月份 ${Object.keys(monthly).length} · 文件证据覆盖已载入 ${covered} 条 / 当前统计 ${total} 条。模块统计可重叠；类型不明保留 other，不用于评价能力。`;
    }
    function activityFromEvents(events) {
      const monthly = Object.create(null), modules = Object.create(null), types = Object.create(null);
      for (const e of events) {
        const month = e.authorDate.slice(0,7); monthly[month] = (monthly[month] || 0) + 1;
        const kind = e.subject.match(/^(feat|fix|docs|test|refactor|chore|perf|build|ci)(?:\([^)]*\))?[!:]/)?.[1] || 'other';
        types[kind] = (types[kind] || 0) + 1;
        for (const m of new Set((e.files || []).map(p => p.includes('/') ? p.split('/')[0] : '(root)'))) modules[m] = (modules[m] || 0) + 1;
      }
      return {monthly,modules,types};
    }
    function downloadShare() {
      const projects = viewProjects();
      if (!projects.length) { $('scopeNote').textContent='当前范围没有项目可导出。'; return; }
      const keepCompanies = $('shareCompanies').checked;
      const companies = [...new Set(projects.map(companyOf))].sort();
      const alias = Object.fromEntries(companies.map((c,i) => [c, keepCompanies ? c : `公司 ${i+1}`]));
      const select = (row,keys) => Object.fromEntries(keys.filter(k => k in row).map(k => [k,row[k]]));
      const ids = new Set(projects.map(p => p.id));
      const career = DATA.career.filter(c => inYear(c) && companyOf(c) in alias).map(c => ({
        ...select(c,['id','role','level','start','end','summary']), organization:alias[companyOf(c)],
        ...(c.groupOrganization ? {groupOrganization:alias[companyOf(c)]} : {})
      }));
      const safeProjects = projects.map(p => ({...select(p,['id','name','category','status','start','end','tech','highlights','summary','nature']),
        organization:alias[companyOf(p)], milestones:(p.milestones || []).map(m => select(m,['date','title','summary','status']))}));
      const repos = [];
      for (const repo of viewRepositories()) {
        const original = DATA.repositories.find(r => r.name === repo.name);
        const linked = new Set([...projectIds(original),...Object.keys(original.projectCounts || {})]);
        const mapped = [...linked].filter(p => ids.has(p));
        if (!mapped.length) continue;
        const all = (DATA.gitEvents || []).filter(e => e.repository === repo.name);
        const events = viewEvents().filter(e => e.repository === repo.name && projectIds(e).some(p => ids.has(p)));
        const complete = all.length === original.count;
        let count, monthly = {}, counts = {};
        if (complete) {
          count = events.length; monthly = activityFromEvents(events).monthly;
          counts = Object.fromEntries(mapped.map(p => [p,events.filter(e => projectIds(e).includes(p)).length]));
        } else if (!$('yearFilter').value && [...linked].every(p => ids.has(p))) {
          count=original.count; monthly=original.activity?.monthly || {};
          counts=Object.fromEntries(mapped.map(p => [p,original.projectCounts?.[p] ?? count]));
        } else if (!$('yearFilter').value && mapped.length === 1 && mapped[0] in (original.projectCounts || {})) {
          count=original.projectCounts[mapped[0]]; counts={[mapped[0]]:count};
        } else { $('scopeNote').textContent='当前范围缺少完整提交记录，请先让智能体补采，再生成分享页。'; return; }
        if (count) repos.push({name:`仓库 ${repos.length+1}`,group:'所选项目代码活动',start:repo.start,end:repo.end,count,
          projectIds:mapped,projectCounts:counts,activity:{monthly},firstMessage:'',lastMessage:''});
      }
      const starts=career.map(c=>c.start).filter(Boolean).sort(), ends=career.map(c=>c.end).filter(Boolean).sort();
      const safe = {meta:{title:'项目履历 · 分享版',subtitle:'所选项目与任职阶段摘要；不含来源原文、邮箱、仓库路径和提交明细。',updatedAt:DATA.meta.updatedAt,synthetic:!!DATA.meta.synthetic},
        profile:{headline:'所选项目概览',careerStart:starts[0] || '',careerEnd:ends.at(-1) || ''},
        leadership:{phases:[],metrics:[],responsibilities:[],copilot:[],boundary:''},career,projects:safeProjects,repositories:repos,gitEvents:[]};
      const details = Object.fromEntries(safeProjects.map(p => [p.id,{path:'',
        markdown:`# ${p.id}｜${p.name}\n\n## 项目概述\n${p.summary || ''}\n\n## 关键工作\n${p.highlights.map(h=>'- '+h).join('\n')}`,
        capabilities:{frontend:[],backend:[],integration:[],collaboration:[],business:[]},
        attachments:$('shareAttachments').checked ? (PROJECT_DETAILS[p.id]?.attachments || []) : []}]));
      const clone = document.documentElement.cloneNode(true);
      // Remove rendered private DOM as well as the raw data; generated scripts contain no profile content.
      for (const id of ['title','subtitle','headline','updatedAt','stats','careerList','projectTimeline','projectGrid','repositoryNote','repoLegend','repoTimeline','repoTable',
          'activityCharts','activityNote','gitEvents','gitEventCount','detailId','detailTitle','detailMeta','detailOverview','detailSources','detailAttachments','detailRecord','detailGitEvents','detailCapabilities','detailPath','detailMarkdown']) clone.querySelector('#'+id).textContent='';
      clone.querySelector('title').textContent=safe.meta.title;
      clone.querySelector('body').classList.remove('modal-open');
      clone.querySelector('#projectDetail').hidden=true;
      clone.querySelector('#projectDetail').setAttribute('aria-hidden','true');
      clone.querySelectorAll('details').forEach(d=>d.removeAttribute('open'));
      clone.querySelectorAll('select').forEach(el=>{while(el.options.length>1) el.remove(1); el.selectedIndex=0;});
      clone.querySelectorAll('input').forEach(el=>{el.value=''; el.removeAttribute('value'); el.checked=false; el.removeAttribute('checked');});
      clone.querySelector('#scopeNote').textContent='公司、项目和代码记录同步筛选';
      clone.querySelector('#gitRecordsSummary').textContent='查看本人提交记录';
      clone.querySelector('#demoNotice').hidden=!safe.meta.synthetic;
      const encoded = value => JSON.stringify(value).replace(/</g,'\\u003c');
      clone.querySelector('#timeline-data').textContent=encoded(safe);
      clone.querySelector('#project-details').textContent=encoded(details);
      clone.querySelector('#fact-source-details').textContent='{}';
      clone.querySelector('#shareResult').hidden=true;
      clone.querySelector('#sharePreview').removeAttribute('srcdoc');
      clone.querySelector('#shareDownload').removeAttribute('href');
      const html='<!doctype html>\n'+clone.outerHTML;
      const previous=$('shareDownload').getAttribute('href');
      if (previous) URL.revokeObjectURL(previous);
      const url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'}));
      $('shareDownload').href=url;
      $('sharePreview').srcdoc=html;
      $('shareResult').hidden=false;
      $('shareDownload').click();
    }
    function renderAll() {
      $('shareResult').hidden=true;
      renderHeader(); renderCareer(); renderProjects(); renderRepositories(); renderGitEvents(); renderActivity();
      $('scopeNote').textContent = $('yearFilter').value ? '日期未知的任职 / 项目仍保留；Git 按作者原始年份筛选，缺少完整记录时标注“已载入”。' : '公司、项目和代码记录同步筛选';
    }

    function bounds(items) {
      const starts = items.map(x => date(x.start)).filter(Boolean);
      const ends = items.map(x => date(x.end)).filter(Boolean);
      return {start: new Date(Math.min(...starts)), end: new Date(Math.max(...ends))};
    }
    function percent(value, span) {
      return ((date(value) - span.start) / (span.end - span.start || 1)) * 100;
    }
    function buildAxis(span, mode = 'year') {
      const axis = document.createElement('div');
      axis.className = 'axis';
      axis.innerHTML = '<div></div><div class="axis-track"></div>';
      const track = axis.lastElementChild;
      if (mode === 'year') {
        for (let y = span.start.getUTCFullYear(); y <= span.end.getUTCFullYear(); y++) {
          const when = new Date(Date.UTC(y, 0, 1));
          const p = Math.max(0, Math.min(100, ((when - span.start) / (span.end - span.start || 1)) * 100));
          track.insertAdjacentHTML('beforeend', `<i class="tick" style="left:${p}%"><span>${y}</span></i>`);
        }
      } else {
        const startYear = span.start.getUTCFullYear();
        for (let cursor = new Date(Date.UTC(startYear, 0, 1)); cursor <= span.end; cursor.setUTCMonth(cursor.getUTCMonth()+3)) {
          if (cursor >= span.start) {
            const p = ((cursor - span.start) / (span.end - span.start || 1)) * 100;
            const label = cursor.getUTCMonth() === 0 ? String(cursor.getUTCFullYear()) : `${cursor.getUTCMonth()+1}月`;
            track.insertAdjacentHTML('beforeend', `<i class="tick" style="left:${p}%"><span>${label}</span></i>`);
          }
        }
      }
      return axis;
    }
    function timelineRow(item, span, color, label, sublabel, projectId = '') {
      const start = percent(item.start, span);
      const width = Math.max(.55, percent(item.end, span) - start);
      const row = document.createElement('div');
      row.className = 'timeline-row';
      const short = width < 10;
      const projectAttrs = projectId ? `data-project-id="${escapeHtml(projectId)}" role="button" tabindex="0" aria-label="查看${escapeHtml(label)}项目详情"` : '';
      row.innerHTML = `
        <div class="row-label"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(sublabel)}</span></div>
        <div class="track"><div class="bar ${short ? 'short' : ''}" ${projectAttrs} data-label="${escapeHtml(item.name)}" style="left:${start}%;width:${width}%;background:${color}" title="${escapeHtml(item.name)}｜${fmt(item.start)}–${rangeEnd(item)}"></div></div>`;
      return row;
    }

    function capabilityBox(title, items) {
      return `<article class="capability-box"><h3>${escapeHtml(title)}</h3>${items.length
        ? `<div class="chips">${items.map(item => `<span class="chip">${escapeHtml(item)}</span>`).join('')}</div>`
        : '<span class="empty-capability">当前项目卡尚未补充</span>'}</article>`;
    }

    // Render a small, escaped Markdown subset. Raw HTML and remote resources stay text.
    function renderProjectRecord(markdown) {
      const output = [];
      let paragraph = [], listOpen = false, code = null;
      const inline = value => escapeHtml(value).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>');
      const flush = () => { if (paragraph.length) { output.push(`<p>${inline(paragraph.join('\n'))}</p>`); paragraph = []; } };
      const closeList = () => { if (listOpen) { output.push('</ul>'); listOpen = false; } };
      for (const line of markdown.split(/\r?\n/)) {
        if (line.startsWith('```')) {
          flush(); closeList();
          if (code === null) code = [];
          else { output.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`); code = null; }
          continue;
        }
        if (code !== null) { code.push(line); continue; }
        if (/^# /.test(line)) { flush(); closeList(); continue; }
        const heading = line.match(/^(#{2,6})\s+(.+)$/);
        const bullet = line.match(/^\s*[-*]\s+(.+)$/);
        if (heading) { flush(); closeList(); const level = heading[1].length === 2 ? 3 : 4; output.push(`<h${level}>${inline(heading[2])}</h${level}>`); }
        else if (bullet) { flush(); if (!listOpen) { output.push('<ul>'); listOpen = true; } output.push(`<li>${inline(bullet[1])}</li>`); }
        else if (!line.trim()) { flush(); closeList(); }
        else { closeList(); paragraph.push(line); }
      }
      flush(); closeList();
      if (code !== null) output.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`);
      return output.join('');
    }

    function openProjectDetail(projectId) {
      const project = DATA.projects.find(item => item.id === projectId);
      const detail = PROJECT_DETAILS[projectId];
      if (!project || !detail) return;
      $('detailId').textContent = `${project.id} · ${project.category} · ${project.nature === 'personal' ? '独立项目' : statusText[project.status] || project.status}`;
      $('detailTitle').textContent = project.name;
      $('detailMeta').textContent = `${project.organization} · ${fmt(project.start)}–${rangeEnd(project)}`;
      $('detailOverview').innerHTML = projectMetrics(project.id) + projectMilestones(project);
      $('detailSources').innerHTML = sourcesMarkup(project.sources);
      $('detailAttachments').innerHTML = (detail.attachments || []).map(a => a.image ? `<figure><img src="${a.url}" alt="${escapeHtml(a.label)}" loading="lazy"><figcaption>${escapeHtml(a.label)}</figcaption></figure>` : `<a href="${a.url}" download="${escapeHtml(a.filename)}">下载 ${escapeHtml(a.label)}</a>`).join('');
      $('detailCapabilities').innerHTML = [
        capabilityBox('前端 / 客户端', detail.capabilities.frontend),
        capabilityBox('项目后端 / 本人参与', detail.capabilities.backend),
        capabilityBox('实时通信 / 设备 / 基础设施', detail.capabilities.integration),
        capabilityBox('研发协作 / 项目工具', detail.capabilities.collaboration),
        capabilityBox('业务能力', detail.capabilities.business),
      ].join('');
      $('detailPath').textContent = detail.path;
      $('detailMarkdown').textContent = detail.markdown;
      $('detailRecord').innerHTML = renderProjectRecord(detail.markdown);
      document.querySelectorAll('.project-extra').forEach(element => element.open = false);
      const projectEvents = viewEvents().filter(e => projectIds(e).includes(projectId)).sort((a,b) => date(b.authorDate) - date(a.authorDate));
      $('detailGit').hidden = !projectEvents.length;
      $('detailGitEvents').innerHTML = projectEvents.slice(0,5).map(event => eventMarkup(event, false)).join('');
      $('detailGitMore').onclick = () => {
        $('gitProject').value = projectId;
        $('gitRepository').value = '';
        $('gitSearch').value = '';
        gitLimit = 30;
        renderGitEvents();
        closeProjectDetail();
        $('gitRecords').open = true;
        $('gitHistory').scrollIntoView({behavior: 'smooth'});
      };
      const modal = $('projectDetail');
      modal.hidden = false;
      modal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-open');
      $('detailClose').focus();
    }

    function closeProjectDetail() {
      const modal = $('projectDetail');
      modal.hidden = true;
      modal.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
    }

    function renderHeader() {
      $('title').textContent = DATA.meta.title;
      $('subtitle').textContent = DATA.meta.subtitle;
      $('headline').textContent = DATA.profile.headline;
      $('updatedAt').textContent = DATA.meta.updatedAt;
      const confirmed = viewProjects().filter(p => p.status !== 'synthetic-draft');
      const repos = viewRepositories();
      const commitCount = repos.reduce((sum, r) => sum + r.count, 0);
      const cards = [
        [new Set(DATA.career.filter(c => inYear(c) && (!$('companyFilter').value || companyOf(c) === $('companyFilter').value)).map(companyOf)).size, '任职公司'],
        [DATA.career.filter(c => inYear(c) && (!$('companyFilter').value || companyOf(c) === $('companyFilter').value)).length, '任职 / 职级阶段'],
        [confirmed.length, '项目数量'],
        [repos.length, '代码仓库'],
        [commitCount.toLocaleString('zh-CN'), repos.some(r=>r.countLabel) ? '已载入本人 Commit' : DATA.meta.synthetic ? '演示本人 Commit' : '本人 Commit']
      ];
      $('stats').innerHTML = cards.map(([v,k]) => `<article class="stat"><strong>${escapeHtml(v)}</strong><span>${escapeHtml(k)}</span></article>`).join('');
      $('demoNotice').hidden = !DATA.meta.synthetic;
    }

    function renderCareer() {
      const entries = [];
      const groups = new Map();
      DATA.career.filter(c => inYear(c) && (!$('companyFilter').value || companyOf(c) === $('companyFilter').value)).forEach(item => {
        if (!item.groupOrganization) {
          entries.push({items: [item]});
          return;
        }
        if (!groups.has(item.groupOrganization)) {
          const group = {organization: item.groupOrganization, items: []};
          groups.set(item.groupOrganization, group);
          entries.push(group);
        }
        groups.get(item.groupOrganization).items.push(item);
      });
      $('careerList').innerHTML = entries.map(entry => {
        if (entry.organization) {
          const phases = [...entry.items].sort((a, b) => (a.start || '9999').localeCompare(b.start || '9999'));
          const roles = [...new Set(phases.map(item => item.role + (item.level ? ' · ' + item.level : '')))];
          const starts = phases.map(item => item.start).filter(Boolean).sort();
          const ends = phases.map(item => item.end).filter(Boolean).sort();
          return `<article class="career-item career-company">
            <header class="career-company-head">
              <div><h3>${escapeHtml(entry.organization)}</h3><p><strong>${escapeHtml(roles.join(' → '))}</strong></p></div>
              <div class="career-date">${fmt(starts[0])} — ${fmt(ends[ends.length - 1])}</div>
            </header>
            <ol class="career-phases" aria-label="公司内部阶段">${phases.map(item => `
              <li class="career-phase">
                <time>${fmt(item.start)} — ${fmt(item.end)}</time>
                <div><h4>${escapeHtml(item.role)}${item.level ? ' · ' + escapeHtml(item.level) : ''}</h4><p>${escapeHtml(item.organization)} · ${escapeHtml(item.summary)}</p>${sourcesMarkup(item.sources)}</div>
              </li>`).join('')}</ol>
          </article>`;
        }
        const item = entry.items[0];
        return `
        <article class="career-item">
          <div class="career-date">${fmt(item.start)}<br>— ${fmt(item.end)}</div>
          <div><h3>${escapeHtml(item.organization)}</h3><p><strong>${escapeHtml(item.role)}${item.level ? ' · ' + escapeHtml(item.level) : ''}</strong> · ${escapeHtml(item.summary)}</p>${sourcesMarkup(item.sources)}</div>
        </article>`;
      }).join('');
    }

    function projectMetrics(projectId) {
      const repos = viewRepositories().filter(r => projectIds(r).includes(projectId) || projectId in (r.projectCounts || {}));
      const commits = repos.reduce((total,r) => {
        if ($('yearFilter').value) return total + viewEvents().filter(e => e.repository === r.name && projectIds(e).includes(projectId)).length;
        return total + (r.projectCounts?.[projectId] ?? (r.projectId === projectId ? r.count : viewEvents().filter(e => e.repository === r.name && projectIds(e).includes(projectId)).length));
      },0);
      return `<div class="project-metrics"><span><strong>${repos.length}</strong> 关联仓库</span><span><strong>${commits.toLocaleString('zh-CN')}</strong> ${$('yearFilter').value ? '已载入本人 Commit' : '本人 Commit'}</span></div>`;
    }
    function projectMilestones(project) {
      return (project.milestones || []).length ? `<ol class="project-milestones">${project.milestones.map(m => `<li><time>${escapeHtml(m.date || '时间待确认')}</time><div><strong>${escapeHtml(m.title)}</strong>${m.summary ? `<p>${escapeHtml(m.summary)}</p>` : ''}${m.status === 'pending' ? '<span class="tag">待确认</span>' : ''}</div></li>`).join('')}</ol>` : '';
    }
    function filteredProjects() {
      const q = $('search').value.trim().toLowerCase();
      const category = $('category').value;
      return viewProjects().filter(p => {
        if (category && p.category !== category) return false;
        const haystack = [p.name,p.organization,p.category,p.summary,...p.tech,...p.highlights].join(' ').toLowerCase();
        return !q || haystack.includes(q);
      });
    }
    function renderProjects() {
      const items = filteredProjects();
      const dated = items.filter(p => p.start && p.end);
      const timeline = $('projectTimeline');
      timeline.innerHTML = '';
      if (dated.length) {
        const span = bounds(dated);
        timeline.appendChild(buildAxis(span, 'year'));
        dated.sort((a,b) => a.start.localeCompare(b.start)).forEach(p => {
          const row = timelineRow(p, span, hashColor(p.category), p.name, `${p.organization} · ${fmt(p.start)}–${rangeEnd(p)}`, p.id);
          timeline.appendChild(row);
        });
      } else {
        timeline.innerHTML = '<div class="empty">没有符合当前筛选条件且带时间的项目。</div>';
      }
      const grid = $('projectGrid');
      if (!items.length) {
        grid.innerHTML = '<div class="empty">没有符合当前筛选条件的项目。</div>';
        return;
      }
      grid.innerHTML = items.map(p => `
        <article class="project-card" data-project-id="${escapeHtml(p.id)}">
          <div class="card-top"><span>${escapeHtml(p.id)} · ${escapeHtml(p.category)}</span><span class="tag ${escapeHtml(p.status)}">${p.nature === 'personal' ? '独立项目' : (statusText[p.status] || escapeHtml(p.status))}</span></div>
          <h3>${escapeHtml(p.name)}</h3>
          <p>${escapeHtml(p.summary)}</p>
          ${projectMetrics(p.id)}
          ${projectMilestones(p)}
          <p class="meta">${escapeHtml(p.organization)}<br>${fmt(p.start)} – ${rangeEnd(p)}</p>
          ${p.url ? `<a class="project-link" href="${escapeHtml(p.url)}" target="_blank" rel="noreferrer">访问线上项目 ↗</a>` : ''}
          <div class="chips">${p.tech.map(t => `<span class="chip">${escapeHtml(t)}</span>`).join('')}</div>
          <button class="detail-link" type="button" data-project-id="${escapeHtml(p.id)}">查看项目详情 →</button>
        </article>`).join('');
    }

    function renderRepositories() {
      const items = [...viewRepositories()].sort((a,b) => date(a.start)-date(b.start));
      const span = bounds(items);
      const groups = [...new Set(items.map(r => r.group))];
      $('repositoryNote').textContent = DATA.meta.repositoryNote || '按本人署名统计本地仓库活动，提交日期只表示代码活动。';
      $('repoLegend').innerHTML = groups.map(g => `<span class="pill" style="color:${hashColor(g)}"><i class="dot"></i>${escapeHtml(g)}</span>`).join('');
      const timeline = $('repoTimeline');
      timeline.innerHTML = '';
      if (items.length) timeline.appendChild(buildAxis(span, 'quarter'));
      else timeline.innerHTML = '<div class="empty">尚未录入仓库活动。</div>';
      let current = '';
      items.forEach(repo => {
        if (repo.group !== current) {
          current = repo.group;
          const heading = document.createElement('div');
          heading.className = 'repo-group';
          heading.textContent = current;
          timeline.appendChild(heading);
        }
        timeline.appendChild(timelineRow(repo, span, hashColor(repo.group), repo.name, `${repo.countLabel || ''}${repo.count} 次 · ${fmt(repo.start)}–${fmt(repo.end)}`));
      });
      $('repoTable').innerHTML = items.map(r => `
        <tr>
          <td><strong>${escapeHtml(r.name)}</strong></td>
          <td class="count">${r.countLabel || ''}${r.count.toLocaleString('zh-CN')}</td>
          <td>${fmt(r.start)}<small>${escapeHtml(r.firstMessage)}</small></td>
          <td>${fmt(r.end)}<small>${escapeHtml(r.lastMessage)}</small></td>
          <td>${duration(r.start, r.end)}</td>
        </tr>`).join('');
    }

    let gitLimit = 30;
    function eventMarkup(event, showProject = true) {
      const projects = DATA.projects.filter(p => projectIds(event).includes(p.id));
      return `<li class="git-event">
        <time>${fmt(event.authorDate)} · ${escapeHtml(event.repository)}${DATA.meta.synthetic ? ' · 演示提交' : ''}</time>
        <h3>${escapeHtml(event.subject)}</h3>
        ${showProject ? projects.map(project => `<button class="event-project" type="button" data-project-id="${escapeHtml(project.id)}">${escapeHtml(project.name)}</button>`).join(' · ') : ''}
        <details><summary>原始提交信息</summary><p>${escapeHtml(event.subject)}</p><code>${escapeHtml(event.sha)}</code><p>作者记录时间：${escapeHtml(event.authorDate)}<br>提交写入时间：${escapeHtml(event.committerDate)}</p>${event.files?.length ? `<p>修改文件：${event.files.map(escapeHtml).join('、')}</p>` : ''}</details>
      </li>`;
    }
    function renderGitEvents() {
      const query = $('gitSearch').value.trim().toLowerCase();
      const project = $('gitProject').value;
      const repository = $('gitRepository').value;
      const events = viewEvents().filter(e => (!project || projectIds(e).includes(project))
        && (!repository || e.repository === repository)
        && (!query || [e.subject,e.title,e.repository].join(' ').toLowerCase().includes(query)))
        .sort((a,b) => date(b.authorDate) - date(a.authorDate) || a.id.localeCompare(b.id));
      $('gitEventCount').textContent = `匹配 ${events.length} 条本人提交 · 按作者记录时间倒序`;
      $('gitEvents').innerHTML = events.length ? events.slice(0,gitLimit).map(event => eventMarkup(event)).join('') : '<li class="empty">没有匹配的本人提交。</li>';
      $('gitMore').hidden = events.length <= gitLimit;
    }

    function init() {
      const companies = new Set([...DATA.career.map(companyOf), ...DATA.projects.map(companyOf)]);
      [...companies].sort().forEach(c => $('companyFilter').appendChild(new Option(c,c)));
      const years = new Set();
      for (const item of [...DATA.career,...DATA.projects,...DATA.repositories]) {
        if (item.start && item.end) for (let y=Number(item.start.slice(0,4)); y<=Number(item.end.slice(0,4)) && years.size < 500; y++) years.add(String(y));
      }
      [...years].sort().reverse().forEach(y => $('yearFilter').appendChild(new Option(y,y)));
      for (const id of ['companyFilter','yearFilter']) $(id).addEventListener('change', () => {gitLimit=30; renderAll();});
      $('downloadShare').addEventListener('click',downloadShare);
      $('resetFilters').addEventListener('click', () => {
        for (const id of ['companyFilter','yearFilter','search','category','gitProject','gitRepository','gitSearch']) $(id).value='';
        gitLimit=30; renderAll();
      });
      $('gitHistory').hidden = !(DATA.gitEvents || []).length;
      $('gitRecordsSummary').textContent = `查看本人提交记录（${(DATA.gitEvents || []).length} 条已载入）`;
      for (const project of DATA.projects) {
        const option = new Option(project.name, project.id);
        $('gitProject').appendChild(option);
      }
      for (const repository of DATA.repositories) $('gitRepository').appendChild(new Option(repository.name,repository.name));
      for (const id of ['gitProject','gitRepository','gitSearch']) $(id).addEventListener(id === 'gitSearch' ? 'input' : 'change', () => {gitLimit = 30; renderGitEvents();});
      $('gitMore').addEventListener('click', () => {gitLimit += 30; renderGitEvents();});
      [...new Set(DATA.projects.map(p => p.category))].sort().forEach(value => {
        const option = document.createElement('option'); option.value = value; option.textContent = value; $('category').appendChild(option);
      });
      ['search','category'].forEach(id => $(id).addEventListener(id === 'search' ? 'input' : 'change', renderProjects));
      document.querySelector('main').addEventListener('click', event => {
        if (event.target.closest('a')) return;
        const trigger = event.target.closest('[data-project-id]');
        if (trigger) openProjectDetail(trigger.dataset.projectId);
      });
      $('projects').addEventListener('keydown', event => {
        if (!['Enter',' '].includes(event.key)) return;
        const trigger = event.target.closest('[data-project-id]');
        if (!trigger) return;
        event.preventDefault();
        openProjectDetail(trigger.dataset.projectId);
      });
      document.querySelectorAll('[data-close-detail]').forEach(button => button.addEventListener('click', closeProjectDetail));
      document.addEventListener('keydown', event => { if (event.key === 'Escape' && !$('projectDetail').hidden) closeProjectDetail(); });
      renderAll();
    }
    init();
  </script>
</body>
</html>
'''


def validate_data(data):
    """Validate data consumed by the HTML, allowing an empty starter."""
    if not isinstance(data, dict):
        raise ValueError('Timeline must be an object')
    for key in ('meta', 'profile', 'leadership'):
        if not isinstance(data.get(key), dict):
            raise ValueError(f'{key} must be an object')
    for key in ('title', 'subtitle', 'updatedAt'):
        if not isinstance(data['meta'].get(key), str):
            raise ValueError(f'meta.{key} must be a string')
    if 'synthetic' in data['meta'] and type(data['meta']['synthetic']) is not bool:
        raise ValueError('meta.synthetic must be a boolean')
    for key in ('careerStart', 'careerEnd', 'headline'):
        if not isinstance(data['profile'].get(key), str):
            raise ValueError(f'profile.{key} must be a string')
    for key in ('phases', 'metrics', 'responsibilities', 'copilot'):
        if not isinstance(data['leadership'].get(key), list):
            raise ValueError(f'leadership.{key} must be an array')
    for key in ('responsibilities', 'copilot'):
        if any(not isinstance(value, str) for value in data['leadership'][key]):
            raise ValueError(f'leadership.{key} entries must be strings')
    if not isinstance(data['leadership'].get('boundary'), str):
        raise ValueError('leadership.boundary must be a string')
    for collection, fields in (('phases', ('period', 'value', 'label')),
                               ('metrics', ('value', 'label'))):
        for record in data['leadership'][collection]:
            if not isinstance(record, dict) or any(not isinstance(record.get(k), str) for k in fields):
                raise ValueError(f'Invalid leadership.{collection} entry')

    def check_dates(record, label):
        dates = []
        for key in ('start', 'end'):
            value = record.get(key)
            if value in (None, ''):
                dates.append(None)
            else:
                if not isinstance(value, str):
                    raise ValueError(f'{label}.{key} must be an ISO date')
                try:
                    dates.append(parse_iso_datetime(value))
                except ValueError:
                    raise ValueError(f'{label}.{key} must be an ISO date') from None
        if bool(dates[0]) != bool(dates[1]):
            raise ValueError(f'{label} needs both dates or neither')
        if dates[0]:
            try:
                if dates[0] > dates[1]:
                    raise ValueError(f'{label} start is after end')
            except TypeError:
                raise ValueError(f'{label} dates must use consistent timezones') from None

    check_dates({'start': data['profile']['careerStart'], 'end': data['profile']['careerEnd']}, 'profile')
    required = {
        'career': ('id', 'organization', 'role', 'summary'),
        'projects': ('id', 'name', 'organization', 'category', 'status'),
        'repositories': ('name', 'group'),
    }
    allowed = {'confirmed', 'resume-supported'}
    for collection, fields in required.items():
        records = data.get(collection)
        if not isinstance(records, list):
            raise ValueError(f'{collection} must be an array')
        values = []
        for record in records:
            if not isinstance(record, dict) or any(not isinstance(record.get(k), str) for k in fields):
                raise ValueError(f'Invalid {collection} entry')
            identity = record[fields[0]]
            if not identity:
                raise ValueError(f'{collection} identity must be nonempty')
            values.append(identity)
            check_dates(record, f'{collection}/{identity}')
            if collection == 'career' and 'level' in record and not isinstance(record['level'], str):
                raise ValueError(f'{identity}.level must be a string')
            if collection == 'career' and 'groupOrganization' in record:
                group = record['groupOrganization']
                if not isinstance(group, str) or not group.strip():
                    raise ValueError(f'{identity}.groupOrganization must be a nonempty string')
            if collection == 'projects':
                milestones = record.get('milestones', [])
                if not isinstance(milestones, list):
                    raise ValueError(f'{identity}.milestones must be an array')
                for milestone in milestones:
                    if not isinstance(milestone, dict) or not isinstance(milestone.get('title'), str):
                        raise ValueError(f'{identity} milestone needs a title')
                    for key in ('date', 'summary'):
                        if key in milestone and not isinstance(milestone[key], str):
                            raise ValueError(f'{identity} milestone {key} must be a string')
                if 'nature' in record and not isinstance(record['nature'], str):
                    raise ValueError(f'{identity}.nature must be a string')
                if not re.fullmatch(r'[PO]\d{2,}', identity):
                    raise ValueError(f'Invalid project ID: {identity}')
                if record['status'] not in allowed:
                    raise ValueError(f'Non-factual project must not be in the active timeline: {identity}')
                for key in ('tech', 'highlights', 'projectBackend', 'collaboration'):
                    items = record.get(key, [])
                    if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
                        raise ValueError(f'{identity}.{key} must be an array of strings')
                if 'tech' not in record or 'highlights' not in record:
                    raise ValueError(f'{identity} needs tech and highlights arrays (may be empty)')
                if record.get('url'):
                    if not isinstance(record['url'], str):
                        raise ValueError(f'{identity}.url must be a string')
                    url = urlsplit(record['url'])
                    if url.scheme not in {'http', 'https'} or not url.netloc:
                        raise ValueError(f'{identity}.url must be an HTTP(S) URL')
            if collection == 'repositories':
                if not record.get('start') or not record.get('end'):
                    raise ValueError(f'Repository dates are required: {identity}')
                if type(record.get('count')) is not int or record['count'] < 1:
                    raise ValueError(f'Repository count must be positive: {identity}')
        if len(values) != len(set(values)):
            raise ValueError(f'{collection} identities must be unique')

    for collection in ('career', 'projects'):
        for record in data[collection]:
            confirmed = record.get('confirmedFields', [])
            if not isinstance(confirmed, list) or any(not isinstance(v, str) for v in confirmed):
                raise ValueError('confirmedFields must contain field names.')
            sources = record.get('sources', [])
            if not isinstance(sources, list):
                raise ValueError('Sources must be an array.')
            for source in sources:
                if not isinstance(source, dict) or any(not isinstance(source.get(k), str) for k in ('field', 'label', 'status')):
                    raise ValueError('Source requires field, label and status strings.')
                if source['status'] not in {'confirmed', 'resume-supported', 'git', 'pending'}:
                    raise ValueError('Invalid source status.')
                for key in ('path', 'excerpt'):
                    if key in source and not isinstance(source[key], str):
                        raise ValueError('Source path/excerpt must be a string.')
            if collection == 'projects':
                attachments = record.get('attachments', [])
                if not isinstance(attachments, list):
                    raise ValueError('Attachments must be an array.')
                for item in attachments:
                    if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k] for k in ('path', 'label')):
                        raise ValueError('Attachment requires a local path and label.')
    projects = {p['id'] for p in data['projects']}
    if not isinstance(data.get('gitEvents', []), list):
        raise ValueError('gitEvents must be an array')
    for collection in ('repositories', 'gitEvents'):
        for record in data.get(collection, []):
            if not isinstance(record.get('projectIds', []), list) or any(not isinstance(p, str) or p not in projects for p in record.get('projectIds', [])):
                raise ValueError('projectIds must reference existing projects.')
            if record.get('projectId') and record['projectId'] not in projects:
                raise ValueError('Repository/event projectId must reference an existing project.')
            if collection == 'repositories':
                counts = record.get('projectCounts', {})
                if not isinstance(counts, dict) or any(p not in projects or type(c) is not int or not 0 <= c <= record['count'] for p, c in counts.items()):
                    raise ValueError('Project counts must be bounded by repository count.')
                stats = record.get('activity', {})
                if not isinstance(stats, dict):
                    raise ValueError('Activity must be an object.')
                for field in ('monthly', 'modules', 'types'):
                    values = stats.get(field, {})
                    if not isinstance(values, dict) or any(not isinstance(k, str) or type(v) is not int or v < 0 for k, v in values.items()):
                        raise ValueError('Activity histogram must contain nonnegative integer counts.')
                    if field == 'monthly' and any(not re.fullmatch(r'\d{4}-(?:0[1-9]|1[0-2])', k) for k in values):
                        raise ValueError('Activity months must use YYYY-MM.')
                    if field == 'monthly' and values and sum(values.values()) != record['count']:
                        raise ValueError('Monthly count must match repository count.')
    career_ids = {c['id'] for c in data['career']}
    for record in data['projects']:
        if not isinstance(record.get('careerIds', []), list) or any(not isinstance(c, str) or c not in career_ids for c in record.get('careerIds', [])):
            raise ValueError('careerIds must reference career stages.')
    repositories = {r['name']: r for r in data['repositories']}
    records = data.get('gitEvents', [])
    if not isinstance(records, list):
        raise ValueError('gitEvents must be an array')
    ids, seen_commits = set(), set()
    for record in records:
        fields = ('id', 'repository', 'sha', 'subject', 'authorDate', 'committerDate')
        if not isinstance(record, dict) or any(not isinstance(record.get(k), str) for k in fields):
            raise ValueError('Invalid gitEvents entry')
        if not record['id'] or record['id'] in ids:
            raise ValueError('Git event IDs must be nonempty and unique')
        ids.add(record['id'])
        pid = record.get('projectId', '')
        if not isinstance(pid, str) or pid and pid not in projects:
            raise ValueError('Git event projectId must reference an existing project')
        if record['repository'] not in repositories:
            raise ValueError('Git event must reference an existing repository')
        if not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', record['sha']):
            raise ValueError('Git event needs a full commit SHA')
        key = (record['repository'], record['sha'])
        if key in seen_commits:
            raise ValueError('Duplicate Git commit in the same repository')
        seen_commits.add(key)
        for field in ('authorDate', 'committerDate'):
            try:
                parsed = parse_iso_datetime(record[field])
                if parsed.tzinfo is None:
                    raise ValueError()
            except ValueError:
                raise ValueError('Git event dates must include a timezone') from None
        if not isinstance(record.get('files', []), list) or any(not isinstance(p, str) for p in record.get('files', [])):
            raise ValueError('Git event files must be strings.')
        repo = repositories[record['repository']]
        try:
            authored = parse_iso_datetime(record['authorDate'])
            if not parse_iso_datetime(repo['start']) <= authored <= parse_iso_datetime(repo['end']):
                raise ValueError('Git event author date is outside repository activity')
        except TypeError:
            raise ValueError('Git events and repository activity must use consistent timezones') from None


def classify_capabilities(tech):
    """Group existing timeline tags for review; never invent missing capabilities."""
    frontend_markers = (
        "vue", "react", "angular", "next", "nuxt", "javascript", "typescript",
        "ant design", "element", "umi", "vux", "electron", "flutter", "webgl",
        "canvas", "fabric", "tradingview", "bizcharts", "echarts", "微信小程序",
        "uniapp", "uni-app",
    )
    backend_markers = (
        "node", "fastify", "fastapi", "python", "go /", "gin", "java", "spring",
        "postgresql", "mysql", "redis", "oauth", "jwt", "rbac", "swagger", "crud",
    )
    integration_markers = (
        "websocket", "sse", "mqtt", "hls", "rtmp", "rtsp", "docker", "helm",
        "js bridge", "walletconnect", "evm", "web3", "传感器", "机器人", "设备",
        "支付", "sdk", "后台 mqtt", "物联网",
    )
    groups = {"frontend": [], "backend": [], "integration": []}
    for value in tech:
        lowered = value.lower()
        if lowered == "web" or any(marker in lowered for marker in frontend_markers):
            groups["frontend"].append(value)
        elif any(marker in lowered for marker in backend_markers):
            groups["backend"].append(value)
        elif any(marker in lowered for marker in integration_markers):
            groups["integration"].append(value)
        else:
            groups["integration"].append(value)
    return groups


def embedded_attachment(root, item):
    path = checked_local(root, item['path'])
    raw = path.read_bytes()
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('Attachment exceeds 2 MiB; resize it first.')
    suffix = path.suffix.lower()
    types = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
             '.webp': 'image/webp', '.pdf': 'application/pdf', '.txt': 'text/plain', '.md': 'text/plain'}
    if suffix not in types:
        raise ValueError('Use PNG/JPEG/WebP/PDF/text attachments; active SVG/HTML is not embedded.')
    valid = (suffix == '.png' and raw.startswith(b'\x89PNG\r\n\x1a\n') or
             suffix in {'.jpg', '.jpeg'} and raw.startswith(b'\xff\xd8\xff') or
             suffix == '.webp' and raw.startswith(b'RIFF') and raw[8:12] == b'WEBP' or
             suffix == '.pdf' and raw.startswith(b'%PDF-') or suffix in {'.txt', '.md'})
    if not valid:
        raise ValueError('Attachment bytes do not match the declared file type.')
    if suffix in {'.txt', '.md'}:
        raw.decode('utf-8')
    return {'label': item['label'], 'filename': path.name, 'image': types[suffix].startswith('image/'),
            'url': 'data:' + types[suffix] + ';base64,' + base64.b64encode(raw).decode('ascii')}


def embed_sources(data, root):
    snapshots = {}
    for collection in ('career', 'projects'):
        for record in data[collection]:
            for source in record.get('sources', []):
                if source.get('path'):
                    path = checked_local(root, source['path'])
                    if path.suffix.lower() not in {'.md', '.txt', '.json'} or path.stat().st_size > 1024 * 1024:
                        raise ValueError('Use a bounded extracted text snapshot as a source.')
                    snapshots[source['path']] = path.read_text(encoding='utf-8')[:16000]
    return snapshots


def build_project_details(data, root=ROOT):
    root = Path(root).resolve()
    cards = {}
    total_asset_bytes = 0
    for path in (root / "references/projects").glob("*.md"):
        path = checked_local(root, path.relative_to(root).as_posix())
        markdown = path.read_text(encoding="utf-8")
        match = re.match(r"# ([PO]\d{2,})｜", markdown)
        if match:
            cards[match.group(1)] = {
                "path": str(path.relative_to(root)),
                "markdown": markdown,
            }
    details = {}
    for project in data["projects"]:
        project_id = project["id"]
        if project_id not in cards:
            raise ValueError(f"Missing Markdown project card for timeline detail: {project_id}")
        capabilities = classify_capabilities(project.get("tech", []))
        project_backend = project.get("projectBackend", [])
        participation = project.get("backendParticipation")
        backend_context = []
        if project_backend:
            backend_context.append("项目后端：" + "、".join(project_backend))
        if participation:
            backend_context.append("参与边界：" + participation)
        capabilities["backend"] = backend_context + capabilities["backend"]
        capabilities["collaboration"] = project.get("collaboration", [])
        capabilities["business"] = project.get("highlights", [])
        attachments = [embedded_attachment(root, a) for a in project.get('attachments', [])]
        total_asset_bytes += sum(len(a['url']) for a in attachments)
        if total_asset_bytes > 16 * 1024 * 1024:
            raise ValueError('Embedded attachments exceed the page size budget.')
        details[project_id] = {**cards[project_id], "capabilities": capabilities, 'attachments': attachments}
    return details


def encode_json_for_html(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def render_html(data, details, sources=None):
    return (HTML.replace('__PAGE_TITLE__', escape(data['meta']['title']))
            .replace('__TIMELINE_DATA__', encode_json_for_html(data))
            .replace('__PROJECT_DETAILS__', encode_json_for_html(details))
            .replace('__SOURCE_DETAILS__', encode_json_for_html(sources or {})))


def build(root=ROOT, output=None):
    from career_data import profile_root
    root = profile_root(root)
    target = Path(output) if output else root / 'showcase/project-timeline.html'
    data = json.loads((root / 'data/timeline.json').read_text(encoding='utf-8'))
    validate_data(data)
    details = build_project_details(data, root)
    data = copy.deepcopy(data)
    sources = embed_sources(data, root)
    page = render_html(data, details, sources)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding='utf-8')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Optional output HTML path')
    args = parser.parse_args()
    try:
        target = build(output=args.output)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    print(f'Created {target} ({target.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
