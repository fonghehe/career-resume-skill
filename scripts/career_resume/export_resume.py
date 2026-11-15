#!/usr/bin/env python3
"""Export Chinese or English Markdown resumes to DOCX and optional local PDF."""

from datetime import date
from io import BytesIO
from pathlib import Path
import re
import os
import shutil
import subprocess
import sys
from xml.sax.saxutils import escape
import tempfile
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from career_resume.cli_support import fail
from career_resume.file_io import write_new
from career_resume.presentation import THEMES, NEUTRAL, theme_colors

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
OFFICE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
ET.register_namespace('w', W)

def word(parent, tag, **attributes):
    return ET.SubElement(parent, f'{{{W}}}{tag}', {f'{{{W}}}{k}': v for k, v in attributes.items()})


def paragraphs(markdown):
    """Read the single-column template's headings, lists, quotes and text in order."""
    result = []
    for number, raw in enumerate(markdown.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if re.search(r'\{\{[^}]*\}\}|【(?:待填|待补|占位)[^】]*】', line):
            raise ValueError(f'Line {number}: fill or remove the template placeholder.')
        if re.match(r'^(?:```|~~~|\||!\[|<\w|<!--|---+$)', line):
            raise ValueError(f'Line {number}: use plain text, headings or lists in the resume template.')
        heading = re.fullmatch(r'(#{1,3})\s+(.+)', line)
        bullet = re.fullmatch(r'[-*+]\s+(.+)', line)
        if heading:
            style, line = {1: 'Title', 2: 'Heading1', 3: 'Heading2'}[len(heading[1])], heading[2]
        elif bullet:
            style, line = 'Bullet', '• ' + bullet[1]
        elif line.startswith('> '):
            style, line = 'Quote', line[2:]
        else:
            style = 'Normal'
        # Keep visible link labels and destinations available in extracted text.
        line = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+|mailto:[^\s)]+)\)',
                      lambda m: m[1] if m[1] == m[2] else f'{m[1]} ({m[2]})', line)
        result.append((style, line))
    if not result or result[0][0] != 'Title' or len(result) < 2:
        raise ValueError('Expected a name heading followed by resume content.')
    return result


def format_notes(items):
    """Flag common contact and employment date errors without changing the resume."""
    notes = []
    for style, line in items:
        contact = re.match(r'^(?:邮箱|e-?mail)\s*[:：]\s*(.*)$', line, re.IGNORECASE)
        if contact and not re.search(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>.]+', contact[1]):
            notes.append('Review the email field: ' + line)
        if style != 'Heading2':
            continue
        span = re.search(r'(?<!\d)(\d{4}[./-]\d{2}(?:[./-]\d{2})?)\s*[–—~至]\s*'
                         r'(\d{4}[./-]\d{2}(?:[./-]\d{2})?)(?!\d)', line)
        if span:
            try:
                dates = []
                for value in span.groups():
                    parts = [int(part) for part in re.split(r'[./-]', value)]
                    dates.append(date(*parts) if len(parts) == 3 else date(*parts, 1))
                if dates[0] > dates[1]:
                    notes.append('Review reversed date range: ' + span[0])
            except ValueError:
                notes.append('Review invalid date range: ' + span[0])
        english = [(MONTH_ORDER[match[1][:3].lower()], int(match[2]))
                   for match in MONTH_YEAR.finditer(line)]
        if len(english) >= 2 and (english[0][1], english[0][0]) > (english[1][1], english[1][0]):
            notes.append('Review reversed date range: ' + line)
    return notes


def inline_runs(text):
    """Keep meaningful emphasis while removing Markdown delimiters from output."""
    offset = 0
    for match in re.finditer(r'(\*\*|__|`)(.+?)\1', text):
        if match.start() > offset:
            yield text[offset:match.start()], False
        yield match[2], match[1] != '`'
        offset = match.end()
    if offset < len(text):
        yield text[offset:], False


