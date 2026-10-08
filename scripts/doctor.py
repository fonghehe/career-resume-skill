#!/usr/bin/env python3
"""Report local prerequisites without installing software or changing career data."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

from bundle import repository_entries, read_version
from career_data import profile_root


def probe(command):
    if not shutil.which(command):
        return None
    try:
        result = subprocess.run([command, '--version'], capture_output=True,
                                text=True, timeout=10, check=False)
        if result.returncode:
            return None
        return result.stdout.strip().splitlines()[0]
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return None


def diagnose(root, *, docs=False):
    root = Path(root).resolve()
    rows = []
    rows.append(('OK' if sys.version_info >= (3, 9) else 'ERROR',
                 'Python ' + sys.version.split()[0] + ' (requires 3.9+)'))
    try:
        entries = repository_entries(root)
        version = read_version(root)
        rows.append(('OK', f'career-resume-skill {version}; complete public resources: {len(entries)} files'))
    except (ValueError, OSError) as exc:
        rows.append(('ERROR', str(exc) + '; obtain the complete project directory'))
    git = probe('git')
    rows.append(('OK' if git else 'INFO', git or 'Git unavailable; only Git collection/checks require it'))
    try:
        profile = profile_root(root)
    except ValueError as exc:
        rows.append(('ERROR', str(exc)))
        return rows
    missing = [rel for rel in ('references/profile.md', 'references/facts.md',
                              'data/timeline.json') if not (profile / rel).is_file()]
    rows.append(('INFO' if missing else 'OK',
                 'Local profile not initialized; run scripts/init_profile.py in your private workspace'
                 if missing else 'Local profile files present (contents not read)'))
    if docs:
        node = probe('node')
        pnpm = probe('pnpm')
        for label, value, minimum in (('Node.js', node, 22), ('pnpm', pnpm, 11)):
            try:
                major = int((value or '').lstrip('v').split('.')[0])
            except ValueError:
                major = 0
            valid = major >= minimum if label == 'Node.js' else major == minimum
            rows.append(('OK' if valid else 'ERROR',
                         f'{label}: {value or "unavailable"}; requires '
                         + (f'{minimum}+' if label == 'Node.js' else f'{minimum}.x (see packageManager)')))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--docs', action='store_true', help='Also check optional documentation runtimes')
    args = parser.parse_args()
    rows = diagnose(args.root, docs=args.docs)
    for status, message in rows:
        print(f'{status}: {message}')
    print('Scope: local prerequisites only; attachment access and model behavior require a host test.')
    return int(any(status == 'ERROR' for status, _ in rows))


if __name__ == '__main__':
    raise SystemExit(main())
