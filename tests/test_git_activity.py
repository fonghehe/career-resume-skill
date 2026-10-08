"""Verify identity selection, date semantics, local scope and non-destructive reports."""

import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from import_git_activity import collect, collect_folder, write_report
from career_data import summarize_repositories
from build_timeline import validate_data


class GitActivityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repository'
        self.repo.mkdir()
        self.command('init', '--initial-branch=main')
        self.command('config', 'user.name', 'Synthetic contributor')
        self.command('config', 'user.email', 'contributor@example.test')
        self.command('config', 'commit.gpgsign', 'false')

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *args, env=None):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, env=env).stdout.strip()

    def commit(self, email, authored, committed, subject):
        env = dict(os.environ)
        env.update(GIT_AUTHOR_NAME='Synthetic contributor', GIT_AUTHOR_EMAIL=email,
                   GIT_COMMITTER_NAME='Synthetic committer',
                   GIT_COMMITTER_EMAIL='committer@example.test',
                   GIT_AUTHOR_DATE=authored, GIT_COMMITTER_DATE=committed)
        self.command('commit', '--allow-empty', '-m', subject, env=env)
        return self.command('rev-parse', 'HEAD')

    def test_exact_identity_unique_hashes_and_distinct_dates(self):
        self.commit('alice@example.test', '2025-02-01T10:00:00+08:00',
                    '2025-03-01T10:00:00+08:00', 'later author date')
        self.commit('other@example.test', '2025-01-15T10:00:00+08:00',
                    '2025-03-02T10:00:00+08:00', 'other contributor')
        sha = self.commit('alice@example.test', '2025-01-01T10:00:00+08:00',
                          '2025-03-03T10:00:00+08:00', '早期活动 <script>')
        self.command('branch', 'same-history')
        before = self.command('status', '--porcelain')
        report = collect(self.repo, ['ALICE@example.test'], 'P42')
        self.assertEqual(len(report['records']), 2)
        self.assertEqual(report['records'][0]['sha'], sha)
        self.assertEqual(report['repository']['count'], 2)
        self.assertEqual(report['repository']['start'], '2025-01-01T10:00:00+08:00')
        self.assertEqual(report['records'][0]['committerDate'], '2025-03-03T10:00:00+08:00')
        self.assertEqual(report['mappingStatus'], 'pending')
        self.assertEqual(report['timelineEvents'][0]['projectId'], 'P42')
        self.assertEqual(report['timelineEvents'][0]['sha'], sha)
        self.assertEqual(self.command('status', '--porcelain'), before)
        self.assertEqual(self.command('rev-parse', 'HEAD'), sha)

    def test_historical_email_and_no_match_do_not_invent_activity(self):
        self.commit('old@example.test', '2025-01-01T10:00:00+08:00',
                    '2025-01-01T10:00:00+08:00', 'historical identity')
        self.commit('new@example.test', '2025-02-01T10:00:00+08:00',
                    '2025-02-01T10:00:00+08:00', 'new identity')
        self.assertEqual(len(collect(self.repo, ['old@example.test', 'new@example.test'])['records']), 2)
        report = collect(self.repo, ['missing@example.test'])
        self.assertEqual(report['records'], [])
        self.assertIsNone(report['repository'])

    def test_utc_git_dates_survive_collection_summary_and_timeline_validation(self):
        first = self.commit('alice@example.test', '2025-02-01T00:00:00+00:00',
                            '2025-02-03T00:00:00+00:00', 'UTC activity')
        second = self.commit('alice@example.test', '2025-01-31T20:00:00-05:00',
                             '2025-02-04T00:00:00+00:00', 'Offset activity')
        self.command('tag', 'utc-snapshot')
        report = collect(self.repo, ['alice@example.test'], 'P01')
        self.assertEqual([r['sha'] for r in report['records']], [first, second])
        self.assertEqual(report['records'][0]['authorDate'], '2025-02-01T00:00:00Z')
        self.assertEqual(report['records'][0]['committerDate'], '2025-02-03T00:00:00Z')
        self.assertEqual(report['records'][1]['authorDate'], '2025-01-31T20:00:00-05:00')
        self.assertEqual(report['repositoryEvidence']['tags'][0]['date'], '2025-02-04T00:00:00Z')
        summaries = summarize_repositories(report['timelineEvents'], [report['repository']])
        self.assertEqual(summaries[0]['start'], '2025-02-01T00:00:00Z')
        self.assertEqual(summaries[0]['end'], '2025-01-31T20:00:00-05:00')
        self.assertEqual(summaries[0]['activity']['monthly'], {'2025-01': 1, '2025-02': 1})
        data = json.loads((Path(__file__).resolve().parents[1] /
                           'assets/examples/career-demo/data/timeline.json').read_text())
        data['repositories'] = summaries
        data['gitEvents'] = report['timelineEvents']
        validate_data(data)
        for date in ('2025-02-30T00:00:00Z', '2025-02-01T00:00:00'):
            with self.subTest(date=date):
                invalid = json.loads(json.dumps(data))
                invalid['gitEvents'][0]['committerDate'] = date
                with self.assertRaises(ValueError):
                    validate_data(invalid)

    def test_snapshot_is_preserved_and_existing_file_cannot_be_replaced(self):
        self.commit('alice@example.test', '2025-01-01T10:00:00+08:00',
                    '2025-01-01T10:00:00+08:00', 'activity')
        report = collect(self.repo, ['alice@example.test'])
        output = self.base / 'private/report.json'
        write_report(report, output)
        self.assertEqual(json.loads(output.read_text()), report)
        before = output.read_bytes()
        with self.assertRaises(FileExistsError):
            write_report(report, output)
        self.assertEqual(output.read_bytes(), before)

    def test_empty_repo_and_required_identity(self):
        self.assertEqual(collect(self.repo, ['alice@example.test'])['records'], [])
        with self.assertRaises(ValueError):
            collect(self.repo, [])
        with self.assertRaises(ValueError):
            collect(self.repo, ['alice@example.test'], 'not-a-project')

    def test_folder_keeps_same_named_repositories_separate_and_skips_links(self):
        self.commit('alice@example.test', '2025-01-01T10:00:00+08:00',
                    '2025-01-02T10:00:00+08:00', 'a memory cue')
        nested = self.base / 'team/repository'
        shutil.copytree(self.repo, nested)
        (self.base / 'linked').symlink_to(self.repo, target_is_directory=True)
        dependencies = self.base / 'node_modules/copied'
        shutil.copytree(self.repo, dependencies)
        before = self.command('status', '--porcelain')
        report = collect_folder(self.base, ['alice@example.test'])
        self.assertEqual(len(report['reports']), 2)
        names = {r['repository']['name'] for r in report['reports']}
        self.assertEqual(names, {'repository', 'team/repository'})
        events = [e for r in report['reports'] for e in r['timelineEvents']]
        self.assertEqual(len({e['id'] for e in events}), 2)
        self.assertEqual({e['repository'] for e in events}, names)
        self.assertTrue(all(not e['projectId'] for e in events))
        self.assertEqual(self.command('status', '--porcelain'), before)

    def test_folder_with_no_repos_or_no_identity_does_not_invent_history(self):
        empty = self.base / 'empty'
        empty.mkdir()
        self.assertEqual(collect_folder(empty, ['alice@example.test'])['reports'], [])
        with self.assertRaises(ValueError):
            collect_folder(empty, [])


if __name__ == '__main__':
    unittest.main()
