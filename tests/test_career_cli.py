"""Exercise the installed entry point against a separate complete workspace."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from career_resume.package import export


class CareerCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.installation = self.base / 'installed'
        export(ROOT, self.installation, directory=True, runtime=True)

    def run_cli(self, *args, ok=True, input_text=None):
        result = subprocess.run([sys.executable, '-B', str(self.installation / 'scripts/career.py'),
                                 *map(str, args)], cwd=self.base, input=input_text, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stdout + result.stderr)
        return result

    def test_new_workspace_build_validate_and_relative_export_use_selected_workspace(self):
        workspace = self.base / 'my-career'
        self.run_cli('init', '--new', workspace)
        timeline = workspace / 'local/data/timeline.json'
        data = json.loads(timeline.read_text())
        data['meta']['synthetic'] = True
        timeline.write_text(json.dumps(data))
        profile = workspace / 'local/references/profile.md'
        with profile.open('a', encoding='utf-8') as stream:
            stream.write('\n虚构教学候选人：参与课程设计，尚未提供任职日期。\n')
        self.run_cli('--workspace', workspace, 'init')
        self.assertIn('虚构教学候选人', profile.read_text())
        self.run_cli('--workspace', workspace, 'build', '--web')
        self.assertIn('虚构教学候选人', (workspace / 'local/output/career/career.md').read_text())
        self.assertTrue((workspace / 'local/showcase/project-timeline.html').is_file())
        self.run_cli('--workspace', workspace, 'validate')
        resume = workspace / 'local/output/career/resume.en.md'
        resume.write_text('# Fictional Teacher\n\n## Skills\n\n- Course design.\n')
        self.run_cli('--workspace', workspace, 'export', 'local/output/career/resume.en.md')
        self.assertTrue(resume.with_suffix('.docx').is_file())
        self.assertFalse((self.installation / 'local/output/career/career.md').exists())

    def test_existing_workspace_and_exports_are_preserved(self):
        self.run_cli('init', '--new', self.installation, ok=False)
        source = self.base / 'resume.zh-CN.md'
        source.write_text('# 虚构候选人\n\n## 技能\n\n- 课程设计。\n')
        self.run_cli('export', source)
        original = source.with_suffix('.docx').read_bytes()
        self.run_cli('export', source, ok=False)
        self.assertEqual(source.with_suffix('.docx').read_bytes(), original)

    def test_all_command_help_is_available_in_the_runtime_without_source_tools(self):
        self.assertFalse((self.installation / 'tools').exists())
        for command in ('init', 'build', 'web', 'validate', 'export', 'workbench',
                        'doctor', 'demo', 'install', 'package', 'git', 'update', 'share', 'versions'):
            with self.subTest(command=command):
                self.assertIn('usage:', self.run_cli(command, '--help').stdout)

    def test_forwarded_version_command_uses_selected_workspace(self):
        workspace = self.base / 'separate-workspace'
        self.run_cli('init', '--new', workspace)
        version = workspace / 'local/output/resumes/fictional-version'
        version.mkdir(parents=True)
        (version / 'match-report.md').write_text(
            '> 虚构教学示例\n\n## 正文依据\n\n'
            '| 正文位置 / 主张 | 履历条目 ID | 来源 |\n'
            '|---|---|---|\n| Fictional claim | P42-A | SYN01 |\n', encoding='utf-8')
        result = self.run_cli('--workspace', workspace, 'versions', 'impact', '--fact', 'P42-A')
        self.assertIn('fictional-version: P42-A | Fictional claim', result.stdout)
        self.assertFalse((self.installation / 'local').exists())

    def test_runtime_rejects_source_only_demo_before_writing(self):
        result = self.run_cli('demo', '--docs', ok=False)
        self.assertIn('full source project', result.stderr)
        self.assertFalse((self.installation / 'docs/public').exists())
        self.assertFalse((self.installation / 'local').exists())

    def test_runtime_zip_asks_for_version_and_explicit_automation_needs_no_input(self):
        result = self.run_cli('package', input_text='3.1.4\n')
        self.assertIn('请输入本次打包版本号', result.stdout)
        archive = self.installation / 'local/dist/career-resume-skill-3.1.4.zip'
        with ZipFile(archive) as bundle:
            self.assertIn('version: 3.1.4', bundle.read('career-resume-skill/SKILL.md').decode())
        self.run_cli('package', '--version', '3.1.5', input_text='')
        self.assertTrue((self.installation / 'local/dist/career-resume-skill-3.1.5.zip').is_file())

    def test_missing_or_invalid_zip_version_writes_nothing(self):
        for answer in ('', '\n', 'v1.2.3\n', '01.2.3\n'):
            with self.subTest(answer=answer):
                self.run_cli('package', input_text=answer, ok=False)
                self.assertFalse((self.installation / 'local').exists())
        self.run_cli('install', '--output', self.base / 'cancelled.zip', input_text='', ok=False)
        self.assertFalse((self.base / 'cancelled.zip').exists())


if __name__ == '__main__':
    unittest.main()
