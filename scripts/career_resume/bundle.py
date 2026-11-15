#!/usr/bin/env python3
"""Explicit public file inventory; never discover candidate data automatically."""

from pathlib import Path
import re

# Five fictional professions share one explicit file layout. These are fixed inventory
# entries, never a directory scan of example data or the private local/ workspace.
PROFESSION_SLUGS = ('teacher', 'designer', 'sales', 'finance', 'engineer')
PROFESSION_FILES = (
    'source/data/timeline.json',
    'source/references/career/README.md',
    'source/references/facts.md',
    'source/references/profile.md',
    'source/references/project-index.md',
    'source/references/questions-to-confirm.md',
    'source/references/sources.md',
    'source/references/projects/P01.md',
    'source/references/projects/P02.md',
    'source/references/projects/P03.md',
    'source/references/sources/manifest.json',
    'source/references/sources/SYN01.md',
    'resume.zh-CN.md',
    'resume.en.md',
    'match-report.md',
)
PROFESSION_EXTRA_FILES = {
    'engineer': (
        'source/demo-code/git-log.txt',
        'source/demo-code/order-workbench/README.md',
        'source/demo-code/order-workbench/order-state.js',
        'source/demo-code/order-workbench/recovery.md',
    ),
}


def profession_public_files():
    """Deterministic expansion of the controlled multi-profession example inventory."""
    return (
        *(f'examples/professions/{slug}/{rel}' for slug in PROFESSION_SLUGS
          for rel in (*PROFESSION_FILES, *PROFESSION_EXTRA_FILES.get(slug, ()))),
        'examples/professions/examples.json',
        'examples/professions/README.md',
    )


