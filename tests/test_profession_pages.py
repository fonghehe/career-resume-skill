"""Isolated non-software pages keep relevant modules and omit empty code UI."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from career_resume.build_timeline import build, render_html, validate_data
from career_resume.package import export
from career_resume.presentation import profession_modules, technical_view


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.nodes = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.nodes[attrs['id']] = attrs


class ProfessionPageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve() / 'skill'
        export(ROOT, self.root, directory=True)
        self.data = json.loads((self.root / 'local/data/timeline.json').read_text())
        self.data['meta']['synthetic'] = True

    def test_professions_render_their_own_populated_modules_without_code(self):
        for profession, title in (('教师', '课程与教研'), ('销售', '客户服务案例'), ('设计师', '设计作品')):
            with self.subTest(profession=profession):
                self.data['presentation'] = {'profession': profession, 'theme': 'sage',
                    'sections': [{'id':'work', 'title':title, 'items':[
                        {'title':'虚构实践', 'period':'2024年', 'summary':'有来源的示例工作', 'factIds':['F01']}]},
                        {'id':'empty', 'title':'无材料模块', 'items':[]}], 'order':['work']}
                validate_data(self.data)
                (self.root / 'local/data/timeline.json').write_text(json.dumps(self.data))
                html = build(self.root).read_text()
                nodes = Elements(html).nodes
                self.assertIn('professional-work', nodes)
                self.assertNotIn('professional-empty', nodes)
                self.assertIn('hidden', nodes['repositories'])
                self.assertIn('hidden', nodes['projects'])
                self.assertIn(title, html)
                self.assertIn('2024年', html)

    def test_content_is_escaped_and_invalid_module_or_order_is_rejected(self):
        self.data['presentation'] = {'sections':[{'id':'practice', 'title':'<script>bad()</script>',
            'items':[{'title':'虚构案例', 'summary':'<img src=x onerror=bad()>', 'bullets':['A & B']}]}]}
        modules, _ = profession_modules(self.data)
        self.assertNotIn('<script>', modules)
        self.assertIn('&lt;script&gt;', modules)
        self.assertIn('&lt;img', modules)
        for mutate in (lambda d:d['presentation'].update(order=['missing']),
                       lambda d:d['presentation']['sections'].append(copy.deepcopy(d['presentation']['sections'][0])),
                       lambda d:d['presentation']['sections'][0].update(id='unsafe" onclick="bad'),
                       lambda d:d['presentation']['sections'][0]['items'][0].update(factIds='F01')):
            data = copy.deepcopy(self.data)
            mutate(data)
            with self.assertRaises(ValueError):
                validate_data(data)

    def test_existing_software_pages_keep_actual_code_records(self):
        data = json.loads((ROOT / 'examples/career-demo/data/timeline.json').read_text())
        html = render_html(data, {})
        self.assertNotIn('hidden', Elements(html).nodes['repositories'])
        self.assertIn('代码活动', html)

    def test_arbitrary_or_unknown_profession_defaults_to_generic_categories(self):
        for profession in ('', '文物修复与社区服务', '自由职业／跨领域实践'):
            self.data['presentation'] = {'profession': profession}
            self.assertFalse(technical_view(self.data))
            self.data['presentation']['technical'] = True
            self.assertTrue(technical_view(self.data))
        legacy = json.loads((ROOT / 'examples/career-demo/data/timeline.json').read_text())
        legacy.pop('presentation', None)
        self.assertTrue(technical_view(legacy))
        legacy['presentation'] = {'technical': False}
        self.assertFalse(technical_view(legacy))


if __name__ == '__main__':
    unittest.main()
