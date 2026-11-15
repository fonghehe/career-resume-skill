"""Export failure boundaries, PDF conversion and automatic language layout."""

from io import BytesIO
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from career_resume.export_resume import W, export, export_formats
from career_resume.export_resume import convert_pdf as convert, conversion_environment

PDF = b'%PDF-1.4\n% fictional converter output for testing only\n%%EOF\n'


class ResumePdfTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'resume.en.md'
        self.source.write_text('# Fictional Teacher\n\n## Experience\n\n'
                               '### Example School | Teacher | 2020 – 2024\n\n'
                               '- Designed reading tasks.\n', encoding='utf-8')

    def converter(self, command, **options):
        source = Path(command[-1])
        self.assertEqual(source.name, 'resume.docx')
        self.assertTrue(source.is_file())
        self.assertTrue(command[1].startswith('-env:UserInstallation=file:'))
        self.assertIn('--headless', command)
        self.assertNotIn('shell', options)
        source.with_suffix('.pdf').write_bytes(PDF)
        return subprocess.CompletedProcess(command, 0)

    def test_language_filename_selects_layout_without_an_extra_flag(self):
        with ZipFile(export(self.source)) as archive:
            styles = ET.fromstring(archive.read('word/styles.xml'))
        ns = {'w': W}
        heading = styles.find('w:style[@w:styleId="Heading1"]', ns)
        self.assertEqual(heading.find('w:rPr/w:color', ns).get(f'{{{W}}}val'), '000000')
        self.assertIsNotNone(heading.find('w:rPr/w:caps', ns))

    def test_both_formats_and_existing_docx_conversion_preserve_the_source(self):
        with patch('career_resume.export_resume.converter_path', return_value='/fictional/soffice'), \
                patch('career_resume.export_resume.subprocess.run', side_effect=self.converter):
            docx, pdf = export_formats(self.source, format='all')
            original = docx.read_bytes()
            self.assertEqual(pdf.read_bytes(), PDF)
            second = convert(docx, self.root / 'second.pdf')
            self.assertEqual(second.read_bytes(), PDF)
            self.assertEqual(docx.read_bytes(), original)
            with self.assertRaises(FileExistsError):
                export_formats(self.source, format='all')
            self.assertEqual(docx.read_bytes(), original)

    def test_pdf_only_uses_a_temporary_docx_and_keeps_no_intermediate_file(self):
        with patch('career_resume.export_resume.converter_path', return_value='/fictional/soffice'), \
                patch('career_resume.export_resume.subprocess.run', side_effect=self.converter):
            outputs = export_formats(self.source, format='pdf')
        self.assertEqual(outputs, [self.source.with_suffix('.pdf')])
        self.assertFalse(self.source.with_suffix('.docx').exists())

    def test_missing_converter_creates_no_export_and_docx_still_works(self):
        with patch('career_resume.export_resume.shutil.which', return_value=None):
            with self.assertRaisesRegex(ValueError, 'LibreOffice'):
                export_formats(self.source, format='all')
            self.assertEqual(list(self.root.glob('*.pdf')), [])
            self.assertEqual(list(self.root.glob('*.docx')), [])
            self.assertTrue(export(self.source).is_file())

    def test_timeout_failure_and_invalid_pdf_never_publish_a_partial_pdf(self):
        docx = export(self.source)
        original = docx.read_bytes()
        failures = [subprocess.TimeoutExpired('soffice', 60),
                    subprocess.CompletedProcess([], 1),
                    subprocess.CompletedProcess([], 0)]
        for result in failures:
            with self.subTest(result=result), \
                    patch('career_resume.export_resume.converter_path', return_value='/fictional/soffice'), \
                    patch('career_resume.export_resume.subprocess.run', side_effect=result if isinstance(result, Exception) else None,
                          return_value=result):
                with self.assertRaises(ValueError):
                    convert(docx)
                self.assertFalse(docx.with_suffix('.pdf').exists())
                self.assertEqual(docx.read_bytes(), original)
        def invalid(command, **options):
            Path(command[-1]).with_suffix('.pdf').write_bytes(b'not a PDF')
            return subprocess.CompletedProcess(command, 0)
        with patch('career_resume.export_resume.converter_path', return_value='/fictional/soffice'), \
                patch('career_resume.export_resume.subprocess.run', side_effect=invalid):
            with self.assertRaisesRegex(ValueError, 'complete PDF'):
                convert(docx)
        self.assertFalse(docx.with_suffix('.pdf').exists())

    def test_symlink_target_does_not_modify_another_file(self):
        docx = export(self.source)
        other = self.root / 'keep.pdf'
        other.write_bytes(b'keep')
        target = self.root / 'link.pdf'
        target.symlink_to(other)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            convert(docx, target)
        self.assertEqual(other.read_bytes(), b'keep')

    def test_font_configuration_is_local_and_escapes_directory_names(self):
        import os
        fonts = self.root / 'fonts & examples'
        fonts.mkdir()
        before = os.environ.copy()
        env = conversion_environment(self.root, [fonts])
        self.assertEqual(os.environ, before)
        config = Path(env['FONTCONFIG_FILE'])
        self.assertEqual(config.parent, self.root)
        tree = ET.fromstring(config.read_bytes())
        self.assertIn(str(fonts), [node.text for node in tree.findall('dir')])
        self.assertEqual(tree.find('cachedir').text, str(self.root / 'font-cache'))
        with self.assertRaisesRegex(ValueError, 'Font directory'):
            conversion_environment(self.root, [self.root / 'missing'])


if __name__ == '__main__':
    unittest.main()
