---
id: D-0015
title: 'D15: The base on its own, and in a brownfield repo'
kind: adr
status: approved
tasks:
- T-0009
- T-0015
created_at: '2026-11-22T21:44:55Z'
updated_at: '2026-11-22T21:46:03Z'
---

Decided 2026-10-15.

The base is a use case in itself: a skeleton with every guard, for prototyping before the shape is
known, or dropped into a brownfield repo with the least disruption.

**Who owns `pyproject.toml`.** The use case, when layered. The base renders a minimal one under
`_skip_if_exists`, which copier never overwrites and leaves out of the update patch, so the
ownership check exempts it. Ruff is the only tool that merges configs: the use case writes
`extend = "ruff-base.toml"` and then **only additive keys** (`extend-select`,
`extend-per-file-ignores`, `extend-exclude`), because `select`, `ignore`, `per-file-ignores` or
`unfixable` would replace the base's lists. pytest, ty and rumdl take the first config file they
find and merge nothing, so their config stays in `pyproject.toml`, guarded by a contract test.

**Order, and the shared questions.** One `copier copy` of the use case, whose only task runs
`copier copy --trust --defaults` of the base; the base owns every bootstrap task. The base defines
the shared questions with `default: "{{ _external_data.use_case.<key> | default('') }}"`, so
layered under `--defaults` it asks nothing and standalone it asks everything. The base's source is
an answer in the use case (`base_template`), so tests and CI can point it at a checkout. A test
asserts both answers files agree on the shared questions. (On copy, copier reads last answers from
`.copier-answers.yml`, never the template's `_answers_file`, so the base's copy already sees the use
case's answers; whether the `_external_data` defaults still earn their place is an open task.)

**Applying the base to an existing repo** is a `copy`, so every task runs: `git init`, `uv sync`,
`git add -A`, `git commit` on whatever branch is checked out, and the `prek install`s.
`copier copy --skip-tasks` avoids it, followed by the tasks by hand; the README documents it. A
`bootstrap_git` question only if brownfield adoption becomes real.

**Brownfield gating.** `finish_branch.py` runs `prek run --all-files`, and `ty` checks the whole
project whatever files it is given, so the gates would fail a legacy codebase at the first save. No
machinery until that reaches `main`; then a `--changed-only` flag on `finish_branch.py` reusing
`stop_gate.changed_files`, and `exclude` lists in the ty and rumdl config the adopter can edit.
