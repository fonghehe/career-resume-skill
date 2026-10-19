"""Observable first-use, workspace isolation and versioned release behavior."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from doctor import diagnose
from package import export
from release import build_release, read_version
from validate import validate


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / 'installation'
        export(ROOT, self.source, directory=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_workspace_cli_does_not_copy_or_replace_installation_profile(self):
        profile = self.source / 'local/references/profile.md'
        profile.write_text('PRIVATE-SHARED-INSTALLATION', encoding='utf-8')
        before = profile.read_bytes()
        workspace = self.base / 'my career'
        result = subprocess.run([sys.executable, str(self.source / 'scripts/init_profile.py'),
                                 '--workspace', str(workspace)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(profile.read_bytes(), before)
        self.assertNotIn('PRIVATE-SHARED-INSTALLATION',
                         (workspace / 'local/references/profile.md').read_text())
        self.assertEqual(validate(workspace)[0], [])
        data = json.loads((workspace / 'local/data/timeline.json').read_text())
        self.assertEqual(data['projects'], [])
        own_profile = workspace / 'local/references/profile.md'
        own_profile.write_text('MY EXISTING CAREER', encoding='utf-8')
        repeat = subprocess.run([sys.executable, str(self.source / 'scripts/init_profile.py'),
                                 '--workspace', str(workspace)], capture_output=True, text=True)
        self.assertNotEqual(repeat.returncode, 0)
        self.assertEqual(own_profile.read_text(), 'MY EXISTING CAREER')

    def test_doctor_does_not_read_personal_profile_or_require_optional_tools(self):
        (self.source / 'local/references/profile.md').write_bytes(b'\xff\xfePRIVATE')
        with patch('doctor.probe', return_value=None):
            rows = diagnose(self.source)
            self.assertFalse(any(status == 'ERROR' for status, _ in rows), rows)
            docs = diagnose(self.source, docs=True)
            self.assertTrue(any(status == 'ERROR' for status, _ in docs))

    def test_workspace_guide_is_initialized_and_personal_changes_are_preserved(self):
        from init_profile import initialize
        guide = self.source / 'local/README.md'
        self.assertTrue(guide.is_file())
        guide.write_text('My private workspace notes', encoding='utf-8')
        initialize(self.source)
        self.assertEqual(guide.read_text(), 'My private workspace notes')
        workspace = self.base / 'new-workspace'
        export(self.source, workspace, directory=True)
        self.assertNotIn('My private workspace notes', (workspace / 'local/README.md').read_text())
        self.assertEqual(validate(workspace)[0], [])

    def test_grouped_examples_are_complete_in_public_workspace(self):
        demo = self.source / 'assets/examples/resume-demo'
        self.assertEqual({p.name for p in demo.iterdir()},
                         {'request.md', 'career.md', 'resume.zh-CN.md', 'match-report.md'})
        self.assertTrue((self.source / 'assets/examples/career-demo/data/timeline.json').is_file())
        self.assertFalse((self.source / 'assets/examples/request.md').exists())
        self.assertEqual(validate(self.source)[0], [])

    def test_doctor_reports_incomplete_installation(self):
        (self.source / 'assets/templates/project-template.md').unlink()
        with patch('doctor.probe', return_value=None):
            self.assertTrue(any(status == 'ERROR' for status, _ in diagnose(self.source)))

    def test_release_checksum_version_and_blank_data_match_actual_archive(self):
        sentinel = ' '.join(('PRIVATE', 'RELEASE', 'RECORD'))
        (self.source / 'local/references/profile.md').write_text(sentinel)
        output = build_release(self.source)
        version = read_version(self.source)
        archive = output / f'career-resume-skill-{version}.zip'
        digest, name = (output / 'SHA256SUMS').read_text().strip().split()
        self.assertEqual(name, archive.name)
        self.assertEqual(digest, hashlib.sha256(archive.read_bytes()).hexdigest())
        with zipfile.ZipFile(archive) as bundle:
            names = [path.removeprefix('career-resume-skill/') for path in bundle.namelist()]
            for excluded in ('VERSION', '.gitignore', 'AGENTS.md', 'package.json',
                             'pnpm-lock.yaml', 'pnpm-workspace.yaml', 'scripts/release.py',
                             'scripts/check.py', 'scripts/check_public_index.py'):
                self.assertNotIn(excluded, names)
            self.assertFalse(any(path.startswith(('.github/', 'tests/', 'docs/maintainers/',
                                                 'docs/.vitepress/')) for path in names))
            self.assertFalse(any(sentinel.encode() in bundle.read(path)
                                 for path in bundle.namelist()))
            data = json.loads(bundle.read('career-resume-skill/local/data/timeline.json'))
            self.assertEqual(data['career'], [])
        before = archive.read_bytes()
        with self.assertRaises(ValueError):
            build_release(self.source)
        self.assertEqual(archive.read_bytes(), before)

    def test_extracted_release_runs_without_repository_files(self):
        output = build_release(self.source)
        with zipfile.ZipFile(next(output.glob('*.zip'))) as archive:
            archive.extractall(self.base / 'extracted')
        skill = self.base / 'extracted/career-resume-skill'
        self.assertFalse((skill / '.gitignore').exists())
        original_profile = (skill / 'local/references/profile.md').read_bytes()
        # Every command uses modules from the actual unpacked bundle, not this checkout.
        workspace = self.base / 'private-workspace'
        installed = self.base / 'other-host'
        for args in (
            ('doctor.py',), ('init_profile.py',), ('validate.py',), ('create_demo.py',),
            ('build_career.py',), ('build_timeline.py',), ('validate.py',),
            ('init_profile.py', '--workspace', str(workspace)),
            ('install_skill.py', '--skills-dir', str(installed)),
            ('package.py', '--output', str(self.base / 'repacked.zip')),
        ):
            with self.subTest(command=args):
                result = subprocess.run([sys.executable, '-B', str(skill / 'scripts' / args[0]),
                                         *args[1:]], cwd=self.base, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((skill / 'local/output/demo/showcase/project-timeline.html').is_file())
        self.assertTrue((skill / '.gitignore').is_file())
        self.assertEqual((skill / 'local/references/profile.md').read_bytes(), original_profile)
        self.assertEqual(validate(workspace)[0], [])
        self.assertEqual(validate(installed / 'career-resume-skill')[0], [])
        self.assertTrue((workspace / '.gitignore').is_file())
        subprocess.run(['git', 'init', '-q', str(workspace)], check=True)
        ignored = subprocess.run(['git', '-C', str(workspace), 'check-ignore', 'local/references/profile.md'],
                                 capture_output=True, text=True)
        self.assertEqual(ignored.returncode, 0, ignored.stderr)
        (skill / 'assets/examples/career-demo/references/attachments/demo-phases.png').unlink()
        broken = subprocess.run([sys.executable, '-B', str(skill / 'scripts/doctor.py')],
                                capture_output=True, text=True)
        self.assertNotEqual(broken.returncode, 0)
        self.assertIn('demo-phases.png', broken.stdout)

    def test_invalid_release_version_cannot_create_artifacts(self):
        output = self.base / 'release'
        for value in ('v0.1.0', '0.1', '01.1.0', '../private', '0.1.0\n1.0.0'):
            with self.subTest(value=value):
                (self.source / 'VERSION').write_text(value)
                with self.assertRaises(ValueError):
                    build_release(self.source, output)
                self.assertFalse(output.exists())

    def test_release_destination_cannot_replace_source_or_symlink(self):
        for target in (self.source, self.source.parent, self.source / 'local/references/release'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                build_release(self.source, target)
        target = self.base / 'linked'
        target.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            build_release(self.source, target)


if __name__ == '__main__':
    unittest.main()
