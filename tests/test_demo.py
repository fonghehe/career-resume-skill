"""Ensure the public demo is independent from private user records."""

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from career_resume.build_timeline import build
from career_resume.bundle import repository_entries
from career_resume.create_demo import create
from career_resume.init_profile import initialize
from career_resume.package import write_tree


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / 'clone'
        self.repo.mkdir()
        write_tree(repository_entries(ROOT), self.repo)
        private = self.repo / 'data/timeline.json'
        private.parent.mkdir()
        # Invalid JSON must not matter: no private input is loaded.
        private.write_text('PRIVATE_SENTINEL_NOT_JSON', encoding='utf-8')
        self.private = private
        self.digest = hashlib.sha256(private.read_bytes()).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def test_local_and_docs_demo_only_embed_fictional_fixture(self):
        for page in (create(self.repo), create(self.repo, docs=True)):
            html = page.read_text(encoding='utf-8')
            self.assertIn('林小禾', html)
            self.assertIn('教学数据', html)
            self.assertIn('sample-console.md', html)
            self.assertIn('id="career" open', html)
            self.assertIn('id="projects" open', html)
            self.assertNotIn('PRIVATE_SENTINEL', html)
        self.assertEqual(hashlib.sha256(self.private.read_bytes()).hexdigest(), self.digest)

    def test_demo_exports_both_word_samples_with_fictional_markers(self):
        from xml.etree import ElementTree as ET
        W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        resume = create(self.repo).parents[1] / 'resume'
        cases = (('zh-CN', '虚构教学示例', '11906'),
                 ('en', 'Fictional teaching example', '12240'))
        for lang, notice, width in cases:
            with ZipFile(resume / f'resume.{lang}.docx') as word:
                document = word.read('word/document.xml')
                self.assertIn(notice.encode(), document)
                page = ET.fromstring(document).find(f'{{{W}}}body/{{{W}}}sectPr/{{{W}}}pgSz')
                self.assertEqual(page.get(f'{{{W}}}w'), width)
        for report in ('match-report.md', 'period-review.md', 'jd-comparison.md'):
            self.assertIn('E01-A', (resume / report).read_text(encoding='utf-8'))

    def test_empty_personal_timeline_links_to_separate_existing_demo(self):
        self.private.unlink()
        self.private.parent.rmdir()
        initialize(self.repo)
        personal = build(self.repo)
        html = personal.read_text(encoding='utf-8')
        self.assertIn('id="emptyTimeline">', html)
        self.assertNotIn('<a id="localDemoLink"', html)
        example = create(self.repo)
        html = build(self.repo).read_text(encoding='utf-8')
        self.assertIn('href="../output/demo/showcase/project-timeline.html"', html)
        self.assertNotIn('林小禾', html)
        self.assertIn('林小禾', example.read_text(encoding='utf-8'))

    def test_repeat_demo_refuses_to_overwrite_existing_output(self):
        page = create(self.repo)
        page.write_text('existing output must survive')
        with self.assertRaises(ValueError):
            create(self.repo)
        self.assertEqual(page.read_text(), 'existing output must survive')

    def test_demo_cannot_target_private_data_directory(self):
        with self.assertRaises(ValueError):
            create(self.repo, self.repo / 'data/new-demo')
        self.assertFalse((self.repo / 'data/new-demo').exists())

    def test_symlink_docs_target_cannot_write_into_private_directory(self):
        public = self.repo / 'docs/public'
        public.mkdir()
        outside = Path(self.temp.name) / 'private'
        outside.mkdir()
        (public / 'demo').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            create(self.repo, docs=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_fixture_cannot_become_public_demo_input(self):
        fixture = self.repo / 'examples/career-demo/data/timeline.json'
        fixture.unlink()
        fixture.symlink_to(self.private)
        with self.assertRaises(ValueError):
            create(self.repo, docs=True)
        self.assertFalse((self.repo / 'docs/public/demo/timeline.html').exists())


if __name__ == '__main__':
    unittest.main()
