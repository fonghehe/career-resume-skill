"""Exercise clone-shaped initialization and the actual Git staging boundary."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from bundle import repository_entries
from check_public_index import check
from init_profile import initialize
from package import write_tree
from validate import validate
from build_timeline import build
from update_profile import update


class LocalProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / 'clone'
        self.repo.mkdir()
        write_tree(repository_entries(ROOT), self.repo)
        self.git('init', '--initial-branch=main')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout

    def test_clone_initialization_build_and_git_add_keep_data_local(self):
        self.assertFalse((self.repo / 'local/references/profile.md').exists())
        self.assertFalse((self.repo / 'local/data/timeline.json').exists())
        created, skipped = initialize(self.repo)
        self.assertGreater(created, 0)
        self.assertEqual(skipped, 0)
        self.assertEqual(validate(self.repo)[0], [])
        build(self.repo)
        self.assertEqual(validate(self.repo)[0], [])
        (self.repo / 'local/references/profile.md').write_text('PRIVATE local person')
        attachment = self.repo / 'local/private/imports/resume.pdf'
        attachment.parent.mkdir(parents=True)
        attachment.write_bytes(b'private attachment')
        self.git('add', '.')
        tracked = set(self.git('ls-files').splitlines())
        self.assertEqual(tracked, set(repository_entries(self.repo)))
        self.assertNotIn('local/references/profile.md', tracked)
        self.assertNotIn('local/data/timeline.json', tracked)
        self.assertEqual(check(self.repo)[0], [])

    def test_repeat_initialization_preserves_existing_personal_files(self):
        initialize(self.repo)
        path = self.repo / 'local/references/profile.md'
        path.write_text('Private facts must survive upgrades')
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(initialize(self.repo)[0], 0)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_default_updates_and_pages_stay_in_local_workspace(self):
        initialize(self.repo)
        result = update(self.repo, {'profile': {'name': 'Local example'}}, apply=True)
        self.assertTrue(result['applied'])
        self.assertTrue((self.repo / 'local/output/updates' / result['id'] / 'before.json').is_file())
        self.assertTrue((self.repo / 'local/showcase/project-timeline.html').is_file())
        self.assertFalse((self.repo / 'output').exists())
        self.assertFalse((self.repo / 'showcase').exists())
        self.assertEqual(validate(self.repo)[0], [])

    def test_legacy_layout_is_read_without_moving_or_replacing_facts(self):
        data = self.repo / 'data/timeline.json'
        data.parent.mkdir()
        original = (self.repo / 'assets/starter/data/timeline.json').read_bytes()
        data.write_bytes(original)
        initialize(self.repo)
        self.assertTrue((self.repo / 'references/profile.md').is_file())
        self.assertFalse((self.repo / 'local/data').exists())
        page = build(self.repo)
        self.assertEqual(page, (self.repo / 'showcase/project-timeline.html').resolve())
        self.assertEqual(data.read_bytes(), original)
        self.assertEqual(validate(self.repo)[0], [])

    def test_ambiguous_old_and_new_profiles_require_explicit_selection(self):
        initialize(self.repo)
        old = self.repo / 'data/timeline.json'
        old.parent.mkdir()
        old.write_text('legacy contents must survive')
        with self.assertRaisesRegex(ValueError, 'Both local and legacy'):
            build(self.repo)
        self.assertEqual(old.read_text(), 'legacy contents must survive')

    def test_forced_personal_staging_is_detected_without_deleting_file(self):
        initialize(self.repo)
        self.git('add', '.')
        self.git('add', '-f', 'local/references/profile.md')
        self.assertTrue(any('local/references/profile.md' in error for error in check(self.repo)[0]))
        self.git('rm', '--cached', 'local/references/profile.md')
        self.assertTrue((self.repo / 'local/references/profile.md').exists())
        self.assertEqual(check(self.repo)[0], [])

    def test_guard_reads_staged_template_not_clean_working_copy(self):
        self.git('add', '.')
        path = self.repo / 'assets/starter/data/timeline.json'
        original = path.read_bytes()
        data = json.loads(original)
        data['profile']['name'] = 'Private person in staged template'
        path.write_text(json.dumps(data))
        self.git('add', 'assets/starter/data/timeline.json')
        path.write_bytes(original)
        self.assertTrue(any('personal information' in error for error in check(self.repo)[0]))

    def test_symlink_profile_is_refused_before_any_file_creation(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.repo / 'local').mkdir()
        (self.repo / 'local/data').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            initialize(self.repo)
        self.assertFalse((self.repo / 'local/references/profile.md').exists())

    def test_personal_memory_in_staged_starter_is_rejected(self):
        self.git('add', '.')
        path = self.repo / 'assets/starter/data/timeline.json'
        data = json.loads(path.read_text())
        data['memories'] = [{'id': 'M01', 'title': 'A private recollection', 'text': 'Private'}]
        path.write_text(json.dumps(data))
        self.git('add', 'assets/starter/data/timeline.json')
        self.assertTrue(any('records' in error for error in check(self.repo)[0]))


if __name__ == '__main__':
    unittest.main()
