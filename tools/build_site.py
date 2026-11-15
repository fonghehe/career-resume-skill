#!/usr/bin/env python3
"""Build offline personal pages from the public fictional multi-profession examples.

Sources live in examples/professions/. Generated HTML is written to
docs/public/demo/professions/ by scripts/career.py demo --docs and never committed.
No personal local/ records, network resources or binary exports are read.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import posixpath
import re
import shutil
import tempfile

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from career_resume.build_timeline import build as build_timeline
from career_resume.build_career import build as build_career
from career_resume.bundle import (PROFESSION_EXTRA_FILES, PROFESSION_FILES, PROFESSION_SLUGS,
                    checked_file)
from career_resume.cli_support import fail
from career_resume.file_io import atomic_write
from career_resume.export_resume import export as export_resume

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = 'examples/professions'
PALETTE = 'assets/themes/palette.json'

NOTICE = '虚构教学示例 · 人物、单位、经历与案例均为设定，不属于使用者，不可用于真实投递'

LINK = re.compile(r'\[([^\]]+)\]\(<?([^)\s>]+)>?(?:\s+"[^"]*")?\)')
BOLD = re.compile(r'\*\*(.+?)\*\*')
CODE = re.compile(r'`([^`]+)`')
TABLE_RULE = re.compile(r'^\|[\s:|-]+\|$')

SITE_CSS = """
:root{--ink:#233039;--muted:#59636a;--line:#dce2e1;--paper:#fff;--accent:#2E79A6;--tint:#EDF6FC}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:88px}
body{margin:0;background:#fafbf9;color:var(--ink);font-family:Arial,"PingFang SC","Hiragino Sans GB",sans-serif;font-size:15px;line-height:1.85}
a{color:inherit;text-decoration:none}button{font:inherit;cursor:pointer}
a:focus-visible,button:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
.shell{width:min(1120px,calc(100% - 72px));margin:auto}
.notice{background:var(--tint);color:var(--accent);font-size:12px;padding:9px 20px;text-align:center;letter-spacing:.03em}
.nav{position:sticky;top:0;z-index:20;background:#fafbf9f2;backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.nav .shell{display:flex;align-items:center;justify-content:space-between;gap:24px;min-height:70px;flex-wrap:wrap}
.brand{font-size:17px;font-weight:700;letter-spacing:.08em}.brand small{font-size:11px;letter-spacing:.03em;color:var(--muted);margin-left:12px;font-weight:400}
.links{display:flex;gap:20px;align-items:center;font-size:13px;flex-wrap:wrap}.links a:hover{color:var(--accent)}
.hero{padding:76px 0 64px;display:grid;grid-template-columns:1.1fr .9fr;gap:56px;align-items:center}
.eyebrow{font-size:11px;letter-spacing:.15em;color:var(--accent);font-weight:700}
h1{font-size:clamp(30px,3.6vw,48px);line-height:1.4;letter-spacing:-.04em;margin:22px 0;white-space:pre-line;font-weight:650}
.intro{color:var(--muted);line-height:2;max-width:560px}
.buttons{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}
.btn{display:inline-flex;align-items:center;gap:12px;padding:10px 19px;border:1px solid var(--line);border-radius:7px;background:var(--paper);font-size:13px}
.btn.primary{background:var(--accent);color:#fff;border-color:var(--accent)}.btn:hover{filter:brightness(.96)}
.visual{background:var(--tint);border:1px solid var(--line);border-radius:16px;padding:30px}
.visual .eyebrow{margin-bottom:18px}.visual ol{padding-left:20px;margin:0;color:var(--muted)}
.visual li{margin:9px 0}.visual .caption{margin-top:20px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:14px}
.strip{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.strip div{padding:17px 12px}.strip div+div{border-left:1px solid var(--line)}
.strip span{display:block;font-size:11px;color:var(--muted);letter-spacing:.08em}.strip strong{font-size:14px}
.section{padding:52px 0;border-bottom:1px solid var(--line)}
.section-head{display:flex;justify-content:space-between;gap:30px;align-items:end;margin-bottom:26px}
.section-head h2{font-size:26px;margin:8px 0 0;letter-spacing:-.02em}.section-head p{color:var(--muted);font-size:13px;margin:0;max-width:460px}
.count{font-size:11px;letter-spacing:.13em;color:var(--accent);font-weight:700}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.card{border:1px solid var(--line);border-radius:10px;background:var(--paper);padding:22px;display:flex;flex-direction:column;gap:10px}
.card .category{font-size:11px;color:var(--accent);letter-spacing:.08em}.card h3{font-size:17px;margin:0;line-height:1.5}
.card time{font-size:12px;color:var(--muted)}.card p{font-size:13px;color:var(--muted);margin:0;flex:1}
.tags{display:flex;gap:6px;flex-wrap:wrap}.tag{font-size:11px;background:var(--tint);color:var(--accent);padding:3px 9px;border-radius:20px}
.text-btn{background:none;border:0;border-bottom:1px solid var(--accent);color:var(--accent);padding:0 0 2px;font-size:13px;align-self:flex-start}
.two-col{display:grid;grid-template-columns:.85fr 1.15fr;gap:46px}
.steps{display:grid;grid-template-columns:1fr 1fr;gap:16px}.step{border:1px solid var(--line);border-radius:9px;padding:18px;background:var(--paper)}
.step .num{font-size:11px;color:var(--accent);font-weight:700;letter-spacing:.1em}.step h3{font-size:15px;margin:7px 0}.step p{font-size:13px;color:var(--muted);margin:0}
.job{border-left:2px solid var(--line);padding:2px 0 22px 22px;margin-bottom:20px}.job:last-child{margin-bottom:0}
.job-head{display:flex;justify-content:space-between;gap:16px;align-items:baseline}.job h3{font-size:17px;margin:0}.job time{font-size:12px;color:var(--muted);white-space:nowrap}
.job .role{font-size:13px;color:var(--accent);margin:5px 0}.job p,.job li{font-size:13px;color:var(--muted)}.job ul{margin:8px 0 0;padding-left:19px}
.more{display:grid;grid-template-columns:1fr 1fr;gap:40px}.more h3{font-size:18px;margin:8px 0}.more p,.more li{font-size:13px;color:var(--muted)}
.contact{margin:46px 0 30px;background:var(--tint);border-radius:12px;padding:30px;display:flex;justify-content:space-between;gap:24px;align-items:center;flex-wrap:wrap}
.contact h2{font-size:22px;margin:8px 0}.contact p{font-size:13px;color:var(--muted);margin:0}
.footer{padding:22px 0 40px;font-size:12px;color:var(--muted);display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}
dialog{border:1px solid var(--line);border-radius:12px;max-width:620px;width:calc(100% - 40px);padding:30px;line-height:1.85}
dialog::backdrop{background:#23303988}dialog h2{font-size:22px;margin:8px 0}dialog h3{font-size:15px;margin:20px 0 6px}
dialog p,dialog li{font-size:14px;color:var(--muted)}dialog ul{padding-left:20px}
.close{float:right;background:none;border:0;font-size:24px;line-height:1;color:var(--muted)}
.doc{max-width:820px;padding:40px 0 70px}.doc h1{font-size:32px;margin:14px 0 8px;white-space:normal}
.doc h2{font-size:22px;margin:34px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.doc h3{font-size:17px;margin:24px 0 8px}.doc h4,.doc h5{font-size:15px;margin:18px 0 6px}
.doc p,.doc li{font-size:14px;line-height:1.9}.doc ul,.doc ol{padding-left:22px}
.doc blockquote{margin:16px 0;padding:10px 18px;background:var(--tint);border-left:3px solid var(--accent);color:var(--muted)}
.doc table{border-collapse:collapse;width:100%;margin:18px 0;font-size:13px}
.doc th,.doc td{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}
.doc th{background:var(--tint)}.doc code{background:#f1f3f2;padding:1px 5px;border-radius:3px;font-size:13px}
.doc pre{background:#f1f3f2;padding:14px;overflow:auto;border-radius:7px}.doc pre code{background:none}
.doc a{color:var(--accent);border-bottom:1px solid var(--tint)}.doc hr{border:0;border-top:1px solid var(--line);margin:28px 0}
.lead{color:var(--muted);font-size:13px;margin:0 0 24px}
.gallery-hero{padding:62px 0 34px}.gallery-hero h1{font-size:clamp(30px,4vw,48px);margin:16px 0}.gallery-hero p{color:var(--muted);max-width:680px}
.gallery-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin:24px 0 60px}
.gallery-card{border:1px solid var(--line);border-radius:11px;background:var(--paper);overflow:hidden}
.gallery-art{height:9px;background:var(--tint);border-bottom:1px solid var(--line)}
.gallery-body{padding:24px}.gallery-body .eyebrow{font-size:10px}.gallery-body h2{font-size:22px;margin:9px 0 4px}
.gallery-body .role{font-size:12px;color:var(--muted)}.gallery-body p{font-size:13px;color:var(--muted);min-height:44px}
.gallery-links{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--accent);margin-top:16px}
@media(max-width:900px){.shell{width:calc(100% - 44px)}.hero,.two-col,.more{grid-template-columns:1fr;gap:26px}.cards,.gallery-grid,.steps{grid-template-columns:1fr 1fr}.section-head{display:block}}
@media(max-width:600px){.shell{width:calc(100% - 32px)}.hero{padding:38px 0}.cards,.gallery-grid,.steps,.strip,.more{grid-template-columns:1fr}.strip div+div{border-left:0;border-top:1px solid var(--line)}.nav .shell{padding:12px 0;gap:8px}.links{gap:12px;font-size:12px}.job-head{display:block}.contact{padding:22px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{.nav,.notice,.buttons,.contact,.footer,.text-btn{display:none}.hero,.section{padding:20px 0}.shell{width:100%}.visual,.cards{display:none}}
"""

DIALOG_JS = """
document.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>document.getElementById(b.dataset.open).showModal()));
document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>b.closest('dialog').close()));
document.querySelectorAll('dialog').forEach(d=>d.addEventListener('click',ev=>{const r=d.getBoundingClientRect();if(ev.clientX<r.left||ev.clientX>r.right||ev.clientY<r.top||ev.clientY>r.bottom)d.close()}));
"""


def esc(value):
    return html.escape(str(value), quote=True)


def resolve_link(href, base):
    """Resolve a Markdown link relative to the generated page directory."""
    if href.startswith(('#', 'mailto:')):
        return href
    if href.startswith(('http://', 'https://')):
        return href
    lower = href.lower()
    if lower.startswith(('javascript:', 'data:', 'vbscript:')):
        return '#'
    anchor = ''
    if '#' in href:
        href, anchor = href.split('#', 1)
        anchor = '#' + anchor
    resolved = posixpath.normpath(posixpath.join(base, href))
    if resolved.startswith('../'):
        return '#'
    return resolved + anchor


def inline_markup(text, base):
    """Escape text, then rebuild only the inline Markdown used by example files."""
    parts = []
    pos = 0
    for match in LINK.finditer(text):
        parts.append(inline_plain(text[pos:match.start()]))
        label, href = match.group(1), match.group(2)
        parts.append(f'<a href="{esc(resolve_link(href, base))}">{inline_plain(label)}</a>')
        pos = match.end()
    parts.append(inline_plain(text[pos:]))
    return ''.join(parts)


def inline_plain(text):
    parts = []
    pos = 0
    for match in BOLD.finditer(text):
        parts.append(esc(text[pos:match.start()]))
        parts.append(f'<strong>{esc(match.group(1))}</strong>')
        pos = match.end()
    parts.append(esc(text[pos:]))
    marked = ''.join(parts)
    return CODE.sub(lambda m: f'<code>{m.group(1)}</code>', marked)


def render_markdown(text, base=''):
    """Render the bounded Markdown subset used by the example documents."""
    lines = text.splitlines()
    out = []
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith('<!--'):
            index += 1
            continue
        if stripped.startswith('```'):
            index += 1
            block = []
            while index < len(lines) and not lines[index].strip().startswith('```'):
                block.append(esc(lines[index]))
                index += 1
            index += 1
            out.append('<pre><code>' + '\n'.join(block) + '</code></pre>')
            continue
        if stripped == '---':
            out.append('<hr>')
            index += 1
            continue
        heading = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if heading:
            level = len(heading.group(1))
            out.append(f'<h{level}>{inline_markup(heading.group(2), base)}</h{level}>')
            index += 1
            continue
        if stripped.startswith('> '):
            quote = []
            while index < len(lines) and lines[index].strip().startswith('> '):
                quote.append(lines[index].strip()[2:])
                index += 1
            out.append('<blockquote>' + inline_markup(' '.join(quote), base) + '</blockquote>')
            continue
        if stripped.startswith('|') and index + 1 < len(lines) and TABLE_RULE.match(lines[index + 1].strip()):
            header = [cell.strip() for cell in stripped.strip('|').split('|')]
            index += 2
            rows = []
            while index < len(lines) and lines[index].strip().startswith('|'):
                rows.append([cell.strip() for cell in lines[index].strip().strip('|').split('|')])
                index += 1
            head = ''.join(f'<th>{inline_markup(cell, base)}</th>' for cell in header)
            body = ''.join('<tr>' + ''.join(f'<td>{inline_markup(cell, base)}</td>' for cell in row) + '</tr>'
                           for row in rows)
            out.append(f'<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')
            continue
        if re.match(r'^[-*]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
            ordered = bool(re.match(r'^\d+\.\s+', stripped))
            items = []
            while index < len(lines) and (re.match(r'^[-*]\s+', lines[index].strip()) if not ordered
                                          else re.match(r'^\d+\.\s+', lines[index].strip())):
                item = re.sub(r'^([-*]|\d+\.)\s+', '', lines[index].strip())
                items.append('<li>' + inline_markup(item, base) + '</li>')
                index += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(items) + f'</{tag}>')
            continue
        paragraph = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip() and not re.match(
                r'^(#{1,6}\s|[-*]\s|\d+\.\s|> |```|\||---$)', lines[index].strip()):
            paragraph.append(lines[index].strip())
            index += 1
        out.append('<p>' + '<br>'.join(inline_markup(item, base) for item in paragraph) + '</p>')
    return '\n'.join(out)


def page(title, body, *, accent, tint, notice=NOTICE):
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><style>{SITE_CSS}</style></head>'
            f'<body style="--accent:{esc(accent)};--tint:{esc(tint)}">'
            f'<div class="notice">{esc(notice)}</div>{body}</body></html>')


def nav(brand, subtitle, links):
    items = ''.join(f'<a href="{esc(href)}">{esc(label)}</a>' for label, href in links)
    return (f'<header class="nav"><div class="shell"><a class="brand" href="index.html">'
            f'{esc(brand)}<small>{esc(subtitle)}</small></a><nav class="links" aria-label="页面导航">'
            f'{items}</nav></div></header>')


def render_document(example, theme, *, title, subtitle, markdown, source_file, base, links):
    accent, tint = '#' + theme['accent'], '#' + theme['background']
    header = nav(f"{example['name']} · {example['profession']}", '虚构示例', links)
    # The page already provides the title; keep the source document's H1 out of the body.
    article = render_markdown(re.sub(r'(?m)^#\s+.*$', '', markdown, count=1), base)
    body = (header + '<main class="shell doc">'
            f'<div class="eyebrow">{esc(subtitle)}</div><h1>{esc(title)}</h1>'
            f'<p class="lead">全部人物、单位、经历与案例均为虚构教学设定。源文件：<a href="{esc(source_file)}">{esc(source_file)}</a></p>'
            f'<article>{article}</article>'
            '<p class="lead">本页由公共示例源数据生成，不读取使用者的私人履历。</p></main>'
            f'<footer class="footer shell"><div>© career-resume-skill · 虚构教学示例</div>'
            '<div><a href="../index.html">返回职业示例集</a> · '
            f'<a href="index.html">返回 {esc(example["name"])} 的主页</a></div></footer>')
    return page(title, body, accent=accent, tint=tint)


def render_site(example, theme):
    accent, tint = '#' + theme['accent'], '#' + theme['background']
    name, profession, slug = example['name'], example['profession'], example['slug']
    links = [
        ('代表实践', '#cases'), ('工作方式', '#method'), ('经历', '#experience'),
        ('完整履历', 'career.html'), ('简历', 'resume.html'), ('时间线', 'timeline.html'),
        ('示例集', '../index.html'),
    ]
    header = nav(f'{name} · {profession}', '虚构人物', links)

    cards, dialogs = [], []
    for number, case in enumerate(example['cases'], 1):
        tags = ''.join(f'<span class="tag">{esc(tool)}</span>' for tool in case['tools'])
        cards.append(
            f'<article class="card"><span class="category">{esc(case["category"])} · {number:02d}</span>'
            f'<time>{esc(case["period"])}</time><h3>{esc(case["name"])}</h3>'
            f'<p>{esc(case["challenge"])}</p><div class="tags">{tags}</div>'
            f'<button class="text-btn" data-open="case-{number}">阅读案例 ↗</button></article>')
        actions = ''.join(f'<li>{esc(action)}</li>' for action in case['actions'])
        dialogs.append(
            f'<dialog id="case-{number}"><button class="close" aria-label="关闭" data-close>×</button>'
            f'<div class="eyebrow">虚构案例 · {esc(case["category"])}</div><h2>{esc(case["name"])}</h2>'
            f'<p>{esc(case["period"])}</p><h3>背景与难点</h3><p>{esc(case["challenge"])}</p>'
            f'<h3>本人行动</h3><ul>{actions}</ul>'
            f'<h3>工作结果与边界</h3><p>{esc(case["result"])}</p>'
            '<p>本案例为虚构教学设定，不属于真实使用者。</p></dialog>')

    steps = ''.join(
        f'<div class="step"><span class="num">{number:02d}</span><h3>{esc(step)}</h3>'
        f'<p>{esc(example["special"][(number - 1) % len(example["special"])]["summary"])}</p></div>'
        for number, step in enumerate(example['process'], 1))
    special = ''.join(f'<p><strong>{esc(item["title"])}</strong>（{esc(item["subtitle"])}）<br>{esc(item["summary"])}</p>'
                      for item in example['special'])
    jobs = ''.join(
        '<article class="job"><div class="job-head">'
        f'<h3>{esc(job["organization"])}</h3><time>{esc(job["period"])}</time></div>'
        f'<div class="role">{esc(job["role"])}</div><p>{esc(job["summary"])}</p><ul>'
        + ''.join(f'<li>{esc(bullet)}</li>' for bullet in job['bullets']) + '</ul></article>'
        for job in example['jobs'])
    skills = ''.join(f'<p><strong>{esc(item["label"])}：</strong>{esc(item["text"])}</p>'
                     for item in example['skills'])
    extras = ''.join(f'<li>{esc(item)}</li>' for item in example['extras'])
    process = ''.join(f'<li>{esc(step)}</li>' for step in example['process'])
    intro = ''.join(f'<p>{esc(item)}</p>' for item in example['summary'])

    body = (
        header +
        '<main class="shell" id="top">'
        '<section class="hero"><div>'
        f'<div class="eyebrow">{esc(example["eyebrow"])}</div>'
        f'<h1>{esc(example["hero"])}</h1>'
        f'<p class="intro">{esc(example["intro"])}</p>'
        '<div class="buttons"><a class="btn primary" href="resume.html">查看简历正文 ↗</a>'
        '<a class="btn" href="career.html">完整职业履历 ↗</a></div>'
        f'<div class="lead" style="margin-top:20px;font-size:12px;color:var(--muted)">{esc(name)} / {esc(profession)} / 虚构人物</div>'
        '</div><div class="visual"><div class="eyebrow">HOW I WORK</div>'
        f'<ol>{process}</ol><div class="caption">{esc(example["specialTitle"])}：'
        f'{esc("；".join(item["title"] for item in example["special"]))}</div></div></section>'
        '<div class="strip">'
        f'<div><span>职业方向</span><strong>{esc(profession)}</strong></div>'
        f'<div><span>任职阶段</span><strong>{len(example["jobs"])} 段经历</strong></div>'
        f'<div><span>代表实践</span><strong>{len(example["cases"])} 个案例</strong></div></div>'
        '<section class="section" id="cases"><div class="section-head"><div>'
        f'<span class="count">01 / SELECTED PRACTICE</span><h2>{esc(example["casesTitle"])}</h2></div>'
        '<p>从问题出发，说明选择、本人行动与工作结果。全部案例均为虚构设定。</p></div>'
        f'<div class="cards">{"".join(cards)}</div></section>'
        '<section class="section two-col" id="method"><div>'
        f'<span class="count">02 / HOW I WORK</span><h2>{esc(example["specialTitle"])}</h2>{intro}{special}</div>'
        f'<div class="steps">{steps}</div></section>'
        '<section class="section two-col" id="experience"><div>'
        f'<span class="count">03 / EXPERIENCE</span><h2>{esc(example["careerTitle"])}</h2>'
        '<p class="intro">按时间倒序的虚构任职记录，完整事实与来源见文字履历。</p>'
        '<a class="text-btn" href="career.html">查看完整履历 ↗</a> '
        '<a class="text-btn" href="timeline.html">查看履历时间线 ↗</a></div>'
        f'<div>{jobs}</div></section>'
        '<section class="section more" id="background"><div>'
        f'<span class="count">04 / BACKGROUND</span><h3>教育与专业能力</h3>'
        f'<p><strong>{esc(example["education"]["school"])}</strong><br>'
        f'{esc(example["education"]["degree"])} · {esc(example["education"]["period"])}</p>{skills}</div>'
        f'<div><span class="count">MATERIALS</span><h3>{esc(example["extraTitle"])}</h3>'
        f'<ul>{extras}</ul><p>本页只展示该职业已设定的模块。所有资质、作品与经历均为虚构，不对应真实人物。</p></div></section>'
        '<section class="contact" id="contact"><div>'
        '<div class="eyebrow">RESUME & RECORDS</div><h2>继续查看这份示例</h2>'
        f'<p>{esc(example["email"])}（示例邮箱）· 简历选材不反向修改完整履历</p></div>'
        '<div class="buttons"><a class="btn primary" href="resume.html">简历正文 ↗</a>'
        '<a class="btn" href="report.html">依据与边界 ↗</a>'
        '<a class="btn" href="resume.en.html">英文简历 ↗</a>'
        '<a class="btn" href="resume.zh-CN.docx" download>中文 Word ↓</a>'
        '<a class="btn" href="resume.en.docx" download>英文 Word ↓</a></div></section>'
        '<footer class="footer"><div>© career-resume-skill · 虚构教学示例，未使用私人履历</div>'
        '<div><a href="../index.html">返回职业示例集</a> · '
        '<a href="career.html">完整履历</a> · <a href="timeline.html">时间线</a></div></footer>'
        '</main>' + ''.join(dialogs) + f'<script>{DIALOG_JS}</script>')
    return page(f'{name} · {profession}（虚构示例）', body, accent=accent, tint=tint)


def render_gallery(examples, palette):
    cards = []
    for example in examples:
        slug, theme = example['slug'], palette['themes'][example['theme']]
        cards.append(
            f'<article class="gallery-card" style="--accent:#{esc(theme["accent"])};--tint:#{esc(theme["background"])}">'
            f'<div class="gallery-art"></div><div class="gallery-body">'
            f'<div class="eyebrow">{esc(example["eyebrow"])}</div>'
            f'<h2>{esc(example["name"])}</h2><div class="role">{esc(example["profession"])} · {esc(theme["name"])}</div>'
            f'<p>{esc(example["intro"])}</p><div class="gallery-links">'
            f'<a href="{slug}/index.html">个人网页 ↗</a><a href="{slug}/career.html">完整履历 ↗</a>'
            f'<a href="{slug}/resume.html">中文简历 ↗</a><a href="{slug}/resume.en.html">英文简历 ↗</a>'
            f'<a href="{slug}/timeline.html">时间线 ↗</a>'
            f'<a href="{slug}/report.html">依据报告 ↗</a></div></div></article>')
    body = (
        nav('职业表达示例集', 'CAREER STUDIES / 虚构', [('设定数据', 'examples.json'),
                                                 ('说明', 'README.md')]) +
        '<main class="shell"><section class="gallery-hero">'
        '<div class="eyebrow">FIVE PROFESSIONS · ONE FACT CHAIN</div>'
        '<h1>五种职业，<br>同一条事实链。</h1>'
        '<p>每个示例都从带来源的事实记录出发，聚合为完整文字履历，再选材成简历，并生成面向访客的个人网页与履历时间线。'
        '模块随职业变化，案例说明问题、本人行动与结果；配色来自固定 HEX 调色板。全部网页离线可用，不加载外部资源。</p>'
        '<div class="buttons"><a class="btn primary" href="teacher/index.html">从第一个示例开始 ↗</a>'
        '<a class="btn" href="README.md">示例说明 ↗</a></div></section>'
        f'<div class="gallery-grid">{"".join(cards)}</div>'
        '<footer class="footer"><div>© career-resume-skill · 全部为虚构教学示例</div>'
        '<div>人物、单位、经历、案例、资格与邮箱均为设定，不可用于真实投递</div></footer></main>')
    return page('五种职业，五份个人表达 · 虚构示例集', body, accent='#2E79A6', tint='#EDF6FC')


def validate_example_data(data, palette):
    """Reject non-fictional or incomplete showcase data before any page is written."""
    if data.get('meta', {}).get('synthetic') is not True:
        raise ValueError('Profession examples must declare meta.synthetic: true.')
    slugs = [example['slug'] for example in data['examples']]
    if sorted(slugs) != sorted(PROFESSION_SLUGS) or len(set(slugs)) != len(slugs):
        raise ValueError('Profession slugs must match the controlled inventory.')
    for example in data['examples']:
        slug = example['slug']
        if example.get('synthetic') is not True:
            raise ValueError(f'{slug}: example must be marked synthetic.')
        if example['theme'] not in palette['themes']:
            raise ValueError(f'{slug}: unknown palette theme {example["theme"]}.')
        if not example['email'].endswith('@example.com'):
            raise ValueError(f'{slug}: only example.com addresses are allowed.')
        for field in ('name', 'profession', 'hero', 'intro', 'eyebrow', 'education',
                      'careerTitle', 'casesTitle', 'specialTitle', 'extraTitle',
                      'jobs', 'cases', 'special', 'skills', 'extras', 'process', 'summary'):
            if not example.get(field):
                raise ValueError(f'{slug}: missing {field}.')
        for job in example['jobs']:
            if not job['organization'].startswith('示例'):
                raise ValueError(f'{slug}: non-fictional organization in example data.')
        if not example['education']['school'].startswith('示例'):
            raise ValueError(f'{slug}: non-fictional school in example data.')


def validate_timeline_marker(root, slug):
    timeline = json.loads(checked_file(
        root, f'{EXAMPLES}/{slug}/source/data/timeline.json').read_text(encoding='utf-8'))
    if timeline.get('meta', {}).get('synthetic') is not True:
        raise ValueError(f'{slug}: timeline data must declare meta.synthetic: true.')


def load_examples(root):
    data = json.loads(checked_file(root, EXAMPLES + '/examples.json').read_text(encoding='utf-8'))
    palette = json.loads(checked_file(root, PALETTE).read_text(encoding='utf-8'))
    validate_example_data(data, palette)
    for example in data['examples']:
        validate_timeline_marker(root, example['slug'])
    return data, palette


def build_examples(root=ROOT, output=None):
    """Generate every public example page from committed sources only."""
    root = Path(root).resolve()
    data, palette = load_examples(root)
    raw = Path(output) if output is not None else root / 'docs/public/demo/professions'
    if any(path.is_symlink() for path in (raw, *raw.parents)):
        raise ValueError('Refusing a symlink output path.')
    target = raw.resolve()
    if any(path.is_symlink() for path in target.parents):
        raise ValueError('Refusing a symlink output path.')
    if target == root or target in root.parents:
        raise ValueError('Examples must not replace the project or its parents.')
    target.mkdir(parents=True, exist_ok=True)
    if any(path.is_symlink() for path in target.rglob('*')):
        raise ValueError('Refusing a symlink inside example output.')

    for example in data['examples']:
        slug, theme = example['slug'], palette['themes'][example['theme']]
        source_dir = root / EXAMPLES / slug
        site_dir = target / slug
        site_dir.mkdir(parents=True, exist_ok=True)
        # Flatten source/ into the page root so timeline.html and Markdown links resolve.
        for rel in (*PROFESSION_FILES, *PROFESSION_EXTRA_FILES.get(slug, ())):
            origin = checked_file(root, f'{EXAMPLES}/{slug}/{rel}')
            destination = site_dir / (rel.removeprefix('source/') if rel.startswith('source/') else rel)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin, destination)

        career = build_career(site_dir).read_text(encoding='utf-8')
        resume = (site_dir / 'resume.zh-CN.md').read_text(encoding='utf-8')
        english = (site_dir / 'resume.en.md').read_text(encoding='utf-8')
        report = (site_dir / 'match-report.md').read_text(encoding='utf-8').replace('](source/', '](')
        (site_dir / 'match-report.md').write_text(report, encoding='utf-8')

        document_links = [('个人网页', 'index.html'), ('完整履历', 'career.html'),
                          ('中文简历', 'resume.html'), ('英文简历', 'resume.en.html'),
                          ('依据报告', 'report.html'),
                          ('时间线', 'timeline.html'), ('示例集', '../index.html')]
        documents = (
            ('career.html', f'{example["name"]} · 完整职业履历', 'FULL CAREER RECORD',
             career, 'output/career/career.md', 'output/career'),
            ('resume.html', f'{example["name"]} · 简历正文', 'RESUME / ZH-CN',
             resume, 'resume.zh-CN.md', ''),
            ('resume.en.html', f'{example["name"]} · English Resume', 'RESUME / EN',
             english, 'resume.en.md', ''),
            ('report.html', f'{example["name"]} · 依据与边界', 'EVIDENCE & BOUNDARIES',
             report, 'match-report.md', ''),
        )
        for filename, title, subtitle, markdown, source_file, base in documents:
            atomic_write(site_dir / filename, render_document(
                example, theme, title=title, subtitle=subtitle, markdown=markdown,
                source_file=source_file, base=base, links=document_links).encode('utf-8'))
        atomic_write(site_dir / 'index.html', render_site(example, theme).encode('utf-8'))
        # Exports are rebuilt from Markdown; binaries stay out of source bundles.
        with tempfile.TemporaryDirectory(prefix='career-profession-docx-') as temporary:
            for language in ('zh-CN', 'en'):
                name = f'resume.{language}.docx'
                docx = export_resume(site_dir / f'resume.{language}.md',
                                     Path(temporary).resolve() / name, theme=example['theme'])
                atomic_write(site_dir / name, docx.read_bytes())
        build_timeline(site_dir, site_dir / 'timeline.html')

    # The generated copy lives under /demo/professions/, so repository-relative
    # documentation links must be rewritten instead of pointing outside the site.
    readme = (root / EXAMPLES / 'README.md').read_text(encoding='utf-8').replace(
        '(../../../docs/examples.md)', '(../../examples)')
    for filename, content in (('README.md', readme),
                              ('examples.json', json.dumps(data, ensure_ascii=False, indent=2) + '\n')):
        atomic_write(target / filename, content.encode('utf-8'))
    atomic_write(target / 'index.html', render_gallery(data['examples'], palette).encode('utf-8'))
    # atomic_write creates new files with tempfile's owner-only mode. Published
    # static pages must stay world-readable like the existing docs demo.
    for path in target.rglob('*'):
        if path.is_file() and not path.is_symlink():
            path.chmod(0o644)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Directory for generated example pages')
    args = parser.parse_args()
    try:
        target = build_examples(output=args.output)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        return fail(exc)
    print(f'Created {len(PROFESSION_SLUGS)} fictional profession sites: {target}')


if __name__ == '__main__':
    raise SystemExit(main())