PUBLIC_FILES = (
    '.github/CODE_OF_CONDUCT.md',
    '.github/CONTRIBUTING.md',
    '.github/ISSUE_TEMPLATE/bug_report.md',
    '.github/ISSUE_TEMPLATE/config.yml',
    '.github/ISSUE_TEMPLATE/feature_request.md',
    '.github/PULL_REQUEST_TEMPLATE.md',
    '.github/SECURITY.md',
    '.github/workflows/ci.yml',
    '.github/workflows/pages.yml',
    '.github/workflows/release.yml',
    'LICENSE',
    'AGENTS.md',
    'README.en.md',
    'README.md',
    'SKILL.md',
    'agents/openai.yaml',
    'assets/templates/career-kb-template.md',
    'assets/templates/project-template.md',
    'assets/templates/resume-template.md',
    'assets/templates/resume-en-template.md',
    'assets/templates/match-report-template.md',
    'assets/templates/interview-template.md',
    'assets/templates/agent-entry-template.md',
    'assets/templates/release-readme.md',
    'assets/themes/palette.json',
    'docs/.vitepress/config.mts',
    'docs/example.md',
    'docs/examples.md',
    'docs/guide/first-library.md',
    'docs/guide/review-career.md',
    'docs/guide/generate-webpage.md',
    'docs/guide/workbench.md',
    'docs/guide/git-timeline.md',
    'docs/guide/import-resume.md',
    'docs/guide/privacy.md',
    'docs/guide/project-cases.md',
    'docs/guide/quick-start.md',
    'docs/guide/troubleshooting.md',
    'docs/guide/using-skill.md',
    'docs/guide/upgrade-skill.md',
    'docs/guide/generate-resume.md',
    'docs/guide/english-resume.md',
    'docs/guide/export-resume.md',
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
    'examples/career-demo/data/timeline.json',
    'examples/career-demo/references/attachments/demo-phases.png',
    'examples/career-demo/references/attachments/demo-phases.md',
    'examples/career-demo/references/attachments/demo-release.md',
    'examples/career-demo/references/projects/sample-console.md',
    'examples/career-demo/references/projects/sample-notebook.md',
    'examples/career-demo/references/projects/sample-portal.md',
    'examples/career-demo/references/sources/demo-resume.md',
    'examples/resume-demo/match-report.md',
    'examples/resume-demo/career.md',
    'examples/resume-demo/request.md',
    'examples/resume-demo/resume.zh-CN.md',
    'examples/resume-demo/resume.en.md',
    'examples/resume-demo/period-review.md',
    'examples/resume-demo/jd-comparison.md',
    'package.json',
    'pnpm-lock.yaml',
    'pnpm-workspace.yaml',
    'references/career-workflow.md',
    'references/fact-contract.md',
    'references/resume-style.md',
    'references/english-resume.md',
    'references/profession-workflow.md',
    'references/enhancements.md',
    'references/resume-workflow.md',
    'scripts/career_resume/build_career.py',
    'scripts/career.py',
    'scripts/career_resume/__init__.py',
    'tools/build_site.py',
    'scripts/career_resume/build_timeline.py',
    'scripts/career_resume/bundle.py',
    'scripts/career_resume/career_data.py',
    'tools/check.py',
    'tools/check_public_index.py',
    'scripts/career_resume/cli_support.py',
    'scripts/career_resume/create_demo.py',
    'scripts/career_resume/doctor.py',
    'scripts/career_resume/export_resume.py',
    'scripts/career_resume/export_share.py',
    'scripts/career_resume/resume_versions.py',
    'scripts/career_resume/file_io.py',
    'scripts/career_resume/presentation.py',
    'scripts/career_resume/import_git_activity.py',
    'scripts/career_resume/init_profile.py',
    'scripts/career_resume/install_skill.py',
    'scripts/career_resume/package.py',
    'tools/release.py',
    'scripts/career_resume/update_profile.py',
    'scripts/career_resume/validate.py',
    'scripts/career_resume/workbench_store.py',
    'scripts/career_resume/serve_workbench.py',
    'assets/workbench/index.html.txt',
    'assets/workbench/workbench.js.txt',
    'assets/workbench/workbench.css.txt',
    'tests/scenarios.md',
    'tests/evals.json',
    'tests/test_demo.py',
    'tests/test_cli_feedback.py',
    'tests/test_enhancements.py',
    'tests/test_git_activity.py',
    'tests/test_local_profile.py',
    'tests/test_onboarding.py',
    'tests/test_agent_install.py',
    'tests/test_release.py',
    'tests/test_resume_tools.py',
    'tests/test_career_cli.py',
    'tests/test_resume_pdf.py',
    'tests/test_international_resume.py',
    'tests/test_profession_pages.py',
    'tests/test_story_timeline.py',
    'tests/test_written_career.py',
    'tests/test_write_recovery.py',
    'tests/test_workbench.py',
    'tests/test_profession_examples.py',
    *profession_public_files(),
)

STARTER_FILES = (
    '.gitignore',
    'local/README.md',
    'local/references/profile.md', 'local/references/facts.md', 'local/references/project-index.md',
    'local/references/career/README.md',
    'local/references/sources.md', 'local/references/sources/manifest.json',
    'local/references/questions-to-confirm.md', 'local/data/timeline.json',
)


