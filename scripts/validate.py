#!/usr/bin/env python3
"""Check portable skill structure, sources and optional timeline, using stdlib."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from bundle import PUBLIC_FILES, STARTER_FILES, read_version
from career_data import profile_root

IGNORED = {'dist', 'output', '.git', '__pycache__', 'node_modules',
           '.vitepress', 'private', 'uploads', 'local'}


def local_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'Path escapes bundle: {relative}')
    return path


def validate(root):
    root = Path(root).resolve()
    errors = []
    # Candidate files may be empty, but the portable workflow remains complete.
    try:
        profile = profile_root(root)
    except ValueError as exc:
        return [str(exc)], 0
    required = PUBLIC_FILES
    for rel in required:
        if not (root / rel).is_file():
            errors.append(f'Missing required file: {rel}')
    for rel in STARTER_FILES:
        path = root / rel if rel == '.gitignore' else profile / rel.removeprefix('local/')
        if not path.is_file():
            errors.append(f'Missing required file: {rel}')
    if (root / 'VERSION').is_file():
        try:
            read_version(root)
        except (ValueError, OSError) as exc:
            errors.append(f'Invalid release version: {exc}')
    entry = root / 'SKILL.md'
    if entry.is_file():
        front = re.match(r'\A---\n(.*?)\n---\n', entry.read_text(encoding='utf-8'), re.S)
        if not front:
            errors.append('SKILL.md must start with YAML frontmatter')
        else:
            fields = {}
            for line in front.group(1).splitlines():
                key, sep, value = line.partition(':')
                if not sep or key not in {'name', 'description'} or not value.strip() or key in fields:
                    errors.append(f'Invalid frontmatter line: {line}')
                fields[key] = value.strip()
            if fields.get('name') != 'career-resume-skill' or not fields.get('description'):
                errors.append('Frontmatter requires name: career-resume-skill and a description')
    md_files = []
    for directory, folders, files in os.walk(root):
        folders[:] = [name for name in folders if name not in IGNORED]
        md_files.extend(Path(directory) / name for name in files if name.endswith('.md'))
    if profile != root:
        if (profile / 'README.md').is_file():
            md_files.append(profile / 'README.md')
        for directory, folders, files in os.walk(profile / 'references'):
            folders[:] = [name for name in folders if name not in IGNORED]
            md_files.extend(Path(directory) / name for name in files if name.endswith('.md'))
    for path in md_files:
        try:
            text = path.read_text(encoding='utf-8')
            if '\ufffd' in text:
                errors.append(f'Unicode replacement character: {path.relative_to(root)}')
            for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)', text):
                target = target.strip().strip('<>')
                if not target or target.startswith('#') or urlsplit(target).scheme:
                    continue
                resolved = local_path(root, str(path.parent.relative_to(root) / unquote(target.split('#', 1)[0])))
                if not resolved.is_file() and profile == root and resolved.is_relative_to(root / 'local'):
                    # New documentation also remains usable with an initialized legacy dataset.
                    resolved = local_path(root, str(resolved.relative_to(root / 'local')))
                if not resolved.is_file():
                    errors.append(f'Broken link in {path.relative_to(root)}: {target}')
        except (ValueError, OSError) as exc:
            errors.append(f'Invalid Markdown {path.relative_to(root)}: {exc}')
    root = profile
    manifest = root / 'references/sources/manifest.json'
    if manifest.is_file():
        try:
            records = json.loads(manifest.read_text(encoding='utf-8'))['sources']
            if not isinstance(records, list):
                raise ValueError('sources must be an array')
            ids = [r['id'] for r in records]
            if len(ids) != len(set(ids)):
                raise ValueError('Source IDs must be unique')
            for record in records:
                if not isinstance(record['id'], str) or not record['id']:
                    raise ValueError('Source ID must be a nonempty string')
                if 'sha256' in record and not re.fullmatch(r'[0-9a-f]{64}', record['sha256']):
                    raise ValueError(f"Invalid original file SHA-256: {record['id']}")
                snapshot = local_path(root, record['extracted_text'])
                text = snapshot.read_text(encoding='utf-8')
                if 'pages' in record:
                    pages = record['pages']
                    if type(pages) is not int or pages < 1:
                        raise ValueError('Source pages must be a positive integer')
                    if re.findall(r'^## Page (\d+)$', text, re.M) != [str(n) for n in range(1, pages + 1)]:
                        raise ValueError(f"Missing or unordered source pages: {record['id']}")
        except (ValueError, KeyError, TypeError, OSError) as exc:
            errors.append(f'Invalid source manifest/snapshot: {exc}')
    cards = {}
    index = root / 'references/project-index.md'
    index_text = index.read_text(encoding='utf-8') if index.is_file() else ''
    for path in (root / 'references/projects').glob('*.md'):
        text = path.read_text(encoding='utf-8')
        match = re.match(r'# ([PO]\d{2,})｜', text)
        if not match:
            errors.append(f'Missing project ID in card heading: {path.name}')
            continue
        pid = match.group(1)
        if pid in cards:
            errors.append(f'Duplicate project ID: {pid}')
        cards[pid] = path
        if f'projects/{path.name}' not in index_text:
            errors.append(f'Unindexed project card: {path.name}')
        if any(prefix != pid for prefix in re.findall(r'\b([PO]\d{2,})-[A-Z0-9]+\b', text)):
            errors.append(f'Project item IDs do not match heading: {path.name}')
        if 'fabricated-excluded' in text or 'synthetic-draft' in text:
            errors.append(f'Excluded or synthetic content must not be an active card: {path.name}')
    timeline = root / 'data/timeline.json'
    if timeline.is_file():
        try:
            from build_timeline import validate_data
            data = json.loads(timeline.read_text(encoding='utf-8'))
            validate_data(data)
            for project in data['projects']:
                if project['id'] not in cards:
                    errors.append(f"Missing timeline project card: {project['id']}")
            for html in (root / 'showcase').glob('*.html'):
                text = html.read_text(encoding='utf-8')
                # Other independent HTML files do not claim to be this timeline.
                if 'id="timeline-data"' not in text:
                    continue
                for element, expected in (('timeline-data', data),):
                    embedded = re.search(r'<script id="' + element + r'" type="application/json">(.*?)</script>', text, re.S)
                    if not embedded or json.loads(embedded.group(1)) != expected:
                        errors.append(f'Timeline HTML is stale: {html.name}')
                embedded = re.search(r'<script id="project-details" type="application/json">(.*?)</script>', text, re.S)
                if not embedded:
                    errors.append(f'Missing embedded project details: {html.name}')
                else:
                    details = json.loads(embedded.group(1))
                    if set(details) != {p['id'] for p in data['projects']}:
                        errors.append(f'Timeline detail IDs do not match projects: {html.name}')
                    for pid, detail in details.items():
                        path = local_path(root, detail['path'])
                        if pid not in cards or path != cards[pid].resolve() or detail['markdown'] != path.read_text(encoding='utf-8'):
                            errors.append(f'Timeline project detail is stale: {pid}')
        except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
            errors.append(f'Invalid timeline data/HTML: {exc}')
    return errors, len(md_files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--personal', action='store_true', help='Also check original author dataset invariants')
    args = parser.parse_args()
    errors, count = validate(args.root)
    if args.personal:
        try:
            from validate_personal import validate as validate_personal
            personal_errors, _ = validate_personal(args.root)
            errors.extend(personal_errors)
        except ImportError:
            errors.append('Personal validator is available only in the original private working copy')
    for error in errors:
        print(f'ERROR: {error}', file=sys.stderr)
    if errors:
        return 1
    print(f'OK: {count} Markdown files; structure, sources and optional timeline checked.')
    print('Scope: no external fact, ATS, visual rendering or client compatibility verification.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
