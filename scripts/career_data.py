"""Shared factual associations, activity summaries and local asset boundaries."""
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import re


def parse_iso_datetime(value):
    """Accept UTC's ISO 8601 Z suffix on Python 3.9 without rewriting evidence."""
    if value.endswith('Z'):
        value = value[:-1] + '+00:00'
    return datetime.fromisoformat(value)


def profile_root(root):
    """Resolve the consolidated local workspace, retaining legacy dataset support."""
    root = Path(root).resolve()
    local = root / 'local'
    if local.is_symlink() or (root / 'data').is_symlink():
        raise ValueError('Refusing a symlink profile directory.')
    if (local / 'data').is_symlink() or (local / 'references').is_symlink():
        raise ValueError('Refusing a symlink profile directory.')
    if (local / 'data').exists() or (local / 'references').exists():
        if (root / 'data/timeline.json').exists() or (root / 'references/profile.md').exists():
            raise ValueError('Both local and legacy profiles exist; choose the dataset directory explicitly.')
        return local
    if (root / 'data').exists() or (root / 'references/profile.md').exists():
        return root
    return local if (root / 'SKILL.md').is_file() else root


def project_ids(record):
    return sorted(set(record.get('projectIds', []) + ([record['projectId']] if record.get('projectId') else [])))


def activity(records):
    unique = {(r['repository'], r['sha']): r for r in records}
    monthly, modules, kinds = Counter(), Counter(), Counter()
    for r in unique.values():
        monthly[r['authorDate'][:7]] += 1  # Original author timezone, not UTC conversion.
        match = re.match(r'^(feat|fix|docs|test|refactor|chore|perf|build|ci)(?:\([^)]*\))?[!:]', r['subject'])
        kinds[match.group(1) if match else 'other'] += 1
        for module in {p.split('/')[0] if '/' in p else '(root)' for p in r.get('files', [])}:
            modules[module] += 1
    return {'monthly': dict(sorted(monthly.items())), 'modules': dict(modules.most_common(12)),
            'types': dict(kinds), 'activeMonths': len(monthly), 'count': len(unique)}


def summarize_repositories(events, existing):
    grouped = defaultdict(list)
    for event in events:
        grouped[event['repository']].append(event)
    result = []
    for repo in existing:
        records = grouped.get(repo['name'], [])
        if not records:
            result.append(repo)
            continue
        ordered = sorted(records, key=lambda r: (parse_iso_datetime(r['authorDate']), r['sha']))
        mapped = defaultdict(list)
        for r in ordered:
            for pid in project_ids(r):
                mapped[pid].append(r)
        # Recompute only for complete imports. A partial list must not erase a summary.
        if len(ordered) < repo.get('count', 0):
            result.append(repo)
            continue
        result.append({**repo, 'count': len(ordered), 'start': ordered[0]['authorDate'],
                       'end': ordered[-1]['authorDate'], 'firstMessage': ordered[0]['subject'],
                       'lastMessage': ordered[-1]['subject'], 'activity': activity(ordered),
                       'projectIds': sorted(mapped),
                       'projectCounts': {p: len(v) for p, v in mapped.items()}})
    return result


def checked_local(root, relative):
    root = Path(root).resolve()
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('Expected a relative local file path.')
    raw = Path(relative)
    if raw.is_absolute() or '..' in raw.parts:
        raise ValueError('Local file must stay inside the profile.')
    path = root / raw
    for item in (path, *path.parents):
        if item == root:
            break
        if item.is_symlink():
            raise ValueError('Symlink local assets are not supported.')
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError('Missing local asset inside profile.')
    return path
