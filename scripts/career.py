#!/usr/bin/env python3
"""One entry point for the career workspace; writing and fact review stay with the agent."""

import argparse
from importlib import import_module
from pathlib import Path

from career_resume.cli_support import fail

ROOT = Path(__file__).resolve().parents[1]
FORWARDED = {
    'install': 'install_skill', 'package': 'package', 'git': 'import_git_activity',
    'update': 'update_profile', 'share': 'export_share', 'versions': 'resume_versions',
}


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--workspace', type=Path, default=ROOT,
                     help='Existing complete workspace; relative resume export paths use this directory')
    commands = cli.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='Fill missing blank records, preserving existing files')
    init.add_argument('--new', type=Path, help='Create a clean complete Skill in a NEW directory')
    build = commands.add_parser('build', help='Rebuild the written career from source records')
    build.add_argument('--web', action='store_true', help='Also rebuild the offline personal page')
    build.add_argument('--output', type=Path, help='Written career output path')
    web = commands.add_parser('web', help='Build the offline page from maintained display data')
    web.add_argument('--output', type=Path, help='Destination HTML file')
    commands.add_parser('validate', help='Check structure, links and source references')
    from career_resume.export_resume import add_arguments
    add_arguments(commands.add_parser('export', help='Export a resume to DOCX, PDF or both'))
    workbench = commands.add_parser('workbench', help='Open the local browser editor')
    workbench.add_argument('--demo', action='store_true', help='Use isolated fictional records')
    workbench.add_argument('--port', type=int, default=0)
    workbench.add_argument('--no-browser', action='store_true')
    doctor = commands.add_parser('doctor', help='Check public resources and optional tools')
    doctor.add_argument('--smoke', action='store_true', help='Test a temporary blank runtime copy')
    doctor.add_argument('--docs', action='store_true', help='Also check documentation dependencies')
    demo = commands.add_parser('demo', help='Create isolated fictional bilingual examples')
    demo.add_argument('--output', type=Path, help='New example output directory')
    demo.add_argument('--docs', action='store_true', help='Rebuild fictional documentation examples (source only)')
    for name, module in FORWARDED.items():
        commands.add_parser(name, add_help=False,
                            help=import_module('career_resume.' + module).__doc__.splitlines()[0])
    return cli


def main(argv=None):
    cli = parser()
    args, extra = cli.parse_known_args(argv)
    if args.command not in FORWARDED and extra:
        cli.error('unrecognized arguments: ' + ' '.join(extra))
    workspace = args.workspace.absolute()
    try:
        if args.command in FORWARDED:
            return import_module('career_resume.' + FORWARDED[args.command]).main(extra, root=workspace)
        if args.command == 'init':
            from career_resume.init_profile import initialize
            if args.new:
                from career_resume.package import export
                target = args.new.absolute()
                export(workspace, target, directory=True, runtime=True)
            else:
                target = workspace
            created, preserved = initialize(target)
            print(f'Workspace: {target}\nCreated {created} files; preserved {preserved} existing files.')
            print('Next: provide your experience to the agent using this workspace/SKILL.md.')
        elif args.command == 'build':
            from career_resume.build_career import build
            output = workspace / args.output if args.output else None
            print('Written career: ' + str(build(workspace, output)))
            if args.web:
                from career_resume.build_timeline import build as build_web
                print('Offline personal page: ' + str(build_web(workspace)))
            print('Rebuilt existing records only. Display data must be synchronized from sources first.')
        elif args.command == 'web':
            from career_resume.build_timeline import build
            output = workspace / args.output if args.output else None
            print('Offline personal page: ' + str(build(workspace, output)))
        elif args.command == 'validate':
            from career_resume.validate import validate
            errors, count = validate(workspace)
            if errors:
                return fail(errors)
            print(f'OK: {count} Markdown files; structure and sources checked. Facts require review.')
        elif args.command == 'export':
            from career_resume.export_resume import run
            return run(args, base=workspace)
        elif args.command == 'workbench':
            from career_resume.serve_workbench import main as serve
            forwarded = ['--workspace', str(workspace), '--port', str(args.port)]
            if args.demo:
                forwarded.append('--demo')
            if args.no_browser:
                forwarded.append('--no-browser')
            return serve(forwarded)
        elif args.command == 'doctor':
            from career_resume.doctor import main as diagnose
            return diagnose([str(workspace)] + (['--smoke'] if args.smoke else [])
                            + (['--docs'] if args.docs else []))
        elif args.command == 'demo':
            from career_resume.create_demo import create
            output = workspace / args.output if args.output else None
            print('Fictional example: ' + str(create(workspace, output, docs=args.docs)))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return fail(exc)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
