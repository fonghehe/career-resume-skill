#!/usr/bin/env python3
"""Explicit public file inventory; never discover candidate data automatically."""

from pathlib import Path
import re

PUBLIC_FILES = (
    '.github/CODE_OF_CONDUCT.md',
    '.github/CONTRIBUTING.md',
    '.github/ISSUE_TEMPLATE/bug_report.md',
    '.github/ISSUE_TEMPLATE/config.yml',
    '.github/ISSUE_TEMPLATE/feature_request.md',
    '.github/PULL_REQUEST_TEMPLATE.md',
    '.github/SECURITY.md',
    '.github/workflows/ci.yml',
    '.github/workflows/release.yml',
    'LICENSE',
    'README.en.md',
    'README.md',
    'SKILL.md',
    'VERSION',
    'agents/openai.yaml',
    'assets/templates/career-kb-template.md',
    'assets/templates/project-template.md',
    'assets/templates/resume-template.md',
    'assets/templates/match-report-template.md',
    'assets/templates/interview-template.md',
    'assets/templates/agent-entry-template.md',
    'docs/.vitepress/config.mts',
    'docs/example.md',
    'docs/guide/first-library.md',
    'docs/guide/review-career.md',
    'docs/guide/generate-webpage.md',
    'docs/guide/git-timeline.md',
    'docs/guide/import-resume.md',
    'docs/guide/privacy.md',
    'docs/guide/project-cases.md',
    'docs/guide/quick-start.md',
    'docs/guide/troubleshooting.md',
    'docs/guide/using-skill.md',
    'docs/guide/generate-resume.md',
    'docs/guide/update-career.md',
    'docs/guide/prepare-interview.md',
    'docs/index.md',
    'docs/maintainers/behavior-testing.md',
    'docs/maintainers/documentation.md',
    'docs/maintainers/releasing.md',
    'docs/reference/commands.md',
    'docs/reference/compatibility.md',
    'docs/reference/data-model.md',
    'docs/reference/directories.md',
    'docs/reference/capabilities.md',
    'assets/examples/career-demo/data/timeline.json',
    'assets/examples/career-demo/references/attachments/demo-phases.png',
    'assets/examples/career-demo/references/attachments/demo-release.md',
    'assets/examples/career-demo/references/projects/sample-console.md',
    'assets/examples/career-demo/references/projects/sample-notebook.md',
    'assets/examples/career-demo/references/projects/sample-portal.md',
    'assets/examples/career-demo/references/sources/demo-resume.md',
    'assets/examples/resume-demo/match-report.md',
    'assets/examples/resume-demo/career.md',
    'assets/examples/resume-demo/request.md',
    'assets/examples/resume-demo/resume.zh-CN.md',
    'package.json',
    'pnpm-lock.yaml',
    'pnpm-workspace.yaml',
    'references/career-workflow.md',
    'references/enhancements.md',
    'references/resume-workflow.md',
    'scripts/build_career.py',
    'scripts/build_timeline.py',
    'scripts/bundle.py',
    'scripts/career_data.py',
    'scripts/check.py',
    'scripts/check_public_index.py',
    'scripts/create_demo.py',
    'scripts/doctor.py',
    'scripts/export_share.py',
    'scripts/import_git_activity.py',
    'scripts/init_profile.py',
    'scripts/install_skill.py',
    'scripts/package.py',
    'scripts/release.py',
    'scripts/update_profile.py',
    'scripts/validate.py',
    'tests/scenarios.md',
    'tests/test_demo.py',
    'tests/test_enhancements.py',
    'tests/test_git_activity.py',
    'tests/test_local_profile.py',
    'tests/test_onboarding.py',
    'tests/test_agent_install.py',
    'tests/test_release.py',
    'tests/test_story_timeline.py',
    'tests/test_written_career.py',
)

STARTER_FILES = (
    '.gitignore',
    'local/README.md',
    'local/references/profile.md', 'local/references/facts.md', 'local/references/project-index.md',
    'local/references/career/README.md',
    'local/references/sources.md', 'local/references/sources/manifest.json',
    'local/references/role-matching.md', 'local/references/resume-modes.md',
    'local/references/backend-capabilities.md', 'local/references/output.md',
    'local/references/questions-to-confirm.md', 'local/references/technical-challenges-to-verify.md',
    'local/references/excluded/fabricated-projects.md', 'local/data/timeline.json',
)


def read_version(root):
    value = checked_file(root, 'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value):
        raise ValueError('VERSION must contain a release version such as 0.1.0 (no v prefix).')
    return value


def checked_file(root, relative):
    """Reject symlinks at every level instead of following them into a release."""
    root = Path(root).resolve()
    path = root / relative
    if not path.is_relative_to(root):
        raise ValueError(f'Path outside bundle: {relative}')
    for candidate in (path, *path.parents):
        if candidate == root:
            break
        if candidate.is_symlink():
            raise ValueError(f'Symlink is not a release input: {relative}')
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError(f'Missing or invalid release file: {relative}')
    return path


def public_entries(root):
    entries = {rel: checked_file(root, rel) for rel in PUBLIC_FILES}
    for rel in STARTER_FILES:
        source = starter_source(rel)
        path = checked_file(root, source)
        entries[rel] = path
        entries[source] = path
    return entries


def repository_entries(root):
    """Files to commit; user data is initialized from tracked starter templates."""
    paths = (*PUBLIC_FILES, '.gitignore',
             *(starter_source(rel) for rel in STARTER_FILES))
    return {rel: checked_file(root, rel) for rel in paths}


def starter_source(relative):
    # A literal .gitignore inside starter/ would hide the templates themselves.
    return 'assets/starter/gitignore.template' if relative == '.gitignore' else 'assets/starter/' + relative.removeprefix('local/')


def personal_entries(root):
    from career_data import profile_root
    entries = public_entries(root)
    profile = profile_root(root)
    for folder in ('references', 'data', 'showcase'):
        base = profile / folder
        if base.is_symlink():
            raise ValueError(f'Symlink is not a backup input: {folder}')
        for path in base.rglob('*'):
            if path.is_symlink():
                raise ValueError(f'Symlink is not a backup input: {path}')
            if path.is_file() and path.suffix in {'.md', '.json', '.html'}:
                rel = path.relative_to(profile).as_posix()
                # Normalize old datasets into the new private directory in backups.
                entries['local/' + rel] = checked_file(profile, rel)
    for rel in ('docs/private-usage.md', 'scripts/validate_personal.py'):
        if (Path(root) / rel).is_file():
            entries[rel] = checked_file(root, rel)
    return entries
