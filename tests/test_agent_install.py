"""Client layout, clean exports and preservation of existing installations."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

PRIVATE_MARKER = '-'.join(('PRIVATE', 'INSTALL', 'SENTINEL'))
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from install_skill import destination, install
from package import export
from validate import validate


class AgentInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / 'source'
        export(ROOT, self.source, directory=True)
        (self.source / 'local/references/profile.md').write_text(PRIVATE_MARKER)

    def tearDown(self):
        self.temp.cleanup()

    def test_each_project_install_is_complete_and_excludes_private_data(self):
        for agent, folder in [('codex', '.agents'), ('claude', '.claude'), ('trae', '.trae')]:
            with self.subTest(agent=agent):
                target, _ = install(self.source, agent, project=self.source)
                self.assertEqual(target, self.source / folder / 'skills/career-resume-skill')
                self.assertEqual(validate(target)[0], [])
                self.assertTrue((target / 'assets/templates/agent-entry-template.md').is_file())
                self.assertNotIn(PRIVATE_MARKER,
                                 (target / 'local/references/profile.md').read_text())
                self.assertTrue((target / 'scripts/init_profile.py').is_file())
                self.assertFalse((target / folder).exists())
                self.assertFalse((target / '.git').exists())
                self.assertEqual(json.loads((target / 'local/data/timeline.json').read_text())['projects'], [])
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        subprocess.run(['git', '-C', str(self.source), 'add', '.'], check=True)
        tracked = subprocess.run(['git', '-C', str(self.source), 'ls-files'],
                                 capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertFalse(any(path.startswith(('.agents/', '.claude/', '.trae/')) for path in tracked))

    def test_user_defaults_and_explicit_trae_global_path(self):
        with patch('install_skill.Path.home', return_value=self.base):
            self.assertEqual(destination('codex')[0], self.base / '.agents/skills/career-resume-skill')
            self.assertEqual(destination('claude')[0], self.base / '.claude/skills/career-resume-skill')
        with self.assertRaises(ValueError):
            destination('trae')
        target, _ = install(self.source, 'trae', skills_dir=self.base / '.trae-cn/skills')
        self.assertTrue((target / 'SKILL.md').is_file())

    def test_workbuddy_zip_is_public_complete_and_does_not_replace_existing_output(self):
        output = self.base / 'import.zip'
        install(self.source, 'workbuddy', output=output)
        before = output.read_bytes()
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
            self.assertIn('career-resume-skill/SKILL.md', names)
            self.assertIn('career-resume-skill/assets/templates/resume-template.md', names)
            self.assertFalse(any(PRIVATE_MARKER.encode() in archive.read(name) for name in names))
        with self.assertRaises(ValueError):
            install(self.source, 'workbuddy', output=output)
        self.assertEqual(output.read_bytes(), before)

    def test_dry_run_cli_creates_nothing_and_existing_installation_is_preserved(self):
        workspace = self.base / 'my career'
        workspace.mkdir()
        result = subprocess.run([sys.executable, '-B', str(self.source / 'scripts/install_skill.py'),
                                 '--agent', 'claude', '--project', str(workspace), '--dry-run'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Planned:', result.stdout)
        self.assertEqual(list(workspace.iterdir()), [])
        target, _ = install(self.source, 'claude', project=workspace)
        (target / 'SKILL.md').write_text('EXISTING-CUSTOM-SKILL')
        with self.assertRaises(ValueError):
            install(self.source, 'claude', project=workspace)
        self.assertEqual((target / 'SKILL.md').read_text(), 'EXISTING-CUSTOM-SKILL')
        self.assertEqual((self.source / 'local/references/profile.md').read_text(), PRIVATE_MARKER)

    def test_symlink_destination_and_conflicting_flags_are_rejected_before_writes(self):
        linked = self.base / 'linked'
        linked.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            install(self.source, 'codex', project=linked)
        for kwargs in ({'agent': 'claude', 'project': self.source, 'skills_dir': self.base},
                       {'agent': 'workbuddy', 'project': self.source},
                       {'agent': 'codex', 'output': self.base / 'a.zip'},
                       {'agent': 'trae', 'project': self.base / 'missing'},
                       {'agent': 'workbuddy', 'output': self.source}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                install(self.source, **kwargs)

    def test_arbitrary_host_directory_needs_no_registered_agent_name(self):
        for agent in (None, 'new-host-not-in-registry'):
            with self.subTest(agent=agent):
                host_dir = self.base / (agent or 'generic') / 'skills'
                target, _ = install(self.source, agent, skills_dir=host_dir)
                self.assertEqual(target, host_dir / 'career-resume-skill')
                self.assertEqual(validate(target)[0], [])
                self.assertNotIn(PRIVATE_MARKER, (target / 'local/references/profile.md').read_text())
        with self.assertRaises(ValueError):
            install(self.source, 'new-host-not-in-registry', project=self.source)

    def test_shared_project_directory_and_claude_code_alias(self):
        target, _ = install(self.source, project=self.source)
        self.assertEqual(target, self.source / '.agents/skills/career-resume-skill')
        other, _ = install(self.source, 'claude-code', project=self.source)
        self.assertEqual(other, self.source / '.claude/skills/career-resume-skill')
        self.assertEqual(destination('universal', project=self.source)[0], target)
        with self.assertRaises(ValueError):
            destination('universal')

    def test_generic_zip_and_cli_without_agent_include_all_resources(self):
        output = self.base / 'generic.zip'
        result = subprocess.run([sys.executable, '-B', str(self.source / 'scripts/install_skill.py'),
                                 '--output', str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(output) as archive:
            self.assertIn('career-resume-skill/SKILL.md', archive.namelist())
            self.assertFalse(any(PRIVATE_MARKER.encode() in archive.read(name) for name in archive.namelist()))
        result = subprocess.run([sys.executable, '-B', str(self.source / 'scripts/install_skill.py'),
                                 '--skills-dir', str(self.base / 'custom skills')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.base / 'custom skills/career-resume-skill/SKILL.md').is_file())


if __name__ == '__main__':
    unittest.main()