def plain_text(text):
    return ''.join(value for value, _ in inline_runs(text))


# Both numeric Chinese-style ranges and English "Mon YYYY – Mon YYYY / Present"
# ranges are accepted; only a complete trailing range becomes a right-aligned date.
MONTH = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
         r'Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?')
NUMERIC_DATE = r'\d{4}(?:[./-]\d{1,2})?(?:[./-]\d{1,2})?'
DATE = rf'(?:{NUMERIC_DATE}|{MONTH}\s+\d{{4}})'
OPEN_ENDED = r'(?:至今|[Pp]resent|[Cc]urrent|[Nn]ow|[Oo]ngoing)'
DATE_SPAN = re.compile(rf'{DATE}\s*[–—~至-]\s*(?:{DATE}|{OPEN_ENDED})', re.IGNORECASE)
MONTH_YEAR = re.compile(rf'(?<!\w)({MONTH})\s+(\d{{4}})(?!\d)', re.IGNORECASE)
MONTH_ORDER = {name[:3].lower(): index for index, name in enumerate(
    ('January', 'February', 'March', 'April', 'May', 'June', 'July',
     'August', 'September', 'October', 'November', 'December'), 1)}

LAYOUTS = ('standard', 'international')
PAGES = {'a4': ('11906', '16838'), 'letter': ('12240', '15840')}


def entry_parts(content):
    parts = re.split(r'\s*[｜|]\s*', content)
    right = ''
    if len(parts) > 1 and DATE_SPAN.fullmatch(plain_text(parts[-1])):
        right = parts.pop()
    return parts[0], '    '.join(parts[1:]), right


def visible_text(style, content):
    if style == 'Bullet':
        return '•\t' + plain_text(content[2:])
    if style != 'Heading2':
        return plain_text(content)
    name, detail, right = entry_parts(content)
    return plain_text(name + ('    ' + detail if detail else '') + ('\t' + right if right else ''))


def add_runs(paragraph, text, bold=None):
    for value, emphasis in inline_runs(text):
        run = word(paragraph, 'r')
        if emphasis or bold is not None:
            word(word(run, 'rPr'), 'b', val='1' if emphasis or bold else '0')
        node = word(run, 't')
        node.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        node.text = value


def document_text(document):
    """Read visible text per paragraph, including tab stops used for dates."""
    return [''.join('\t' if node.tag == f'{{{W}}}tab' else (node.text or '')
                    for run in paragraph.findall(f'{{{W}}}r') for node in run.iter()
                    if node.tag in (f'{{{W}}}t', f'{{{W}}}tab'))
            for paragraph in document.iter(f'{{{W}}}p')]


