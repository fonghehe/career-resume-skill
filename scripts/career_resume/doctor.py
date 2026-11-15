#!/usr/bin/env python3
"""Report local prerequisites without installing software or changing career data."""

from career_resume import ROOT
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from career_resume.bundle import STARTER_FILES, checked_file, is_source_tree, repository_entries, read_version, runtime_entries
from career_resume.career_data import profile_root
from career_resume.cli_support import fail


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
        source_tree = is_source_tree(root)
        entries = repository_entries(root) if source_tree else runtime_entries(root)
        label = 'source (' + (read_version(root) or 'no local release yet') + ')' if source_tree else 'runtime Skill'
        rows.append(('OK', f'career-resume-skill {label}; complete public resources: {len(entries)} files'))
    except (ValueError, OSError) as exc:
        rows.append(('ERROR', str(exc) + '; obtain the complete project directory'))
    git = probe('git')
    rows.append(('OK' if git else 'INFO', git or 'Git unavailable; only Git collection/checks require it'))
    from career_resume.export_resume import converter_path
    try:
        rows.append(('OK', 'Optional PDF converter: ' + converter_path()))
    except ValueError:
        rows.append(('INFO', 'LibreOffice unavailable; DOCX export works, PDF requires a local converter or Word'))
    try:
        profile = profile_root(root)
    except ValueError as exc:
        rows.append(('ERROR', str(exc)))
        return rows
    missing = [rel for rel in STARTER_FILES if rel != '.gitignore'
               and not (profile / rel.removeprefix('local/')).is_file()]
    rows.append(('INFO' if missing else 'OK',
                 'Local profile not initialized; run scripts/career.py init in your private workspace'
                 if missing else 'Local profile files present (contents not read)'))
    if not (root / '.gitignore').is_file():
        rows.append(('INFO', 'Workspace ignore rules missing; run scripts/career.py init before saving personal data'))
    if docs:
        if not source_tree:
            rows.append(('ERROR', 'Documentation builds require the full source project; runtime packages use offline Markdown guides'))
            return rows
        try:
            manifest = json.loads(checked_file(root, 'package.json').read_text(encoding='utf-8'))
            node_major = manifest['engines']['node'].removesuffix('.x')
            pnpm_version = manifest['packageManager'].removeprefix('pnpm@')
        except (ValueError, OSError, KeyError, TypeError) as exc:
            rows.append(('ERROR', 'Invalid documentation toolchain configuration: ' + str(exc)))
            return rows
        for label, value, required in (('Node.js', probe('node'), node_major + '.x'),
                                       ('pnpm', probe('pnpm'), pnpm_version)):
            actual = (value or '').lstrip('v')
            valid = actual.split('.')[0] == node_major if label == 'Node.js' else actual == required
            rows.append(('OK' if valid else 'ERROR',
                         f'{label}: {value or "unavailable"}; requires {required} (package.json)'))
    return rows


def smoke(root):
    """Run core tools on a fresh public runtime copy, never existing user records."""
    from career_resume.package import export
    commands = ('init', 'validate', 'build', 'web', 'demo', 'validate')
    with tempfile.TemporaryDirectory(prefix='career-runtime-self-check-') as temporary:
        runtime = Path(temporary).resolve() / 'career-resume-skill'
        export(root, runtime, directory=True, runtime=True)
        for command in commands:
            result = subprocess.run([sys.executable, '-B', str(runtime / 'scripts/career.py'), command],
                                    cwd=runtime, capture_output=True, text=True)
            if result.returncode:
                raise ValueError(f'Runtime self-check failed: {command}\n' + result.stdout + result.stderr)
    return commands


def main(argv=None):
    parser = argparse.ArgumentParser(prog='career.py doctor', description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=ROOT)
    parser.add_argument('--docs', action='store_true', help='Also check optional documentation runtimes')
    parser.add_argument('--smoke', action='store_true',
                        help='Run core tools in a temporary blank runtime copy; leave existing personal data untouched')
    args = parser.parse_args(argv)
    rows = diagnose(args.root, docs=args.docs)
    for status, message in rows:
        if status != 'ERROR':
            print(f'{status}: {message}')
    errors = [message for status, message in rows if status == 'ERROR']
    if errors:
        return fail(errors)
    if args.smoke:
        try:
            scripts = smoke(args.root)
        except (ValueError, OSError) as exc:
            return fail(exc)
        print('OK: Runtime self-check passed: ' + ' -> '.join(scripts))
    scope = 'local prerequisites and blank runtime self-check' if args.smoke else 'local prerequisites only'
    print(f'Scope: {scope}; attachment access and model behavior require a host test.')
    return 0
