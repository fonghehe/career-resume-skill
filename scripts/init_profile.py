#!/usr/bin/env python3
"""Create missing, Git-ignored local career files without replacing user data."""

import argparse
from pathlib import Path

from bundle import STARTER_FILES, checked_file, starter_source
from career_data import profile_root


def initialize(root):
    root = Path(root).resolve()
    profile = profile_root(root)
    pending = []
    skipped = 0
    for rel in STARTER_FILES:
        if rel == '.gitignore':
            continue
        source = checked_file(root, starter_source(rel))
        target = profile / rel.removeprefix('local/')
        for path in (target, *target.parents):
            if path == root:
                break
            if path.is_symlink():
                raise ValueError('Refusing a symlink in local profile paths.')
        if target.exists():
            if not target.is_file():
                raise ValueError('A local profile file path is occupied by a directory.')
            skipped += 1
        else:
            pending.append((source, target))
    for source, target in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(source.read_bytes())
    return len(pending), skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--workspace', type=Path,
                        help='Create a complete, clean private workspace in a NEW directory')
    args = parser.parse_args()
    try:
        if args.workspace:
            # Reuse the public boundary rather than copying an installed user's data.
            from package import export
            count = export(args.root, args.workspace, directory=True)
            print(f'Created clean workspace: {args.workspace.resolve()} ({count} files).')
            print('Use this workspace for career data; the source installation was preserved.')
            return
        created, skipped = initialize(args.root)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f'Created {created} local files; preserved {skipped} existing files.')
    print('Local profiles and generated data are ignored by Git.')


if __name__ == '__main__':
    main()