def build_docx(items, theme='sky', layout='standard', page=None):
    palette = theme_colors(theme)  # Validate the choice even when a layout ignores color.
    if layout not in LAYOUTS:
        raise ValueError('Unknown resume layout; choose: ' + ', '.join(LAYOUTS))
    if page is not None and page not in PAGES:
        raise ValueError('Unknown page size; choose: ' + ', '.join(PAGES))
    international = layout == 'international'
    page = page or ('letter' if international else 'a4')
    page_width, page_height = PAGES[page]
    margin = '1080' if international else '600'
    doc = ET.Element(f'{{{W}}}document')
    body = word(doc, 'body')
    content_width = str(int(page_width) - 2 * int(margin))
    before_sections = True
    for style, content in items:
        paragraph = word(body, 'p')
        props = word(paragraph, 'pPr')
        display_style = style
        if style == 'Heading1':
            before_sections = False
        elif style == 'Normal' and before_sections:
            display_style = 'Contact'
        word(props, 'pStyle', val=display_style)
        if style == 'Heading2':
            name, detail, right = entry_parts(content)
            if right:
                word(word(props, 'tabs'), 'tab', val='right', pos=content_width)
            add_runs(paragraph, name, bold=True)
            if detail:
                add_runs(paragraph, '    ' + detail, bold=False)
            if right:
                word(word(paragraph, 'r'), 'tab')
                add_runs(paragraph, right, bold=False)
        elif style == 'Bullet':
            add_runs(paragraph, '•')
            word(word(paragraph, 'r'), 'tab')
            add_runs(paragraph, content[2:])
        else:
            add_runs(paragraph, content)
    section = word(body, 'sectPr')
    word(section, 'pgSz', w=page_width, h=page_height)
    word(section, 'pgMar', top=margin, bottom=margin, left=margin, right=margin,
         header='720' if international else '240',
         footer='720' if international else '240', gutter='0')

    styles = ET.Element(f'{{{W}}}styles')
    for name, label, size, bold, color in (
        ('Normal', 'Normal', '21', False, NEUTRAL['body']),
        ('Title', 'Title', '40' if international else '44', True, NEUTRAL['title']),
        ('Contact', 'Contact', '20', False,
         NEUTRAL['body'] if international else NEUTRAL['muted']),
        ('Heading1', 'heading 1', '22' if international else '28', True,
         NEUTRAL['title'] if international else palette['accent']),
        ('Heading2', 'heading 2', '21' if international else '23', False, NEUTRAL['body']),
        ('Bullet', 'Resume bullet', '21', False, NEUTRAL['body']),
        ('Quote', 'Resume note', '19', False,
         NEUTRAL['body'] if international else NEUTRAL['muted']),
    ):
        style = word(styles, 'style', type='paragraph', styleId=name)
        if name == 'Normal':
            style.set(f'{{{W}}}default', '1')
        word(style, 'name', val=label)
        if name != 'Normal':
            word(style, 'basedOn', val='Normal')
        props = word(style, 'pPr')
        if name in ('Title', 'Heading1', 'Heading2'):
            word(props, 'keepNext')
        # Keep a short bullet or business-context paragraph together across a
        # page boundary; keepNext still applies only to headings, not whole jobs.
        word(props, 'keepLines')
        word(props, 'widowControl', val='1')
        if name == 'Heading1':
            border = word(props, 'pBdr')
            if international:
                # ATS-friendly: a single thin rule, no color fill or side bar.
                word(border, 'bottom', val='single', sz='6', space='4', color=NEUTRAL['title'])
            else:
                word(border, 'left', val='single', sz='18', space='8', color=palette['accent'])
                word(props, 'shd', val='clear', color='auto', fill=palette['background'])
        if name == 'Bullet':
            word(word(props, 'tabs'), 'tab', val='left', pos='200')
        # Explicit values prevent template defaults / East Asian document grids
        # from changing one body paragraph's alignment or baseline spacing.
        word(props, 'snapToGrid', val='0')
        if international:
            # All non-title styles share one exact 14.4 pt line height.
            word(props, 'spacing',
                 before='240' if name == 'Heading1' else '120' if name == 'Heading2' else '0',
                 after='60', line='480' if name == 'Title' else '288', lineRule='exact')
        else:
            word(props, 'spacing', before='300' if name == 'Heading1' else '140' if name == 'Heading2' else '0',
                 after='140' if name == 'Heading1' else '120' if name in ('Title', 'Contact') else '60',
                 line='600' if name == 'Title' else '440' if name == 'Heading1' else '360' if name == 'Heading2' else '336',
                 lineRule='exact')
        if name == 'Bullet':
            word(props, 'ind', left='200', hanging='200')
        if name == 'Heading1' and not international:
            word(props, 'ind', left='160')
        word(props, 'contextualSpacing', val='0')
        word(props, 'jc', val='left')
        runs = word(style, 'rPr')
        word(runs, 'rFonts', ascii='Arial', hAnsi='Arial',
             eastAsia='Arial' if international else 'Microsoft YaHei')
        if bold:
            word(runs, 'b')
        if international and name == 'Heading1':
            # Visual uppercase only: ATS text extraction still reads the original heading.
            word(runs, 'caps')
        word(runs, 'color', val=color)
        word(runs, 'sz', val=size)
        word(runs, 'szCs', val=size)

    types = ET.Element('Types', xmlns=CT)
    for extension, content_type in (
        ('rels', 'application/vnd.openxmlformats-package.relationships+xml'),
        ('xml', 'application/xml'),
    ):
        ET.SubElement(types, 'Default', Extension=extension, ContentType=content_type)
    for name, suffix in (('document', 'document.main'), ('styles', 'styles')):
        ET.SubElement(types, 'Override', PartName=f'/word/{name}.xml',
                      ContentType=f'application/vnd.openxmlformats-officedocument.wordprocessingml.{suffix}+xml')

    package_rels = ET.Element('Relationships', xmlns=REL)
    ET.SubElement(package_rels, 'Relationship', Id='rId1', Type=OFFICE + 'officeDocument',
                  Target='word/document.xml')
    doc_rels = ET.Element('Relationships', xmlns=REL)
    ET.SubElement(doc_rels, 'Relationship', Id='rId1', Type=OFFICE + 'styles', Target='styles.xml')
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for path, tree in (
            ('[Content_Types].xml', types), ('_rels/.rels', package_rels),
            ('word/document.xml', doc), ('word/styles.xml', styles),
            ('word/_rels/document.xml.rels', doc_rels),
        ):
            xml = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
            ET.fromstring(xml)  # Reject XML-invalid input before creating the artifact.
            archive.writestr(path, xml)
    return output.getvalue()


