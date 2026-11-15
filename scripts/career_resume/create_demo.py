#!/usr/bin/env python3
"""Build fictional timeline and resume examples without reading user records."""

from career_resume import ROOT
from pathlib import Path
import shutil

from career_resume.build_timeline import build
from career_resume.bundle import checked_file, is_source_tree
from career_resume.export_resume import export

FIXTURES = (
    'data/timeline.json',
    'references/projects/sample-portal.md',
    'references/projects/sample-console.md',
    'references/projects/sample-notebook.md',
    'references/sources/demo-resume.md',
    'references/attachments/demo-release.md',
)

RESUME_FIXTURES = (
    'request.md', 'career.md', 'match-report.md', 'resume.zh-CN.md', 'resume.en.md',
    'period-review.md', 'jd-comparison.md',
)


def create(root=ROOT, output=None, *, docs=False):
    root = Path(root).resolve()
    if docs and not is_source_tree(root):
        raise ValueError('Documentation examples require the full source project; use demo without --docs in a runtime Skill.')
    source = root / 'examples/career-demo'
    media = 'references/attachments/demo-phases.' + ('png' if is_source_tree(root) else 'md')
    fixtures = (*FIXTURES, media)
    for rel in fixtures:
        checked_file(root, 'examples/career-demo/' + rel)
    if docs:
        if output is not None:
            raise ValueError('Docs mode has a fixed output path.')
        # Only explicit fictional fixtures are loaded, never root/data/ or local/.
        target = root / 'docs/public/demo/timeline.html'
        if any(path.is_symlink() for path in (target, *target.parents)):
            raise ValueError('Refusing a symlink documentation output path.')
        import runpy
        build_examples = runpy.run_path(str(checked_file(root, 'tools/build_site.py')))['build_examples']
        build(source, target)
        build_examples(root, root / 'docs/public/demo/professions')
        return target
    resumes = [checked_file(root, 'examples/resume-demo/' + name) for name in RESUME_FIXTURES]
    raw = Path(output) if output is not None else root / 'local/output/demo'
    if any(path.is_symlink() for path in (raw, *raw.parents)):
        raise ValueError('Refusing a symlink output directory.')
    target = raw.resolve()
    if target == root or target in root.parents:
        raise ValueError('Demo must not replace the project or its parents.')
    if root in target.parents and not (target.is_relative_to(root / 'output') or target.is_relative_to(root / 'local/output')):
        raise ValueError('A demo inside the project must be under local/output/.')
    if target.exists():
        raise ValueError('Demo directory exists; choose a new --output directory.')
    target.mkdir(parents=True)
    for rel in fixtures:
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, path)
    resume_dir = target / 'resume'
    resume_dir.mkdir()
    for fixture in resumes:
        path = resume_dir / fixture.name
        shutil.copyfile(fixture, path)
        if fixture.name == 'resume.zh-CN.md':
            export(path)
        elif fixture.name == 'resume.en.md':
            export(path, layout='international')
    return build(target)
