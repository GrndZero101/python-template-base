---
id: D-0017
title: 'D17: CI is a question, and optional'
kind: adr
status: approved
tasks:
- T-0020
created_at: '2026-11-22T21:44:58Z'
updated_at: '2026-11-22T21:46:03Z'
---

Decided 2026-10-18.

The base asks `ci`: `none` (the default) or `github`. The author will use the template where there
is either no CI or GitLab CI, so GitHub Actions cannot be assumed. `none` renders nothing, which
leaves a project free to add its own CI without conflicting on `copier update`. `github` renders one
thin `.github/workflows/ci.yml` that runs `prek run --all-files` and `uv run pytest` and nothing
else, so the logic stays in the gate and another host costs only a short file. Linux only, with
macOS and Windows commented in, on pushes to `main` and pull requests: a Free account's private repo
has 2,000 minutes a month, and macOS burns them at about ten times Linux.

The CLI layer asks `ci` too, because its task applies the base with `--defaults`: a question only
the base asked would never reach a CLI user. The workflow is literal (its `${{ }}` would read as
Jinja); the condition is in its directory's name. `gitlab` is a later choice: nothing here can test
it.
