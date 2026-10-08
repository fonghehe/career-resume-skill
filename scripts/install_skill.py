#!/usr/bin/env python3
"""Install a public Skill into any host directory or export an import ZIP."""

import argparse
from pathlib import Path
import tempfile

from bundle import public_entries
from package import export

NAME = 'career-resume-skill'
PROJECT_FOLDERS = {'codex': '.agents/skills', 'claude': '.claude/skills',
                   'claude-code': '.claude/skills', 'trae': '.trae/skills',
                   'universal': '.agents/skills'}
USER_FOLDERS = {'codex': '.agents/skills', 'claude': '.claude/skills'}
USER_FOLDERS['claude-code'] = USER_FOLDERS['claude']


def destination(agent=None, *, project=None, skills_dir=None, output=None, root=None):
    if output is not None or agent == 'workbuddy':
        if agent in PROJECT_FOLDERS:
            raise ValueError('--output selects generic ZIP mode; omit the directory agent preset.')
        if project is not None or skills_dir is not None:
            raise ValueError('ZIP mode cannot use --project/--skills-dir.')
        target = Path(output) if output is not None else Path(root) / 'local/dist' / (NAME + '-workbuddy.zip')
        if target.suffix.lower() != '.zip':
            raise ValueError('Import output must have a .zip extension.')
        return target.expanduser().absolute(), False
    if project is not None and skills_dir is not None:
        raise ValueError('Choose --project or --skills-dir, not both.')
    if skills_dir is not None:
        base = Path(skills_dir).expanduser().absolute()
    elif project is not None:
        agent = agent or 'universal'
        if agent not in PROJECT_FOLDERS:
            raise ValueError('Unknown project discovery path; use --skills-dir with your host directory.')
        project = Path(project).expanduser().absolute()
        if not project.is_dir():
            raise ValueError('--project must point to an existing workspace directory.')
        base = project / PROJECT_FOLDERS[agent]
    elif agent in USER_FOLDERS:
        base = Path.home() / USER_FOLDERS[agent]
    else:
        raise ValueError('Use --skills-dir for any host, --output for ZIP, or --project with a known preset. '
                         'Shared/global paths are host-specific; no default is assumed.')
    return base / NAME, True


def install(root, agent=None, *, project=None, skills_dir=None, output=None, dry_run=False):
    root = Path(root).resolve()
    target, directory = destination(agent, project=project, skills_dir=skills_dir,
                                    output=output, root=root)
    # Check the lexical path before resolving it, including missing destinations.
    for path in (target, *target.parents):
        if path.is_symlink():
            raise ValueError('Refusing a symlink in the installation destination.')
    if target == root or target in root.parents:
        raise ValueError('Installation must not replace the source or its parent.')
    if target.exists():
        raise ValueError(f'Destination already exists; existing files were preserved: {target}')
    # Never read local profiles, outputs, node_modules or Git history.
    count = len(public_entries(root))
    if not dry_run:
        # A clean staging copy also allows a project-local install inside the source
        # workspace without relaxing the public export command's output boundary.
        with tempfile.TemporaryDirectory(prefix=NAME + '-install-') as temp:
            staging = Path(temp) / NAME
            export(root, staging, directory=True)
            export(staging, target, directory=directory)
    return target, count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', help='Optional preset: codex, claude/claude-code, trae, universal, workbuddy; '
                        'other host names work with --skills-dir or --output')
    parser.add_argument('--project', type=Path, help='Existing workspace; defaults to project .agents/skills')
    parser.add_argument('--skills-dir', type=Path, help='Explicit host skills directory (Skill name is appended)')
    parser.add_argument('--output', type=Path, help='Public import ZIP for any compatible host')
    parser.add_argument('--list-agents', action='store_true', help='Show built-in shortcuts, not a compatibility limit')
    parser.add_argument('--dry-run', action='store_true', help='Show the destination without writing files')
    args = parser.parse_args()
    if args.list_agents:
        print('Built-in shortcuts: ' + ', '.join((*PROJECT_FOLDERS, 'workbuddy')))
        print('Any other file-based host: --skills-dir <host-directory>; ZIP import: --output <new.zip>.')
        print('For ecosystem multi-agent installation, export a public tree and use the skills CLI.')
        return
    try:
        target, count = install(Path(__file__).resolve().parents[1], args.agent,
                                project=args.project, skills_dir=args.skills_dir,
                                output=args.output, dry_run=args.dry_run)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f'{"Planned" if args.dry_run else "Created"}: {target} ({count} public files).')
    if args.agent == 'workbuddy':
        print('Import this ZIP from WorkBuddy Skills > Add Skill > Upload Skill.')
    elif args.output is not None:
        print('Import the public ZIP using your host UI; check its required archive layout and metadata.')
    else:
        print('Open the client and select career-resume-skill; refresh/restart if it is not listed.')
    print('Specify your private workspace in the prompt; run its scripts for all career data.')


if __name__ == '__main__':
    main()
