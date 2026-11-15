#!/usr/bin/env python3
"""Build a versioned public ZIP and SHA256SUMS locally; never publish or include personal data."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from career_resume.bundle import read_version, select_version, validate_version
from career_resume.package import (MAX_RUNTIME_BYTES, MAX_RUNTIME_FILES, archive_statistics, export)
from career_resume.cli_support import fail


def build_release(root, output=None, *, version=None, skillhub=False):
    root = Path(root).resolve()
    current = read_version(root)
    version = validate_version(version) if version is not None else current
    if version is None:
        raise ValueError('No local VERSION record; choose a complete version for this package.')
    folder = 'skillhub' if skillhub else 'releases'
    raw = Path(output).absolute() if output is not None else root / 'local/dist' / folder / version
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
        export(root, archive, skillhub_version=version if skillhub else None)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (staging / 'SHA256SUMS').write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
        stats = archive_statistics(archive)
        report = {'archive': archive.name, 'version': version,
                  'distribution': 'skillhub' if skillhub else 'runtime',
                  **stats, 'maxFiles': MAX_RUNTIME_FILES,
                  'remainingFiles': MAX_RUNTIME_FILES - stats['fileCount'],
                  'maxUncompressedBytes': MAX_RUNTIME_BYTES, 'sha256': digest}
        # The report stays next to the ZIP, so it does not consume upload slots.
        (staging / 'PACKAGE-INFO.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        target.mkdir()
        try:
            for path in staging.iterdir():
                shutil.copyfile(path, target / path.name)
            if version != current:
                # Update VERSION last, atomically, on its own filesystem. Failed
                # packaging must leave both the source version and old releases intact.
                update_path = None
                try:
                    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=root,
                                                     prefix='.career-version-', delete=False) as update:
                        update_path = Path(update.name)
                        update.write(version + '\n')
                    if (root / 'VERSION').exists():
                        shutil.copymode(root / 'VERSION', update_path)
                    update_path.replace(root / 'VERSION')
                finally:
                    if update_path is not None:
                        update_path.unlink(missing_ok=True)
        except Exception:
            shutil.rmtree(target)
            raise
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, help='New output directory (default local/dist/<distribution>/<version>)')
    parser.add_argument('--version', help='Explicit X.Y.Z for automation; otherwise ask every time')
    parser.add_argument('--skillhub', action='store_true',
                        help='Add required SkillHub metadata to the packaged entry only')
    args = parser.parse_args(argv)
    try:
        root = Path(__file__).resolve().parents[1]
        version = select_version(root, args.version)
        target = build_release(root, args.output_dir, version=version, skillhub=args.skillhub)
    except (ValueError, OSError) as exc:
        return fail(exc)
    print('Created PUBLIC release artifacts: ' + str(target))
    report = json.loads((target / 'PACKAGE-INFO.json').read_text(encoding='utf-8'))
    print(f'Upload budget: {report["fileCount"]}/{report["maxFiles"]} files; '
          f'{report["remainingFiles"]} remaining; '
          f'{report["uncompressedBytes"]}/{report["maxUncompressedBytes"]} uncompressed bytes.')
    print('Upload the ZIP only; PACKAGE-INFO.json and SHA256SUMS stay outside the Skill.')
    print('VERSION: ' + read_version(root) + '; review it before creating the matching tag.')
    print('Run tools/check.py before publishing; SHA256SUMS verifies integrity, not authorship.')


if __name__ == '__main__':
    raise SystemExit(main())
