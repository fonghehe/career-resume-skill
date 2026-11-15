"""Public five-profession examples stay fictional, self-contained and rebuildable."""

import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tools'))
from build_site import (build_examples, load_examples, render_markdown,
                        validate_example_data, validate_timeline_marker)
from career_resume.bundle import PROFESSION_SLUGS

EXAMPLES = 'examples/professions'
PAGES = ('index.html', 'career.html', 'resume.html', 'resume.en.html', 'report.html', 'timeline.html',
         'resume.zh-CN.md', 'resume.en.md', 'resume.zh-CN.docx', 'resume.en.docx',
         'data/timeline.json', 'output/career/career.md')


class ProfessionExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.base = Path(temporary.name).resolve()
        cls.output = cls.base / 'site'
        cls.target = build_examples(ROOT, cls.output)

    def test_committed_sources_are_explicitly_fictional(self):
        data, palette = load_examples(ROOT)
        self.assertIs(data['meta']['synthetic'], True)
        self.assertEqual(sorted(item['slug'] for item in data['examples']),
                         sorted(PROFESSION_SLUGS))
        for item in data['examples']:
            with self.subTest(slug=item['slug']):
                slug = item['slug']
                self.assertIs(item['synthetic'], True)
                self.assertTrue(item['email'].endswith('@example.com'))
                self.assertIn(item['theme'], palette['themes'])
                self.assertTrue(all(job['organization'].startswith('示例') for job in item['jobs']))
                root = ROOT / EXAMPLES / slug
                for rel in ('source/data/timeline.json', 'source/references/facts.md',
                            'source/references/sources/SYN01.md',
                            'resume.en.md', 'resume.zh-CN.md', 'match-report.md'):
                    self.assertTrue((root / rel).is_file(), rel)
                timeline = json.loads((root / 'source/data/timeline.json').read_text(encoding='utf-8'))
                self.assertIs(timeline['meta']['synthetic'], True)
        # No real-world contact details slipped into any public example text.
        sources = (ROOT / EXAMPLES).rglob('*')
        emails = {match for path in sources if path.is_file() and path.suffix in {'.md', '.json'}
                  for match in re.findall(r'[\w.+-]+@[\w.-]+\.[\w.-]+', path.read_text(encoding='utf-8'))}
        self.assertTrue(emails)
        self.assertTrue(all(email.endswith('@example.com') for email in emails), sorted(emails))

    def test_build_recreates_every_page_without_network_resources(self):
        target = self.target
        self.assertTrue((target / 'index.html').is_file())
        data, _ = load_examples(ROOT)
        for item in data['examples']:
            with self.subTest(slug=item['slug']):
                folder = target / item['slug']
                for rel in PAGES:
                    self.assertTrue((folder / rel).is_file(), rel)
                site = (folder / 'index.html').read_text(encoding='utf-8')
                self.assertIn('虚构', site)
                self.assertIn(item['name'], site)
                self.assertIn(item['cases'][0]['name'], site)
                self.assertIn(item['name'], (folder / 'resume.html').read_text(encoding='utf-8'))
                self.assertIn('职业履历', (folder / 'career.html').read_text(encoding='utf-8'))
                timeline = (folder / 'timeline.html').read_text(encoding='utf-8')
                self.assertIn('<script id="timeline-data"', timeline)
                self.assertIn('虚构', timeline)
        gallery = (target / 'index.html').read_text(encoding='utf-8')
        for item in data['examples']:
            self.assertIn(item['slug'] + '/index.html', gallery)
        for page in target.rglob('*.html'):
            text = page.read_text(encoding='utf-8')
            self.assertNotIn('<script src=', text, page.name)
            self.assertNotIn('https://', text, page.name)
            self.assertNotIn('@import', text, page.name)
            self.assertTrue((target / 'README.md').is_file())
            self.assertTrue((target / 'examples.json').is_file())

    def test_generated_relative_links_resolve(self):
        target = self.target
        broken = []
        for page in target.rglob('*.html'):
            for href in re.findall(r'href="([^"]+)"', page.read_text(encoding='utf-8')):
                if href.startswith(('#', 'mailto:', 'http://', 'https://')) or href.startswith('${'):
                    continue
                clean = href.split('#')[0]
                if clean and not (page.parent / clean).resolve().exists():
                    broken.append((page.relative_to(target).as_posix(), href))
        self.assertEqual(broken, [])

    def test_bilingual_exports_are_rebuildable_and_preserve_their_markdown_text(self):
        from career_resume.export_resume import document_text, paragraphs, visible_text
        from xml.etree import ElementTree as ET
        from zipfile import ZipFile
        # A second build must regenerate downloads without a file-exists failure.
        build_examples(ROOT, self.output)
        for slug in PROFESSION_SLUGS:
            for language in ('zh-CN', 'en'):
                folder = self.output / slug
                markdown = (folder / f'resume.{language}.md').read_text(encoding='utf-8')
                with ZipFile(folder / f'resume.{language}.docx') as archive:
                    self.assertIsNone(archive.testzip())
                    text = document_text(ET.fromstring(archive.read('word/document.xml')))
                self.assertEqual(text, [visible_text(style, line) for style, line in paragraphs(markdown)])

    def test_markdown_renderer_escapes_injected_markup_and_keeps_tables(self):
        rendered = render_markdown('# 标题\n\n<script>bad()</script>\n\n**粗体** '
                                   '[点我](javascript:bad)\n\n| 列 | 值 |\n|---|---|\n| A | B |\n')
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)
        self.assertIn('<strong>粗体</strong>', rendered)
        self.assertIn('href="#"', rendered)
        self.assertIn('<table>', rendered)
        self.assertIn('<td>B</td>', rendered)
        self.assertIn('<h1>标题</h1>', rendered)

    def test_real_contacts_and_unmarked_data_are_rejected(self):
        data, palette = load_examples(ROOT)
        changes = (
            lambda d: d['examples'][0].update(email='real.person@gmail.com'),
            lambda d: d['examples'][0]['jobs'][0].update(organization='某真实公司'),
            lambda d: d['examples'][0].update(synthetic=False),
            lambda d: d.update(meta={'synthetic': False}),
        )
        for change in changes:
            with self.subTest(change=repr(change)):
                mutated = copy.deepcopy(data)
                change(mutated)
                with self.assertRaises(ValueError):
                    validate_example_data(mutated, palette)

        marker = self.base / 'fake' / EXAMPLES / 'teacher/source/data/timeline.json'
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({'meta': {'synthetic': False}}), encoding='utf-8')
        with self.assertRaises(ValueError):
            validate_timeline_marker(self.base / 'fake', 'teacher')
        marker.write_text(json.dumps({'meta': {'synthetic': True}}), encoding='utf-8')
        validate_timeline_marker(self.base / 'fake', 'teacher')
        with self.assertRaises(ValueError):
            build_examples(ROOT, ROOT)


if __name__ == '__main__':
    unittest.main()
