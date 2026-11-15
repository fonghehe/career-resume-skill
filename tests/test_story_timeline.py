"""Test company stages, project milestones, Git associations and safe embedding."""

import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from career_resume.build_timeline import build, validate_data
from career_resume.create_demo import create


class ProjectTimelineTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'examples/career-demo/data/timeline.json').read_text())

    def test_svn_working_copy_evidence_is_separate_from_git_counts(self):
        data = copy.deepcopy(self.data)
        data['projects'][0]['svnWorkingCopy'] = {
            'name': 'fictional-svn', 'revision': 42, 'author': 'demo-author',
            'fileCount': 7, 'directoryCount': 3, 'visibleRevisionCount': 4,
            'start': '2023-01-01T10:00:00+08:00', 'end': '2023-02-01T10:00:00+08:00',
            'historyComplete': False,
        }
        validate_data(data)
        self.assertEqual(sum(r['count'] for r in data['repositories']), 14)
        for key, value in [('fileCount', True), ('fileCount', -1), ('revision', '42'),
                           ('historyComplete', True), ('commitCount', 4),
                           ('start', 'not-a-date'), ('end', '2020-01-01T00:00:00Z')]:
            with self.subTest(key=key, value=value):
                bad = copy.deepcopy(data)
                bad['projects'][0]['svnWorkingCopy'][key] = value
                with self.assertRaises(ValueError):
                    validate_data(bad)
        for value in (None, [], 'svn'):
            bad = copy.deepcopy(data)
            bad['projects'][0]['svnWorkingCopy'] = value
            with self.assertRaises(ValueError):
                validate_data(bad)

    def test_demo_is_complete_and_separately_marked_fictional(self):
        validate_data(self.data)
        self.assertTrue(self.data['meta']['synthetic'])
        self.assertGreaterEqual(len(self.data['projects']), 3)
        self.assertNotIn('memories', self.data)
        companies = {e.get('groupOrganization', e['organization']) for e in self.data['career']}
        self.assertEqual(len(companies), 2)
        self.assertEqual(len(self.data['career']), 3)
        self.assertEqual(sum(r['count'] for r in self.data['repositories']), 14)
        self.assertTrue(all(p['milestones'] for p in self.data['projects']))
        self.assertGreaterEqual(len(self.data['gitEvents']), 10)
        for repo in self.data['repositories']:
            events = [e for e in self.data['gitEvents'] if e['repository'] == repo['name']]
            self.assertEqual(len(events), repo['count'])
            self.assertTrue(all(e['projectId'] == repo['projectId'] for e in events))

    def test_project_stages_and_grades_require_structured_values(self):
        mutations = (
            lambda d: d['career'][0].update(level=6),
            lambda d: d['projects'][0].update(milestones='some stages'),
            lambda d: d['projects'][0]['milestones'][0].update(title=123),
            lambda d: d['projects'][0]['milestones'][0].update(date=2024),
        )
        for mutate in mutations:
            data = copy.deepcopy(self.data)
            mutate(data)
            with self.assertRaises(ValueError):
                validate_data(data)

    def test_unassociated_duplicate_or_invalid_git_records_are_rejected(self):
        mutations = (
            lambda d: d['gitEvents'][0].update(repository='missing'),
            lambda d: d['gitEvents'][0].update(projectId='P99'),
            lambda d: d['gitEvents'][0].update(sha='not-a-commit'),
            lambda d: d['gitEvents'][0].update(authorDate='2020-01-01T10:00:00+08:00'),
            lambda d: d['gitEvents'][0].update(committerDate='2025-01-01'),
            lambda d: d['gitEvents'].append(dict(d['gitEvents'][0], id='another-id')),
        )
        for mutate in mutations:
            data = copy.deepcopy(self.data)
            mutate(data)
            with self.assertRaises(ValueError):
                validate_data(data)

    def test_original_commit_and_milestones_survive_safe_html_embedding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / 'demo'
            create(ROOT, root)
            data = json.loads((root / 'data/timeline.json').read_text())
            text = '</script><img src=x onerror="alert(1)"> a commit subject'
            data['projects'][0]['milestones'][0]['title'] = text
            data['gitEvents'][0]['subject'] = text
            (root / 'data/timeline.json').write_text(json.dumps(data))
            html = build(root).read_text()
            self.assertNotIn(text, html)
            embedded = re.search(r'<script id="timeline-data" type="application/json">(.*?)</script>', html, re.S)
            self.assertEqual(json.loads(embedded.group(1)), data)

    def test_legacy_extra_fields_are_preserved_without_a_diary_view(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / 'demo'
            create(ROOT, root)
            path = root / 'data/timeline.json'
            data = json.loads(path.read_text())
            data['memories'] = [{'title': 'legacy private material'}]
            path.write_text(json.dumps(data))
            before = path.read_bytes()
            html = build(root).read_text()
            self.assertEqual(path.read_bytes(), before)
            self.assertNotIn('id="memories"', html)
            self.assertNotIn('id="memoryGrid"', html)

    def test_existing_blank_data_needs_no_new_fields(self):
        data = json.loads((ROOT / 'assets/starter/data/timeline.json').read_text())
        validate_data(data)


if __name__ == '__main__':
    unittest.main()
