---
id: D-0019
title: 'D19: ty is a local hook'
kind: adr
status: approved
tasks: []
created_at: '2026-11-22T21:45:00Z'
updated_at: '2026-11-22T21:45:01Z'
---

Decided 2026-10-16.

ty runs as a local hook, `uv run --with ty ty check`, in the template and at the root, not through
ty-pre-commit. That hook runs uv's preview `uv check`, which skips every file with a PEP 723 header
and forwards no flag, so a uv script (and the root's `bootstrap.py`) was never type-checked. The
per-script alternative, `uv check --script`, takes one file and checks an environment `uv run`
syncs inexactly. A generation test proves the swap: a script in `scripts/` with a type error fails
the gate.
