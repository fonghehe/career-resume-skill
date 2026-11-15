#!/usr/bin/env python3
"""Export a public starter bundle by default, or an explicit personal backup."""

from career_resume import ROOT
import argparse
import json
import os
import posixpath
import re
from pathlib import Path
import shutil
import tempfile
import zipfile
from urllib.parse import urlsplit

from career_resume.bundle import is_source_tree, personal_entries, public_entries, runtime_entries, select_version, validate_version
from career_resume.validate import validate
from career_resume.cli_support import fail
from career_resume.file_io import new_file

MAX_RUNTIME_FILES = 200
MAX_RUNTIME_BYTES = 10 * 1024 * 1024
RUNTIME_EXTENSIONS = frozenset({'.md', '.txt', '.py', '.json', '.yaml', '.yml'})


def check_runtime_budget(file_count, uncompressed_bytes):
    if file_count > MAX_RUNTIME_FILES:
        raise ValueError(f'Runtime bundles must contain at most {MAX_RUNTIME_FILES} files; '
                         f'found {file_count}. Keep source-only examples and maintenance files out of the runtime inventory.')
    if uncompressed_bytes > MAX_RUNTIME_BYTES:
        raise ValueError('Runtime bundles must not exceed 10 MiB of uncompressed files; '
                         f'found {uncompressed_bytes} bytes.')


def archive_statistics(path, *, runtime=True):
    """Measure the finished ZIP, excluding directory entries from the file count."""
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        files = [entry for entry in archive.infolist() if not entry.is_dir()]
        total = sum(entry.file_size for entry in files)
        if runtime:
            check_runtime_budget(len(files), total)
            for entry in files:
                if Path(entry.filename).suffix.lower() not in RUNTIME_EXTENSIONS:
                    raise ValueError('Unsupported runtime file type: ' + entry.filename)
        return {'fileCount': len(files), 'uncompressedBytes': total,
                'zipBytes': path.stat().st_size}


def link_runtime_guides(staging, entries):
    """Link optional tutorials to the website instead of duplicating them in the Skill."""
    for relative in entries:
        if not relative.endswith('.md'):
            continue
        path = staging / relative
        def replace(match):
            target = match[1]
            file, separator, anchor = target.partition('#')
            if not file or urlsplit(file).scheme or file.startswith('/'):
                return match[0]
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(relative), file))
            if not resolved.startswith('docs/') or not resolved.endswith('.md') or resolved in entries:
                return match[0]
            url = 'https://fonghehe.github.io/career-resume-skill/' + resolved[5:-3] + '.html'
            return '](' + url + (separator + anchor if separator else '') + ')'
        path.write_text(re.sub(r'\]\(([^)\s]+)\)', replace, path.read_text(encoding='utf-8')), encoding='utf-8')


def write_tree(entries, target):
    for relative, source in sorted(entries.items()):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, path)


