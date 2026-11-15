#!/usr/bin/env python3
"""Aggregate maintained Markdown records into a private written career artifact."""

from career_resume import ROOT
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from career_resume.career_data import checked_local, profile_root
from career_resume.file_io import atomic_write

MARKER = '<!-- career-resume-skill:generated-career -->'
LEGACY_MARKER = '<!-- career-skill:generated-career -->'
RECORDS = (
    ('履历入口', 'references/career/README.md'),
    ('个人档案与任职', 'references/profile.md'),
    ('事实、确认与更正', 'references/facts.md'),
    ('项目索引', 'references/project-index.md'),
    ('来源索引', 'references/sources.md'),
    ('待确认事项', 'references/questions-to-confirm.md'),
)


def relative_link(path, parent):
    return Path(os.path.relpath(path, parent)).as_posix()


def relocated_markdown(text, source, target):
    """Keep local links usable and nest headings without rewriting factual text."""
    def link(match):
        address = match.group(2).strip().strip('<>')
        if not address or address.startswith('#') or urlsplit(address).scheme:
            return match.group(0)
        path, separator, fragment = address.partition('#')
        relocated = relative_link(source.parent / path, target.parent)
        if separator:
            relocated += '#' + fragment
        return match.group(1) + '<' + relocated + '>)'

    lines = []
    fence = None
    for line in text.splitlines():
        delimiter = re.match(r'^\s*(`{3,}|~{3,})', line)
        if delimiter:
            token = delimiter.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            lines.append(line)
            continue
        if fence is None:
            line = re.sub(r'^#{1,6}(?=\s)', lambda m: '#' * min(6, len(m[0]) + 2), line)
            line = re.sub(r'(!?\[[^\]\n]*\]\()([^\n)]+)\)', link, line)
        lines.append(line)
    return '\n'.join(lines)


def career_records(profile):
    """Include maintained career notes, excluding the already included entrypoint."""
    folder = profile / 'references/career'
    if folder.is_symlink():
        raise ValueError('Refusing a symlink career directory.')
    records = []
    for directory, folders, files in os.walk(folder):
        folders.sort()
        for name in folders:
            if (Path(directory) / name).is_symlink():
                raise ValueError('Refusing a symlink career record directory.')
        for name in sorted(files):
            path = Path(directory) / name
            if path.suffix != '.md' or path == folder / 'README.md':
                continue
            records.append(checked_local(profile, path.relative_to(profile).as_posix()))
    return sorted(records)


def build(root=ROOT, output=None):
    profile = profile_root(root)
    target = Path(output).absolute() if output else profile / 'output/career/career.md'
    if any(path.is_symlink() for path in (target, *target.parents)):
        raise ValueError('Refusing a symlink career output path.')
    target = target.resolve()
    if not target.is_relative_to(profile / 'output') or target.suffix != '.md':
        raise ValueError('Written career output must be a Markdown file inside profile/output/.')
    if target.exists() and (not target.is_file() or not target.read_text(encoding='utf-8').startswith(
            (MARKER + '\n', LEGACY_MARKER + '\n'))):
        raise ValueError('Refusing to replace a file that is not a generated career artifact.')

    records = [(label, checked_local(profile, path)) for label, path in RECORDS]
    records += [('职业详细记录', path) for path in career_records(profile)]
    projects = profile / 'references/projects'
    if projects.is_symlink():
        raise ValueError('Refusing a symlink project directory.')
    records += [('项目详细记录', checked_local(profile, path.relative_to(profile).as_posix()))
                for path in sorted(projects.glob('*.md'))]
    synthetic = False
    if (profile / 'data/timeline.json').exists():
        data = json.loads(checked_local(profile, 'data/timeline.json').read_text(encoding='utf-8'))
        if not isinstance(data, dict) or not isinstance(data.get('meta', {}), dict):
            raise ValueError('Timeline metadata must be an object.')
        synthetic = data.get('meta', {}).get('synthetic', False)

    lines = [MARKER, '# 职业履历', '',
             '由已有 Markdown 记录聚合，保留来源状态与待确认信息。修改源记录后重新生成；此文件不是投递简历。', '']
    if synthetic:
        lines += ['> 虚构教学履历，不属于使用者，不可用于真实投递。', '']
    for label, source in records:
        text = source.read_text(encoding='utf-8')
        lines += ['## ' + label, '',
                  '[源记录](<' + relative_link(source, target.parent) + '>)', '',
                  relocated_markdown(text, source, target), '']
    # Read all inputs before creating output, preserving sources even on failure.
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(target, '\n'.join(lines).encode('utf-8'))
    return target
