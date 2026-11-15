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
sys.path.insert(0, str(ROOT / 'tools'))

from career_resume.doctor import diagnose
from career_resume.package import export
from release import build_release, read_version
from career_resume.validate import validate


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / 'installation'
        export(ROOT, self.source, directory=True)
        (self.source / 'VERSION').write_text('1.0.0\n', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_fresh_source_without_local_version_can_validate_and_package(self):
        (self.source / 'VERSION').unlink()
        self.assertIsNone(read_version(self.source))
        self.assertEqual(validate(self.source)[0], [])
        self.assertFalse(any(status == 'ERROR' for status, _ in diagnose(self.source)))
        result = subprocess.run([sys.executable, '-B', str(self.source / 'tools/release.py')],
                                input='2.1.0\n', capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(read_version(self.source), '2.1.0')
        public = self.base / 'public-without-local-version'
        export(self.source, public, directory=True)
        self.assertFalse((public / 'VERSION').exists())

    def test_workspace_cli_does_not_copy_or_replace_installation_profile(self):
        profile = self.source / 'local/references/profile.md'
        profile.write_text('PRIVATE-SHARED-INSTALLATION', encoding='utf-8')
        before = profile.read_bytes()
        workspace = self.base / 'my career'
        result = subprocess.run([sys.executable, str(self.source / 'scripts/career.py'), 'init',
                                 '--new', str(workspace)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(profile.read_bytes(), before)
        self.assertNotIn('PRIVATE-SHARED-INSTALLATION',
                         (workspace / 'local/references/profile.md').read_text())
        self.assertEqual(validate(workspace)[0], [])
        data = json.loads((workspace / 'local/data/timeline.json').read_text())
        self.assertEqual(data['projects'], [])
        own_profile = workspace / 'local/references/profile.md'
        own_profile.write_text('MY EXISTING CAREER', encoding='utf-8')
        repeat = subprocess.run([sys.executable, str(self.source / 'scripts/career.py'), 'init',
                                 '--new', str(workspace)], capture_output=True, text=True)
        self.assertNotEqual(repeat.returncode, 0)
        self.assertEqual(own_profile.read_text(), 'MY EXISTING CAREER')

    def test_doctor_does_not_read_personal_profile_or_require_optional_tools(self):
        (self.source / 'local/references/profile.md').write_bytes(b'\xff\xfePRIVATE')
        with patch('career_resume.doctor.probe', return_value=None):
            rows = diagnose(self.source)
            self.assertFalse(any(status == 'ERROR' for status, _ in rows), rows)
            docs = diagnose(self.source, docs=True)
            self.assertTrue(any(status == 'ERROR' for status, _ in docs))

    def test_runtime_has_one_template_copy_and_initializes_only_when_used(self):
        from career_resume.init_profile import initialize
        runtime = self.base / 'runtime'
        export(self.source, runtime, directory=True, runtime=True)
        template = runtime / 'assets/starter/references/profile.md'
        original = template.read_bytes()
        self.assertFalse((runtime / 'local').exists())
        self.assertEqual(validate(runtime)[0], [])
        initialize(runtime)
        profile = runtime / 'local/references/profile.md'
        self.assertEqual(profile.read_bytes(), original)
        profile.write_text('# 虚构既有资料\n\n本次只验证初始化保留原文。\n')
        (runtime / 'local/references/facts.md').unlink()
        self.assertTrue(validate(runtime)[0], 'A partial existing profile must not be silently skipped.')
        initialize(runtime)
        self.assertIn('虚构既有资料', profile.read_text())
        self.assertEqual(template.read_bytes(), original)
        self.assertEqual(validate(runtime)[0], [])

    def test_runtime_optional_guide_links_preserve_external_urls_and_offline_guides(self):
        from career_resume.package import link_runtime_guides
        stage = self.base / 'guide-fixture'
        stage.mkdir()
        entry = stage / 'SKILL.md'
        external = 'https://example.test/manual.md#keep'
        entry.write_text('[optional](docs/guide/using-skill.md#集成)\n'
                         '[offline](docs/guide/export-resume.md)\n'
                         f'[external]({external})\n', encoding='utf-8')
        offline = stage / 'docs/guide/export-resume.md'
        offline.parent.mkdir(parents=True)
        offline.write_text('# Offline export guide\n', encoding='utf-8')
        link_runtime_guides(stage, {'SKILL.md': entry, 'docs/guide/export-resume.md': offline})
        text = entry.read_text()
        self.assertIn('[offline](docs/guide/export-resume.md)', text)
        self.assertIn('[external](' + external + ')', text)
        self.assertIn('https://fonghehe.github.io/career-resume-skill/guide/using-skill.html#集成', text)

    def test_workspace_guide_is_initialized_and_personal_changes_are_preserved(self):
        from career_resume.init_profile import initialize
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
        demo = self.source / 'examples/resume-demo'
        self.assertEqual({p.name for p in demo.iterdir()},
                         {'request.md', 'career.md', 'resume.zh-CN.md', 'resume.en.md', 'match-report.md',
                          'period-review.md', 'jd-comparison.md'})
        self.assertTrue((self.source / 'examples/career-demo/data/timeline.json').is_file())
        self.assertFalse((self.source / 'examples/request.md').exists())
        self.assertEqual(validate(self.source)[0], [])

    def test_doctor_reports_incomplete_installation(self):
        (self.source / 'assets/templates/project-template.md').unlink()
        with patch('career_resume.doctor.probe', return_value=None):
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
            report = json.loads((output / 'PACKAGE-INFO.json').read_text(encoding='utf-8'))
            files = [entry for entry in bundle.infolist() if not entry.is_dir()]
            self.assertEqual(report['fileCount'], len(files))
            self.assertEqual(report['remainingFiles'], 200 - len(files))
            self.assertEqual(report['uncompressedBytes'], sum(entry.file_size for entry in files))
            self.assertEqual(report['zipBytes'], archive.stat().st_size)
            self.assertEqual(report['sha256'], digest)
            self.assertEqual(report['distribution'], 'runtime')
            self.assertNotIn('career-resume-skill/PACKAGE-INFO.json', bundle.namelist())
            names = [path.removeprefix('career-resume-skill/') for path in bundle.namelist()]
            for excluded in ('VERSION', '.gitignore', 'AGENTS.md', 'package.json',
                             'pnpm-lock.yaml', 'pnpm-workspace.yaml', 'tools/release.py',
                             'tools/check.py', 'tools/check_public_index.py'):
                self.assertNotIn(excluded, names)
            self.assertFalse(any(path.startswith(('.github/', 'tests/', 'docs/maintainers/',
                                                 'docs/.vitepress/')) for path in names))
            self.assertFalse(any(sentinel.encode() in bundle.read(path)
                                 for path in bundle.namelist()))
            data = json.loads(bundle.read('career-resume-skill/assets/starter/data/timeline.json'))
            self.assertEqual(data['career'], [])
        before = archive.read_bytes()
        with self.assertRaises(ValueError):
            build_release(self.source)
        self.assertEqual(archive.read_bytes(), before)

    def test_extracted_release_runs_without_repository_files(self):
        output = build_release(self.source, skillhub=True)
        with zipfile.ZipFile(next(output.glob('*.zip'))) as archive:
            archive.extractall(self.base / 'extracted')
        skill = self.base / 'extracted/career-resume-skill'
        self.assertFalse((skill / '.gitignore').exists())
        self.assertFalse((skill / 'assets/starter/gitignore.template').exists())
        self.assertFalse((skill / 'LICENSE').exists())
        self.assertFalse((skill / 'local').exists())
        original_profile = (skill / 'assets/starter/references/profile.md').read_bytes()
        # Every command uses modules from the actual unpacked bundle, not this checkout.
        workspace = self.base / 'private-workspace'
        installed = self.base / 'other-host'
        for args in (
            ('doctor',), ('init',), ('validate',), ('demo',),
            ('build',), ('web',), ('validate',),
            ('init', '--new', str(workspace)),
            ('install', '--skills-dir', str(installed)),
            ('package', '--version', '1.0.0', '--output', str(self.base / 'repacked.zip')),
        ):
            with self.subTest(command=args):
                result = subprocess.run([sys.executable, '-B', str(skill / 'scripts/career.py'), args[0],
                                         *args[1:]], cwd=self.base, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((skill / 'local/output/demo/showcase/project-timeline.html').is_file())
        self.assertTrue((skill / '.gitignore').is_file())
        self.assertEqual((skill / '.gitignore').read_bytes(),
                         (skill / 'assets/starter/gitignore.txt').read_bytes())
        self.assertEqual((skill / 'local/references/profile.md').read_bytes(), original_profile)
        self.assertEqual(validate(workspace)[0], [])
        self.assertEqual(validate(installed / 'career-resume-skill')[0], [])
        self.assertTrue((workspace / '.gitignore').is_file())
        subprocess.run(['git', 'init', '-q', str(workspace)], check=True)
        ignored = subprocess.run(['git', '-C', str(workspace), 'check-ignore', 'local/references/profile.md'],
                                 capture_output=True, text=True)
        self.assertEqual(ignored.returncode, 0, ignored.stderr)
        (skill / 'examples/career-demo/references/attachments/demo-phases.md').unlink()
        broken = subprocess.run([sys.executable, '-B', str(skill / 'scripts/career.py'), 'doctor'],
                                capture_output=True, text=True)
        self.assertNotEqual(broken.returncode, 0)
        self.assertIn('demo-phases.md', broken.stderr)

    def test_skillhub_release_includes_market_metadata_without_changing_source_entry(self):
        source_entry = self.source / 'SKILL.md'
        original = source_entry.read_bytes()
        output = build_release(self.source, skillhub=True)
        with zipfile.ZipFile(next(output.glob('*.zip'))) as archive:
            entry = archive.read('career-resume-skill/SKILL.md').decode()
        front = entry.split('---', 2)[1]
        fields = dict(line.split(':', 1) for line in front.strip().splitlines())
        self.assertEqual(fields['slug'].strip(), 'career-resume-skill')
        self.assertEqual(fields['displayName'].strip(), 'career-resume-skill')
        self.assertEqual(fields['version'].strip(), read_version(self.source))
        self.assertEqual(fields['license'].strip(), 'MIT')
        self.assertEqual(source_entry.read_bytes(), original)

    def test_invalid_release_version_cannot_create_artifacts(self):
        output = self.base / 'release'
        for value in ('v0.1.0', '0.1', '01.1.0', '../private', '0.1.0\n1.0.0'):
            with self.subTest(value=value):
                (self.source / 'VERSION').write_text(value)
                with self.assertRaises(ValueError):
                    build_release(self.source, output)
                self.assertFalse(output.exists())

    def test_release_cli_asks_for_each_full_version_and_builds_matching_artifacts(self):
        for expected in ('1.4.10', '1.5.0', '2.0.0'):
            with self.subTest(version=expected):
                (self.source / 'VERSION').write_text('1.4.9\n')
                result = subprocess.run([sys.executable, '-B', str(self.source / 'tools/release.py'),
                                         '--skillhub'], input=expected + '\n', capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(read_version(self.source), expected)
                self.assertIn('请输入本次打包版本号', result.stdout)
                output = self.source / 'local/dist/skillhub' / expected
                archive = output / f'career-resume-skill-{expected}.zip'
                digest, name = (output / 'SHA256SUMS').read_text().split()
                self.assertEqual(name, archive.name)
                self.assertEqual(digest, hashlib.sha256(archive.read_bytes()).hexdigest())
                with zipfile.ZipFile(archive) as bundle:
                    self.assertNotIn('career-resume-skill/VERSION', bundle.namelist())
                    front = bundle.read('career-resume-skill/SKILL.md').decode().split('---', 2)[1]
                    fields = dict(line.split(':', 1) for line in front.strip().splitlines())
                    self.assertEqual(fields['version'].strip(), expected)

    def test_release_cli_without_a_valid_choice_preserves_version_and_writes_nothing(self):
        version = self.source / 'VERSION'
        original = version.read_bytes()
        for answer in ('', '\n', 'v1.1.0\n', '01.1.0\n', '../escape\n'):
            with self.subTest(answer=answer):
                result = subprocess.run([sys.executable, '-B', str(self.source / 'tools/release.py')],
                                        input=answer, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(version.read_bytes(), original)
                self.assertFalse((self.source / 'local/dist').exists())

    def test_release_cli_explicit_version_supports_automation(self):
        result = subprocess.run([sys.executable, '-B', str(self.source / 'tools/release.py'),
                                 '--version', '7.2.0'], input='', capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('请输入', result.stdout)
        self.assertEqual(read_version(self.source), '7.2.0')
        self.assertTrue((self.source / 'local/dist/releases/7.2.0/career-resume-skill-7.2.0.zip').is_file())

    def test_failed_selected_version_preserves_version_and_existing_release(self):
        version = self.source / 'VERSION'
        version.write_text('1.4.9\n')
        target = self.base / 'occupied'
        target.mkdir()
        sentinel = target / 'existing.zip'
        sentinel.write_bytes(b'preserve this release')
        with self.assertRaises(ValueError):
            build_release(self.source, target, version='9.0.0')
        self.assertEqual(version.read_text(), '1.4.9\n')
        self.assertEqual(sentinel.read_bytes(), b'preserve this release')

        (self.source / 'assets/templates/project-template.md').unlink()
        missing = self.base / 'failed-release'
        with self.assertRaises(ValueError):
            build_release(self.source, missing, version='9.0.0')
        self.assertFalse(missing.exists())
        self.assertEqual(version.read_text(), '1.4.9\n')

    def test_failed_version_write_does_not_leave_a_release(self):
        version = self.source / 'VERSION'
        original = version.read_bytes()
        target = self.base / 'write-failed-release'
        with patch('release.tempfile.NamedTemporaryFile', side_effect=PermissionError('read-only source')):
            with self.assertRaises(PermissionError):
                build_release(self.source, target, version='9.0.0')
        self.assertEqual(version.read_bytes(), original)
        self.assertFalse(target.exists())

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
