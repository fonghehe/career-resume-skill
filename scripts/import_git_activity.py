#!/usr/bin/env python3
"""Read author-matched activity from local Git refs into a private JSON report."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

from career_data import activity, parse_iso_datetime, project_ids


def git(repo, *args):
    result = subprocess.run(
        ['git', '--no-pager', '--literal-pathspecs', '-c', 'log.showSignature=false', '-C', str(repo), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding='utf-8', errors='replace', check=False, timeout=60,
        env={**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0', 'GIT_OPTIONAL_LOCKS': '0'},
    )
    if result.returncode:
        # Avoid echoing repository paths, identities or subjects in diagnostics.
        raise ValueError('Unable to read Git repository; verify its path and access.')
    return result.stdout



def bounded_git(repo, *args, limit=65536):
    """Bound optional code evidence before decoding; external diff drivers are disabled."""
    command = ['git', '--no-pager', '--literal-pathspecs', '-C', str(repo), *args]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          env={**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0', 'GIT_OPTIONAL_LOCKS': '0'}) as process:
        raw = process.stdout.read(limit + 1)
        truncated = len(raw) > limit
        if truncated:
            process.kill()
        code = process.wait(timeout=30)
        if code and not truncated:
            raise ValueError('Unable to inspect requested Git evidence.')
    return {'text': raw[:limit].decode('utf-8', errors='replace'), 'truncated': truncated}


def repository_evidence(repo):
    readmes = []
    files = git(repo, 'ls-tree', '--name-only', 'HEAD', '--').splitlines() if git(repo, 'rev-list', '--all', '--max-count=1').strip() else []
    for name in files:
        if name.lower() in {'readme', 'readme.md', 'readme.txt', 'readme.rst'}:
            readmes.append({'path': name, **bounded_git(repo, 'show', 'HEAD:' + name, limit=16384)})
    tags = git(repo, 'for-each-ref', '--count=100', '--sort=-creatordate',
               '--format=%(refname:short)%09%(objectname)%09%(creatordate:iso-strict)', 'refs/tags').splitlines()
    return {'readmes': readmes, 'tags': [dict(zip(('tag', 'object', 'date'), line.split('\t'))) for line in tags],
            'note': 'README and tags describe repository context, not personal authorship or release ownership.'}

def collect(repo, author_emails, project_id='', *, mapping=None, details_limit=200):
    repo = Path(repo).resolve()
    if not repo.is_dir():
        raise ValueError('Repository directory does not exist.')
    if not author_emails or any(not value.strip() for value in author_emails):
        raise ValueError('Provide at least one nonempty author email.')
    if project_id and not re.fullmatch(r'[PO]\d{2,}', project_id):
        raise ValueError('Project ID must be P01 / O01 or another stable project ID.')
    top = Path(git(repo, 'rev-parse', '--show-toplevel').strip()).resolve()
    emails = {value.strip().casefold() for value in author_emails}
    raw = git(top, 'log', '--all', '--no-notes',
              '--format=%H%x00%aI%x00%cI%x00%ae%x00%s')
    records = {}
    for line in raw.splitlines():
        fields = line.split('\0', 4)
        if len(fields) != 5:
            raise ValueError('Unexpected Git log record format.')
        sha, authored, committed, email, subject = fields
        if email.casefold() not in emails:
            continue
        try:
            author_date = parse_iso_datetime(authored)
            committer_date = parse_iso_datetime(committed)
        except ValueError:
            raise ValueError('Invalid date in Git record.') from None
        if author_date.tzinfo is None or committer_date.tzinfo is None:
            raise ValueError('Git dates must include a timezone.')
        records[sha] = {
            'sha': sha, 'authorDate': authored, 'committerDate': committed,
            'authorEmail': email, 'subject': subject,
        }
    if type(details_limit) is not int or not 0 <= details_limit <= 2000:
        raise ValueError('Details limit must be between 0 and 2000.')
    ordered = sorted(records.values(), key=lambda item: (
        parse_iso_datetime(item['authorDate']), item['sha']))
    mapping = mapping or {}
    matched = {}
    for pid, paths in mapping.items():
        if not re.fullmatch(r'[PO]\d{2,}', pid) or not isinstance(paths, list) or not paths:
            raise ValueError('Mapping requires stable project IDs and nonempty path arrays.')
        if any(not isinstance(p, str) or not p or p.startswith('-') or Path(p).is_absolute()
               or '..' in Path(p).parts or '\\' in p for p in paths):
            raise ValueError('Mapping paths must be literal paths inside the repository.')
        matched[pid] = set(git(top, 'log', '--all', '--format=%H', '--', *paths).splitlines())
    recent = sorted(ordered, key=lambda r: r['authorDate'], reverse=True)[:details_limit]
    for record in recent:
        files = git(top, 'diff-tree', '--root', '-m', '--no-commit-id', '--name-only',
                    '-r', '-z', '--no-renames', record['sha'], '--')
        record['files'] = sorted(set(filter(None, files.split('\0'))))
    for record in ordered:
        record['projectIds'] = sorted(pid for pid, hashes in matched.items() if record['sha'] in hashes)
        if not mapping and project_id:
            record['projectIds'] = [project_id]
    statistics = activity([dict(r, repository=top.name) for r in ordered])
    statistics['fileEvidenceCommits'] = len(recent)
    evidence = repository_evidence(top)
    candidates = []
    for month in statistics['monthly']:
        items = [r for r in ordered if r['authorDate'].startswith(month)]
        kinds = activity([dict(r, repository=top.name) for r in items])['types']
        candidates.append({'date': month, 'status': 'pending', 'commitCount': len(items),
                           'types': kinds, 'evidenceShas': [r['sha'] for r in items],
                           'projectIds': sorted({p for r in items for p in r['projectIds']}),
                           'title': '代码活动阶段（待确认）'})
    note = ('Exact author-email match across local refs; unique commit hashes. '
            'Author Date is activity metadata, not employment, project dates, '
            'independent output or launch evidence. Mapping requires confirmation.')
    repository = None
    if ordered:
        repository = {
            'name': top.name, 'group': 'Git author activity', 'projectId': project_id,
            'start': ordered[0]['authorDate'], 'end': ordered[-1]['authorDate'],
            'count': len(ordered), 'tech': [], 'activity': statistics,
            'projectIds': sorted({p for r in ordered for p in r['projectIds']}),
            'projectCounts': {p: sum(p in r['projectIds'] for r in ordered)
                              for p in {p for r in ordered for p in r['projectIds']}}, 'dateBasis': 'author_date', 'note': note,
        }
    return {
        'schemaVersion': 1,
        'collectedAt': datetime.now(timezone.utc).isoformat(),
        'repositoryPath': str(top), 'authorEmails': sorted(emails),
        'projectId': project_id, 'mappingStatus': 'confirmed' if mapping else 'pending',
        'repositoryEvidence': evidence, 'stageCandidates': candidates,
        'scope': 'local_refs_only', 'dateBasis': 'author_date',
        'note': note, 'repository': repository, 'records': ordered,
        'timelineEvents': [{
            'id': top.name + ':' + record['sha'], 'repository': top.name,
            'projectId': project_id, **record,
        } for record in ordered],
    }


def collect_folder(folder, author_emails, *, mapping=None, details_limit=200):
    """Find local working repositories without following links or touching their state."""
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise ValueError('Project folder does not exist.')
    if not author_emails or any(not value.strip() for value in author_emails):
        raise ValueError('Provide at least one nonempty author email.')
    repositories = []
    excluded = {'.git', 'node_modules', '.venv', 'venv', '__pycache__',
                '.cache', 'dist', 'build', '.next', '.dart_tool'}
    def unreadable(_):
        raise ValueError('Unable to read part of the project folder; verify access.')
    for directory, folders, files in os.walk(folder, followlinks=False, onerror=unreadable):
        path = Path(directory)
        if '.git' in folders or '.git' in files:
            repositories.append(path)
        folders[:] = [name for name in folders if name not in excluded
                      and not (path / name).is_symlink()]
    reports, skipped = [], []
    for repo in sorted(repositories):
        label = repo.relative_to(folder).as_posix()
        if label == '.':
            label = folder.name
        try:
            report = collect(repo, author_emails, mapping=(mapping or {}).get(label), details_limit=details_limit)
            report['relativePath'] = label
            if report['repository']:
                report['repository']['name'] = label
            for event in report['timelineEvents']:
                event.update(id=label + ':' + event['sha'], repository=label)
            reports.append(report)
        except ValueError as exc:
            skipped.append({'relativePath': label, 'reason': str(exc)})
    return {
        'schemaVersion': 2, 'scope': 'local_refs_only',
        'collectedAt': datetime.now(timezone.utc).isoformat(),
        'folderPath': str(folder), 'authorEmails': sorted({e.strip().casefold() for e in author_emails}),
        'mappingStatus': 'pending', 'reports': reports, 'skipped': skipped,
        'note': 'Local author activity only; project stages and contributions need factual confirmation.',
    }


def write_report(report, output):
    output = Path(output)
    if output.is_symlink():
        raise ValueError('Refusing a symlink output path.')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Never replace a previous activity snapshot or another source file.
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--repo', type=Path, help='Local repository path')
    source.add_argument('--folder', type=Path, help='Read repositories in a project folder recursively')
    parser.add_argument('--author-email', required=True, action='append',
                        help='Exact author email; repeat for historical identities')
    parser.add_argument('--project-id', default='', help='Candidate mapping, e.g. P01')
    parser.add_argument('--mapping', type=Path, help='Confirmed JSON: repository name -> project ID -> literal paths')
    parser.add_argument('--details-limit', type=int, default=200, help='Recent commits with file evidence, max 2000')
    parser.add_argument('--inspect-commit', help='Inspect one author-matched SHA; bounded code diff')
    parser.add_argument('--output', type=Path, help='New private JSON file; never overwrites')
    args = parser.parse_args()
    if args.folder and args.project_id:
        parser.error('--project-id applies to --repo; folder mappings are organized by the agent.')
    try:
        mapping = json.loads(args.mapping.read_text()) if args.mapping else {}
        if not isinstance(mapping, dict):
            raise ValueError('Mapping must be an object.')
        report = (collect_folder(args.folder, args.author_email, mapping=mapping, details_limit=args.details_limit) if args.folder
                  else collect(args.repo, args.author_email, args.project_id, mapping=mapping.get(args.repo.resolve().name), details_limit=args.details_limit))
        if args.inspect_commit:
            if args.folder or args.inspect_commit not in {r['sha'] for r in report['records']}:
                raise ValueError('Inspection requires one author-matched SHA in a single repository.')
            report['codeEvidence'] = bounded_git(args.repo, 'show', '--format=', '--no-ext-diff', '--no-textconv', args.inspect_commit, '--')
        label = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        safe_name = re.sub(r'[^A-Za-z0-9_-]', '_', (args.folder or args.repo).resolve().name)
        output = args.output or Path(__file__).resolve().parents[1] / 'local/output' / 'git-activity' / f'{safe_name}-{label}.json'
        write_report(report, output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    count = (sum(len(item['records']) for item in report['reports']) if args.folder else len(report['records']))
    print(f'Saved {count} author-matched records to a private JSON report.')
    if args.folder:
        print(f'Read {len(report["reports"])} repositories; skipped {len(report["skipped"])} unreadable repositories.')
    print('Project mapping remains pending; no timeline or repository was modified.')


if __name__ == '__main__':
    main()