def resolved_layout(source, layout=None):
    if layout in (None, 'auto'):
        return 'international' if Path(source).name.lower().endswith('.en.md') else 'standard'
    return layout


def export(source, output=None, *, notes=None, theme='sky', layout=None, page=None):
    source = Path(source)
    target = Path(output) if output is not None else source.with_suffix('.docx')
    if source.suffix.lower() != '.md' or target.suffix.lower() != '.docx':
        raise ValueError('Expected a Markdown resume and a .docx output path.')
    if any(path.is_symlink() for item in (source, target) for path in (item, *item.parents)):
        raise ValueError('Refusing a symlink resume path.')
    items = paragraphs(source.read_text(encoding='utf-8-sig'))
    data = build_docx(items, theme=theme, layout=resolved_layout(source, layout), page=page)
    with ZipFile(BytesIO(data)) as archive:
        document = ET.fromstring(archive.read('word/document.xml'))
        extracted = document_text(document)
        if archive.testzip() or extracted != [visible_text(style, line) for style, line in items]:
            raise ValueError('DOCX verification failed: extracted text differs from the resume.')
    write_new(target, data)
    if notes is not None:
        notes.extend(format_notes(items))
    return target


def converter_path(explicit=None):
    candidates = ([str(explicit)] if explicit else
                  ['soffice', 'libreoffice',
                   '/Applications/LibreOffice.app/Contents/MacOS/soffice',
                   r'C:\Program Files\LibreOffice\program\soffice.exe'])
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    raise ValueError('PDF export requires local LibreOffice. Install it or use '
                     '--converter /path/to/soffice; DOCX export needs no converter. '
                     'You can also open the DOCX in Word and save as PDF.')


