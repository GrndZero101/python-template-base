---
id: D-0002
title: 'D2: Spec runs by hand, sonnet the baseline'
kind: adr
status: approved
tasks:
- M-0004
created_at: '2026-11-22T21:44:41Z'
updated_at: '2026-11-22T21:46:03Z'
---

Decided in phases 1–6 (2026-10).

Spec runs are run by hand: a fresh project, a spec handed unedited to a model, the gate and tests
run by hand, then a review in a separate `opus` session in plan mode driven by
`examples/evaluate.md` in the CLI repo. Sonnet is the baseline; haiku is an occasional stretch run
whose findings are acted on only when the fix is a cheap mechanical check that helps any model. The
runs so far, and what they taught, are in the note "Spec runs".
