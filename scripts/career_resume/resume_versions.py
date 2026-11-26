#!/usr/bin/env python3
"""Compare saved resume versions or find claims that cite corrected facts."""

from career_resume import ROOT
import argparse
from difflib import unified_diff
from pathlib import Path
import re

from career_resume.career_data import checked_local, profile_root
from career_resume.cli_support import fail

FACT_ID = re.compile(r'[A-Z]+[0-9]+(?:-[A-Z0-9]+)*')
ID_IN_CELL = re.compile(r'(?<![A-Za-z0-9_-])' + FACT_ID.pattern + r'(?![A-Za-z0-9_-])')


def evidence(report):
    """Read the existing report template's claim and ID columns only."""
    rows = []
    in_section = False
    incomplete = False
    for raw in report.splitlines():
        line = raw.strip()
        if re.match(r'^#{1,2}\s', line):
            if in_section:
                break
            in_section = line == '## 正文依据'
        if not in_section or not line.startswith('|'):
            continue
        cells = re.split(r'(?<!\\)\|', line.strip('|'))
        if len(cells) < 2:
            incomplete = True
            continue
        claim, ids = (cell.strip() for cell in cells[:2])
        if claim.startswith(('简历位置', '正文位置')) or re.fullmatch(r'[-: ]+', claim):
            continue
        facts = set(ID_IN_CELL.findall(ids))
        # Older reports abbreviate P01-A / B / C. Keep known IDs, but require
        # review because the omitted prefixes cannot be matched exactly.
        if re.search(r'/\s*[A-Z][A-Z0-9]*(?![A-Za-z0-9_-])', ids):
            incomplete = True
        if facts and claim:
            rows.append((claim, facts))
        else:
            incomplete = True
    return rows, incomplete or not rows


def impact(profile, facts):
    if any(not FACT_ID.fullmatch(fact) for fact in facts):
        raise ValueError('Pass exact fact IDs such as E01-T or P01-A.')
    folder = profile / 'output/resumes'
    if not folder.exists() and not folder.is_symlink():
        return ['No saved resume versions found.']
    if folder.is_symlink() or folder.parent.is_symlink() or not folder.is_dir():
        raise ValueError('Expected a regular output/resumes directory.')
    lines = []
    for version in sorted(folder.iterdir()):
        if version.is_symlink():
            raise ValueError('Refusing a symlink resume version.')
        if not version.is_dir():
            continue
        path = version / 'match-report.md'
        if path.exists() or path.is_symlink():
            report = checked_local(profile, path.relative_to(profile).as_posix())
            rows, incomplete = evidence(report.read_text(encoding='utf-8'))
            for claim, ids in rows:
                if ids & facts:
                    lines.append(f'{version.name}: {", ".join(sorted(ids & facts))} | {claim}')
        else:
            incomplete = True
        if incomplete:
            lines.append(f'{version.name}: manual review needed (missing or incomplete claim mapping).')
    return lines or ['No saved claim mappings reference those exact IDs.']


def compare(before, after, language):
    versions = (Path(before), Path(after))
    if any(item.is_symlink() for path in versions for item in (path, *path.parents)):
        raise ValueError('Refusing a symlink resume version.')
    contents = [checked_local(path, f'resume.{language}.md').read_text(encoding='utf-8').splitlines()
                for path in versions]
    result = list(unified_diff(*contents, fromfile=str(before), tofile=str(after), lineterm=''))
    if not result:
        result = ['No changes in the selected resume text.']
    mappings = []
    for path in versions:
        report = path / 'match-report.md'
        if report.exists() or report.is_symlink():
            rows, incomplete = evidence(checked_local(path, report.name).read_text(encoding='utf-8'))
        else:
            rows, incomplete = [], True
        if incomplete:
            result.append(f'{path}: claim mapping missing or incomplete.')
        mappings.append(set().union(*(ids for _, ids in rows)))
    for label, ids in (('Added citations', mappings[1] - mappings[0]),
                       ('Removed citations', mappings[0] - mappings[1])):
        result.append(f'{label} (from available mappings): {", ".join(sorted(ids)) or "—"}')
    return result


def main(argv=None, *, root=ROOT):
    parser = argparse.ArgumentParser(prog='career.py versions', description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    diff = modes.add_parser('compare', help='Compare two version directories')
    diff.add_argument('before', type=Path)
    diff.add_argument('after', type=Path)
    diff.add_argument('--language', choices=('zh-CN', 'en'), default='zh-CN')
    check = modes.add_parser('impact', help='Find saved claims that cite corrected facts')
    check.add_argument('--fact', nargs='+', required=True, metavar='ID')
    args = parser.parse_args(argv)
    try:
        if args.mode == 'compare':
            lines = compare(Path(root) / args.before, Path(root) / args.after, args.language)
        else:
            lines = impact(profile_root(root), set(args.fact))
    except (ValueError, OSError) as exc:
        return fail(exc)
    print('\n'.join(lines))
