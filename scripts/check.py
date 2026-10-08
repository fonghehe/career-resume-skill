#!/usr/bin/env python3
"""Validate a clean public export and run its tests/demo in a temporary directory."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from package import export
from validate import validate


def check(root, *, local=False, index=False):
    root = Path(root).resolve()
    if not shutil.which('git'):
        raise ValueError('Git is required for the regression suite (core profile tools do not need it).')
    if local:
        errors, _ = validate(root)
        if errors:
            raise ValueError('Local validation failed:\n' + '\n'.join(errors))
    if index:
        from check_public_index import check as check_index
        errors, _ = check_index(root)
        if errors:
            raise ValueError('Public Git index check failed:\n' + '\n'.join(errors))
    with tempfile.TemporaryDirectory(prefix='career-resume-skill-check-') as temporary:
        public = Path(temporary) / 'career-resume-skill'
        export(root, public, directory=True)
        for command in (
            [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
            [sys.executable, '-B', 'scripts/create_demo.py'],
            [sys.executable, '-B', 'scripts/build_career.py'],
            [sys.executable, '-B', 'scripts/build_timeline.py'],
            [sys.executable, '-B', 'scripts/validate.py'],
        ):
            subprocess.run(command, cwd=public, check=True)
    print('OK: clean public export, regression tests, fictional demo and empty timeline.', flush=True)
    print('Scope: no model/attachment/ATS/visual verification; personal data checked only with --local.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--local', action='store_true', help='Also validate existing local career files')
    parser.add_argument('--index', action='store_true', help='Also inspect the actual Git index')
    args = parser.parse_args()
    try:
        check(args.root, local=args.local, index=args.index)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
