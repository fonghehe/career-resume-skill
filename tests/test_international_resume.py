"""Regression tests for the monochrome ATS-friendly English DOCX layout."""

from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from career_resume.export_resume import THEMES, export, document_text, W

NS = {'w': W}
EN_RESUME = (
    '# Jane Doe\n\n'
    'San Francisco, CA | jane@example.test\n\n'
    '## Professional Summary\n\n'
    'Frontend engineer with business back-office experience.\n\n'
    '## Professional Experience\n\n'
    '### Sample Company | Frontend Engineer | Jan 2024 – Present\n\n'
    '- Built ticket filtering and **form validation** in React.\n\n'
    '## Education\n\n'
    '### Sample University | B.S. in Software Engineering | 2018 – 2022\n'
)


class InternationalResumeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.profile = Path(temporary.name).resolve()
        self.source = self.profile / 'resume.en.md'
        self.source.write_text(EN_RESUME, encoding='utf-8')

    def parts(self, path):
        with ZipFile(path) as archive:
            self.assertIsNone(archive.testzip())
            return (ET.fromstring(archive.read('word/document.xml')),
                    ET.fromstring(archive.read('word/styles.xml')))

    def style(self, styles, style_id):
        return styles.find(f'w:style[@w:styleId="{style_id}"]', NS)

    def test_layout_is_monochrome_with_uppercase_ruled_sections(self):
        doc, styles = self.parts(export(self.source, layout='international'))
        heading = self.style(styles, 'Heading1')
        self.assertEqual(heading.find('w:rPr/w:color', NS).get(f'{{{W}}}val'), '000000')
        self.assertIsNotNone(heading.find('w:rPr/w:caps', NS))
        bottom = heading.find('w:pPr/w:pBdr/w:bottom', NS)
        self.assertIsNotNone(bottom)
        self.assertEqual(bottom.get(f'{{{W}}}color'), '000000')
        self.assertIsNone(heading.find('w:pPr/w:pBdr/w:left', NS))
        self.assertIsNone(heading.find('w:pPr/w:shd', NS))
        self.assertFalse(styles.findall('.//w:shd', NS), 'theme fills must not appear')
        self.assertEqual(self.style(styles, 'Heading1').find('w:rPr/w:rFonts', NS)
                         .get(f'{{{W}}}eastAsia'), 'Arial')
        section = doc.find('w:body/w:sectPr', NS)
        self.assertEqual(section.find('w:pgSz', NS).get(f'{{{W}}}w'), '12240')
        self.assertEqual(section.find('w:pgSz', NS).get(f'{{{W}}}h'), '15840')
        self.assertEqual(section.find('w:pgMar', NS).get(f'{{{W}}}left'), '1080')
        self.assertIsNone(section.find('w:docGrid', NS))
        self.assertIn('Sample Company    Frontend Engineer\tJan 2024 – Present',
                      document_text(doc))
        self.assertIn('•\tBuilt ticket filtering and form validation in React.',
                      document_text(doc))

    def test_every_non_title_paragraph_shares_one_exact_line_height(self):
        doc, styles = self.parts(export(self.source, layout='international'))
        for style in styles.findall('w:style', NS):
            style_id = style.get(f'{{{W}}}styleId')
            spacing = style.find('w:pPr/w:spacing', NS)
            snap = style.find('w:pPr/w:snapToGrid', NS)
            self.assertIsNotNone(spacing, style_id)
            self.assertEqual(spacing.get(f'{{{W}}}lineRule'), 'exact', style_id)
            self.assertEqual(snap.get(f'{{{W}}}val'), '0', style_id)
            expected = '480' if style_id == 'Title' else '288'
            self.assertEqual(spacing.get(f'{{{W}}}line'), expected, style_id)
        for paragraph in doc.iter(f'{{{W}}}p'):
            self.assertIsNotNone(paragraph.find(f'{{{W}}}pPr/{{{W}}}pStyle'))
            self.assertIsNone(paragraph.find(f'{{{W}}}pPr/{{{W}}}spacing'))

    def test_page_option_switches_to_a4_and_moves_the_date_tab_stop(self):
        doc, _ = self.parts(export(self.source, self.profile / 'a4.docx',
                                   layout='international', page='a4'))
        section = doc.find('w:body/w:sectPr', NS)
        self.assertEqual(section.find('w:pgSz', NS).get(f'{{{W}}}w'), '11906')
        self.assertEqual(section.find('w:pgSz', NS).get(f'{{{W}}}h'), '16838')
        tab = next(p.find('w:pPr/w:tabs/w:tab', NS) for p in doc.iter(f'{{{W}}}p')
                   if p.find('w:pPr/w:tabs/w:tab', NS) is not None
                   and p.find('w:pPr/w:tabs/w:tab', NS).get(f'{{{W}}}val') == 'right')
        self.assertEqual(tab.get(f'{{{W}}}pos'), '9746')

    def test_theme_colors_are_ignored_but_invalid_themes_still_fail(self):
        for key in THEMES:
            doc, styles = self.parts(export(self.source, self.profile / (key + '.docx'),
                                            theme=key, layout='international'))
            heading = self.style(styles, 'Heading1')
            self.assertEqual(heading.find('w:rPr/w:color', NS).get(f'{{{W}}}val'), '000000')
            self.assertIsNone(heading.find('w:pPr/w:shd', NS))
        with self.assertRaises(ValueError):
            export(self.source, self.profile / 'invalid.docx', theme='unknown',
                   layout='international')
        self.assertFalse((self.profile / 'invalid.docx').exists())

    def test_english_and_numeric_date_ranges_right_align(self):
        source = self.profile / 'dates.en.md'
        source.write_text(
            '# Jane Doe\n\n## Experience\n\n'
            '### A | Engineer | Jan 2024 – Present\n\n'
            '### B | Engineer | January 2024 - Dec 2025\n\n'
            '### C | Engineer | Sep 2023 – Mar 2024\n\n'
            '### D | Engineer | 2018 – 2022\n\n'
            '### E | Engineer | 2024.01–2025.12\n\n'
            '### F | Frontend Development\n', encoding='utf-8')
        notes = []
        doc, _ = self.parts(export(source, notes=notes, layout='international'))
        self.assertEqual(notes, [])
        right_tabs = []
        for paragraph in doc.iter(f'{{{W}}}p'):
            tab = paragraph.find('w:pPr/w:tabs/w:tab', NS)
            if tab is not None and tab.get(f'{{{W}}}val') == 'right':
                right_tabs.append(''.join(paragraph.itertext()))
        self.assertEqual(len(right_tabs), 5)
        self.assertTrue(any('Frontend Development' in text for text in
                            [''.join(p.itertext()) for p in doc.iter(f'{{{W}}}p')]))
        self.assertNotIn('Frontend Development', right_tabs)

    def test_reversed_english_month_range_is_reported(self):
        source = self.profile / 'reversed.en.md'
        source.write_text('# Jane Doe\n\n## Experience\n\n'
                          '### A | Engineer | Dec 2025 – Jan 2024\n', encoding='utf-8')
        notes = []
        export(source, notes=notes, layout='international')
        self.assertEqual(len(notes), 1)
        self.assertIn('reversed date range', notes[0])

    def test_invalid_layout_or_page_creates_no_file(self):
        for kwargs in ({'layout': 'unknown'}, {'layout': 'international', 'page': 'tabloid'}):
            with self.assertRaises(ValueError):
                export(self.source, self.profile / 'bad.docx', **kwargs)
            self.assertFalse((self.profile / 'bad.docx').exists())

    def test_standard_layout_remains_the_chinese_default(self):
        source = self.profile / 'resume.zh-CN.md'
        source.write_text('# 虚构候选人\n\n## 工作经历\n\n'
                          '### 示例公司｜工程师｜2024.01–2025.12\n', encoding='utf-8')
        doc, styles = self.parts(export(source))
        section = doc.find('w:body/w:sectPr', NS)
        self.assertEqual(section.find('w:pgSz', NS).get(f'{{{W}}}w'), '11906')
        self.assertEqual(section.find('w:pgMar', NS).get(f'{{{W}}}left'), '600')
        heading = self.style(styles, 'Heading1')
        self.assertEqual(heading.find('w:pPr/w:shd', NS).get(f'{{{W}}}fill'), 'EDF6FC')
        self.assertIsNotNone(heading.find('w:pPr/w:pBdr/w:left', NS))
        self.assertIsNone(heading.find('w:rPr/w:caps', NS))
        self.assertEqual(self.style(styles, 'Normal').find('w:pPr/w:spacing', NS)
                         .get(f'{{{W}}}line'), '336')


if __name__ == '__main__':
    unittest.main()
