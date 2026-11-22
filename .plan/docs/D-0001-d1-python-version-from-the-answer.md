---
id: D-0001
title: 'D1: .python-version from the answer'
kind: adr
status: approved
tasks: []
created_at: '2026-11-22T21:44:40Z'
updated_at: '2026-11-22T21:44:41Z'
---

Decided in phases 1–6 (2026-10-02 to 10-04).

`.python-version` is rendered from the project's Python answer: 3.12 to 3.14, default 3.14. The
same answer (`python_version`) is the floor in `requires-python` and ruff's `target-version`,
so the project's Python is stated once.
