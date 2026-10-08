"""Regression tests for real release boundaries and portable data invariants."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from build_timeline import build, validate_data
from package import export
from validate import validate


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.public = self.base / 'public'
        export(ROOT, self.public, directory=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_public_starter_has_no_candidate_records_and_validates(self):
        errors, _ = validate(self.public)
        self.assertEqual(errors, [])
        data = json.loads((self.public / 'local/data/timeline.json').read_text())
        for key in ('career', 'projects', 'repositories'):
            self.assertEqual(data[key], [])
        self.assertEqual(data['profile']['name'], '')
        sources = json.loads((self.public / 'local/references/sources/manifest.json').read_text())
        self.assertEqual(sources['sources'], [])
        self.assertFalse((self.public / '.git').exists())
        self.assertFalse((self.public / 'docs/private-usage.md').exists())
        self.assertFalse((self.public / 'scripts/validate_personal.py').exists())
        self.assertFalse((self.public / 'showcase').exists())

    def test_default_zip_excludes_planted_private_data_and_preserves_source(self):
        sentinel = '-'.join(('PRIVATE', 'CANDIDATE', 'SENTINEL', '4937'))
        files = ('local/references/profile.md', 'local/references/user-confirmations/private.md',
                 'local/references/evidence/private.md', 'local/references/sources/raw.md',
                 'examples/ai-frontend/private.md', 'showcase/private.html',
                 'output/private.md', 'docs/private-usage.md', '.git/private.txt')
        for rel in files:
            path = self.public / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(sentinel)
        before = {rel: hashlib.sha256((self.public / rel).read_bytes()).hexdigest() for rel in files}
        archive_path = self.base / 'release.zip'
        export(self.public, archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            self.assertTrue(all(name.startswith('career-resume-skill/') for name in archive.namelist()))
            self.assertFalse(any(sentinel.encode() in archive.read(name) for name in archive.namelist()))
            self.assertIn('career-resume-skill/LICENSE', archive.namelist())
            target = self.base / 'unzipped'
            archive.extractall(target)
        self.assertEqual(validate(target / 'career-resume-skill')[0], [])
        after = {rel: hashlib.sha256((self.public / rel).read_bytes()).hexdigest() for rel in files}
        self.assertEqual(before, after)

    def test_personal_backup_requires_explicit_mode_and_keeps_data(self):
        sentinel = 'PERSONAL-BACKUP-SENTINEL'
        (self.public / 'local/references/profile.md').write_text(sentinel)
        target = self.base / 'personal.zip'
        export(self.public, target, include_personal=True)
        with zipfile.ZipFile(target) as archive:
            self.assertEqual(archive.read('career-resume-skill/local/references/profile.md').decode(), sentinel)

    def test_output_cannot_overwrite_sources_or_existing_exports(self):
        with self.assertRaises(ValueError):
            export(self.public, self.public / 'README.md', overwrite=True)
        with self.assertRaises(ValueError):
            export(self.public, self.public, directory=True)
        with self.assertRaises(ValueError):
            export(self.public, self.public.parent, directory=True)
        target = self.base / 'release.zip'
        export(self.public, target)
        old = target.read_bytes()
        with self.assertRaises(ValueError):
            export(self.public, target)
        self.assertEqual(target.read_bytes(), old)
        export(self.public, target, overwrite=True)
        with self.assertRaises(ValueError):
            export(self.public, self.public, directory=True, overwrite=True)

    def test_symlink_input_is_rejected(self):
        secret = self.base / 'secret.md'
        secret.write_text('secret')
        path = self.public / 'assets/templates/resume-template.md'
        path.unlink()
        path.symlink_to(secret)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            export(self.public, self.base / 'unsafe.zip')
        self.assertFalse((self.base / 'unsafe.zip').exists())

    def test_symlink_parent_input_is_rejected(self):
        original = self.public / 'agents'
        moved = self.base / 'moved-agents'
        original.rename(moved)
        original.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            export(self.public, self.base / 'unsafe.zip')

    def add_project(self):
        path = self.public / 'local/references/projects/ticket.md'
        path.parent.mkdir(parents=True)
        path.write_text('# P42｜示例项目\n\nP42-A confirmed：仅测试，参与页面开发。\n')
        (self.public / 'local/references/project-index.md').write_text('# 索引\n\n[项目](projects/ticket.md)\n')
        data = json.loads((self.public / 'local/data/timeline.json').read_text())
        data['projects'] = [{'id': 'P42', 'name': '示例项目', 'nature': 'personal',
                             'organization': '独立', 'category': '前端', 'status': 'confirmed',
                             'start': '', 'end': '', 'tech': [], 'highlights': []}]
        (self.public / 'local/data/timeline.json').write_text(json.dumps(data, ensure_ascii=False))
        return path, data

    def test_arbitrary_single_project_and_stale_html(self):
        path, _ = self.add_project()
        self.assertEqual(validate(self.public)[0], [])
        build(self.public)
        self.assertEqual(validate(self.public)[0], [])
        path.write_text(path.read_text() + '\n新增真实确认。\n')
        errors, _ = validate(self.public)
        self.assertTrue(any('stale' in error for error in errors), errors)
        build(self.public)
        self.assertEqual(validate(self.public)[0], [])

    def test_empty_timeline_builds_without_personal_details(self):
        html = build(self.public).read_text()
        self.assertIn('id="timeline-data"', html)
        self.assertIn('id="project-details"', html)
        self.assertEqual(validate(self.public)[0], [])

    def test_unsafe_urls_invalid_dates_and_synthetic_projects_rejected(self):
        _, data = self.add_project()
        for url in ('javascript:alert(1)', 'data:text/html,test', 'https:missing-host'):
            with self.subTest(url=url):
                copy = json.loads(json.dumps(data))
                copy['projects'][0]['url'] = url
                with self.assertRaises(ValueError):
                    validate_data(copy)
        for start, end in (('2025-02-31', '2025-03-01'), ('2025-03-01', '2025-02-01'),
                           ('2025-01-01', '')):
            with self.subTest(start=start, end=end):
                copy = json.loads(json.dumps(data))
                copy['projects'][0].update(start=start, end=end)
                with self.assertRaises(ValueError):
                    validate_data(copy)
        data['projects'][0]['status'] = 'synthetic-draft'
        with self.assertRaises(ValueError):
            validate_data(data)

    def test_source_path_cannot_escape_bundle(self):
        manifest = self.public / 'local/references/sources/manifest.json'
        manifest.write_text(json.dumps({'sources': [{'id': 'S8', 'extracted_text': '../outside.md'}]}))
        errors, _ = validate(self.public)
        self.assertTrue(any('escapes bundle' in error for error in errors), errors)

    def test_plain_text_sources_need_no_pdf_hash(self):
        (self.public / 'local/references/sources/S8.md').write_text('# 授权文本快照\n')
        manifest = self.public / 'local/references/sources/manifest.json'
        manifest.write_text(json.dumps({'sources': [{'id': 'S8', 'extracted_text': 'references/sources/S8.md'}]}))
        self.assertEqual(validate(self.public)[0], [])


if __name__ == '__main__':
    unittest.main()
