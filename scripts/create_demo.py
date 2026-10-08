#!/usr/bin/env python3
"""Build a fictional timeline example without reading or replacing user records."""

import argparse
from pathlib import Path
import shutil

from build_timeline import build
from bundle import checked_file

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = (
    'data/timeline.json',
    'references/projects/sample-portal.md',
    'references/projects/sample-console.md',
    'references/projects/sample-notebook.md',
    'references/sources/demo-resume.md', 'references/attachments/demo-phases.png',
    'references/attachments/demo-release.md',
)


def create(root=ROOT, output=None, *, docs=False):
    root = Path(root).resolve()
    source = root / 'assets/examples/career-demo'
    for rel in FIXTURES:
        checked_file(root, 'assets/examples/career-demo/' + rel)
    if docs:
        if output is not None:
            raise ValueError('Docs mode has a fixed output path.')
        # Only the explicit fictional fixture is loaded, never root/data/.
        target = root / 'docs/public/demo/timeline.html'
        if any(path.is_symlink() for path in (target, *target.parents)):
            raise ValueError('Refusing a symlink documentation output path.')
        return build(source, target)
    raw = Path(output) if output is not None else root / 'local/output/demo'
    if any(path.is_symlink() for path in (raw, *raw.parents)):
        raise ValueError('Refusing a symlink output directory.')
    target = raw.resolve()
    if target == root or target in root.parents:
        raise ValueError('Demo must not replace the project or its parents.')
    if root in target.parents and not (target.is_relative_to(root / 'output') or target.is_relative_to(root / 'local/output')):
        raise ValueError('A demo inside the project must be under local/output/.')
    if target.exists():
        raise ValueError('Demo directory exists; choose a new --output directory.')
    target.mkdir(parents=True)
    for rel in FIXTURES:
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, path)
    return build(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--output', type=Path, help='New demonstration directory')
    mode.add_argument('--docs', action='store_true', help='Rebuild the public fictional docs example')
    args = parser.parse_args()
    try:
        result = create(output=args.output, docs=args.docs)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    print('Created fictional example: ' + str(result))


if __name__ == '__main__':
    main()
