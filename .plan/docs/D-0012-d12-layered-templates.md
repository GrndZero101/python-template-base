---
id: D-0012
title: 'D12: Layered templates'
kind: adr
status: approved
tasks: []
created_at: '2026-11-22T21:44:52Z'
updated_at: '2026-11-22T21:44:52Z'
---

Decided 2026-10-15.

A shared base template plus one thin template per use case, applied to the same project with
separate answers files, as copier documents. A spike with two local templates proved it: one
`copier copy` of the use case produced both layers, its task running `copier copy` of the base; the
base read the use case's answers through `_external_data`; `copier update -a
.copier-answers.base.yml` and a plain `copier update` each touched only their own layer; a local
edit survived.

**No update chain**: a project records both sources, so a base fix reaches it without a use-case
release.

Costs: an update is two commands, each needing a clean tree. A file both layers render conflicts
(proven: markers in `pyproject.toml`), so ownership must be disjoint and checked, which the CLI
repo's suite does. Only ruff can extend a base-owned config, so pytest, ty and rumdl config and the
dev group repeat in each use case's `pyproject.toml` (D15). The base's CI must run every use case's
suite. Rules split as `CLAUDE.md` (base) plus `.claude/rules/<use case>.md`, which Claude Code loads
at the same priority.

Rejected: copying `tools/` per repo (drift), and vendoring the base into each use case as a subtree
(a real update chain). The base is updated first: D21.