def conversion_environment(stage, font_dirs=None):
    """Expose fonts only to this conversion; headless macOS builds may miss system fonts."""
    env = os.environ.copy()
    directories = list(font_dirs or [])
    if sys.platform == 'darwin' and not env.get('FONTCONFIG_FILE'):
        directories.extend(path for path in ('/System/Library/Fonts', '/Library/Fonts')
                           if Path(path).is_dir())
    if not directories:
        return env
    paths = []
    for directory in directories:
        path = Path(directory).expanduser().resolve()
        if not path.is_dir():
            raise ValueError('Font directory does not exist: ' + str(directory))
        if str(path) not in paths:
            paths.append(str(path))
    config = stage / 'fonts.conf'
    # Preserve an explicitly configured font environment without changing it.
    # Otherwise, the configured directories and cache live only in this process.
    inherited = env.get('FONTCONFIG_FILE')
    includes = [inherited] if inherited else []
    config.write_text('<?xml version="1.0"?><fontconfig>' +
                      ''.join('<include ignore_missing="yes">' + escape(p) + '</include>' for p in includes) +
                      ''.join('<dir>' + escape(p) + '</dir>' for p in paths) +
                      '<cachedir>' + escape(str(stage / 'font-cache')) + '</cachedir></fontconfig>',
                      encoding='utf-8')
    env['FONTCONFIG_FILE'] = str(config)
    env['SAL_FONTPATH'] = os.pathsep.join(filter(None, [env.get('SAL_FONTPATH'), *paths]))
    return env


def convert_pdf(source, output=None, *, converter=None, font_dirs=None, timeout=60):
    """Convert the supplied DOCX in an isolated profile; preserve all existing files."""
    source = Path(source)
    target = Path(output) if output is not None else source.with_suffix('.pdf')
    if source.suffix.lower() != '.docx' or target.suffix.lower() != '.pdf':
        raise ValueError('PDF conversion expects a .docx source and a .pdf output path.')
    if any(p.is_symlink() for item in (source, target) for p in (item, *item.parents)):
        raise ValueError('Refusing a symlink resume path.')
    if not source.is_file():
        raise FileNotFoundError(source)
    if target.exists():
        raise FileExistsError('PDF output already exists: ' + str(target))
    executable = converter_path(converter)
    with tempfile.TemporaryDirectory(prefix='career-resume-pdf-') as temporary:
        stage = Path(temporary).resolve()
        env = conversion_environment(stage, font_dirs)
        staged_source = stage / 'resume.docx'
        shutil.copyfile(source, staged_source)
        try:
            result = subprocess.run(
                [executable, '-env:UserInstallation=' + (stage / 'profile').as_uri(),
                 '--headless', '--convert-to', 'pdf:writer_pdf_Export',
                 '--outdir', str(stage), str(staged_source)],
                capture_output=True, timeout=timeout, check=False, env=env)
        except subprocess.TimeoutExpired:
            raise ValueError('Local PDF conversion timed out; no PDF was saved. '
                             'The source DOCX is preserved.') from None
        pdf = stage / 'resume.pdf'
        if result.returncode or not pdf.is_file():
            raise ValueError('Local PDF conversion failed; no PDF was saved. '
                             'Check that LibreOffice can open the source DOCX.')
        raw = pdf.read_bytes()
        if not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-1024:]:
            raise ValueError('Converter output is not a complete PDF; no PDF was saved.')
        write_new(target, raw)
    return target


def render_pdf(docx, *, converter=None):
    """Return a PDF download from the exact DOCX bytes used by the editor."""
    with tempfile.TemporaryDirectory(prefix='career-resume-download-') as temporary:
        source = Path(temporary).resolve() / 'resume.docx'
        source.write_bytes(docx)
        return convert_pdf(source, converter=converter).read_bytes()


