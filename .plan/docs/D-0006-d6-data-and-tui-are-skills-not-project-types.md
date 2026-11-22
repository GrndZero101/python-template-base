---
id: D-0006
title: 'D6: Data and TUI are skills, not project types'
kind: adr
status: approved
tasks: []
created_at: '2026-11-22T21:44:45Z'
updated_at: '2026-11-22T21:44:46Z'
---

Decided 2026-10-05.

`data` (polars, duckdb) and `tui` (Textual) are recipe-first skills layered on the CLI scaffold,
shipped to every project, not project types. Each ships reference code that a generation test copies
exactly as the recipe says, registers in `cli.py` and gates. This makes D7, their order, moot.
