#!/usr/bin/env python3
"""Export selected factual summaries as a standalone sharing copy; never publish."""
from career_resume import ROOT
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path

from career_resume.build_timeline import build_project_details, render_html, validate_data
from career_resume.career_data import checked_local, project_ids, activity
from career_resume.cli_support import fail
from career_resume.file_io import write_new



def share_data(data, selected, *, name='', keep_companies=False):
    validate_data(data)
    selected = set(selected)
    if not selected or not selected <= {p['id'] for p in data['projects']}:
        raise ValueError('Select at least one existing project.')
    company_names = sorted({p.get('groupOrganization', p['organization']) for p in data['projects'] if p['id'] in selected})
    aliases = {c: c if keep_companies else f'公司 {i+1}' for i, c in enumerate(company_names)}
    career = []
    for item in data['career']:
        company = item.get('groupOrganization', item['organization'])
        if company not in aliases:
            continue
        row = {k: copy.deepcopy(item[k]) for k in ('id', 'role', 'level', 'start', 'end', 'summary') if k in item}
        row['organization'] = aliases[company]
        if item.get('groupOrganization'):
            row['groupOrganization'] = aliases[company]
        career.append(row)
    projects = []
    for item in data['projects']:
        if item['id'] not in selected:
            continue
        row = {k: copy.deepcopy(item[k]) for k in ('id', 'name', 'category', 'status', 'start', 'end', 'tech', 'highlights', 'summary', 'nature') if k in item}
        row['organization'] = aliases[item.get('groupOrganization', item['organization'])]
        row['milestones'] = [{k: m[k] for k in ('date', 'title', 'summary', 'status') if k in m} for m in item.get('milestones', [])]
        projects.append(row)
    repos = []
    for repo in data['repositories']:
        linked = set(project_ids(repo)) | set(repo.get('projectCounts', {}))
        ids = linked & selected
        if not ids:
            continue
        events = [e for e in data.get('gitEvents', []) if e['repository'] == repo['name']]
        included = [e for e in events if set(project_ids(e)) & selected]
        complete = len(events) == repo['count']
        # Overlapping project counts cannot be summed without the full commit set.
        if complete:
            count = len(included)
            monthly = activity(included)['monthly']
        elif linked <= selected:
            count = repo['count']
            monthly = repo.get('activity', {}).get('monthly', {})
        elif len(ids) == 1 and next(iter(ids)) in repo.get('projectCounts', {}):
            count = repo['projectCounts'][next(iter(ids))]
            monthly = {}
        else:
            raise ValueError('Import complete records before sharing a subset of a shared repository.')
        if not count:
            continue
        counts = {pid: sum(pid in project_ids(e) for e in included) if complete else repo.get('projectCounts', {}).get(pid, count)
                  for pid in ids}
        repos.append({'name': f'仓库 {len(repos)+1}', 'group': '所选项目代码活动', 'start': repo['start'], 'end': repo['end'],
                      'count': count, 'projectIds': sorted(ids), 'projectCounts': counts,
                      'activity': {'monthly': monthly}, 'firstMessage': '', 'lastMessage': ''})
    starts = sorted(c['start'] for c in career if c.get('start'))
    ends = sorted(c['end'] for c in career if c.get('end'))
    result = {'meta': {'title': (name + ' · ' if name else '') + '项目履历 · 分享版',
                       'subtitle': '所选项目与任职阶段摘要；不含来源原文、邮箱、仓库路径和提交明细。',
                       'updatedAt': data['meta']['updatedAt'], 'synthetic': data['meta'].get('synthetic', False)},
              'profile': {'headline': '所选项目概览', 'careerStart': starts[0] if starts else '', 'careerEnd': ends[-1] if ends else ''},
              'leadership': {'phases': [], 'metrics': [], 'responsibilities': [], 'copilot': [], 'boundary': ''},
              'career': career, 'projects': projects, 'repositories': repos, 'gitEvents': []}
    validate_data(result)
    return result


def share_details(data, root=None, *, original=None, include_attachments=False):
    details = {}
    for p in data['projects']:
        markdown = f"# {p['id']}｜{p['name']}\n\n## 项目概述\n{p.get('summary', '')}\n\n## 关键工作\n"
        markdown += '\n'.join('- ' + value for value in p['highlights'])
        details[p['id']] = {'path': '', 'markdown': markdown,
                           'capabilities': {key: [] for key in ('frontend', 'backend', 'integration', 'collaboration', 'business')},
                           'attachments': original[p['id']].get('attachments', []) if include_attachments else []}
    return details


def export(root, selected, output=None, *, name='', keep_companies=False, include_attachments=False):
    from career_resume.career_data import profile_root
    root = profile_root(root)
    source = json.loads(checked_local(root, 'data/timeline.json').read_text())
    data = share_data(source, selected, name=name, keep_companies=keep_companies)
    original = build_project_details(source, root) if include_attachments else None
    details = share_details(data, original=original, include_attachments=include_attachments)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target = Path(output) if output else root / 'output/shares' / f'career-{stamp}.html'
    if not target.is_absolute():
        target = root / target
    if not target.resolve().is_relative_to(root / 'output') or any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError('Sharing copy must be a new file under workspace/output/.')
    target.parent.mkdir(parents=True, exist_ok=True)
    write_new(target, render_html(data, details).encode('utf-8'))
    return target


def main(argv=None, *, root=ROOT):
    parser = argparse.ArgumentParser(prog='career.py share', description=__doc__)
    parser.add_argument('--workspace', type=Path, default=root)
    parser.add_argument('--project', required=True, action='append', help='Explicitly selected project ID')
    parser.add_argument('--name', default='', help='Optional display name for this copy')
    parser.add_argument('--keep-company-names', action='store_true')
    parser.add_argument('--include-attachments', action='store_true', help='Only after reviewing images/documents for sharing')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        print(export(args.workspace, args.project, args.output, name=args.name,
                     keep_companies=args.keep_company_names, include_attachments=args.include_attachments))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return fail(exc)
