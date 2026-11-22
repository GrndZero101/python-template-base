---
id: D-0023
title: Spec runs
kind: note
status: approved
tasks:
- M-0004
- T-0010
created_at: '2026-11-22T21:45:05Z'
updated_at: '2026-11-22T21:46:03Z'
---

The benchmark of a model building on the typer scaffold (D2). The procedure is the CLI repo's
`examples/README.md`; the review is driven by `examples/evaluate.md` there. Rerun after any change
to what a skill or the gate tells a model; that is a task. Each finding becomes a task, checked
against the code first.

| Date | Spec | Model | Template | Gate | Tests | `/cost` | Verdict and main findings |
|---|---|---|---|---|---|---|---|
| 2026-10-03 | geo | haiku | `354b24f` | pass | 215 pass | 68 calls, 26k out | Two required tests wrong or missing. Never loaded `python-cli-modern`: hand-rolled `httpx.Client()`, patched httpx in every test, no response model, cause dropped on exit. |
| 2026-10-03 | geo | sonnet | `354b24f` | pass | 212 pass | 9 calls, 10k out | Meets every row. Loaded the skill second, copied `http_client.py`, `MockTransport` throughout. Wrote every file through one heredoc. |
| 2026-10-03 | geo | haiku | `f6c03ff` | pass | pass | 68 calls, 31k out | Close. Found `build_client` through `CLAUDE.md` and copied it. Still never loaded the skill: parsed the response by hand, reported `exc.request.url` instead of the cause. |
| 2026-10-03 | currency | sonnet | `2b06886` | pass | 276 pass | 15 requests, 17.7k out, $0.65 | Meets the spec, every value a `Decimal`. Branched unprompted, `Annotated` throughout. 8 of 11 writes were Bash; validated arguments by hand as `str`; mocked a "missing key" the service answers with a 404; `finish_branch.py` failed twice on a dirty tree. All seven findings acted on. |
| 2026-10-05 | spend | sonnet | `73933c1` | pass | 283 pass | 14 calls, 35k out | Meets the spec. Loaded `python-data` first, unprompted, then `python-cli-modern`; branched first; left the work on its branch and said so. Every write was Bash, so only the stop gate ran. Read columns by name, sidestepping the skill's positional `scan_csv(schema=)` — fixed. Three fix rounds, none template defects: `ty` on `Series.sum()`'s broad return type, `PLR0917`/`PLR0913` on a seven-parameter command (`*` and a commented `noqa`), and a rich title wrapping at 80 columns under a substring assert. |
| 2026-10-05 | logs | sonnet | `15ed246` | pass | pass | 10 calls, 32k out | Meets the spec. Loaded `python-tui` unprompted; branched first; finished with `finish_branch.py`. Every write was Bash. Logic outside the app, `.tcss` styles, letters typed in search tested not to fire bindings. Patched its own `run_screen` seam in the command tests — beyond `CLAUDE.md`'s one sanctioned patch, and it said so. Fixed: `run_screen` is in the reference and named beside `build_client`. |

What the runs taught: the skill's content works and its discovery is weak below sonnet; sonnet
writes through Bash as a habit, so the backstops matter more than the edit-time gate; and specs and
API docs are unreliable about failures, so the recipe says to provoke each one live. A specific,
greppable name in `CLAUDE.md` (`build_client`) steered haiku where a docstring pointer did not.
Convention messages that name the reference file to copy reached haiku, which never loaded the
skill on its own.
