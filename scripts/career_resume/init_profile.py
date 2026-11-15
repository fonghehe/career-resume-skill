#!/usr/bin/env python3
"""Create missing, Git-ignored local career files without replacing user data."""

from pathlib import Path

from career_resume.bundle import STARTER_FILES, checked_file, is_source_tree, starter_source
from career_resume.career_data import profile_root
from career_resume.file_io import write_new


def initialize(root):
    root = Path(root).resolve()
    profile = profile_root(root)
    pending = []
    skipped = 0
    runtime = not is_source_tree(root)
    for rel in STARTER_FILES:
        source = checked_file(root, starter_source(rel, runtime=runtime))
        target = root / rel if rel == '.gitignore' else profile / rel.removeprefix('local/')
        for path in (target, *target.parents):
            if path == root:
                break
            if path.is_symlink():
                raise ValueError('Refusing a symlink in local profile paths.')
        if target.exists():
            if not target.is_file():
                raise ValueError('A local profile file path is occupied by a directory.')
            skipped += 1
        else:
            pending.append((source, target))
    for source, target in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        write_new(target, source.read_bytes())
    return len(pending), skipped
