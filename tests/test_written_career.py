"""Written careers preserve maintained facts and the private export boundary."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_career import build
from init_profile import initialize
from package import export


class WrittenCareerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'workspace'
        export(ROOT, self.root, directory=True)
        self.profile = self.root / 'local'

    def tearDown(self):
        self.temp.cleanup()

    def test_text_only_career_preserves_precision_states_and_contribution(self):
        (self.profile / 'data/timeline.json').unlink()
        profile = self.profile / 'references/profile.md'
        profile.write_text('# 任职\nE01-A｜2024.01–离职未知｜参与页面维护｜confirmed\n')
        card = self.profile / 'references/projects/portal.md'
        card.parent.mkdir()
        card.write_text('# P01｜项目\nP01-A｜resume-supported｜本人只做前端，Java 是项目环境。\n')
        source_files = list((self.profile / 'references').rglob('*.md'))
        before = {p: p.read_bytes() for p in source_files}
        target = build(self.root)
        text = target.read_text()
        self.assertIn('2024.01–离职未知', text)
        self.assertIn('E01-A', text)
        self.assertIn('confirmed', text)
        self.assertIn('P01-A｜resume-supported｜本人只做前端，Java 是项目环境。', text)
        self.assertEqual({p: p.read_bytes() for p in source_files}, before)
        first = target.read_bytes()
        self.assertEqual(build(self.root).read_bytes(), first)
        self.assertFalse((self.profile / 'showcase').exists())

    def test_links_remain_usable_and_code_examples_are_preserved(self):
        profile = self.profile / 'references/profile.md'
        profile.write_text('# 档案\n[事实](facts.md)\n```md\n# 原始文本\n[事实](facts.md)\n```\n')
        text = build(self.root).read_text()
        self.assertIn('[事实](<../../references/facts.md>)', text)
        self.assertIn('```md\n# 原始文本\n[事实](facts.md)\n```', text)

    def test_nested_career_records_are_included_once_and_rebuilt(self):
        case = self.profile / 'references/career/cases/realtime/P01-reconnect.md'
        case.parent.mkdir(parents=True)
        case.write_text('# 重连案例\nP01-A｜confirmed｜本人实现状态恢复。\n'
                        '[来源](../../../sources.md)\n')
        skills = self.profile / 'references/career/skills.md'
        skills.write_text('# 能力依据\n仅依据 P01-A，保留本人职责边界。\n')
        entry = self.profile / 'references/career/README.md'
        entry.write_text('# 履历入口\n[重连案例](cases/realtime/P01-reconnect.md)\n')
        before = {path: path.read_bytes() for path in (entry, case, skills)}
        text = build(self.root).read_text()
        self.assertEqual(text.count('### 履历入口'), 1)
        self.assertEqual(text.count('### 重连案例'), 1)
        self.assertIn('P01-A｜confirmed｜本人实现状态恢复。', text)
        self.assertIn('仅依据 P01-A，保留本人职责边界。', text)
        self.assertIn('[来源](<../../references/sources.md>)', text)
        self.assertIn('[重连案例](<../../references/career/cases/realtime/P01-reconnect.md>)', text)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        case.write_text(case.read_text() + '\n结果仍待确认。\n')
        self.assertIn('结果仍待确认。', build(self.root).read_text())

    def test_symlink_career_records_cannot_change_existing_output(self):
        target = build(self.root)
        before = target.read_bytes()
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (outside / 'case.md').write_text('External material')
        link = self.profile / 'references/career/cases'
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            build(self.root)
        self.assertEqual(target.read_bytes(), before)
        link.unlink()
        link = self.profile / 'references/career/case.md'
        link.symlink_to(outside / 'case.md')
        with self.assertRaises(ValueError):
            build(self.root)
        self.assertEqual(target.read_bytes(), before)

    def test_rebuild_reflects_corrections_without_overwriting_an_existing_resume(self):
        target = build(self.root)
        old = target.read_bytes()
        resume = self.profile / 'output/resumes/existing/resume.zh-CN.md'
        resume.parent.mkdir(parents=True)
        resume.write_text('Existing application version')
        (self.profile / 'references/facts.md').write_text('E01-A 更正职称，其他字段仍待确认。')
        self.assertNotEqual(build(self.root).read_bytes(), old)
        self.assertEqual(resume.read_text(), 'Existing application version')

    def test_outputs_cannot_replace_sources_symlinks_or_handwritten_records(self):
        source = self.profile / 'references/facts.md'
        before = source.read_bytes()
        with self.assertRaises(ValueError):
            build(self.root, source)
        self.assertEqual(source.read_bytes(), before)
        target = self.profile / 'output/career/manual.md'
        target.parent.mkdir(parents=True)
        target.write_text('Handwritten record')
        with self.assertRaises(ValueError):
            build(self.root, target)
        self.assertEqual(target.read_text(), 'Handwritten record')
        link = self.profile / 'output/linked'
        link.symlink_to(source.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            build(self.root, link / 'facts.md')

    def test_private_written_records_are_absent_from_public_export(self):
        marker = '-'.join(('PRIVATE', 'WRITTEN', 'CAREER', 'SENTINEL'))
        (self.profile / 'references/profile.md').write_text(marker)
        case = self.profile / 'references/career/cases/private.md'
        case.parent.mkdir(parents=True)
        case.write_text(marker)
        build(self.root)
        public = Path(self.temp.name) / 'public'
        export(self.root, public, directory=True)
        self.assertFalse((public / 'local/output/career/career.md').exists())
        self.assertFalse(any(marker.encode() in p.read_bytes() for p in public.rglob('*') if p.is_file()))

    def test_initializer_preserves_existing_career_entry(self):
        entry = self.profile / 'references/career/README.md'
        entry.write_text('Existing career entry')
        initialize(self.root)
        self.assertEqual(entry.read_text(), 'Existing career entry')

    def test_generated_career_from_previous_name_can_be_rebuilt(self):
        target = build(self.root)
        legacy = '<!-- career-skill:generated-career -->'
        current = '<!-- career-resume-skill:generated-career -->'
        target.write_text(target.read_text().replace(current, legacy, 1))
        source = self.profile / 'references/facts.md'
        source.write_text('E01-A 本人确认，只负责前端。')
        before = source.read_bytes()
        result = build(self.root).read_text()
        self.assertTrue(result.startswith(current + '\n'))
        self.assertIn('E01-A 本人确认，只负责前端。', result)
        self.assertEqual(source.read_bytes(), before)

    def test_synthetic_data_is_labeled_and_script_uses_its_workspace(self):
        path = self.profile / 'data/timeline.json'
        data = json.loads(path.read_text())
        data['meta']['synthetic'] = True
        path.write_text(json.dumps(data))
        result = subprocess.run([sys.executable, '-B', str(self.root / 'scripts/build_career.py')],
                                cwd=self.temp.name, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('虚构教学履历', (self.profile / 'output/career/career.md').read_text())


if __name__ == '__main__':
    unittest.main()
