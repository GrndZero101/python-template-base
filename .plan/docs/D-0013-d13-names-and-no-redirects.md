---
id: D-0013
title: 'D13: Names, and no redirects'
kind: adr
status: approved
tasks:
- T-0013
created_at: '2026-11-22T21:44:53Z'
updated_at: '2026-11-22T21:46:03Z'
---

Decided 2026-10-15.

This repo is `python-template-base`; use cases are `python-template-cli-typer`, `-cli-stdlib`,
`-api-fastapi`, and `js-template-web-vue` for a Vue front end. uv scripts with PEP 723 metadata are
a **skill in the base** (`python-uv-script`), not a repo. Each use case gets a public
`python-canary-<use case>`; the base gets `python-canary-base` only once it has the uv-script skill
to exercise.

The sole user is the author, so renames break cleanly: every reference is updated, and nothing may
rely on GitHub's redirect from an old name. "Dogfood" is retired. Renaming a local directory moves
the Claude Code memory directory too, which is keyed on the path, and leaves `.venv` pointing at the
old path (`rm -rf .venv && uv sync`).
