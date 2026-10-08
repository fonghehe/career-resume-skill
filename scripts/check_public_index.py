#!/usr/bin/env python3
"""Reject tracked personal paths and nonempty starter data before committing."""

import argparse
import json
from pathlib import Path
import subprocess

from bundle import repository_entries


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise ValueError('Unable to read Git index; run from a Git working tree.')
    return result.stdout


def check(root):
    root = Path(root).resolve()
    allowed = set(repository_entries(root))
    paths = git(root, 'ls-files', '--cached', '-z').decode().split('\0')
    paths = {path for path in paths if path}
    errors = [f'Non-public path in Git index: {path}' for path in sorted(paths - allowed)]
    for rel in ('assets/starter/data/timeline.json', 'assets/starter/references/sources/manifest.json'):
        if rel not in paths:
            continue
        try:
            data = json.loads(git(root, 'show', ':' + rel))
            if rel.endswith('timeline.json'):
                if any(data.get(key) != [] for key in ('career', 'projects', 'repositories')) or any(
                        data.get(key, []) != [] for key in ('memories', 'gitEvents', 'questions')):
                    errors.append('Starter timeline must not contain career/project/Git records.')
                if any(data.get('profile', {}).values()):
                    errors.append('Starter profile must not contain personal information.')
                leadership = data.get('leadership', {})
                if any(leadership.values()):
                    errors.append('Starter leadership must not contain personal information.')
            elif data.get('sources') != []:
                errors.append('Starter source manifest must be empty.')
        except (ValueError, TypeError, AttributeError):
            errors.append(f'Invalid starter JSON in Git index: {rel}')
    return errors, len(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        errors, count = check(args.root)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    for error in errors:
        print('ERROR: ' + error)
    if errors:
        return 1
    print(f'OK: {count} indexed files belong to the public repository inventory.')
    print('Scope: path and starter-data checks; review newly edited public file content separately.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
