"""Regression tests for local document export and evidence-based version checks."""

from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from career_resume.export_resume import THEMES, export, document_text, W
from career_resume.resume_versions import compare, impact


class ResumeToolsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.profile = Path(temporary.name).resolve()

    def version(self, name, resume, ids=None):
        folder = self.profile / 'output/resumes' / name
        folder.mkdir(parents=True)
        (folder / 'resume.zh-CN.md').write_text(resume, encoding='utf-8')
        if ids:
            (folder / 'match-report.md').write_text(
                '## 正文依据\n\n| 正文位置 / 主张 | 履历条目 ID | 来源 |\n'
                f'|---|---|---|\n| 工单页 \\| 筛选 | {ids} | S1 |\n'
                '## 要求映射\n| 待学习 | P99-A | 无 |\n', encoding='utf-8',
            )
        return folder

    def test_docx_preserves_text_order_and_existing_file(self):
        source = self.profile / 'resume.zh-CN.md'
        source.write_text(
            '# 示例候选人\n\n> 虚构教学示例\n\n邮箱：name@\n\n## 任职\n\n'
            '### 示例公司｜2025.05–2024.01\n\n- **实现筛选** & 表单\n', encoding='utf-8',
        )
        notes = []
        output = export(source, notes=notes)
        self.assertEqual(len(notes), 2)
        with ZipFile(output) as archive:
            self.assertIsNone(archive.testzip())
            doc = ET.fromstring(archive.read('word/document.xml'))
            self.assertEqual(document_text(doc), [
                '示例候选人', '虚构教学示例', '邮箱：name@', '任职',
                '示例公司\t2025.05–2024.01', '•\t实现筛选 & 表单',
            ])
        before = output.read_bytes()
        with self.assertRaises(FileExistsError):
            export(source)
        self.assertEqual(output.read_bytes(), before)

    def test_reference_style_applies_to_selected_modules_and_retains_emphasis(self):
        source = self.profile / 'resume.zh-CN.md'
        source.write_text('# 虚构候选人\n\nfictional@example.test\n\n'
                          '## 研究成果\n\n- 参与 **离线索引** 实验，维护 `Python` 工具。\n\n'
                          '## 教育经历\n\n### 示例大学｜本科 · 软件工程｜2018–2022\n\n'
                          '## 项目经历\n\n### 虚构项目｜参与开发\n\n支持离线检索。\n', encoding='utf-8')
        with ZipFile(export(source)) as archive:
            doc = ET.fromstring(archive.read('word/document.xml'))
            styles = ET.fromstring(archive.read('word/styles.xml'))
        ns = {'w': W}
        section_style = styles.find('w:style[@w:styleId="Heading1"]', ns)
        self.assertEqual(section_style.find('w:pPr/w:shd', ns).get(f'{{{W}}}fill'), 'EDF6FC')
        self.assertEqual(section_style.find('w:pPr/w:pBdr/w:left', ns).get(f'{{{W}}}color'), '2E79A6')
        self.assertEqual(section_style.find('w:rPr/w:color', ns).get(f'{{{W}}}val'), '2E79A6')
        paragraphs = list(doc.iter(f'{{{W}}}p'))
        entry = next(p for p in paragraphs if '示例大学' in ''.join(p.itertext()))
        tab = entry.find('w:pPr/w:tabs/w:tab', ns)
        self.assertEqual(tab.get(f'{{{W}}}val'), 'right')
        self.assertEqual(document_text(entry), ['示例大学    本科 · 软件工程\t2018–2022'])
        bold = [r.find('w:t', ns).text for r in doc.findall('.//w:r', ns)
                if r.find('w:rPr/w:b[@w:val="1"]', ns) is not None]
        self.assertIn('离线索引', bold)
        self.assertIn('示例大学', bold)
        self.assertNotIn('    本科 · 软件工程', bold)
        self.assertIn('研究成果', document_text(doc))
        self.assertNotIn('工作经历', document_text(doc))
        project = next(p for p in paragraphs if '虚构项目' in ''.join(p.itertext()))
        self.assertIsNone(project.find('w:pPr/w:tabs', ns))
        self.assertFalse(doc.findall('.//w:br[@w:type="page"]', ns))

    def test_docx_uses_uniform_exact_line_spacing(self):
        """Even line spacing in Word and DOCX-converted PDF is a release requirement."""
        source = self.profile / 'resume.zh-CN.md'
        source.write_text('# 虚构候选人\n\nfictional@example.test\n\n> 虚构教学示例\n\n'
                          '## 工作经历\n\n### 示例公司｜工程师｜2024–2025\n\n- 参与 **页面维护**。\n'
                          '正文段落。\n', encoding='utf-8')
        with ZipFile(export(source)) as archive:
            doc = ET.fromstring(archive.read('word/document.xml'))
            styles = ET.fromstring(archive.read('word/styles.xml'))
        ns = {'w': W}
        body_line = None
        for style in styles.findall('w:style', ns):
            sid = style.get(f'{{{W}}}styleId')
            spacing = style.find('w:pPr/w:spacing', ns)
            snap = style.find('w:pPr/w:snapToGrid', ns)
            self.assertIsNotNone(spacing, sid + ' lacks explicit spacing')
            self.assertEqual(spacing.get(f'{{{W}}}lineRule'), 'exact', sid + ' line rule')
            self.assertIsNotNone(spacing.get(f'{{{W}}}line'), sid + ' line height')
            self.assertEqual(snap.get(f'{{{W}}}val') if snap is not None else None, '0',
                             sid + ' must disable the East Asian document grid')
            if sid in ('Normal', 'Bullet', 'Contact', 'Quote'):
                if body_line is None:
                    body_line = spacing.get(f'{{{W}}}line')
                else:
                    self.assertEqual(spacing.get(f'{{{W}}}line'), body_line,
                                     sid + ' deviates from the uniform body line height')
        self.assertEqual(body_line, '336')
        for paragraph in doc.iter(f'{{{W}}}p'):
            text = ''.join(paragraph.itertext())
            reference = paragraph.find(f'{{{W}}}pPr/{{{W}}}pStyle')
            self.assertIsNotNone(reference, 'unstyled paragraph: ' + text)
            self.assertIsNone(paragraph.find(f'{{{W}}}pPr/{{{W}}}spacing'),
                              'inline spacing override: ' + text)
        self.assertIsNone(doc.find(f'{{{W}}}body/{{{W}}}sectPr/{{{W}}}docGrid'))

    def test_theme_changes_keep_the_same_resume_text_and_existing_exports(self):
        source = self.profile / 'resume.zh-CN.md'
        source.write_text('# 虚构候选人\n\n## 工作经历\n\n### 示例公司｜工程师｜2024–2025\n\n- 参与 **页面维护**。\n')
        expected = None
        for key, palette in THEMES.items():
            path = export(source, self.profile / (key + '.docx'), theme=key)
            with ZipFile(path) as archive:
                text = document_text(ET.fromstring(archive.read('word/document.xml')))
                styles = ET.fromstring(archive.read('word/styles.xml'))
            if expected is None:
                expected = text
            self.assertEqual(text, expected)
            heading = styles.find(f'{{{W}}}style[@{{{W}}}styleId="Heading1"]')
            self.assertEqual(heading.find(f'{{{W}}}rPr/{{{W}}}color').get(f'{{{W}}}val'), palette['accent'])
            self.assertEqual(heading.find(f'{{{W}}}pPr/{{{W}}}shd').get(f'{{{W}}}fill'), palette['background'])
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                export(source, path, theme='sky')
            self.assertEqual(path.read_bytes(), before)
        for invalid in ('unknown', ['sky']):
            with self.assertRaises(ValueError):
                export(source, self.profile / 'invalid.docx', theme=invalid)
            self.assertFalse((self.profile / 'invalid.docx').exists())

    def test_placeholder_leaves_no_docx(self):
        source = self.profile / 'resume.zh-CN.md'
        source.write_text('# {{姓名}}\n\n## 任职\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'placeholder'):
            export(source)
        self.assertFalse(source.with_suffix('.docx').exists())

    def test_compare_and_impact_use_exact_ids_from_claim_mappings(self):
        before = self.version('before', '# 虚构旧版本\n', '`P01-A` / E01-T')
        after = self.version('after', '# 虚构新版本\n', 'P01-A2')
        self.version('unmapped', '# 虚构历史版本\n')
        diff = '\n'.join(compare(before, after, 'zh-CN'))
        self.assertIn('-# 虚构旧版本', diff)
        self.assertIn('+# 虚构新版本', diff)
        self.assertIn('Added citations (from available mappings): P01-A2', diff)
        matches = impact(self.profile, {'P01-A', 'P99-A'})
        self.assertEqual(len(matches), 2)
        self.assertIn('before: P01-A', matches[0])
        self.assertIn('unmapped: manual review', matches[1])
