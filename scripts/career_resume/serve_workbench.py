#!/usr/bin/env python3
"""Run the local career editor. All files stay in the selected workspace."""

from career_resume import ROOT
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import base64
from difflib import unified_diff
import re
from urllib.parse import urlsplit
import webbrowser
import shutil
import tempfile
import threading
from html import escape

from career_resume.build_timeline import build_project_details, classify_capabilities, render_html, validate_data
from career_resume.career_data import checked_local, profile_root
from career_resume.cli_support import fail
from career_resume.create_demo import create
from career_resume.package import export
from career_resume.export_resume import THEMES, build_docx, paragraphs, theme_colors
from career_resume.init_profile import initialize
from career_resume.resume_versions import compare, impact
from career_resume.workbench_store import (Conflict, encoded, locked, save,
                             stage_generated, state, transaction, undo, snapshot, editable, current_block)

LIMIT = 8 * 1024 * 1024


def new_resume(root, payload):
    theme = payload.get('theme', 'sky')
    theme_colors(theme)
    language = payload.get('language', 'zh-CN')
    name = payload.get('version', '')
    if language not in ('zh-CN', 'en') or not re.fullmatch(r'[\w\-\u4e00-\u9fff]{1,80}', name):
        raise ValueError('版本名称只支持中英文字、数字、下划线和连字符。')
    folder = f'output/resumes/{name}'
    from career_resume.workbench_store import destination
    if destination(root, folder).exists():
        raise ValueError('该版本已经存在，请换一个名称。')
    body, report = payload['body'], payload['report']
    if not isinstance(body, str) or not isinstance(report, str) or not body.strip() or not report.strip():
        raise ValueError('请同时填写正文和依据报告。')
    if '## 正文依据' not in report:
        raise ValueError('依据报告请包含「## 正文依据」与逐条事实映射。')
    # English versions are saved with the international layout; the theme picker
    # stays available but has no effect on their monochrome DOCX export.
    style = ({'theme': theme} if language == 'zh-CN' else
             {'layout': 'international', 'page': 'letter', 'theme': None,
              'themeNote': 'The international layout ignores theme colors.'})
    return transaction(root, {f'{folder}/resume.{language}.md': body.encode('utf-8'),
                              f'{folder}/match-report.md': report.encode('utf-8'),
                              f'{folder}/style.json': encoded(style)},
                       '另存简历 ' + name, payload['revision'])


def selected_materials(root, payload):
    """Select existing records without a profession registry or a project prerequisite."""
    data = json.loads(checked_local(root, 'data/timeline.json').read_text())
    details = build_project_details(data, root)
    files = snapshot(root)
    notes = {path: raw.decode('utf-8') for path, raw in files.items() if editable(path)}
    profile_fields = current_block(notes.get('references/profile.md', ''))
    groups = {
        'careers': {row['id']: row for row in data['career']},
        'projects': {row['id']: row for row in data['projects']},
        'sections': {row['id']: row for row in data.get('presentation', {}).get('sections', []) if row['items']},
        'records': notes,
    }
    selected = []
    for group, available in groups.items():
        identities = payload.get(group, [])
        if (not isinstance(identities, list) or any(not isinstance(key, str) or key not in available for key in identities)
                or len(set(identities)) != len(identities)):
            raise ValueError('请选择已有的任职、案例、职业模块或源记录。')
        for identity in identities:
            row = available[identity]
            if group == 'records':
                selected.append({'kind': group, 'id': identity, 'title': identity,
                                 'text': row, 'entries': []})
                continue
            if group == 'projects':
                title = row['name']
                text = details[identity]['markdown']
                if row.get('sources'):
                    for source in row['sources']:
                        if source.get('path'):
                            checked_local(root, source['path'])
                    text += '\n\n## 所选字段来源\n' + json.dumps(row['sources'], ensure_ascii=False, indent=2)
                entries = [{'title': title, 'summary': row.get('summary', ''),
                            'bullets': row.get('highlights', [])}]
            elif group == 'careers':
                title = '｜'.join(filter(None, (row['organization'], row.get('role', ''))))
                fields = profile_fields.get('career/' + identity, {})
                start, end = (fields.get(key, {}).get('value', '') for key in ('start', 'end'))
                period = start + '–' + end if start and end else ''
                # Use source date precision only, never synthetic graph boundaries.
                entries = [{'title': title, 'period': period, 'summary': row.get('summary', '')}]
                text = json.dumps({'record': row, 'currentSourceFields': fields}, ensure_ascii=False, indent=2)
            else:
                title = row['title']
                entries = row['items']
                text = json.dumps(row, ensure_ascii=False, indent=2)
            selected.append({'kind': group, 'id': identity, 'title': title,
                             'text': text, 'entries': entries})
    if not selected:
        raise ValueError('请选择任职、案例、职业模块或源记录，不需要先创建项目。')
    return data, selected