# Runtime resources are selected from the controlled inventory, never a directory scan.
# Repository maintenance files stay available to source exports and index checks only.
RUNTIME_FILES = (
    'LICENSE.md', 'README.md', 'SKILL.md', 'agents/openai.yaml',
    'references/career-workflow.md', 'references/fact-contract.md', 'references/resume-style.md', 'references/english-resume.md', 'references/profession-workflow.md', 'references/enhancements.md', 'references/resume-workflow.md',
    'scripts/career_resume/build_career.py', 'scripts/career_resume/build_timeline.py', 'scripts/career.py',
    'scripts/career_resume/__init__.py',
    'scripts/career_resume/bundle.py',
    'scripts/career_resume/career_data.py', 'scripts/career_resume/create_demo.py', 'scripts/career_resume/doctor.py',
    'scripts/career_resume/cli_support.py',
    'scripts/career_resume/file_io.py',
    'scripts/career_resume/presentation.py', 'assets/themes/palette.json',
    'scripts/career_resume/export_resume.py', 'scripts/career_resume/resume_versions.py',
    'scripts/career_resume/export_share.py', 'scripts/career_resume/import_git_activity.py', 'scripts/career_resume/init_profile.py',
    'scripts/career_resume/install_skill.py', 'scripts/career_resume/package.py', 'scripts/career_resume/update_profile.py', 'scripts/career_resume/validate.py',
    'scripts/career_resume/workbench_store.py', 'scripts/career_resume/serve_workbench.py',
    'assets/workbench/index.html.txt', 'assets/workbench/workbench.js.txt', 'assets/workbench/workbench.css.txt',
    # The five-profession showcase is documentation/website material, not a
    # runtime dependency; keeping it out preserves the SkillHub file budget.
    # Keep operational instructions offline; the tutorial website stays in source.
    'docs/guide/quick-start.md', 'docs/guide/generate-webpage.md', 'docs/guide/workbench.md',
    'docs/guide/export-resume.md', 'docs/guide/troubleshooting.md', 'docs/reference/data-model.md',
    *(rel for rel in PUBLIC_FILES if rel.startswith('examples/')
      and not rel.endswith('.png') and not rel.startswith('examples/professions/')),
    *(rel for rel in PUBLIC_FILES if rel.startswith('assets/templates/')
      and rel != 'assets/templates/release-readme.md'),
)


def is_source_tree(root):
    """Recognize maintenance inputs without requiring them in an installed Skill."""
    return any((Path(root) / rel).exists() for rel in ('package.json', 'tools/check.py'))


def runtime_entries(root):
    """Complete installable Skill, including every template and demo dependency."""
    source_tree = is_source_tree(root)
    entries = {}
    for rel in RUNTIME_FILES:
        source = ({'README.md': 'assets/templates/release-readme.md', 'LICENSE.md': 'LICENSE'}.get(rel, rel)
                  if source_tree else rel)
        entries[rel] = checked_file(root, source)
    for rel in STARTER_FILES:
        source = starter_source(rel, runtime=not source_tree)
        output = starter_source(rel, runtime=True)
        entries[output] = checked_file(root, source)
    return entries


def read_version(root):
    path = Path(root) / 'VERSION'
    if not path.exists() and not path.is_symlink():
        return None
    value = checked_file(root, 'VERSION').read_text(encoding='utf-8').strip()
    return validate_version(value)


def validate_version(value):
    """Accept a complete numeric release version without guessing its significance."""
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value):
        raise ValueError('Version must be MAJOR.MINOR.PATCH, such as 1.1.0 (no v prefix or leading zeros).')
    return value


def select_version(root, explicit=None):
    """Prompt at the CLI boundary; automation must supply an explicit version."""
    if explicit is not None:
        return validate_version(explicit)
    if is_source_tree(root):
        current = read_version(root)
        if current is not None:
            print('上次本地打包版本：' + current)
    print('版本规则：修复改最后一位；兼容的新功能改中间一位；不兼容改第一位。')
    try:
        value = input('请输入本次打包版本号（例如 1.1.0；留空取消）：').strip()
    except (EOFError, KeyboardInterrupt) as exc:
        raise ValueError('未提供版本号，打包已取消。自动化调用请显式传入 --version X.Y.Z。') from exc
    if not value:
        raise ValueError('未提供版本号，打包已取消；现有版本和产物保留。')
    return validate_version(value)


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


def starter_source(relative, *, runtime=False):
    # A literal .gitignore inside starter/ would hide the templates themselves.
    if relative == '.gitignore':
        return 'assets/starter/gitignore.txt' if runtime else 'assets/starter/gitignore.template'
    return 'assets/starter/' + relative.removeprefix('local/')


def personal_entries(root):
    from career_resume.career_data import profile_root
    entries = public_entries(root) if is_source_tree(root) else runtime_entries(root)
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
    return entries
