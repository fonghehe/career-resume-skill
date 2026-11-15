"""Local workbench transactions, provenance and compatibility with Markdown records."""

from contextlib import contextmanager
from datetime import date, datetime, timezone
import base64
import calendar
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid

from career_resume.build_career import build as build_career
from career_resume.build_timeline import build as build_timeline, build_project_details, validate_data
from career_resume.career_data import checked_local
from career_resume.file_io import atomic_write, write_new
from career_resume.presentation import theme_colors

FIELDS = {
    'profile': ('name', 'englishName', 'headline', 'email', 'phone', 'education'),
    'career': ('organization', 'role', 'level', 'start', 'end', 'summary'),
    'projects': ('name', 'organization', 'nature', 'category', 'start', 'end', 'summary',
                 'tech', 'highlights', 'projectBackend', 'collaboration', 'milestones'),
}
LISTS = {'tech', 'highlights', 'projectBackend', 'collaboration'}
MARKER = '<!-- career-workbench-current -->'
END = '<!-- /career-workbench-current -->'


class Conflict(ValueError):
    """The user must review newer files before saving this draft."""


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def destination(root, relative):
    raw = Path(relative)
    if raw.is_absolute() or '..' in raw.parts or '\\' in relative:
        raise ValueError('文件路径超出当前资料库。')
    path = root / raw
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('工作台需要真实文件路径，请移除路径中的符号链接。')
    return path


def snapshot(root):
    """Fingerprint editable records and source snapshots; never load original uploads."""
    result = {}
    for folder in ('references', 'output/resumes'):
        base = destination(root, folder)
        for directory, folders, files in os.walk(base):
            for name in folders + files:
                if (Path(directory) / name).is_symlink():
                    raise ValueError('资料目录包含符号链接。')
            for name in sorted(files):
                path = Path(directory) / name
                if path.suffix in ('.md', '.json'):
                    result[path.relative_to(root).as_posix()] = path.read_bytes()
    result['data/timeline.json'] = checked_local(root, 'data/timeline.json').read_bytes()
    for rel in ('showcase/project-timeline.html', 'output/career/career.md'):
        path = destination(root, rel)
        if path.is_file():
            result[rel] = path.read_bytes()
    return result


def revision(files):
    return sha(encoded({key: sha(value) for key, value in sorted(files.items())}))


def editable(path):
    return path in ('references/profile.md', 'references/facts.md', 'references/project-index.md',
                    'references/questions-to-confirm.md') or bool(re.fullmatch(
                        r'references/(?:projects|career)/[A-Za-z0-9_./\-\u4e00-\u9fff]+\.md', path))


def current_block(text):
    if MARKER not in text:
        return {}
    match = re.search(re.escape(MARKER) + r'\n```json\n(.*?)\n```\n' + re.escape(END), text, re.S)
    if not match or text.count(MARKER) != 1:
        raise ValueError('网页维护字段块格式有误，请先检查原文。')
    value = json.loads(match[1])
    if not isinstance(value, dict):
        raise ValueError('网页维护字段块必须是对象。')
    return value


def replace_block(text, fields):
    block = MARKER + '\n```json\n' + encoded(fields).decode().replace('<', '\\u003c').rstrip() + '\n```\n' + END
    if MARKER in text:
        current_block(text)
        return re.sub(re.escape(MARKER) + r'.*?' + re.escape(END), lambda _: block, text, flags=re.S)
    return text.rstrip() + '\n\n## 网页维护的当前字段\n\n以下记录为用户保存的最新字段值。采用时按字段核对来源和状态，同字段旧表述以这里为准。\n\n' + block + '\n'


def display_date(value, *, end=False):
    if not value:
        return ''
    if re.fullmatch(r'\d{4}', value):
        return date(int(value), 12 if end else 1, 31 if end else 1).isoformat()
    if re.fullmatch(r'\d{4}-\d{2}', value):
        year, month = map(int, value.split('-'))
        return date(year, month, calendar.monthrange(year, month)[1] if end else 1).isoformat()
    return date.fromisoformat(value).isoformat()


def history_root(root):
    return destination(root, 'output/workbench/history')


def restore_pending(root):
    pending = destination(root, 'output/workbench/pending.json')
    if not pending.exists():
        return
    record = json.loads(pending.read_text(encoding='utf-8'))
    if (history_root(root) / (record['id'] + '.committed')).exists():
        pending.unlink()
        return
    # Recover a crash or a partial write only while it still matches this transaction.
    for rel, state in record['files'].items():
        path = destination(root, rel)
        now = path.read_bytes() if path.exists() else None
        before = base64.b64decode(state['before']) if state['before'] is not None else None
        after = base64.b64decode(state['after']) if state['after'] is not None else None
        if now == before:
            continue
        if now != after:
            raise Conflict('未完成的保存与外部修改冲突，请保留文件并检查 output/workbench/pending.json。')
        if before is None:
            path.unlink()
        else:
            atomic_write(path, before)
    pending.unlink()


