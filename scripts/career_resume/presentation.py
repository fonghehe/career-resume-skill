"""Shared exact palettes and optional profession-neutral presentation records."""

from career_resume import ROOT
import json
from pathlib import Path
import re

CONFIG = json.loads((ROOT / 'assets/themes/palette.json').read_text(encoding='utf-8'))
THEMES = CONFIG['themes']
NEUTRAL = CONFIG['neutral']


def theme_colors(theme):
    if not isinstance(theme, str) or theme not in THEMES:
        raise ValueError('Unknown resume theme; choose: ' + ', '.join(THEMES))
    if any(not isinstance(v, str) or not re.fullmatch(r'[0-9A-F]{6}', v)
           for v in (THEMES[theme]['accent'], THEMES[theme]['background'], *NEUTRAL.values())):
        raise ValueError('Palette colors must be explicit six-digit uppercase HEX values')
    return THEMES[theme]


def technical_view(data):
    """Technical categories require an explicit choice or actual code evidence."""
    view = data.get('presentation', {})
    if 'technical' in view:
        return view['technical']
    return bool(data.get('repositories') or data.get('gitEvents') or
                any(row.get('svnWorkingCopy') for row in data.get('projects', [])))


def validate_presentation(data):
    view = data.get('presentation', {})
    if not isinstance(view, dict):
        raise ValueError('presentation must be an object')
    theme_colors(view.get('theme', 'sky'))
    for key in ('profession', 'careerTitle', 'projectsTitle', 'projectsIntro'):
        if key in view and not isinstance(view[key], str):
            raise ValueError('presentation.' + key + ' must be a string')
    if 'technical' in view and type(view['technical']) is not bool:
        raise ValueError('presentation.technical must be a boolean')
    sections = view.get('sections', [])
    if not isinstance(sections, list) or len(sections) > 24:
        raise ValueError('presentation.sections must be an array of at most 24 modules')
    seen = set()
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get('id'), str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,47}', section['id']):
            raise ValueError('Presentation module requires a short lowercase ID')
        if section['id'] in seen or section['id'] in {'career', 'projects', 'repositories'}:
            raise ValueError('Presentation module ID must be unique and not reserved')
        seen.add(section['id'])
        if not isinstance(section.get('title'), str) or not section['title'].strip():
            raise ValueError('Presentation module title is required')
        if not isinstance(section.get('items'), list) or len(section['items']) > 100:
            raise ValueError('Presentation module items must be an array of at most 100 records')
        for item in section['items']:
            if not isinstance(item, dict) or not isinstance(item.get('title'), str) or not item['title'].strip():
                raise ValueError('Presentation item title is required')
            for key in ('subtitle', 'period', 'summary'):
                if key in item and not isinstance(item[key], str):
                    raise ValueError('Presentation item ' + key + ' must be a string')
            for key in ('bullets', 'factIds'):
                if key in item and (not isinstance(item[key], list) or any(not isinstance(v, str) for v in item[key])):
                    raise ValueError('Presentation item ' + key + ' must contain strings')
    order = view.get('order', [])
    if not isinstance(order, list) or any(not isinstance(v, str) for v in order):
        raise ValueError('presentation.order must contain module IDs')
    if len(order) != len(set(order)) or set(order) - (seen | {'career', 'projects', 'repositories'}):
        raise ValueError('presentation.order contains duplicate or unknown modules')
    return view


def profession_modules(data):
    """Render only populated plain-text modules, escaping all material as data."""
    from html import escape
    view = validate_presentation(data)
    modules, links = [], []
    for section in view.get('sections', []):
        if not section['items']:
            continue
        identity = 'professional-' + section['id']
        items = []
        for item in section['items']:
            fields = [f'<h3>{escape(item["title"])}</h3>']
            for key in ('subtitle', 'period', 'summary'):
                if item.get(key):
                    fields.append('<p>' + escape(item[key]) + '</p>')
            if item.get('bullets'):
                fields.append('<ul>' + ''.join('<li>' + escape(line) + '</li>' for line in item['bullets']) + '</ul>')
            items.append('<article class="professional-item">' + ''.join(fields) + '</article>')
        title = escape(section['title'])
        modules.append(f'<details class="panel module" id="{identity}" open><summary class="module-summary"><h2>{title}</h2></summary><div class="module-content">' + ''.join(items) + '</div></details>')
        links.append(f'<a href="#{identity}">{title}</a>')
    return ''.join(modules), ''.join(links)
