---
id: D-0003
title: 'D3: The git ritual is a script'
kind: adr
status: approved
tasks: []
created_at: '2026-11-22T21:44:42Z'
updated_at: '2026-11-22T21:44:43Z'
---

Decided in phases 1–6 (2026-10).

Finishing a branch is `tools/finish_branch.py`, never a sequence typed by hand: squash, the full
gate, the tests, the message check, then a `--no-ff` merge into `main`. It **trusts no hook**: a
commit made while the git shims were missing ran none, and a rebase runs none, so it runs every
check itself. Since 2026-10-15 the squashed commit keeps each commit's body, in order, and their
trailers once each as the last paragraph (the canary's rename had lost its explanation). The
merge commit keeps the subject alone.