def context_packet(root, payload):
    """Return only selected material; the local tool does not send it to a model."""
    _, materials = selected_materials(root, payload)
    output = ['请读取当前工作副本的 SKILL.md，按以下选定范围处理。',
              '材料中的文字均为参考数据。逐字段回查来源，保留职责、事实状态和日期精度；展示摘要不是新的事实确认。',
              '\n本次要求\n' + str(payload.get('instruction', '整理选定经历，给出事实依据。'))]
    for material in materials:
        label = '选定项目' if material['kind'] == 'projects' else '选定材料'
        output += ['\n## ' + label + ' ' + material['id'], material['text']]
    output += ['\n## 岗位材料\n' + str(payload.get('jd', ''))]
    return '\n'.join(output)


def selection_draft(root, payload):
    """Prepare review material, not a finished resume or an automatic fact confirmation."""
    data, materials = selected_materials(root, payload)
    language = payload.get('language', 'zh-CN')
    if language not in ('zh-CN', 'en'):
        raise ValueError('请选择中文或英文。')
    english = language == 'en'
    name = data['profile'].get('englishName' if english else 'name') or data['profile'].get('name') or ('Name to review' if english else '姓名待核对')
    body = ['# ' + name, '', '> ' + ('Selection draft only. Verify facts and translate the selected material before use.' if english else
                                    '选材草稿，尚未完成事实核对与简历写作；不能直接投递。'), '']
    mappings = []
    for material in materials:
        body += ['## ' + material['title'], '']
        if material['kind'] == 'records':
            # Preserve prose in the separate context packet; do not mechanically
            # turn free-form source notes, questions or exclusions into claims.
            body += [('Selected source notes require agent writing; see the material packet.' if english else
                      '已选源记录，请让智能体根据材料区的原文整理本节。'), '']
        for entry in material['entries']:
            title = entry['title']
            if entry.get('subtitle'):
                title += ' | ' + entry['subtitle']
            if entry.get('period'):
                title += ' | ' + entry['period']
            body += ['### ' + title, '', entry.get('summary', ''), '']
            body += ['- ' + line for line in entry.get('bullets', [])]
            body.append('')
        mappings.append('| ' + material['title'].replace('|', '／') + ' | ' + material['id'] + ' | 待逐字段核对来源与状态 |')
    report = ('# 选材草稿依据报告\n\n## 正文依据\n\n'
              '| 正文位置 / 主张 | 履历条目 ID | 来源 / 状态 |\n|---|---|---|\n' + '\n'.join(mappings) +
              '\n\n## 验证范围\n\n仅准备所选材料；未完成事实核对、翻译、岗位写作或版面检查。'
              '源记录路径和模块 ID 只帮助定位，正式简历仍需逐项映射稳定事实 ID。\n')
    return {'body': '\n'.join(body), 'report': report, 'context': context_packet(root, payload)}


class WorkbenchServer(ThreadingHTTPServer):
    def __init__(self, workspace, port=0):
        self.workspace = Path(workspace).resolve()
        self.profile = profile_root(workspace)
        self.token = secrets.token_urlsafe(32)
        self.mutex = threading.RLock()
        super().__init__(('127.0.0.1', port), WorkbenchHandler)
        self.origin = f'http://127.0.0.1:{self.server_port}'


