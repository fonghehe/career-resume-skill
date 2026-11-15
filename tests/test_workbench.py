"""Verify source persistence, conflict detection, recovery and portable editor resources."""
import base64
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from career_resume.package import export
from career_resume.validate import validate
from career_resume.serve_workbench import WorkbenchHandler, context_packet, demo_workspace, new_resume, selection_draft
from career_resume.workbench_store import (Conflict, destination, encoded, locked, revision, save,
                             snapshot, state, transaction, undo, current_block)
from career_resume.file_io import atomic_write
from career_resume.export_resume import W, export as export_docx
from career_resume.resume_versions import impact


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name).resolve() / 'skill'
        export(ROOT, self.workspace, directory=True, runtime=True)
        from career_resume.init_profile import initialize
        initialize(self.workspace)
        self.root = self.workspace / 'local'
        timeline = self.root / 'data/timeline.json'
        data = json.loads(timeline.read_text())
        data['meta']['synthetic'] = True
        timeline.write_text(json.dumps(data, ensure_ascii=False))

    def change(self, fields, **extras):
        return {'collection':'projects', 'id':'P01', 'fields':fields,
                'mode':'fact', 'confirmed':True, **extras}

    def apply(self, changes=None, **extra):
        with locked(self.root):
            return save(self.root, {'revision':state(self.root)['revision'],
                                   'changes':changes or [], **extra})

    def add_project(self):
        return self.apply([self.change({'name':'虚构工单', 'organization':'虚构公司', 'summary':'参与前端筛选',
                                       'tech':['React'], 'start':'2024-01', 'end':'2024-03'})])

    def test_source_roundtrip_month_precision_and_field_confirmation(self):
        self.add_project()
        data = state(self.root)
        self.assertEqual(data['data']['projects'][0]['start'], '2024-01-01')
        self.assertEqual(data['data']['projects'][0]['end'], '2024-03-31')
        self.assertIn('"value": "2024-01"', data['notes'][data['cards']['P01']])
        self.assertIn('P01-WB-SUMMARY', data['notes'][data['cards']['P01']])
        old = (self.root / 'references/sources').glob('WB*.md')
        old = {p.name:p.read_bytes() for p in old}
        self.apply([self.change({'summary':'负责前端筛选'}, factIds={'summary':'P01-A'})])
        refreshed = state(self.root)
        self.assertIn('P01-A', refreshed['notes'][refreshed['cards']['P01']])
        for name, content in old.items():
            self.assertEqual((self.root / 'references/sources' / name).read_bytes(), content)
        self.assertEqual(validate(self.workspace)[0], [])
        self.assertIn('负责前端筛选', (self.root / 'output/career/career.md').read_text())

    def test_stale_revision_and_unconfirmed_changes_do_not_write(self):
        self.add_project()
        before = snapshot(self.root)
        for extra in ({'confirmed':False},):
            with self.assertRaises(ValueError):
                self.apply([self.change({'summary':'新职责'}, **extra)])
        self.assertEqual(snapshot(self.root), before)

        with locked(self.root), self.assertRaises(Conflict):
            save(self.root, {'revision':'stale', 'changes':[self.change({'summary':'新职责'})]})
        self.assertEqual(snapshot(self.root), before)

    def test_year_only_dates_and_unknown_job_title_preserve_source_precision(self):
        self.apply([{'collection': 'career', 'id': 'E01', 'mode': 'fact', 'confirmed': True,
                     'fields': {'organization': '虚构学校', 'role': '', 'start': '2020', 'end': '2022'}}])
        current = state(self.root)
        job = current['data']['career'][0]
        self.assertEqual((job['start'], job['end'], job['role']), ('2020-01-01', '2022-12-31', ''))
        self.assertIn('"value": "2020"', current['notes']['references/profile.md'])
        self.assertEqual(current_block(current['notes']['references/profile.md'])['career/E01']['role']['status'], 'pending')
        self.assertNotIn('role', job.get('confirmedFields', []))
        self.assertEqual(validate(self.workspace)[0], [])

    def test_clearing_a_field_removes_current_support_and_preserves_old_sources(self):
        self.add_project()
        old_sources = {path.name: path.read_bytes() for path in (self.root / 'references/sources').glob('WB*.md')}
        self.apply([self.change({'summary': ''})])
        current = state(self.root)
        project = current['data']['projects'][0]
        self.assertEqual(project['summary'], '')
        self.assertNotIn('summary', project['confirmedFields'])
        self.assertFalse(any(entry['field'] == 'summary' for entry in project['sources']))
        fields = current_block(current['notes'][current['cards']['P01']])['projects/P01']
        self.assertEqual(fields['summary']['status'], 'pending')
        for name, content in old_sources.items():
            self.assertEqual((self.root / 'references/sources' / name).read_bytes(), content)

    def test_failed_multi_file_write_rolls_back_and_preserves_sources(self):
        self.add_project()
        before = snapshot(self.root)
        calls = 0
        def broken(path, data):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError('simulated write failure')
            return atomic_write(path, data)
        with patch('career_resume.workbench_store.atomic_write', side_effect=broken):
            with self.assertRaises(OSError):
                self.apply([self.change({'summary':'失败的更正'})])
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse((self.root / 'output/workbench/pending.json').exists())

    def test_history_restore_and_newer_content_guard(self):
        self.add_project()
        before = snapshot(self.root)
        identity = self.apply([self.change({'summary':'新摘要'})])
        with locked(self.root):
            undo(self.root, identity, state(self.root)['revision'])
        self.assertEqual(snapshot(self.root), before)
        identity = self.apply([self.change({'summary':'新摘要'})])
        self.apply([self.change({'summary':'再一次更正'})])
        with locked(self.root), self.assertRaises(Conflict):
            undo(self.root, identity, state(self.root)['revision'])

    def test_crash_journal_is_recovered_before_read(self):
        target = self.root / 'references/profile.md'
        before = target.read_bytes()
        after = b'partial transaction'
        pending = self.root / 'output/workbench/pending.json'
        pending.parent.mkdir(parents=True)
        pending.write_bytes(encoded({'id':'CRASH', 'files':{'references/profile.md':{
            'before':base64.b64encode(before).decode(), 'after':base64.b64encode(after).decode()}}}))
        target.write_bytes(after)
        with locked(self.root):
            self.assertEqual(target.read_bytes(), before)
        self.assertFalse(pending.exists())

    def test_display_change_keeps_fact_status_and_raw_edit_preserves_managed_block(self):
        self.add_project()
        before = state(self.root)['data']['projects'][0]
        self.apply([self.change({'summary':'展示摘要'}, mode='display', confirmed=False)])
        after = state(self.root)['data']['projects'][0]
        self.assertEqual(before['confirmedFields'], after['confirmedFields'])
        self.assertEqual(before['sources'], after['sources'])
        path = state(self.root)['cards']['P01']
        text = (self.root / path).read_text()
        self.apply(notes=[{'path':path,'text':text+'\n自由编写的原文补充。\n'}])
        self.assertIn('自由编写的原文补充', (self.root / 'showcase/project-timeline.html').read_text())
        with self.assertRaises(ValueError):
            self.apply(notes=[{'path':path,'text':'# P01｜覆写字段块'}])

    def test_isolated_demo_and_resume_versions_are_complete(self):
        demo = self.workspace.parent / 'demo'
        demo_workspace(demo)
        root = demo / 'local'
        data = state(root)
        self.assertTrue(data['data']['meta']['synthetic'])
        self.assertEqual(len(data['data']['projects']), 3)
        self.assertEqual(validate(demo)[0], [])
        text = context_packet(root, {'projects':['P02'], 'instruction':'只润色控制台'})
        self.assertIn('P02｜', text)
        self.assertNotIn('## 选定项目 P01', text)
        with locked(root):
            new_resume(root, {'revision':data['revision'],'version':'test-v2','language':'zh-CN',
                              'body':'# 虚构候选人\n\n参与页面开发。', 'report':'## 正文依据\n\n待核对。'})
        self.assertEqual(len(state(root)['resumes']), 3)
        with locked(root), self.assertRaises(ValueError):
            new_resume(root, {'revision':state(root)['revision'],'version':'test-v2','language':'zh-CN',
                              'body':'# 覆盖旧版本', 'report':'## 正文依据'})
        with self.assertRaises(ValueError):
            destination(root, '../outside.md')

    def test_no_project_material_selection_uses_arbitrary_professional_sections(self):
        self.apply([{'collection': 'career', 'id': 'E01', 'mode': 'fact', 'confirmed': True,
                     'fields': {'organization': '虚构社区服务点', 'role': '服务协调',
                                'summary': '参与服务安排与记录整理。', 'start': '2023', 'end': '2024'}}])
        path = self.root / 'data/timeline.json'
        data = json.loads(path.read_text())
        data['presentation'] = {'profession': '修复、讲解与社区服务（虚构跨领域）',
            'sections': [{'id': 'learning-and-practice', 'title': '学习与专业实践',
                          'items': [{'title': '虚构修复记录整理研修', 'period': '2022',
                                     'summary': '参与材料记录练习。', 'factIds': ['F99']}]}]}
        path.write_text(json.dumps(data, ensure_ascii=False))
        before = snapshot(self.root)
        payload = {'careers': ['E01'], 'sections': ['learning-and-practice']}
        draft = selection_draft(self.root, payload)
        self.assertIn('虚构社区服务点', draft['body'])
        self.assertIn('虚构修复记录整理研修', draft['body'])
        self.assertIn('2023–2024', draft['body'])
        self.assertNotIn('2023-01-01', draft['body'])
        self.assertIn('F99', draft['context'])
        self.assertNotIn('## 项目经历', draft['body'])
        self.assertEqual(json.loads(path.read_text())['projects'], [])
        self.assertEqual(snapshot(self.root), before)

    def test_source_only_selection_keeps_scope_and_does_not_turn_notes_into_claims(self):
        selected = self.root / 'references/career/learning.md'
        selected.parent.mkdir(parents=True, exist_ok=True)
        selected.write_text('# 虚构学习记录\n\nF01｜2021 年参与社区讲解培训｜confirmed｜虚构口述\n')
        unselected = selected.with_name('other.md')
        unselected.write_text('# 虚构未选材料\n\nUNSELECTED-MATERIAL-SENTINEL\n')
        payload = {'records': ['references/career/learning.md'], 'language': 'en'}
        before = snapshot(self.root)
        draft = selection_draft(self.root, payload)
        self.assertIn('2021 年参与社区讲解培训', draft['context'])
        self.assertNotIn('UNSELECTED-MATERIAL-SENTINEL', draft['context'])
        self.assertNotIn('2021 年参与社区讲解培训', draft['body'])
        self.assertEqual(snapshot(self.root), before)
        for payload in ({}, {'records': ['../outside.md']}, {'careers': ['E99']},
                        {'sections': ['not-a-registered-section']}, {'projects': ['P99']}):
            with self.assertRaises(ValueError):
                context_packet(self.root, payload)

    def test_learning_and_service_resume_versions_export_without_projects(self):
        bodies = {
            'zh-CN': '# 虚构候选人\n\n## 工作与实践经历\n\n'
                     '### 虚构社区服务点｜服务协调｜2023–2024\n\n- 参与服务安排与记录整理。\n\n'
                     '## 学习经历\n\n### 虚构资料整理研修｜2022\n',
            'en': '# Fictional Candidate\n\n## Professional Experience\n\n'
                  '### Example Community Service Point | Service Coordination | 2023 – 2024\n\n'
                  '- Contributed to service scheduling and record organization.\n\n'
                  '## Education & Training\n\n### Example Record Organization Workshop | 2022\n',
        }
        for language, body in bodies.items():
            with locked(self.root):
                new_resume(self.root, {'revision': state(self.root)['revision'],
                    'version': 'fictional-general-' + language, 'language': language,
                    'body': body, 'report': '## 正文依据\n\n虚构测试材料：E01-A / L01，供隔离工具测试。'})
            source = self.root / 'output/resumes' / ('fictional-general-' + language) / f'resume.{language}.md'
            output = export_docx(source)
            with ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn('2023', archive.read('word/document.xml').decode())
        self.assertEqual(state(self.root)['data']['projects'], [])

    def test_fictional_correction_to_new_resume_preserves_old_evidence_and_exports(self):
        timeline = self.root / 'data/timeline.json'
        data = json.loads(timeline.read_text())
        data['meta']['synthetic'] = True
        timeline.write_bytes(encoded(data))
        self.add_project()
        fact = 'P01-WB-SUMMARY'

        def resume(version, claim):
            report = ('# 依据报告（虚构测试）\n\n## 正文依据\n\n'
                      '| 简历位置 / 主张 | 履历条目 ID | 来源 / 状态 |\n'
                      '|---|---|---|\n'
                      f'| 项目：{claim} | {fact} | 工作台本人模拟确认 / confirmed |\n')
            with locked(self.root):
                new_resume(self.root, {'revision':state(self.root)['revision'],
                                      'version':version, 'language':'zh-CN',
                                      'body':f'# 虚构候选人\n\n## 项目经历\n\n- {claim}\n',
                                      'report':report})
            folder = self.root / 'output/resumes' / version
            export_docx(folder / 'resume.zh-CN.md')
            return folder

        old = resume('fictional-v1', '参与前端筛选')
        preserved = {p:p.read_bytes() for p in old.iterdir()}
        preserved.update({p:p.read_bytes() for p in (self.root / 'references/sources').glob('WB*.md')})
        self.apply([self.change({'summary':'虚构测试：负责前端筛选'},
                                factIds={'summary':fact})])
        findings = impact(self.root, {fact})
        self.assertTrue(any('fictional-v1' in line and fact in line for line in findings))
        self.assertEqual(impact(self.root, {'P99-A'}),
                         ['No saved claim mappings reference those exact IDs.'])
        new = resume('fictional-v2', '负责前端筛选')
        with ZipFile(new / 'resume.zh-CN.docx') as archive:
            text = ''.join(ET.fromstring(archive.read('word/document.xml')).itertext())
        self.assertIn('负责前端筛选', text)
        self.assertNotIn('参与前端筛选', text)
        self.assertIn('负责前端筛选', (self.root / 'output/career/career.md').read_text())
        for path, content in preserved.items():
            self.assertEqual(path.read_bytes(), content, path)
        self.assertEqual(validate(self.workspace)[0], [])
        self.assertTrue(state(self.root)['data']['meta']['synthetic'])

    def test_resume_theme_roundtrip_and_download_override_preserve_saved_version(self):
        with locked(self.root):
            new_resume(self.root, {'revision':state(self.root)['revision'],
                                  'version':'fictional-theme','language':'zh-CN', 'theme':'sage',
                                  'body':'# 虚构候选人\n\n## 任职\n\n参与页面维护。',
                                  'report':'# 虚构依据\n\n## 正文依据\n\n用于主题测试。'})
        row = state(self.root)['resumes'][0]
        self.assertEqual(row['theme'], 'sage')
        before = snapshot(self.root)
        from io import BytesIO
        for override, color in (({}, '4B7863'), ({'theme':'lavender'}, '77639E')):
            data = WorkbenchHandler.action(None, '/api/docx', self.root, {'path':row['path'], **override})
            with ZipFile(BytesIO(data)) as archive:
                styles = ET.fromstring(archive.read('word/styles.xml'))
            heading = styles.find('.//{%s}style[@{%s}styleId="Heading1"]' % (W, W))
            self.assertEqual(heading.find('{%s}rPr/{%s}color' % (W, W)).get('{%s}val' % W), color)
        self.assertEqual(snapshot(self.root), before)

    def test_english_resume_version_saves_and_downloads_in_international_layout(self):
        with locked(self.root):
            new_resume(self.root, {'revision':state(self.root)['revision'],
                                  'version':'fictional-en','language':'en','theme':'sky',
                                  'body':'# Sample Candidate\n\n> Fictional teaching example\n\n'
                                         '## Experience\n\n### Sample Co | Engineer | Jan 2024 – Present\n',
                                  'report':'# Fictional report\n\n## 正文依据\n\n| A | E01 | S1 |\n'})
        row = next(item for item in state(self.root)['resumes'] if item['version'] == 'fictional-en')
        self.assertEqual(row['theme'], 'sky')  # fallback keeps the theme picker usable
        style = json.loads((self.root / 'output/resumes/fictional-en/style.json').read_text(encoding='utf-8'))
        self.assertEqual(style['layout'], 'international')
        self.assertIsNone(style['theme'])
        from io import BytesIO
        data = WorkbenchHandler.action(None, '/api/docx', self.root,
                                       {'path':row['path'], 'theme':'peach', 'page':'a4'})
        with ZipFile(BytesIO(data)) as archive:
            doc = ET.fromstring(archive.read('word/document.xml'))
            styles = ET.fromstring(archive.read('word/styles.xml'))
        heading = styles.find('.//{%s}style[@{%s}styleId="Heading1"]' % (W, W))
        self.assertEqual(heading.find('{%s}rPr/{%s}color' % (W, W)).get('{%s}val' % W), '000000')
        self.assertIsNotNone(heading.find('{%s}rPr/{%s}caps' % (W, W)))
        self.assertIsNone(heading.find('{%s}pPr/{%s}shd' % (W, W)))
        page = doc.find('.//{%s}sectPr/{%s}pgSz' % (W, W))
        self.assertEqual(page.get('{%s}w' % W), '11906')  # explicit A4 override


if __name__ == '__main__':
    unittest.main()
