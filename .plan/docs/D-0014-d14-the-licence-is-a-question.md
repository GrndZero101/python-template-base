---
id: D-0014
title: 'D14: The licence is a question'
kind: adr
status: approved
tasks: []
created_at: '2026-11-22T21:44:54Z'
updated_at: '2026-11-22T21:44:55Z'
---

Decided 2026-10-15.

The base asks `license` (MIT default, Apache-2.0, Proprietary) and `copyright_holder` (default
`author_name`; not git config, which copier can read only through an extension each user must
install), and records the year at generation. That takes both halves of copier's "lock a computed
value" recipe, because a `when: false` answer is otherwise dropped from the answers file and
recomputed on every update: `default: "{{ copyright_year | default('%Y' | strftime) }}"`, and the
answers-file template dumping `{{ dict(_copier_answers, copyright_year=copyright_year) |
to_nice_yaml }}`. The Apache text is verbatim from the ASF's, taken from an installed package, not
typed from memory. `license` in `pyproject.toml` is the SPDX id (`LicenseRef-Proprietary` for
Proprietary). A test edits the recorded year and checks an update keeps it.
