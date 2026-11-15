"""Observable recovery guidance and isolated checks for installed runtime bundles."""

from pathlib import Path
from contextlib import redirect_stderr
import io
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from career_resume.doctor import diagnose
from career_resume.init_profile import initialize
from career_resume.package import export
from career_resume.cli_support import CliError, fail


class CliFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / 'source'
        export(ROOT, self.source, directory=True)
        (self.source / 'VERSION').write_text('1.0.0\n', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, script, *args, root=None):
        if script == 'release.py':
            return subprocess.run([sys.executable, '-B', str((root or self.source) / 'tools/release.py'),
                                   *map(str, args)], cwd=self.base, capture_output=True, text=True)
        return subprocess.run([sys.executable, '-B', str((root or self.source) / 'scripts/career.py'), script,
                               *map(str, args)], cwd=self.base, capture_output=True, text=True)

    def test_existing_destinations_get_actionable_errors_and_keep_existing_files(self):
        occupied = self.base / 'occupied'
        occupied.mkdir()
        sentinel = occupied / 'preserve.md'
        sentinel.write_text('Existing fictional notes')
        host = self.base / 'host'
        (host / 'career-resume-skill').mkdir(parents=True)
        archive = self.base / 'existing.zip'
        archive.write_bytes(b'preserve original export')
        version = (self.source / 'VERSION').read_bytes()
        for script, args in (
            ('init', ('--new', occupied)),
            ('demo', ('--output', occupied)),
            ('install', ('--skills-dir', host)),
            ('package', ('--version', '1.0.0', '--output', archive)),
            ('release.py', ('--output-dir', occupied, '--version', '1.1.0')),
        ):
            with self.subTest(script=script):
                result = self.run_cli(script, *args)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('ERROR:', result.stderr)
                self.assertIn('CODE: 1004', result.stderr)
                self.assertIn('NEXT:', result.stderr)
                self.assertIn('新目标', result.stderr)
                self.assertIn(str(self.source / 'docs/guide/troubleshooting.md'), result.stderr)
                self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(sentinel.read_text(), 'Existing fictional notes')
        self.assertEqual(archive.read_bytes(), b'preserve original export')
        self.assertEqual((self.source / 'VERSION').read_bytes(), version)

    def test_incomplete_public_resources_explain_how_to_recover(self):
        (self.source / 'assets/templates/project-template.md').unlink()
        for script, args in (('install', ('--version', '1.0.0', '--output', self.base / 'new.zip')),
                             ('doctor', ())):
            with self.subTest(script=script):
                result = self.run_cli(script, *args)
                self.assertEqual(result.returncode, 1)
                self.assertIn('project-template.md', result.stderr)
                self.assertIn('CODE: 1005', result.stderr)
                self.assertIn('完整', result.stderr)
                self.assertIn('NEXT:', result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_validate_suggests_initialization_for_missing_private_starter(self):
        (self.source / 'local/references/profile.md').unlink()
        result = self.run_cli('validate')
        self.assertEqual(result.returncode, 1)
        self.assertIn('career.py init', result.stderr)
        self.assertIn('CODE: 1006', result.stderr)
        self.assertIn('NEXT:', result.stderr)

    def test_invalid_utf8_project_card_reports_failure_without_traceback(self):
        card = self.source / 'local/references/projects/broken.md'
        card.parent.mkdir()
        card.write_bytes(b'\xff\xfeFICTIONAL')
        result = self.run_cli('validate')
        self.assertEqual(result.returncode, 1)
        self.assertIn('broken.md', result.stderr)
        self.assertIn('UTF-8', result.stderr)
        self.assertIn('CODE: 1002', result.stderr)
        self.assertIn('HELP:', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(card.read_bytes(), b'\xff\xfeFICTIONAL')

    def test_diagnostic_codes_are_independent_of_exit_status(self):
        for error, code in ((PermissionError('denied'), 1001),
                            (ValueError('Refusing a symlink output'), 1003),
                            (CliError(1007, 'Git read timed out'), 1007),
                            (ValueError('invalid field'), 1000)):
            with self.subTest(code=code), redirect_stderr(io.StringIO()) as output:
                self.assertEqual(fail(error), 1)
                self.assertIn('CODE: ' + str(code), output.getvalue())
                self.assertIn('NEXT:', output.getvalue())

    def test_runtime_smoke_uses_blank_temporary_data_and_preserves_current_profile(self):
        runtime = self.base / 'runtime'
        export(self.source, runtime, directory=True, runtime=True)
        from career_resume.init_profile import initialize
        initialize(runtime)
        profile = runtime / 'local/references/profile.md'
        timeline = runtime / 'local/data/timeline.json'
        profile.write_bytes(b'\xff\xfeDO-NOT-READ-PERSONAL-TEXT')
        timeline.write_bytes(b'NOT-VALID-PERSONAL-JSON')
        before = {path.relative_to(runtime): path.read_bytes() for path in runtime.rglob('*') if path.is_file()}
        result = self.run_cli('doctor', '--smoke', root=runtime)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Runtime self-check passed', result.stdout)
        for script in ('init', 'validate', 'build', 'web', 'demo'):
            self.assertIn(script, result.stdout)
        after = {path.relative_to(runtime): path.read_bytes() for path in runtime.rglob('*') if path.is_file()}
        self.assertEqual(before, after)

    def test_runtime_docs_diagnostic_requests_source_instead_of_optional_dependencies(self):
        runtime = self.base / 'runtime'
        export(self.source, runtime, directory=True, runtime=True)
        with patch('career_resume.doctor.probe', return_value=None):
            errors = [message for status, message in diagnose(runtime, docs=True) if status == 'ERROR']
        self.assertEqual(len(errors), 1, errors)
        self.assertIn('source', errors[0])

    def test_docs_diagnostic_follows_node_and_pnpm_pins(self):
        manifest = json.loads((self.source / 'package.json').read_text())
        pinned = manifest['packageManager'].removeprefix('pnpm@')
        for node, pnpm, expected in (('v24.0.0', pinned, True),
                                     ('v22.0.0', pinned, False),
                                     ('v24.0.0', '10.0.0', False)):
            with self.subTest(node=node, pnpm=pnpm):
                probes = {'node': node, 'pnpm': pnpm, 'git': 'git version 2.0'}
                with patch('career_resume.doctor.probe', side_effect=probes.get):
                    rows = diagnose(self.source, docs=True)
                errors = [message for status, message in rows if status == 'ERROR']
                self.assertEqual(not errors, expected, rows)

    def test_doctor_points_out_missing_ignore_rules_without_reading_private_contents(self):
        runtime = self.base / 'runtime'
        export(self.source, runtime, directory=True, runtime=True)
        with patch('career_resume.doctor.probe', return_value=None):
            rows = diagnose(runtime)
        self.assertTrue(any(status == 'INFO' and 'ignore' in message and 'career.py init' in message
                            for status, message in rows), rows)
        initialize(runtime)
        with patch('career_resume.doctor.probe', return_value=None):
            rows = diagnose(runtime)
        self.assertFalse(any(status == 'INFO' and 'ignore' in message for status, message in rows), rows)

    def test_daily_tools_use_the_same_failure_format_without_changing_sources(self):
        profile = self.source / 'local/references/profile.md'
        original = profile.read_bytes()
        invalid_delta = self.base / 'invalid.json'
        invalid_delta.write_text('not JSON')
        for script, args in (
            ('build', ('--output', profile)),
            ('share', ('--workspace', self.source, '--project', 'P99')),
            ('git', ('--repo', self.base / 'not-a-repo', '--author-email', 'demo@example.test')),
            ('update', ('--workspace', self.source, '--delta', invalid_delta)),
            ('web', ('--output', profile)),
        ):
            with self.subTest(script=script):
                result = self.run_cli(script, *args)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('ERROR:', result.stderr)
                self.assertIn('NEXT:', result.stderr)
                self.assertIn('HELP:', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(profile.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