def export(root, output, *, include_personal=False, directory=False, overwrite=False, runtime=None,
           skillhub_version=None):
    if skillhub_version is not None:
        validate_version(skillhub_version)
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
    if skillhub_version is not None:
        if include_personal or runtime is False:
            raise ValueError('SkillHub export requires a public runtime bundle.')
        runtime = True
    if runtime is None:
        runtime = not directory or not is_source_tree(root)
    entries = (personal_entries(root) if include_personal else
               runtime_entries(root) if runtime else public_entries(root))
    if runtime and not include_personal:
        # SkillHub's web uploader accepts at most 200 files / 10 MiB and skips
        # binary attachments. Ship the text-only subset needed by this Skill.
        for relative in entries:
            if Path(relative).suffix.lower() not in RUNTIME_EXTENSIONS:
                raise ValueError('Unsupported runtime file type: ' + relative)
        check_runtime_budget(len(entries), sum(path.stat().st_size for path in entries.values()))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.career-resume-skill-', dir=output.parent) as temp:
        staging = Path(temp) / 'career-resume-skill'
        staging.mkdir()
        write_tree(entries, staging)
        if runtime and not include_personal:
            link_runtime_guides(staging, entries)
            if skillhub_version is not None:
                entry = staging / 'SKILL.md'
                _, front, body = entry.read_text(encoding='utf-8').split('---', 2)
                metadata = {'slug': 'career-resume-skill', 'displayName': 'career-resume-skill',
                            'version': skillhub_version, 'license': 'MIT'}
                lines = [line for line in front.strip('\n').splitlines()
                         if line.partition(':')[0] not in metadata]
                lines.extend(f'{key}: {value}' for key, value in metadata.items())
                entry.write_text('---\n' + '\n'.join(lines) + '\n---' + body, encoding='utf-8')
            demo = staging / 'examples/career-demo/data/timeline.json'
            data = json.loads(demo.read_text(encoding='utf-8'))
            for project in data['projects']:
                for attachment in project.get('attachments', []):
                    if attachment['path'] == 'references/attachments/demo-phases.png':
                        attachment['path'] = 'references/attachments/demo-phases.md'
                        attachment['label'] = '工具集阶段概览（文字版，虚构）'
            demo.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            check_runtime_budget(len(entries), sum((staging / relative).stat().st_size for relative in entries))
        errors, _ = validate(staging)
        if errors:
            raise ValueError('Export validation failed:\n' + '\n'.join(errors))
        if directory:
            # Exclusive mkdir prevents accidentally merging into an existing tree.
            output.mkdir()
            try:
                write_tree({relative: staging / relative for relative in entries}, output)
            except Exception:
                shutil.rmtree(output)
                raise
        else:
            archive_path = Path(temp) / 'bundle.zip'
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
                for relative in sorted(entries):
                    archive.write(staging / relative, 'career-resume-skill/' + relative)
            # Check the actual upload artifact after all metadata/fixture rewrites.
            if runtime and not include_personal:
                archive_statistics(archive_path)
            if overwrite:
                os.replace(archive_path, output)
            else:
                with new_file(output) as target, archive_path.open('rb') as source:
                    shutil.copyfileobj(source, target)
    return len(entries)


def main(argv=None, *, root=ROOT):
    parser = argparse.ArgumentParser(prog='career.py package', description=__doc__)
    parser.add_argument('--output', type=Path, help='ZIP output path')
    parser.add_argument('--overwrite', action='store_true', help='Replace a ZIP deliberately')
    parser.add_argument('--version', help='Explicit X.Y.Z for a public ZIP; otherwise ask every time')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--include-personal', action='store_true', help='Sensitive personal backup')
    mode.add_argument('--public-dir', type=Path, help='Export clean public tree to a new directory')
    parser.add_argument('--runtime', action='store_true',
                        help='Export only installable Skill resources (ZIP always uses this layout)')
    args = parser.parse_args(argv)
    if args.public_dir and args.output:
        parser.error('--output is for ZIP mode; use --public-dir alone')
    if args.runtime and args.include_personal:
        parser.error('--runtime cannot be combined with --include-personal')
    if args.version is not None and (args.public_dir or args.include_personal):
        parser.error('--version applies only to public ZIPs; source exports and private backups have no release version')
    root = Path(root).resolve()
    try:
        version = select_version(root, args.version) if not (args.public_dir or args.include_personal) else None
        filename = 'career-resume-skill-personal.zip' if args.include_personal else f'career-resume-skill-{version}.zip'
        output = args.public_dir or args.output or root / 'local/dist' / filename
        count = export(root, output, include_personal=args.include_personal,
                       directory=bool(args.public_dir), overwrite=args.overwrite,
                       runtime=True if args.runtime else None, skillhub_version=version)
    except (ValueError, OSError) as exc:
        return fail(exc)
    kind = 'PERSONAL backup (contains candidate data)' if args.include_personal else 'PUBLIC starter'
    print(f'Created {kind}: {output.resolve()} ({count} files)')
    if not args.public_dir and not args.include_personal:
        stats = archive_statistics(output)
        print(f'Upload budget: {stats["fileCount"]}/{MAX_RUNTIME_FILES} files; '
              f'{MAX_RUNTIME_FILES - stats["fileCount"]} remaining; '
              f'{stats["uncompressedBytes"]}/{MAX_RUNTIME_BYTES} uncompressed bytes.')
