#!/usr/bin/env python3
"""Merge a factual delta, preview conflicts, snapshot changes and undo safely."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

from build_timeline import build, build_project_details, embed_sources, validate_data
from career_data import checked_local, summarize_repositories, profile_root

ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = {'career': 'id', 'projects': 'id', 'repositories': 'name', 'gitEvents': 'id'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def atomic(path, raw):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def merge(current, delta, corrections=()):
    if not isinstance(delta, dict) or set(delta) - set(COLLECTIONS) - {'profile', 'meta'}:
        raise ValueError('Delta accepts career/projects/repositories/gitEvents/profile/meta only.')
    result = copy.deepcopy(current)
    changes, conflicts = [], []
    corrections = set(corrections)
    for collection, patch in delta.items():
        if collection in ('profile', 'meta'):
            if not isinstance(patch, dict):
                raise ValueError('Metadata delta must be an object.')
            rows = [(collection, result[collection], patch)]
        else:
            if not isinstance(patch, list):
                raise ValueError('Collection delta must be an array.')
            key = COLLECTIONS[collection]
            index = {r[key]: r for r in result.setdefault(collection, [])}
            seen = set()
            rows = []
            for item in patch:
                if not isinstance(item, dict) or not isinstance(item.get(key), str) or item[key] in seen:
                    raise ValueError('Delta identities must be present and unique.')
                seen.add(item[key])
                identity = item[key]
                # Commit identity is repository + SHA, even if the incoming event ID differs.
                if collection == 'gitEvents':
                    match = next((r for r in index.values() if (r['repository'], r['sha']) ==
                                  (item.get('repository'), item.get('sha'))), None)
                    if match:
                        identity = match['id']
                        item = {**item, 'id': identity}
                if identity not in index:
                    result[collection].append(copy.deepcopy(item))
                    index[identity] = result[collection][-1]
                    changes.append({'record': f'{collection}/{identity}', 'action': 'added'})
                else:
                    rows.append((f'{collection}/{identity}', index[identity], item))
        for label, old, new in rows:
            locked = set(old.get('confirmedFields', []))
            locked.update(s['field'] for s in old.get('sources', []) if s.get('status') == 'confirmed')
            if label.startswith('gitEvents/'):
                locked.update({'id', 'repository', 'sha', 'authorDate', 'committerDate', 'subject'})
            if old.get('status') == 'confirmed':
                locked.update(set(old) - {'sources', 'confirmedFields'})
            for field, value in new.items():
                if field in ('sources', 'confirmedFields'):
                    if not isinstance(value, list):
                        raise ValueError('Sources and confirmed fields must be arrays.')
                    combined = copy.deepcopy(old.get(field, []))
                    for entry in value:
                        if entry not in combined:
                            combined.append(copy.deepcopy(entry))
                    value = combined
                if old.get(field) == value:
                    continue
                pointer = f'{label}.{field}'
                append_only_stages = (field == 'milestones' and isinstance(value, list) and isinstance(old.get(field), list)
                                      and value[:len(old[field])] == old[field])
                immutable_commit = label.startswith('gitEvents/') and field in {'id', 'repository', 'sha', 'authorDate', 'committerDate', 'subject'}
                if field in locked and not append_only_stages and (pointer not in corrections or immutable_commit):
                    conflicts.append({'field': pointer, 'current': old.get(field), 'proposed': value})
                    continue
                changes.append({'record': label, 'field': field, 'before': old.get(field), 'after': value})
                old[field] = copy.deepcopy(value)
    result['repositories'] = summarize_repositories(result.get('gitEvents', []), result['repositories'])
    validate_data(result)
    return result, {'changes': changes, 'conflicts': conflicts}


def safe_destination(root, relative):
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Refusing a symlink profile destination.')
    return path


def update(root, delta=None, *, apply=False, corrections=(), undo=None):
    root = profile_root(root)
    path = checked_local(root, 'data/timeline.json')
    history = safe_destination(root, 'output/updates')
    lock = safe_destination(root, 'data/.update.lock')
    # Preview also takes a lock, so applied changes cannot race its snapshot.
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        before = path.read_bytes()
        if undo:
            if not undo.isalnum():
                raise ValueError('Invalid update ID.')
            record = json.loads(checked_local(root, f'output/updates/{undo}/report.json').read_text())
            if not record.get('applied'):
                raise ValueError('This update was not successfully applied.')
            if digest(before) != record['afterHash']:
                raise ValueError('Profile changed since this update; refusing to undo newer changes.')
            after = checked_local(root, f'output/updates/{undo}/before.json').read_bytes()
            report = {'changes': [{'action': 'undo', 'update': undo}], 'conflicts': []}
            result = json.loads(after)
            validate_data(result)
        else:
            result, report = merge(json.loads(before), delta, corrections)
            after = encode(result)
        embed_sources(copy.deepcopy(result), root)
        build_project_details(result, root)  # Missing sources/cards/assets fail before writing.
        safe_destination(root, 'showcase/project-timeline.html')
        if not apply:
            return report
        if before == after or not report['changes']:
            return {**report, 'applied': False}
        identity = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        folder = history / identity
        folder.mkdir(parents=True)
        report.update(id=identity, beforeHash=digest(before), afterHash=digest(after), applied=False)
        (folder / 'before.json').write_bytes(before)
        (folder / 'report.json').write_bytes(encode(report))
        if path.read_bytes() != before:
            raise ValueError('Profile changed during the update.')
        atomic(path, after)
        try:
            build(root)
        except Exception:
            atomic(path, before)
            raise
        report['applied'] = True
        atomic(folder / 'report.json', encode(report))
        return report
    finally:
        os.close(fd)
        lock.unlink()


def git_delta(root, report):
    root = profile_root(root)
    current = json.loads(checked_local(root, 'data/timeline.json').read_text())
    old_events = {(r['repository'], r['sha']): r for r in current.get('gitEvents', [])}
    old_repos = {r['name']: r for r in current['repositories']}
    repositories, events = [], []
    for item in report.get('reports', [report]):
        repo = item.get('repository')
        if not repo:
            continue
        repo = copy.deepcopy(repo)
        old = old_repos.get(repo['name'], {})
        if item.get('mappingStatus') != 'confirmed':
            for field in ('projectId', 'projectIds', 'projectCounts'):
                if field in old:
                    repo[field] = old[field]
        repositories.append(repo)
        for event in item['timelineEvents']:
            event = copy.deepcopy(event)
            previous = old_events.get((event['repository'], event['sha']), {})
            if item.get('mappingStatus') != 'confirmed':
                for field in ('projectId', 'projectIds'):
                    if field in previous:
                        event[field] = previous[field]
                if not project_ids_for_delta(event) and old.get('projectId'):
                    event['projectId'] = old['projectId']
                    event['projectIds'] = [old['projectId']]
            events.append(event)
    return {'repositories': repositories, 'gitEvents': events}


def project_ids_for_delta(record):
    return record.get('projectIds') or record.get('projectId')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--delta', type=Path)
    source.add_argument('--git-report', type=Path, help='Merge an import_git_activity report')
    source.add_argument('--undo', help='Update ID to undo, only if current data still matches')
    parser.add_argument('--apply', action='store_true', help='Default is preview only')
    parser.add_argument('--confirmed-correction', action='append', default=[], help='Field pointer explicitly corrected by the user')
    args = parser.parse_args()
    try:
        delta = json.loads(args.delta.read_text()) if args.delta else None
        if args.git_report:
            delta = git_delta(args.workspace, json.loads(args.git_report.read_text()))
        print(json.dumps(update(args.workspace, delta, apply=args.apply, corrections=args.confirmed_correction,
                                undo=args.undo), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
