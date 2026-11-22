---
id: D-0021
title: 'D21: The base layer is updated first'
kind: adr
status: approved
tasks: []
created_at: '2026-11-22T21:45:03Z'
updated_at: '2026-11-22T21:45:03Z'
---

Decided 2026-10-17.

A project's two layers are updated base first, then the use case: in the READMEs' manual flows, the
generated README's, and `bootstrap.py`'s `ANSWERS_FILES`. The canary's first run of the helper
failed the other way round: the use case raised uv's `required-version` before the base raised the
`uv-pre-commit` rev, so the `uv-lock` hook's uv was refused. D16 removed that pin, and the reason
that remains is general: the use case is written against the base, so the base must be in place
first. Each layer is a separate commit, since copier refuses a dirty tree.
