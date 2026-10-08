#!/usr/bin/env python3
"""Aggregate maintained Markdown records into a private written career artifact."""

import argparse
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from career_data import checked_local, profile_root

ROOT = Path(__file__).resolve().parents[1]
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
    target.write_text('\n'.join(lines), encoding='utf-8')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, help='Generated Markdown path inside the profile output directory')
    args = parser.parse_args()
    try:
        target = build(args.root, args.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print('Created written career: ' + str(target))
    print('Scope: existing records only; no attachment extraction, fact verification or resume generation.')


if __name__ == '__main__':
    main()
