# career-resume-skill · Career Records and Resumes

[中文](README.md) · English · [Documentation](https://fonghehe.github.io/career-resume-skill/) · [GitHub](https://github.com/fonghehe/career-resume-skill) · [MIT](LICENSE)

**Build a complete career record first, then derive general or job-targeted resumes from it.**

Start with your account of your experience, an old resume or project materials. Keep employment, education, responsibilities, skills and results together with sources and uncertainty. The agent maintains the complete record and selects supported facts for each resume version. A job description, existing resume and source repositories are optional.

After years of programming, project details can be scattered across old resumes, repositories, documents and memory. Start with one project you remember, recover the problems, responsibilities and decisions, then review how your work changed across projects. You can maintain this record even when you are not looking for a job. See [reviewing past projects](docs/guide/review-career.md) (Chinese).

## Start

Download or clone the full project and open it in a file-capable agent. Provide your experience or put an old resume in `local/private/resume.pdf`, then send:

```text
Read this project's SKILL.md.
My experience materials are [text or actual path].
Build a complete written career record with employment, education, projects and skills.
Preserve sources, responsibility boundaries and unknowns.
Deliver the written record and its maintained source files; ask a few key questions.
Write my records in English.
```

Python 3.9+ is required for core tools; Git collection needs Git. Attachment extraction depends on your host. You can start without repository code.

## Multi-agent access

The shared entry uses the Agent Skills format. Use the ecosystem installer to select multiple agents, target any host skill directory, import a ZIP, or ask a file-capable agent to read `SKILL.md`. Adding a host does not require rewriting the workflow.

```sh
# Ecosystem installer: select one or more agents (requires Node.js/npm and network)
python3 scripts/package.py --public-dir local/dist/ecosystem/career-resume-skill
npx skills add ./local/dist/ecosystem/career-resume-skill --skill career-resume-skill --copy

# Any host with a local skill directory
python3 scripts/install_skill.py --skills-dir /absolute/path/host-skills

# Any host that accepts this import layout
python3 scripts/install_skill.py --output local/dist/career-resume-skill-import.zip
```

For hosts that read project `.agents/skills/`, use `--project /absolute/path/my-career`. Codex, Claude Code, Trae and WorkBuddy shortcuts remain available as examples. The installer copies only public resources and blank records, refuses existing destinations, and supports `--dry-run`.

Specify your private workspace path and use its files and scripts. See [multi-agent setup](docs/guide/using-skill.md) and [custom/cloud integration](docs/reference/compatibility.md) (Chinese). Client discovery and execution need host testing; a common format alone does not establish compatibility.

## Two-stage delivery

| Stage | Deliverables |
|---|---|
| Career record | Maintained files under `local/references/`, an entry at `career/README.md`, and a complete written artifact at `local/output/career/career.md` |
| Resume | `local/output/resumes/YYYY-MM-DD-direction/resume.en.md` or `resume.zh-CN.md`, plus `match-report.md` with claim-to-fact mappings, selection decisions and gaps |

Ask for a general resume in your chosen direction, or provide a JD for a targeted version. The full career record is preserved. New facts enter the record before a revised resume is generated. Word/PDF and interview materials are available on request, subject to actual host tools.

See [quick start](docs/guide/quick-start.md), [ongoing updates](docs/guide/update-career.md), [resume generation](docs/guide/generate-resume.md) and [directory layout](docs/reference/directories.md) (Chinese).

## Optional offline overview

- Employers with internal department, role and grade stages grouped together.
- Project responsibilities, milestones, associated repositories and commit counts.
- Author-matched repository activity dates and totals.
- Expandable commit details with subject, SHA, Author Date and Committer Date.

Open `local/showcase/project-timeline.html`; written records start at `local/references/career/README.md`. Reuse the same directory for later updates. Application resumes and interview content are optional derived outputs.

The [first career guide](docs/guide/first-library.md) and [demo](docs/example.md) are in Chinese. The fictional demo has 2 employers, 3 employment/grade stages, 3 projects, 3 repositories and 14 author-matched commits. All grades, dates and commits are explicitly invented for demonstration.

## Preview

```sh
python3 scripts/create_demo.py
```

Open `local/output/demo/showcase/project-timeline.html`. Existing output is preserved; choose a new `--output` directory when needed.

## Data and maintenance

Personal files and generated records use ignored directories. Keep `assets/starter/` empty. Git ignores do not remove tracked files or history. Commit dates and counts describe code activity, not employment, launch dates, grade or independent impact.

See [capabilities](docs/reference/capabilities.md), [interview preparation](docs/guide/prepare-interview.md), [tools](docs/reference/commands.md), [data format](docs/reference/data-model.md), [compatibility](docs/reference/compatibility.md) and [privacy](docs/guide/privacy.md).

```sh
python3 scripts/check.py
pnpm install --frozen-lockfile
pnpm docs:build
```

Utilities use the Python standard library. Regression tests need Git; the optional tutorial site needs Node.js 22+ and pinned pnpm. Tool tests do not establish host/model behavior.

Public export uses blank records and an explicit file inventory. Personal ZIP backups include selected Markdown, JSON and HTML; attachments, source repositories and output need separate backups. [Releasing](docs/maintainers/releasing.md) · [Contributing](.github/CONTRIBUTING.md) · [Code of conduct](.github/CODE_OF_CONDUCT.md) · [Security](.github/SECURITY.md).

MIT covers generic code and templates, not personal or third-party records stored alongside them.

## Everyday updates

Ask the agent to update recent Git activity while preserving confirmed facts, map directories in a monorepo to different projects, propose stages using README/tags/changed files, attach a screenshot, or share only selected projects. The page filters all sections by company/year and expands sources and activity statistics on demand. Its download button creates a standalone sharing copy; review retained text and optional attachments before sharing. See [maintenance and sharing](references/enhancements.md) for tool contracts.

## Directory layout

`docs/guide/` holds tutorials, `docs/reference/` holds command and data contracts, and `docs/maintainers/` holds project maintenance guidance. Agent rules live in `references/`, reusable templates in `assets/templates/`, and blank workspace files in `assets/starter/`. Fictional text examples are grouped under `assets/examples/resume-demo/`; offline-page fixtures use `assets/examples/career-demo/`. Initialization also provides `local/README.md` as a workspace guide. Tests and behavioral scenarios live together in `tests/`; GitHub community files and workflows live in `.github/`. Personal files and generated artifacts are consolidated in ignored `local/`, including references, data, private attachments, showcase, output and dist. Legacy datasets remain readable.
