"""Behavioral tests for factual updates, mapping, evidence, assets and sharing."""
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_timeline import build, validate_data, embedded_attachment
from create_demo import create
from update_profile import merge, update, git_delta
from export_share import export, share_data
from import_git_activity import collect


class EnhancementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve() / 'demo'
        create(ROOT, self.root)
        self.data = json.loads((self.root / 'data/timeline.json').read_text())

    def tearDown(self):
        self.temp.cleanup()

    def test_confirmed_fields_survive_and_sources_accumulate(self):
        delta = {'projects': [{'id':'P01', 'milestones':[{'title':'unverified replacement'}],
                              'sources':[{'field':'summary','status':'git','label':'New evidence'}]}]}
        result, report = merge(self.data, delta)
        self.assertEqual(result['projects'][0]['milestones'], self.data['projects'][0]['milestones'])
        self.assertEqual(len(report['conflicts']), 1)
        self.assertEqual(len(result['projects'][0]['sources']), 3)
        result, report = merge(self.data, delta, ['projects/P01.milestones'])
        self.assertEqual(result['projects'][0]['milestones'][0]['title'], 'unverified replacement')
        self.assertFalse(report['conflicts'])

    def test_new_stages_append_without_rewriting_confirmed_history(self):
        stages=copy.deepcopy(self.data['projects'][0]['milestones'])
        stages.append({'date':'2025.01','title':'New pending stage','status':'pending'})
        result,report=merge(self.data,{'projects':[{'id':'P01','milestones':stages}]})
        self.assertFalse(report['conflicts'])
        self.assertEqual(result['projects'][0]['milestones'][:-1],self.data['projects'][0]['milestones'])
        stages[0]['title']='Rewrite confirmed stage'
        _,report=merge(self.data,{'projects':[{'id':'P01','milestones':stages}]})
        self.assertEqual(len(report['conflicts']),1)

    def test_duplicate_sha_and_immutable_original_evidence(self):
        event = dict(self.data['gitEvents'][0], id='a different ID', subject='fabricated subject')
        result, report = merge(self.data, {'gitEvents':[event]})
        self.assertEqual(len(result['gitEvents']), 14)
        self.assertEqual(result['gitEvents'][0]['subject'], self.data['gitEvents'][0]['subject'])
        self.assertEqual(report['conflicts'][0]['field'].split('.')[-1], 'subject')
        result,report=merge(self.data,{'gitEvents':[event]},[f"gitEvents/{self.data['gitEvents'][0]['id']}.subject"])
        self.assertEqual(result['gitEvents'][0]['subject'],self.data['gitEvents'][0]['subject'])
        self.assertEqual(len(report['conflicts']),1)

    def test_preview_apply_noop_and_guarded_undo(self):
        original = (self.root / 'data/timeline.json').read_bytes()
        delta = {'projects':[{'id':'P01','summary':'A factual correction'}]}
        report = update(self.root, delta)
        self.assertFalse('id' in report)
        self.assertEqual((self.root/'data/timeline.json').read_bytes(),original)
        applied = update(self.root, delta, apply=True)
        self.assertTrue(applied['applied'])
        self.assertIn('A factual correction', build(self.root).read_text())
        self.assertFalse(update(self.root, delta, apply=True)['applied'])
        update(self.root, undo=applied['id'], apply=True)
        self.assertEqual((self.root/'data/timeline.json').read_bytes(),original)
        old = update(self.root, delta, apply=True)
        update(self.root, {'meta':{'subtitle':'Later update'}}, apply=True)
        with self.assertRaises(ValueError): update(self.root, undo=old['id'], apply=True)

    def test_failed_build_restores_data_and_records_unapplied_history(self):
        before=(self.root/'data/timeline.json').read_bytes()
        with patch('update_profile.build', side_effect=OSError('simulated write failure')):
            with self.assertRaises(OSError):
                update(self.root,{'meta':{'subtitle':'new text'}},apply=True)
        self.assertEqual((self.root/'data/timeline.json').read_bytes(),before)
        records=list((self.root/'output/updates').glob('*/report.json'))
        self.assertEqual(len(records),1)
        self.assertFalse(json.loads(records[0].read_text())['applied'])
        with self.assertRaises(ValueError):update(self.root,undo=records[0].parent.name,apply=True)

    def test_invalid_source_fails_before_mutating_profile(self):
        before = (self.root/'data/timeline.json').read_bytes()
        with self.assertRaises(ValueError):
            update(self.root, {'projects':[{'id':'P01','sources':[{'field':'summary','label':'missing','status':'git','path':'references/missing.md'}]}]}, apply=True)
        self.assertEqual((self.root/'data/timeline.json').read_bytes(),before)
        self.assertFalse((self.root/'data/.update.lock').exists())

    def test_existing_lock_and_symlink_history_are_refused(self):
        lock = self.root/'data/.update.lock';lock.write_text('busy')
        with self.assertRaises(FileExistsError): update(self.root, {})
        lock.unlink()
        external=Path(self.temp.name)/'outside';external.mkdir()
        (self.root/'output').mkdir();(self.root/'output/updates').symlink_to(external,target_is_directory=True)
        with self.assertRaises(ValueError): update(self.root,{})
        self.assertEqual(list(external.iterdir()),[])

    def test_unmapped_report_does_not_clear_known_mapping(self):
        report={'repository':dict(self.data['repositories'][0],projectId='',projectIds=[],projectCounts={}),
                'mappingStatus':'pending','timelineEvents':[dict(self.data['gitEvents'][0],projectId='',projectIds=[])]}
        delta=git_delta(self.root,report)
        self.assertEqual(delta['gitEvents'][0]['projectId'],'P01')
        result,_=merge(self.data,delta)
        self.assertEqual(result['repositories'][0]['projectCounts']['P01'],5)

    def test_multirepo_project_counts_do_not_inflate_global_commits(self):
        result,_=merge(self.data, {})
        self.assertEqual(sum(r['count'] for r in result['repositories']),14)
        self.assertEqual(sum(r.get('projectCounts',{}).get('P03',0) for r in result['repositories']),5)
        self.assertEqual(sum(sum(r['projectCounts'].values()) for r in result['repositories']),15)

    def test_sources_and_attachments_are_offline_and_safe(self):
        html=build(self.root).read_text()
        details=json.loads(re.search(r'<script id="project-details" type="application/json">(.*?)</script>',html,re.S).group(1))
        self.assertTrue(details['P03']['attachments'][0]['url'].startswith('data:image/png;base64,'))
        self.assertIn('虚构演示来源', html)
        for path in ('../outside.png','/tmp/outside.png'):
            with self.assertRaises(ValueError): embedded_attachment(self.root,{'path':path,'label':'invalid'})
        asset=self.root/'references/attachments/fake.png';asset.write_text('<script>bad</script>')
        with self.assertRaises(ValueError): embedded_attachment(self.root,{'path':asset.relative_to(self.root).as_posix(),'label':'fake'})
        target=self.root/'references/attachments/link.png';target.symlink_to(self.root/'references/attachments/demo-phases.png')
        with self.assertRaises(ValueError): embedded_attachment(self.root,{'path':target.relative_to(self.root).as_posix(),'label':'link'})

    def test_extension_schema_rejects_unbounded_counts_and_unknown_ids(self):
        for change in (lambda d:d['repositories'][0].update(projectCounts={'P01':999}),
                       lambda d:d['gitEvents'][0].update(projectIds=['P99']),
                       lambda d:d['projects'][0].update(careerIds=['E99']),
                       lambda d:d['repositories'][0].update(activity={'monthly':{'2024-13':5}})):
            data=copy.deepcopy(self.data);change(data)
            with self.assertRaises(ValueError): validate_data(data)

    def test_share_allowlist_removes_private_data_and_preserves_original(self):
        self.data['privateToken']='PRIVATE_TOKEN_SENTINEL'
        self.data['projects'][0]['sources'][0]['excerpt']='PRIVATE_SOURCE_SENTINEL'
        self.data['repositories'][0]['path']='/Users/PRIVATE_PATH_SENTINEL'
        self.data['gitEvents'][0]['authorEmail']='PRIVATE_EMAIL_SENTINEL@example.test'
        path=self.root/'data/timeline.json';path.write_text(json.dumps(self.data))
        before=path.read_bytes()
        target=export(self.root,['P01'])
        html=target.read_text()
        for text in ('PRIVATE_', 'knowledge-portal', self.data['gitEvents'][0]['sha'], 'sample-portal.md','示例甲公司（虚构）'):
            self.assertNotIn(text,html)
        self.assertNotIn('data:image/png',html)
        self.assertEqual(path.read_bytes(),before)
        with self.assertRaises(FileExistsError): export(self.root,['P01'],target)
        with self.assertRaises(ValueError): export(self.root,['P01'],self.root/'data/timeline.json')

    def test_share_selected_counts_and_optional_attachments(self):
        safe=share_data(self.data,['P03'])
        self.assertEqual(sum(r['count'] for r in safe['repositories']),5)
        self.assertEqual(len(safe['projects']),1)
        with_media=export(self.root,['P03'],include_attachments=True)
        self.assertIn('data:image/png;base64,',with_media.read_text())
        self.assertNotIn('sample-notebook.md',with_media.read_text())

    def test_partial_shared_repository_subset_is_not_guessed(self):
        data=copy.deepcopy(self.data);data['gitEvents']=[]
        data['repositories'][0]['projectIds']=['P01','P02','P03']
        data['repositories'][0]['projectCounts']={'P01':5,'P02':2,'P03':1}
        with self.assertRaises(ValueError): share_data(data,['P02','P03'])

    def test_real_git_directory_mapping_tags_and_changed_files(self):
        repo=Path(self.temp.name)/'mono';repo.mkdir()
        def git(*args):
            env = {**os.environ, 'GIT_AUTHOR_DATE': '2025-01-01T00:00:00+00:00',
                   'GIT_COMMITTER_DATE': '2025-01-02T00:00:00+00:00'}
            return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,text=True,env=env).stdout.strip()
        git('init','--initial-branch=main');git('config','user.email','owner@example.test');git('config','user.name','Synthetic');git('config','commit.gpgsign','false')
        for folder in ('apps/portal','apps/console'):(repo/folder).mkdir(parents=True)
        (repo/'README.md').write_text('A synthetic monorepo README')
        (repo/'apps/portal/main.ts').write_text('export const portal = 1;')
        git('add','.');git('commit','-m','feat: create portal');git('tag','v0.1')
        first=git('rev-parse','HEAD')
        (repo/'apps/console/main.ts').write_text('export const consoleApp = 1;')
        git('add','.');git('commit','-m','feat: create console')
        report=collect(repo,['owner@example.test'],mapping={'P01':['apps/portal'],'P02':['apps/console']})
        self.assertEqual(report['repository']['count'],2)
        self.assertEqual(report['repository']['projectCounts'],{'P01':1,'P02':1})
        record=next(r for r in report['records'] if r['sha']==first)
        self.assertEqual(record['projectIds'],['P01'])
        self.assertIn('apps/portal/main.ts',record['files'])
        self.assertEqual(report['repositoryEvidence']['tags'][0]['tag'],'v0.1')
        self.assertIn('synthetic monorepo',report['repositoryEvidence']['readmes'][0]['text'])
        self.assertTrue(all(c['status']=='pending' for c in report['stageCandidates']))
        with self.assertRaises(ValueError): collect(repo,['owner@example.test'],mapping={'P01':['../outside']})
        self.assertEqual(git('status','--porcelain'),'')


if __name__ == '__main__': unittest.main()