@contextmanager
def locked(root):
    lock = destination(root, 'data/.update.lock')
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        try:
            owner = json.loads(lock.read_text(encoding='utf-8'))
            if owner.get('workbench') is not True or type(owner.get('pid')) is not int:
                raise Conflict('其他更新正在运行，请稍后重试。')
            os.kill(owner['pid'], 0)
        except ProcessLookupError:
            lock.unlink()
            with locked(root):
                yield
            return
        except (ValueError, OSError):
            raise Conflict('资料库正在更新，请稍后重试。') from None
        raise Conflict('资料库正在更新，请稍后重试。')
    try:
        os.write(fd, encoded({'workbench': True, 'pid': os.getpid()}))
        os.fsync(fd)
        restore_pending(root)
        yield
    finally:
        os.close(fd)
        lock.unlink()


def transaction(root, changes, label, expected):
    """Publish a prepared journal before writes, then commit all files or recover them."""
    if revision(snapshot(root)) != expected:
        raise Conflict('文件已被其他页面或 Agent 修改，请重新载入后核对。')
    identity = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + uuid.uuid4().hex[:8]
    entries = {}
    for rel, after in changes.items():
        path = destination(root, rel)
        before = path.read_bytes() if path.is_file() else None
        if before != after:
            entries[rel] = {'before': base64.b64encode(before).decode() if before is not None else None,
                            'after': base64.b64encode(after).decode() if after is not None else None}
    if not entries:
        return None
    history = history_root(root)
    history.mkdir(parents=True, exist_ok=True)
    pending = destination(root, 'output/workbench/pending.json')
    record = {'id': identity, 'label': label, 'time': datetime.now().astimezone().isoformat(), 'files': entries}
    # Snapshot is immutable. A separate commit receipt distinguishes failed transactions.
    write_new(history / (identity + '.json'), encoded(record))
    write_new(pending, encoded(record))
    try:
        if revision(snapshot(root)) != expected:
            raise Conflict('保存前资料发生变化，请重新载入。')
        for rel, state in entries.items():
            path = destination(root, rel)
            before = base64.b64decode(state['before']) if state['before'] is not None else None
            if (path.read_bytes() if path.exists() else None) != before:
                raise Conflict('保存期间文件被修改，请检查并重新载入。')
            after = base64.b64decode(state['after']) if state['after'] is not None else None
            if after is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(path, after)
        write_new(history / (identity + '.committed'), b'complete\n')
        pending.unlink()
    except BaseException:
        restore_pending(root)
        raise
    return identity