def export_formats(source, output=None, *, format='docx', converter=None, font_dirs=None, **options):
    """Share the same verified DOCX pipeline for both languages and all formats."""
    source = Path(source)
    if format not in ('docx', 'pdf', 'all'):
        raise ValueError('Choose docx, pdf or all for the export format.')
    if source.suffix.lower() == '.docx':
        if format != 'pdf':
            raise ValueError('An existing DOCX supports --format pdf; use Markdown for docx/all.')
        return [convert_pdf(source, output, converter=converter, font_dirs=font_dirs)]
    if format == 'docx':
        return [export(source, output, **options)]
    # Resolve prerequisites and collisions before creating any exported files.
    converter_path(converter)
    pdf = Path(output) if output is not None else source.with_suffix('.pdf')
    if pdf.suffix.lower() != '.pdf':
        raise ValueError('PDF export expects a .pdf output path.')
    targets = [pdf] + ([pdf.with_suffix('.docx')] if format == 'all' else [])
    for target in targets:
        if any(p.is_symlink() for p in (target, *target.parents)):
            raise ValueError('Refusing a symlink resume path.')
        if target.exists():
            raise FileExistsError('Resume output already exists: ' + str(target))
    if format == 'all':
        docx = export(source, pdf.with_suffix('.docx'), **options)
        try:
            convert_pdf(docx, pdf, converter=converter, font_dirs=font_dirs)
        except (ValueError, OSError) as exc:
            raise ValueError(f'{exc} Verified DOCX retained at: {docx}') from exc
        return [docx, pdf]
    with tempfile.TemporaryDirectory(prefix='career-resume-export-') as temporary:
        docx = export(source, Path(temporary).resolve() / 'resume.docx', **options)
        return [convert_pdf(docx, pdf, converter=converter, font_dirs=font_dirs)]


def add_arguments(parser):
    parser.add_argument('resume', type=Path, nargs='?')
    parser.add_argument('--output', type=Path, help='New output path; for all, specify the PDF path')
    parser.add_argument('--format', choices=('docx', 'pdf', 'all'), default='docx',
                        help='DOCX needs only Python; PDF/all also need local LibreOffice')
    parser.add_argument('--converter', help='Local soffice executable for PDF conversion')
    parser.add_argument('--font-dir', type=Path, action='append', default=[],
                        help='Additional local font directory for PDF conversion; repeat as needed')
    parser.add_argument('--theme', choices=tuple(THEMES), default='sky', help='Section heading color theme')
    parser.add_argument('--layout', choices=('auto', *LAYOUTS), default='auto',
                        help='auto: resume.en.md uses international; other names use standard')
    parser.add_argument('--page', choices=tuple(PAGES),
                        help='Page size; defaults to A4 for standard and US Letter for international')
    parser.add_argument('--list-themes', action='store_true', help='List available themes without reading a resume')
    return parser


def run(args, *, base=None):
    if args.list_themes:
        for key, palette in THEMES.items():
            print(f'{key}: {palette["name"]} | #{palette["accent"]} / #{palette["background"]}')
        return 0
    if args.resume is None:
        return fail(ValueError('Provide a Markdown resume or use --list-themes.'))
    if base is not None:
        args.resume = Path(base) / args.resume
        if args.output is not None:
            args.output = Path(base) / args.output
        args.font_dir = [Path(base) / path for path in args.font_dir]
    notes = []
    try:
        outputs = export_formats(args.resume, args.output, format=args.format,
                                 converter=args.converter, font_dirs=args.font_dir, notes=notes, theme=args.theme,
                                 layout=args.layout, page=args.page)
    except (ValueError, OSError, ET.ParseError) as exc:
        return fail(exc)
    for output in outputs:
        print('Created ' + output.suffix[1:].upper() + ': ' + str(output))
    if args.resume.suffix.lower() == '.docx':
        print('Source: existing DOCX; original layout preserved.')
    elif resolved_layout(args.resume, args.layout) == 'international':
        print('Layout: international (ATS-friendly, monochrome, uppercase section rules); '
              'theme colors ignored')
        print('Page: ' + (args.page or 'letter'))
    else:
        print('Theme: ' + THEMES[args.theme]['name'] + ' (' + args.theme + ')')
        if args.page:
            print('Page: ' + args.page)
    for note in notes:
        print('NOTE: ' + note)
    print('DOCX exports verify text order and package integrity. Review rendered pages, '
          'fonts and contact details; PDF conversion does not verify visual layout or ATS behavior.')
    return 0
