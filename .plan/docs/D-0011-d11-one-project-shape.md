---
id: D-0011
title: 'D11: One project shape'
kind: adr
status: superseded
tasks: []
created_at: '2026-11-22T21:44:51Z'
updated_at: '2026-11-22T21:44:51Z'
---

Decided 2026-10-05; superseded across repos by D12.

`project_type` branched `copier.yml`, `pyproject.toml`, the README and the tests, and the three
unbuilt types' skills rotted unexercised: every one broke on a first attempt. So there was one
shape, the typer CLI. Layering directories for two CLI scaffolds was rejected: `_exclude` matches
rendered paths, so same-named modules needed Jinja-named directories, which the 2026-10-05 attempt
showed to be unreadable.