def stage_generated(root, planned):
    """Build against an isolated copy of relevant records before touching live files."""
    files = snapshot(root)
    files.update(planned)
    data = json.loads(files['data/timeline.json'])
    validate_data(data)
    for rel, marker in (('output/career/career.md', '<!-- career-resume-skill:generated-career -->'),
                        ('showcase/project-timeline.html', '<script id="timeline-data"')):
        target = destination(root, rel)
        if target.exists() and marker not in target.read_text(encoding='utf-8'):
            raise ValueError('生成目标含手写内容，请另存后再构建：' + rel)
    with tempfile.TemporaryDirectory(prefix='career-workbench-') as temporary:
        stage = Path(temporary).resolve()
        for rel, raw in files.items():
            if not rel.startswith(('references/', 'data/')) or raw is None:
                continue
            path = stage / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        for project in data['projects']:
            for attachment in project.get('attachments', []):
                rel = attachment['path']
                source = checked_local(root, rel)
                target = destination(stage, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
        for builder in (build_career, build_timeline):
            path = builder(stage)
            planned[path.relative_to(stage).as_posix()] = path.read_bytes()
    return planned


def state(root):
    files = snapshot(root)
    data = json.loads(files['data/timeline.json'])
    validate_data(data)
    cards = build_project_details(data, root)
    notes = {key: value.decode('utf-8') for key, value in files.items() if editable(key)}
    resumes = []
    for rel in sorted(files):
        match = re.fullmatch(r'output/resumes/([^/]+)/resume\.(zh-CN|en)\.md', rel)
        if match:
            folder = 'output/resumes/' + match[1]
            style = json.loads(files.get(folder + '/style.json', b'{"theme":"sky"}'))
            # English / international versions record no theme; fall back for the theme picker.
            theme = (style.get('theme') if isinstance(style, dict) else None) or 'sky'
            theme_colors(theme)
            resumes.append({'version': match[1], 'language': match[2], 'path': rel,
                            'theme': theme,
                            'body': files[rel].decode('utf-8'),
                            'report': files.get(folder + '/match-report.md', b'').decode('utf-8')})
    histories = []
    for path in sorted(history_root(root).glob('*.json'), reverse=True):
        if path.with_suffix('.committed').is_file():
            record = json.loads(path.read_text(encoding='utf-8'))
            histories.append({k: record[k] for k in ('id', 'label', 'time')})
    return {'revision': revision(files), 'data': data, 'notes': notes,
            'cards': {pid: detail['path'] for pid, detail in cards.items()},
            'resumes': resumes, 'history': histories[:100], 'workspace': str(root)}


def record_path(collection, identity, cards):
    if collection == 'projects':
        return cards.get(identity, f'references/projects/{identity.lower()}.md')
    return 'references/profile.md'


def save(root, payload):
    files = snapshot(root)
    if payload['revision'] != revision(files):
        raise Conflict('文件已更新，请重新载入后再保存。')
    data = json.loads(files['data/timeline.json'])
    cards = {pid: detail['path'] for pid, detail in build_project_details(data, root).items()}
    changes = payload.get('changes', [])
    notes = payload.get('notes', [])
    if not isinstance(changes, list) or not isinstance(notes, list):
        raise ValueError('修改列表格式有误。')
    planned = {}
    source_id = 'WB' + uuid.uuid4().hex.upper()
    source_path = f'references/sources/{source_id}.md'
    audit = []
    seen = set()
    for change in changes:
        collection, identity = change['collection'], change['id']
        if collection not in FIELDS or not isinstance(identity, str):
            raise ValueError('无法编辑该记录。')
        if (collection, identity) in seen:
            raise ValueError('同一记录请合并为一次修改。')
        seen.add((collection, identity))
        if collection != 'profile' and not re.fullmatch(r'E\d{2,}' if collection == 'career' else r'[PO]\d{2,}', identity):
            raise ValueError('记录编号格式应为 E01 或 P01 / O01。')
        fields = change['fields']
        if not isinstance(fields, dict) or set(fields) - set(FIELDS[collection]):
            raise ValueError('修改中包含不支持的字段。')
        mode = change.get('mode')
        if mode not in ('fact', 'display'):
            raise ValueError('请选择事实更正或展示修改。')
        if mode == 'fact' and change.get('confirmed') is not True:
            raise ValueError('请明确确认本次事实字段。')
        if mode == 'display' and set(fields) - {'summary', 'headline'}:
            raise ValueError('展示修改只支持摘要和定位，其他字段请保存为事实更正。')
        rows = data[collection] if collection != 'profile' else [data['profile']]
        row = next((r for r in rows if collection == 'profile' or r['id'] == identity), None)
        is_new = row is None
        if is_new:
            if mode != 'fact':
                raise ValueError('新增记录需要本人确认。')
            row = {'id': identity}
            if collection == 'career':
                row.update(organization='', role='', summary='', start='', end='')
            else:
                row.update(name='', organization='', nature='company', category='', status='confirmed',
                           tech=[], highlights=[], summary='', start='', end='')
            rows.append(row)
        path = record_path(collection, identity, cards)
        text = planned.get(path, files.get(path, f'# {identity}｜{fields.get("name", "新项目")}\n'.encode())).decode('utf-8')
        managed = current_block(text)
        group = managed.setdefault(collection + '/' + identity, {})
        for field, value in fields.items():
            if field in LISTS:
                valid = isinstance(value, list) and all(isinstance(v, str) for v in value)
            elif field == 'milestones':
                valid = isinstance(value, list) and all(isinstance(v, dict) and isinstance(v.get('title'), str) for v in value)
            else:
                valid = isinstance(value, str)
            if not valid:
                raise ValueError('字段格式有误：' + field)
            shown = display_date(value, end=field == 'end') if field in ('start', 'end') else value
            existing = group.get(field, {}).get('value', row.get(field))
            if not is_new and existing == value and not change.get('confirmOnly'):
                continue
            supplied_id = change.get('factIds', {}).get(field)
            fid = supplied_id or group.get(field, {}).get('id') or (identity if collection != 'profile' else 'U01') + '-WB-' + field.upper()
            if not isinstance(fid, str) or not re.fullmatch(r'[A-Z]+[0-9]+(?:-[A-Z0-9]+)*', fid):
                raise ValueError('事实编号格式有误。')
            if collection == 'projects' and not fid.startswith(identity + '-'):
                raise ValueError('项目事实编号须使用当前项目编号作为前缀。')
            supported = value not in ('', [])
            status = ('confirmed' if supported else 'pending') if mode == 'fact' else 'display-only'
            group[field] = {'id': fid, 'value': value, 'status': status,
                            'source': source_id, 'date': datetime.now().astimezone().isoformat()}
            audit.append({'record': collection + '/' + identity, 'field': field, 'id': fid,
                          'before': existing, 'after': value, 'mode': mode})
            row[field] = shown
            if collection != 'profile' and mode == 'fact':
                # The display projection carries current support only. Previous
                # values and sources remain in immutable snapshots and history.
                row['sources'] = [entry for entry in row.get('sources', []) if entry.get('field') != field]
                if supported:
                    row['sources'].append({'field': field, 'label': fid, 'status': 'confirmed',
                                           'path': source_path, 'excerpt': json.dumps(value, ensure_ascii=False)})
                confirmed = row.setdefault('confirmedFields', [])
                if supported and field not in confirmed:
                    confirmed.append(field)
                elif not supported and field in confirmed:
                    confirmed.remove(field)
            if field in ('start', 'end') and value and len(value) in (4, 7):
                data['meta']['dateConvention'] = '仅有年份或月份的日期在图上按该年或月的首尾展示，源记录保留原精度。'
        if collection == 'projects' and not row.get('name', '').strip():
            raise ValueError('请填写项目名称。')
        if collection == 'career' and not row.get('organization', '').strip():
            raise ValueError('请填写单位或任职归属；未知职称可以留空。')
        planned[path] = replace_block(text, managed).encode('utf-8')
        if is_new and collection == 'projects':
            index = 'references/project-index.md'
            index_text = planned.get(index, files[index]).decode('utf-8')
            planned[index] = (index_text.rstrip() + f'\n\n- [{identity}](projects/{Path(path).name})\n').encode('utf-8')
    for note in notes:
        path, text = note['path'], note['text']
        if not editable(path) or path not in files or path in planned or not isinstance(text, str):
            raise ValueError('原文修改仅支持已有可维护记录，请分开保存表单和同一份原文。')
        if current_block(files[path].decode()) != current_block(text):
            raise ValueError('网页维护字段请在表单中修改，保留原文中的维护字段块。')
        if path.startswith('references/projects/'):
            before = re.match(r'# ([PO]\d{2,})｜', files[path].decode())
            after = re.match(r'# ([PO]\d{2,})｜', text)
            if not before or not after or before[1] != after[1]:
                raise ValueError('保留项目卡首行的稳定编号。')
        planned[path] = text.encode('utf-8')
        audit.append({'record': path, 'mode': 'manual-source-edit', 'before': files[path].decode(), 'after': text})
    if not audit:
        return None
    if audit:
        notice = '> 虚构教学记录，仅限演示。\n\n' if data['meta'].get('synthetic') else ''
        planned[source_path] = (f'# {source_id} 网页修改记录\n\n' + notice +
                               '用户在本地工作台保存。事实确认仅作用于 mode 为 fact 的字段。\n\n```json\n' +
                               encoded(audit).decode() + '```\n').encode('utf-8')
        manifest_path = 'references/sources/manifest.json'
        manifest = json.loads(files[manifest_path])
        manifest['sources'].append({'id': source_id, 'filename': source_id + '.md',
                                    'extracted_text': source_path, 'imported_on': date.today().isoformat()})
        planned[manifest_path] = encoded(manifest)
        source_index = files['references/sources.md'].decode('utf-8')
        planned['references/sources.md'] = (source_index.rstrip() + f'\n\n- [{source_id} 网页修改](sources/{source_id}.md)\n').encode()
        log_path = 'references/career/workbench.md'
        log = files.get(log_path, '# 网页维护记录\n\n按字段查看最新记录，旧值保留在来源快照与历史中。\n'.encode()).decode()
        log += f'\n## {source_id}\n\n'
        for item in audit:
            log += '- ' + json.dumps(item, ensure_ascii=False) + '\n'
        planned[log_path] = log.encode()
        entry = files['references/career/README.md'].decode()
        if 'workbench.md' not in entry:
            planned['references/career/README.md'] = (entry.rstrip() + '\n\n- [网页维护记录](workbench.md)\n').encode()
    planned['data/timeline.json'] = encoded(data)
    return transaction(root, stage_generated(root, planned), '编辑履历', payload['revision'])


def undo(root, identity, expected):
    if not re.fullmatch(r'[A-Za-z0-9]+', identity):
        raise ValueError('历史编号有误。')
    folder = history_root(root)
    checked_local(root, f'output/workbench/history/{identity}.committed')
    record = json.loads(checked_local(root, f'output/workbench/history/{identity}.json').read_text())
    restore = {}
    for rel, item in record['files'].items():
        path = destination(root, rel)
        now = path.read_bytes() if path.exists() else None
        after = base64.b64decode(item['after']) if item['after'] is not None else None
        if now != after:
            raise Conflict('该记录之后已有修改，无法恢复。请先恢复更新的记录。')
        restore[rel] = base64.b64decode(item['before']) if item['before'] is not None else None
    return transaction(root, restore, '恢复 ' + identity, expected)
