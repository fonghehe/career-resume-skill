#!/usr/bin/env python3
"""Export a public starter bundle by default, or an explicit personal backup."""

import argparse
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

from bundle import personal_entries, public_entries
from validate import validate


def write_tree(entries, target):
    for relative, source in sorted(entries.items()):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, path)


def export(root, output, *, include_personal=False, directory=False, overwrite=False):
    root = Path(root).resolve()
    raw_output = Path(output).absolute()
    if raw_output.is_symlink():
        raise ValueError('Refusing a symlink output path')
    output = raw_output.resolve()
    if output == root or output in root.parents:
        raise ValueError('Output must not replace the skill or its parent directory')
    if root in output.parents and not (output.is_relative_to(root / 'dist') or output.is_relative_to(root / 'local/dist')):
        raise ValueError('An output inside the skill must be under local/dist/')
    if directory and include_personal:
        raise ValueError('--public-dir cannot be combined with --include-personal')
    if directory and overwrite:
        raise ValueError('Directory export never overwrites an existing directory')
    if output.exists() and (directory or not overwrite):
        raise ValueError(f'Output already exists: {output}')
    entries = personal_entries(root) if include_personal else public_entries(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.career-resume-skill-', dir=output.parent) as temp:
        staging = Path(temp) / 'career-resume-skill'
        staging.mkdir()
        write_tree(entries, staging)
        errors, _ = validate(staging)
        if errors:
            raise ValueError('Export validation failed:\n' + '\n'.join(errors))
        if directory:
            # Exclusive mkdir prevents accidentally merging into an existing tree.
            output.mkdir()
            try:
                write_tree(entries, output)
            except Exception:
                shutil.rmtree(output)
                raise
        else:
            archive_path = Path(temp) / 'bundle.zip'
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
                for relative in sorted(entries):
                    archive.write(staging / relative, 'career-resume-skill/' + relative)
            if overwrite:
                os.replace(archive_path, output)
            else:
                with output.open('xb') as target, archive_path.open('rb') as source:
                    shutil.copyfileobj(source, target)
    return len(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='ZIP output path')
    parser.add_argument('--overwrite', action='store_true', help='Replace a ZIP deliberately')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--include-personal', action='store_true', help='Sensitive personal backup')
    mode.add_argument('--public-dir', type=Path, help='Export public tree to a new directory')
    args = parser.parse_args()
    if args.public_dir and args.output:
        parser.error('--output is for ZIP mode; use --public-dir alone')
    root = Path(__file__).resolve().parent.parent
    filename = 'career-resume-skill-personal.zip' if args.include_personal else 'career-resume-skill-public.zip'
    output = args.public_dir or args.output or root / 'local/dist' / filename
    try:
        count = export(root, output, include_personal=args.include_personal,
                       directory=bool(args.public_dir), overwrite=args.overwrite)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    kind = 'PERSONAL backup (contains candidate data)' if args.include_personal else 'PUBLIC starter'
    print(f'Created {kind}: {output.resolve()} ({count} files)')


if __name__ == '__main__':
    main()
