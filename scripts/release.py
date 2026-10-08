#!/usr/bin/env python3
"""Build a versioned public ZIP and SHA256SUMS locally; never publish or include personal data."""

import argparse
import hashlib
from pathlib import Path
import shutil
import tempfile

from bundle import read_version
from package import export


def build_release(root, output=None):
    root = Path(root).resolve()
    version = read_version(root)
    raw = Path(output).absolute() if output is not None else root / 'local/dist/releases' / version
    if raw.is_symlink():
        raise ValueError('Refusing a symlink release output.')
    target = raw.resolve()
    if target == root or target in root.parents:
        raise ValueError('Release must not replace the project or its parents.')
    if root in target.parents and not (target.is_relative_to(root / 'dist') or target.is_relative_to(root / 'local/dist')):
        raise ValueError('A release inside the project must be under local/dist/.')
    if target.exists():
        raise ValueError('Release output exists; choose a new directory. Existing artifacts are preserved.')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.career-release-', dir=target.parent) as temporary:
        staging = Path(temporary)
        archive = staging / f'career-resume-skill-{version}.zip'
        export(root, archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (staging / 'SHA256SUMS').write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
        target.mkdir()
        try:
            for path in staging.iterdir():
                shutil.copyfile(path, target / path.name)
        except Exception:
            shutil.rmtree(target)
            raise
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, help='New release directory (default local/dist/releases/VERSION)')
    args = parser.parse_args()
    try:
        target = build_release(Path(__file__).resolve().parents[1], args.output_dir)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print('Created PUBLIC release artifacts: ' + str(target))
    print('Run scripts/check.py before publishing; SHA256SUMS verifies integrity, not authorship.')


if __name__ == '__main__':
    main()