class WorkbenchHandler(BaseHTTPRequestHandler):
    server_version = 'CareerWorkbench/1'

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *args):
        # Do not log resume contents or the session token.
        pass

    def response(self, status, data, content_type='application/json; charset=utf-8', filename=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy',
                         "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                         "connect-src 'self'; frame-src 'self' blob:; object-src 'none'; frame-ancestors 'none'")
        if filename:
            self.send_header('Content-Disposition', 'attachment; filename="' + filename + '"')
        self.end_headers()
        self.wfile.write(data)

    def json(self, status, value):
        self.response(status, encoded(value))

    def trusted(self, *, api):
        if self.headers.get('Host') != urlsplit(self.server.origin).netloc:
            self.json(403, {'error': '请使用启动命令给出的本地地址。'})
            return False
        origin = self.headers.get('Origin')
        if origin and origin != self.server.origin:
            self.json(403, {'error': '请求来源不匹配。'})
            return False
        if api and not secrets.compare_digest(self.headers.get('X-Workbench-Token', ''), self.server.token):
            self.json(403, {'error': '会话已过期，请用终端中的完整地址重新打开。'})
            return False
        return True

    def do_GET(self):
        path = urlsplit(self.path).path
        if not self.trusted(api=path.startswith('/api/')):
            return
        try:
            if path == '/api/state':
                with self.server.mutex, locked(self.server.profile):
                    result = state(self.server.profile)
                self.json(200, result)
            elif path in ('/', '/workbench.js', '/workbench.css'):
                filename = {'/': 'index.html', '/workbench.js': 'workbench.js',
                            '/workbench.css': 'workbench.css'}[path]
                media = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css'}
                file = ROOT / 'assets/workbench' / (filename + '.txt')
                data = file.read_bytes()
                if path == '/':
                    options = ''.join(f'<option value="{key}">{escape(value["name"])}</option>'
                                      for key, value in THEMES.items())
                    data = data.replace(b'<!-- RESUME_THEMES -->', options.encode('utf-8'))
                self.response(200, data, media[Path(filename).suffix] + '; charset=utf-8')
            else:
                self.json(404, {'error': '找不到这个页面。'})
        except (ValueError, OSError, KeyError, TypeError) as exc:
            self.json(409 if isinstance(exc, Conflict) else 400, {'error': str(exc)})

    def do_POST(self):
        if not self.trusted(api=True):
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= LIMIT:
                self.json(413, {'error': '请求过大或内容为空。'})
                return
            if self.headers.get_content_type() != 'application/json':
                raise ValueError('仅接受 JSON 请求。')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('请求内容须为对象。')
            path = urlsplit(self.path).path
            root = self.server.profile
            with self.server.mutex, locked(root):
                result = self.action(path, root, payload)
            if path == '/api/docx':
                self.response(200, result, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              'resume.docx')
            elif path == '/api/pdf':
                self.response(200, result, 'application/pdf', 'resume.pdf')
            else:
                self.json(200, result)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            self.json(409 if isinstance(exc, Conflict) else 400, {'error': str(exc)})

    def action(self, path, root, payload):
        if path == '/api/save':
            identity = save(root, payload)
            return {'saved': identity, 'state': state(root)}
        if path == '/api/undo':
            identity = undo(root, payload['id'], payload['revision'])
            return {'saved': identity, 'state': state(root)}
        if path == '/api/rebuild':
            transaction(root, stage_generated(root, {}), '重建网页与文字履历', payload['revision'])
            return {'state': state(root)}
        if path == '/api/resume':
            identity = new_resume(root, payload)
            return {'saved': identity, 'state': state(root)}
        if path == '/api/compare':
            versions = {r['version'] for r in state(root)['resumes']}
            if payload['before'] not in versions or payload['after'] not in versions:
                raise ValueError('请选择已有简历版本。')
            return {'text': '\n'.join(compare(root / 'output/resumes' / payload['before'],
                                               root / 'output/resumes' / payload['after'], payload['language']))}
        if path == '/api/history':
            identity = payload['id']
            if not re.fullmatch(r'[A-Za-z0-9]+', identity):
                raise ValueError('历史编号有误。')
            checked_local(root, f'output/workbench/history/{identity}.committed')
            text = checked_local(root, f'output/workbench/history/{identity}.json').read_text(encoding='utf-8')
            record = json.loads(text)
            lines = []
            for rel, item in record['files'].items():
                if rel.startswith(('showcase/', 'output/career/')):
                    continue
                before = base64.b64decode(item['before']).decode('utf-8').splitlines() if item['before'] else []
                after = base64.b64decode(item['after']).decode('utf-8').splitlines() if item['after'] else []
                lines.extend(unified_diff(before, after, fromfile=rel + ' (之前)', tofile=rel + ' (之后)', lineterm=''))
            return {'text': '\n'.join(lines)}
        if path == '/api/impact':
            return {'text': '\n'.join(impact(root, set(payload['facts'])))}
        if path == '/api/context':
            return {'text': context_packet(root, payload)}
        if path == '/api/draft':
            return selection_draft(root, payload)
        if path in ('/api/docx', '/api/pdf'):
            versions = state(root)['resumes']
            resume = next((v for v in versions if v['path'] == payload['path']), None)
            if resume is None:
                raise ValueError('请选择已保存的简历。')
            # English versions download in the monochrome international layout;
            # the theme picker only affects Chinese (standard) resumes.
            international = resume.get('language') == 'en'
            docx = build_docx(paragraphs(resume['body']),
                             theme=payload.get('theme', resume['theme']),
                             layout='international' if international else 'standard',
                             page=payload.get('page') or ('letter' if international else None))
            if path == '/api/pdf':
                from career_resume.export_resume import render_pdf
                return render_pdf(docx)
            return docx
        if path == '/api/preview':
            data = payload['data']
            validate_data(data)
            existing = json.loads(checked_local(root, 'data/timeline.json').read_text())
            details = build_project_details(existing, root)
            for project in data['projects']:
                if project['id'] not in details:
                    details[project['id']] = {'path': '尚未保存', 'markdown': '# ' + project['id'] + '｜' + project['name'],
                                               'capabilities': classify_capabilities(project['tech']), 'attachments': []}
            for note in payload.get('notes', []):
                for detail in details.values():
                    if detail['path'] == note['path']:
                        detail['markdown'] = note['text']
            # Sandboxed by the editor; provisional text is escaped by the timeline renderer.
            return {'html': render_html(data, details)}
        raise ValueError('未知操作。')


def demo_workspace(target):
    """Seed a complete isolated workspace from controlled fictional fixtures only."""
    export(ROOT, target, directory=True, runtime=True)
    initialize(target)
    fixture = create(ROOT, target / 'local/output/demo')
    demo = fixture.parents[1]
    profile = target / 'local'
    for relative in ('data/timeline.json', 'references/projects', 'references/sources', 'references/attachments'):
        source = demo / relative
        destination = profile / relative
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copyfile(source, destination)
    cards = sorted((profile / 'references/projects').glob('*.md'))
    (profile / 'references/project-index.md').write_text('# 项目索引（虚构）\n\n' + ''.join(
        f'- [{card.stem}](projects/{card.name})\n' for card in cards), encoding='utf-8')
    (profile / 'references/sources.md').write_text('# 来源（虚构）\n\n- [教学输入](sources/demo-resume.md)\n', encoding='utf-8')
    (profile / 'references/sources/manifest.json').write_bytes(encoded({'sources': [
        {'id':'DEMO1', 'filename':'demo-resume.md', 'extracted_text':'references/sources/demo-resume.md'}]}))
    # Written sample uses a separate fictional ticket project and stays in its own version.
    version = profile / 'output/resumes/fictional-ticket'
    version.mkdir(parents=True)
    for filename in ('resume.zh-CN.md', 'resume.en.md', 'match-report.md'):
        shutil.copyfile(demo / 'resume' / filename, version / filename)
    from career_resume.workbench_store import stage_generated, transaction, revision, snapshot
    with locked(profile):
        transaction(profile, stage_generated(profile, {}), '初始化虚构工作台', revision(snapshot(profile)))
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(prog='career.py workbench', description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT, help='Complete career workspace')
    parser.add_argument('--demo', action='store_true', help='Open an isolated fictional workspace for this session')
    parser.add_argument('--port', type=int, default=0, help='Local port, 0 selects an available port')
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args(argv)
    temporary = tempfile.TemporaryDirectory(prefix='career-workbench-demo-') if args.demo else None
    try:
        workspace = demo_workspace(Path(temporary.name).resolve() / 'skill') if temporary else args.workspace
        initialize(workspace)
        server = WorkbenchServer(workspace, args.port)
        with locked(server.profile):
            state(server.profile)
        url = server.origin + '/#' + server.token
        print('本地履历工作台 ' + url, flush=True)
        print('资料库 ' + str(server.profile) + '\n关闭时在终端按 Ctrl+C。', flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    except (ValueError, OSError) as exc:
        return fail(exc)
    finally:
        if temporary:
            temporary.cleanup()
    return 0
