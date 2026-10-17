# TODO

Outstanding work, with enough context to pick up cold in a new session. Rules and workflow live in
[CLAUDE.md](CLAUDE.md); this file is what is *not yet done*, plus the lessons from what is that a
new session would otherwise relearn. The detail of finished work is in `git log`.

## Next up

**The setup helper is closed** (2026-10-18): step 4 below, the canary's update through it, is
done and pushed. **The next step is not chosen yet.** The candidates already in this file are
phase 10's "Later in the phase" (`python-canary-base` to exercise the uv-script skill, and
`python-template-cli-stdlib` seeded from `archive/cli-stdlib`) and phase 8, which waits behind
phase 10. Ask the author before starting either. The history below stays as the record of how the
helper got here.

**The setup helper's next pieces**, under "Setup helper (after step 9)". The shim, the `uv` pin
in this repo and `doctor` were merged on 2026-10-17, and the pin in the CLI repo the same day
(`db884f7` there: both pyprojects, both setup-uv steps, and
`test_every_copy_of_the_uv_pin_agrees_with_the_base`, which reads this repo's `bootstrap.sh`, so
moving the pin here without the CLI repo fails this repo's CI). `setup`, `new` and `pins` were
merged later that day; the settings-defaults fix planned with `new` proved unneeded (see "Built so
far"), and `update` after them, and its end-to-end test in the CLI repo on 2026-10-17. Read
"Built so far" there first.

**The canary's first run of the helper failed** (2026-10-17), and that run was discarded: the
canary is back on `main` at `6615e62`, answers at `cf14b42` and `0bd228a`. `update` stopped at the
CLI layer's commit: its `pyproject.toml` raised `required-version` to `>=0.12.24`, while the
project's `.pre-commit-config.yaml` — the base's, not yet updated — still had `uv-pre-commit` at
`0.12.22`, so the `uv-lock` hook's uv was refused. The floor and the hook's `rev` are copies of
one pin held by **different layers**, and updating the use case first raises the floor before the
rev. That happens on every pin move, whatever the floor. The end-to-end test missed it because
its snapshots add a marker line and never move the pin. Nothing recorded why the use case went
first. Each step in its own session, in this order:

1. [x] **Update the base first** (2026-10-17, both repos). `ANSWERS_FILES` in `bootstrap.py` and
   its tests, both READMEs' manual flows (each now says why), the generated `README.md.jinja`'s,
   and the end-to-end test's expected commit order. Base first keeps the rev at or above the floor
   at every step, the invariant the base's agreement test already asserts. **Not done: moving the
   pin in the end-to-end test's snapshots.** CI's uv *is* the pin, so the test could reproduce the
   failure only by generating at a version below the pin and updating to it. That needs a
   hard-coded earlier version with a `uv-pre-commit` tag, one more copy for every pin move. Moot
   after step 2, which leaves no pin to move.
2. [x] **Unpin uv** (D16), both repos, base first. **The base half is merged** (2026-10-18,
   branch `build/unpin-uv`). Pushing it alone would fail the base's CI on the CLI's
   `test_every_copy_of_the_uv_pin_agrees_with_the_base`, which read the base's `UV_VERSION`. What
   landed:
   - The shim installs with the unversioned installer (consent kept) and runs `uv self update >&2`
     on every run, unasked; a failure is still `not_standalone`. `UV_VERSION`, `older_than` and
     `awk` are gone. The stub-`uv` tests are now: updated then hands off, the helper's exit code,
     missing without and with `--yes` (curl and wget), and not self-updatable.
   - `pins` and everything only it used (`PinSite`, the site tables, `read_pin`, `resolve_target`,
     `uv_reaches`, `move_uv`, `Probe.fetch`, `UV_RELEASES`, `CLI_REPO_NAME`, `main`'s `root`).
   - `required-version` out of the root `pyproject.toml` and `template/pyproject.toml.jinja`;
     setup-uv's `version` out of both CI steps; a weekly run, Mondays 06:17 UTC.
   - The template's `uv-pre-commit` hook is a local `uv-lock` hook: `uv lock`, `language: system`,
     upstream's `files:` (`^(uv\.lock|pyproject\.toml|uv\.toml)$`) and `pass_filenames: false`.
   - `session_doctor` adds "Worth doing: uv X is behind the latest release, Y. Fix: uv self update"
     from `uv self version --short` and PyPI's JSON, with a 2-second timeout. **Measured**: the hook
     took 0.03 s before and 0.53 s after, online; refused offline it adds nothing; a black-holed
     network costs the full 2 s. Quiet when offline, when PyPI answers oddly, and when either
     version is not plain numbers (a dev build). One `except` per error type, not a tuple: ruff at
     py314 rewrites a tuple to the bare form, a syntax error at the 3.12 floor.
   - The READMEs' and `bootstrap.py`'s reason for base-first is now that the use case is written
     against the base, not the pin.
   - Checked: the root gate, and the CLI suite against this base with `BASE_TEMPLATE_DIR` (43
     passed, the agreement test deselected); `sh bootstrap.sh doctor` for real.

   **The CLI half is merged too** (2026-10-18, `18a8b3b` there): `required-version` out of both
   pyprojects (the root keeps `[tool.uv]` for `package = false`), setup-uv's `version` out of both
   steps, a weekly run at 06:47 UTC on Mondays, the agreement test deleted, and both READMEs'
   base-first reason reworded. Its suite passed against the unpushed base, 43 of 43. Both were
   pushed on 2026-10-18, base first; the base's run passed without a rerun, having checked out the
   CLI's new `main`, pushed seconds after.
3. [x] **Unpin the other tools** (D16), both repos, merged 2026-10-18 from `build/unpin-tools`
   (`62a0e67` here, `d6bac69` there), `main` pushed in both the same day. The branches were pushed first
   and passed CI on Ubuntu and macOS in both repos, proving the `$GITHUB_PATH` step; they are
   deleted from GitHub. Settled by trying each option in a generated project:
   - **Hook revs: local hooks through `uv run --no-project --with <tool>`, no version.** uv
     re-resolves on every run and trusts its cached copy of PyPI's simple page for its
     `max-age=600`, so a release reaches the gate within ten minutes (`-v`: "Found fresh
     response"). Warm, the base's whole gate took 0.21 s against 0.19 s pinned; the first run,
     downloading, 2.4 s. Offline with a stale cache it fails after 4 s of retries, **as the pinned
     `ty==0.0.84` hook already did**: `--with` resolves even an exact pin. `uvx ruff` was rejected:
     it reuses an installed uv tool and never floats; `uvx ruff@latest` hits the network every run.
     Every remote hook is on PyPI (`conventional-pre-commit`, `ruff`, `rumdl`, `shellcheck-py`),
     each now a local hook with its upstream entry, types and `require_serial`, ids unchanged; ty is
     `uv run --with ty`. The gate passed at ruff 0.17.1, ty 0.0.89 and rumdl 0.3.0 with no code
     change, and the commit-msg hook still rejects a bad message.
   - **`prek autoupdate` rejected.** Tried: it moved ruff and rumdl in a project, and the next
     `copier update` merged cleanly only when the base had moved to the **same** tag; the base at
     ruff v0.17.0 against the project's v0.17.1 left conflict markers in
     `.pre-commit-config.yaml`. It also cannot move ty's `==`, and needs a bot to move the base.
   - **prek leaves both dev groups**; CI installs it with `uv tool install` and puts
     `uv tool dir --bin` on `$GITHUB_PATH`, which setup-uv does itself only on Windows.
     Generated projects already ran prek from PATH.
   - **copier cannot leave**: pytest-copie depends on it, and under `uv run` the venv's copier
     shadows the uv tool's, nested `copier copy` tasks included. Its floor is gone from both dev
     groups and CI syncs with `--upgrade` instead of `--locked`, so CI runs the latest copier;
     both locks were upgraded too (copier 9.17.0 to 9.19.1). Locally, `uv lock --upgrade` moves it.
   - **`update` upgrades the uv tools first**, as `setup` does, and stops if one will not
     upgrade, before any copier runs. Two tests.
   - **Unchanged by decision:** a generated project's `uv.lock` and its dev-group floors are its
     own dependencies, not the toolchain, and are not shipped (`uv sync` writes the lock at
     generation, at the latest of everything). The uv-script skill's `exclude-newer` stays: it is
     a standalone script's substitute for a lock. Actions stay pinned by SHA: supply-chain
     hygiene, not the toolchain.
   - **Fixed on the way: the generation suite wrote into this repo's index at commit.** A git
     hook exports `GIT_INDEX_FILE=.git/index`; copier runs `git --git-dir=<temp clone>` from the
     repo root, so its staging of the dirty template landed in **this** repo's index, pointing at
     objects only the clone had. Seen as a failed commit ("invalid object ... for 'TODO.md'") and
     `git fsck` reporting a missing blob; `git rm --cached` and `git add` of the file repaired it.
     Not copier 9.19: 9.17.0 does it too, on a sound index, and a run outside a hook does not.
     Earlier commits likely hit it only in the cache-tree, which the next write rebuilds. Both
     repos' `tests/conftest.py` now drop git's repo-local variables (`git rev-parse
     --local-env-vars`) in `pytest_configure`, from `os.environ` **and** plumbum's `local.env`,
     which copier runs git through and which copied the environment when pytest-copie loaded,
     before any conftest. Verified: the suite under `GIT_INDEX_FILE=.git/index`, then a clean fsck.
   - Checked: the base's whole gate (generation tests included) and the CLI's gate and suite
     against this base, 43 of 43. The CLI repo had **no git shims installed**; `prek install` with
     all three fixed it locally. Pushed on 2026-10-18, the base (`2cab442`) and the CLI straight
     after: the base's run passed with no rerun, both generation jobs having checked out the CLI's
     new `main`, and the CLI's run passed too.
4. [x] **The canary's update, through the helper**, which closes the helper (2026-10-18, from a
   session started in the canary). Run in two passes, because `--finish` merges as soon as the
   last layer commits and leaves no moment to review: first
   `sh ../python-template-base/bootstrap.sh update .` in a real terminal, since copier re-asks
   every question with the recorded answers as defaults and the agent's shell has no TTY. It
   committed both layers on `chore/template-update`, base first: `0bd228a -> 2cab442`, then
   `cf14b42 -> d6bac69`. `git diff main` on both answers files showed `_commit` alone moving, so
   copier answered nothing on its own; the CLI layer's `completion_env_var` is `when: false` and is
   never recorded. Then the same command with `--finish`: both layers `already at`, and
   `finish_branch.py` merged as `afe247a`, pushed. The canary now has no `required-version` and no
   hook `rev`. The base layer's run warns `MissingFileWarning ... .copier-answers.yml` from
   copier's `_user_data.py`, harmlessly: its own answers are in `.copier-answers.base.yml`.

Neither repo pins its toolchain now (after step 3's push): uv, prek, copier and every hook run at
their latest (uv 0.13.1, prek 0.5.5, copier 9.19.1, ruff 0.17.1, ty 0.0.89, rumdl 0.3.0 on
2026-10-18).

Found on the way, not fixed: generating the base alone with a blank `author_name` writes
`Copyright (c) 2026` with a trailing space into `LICENSE`, which `trailing-whitespace` rewrites on
the first gate run. The tests always pass an author, so nothing catches it.

Work runs sequentially, with no worktrees or side tracks. The rest of phase 8 waits behind phase 10
so that nothing under `template/` moves twice.

Running two generation suites at once failed the CLI repo's
`test_generated_project_works_at_the_python_floor` once (2026-10-17); alone, and in a full rerun,
it passed. Run suites one at a time, as "How work runs" already says, before reading a failure as
real.

The state to expect:

- This repo is the base alone: `template/` and the root `copier.yml`. `tests/test_template.py`
  holds three tests, two of which generate the base alone and run its gate (about thirty-five
  seconds together, five when every cache is warm); `uv run pytest` runs them,
  `prek run --all-files` is the whole gate. Finish a branch with
  `uv run python template/tools/finish_branch.py --no-tests "<type(scope): summary>"`.
- The CLI repo is the sibling directory `../python-template-cli-typer`, seeded from this repo's
  history (a plain clone, so every old hash survives). Its suite (44 tests) generates through the
  CLI template with the base layered on; `BASE_TEMPLATE_DIR` names the base checkout, and without
  it the tests use the base on GitHub. It has no `tools/` and no hooks of its own, by decision: the
  root gate there is prek hygiene, ruff, rumdl and the generation tests.
- Each repo's CI checks the other out (`base/` there, `cli/` here) and ignores that directory in
  `.gitignore`, because copier reads an untracked nested repository as a submodule with no
  `.gitmodules` and fails. This repo's CI runs the CLI suite against the commit under test, which
  is now the only automatic check of the hooks, the licence and the update tests.
- Both repos' `main` are pushed. The CLI repo's CI uses the base's GitHub `main`, so push the base
  first whenever a CLI change depends on a base change. A change that must land in both at once,
  such as a shared question's help text, fails the base's CI whichever goes first: that run checks
  out the CLI's `main` before the CLI half is there. Push the CLI half straight after, then
  `gh run rerun <id> --failed` the base's run (2026-10-16, the blank `author_email`).
- Nothing relies on GitHub's redirect from an old name. The canary is
  `GrndZero101/python-canary-cli-typer`, public since 2026-10-15, at `afe247a` (the helper's
  update, "Next up" step 4, pushed 2026-10-18). Its history was rewritten on 2026-10-15 (step 8),
  so canary hashes from before that no longer exist anywhere. `.copier-answers.yml` names
  `gh:GrndZero101/python-template-cli-typer` at `d6bac69`, and `.copier-answers.base.yml` names
  `gh:GrndZero101/python-template-base` at `2cab442`. Its package
  is `python_canary_cli_typer`; its script is still `tdf-cli`. The old `template-dogfood` memory
  directory and `~/.claude.json` entries are gone.
- Renaming the directory left the `.venv` pointing at the old path (`Failed to spawn: pytest`):
  `rm -rf .venv && uv sync` fixed it. Any other clone moved on disk needs the same. pytest's
  assertion-rewrite cache (`tests/__pycache__/*-pytest-*.pyc`) also keeps the old path in the
  locations it reports, until `__pycache__` is deleted: cosmetic.

## How work is judged

- **Three goals** (2026-10-02): well-structured DevOps and QOL CLI tools; code a person can
  maintain and step through; and token efficiency — a sonnet-class model builds a good tool
  cheaply because the skills, tooling and hooks carry the knowledge. **Sonnet is the baseline**;
  haiku is an occasional stretch run whose findings are acted on only when the fix is a cheap
  mechanical check that helps any model.
- **Machinery has a budget** (2026-10-04). `tools/` is eleven modules and about 2,000 lines. Add
  a hook, module or stored state only for a defect that actually reached `main`; prefer extending
  an existing check (`finish_branch.py`, the `pre-merge-commit` hook, the stop gate) over a new
  one; and verify a reviewer's claim against the code before acting on it. Two of the currency
  review's seven proposals were wrong on inspection; the 2026-10-15 review's held, bar one
  overstatement and one proposed question that copier's `--skip-tasks` made unnecessary.
- **Prefer a mechanical check, a script or a copyable reference file** to more prose in
  `CLAUDE.md` or a skill. A specific, greppable name in `CLAUDE.md` (`build_client`) steered haiku
  where a docstring pointer did not.
- **Done means**: the generation suite and `prek run --all-files` pass; anything that changes what
  a skill tells a model has been run through a generated project's gate, not just read; and a
  phase that changes what generated projects receive ends with a `copier update` of the canary.
- **Format template code in a generated project before committing.** `template/` is not linted in
  place, so a formatting slip surfaces only in the generation suite, a minute later, at commit.
  Generate a scratch project, copy the file in, `prek run ruff-format`, copy it back.

## Sessions and checkpoints

Decided 2026-10-15. A long session gets slower and costlier per turn and drifts from what is
written down; a fresh one reads only `CLAUDE.md`, memory and this file. So work is cut into
sessions at **checkpoints**, and at each one Claude says so: "Checkpoint: start a new session",
with the next step named in "Next up". Before that it finishes the step, merges it, and updates
this file, which is the hand-off — a fresh session must be able to start from it alone, and a gap
it finds is fixed here first.

**Every checkpoint ends with the command that starts the next session**, prompt included, ready
to paste (2026-10-18). `claude "<prompt>"` runs the prompt as the first turn and stays
interactive; `claude -p` would exit after it. For a step in both template repos:

```bash
cd ~/projects/github/GrndZero101/python-template-base && \
  claude --add-dir ../python-template-cli-typer "<prompt naming the step in TODO.md>"
```

The prompt names the step and says what state it starts from (merged, pushed or not), so the
first turn does not have to work that out.

A checkpoint falls:

- at the end of any step that ends mergeable, once this file says what comes next;
- after a review is triaged and recorded — the session that made the decisions triages, since it
  holds the evidence, and a fresh one carries them out;
- when the next step needs another working directory: hooks, skills and memory all belong to the
  directory a session started in. The CLI repo does not count — it is added to a base session (see
  "How work runs") — but the canary does, since it has hooks of its own;
- when `/context` shows the session past about half its window, at the next mergeable point.

Phase 10's checkpoints are named in its steps, C1 to C5. C4 is mandatory, not advisory: the
rename moves the directory the session started in.

## How work runs

Decided 2026-10-15, amended the same day. **Sequential: one session, one branch, one step at a
time.** An earlier plan ran side tracks in git worktrees beside phase 10. It was dropped before
any ran: the author reviews every decision and merge, so a second track mostly adds context
switching; each session pays its own context, against goal 3; two local generation suites slow
each other down; and `finish_branch.py` ends by switching to `main`, which git refuses while
another worktree has it checked out. Phase 10's steps also move the files each next step depends
on. Read-only work — a review, an audit — is still a session started where the files are.

**A step in both template repos is one session** (2026-10-18), started in the base with
`--add-dir ../python-template-cli-typer` (or `/add-dir` mid-session). Before, each such step took
two sessions, the second re-deriving what the first knew, against goal 3. Nothing is lost:

- The base's hooks, `CLAUDE.md`, skills and memory load as before.
- The CLI repo has no `.claude/` of its own, and the base's hooks skip a file in a sibling repo by
  design (`owning_repo` in `hook_payload.py`), so its edits are ungated as they always were. Its
  prek git hooks still run at commit, and `finish_branch.py` gates it in full.
- Its `CLAUDE.md` is not loaded for an added directory, so the session reads it before the first
  edit there. `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` is said to load it; unverified —
  check with `/memory` before relying on it.
- Git there is `git -C ../python-template-cli-typer`. Its suite and its finish run inside it,
  pointed at this checkout, each as one command:
  `cd ../python-template-cli-typer && BASE_TEMPLATE_DIR=<base> uv run pytest`, and the same with
  `uv run python <base>/template/tools/finish_branch.py --no-tests "<summary>"`.

The order of work is unchanged: the base half, then the CLI half, then the pushes (base first) and
the base's CI rerun. Starting in the parent directory instead was rejected: it has no
`.claude/settings.json` or `.git`, so no hook would run in either repo, and the memory is keyed on
the start directory.

## Status snapshot

- Two copier templates, both **published**: the base at
  [GrndZero101/python-template-base](https://github.com/GrndZero101/python-template-base) and the
  typer CLI at
  [GrndZero101/python-template-cli-typer](https://github.com/GrndZero101/python-template-cli-typer),
  each with `copier.yml` at the root and its files under `template/` via `_subdirectory`. **One
  project shape** (2026-10-05): the typer CLI scaffold. Data processing and full-screen TUIs are
  skills layered on it, not project types.
- **Three recipes ship reference code** that a generation test copies exactly as the recipe says,
  registers in `cli.py` and gates: `python-cli-typer`'s `status`, `python-data`'s `summary`
  (polars, CSV or parquet) and `python-tui`'s `browse` (Textual, Pilot tests).
- `copier update` works and is tested. Every `_task` is guarded with
  `when: "{{ _copier_operation == 'copy' }}"`, or the tasks re-run on update and the commit task
  fails on `no-commit-to-branch`. The variable is `_copier_operation`: `_copier_conf.operation`
  renders undefined, which silently disables every task, copy included.
- `template/` cannot be linted in place (Jinja, no `pyproject.toml`). `tests/test_template.py`
  generates projects and runs their gate and suite; it is the only check on `template/`.
- **CI** (2026-10-15): `.github/workflows/ci.yml` runs the root gate on Linux and the generation
  suite on Ubuntu and macOS on a push to any branch, unless it touches only docs: its `paths` list
  mirrors `generation-tests`' `files:`. Free, since the repo is public. Windows is opt-in since
  2026-10-16, in both repos: `gh workflow run ci.yml --ref <branch> -f windows=true`, at
  milestones and in work aimed at Windows. The targets are Unix-alikes (Linux, macOS, WSL2).
  Warm-cache times: gate 14s, Ubuntu 1m05, macOS 1m43, Windows 7m54; with the CLI suite on
  2026-10-16, Ubuntu 1m26, macOS 4m10, Windows 14m23. Why Windows is that slow is unconfirmed: the
  uv cache is on `D:` and pytest's tmp on `C:`, so uv cannot hardlink and may copy every package
  per project. `--basetemp` on `D:` plus `--durations=15` would test it, in a Windows uplift.
  CI installs `prek` and `copier` as uv tools and syncs with `--upgrade`; with `CI=true` a missing
  tool fails a test rather than skipping it.
- Toolchain: `uv`, `ruff`, `ty`, `prek`, `rumdl`, `copier`, all at their latest (D16). Every hook
  but the builtins is local, `uv run --no-project --with <tool>` with no version (step 3).
  Preview rules are selected one by one (`explicit-preview-rules`); pytest names its strict options
  individually and turns warnings into errors. **ty is a local hook** since 2026-10-16,
  `uv run --with ty ty check`, not ty-pre-commit: that hook runs uv's preview `uv check`, which
  skips every file with a PEP 723 header and forwards no flag, so a uv script was never
  type-checked.
- `template/tools/`, eleven modules: the hooks `branch_guard` (`PreToolUse`: no edits on `main`),
  `gate` (`PostToolUse`: the gate on every Edit/Write, concise, pausing on conflict markers),
  `stop_gate` (`Stop`: changed files and the tests, measured from the merge-base, blocking once)
  and `session_doctor` (`SessionStart`: status, plus a missing `prek` or git shim, and a uv
  behind its latest release, as advice);
  `check_conventions` and `convention_rules`, ten rules no linter covers (`nested-def`,
  `nested-class`, `complex-comprehension`, `raise-from-none`, `dynamic-attribute`,
  `missing-main-guard`, `raw-httpx-client`, `patched-httpx`, `silent-exit`, `typer-default`);
  `finish_branch` (squash, full gate, tests, message check, `--no-ff` merge — trusting no hook);
  `gate_log`, `hook_payload`, and the DebugMCP launchers `debug_module` and `debug_pytest`.
- Hooks are **exec form** with `${CLAUDE_PROJECT_DIR}` paths and launch through
  `uv run --no-project --no-config`, so neither a `cd` nor a conflicted `pyproject.toml` breaks
  them. Bash writes (heredocs, `sed -i`) skip the edit-time gate by design; the stop gate and
  `finish_branch.py` are the backstop, and both run the tests. Proven in the canary on
  2026-10-04: a `sed -i` `print` passed the edit-time gate and the stop gate blocked it.
- `cli-modern` ships a **scaffold**, not a demo: an `about` command, global `--verbose`/`--version`,
  a per-command `--output`, each resolving flag, then `<SCRIPT>_*` environment variable, then
  config file, then default through pydantic-settings. `python-cli-typer` is recipe-first — add a
  command, call an HTTP API, a validated argument, add a setting or a secret.
- Agent debugging is the **standalone DebugMCP CLI**, registered per user as `debugmcp-cli`.
  Projects ship `.debugmcp.json`, the two launchers and the `python-debug` skill. Proven headless
  in WSL; neither adapter can pass program arguments, so the skill drives commands through tests.
- **The canary**, the public `GrndZero101/python-canary-cli-typer` (since 2026-10-15, after a
  clean audit, D13): a consumer of both layers with its own `weather` command,
  script `tdf-cli` and package `python_canary_cli_typer`. Its author email, in its answers and in
  every commit, is the GitHub noreply address. **Drive it from a session started in
  its own directory**: Claude Code loads hooks and skills from the session's project, so from here
  they are all inert. A rehearsal on a scratch clone (`_src_path` edited,
  `copier update --trust --defaults --vcs-ref <branch>`) predicts a real update exactly. After an
  update, `session_doctor` may report missing git shims;
  `prek install -t pre-commit -t commit-msg -t pre-merge-commit` restores them.

## Decisions

Open:

| # | Decision | Needed by | Recommendation |
|---|---|---|---|
| D5 | Tagging, which changes `copier update` semantics | Phase 8 | Stay untagged until the canary settles, then `v0.1.0`. See phase 8. |

Decided:

- **D1** — `.python-version` rendered from the answer, 3.12–3.14, default 3.14.
- **D2** — spec runs by hand, sonnet the baseline, reviewed by Opus (see "Spec runs").
- **D3** — the git ritual is a script, `finish_branch.py`.
- **D4** (2026-10-05, replacing 2026-10-04) — `cli-stdlib` is its own repo, not a type here. A
  scaffold built for it on 2026-10-05 is parked on the local branch `archive/cli-stdlib`
  (`4098f9e`) to seed that repo; delete the branch once it has.
- **D6** (2026-10-05) — `data` and `tui` are recipe-first skills layered on the CLI, shipped to
  every project, not project types. **D7** (their order) is moot.
- **D8** (2026-10-04) — the config file lives in `~/.config/<script>/` on macOS as on Linux,
  `XDG_CONFIG_HOME` honoured on every platform, `%APPDATA%` on Windows.
- **D9** (2026-10-04) — a data command's JSON emits secrets raw, as `terraform output -json` and
  `gh auth token` do, via an explicit `.get_secret_value()`; incidental exposure — repr, logs,
  whole-model dumps such as `about` — is masked by `SecretStr`, as `gh auth status` and
  `kubectl config view` mask. Checked: pydantic-settings masks `repr` and
  `model_dump(mode="json")`.
- **D10** (2026-10-04) — the config file is YAML, for flexibility as configs grow.
- **D11** (2026-10-05) — **one project shape.** `project_type` branched `copier.yml`,
  `pyproject.toml`, the README and the tests, and the three unbuilt types' skills rotted unexercised
  (every one broke on a first attempt). Why not layer directories for two CLI scaffolds: `_exclude`
  matches rendered paths, so same-named modules needed Jinja-named directories, which the
  2026-10-05 attempt showed to be unreadable. Superseded across repos by D12.
- **D12** (2026-10-15) — **layered templates.** A shared base template plus one thin template per
  use case, applied to the same project with separate answers files, as copier documents. A spike
  with two local templates proved it: one `copier copy` of the use case produced both layers, its
  task running `copier copy` of the base; the base read the use case's answers through
  `_external_data`; `copier update -a .copier-answers.base.yml` and a plain `copier update` each
  touched only their own layer; a local edit survived. **No update chain**: a project records both
  sources, so a base fix reaches it without a use-case release. The costs: an update is two
  commands, each needing a clean tree; a file both layers render conflicts (proven — markers in
  `pyproject.toml`), so ownership must be disjoint and checked; only ruff can extend a base-owned
  config, so pytest, ty and rumdl config and the dev group repeat in each use case's
  `pyproject.toml` (D15); and the base's CI must run every use case's suite. Rules split as
  `CLAUDE.md` (base) plus `.claude/rules/<use case>.md`, which Claude Code loads at the same
  priority. Rejected: copying `tools/` per repo (drift), and vendoring the base into each use case
  as a subtree (a real update chain).
- **D13** (2026-10-15) — **names, and no redirects.** This repo becomes `python-template-base`;
  use cases are `python-template-cli-typer` (today's scaffold), `-cli-stdlib`, `-api-fastapi`, and
  `js-template-web-vue` for the Vue front end in `~/tmp/operator/inventory-app-design-spec.md`.
  uv scripts with PEP 723 metadata are a **skill in the base**, not a repo. The skill
  `python-cli-modern` becomes `python-cli-typer`. Each use case gets a public
  `python-canary-<use case>`; the base gets `python-canary-base` only once it has the uv-script
  skill to exercise. The sole user is the author, so renames break cleanly: every reference is
  updated, and nothing may rely on GitHub's redirect from an old name. "Dogfood" is retired for
  corporate use. The local directory moves too, and with it the Claude Code memory directory,
  which is keyed on the path.
- **D14** (2026-10-15) — **licence is a question.** `template/LICENSE` ships "Copyright (c) 2026
  GrndZero101" literally, so every generated project names the template's author. The base asks
  `license` (MIT default, Apache-2.0, Proprietary) and `copyright_holder` (default `author_name`;
  not git config, which copier can read only through an extension each user must install), and
  records the year at generation. That takes both halves of copier's "lock a computed value"
  recipe, because a `when: false` answer is otherwise dropped from the answers file and
  recomputed on every update: `default: "{{ copyright_year | default('%Y' | strftime) }}"`, and
  the answers-file template dumping
  `{{ dict(_copier_answers, copyright_year=copyright_year) | to_nice_yaml }}`. Checked: copier
  9.17 loads `strftime` by default.
- **D15** (2026-10-15) — **the base on its own, and in a brownfield repo.** The base is a use case
  in itself: a skeleton with every guard for prototyping before the shape is known, or dropped
  into a brownfield repo with the least disruption. The 2026-10-15 review's proposed answers were
  each checked against the code, and accepted unamended.

  **Who owns `pyproject.toml`.** The use case, when layered. The base renders a minimal one under
  `_skip_if_exists`, which copier never overwrites and leaves out of the update patch, for the
  standalone and brownfield cases — so the ownership check exempts it. Ruff is the only tool that
  merges configs: the use case writes `extend = "ruff-base.toml"` and then **only additive keys**
  (`extend-select`, `extend-per-file-ignores`, `extend-exclude`), because its own `select` or
  `per-file-ignores` would replace the base's lists, dropping the whole rule set and the `tools/**`
  exemptions. pytest, ty and rumdl take the first config file they find and merge nothing, so a
  base-owned `pytest.ini`, `ty.toml` or `.rumdl.toml` would lock every use case and brownfield repo
  out of adding a setting (FastAPI's async tests need their own); their config stays in
  `pyproject.toml`, guarded by the contract test in phase 10.

  **Order, and the shared questions.** Keep the spike's: one `copier copy` of the use case, whose
  only task runs `copier copy --trust --defaults` of the base, and the base owns every bootstrap
  task. The base defines the shared questions (author, licence, Python version) with
  `default: "{{ _external_data.use_case.<key> | default('') }}"`, so layered under `--defaults` it
  asks nothing, and standalone it asks everything; a missing answers file yields an empty dict.
  The base's source is an answer in the use case (`base_template`, default
  `gh:GrndZero101/python-template-base`), so the generation tests and the base's CI can point it at
  a local checkout. The base's `copier.yml` sets `_answers_file: .copier-answers.base.yml`, so no
  `-a` is needed. Cost: shared questions are defined twice; a generation test asserts both
  answers files agree on them.

  **Applying the base to an existing repo** (the canary, a brownfield repo). It is a `copy`, so
  every task runs: `git init`, `uv sync`, `git add -A`, `git commit` on whatever branch is checked
  out, and the `prek install`s. `copier copy --skip-tasks` (`-T`) avoids it, followed by the three
  `prek install`s by hand. A `bootstrap_git` question only if brownfield adoption becomes real.
  "Generation into unusual git states" — a destination that is already a repo, a default branch
  other than `main` — belongs here, not in phase 8.

  **Brownfield gating.** `finish_branch.py` runs `prek run --all-files` (finish_branch.py:209), and
  `ty` checks the whole project whatever files it is given (gate.py:20–23), so the edit-time and
  stop gates would fail a legacy codebase at the first save too. No machinery now: brownfield has
  not reached `main`. When it does: a `--changed-only` flag on `finish_branch.py` reusing
  `stop_gate.changed_files`, and `exclude` lists in the ty and rumdl config the adopter can edit.
- **D16** (2026-10-17) — **the template never pins its toolchain.** uv, prek, copier and the
  gate's tools run at their latest, on users' machines and on CI alike, replacing the 2026-10-16
  pin-and-floor design under "Setup helper". There are no users to protect from an upgrade, and
  the pin's copies across two repos and two layers caused the canary's failed update rather than
  preventing one. The cost is accepted: CI loses reproducibility, and an upstream release will
  sometimes break a run, which is fixed forward. The weekly CI run surfaces that. A downstream
  project that wants a frozen toolchain gets a `seal` command later (see "Later"); the template
  never seals itself.

## Done: phases 1–9, and the lessons that still apply

Phases 1–6 (2026-10-02 to 10-04) fixed the defects a review reproduced at `712a7f8`, then made the
gate concise and unavoidable, stabilised the toolchain, turned conventions into checks, cut
`template/CLAUDE.md` from 296 lines to about 170, and made the skills recipes. Phase 7 added
secrets, the config file and the install story; phase 9 made data and TUI layered skills; phase 8
put this repo under CI. The detail is in `git log`.

- **The edit-time gate's report** is `prek --quiet` with ruff and ty set to concise output: 266
  bytes where it was 3,048. A repeated convention message prints once, then only its location.
- **`finish_branch.py` trusts no hook.** A commit made while the shims were missing ran none, and
  a rebase runs none, so it runs the full gate, the tests and the message check itself.
- **A half-added setting fails `tests/test_config.py`**, naming the missed step. `load_settings`
  keeps its explicit keywords: only the `Settings` constructor is documented to resolve sources.
- **A new global option needs no command edit**: commands take `GlobalOptions` whole and required.
  The canary proved the earlier per-command wiring leaked — its `weather.py` accepted `--config`
  and ignored it — and, after the fix, that a stale call fails `ty` with an error that alone leads
  to the fix.
- **Convention messages route the model to the skill**: `raw-httpx-client`, `patched-httpx` and
  `silent-exit` each name the reference file to copy. That reached haiku, which never loaded the
  skill on its own.
- **pydantic-settings has no runtime path for `YamlConfigSettingsSource`**, and that source lets a
  list-shaped file escape as a bare `ValueError`, so `config_file.py` parses with `yaml.safe_load`.
- **An editable `uv tool install` keeps its old `--version`** until `--reinstall`; a plain one is a
  snapshot that `uv tool upgrade` rebuilds from its source.
- **Library facts the skills now encode**: registering a polars frame in duckdb needs `pyarrow`;
  duckdb's integer `sum` is `Decimal(38, 0)`; a positional `scan_csv(schema=)` silently mislabels
  swapped columns; loguru's sink bypasses Textual's stderr redirect, so the app logs with
  `self.log`; rich's `err.print` wraps errors at the console width and reads `[...]` as markup, so
  commands write errors with `sys.stderr.write`.
- **`pytest.raises(match=)` is a regex**: `repr()` of a Windows path is full of escapes. CI's first
  run caught it on Windows only; the reference tests `re.escape` it. Windows runners check out
  with `core.autocrlf=true`, as users' Git for Windows does, and nothing broke on CRLF.
- **Decided against**, 2026-10-04: a `PostToolUse` hook on `Bash`, and a per-session stop-gate
  checkpoint (`tools/session_base.py`, built and discarded). The gap they targeted — tests never
  run on work merged within a turn — took three lines in `finish_branch.py`.

## Spec runs

Resumed 2026-10-05 for the layered skills. By hand, as `examples/README.md` in the CLI repo
describes — a fresh project, the spec handed unedited to sonnet, the gate and tests run by hand,
then a review in a separate `opus` session in plan mode driven by `examples/evaluate.md` there. Each
template finding becomes an item here, checked against the code first. Rerun both specs after any
phase that changes what a skill or the gate tells a model; the fixes from the currency run — the
validated-argument recipe, the corrected spec, `finish_branch.py` running the tests — are not yet
measured.

| Date | Spec | Model | Template | Gate | Tests | `/cost` | Verdict and main findings |
|---|---|---|---|---|---|---|---|
| 2026-10-03 | geo | haiku | `354b24f` | pass | 215 pass | 68 calls, 26k out | Two required tests wrong or missing. Never loaded `python-cli-modern`: hand-rolled `httpx.Client()`, patched httpx in every test, no response model, cause dropped on exit. |
| 2026-10-03 | geo | sonnet | `354b24f` | pass | 212 pass | 9 calls, 10k out | Meets every row. Loaded the skill second, copied `http_client.py`, `MockTransport` throughout. Wrote every file through one heredoc. |
| 2026-10-03 | geo | haiku | `f6c03ff` | pass | pass | 68 calls, 31k out | Close. Found `build_client` through `CLAUDE.md` and copied it. Still never loaded the skill: parsed the response by hand, reported `exc.request.url` instead of the cause. |
| 2026-10-03 | currency | sonnet | `2b06886` | pass | 276 pass | 15 requests, 17.7k out, $0.65 | Meets the spec, every value a `Decimal`. Branched unprompted, `Annotated` throughout. 8 of 11 writes were Bash; validated arguments by hand as `str`; mocked a "missing key" the service answers with a 404; `finish_branch.py` failed twice on a dirty tree. All seven findings acted on. |
| 2026-10-05 | spend | sonnet | `73933c1` | pass | 283 pass | 14 calls, 35k out | Meets the spec. Loaded `python-data` first, unprompted, then `python-cli-modern`; branched first; left the work on its branch and said so. Every write was Bash, so only the stop gate ran. Read columns by name, sidestepping the skill's positional `scan_csv(schema=)` — fixed. Three fix rounds, none template defects: `ty` on `Series.sum()`'s broad return type, `PLR0917`/`PLR0913` on a seven-parameter command (`*` and a commented `noqa`), and a rich title wrapping at 80 columns under a substring assert. |
| 2026-10-05 | logs | sonnet | `15ed246` | pass | pass | 10 calls, 32k out | Meets the spec. Loaded `python-tui` unprompted; branched first; finished with `finish_branch.py`. Every write was Bash. Logic outside the app, `.tcss` styles, letters typed in search tested not to fire bindings. Patched its own `run_screen` seam in the command tests — beyond `CLAUDE.md`'s one sanctioned patch, and it said so: the reference had no seam, so the skill could not show how to test a picker through `main`. Fixed: `run_screen` is in the reference and named beside `build_client`. |

What the runs taught: the skill's content works and its discovery is weak below sonnet; sonnet
writes through Bash as a habit, so the backstops matter more than the edit-time gate; and specs and
API docs are unreliable about failures, so the recipe now says to provoke each one live.

Open from the runs:

- [ ] The gate's pause on conflict markers and the conflicted-`pyproject.toml` guard are proven
  only by generation tests, never by a consumer update with a real conflict. The `7a5941e` and
  `2957d4c` canary updates had none; still watching.
- [ ] **Watch, from the `spend` run** — act on a second occurrence, each a line in a skill: a
  command with more than five parameters trips `PLR0913` and `PLR0917`, and the answer is
  keyword-only flags plus a commented `noqa`; polars' `Series.sum()` is typed as a broad union, so
  `ty` wants `int(...)` before it reaches an `int` parameter; and a test asserting a substring of a
  rich table breaks when the title wraps at 80 columns.
- [ ] **Declare each setting once**, if a run shows a model fumbling "Recipe: add a setting". Today
  a setting is declared four times — `Settings`, `_Overrides`, a `GlobalOptions` field or
  `load_settings` keyword, an option alias — and `load_settings` copies each flag by hand. Building
  `given` from `dataclasses.asdict(options)` plus the keywords, dropping `None`, deletes
  `_Overrides` and the copy lines: three edits instead of four, and two wiring tests in
  `test_config.py` go. Bundle with it: the app callback and each command both call
  `load_settings`, so every run parses the environment and reads the config file twice; the
  callback needs only `verbose`. Found 2026-10-05. Judged not worth changing: the unused `err`
  console, `config.py` importing rich through `output.py`, and five docstring lines over 100
  columns.

## Phase 10 — Base and use-case layers

Prove D12 on the use case that already works before building another. One session at a time, in
order; each step ends mergeable, and the checkpoints say where a new session starts. Rehearse
each step on scratch copies first; the canary's update is the acceptance test.

1. [x] **Settle D15**: accepted unamended (2026-10-15) and moved to "Decided".
   **Checkpoint C1**, reached.
2. [x] **Assign every file an owner**, done by directory (2026-10-16). `template/` and the root
   `copier.yml` are the base; `use-cases/cli-typer/` (its own `copier.yml` and `template/`) is the
   CLI layer, and step 6 lifts it out with its history. The owners are in the root `CLAUDE.md`.
   Notes a fresh session needs:
   - `.claude/rules/cli-typer.md` does not exist yet. Step 3 creates it, in
     `use-cases/cli-typer/template/.claude/rules/`, with the rows it moves out of the base.
   - The skill rename is done: `python-cli-modern` is `python-cli-typer` everywhere but the
     spec-run table, which is history.
   - `ruff-base.toml` holds all of ruff's rules as a top-level file (`[lint]`, not
     `[tool.ruff.lint]`). `target-version` stays in each `pyproject.toml`, because it follows the
     project's Python floor. The use case adds only `extend-immutable-calls` for typer.
   - The base shares four questions, not three: `project_name` as well, because its fallback
     `pyproject.toml` needs a name. Only `project_name` has a validator, as the others were
     optional before the split.
   - The use case's `base_template` defaulted to `gh:GrndZero101/python-template` until step 7
     renamed the repo; it is now `gh:GrndZero101/python-template-base`.
   - The update tests build their templates with `_snapshot`: a use case is a subdirectory, which
     copier cannot update from, so each test copies it into a throwaway git repo. The snapshot
     includes uncommitted changes, so the tests no longer see only committed state.
   - New tests: each layer writes its own answers file; the use case keeps the `pyproject.toml` it
     wrote; each layer updates only its own files (D12's claim); the base alone passes its gate.
3. [x] **Neutralise base-owned text that names the CLI** (2026-10-16). The typer and httpx rows
   and the sanctioned-patches sentence moved from the base `CLAUDE.md` to
   `use-cases/cli-typer/template/.claude/rules/cli-typer.md`; the `convention_rules.py` messages
   point at `.claude/skills/*/reference/` rather than a named skill, and `silent-exit`'s message
   covers stdlib logging as well as loguru. A generation test keeps those names out of the base.
4. [x] **The mechanical checks** (2026-10-16), in `tests/test_template.py` under "the contract
   between the layers": the layers render no file in common but the base's `_skip_if_exists`; the
   two `copier.yml` files define every base question alike (type, help, choices) and the generated
   answers files agree; and the `pyproject.toml` of the use case and of the base alone both hold
   what the base relies on. The ruff keys forbidden beside `extend` are `select`, `ignore`,
   `per-file-ignores` and `unfixable`, not just the first two D15 named: each replaces a base
   list. Each check was shown to fail when its rule was broken.
5. [x] **Licence questions** (D14, 2026-10-16). Both `copier.yml` files ask `license` (MIT,
   Apache-2.0, Proprietary) and `copyright_holder`, and compute `copyright_year`; both
   answers-file templates write the year back, so an update keeps it (a test edits the recorded
   year to 1999 and checks the update leaves it). `template/LICENSE` is `LICENSE.jinja`, holding
   the three texts, the Apache one verbatim from the Apache Software Foundation's text (found in
   an installed package, not typed from memory). Both `pyproject.toml.jinja` files gain
   `license = "<SPDX>"` (`LicenseRef-Proprietary` for Proprietary), and `uv build` accepts all
   three. The README's licence line follows the answer. The root `LICENSE` stays MIT: it is this
   repo's own.
   **Checkpoint C2**, reached: steps 2–5 are merged here, and the layering is rehearsed by the
   update tests and by scratch generations.
6. [x] **New repo `python-template-cli-typer`**, public (read "Before step 6" below first). Done:
   both CIs green.
   **Seed it from this repo's history** —
   clone, then remove base-owned files — never `git init`: `copier update` re-renders the old
   template at the commit recorded in the canary's answers file, and that commit must exist in the
   new repo. CI on three platforms against the base at `HEAD`; the base's CI checks it out and runs
   its generation suite against the base commit under test, through `base_template`.
   **Checkpoint C3**, reached.
7. [x] **Rename** (D13): this repo to `python-template-base` on GitHub, the local directory, the
   remote URL and the Claude Code memory directory; then every reference to the old name. Done
   2026-10-15: the author renamed the repo, directory and remote by hand; the memory was copied
   across and the old project directory deleted; both repos' references followed, the bootstrap
   commit message becoming `chore: generate project from python-template-base` and the root dev
   project `python-template-base-dev`.
   **Checkpoint C4, mandatory**: the session's directory no longer exists. Reached.
8. [x] **Migrate the canary** to two answers files. Done 2026-10-15, C5 included. What the run
   showed:
   - Both copier commands took `--skip-tasks --defaults`. `--defaults` answers the questions added
     since `2957d4c` (`license` MIT, `copyright_holder` the author, `base_template`), so `LICENSE`
     now names Timothy Longbottom, not GrndZero101.
   - Step 1 conflicted only on the README's "Generated from" line; the template's side is right.
   - Between the steps `.gitignore` is gone, so `.gate.log` and `__pycache__` show as untracked:
     `git add -A` only after step 2. Commit nothing in between either, since the hooks' config is
     gone too.
   - The rehearsal and the real run matched file for file (35 files, +190 −138); afterwards a
     plain update and a base update were both no-ops. The base update's `MissingFileWarning` for
     `.copier-answers.yml` comes from copier rendering the old base in a temp directory: harmless.

   The plan, as followed. **Order matters**: `copier update` deletes every file the old render had
   and the new one lacks, with no check for local edits (`_remove_old_files`, still so in copier
   9.18). So:
   1. Edit `_src_path` in `.copier-answers.yml` to the CLI repo — the one sanctioned edit of a file
      that says never to edit it — and `copier update`. The canary's edits to `cli.py`,
      `pyproject.toml` and `README.md` merge; every base-owned file is deleted.
   2. `copier copy --trust --skip-tasks <base> .`, which recreates them at the base's `HEAD`;
      the canary never edited them, so nothing is lost. Then the three `prek install`s by hand.

   The reverse order deletes the base again. Step 1 deletes `.claude/settings.json` and `tools/`,
   so run the migration by hand or from a session outside the canary, never inside it. Rehearse
   on a scratch clone. Then rename the repo to `python-canary-cli-typer`. Make it public only
   after a secrets audit of its whole history: read-only, from a session in its directory.
   **Checkpoint C5**: a new session started in the canary, to confirm its hooks, skills, gate
   and tests. Reached 2026-10-15, and the canary made public the same day:
   - All four hooks fire and block: the branch guard refused a Write on `main`; on a probe branch
     the edit-time gate and the stop gate both blocked a `print` and a nested `def`. Skills load,
     the gate is green (bar `no-commit-to-branch`, which always fails on `main`), and the suite
     passes (272, one skip).
   - The secrets audit was clean: all 28 commits then, every ref, by pattern with no scanner
     installed — token shapes, secret-named literals, credentialed URLs, sensitive file names,
     long literals, IPs. GitHub held no issues, PRs, Actions runs or releases. The only personal
     data was the author's two email addresses.
   - **The package rename** (D13) was two user-run updates that change answers only:
     `copier update --trust --defaults --vcs-ref=:current: --data package_name=... --data
     project_name=... --data project_description=...`, then the base with
     `-a .copier-answers.base.yml --data project_name=...`, which changed only its answers file.
     No conflicts, but `_remove_old_files` bites here too: each template file under `src/<package>/`
     is rendered at the new path and the old one deleted, edits and all. `cli.py` silently lost the
     `weather` registration — no marker, no `.rej`. Project-only modules (`weather.py`,
     `http_client.py`) stayed in the old directory, their tests importing the old name. After
     `uv sync` the `tdf-cli` script was missing, probably because the old and new distributions
     both own it and removing the old took it; `uv sync --reinstall-package <new>` restored it.
   - **The email scrub**, because the author wants no personal address in the canary:
     `author_email` became the GitHub noreply address through the same kind of update on both
     layers. The history was rewritten with `git filter-repo` (`--mailmap`, `--replace-text`,
     `--replace-message`) on a fresh clone, verified — no address in any object, the tip's tree
     identical — and pushed to a deleted and recreated GitHub repo, since a force-push leaves old
     commits reachable by hash. The author ran the rewrite, the delete and the push: an agent's
     auto mode refuses history rewriting.

   Follow-ups the canary found:
   - [x] ~~**Document renaming a project**~~ — dropped 2026-10-16. The canary's rename was part of
     the restructuring, and the pain makes a rename rare enough not to document. Looking at the
     sync docs for it found the real gap instead, fixed the same day: a generated CLI project's
     README updated only the use case, never the base, and the base README still described the
     CLI. Both now give the two-layer update flow.
   - [x] **A blank `author_email`** rendered `email = ""` in `pyproject.toml`. Fixed 2026-10-16 in
     both repos: the key is left out when the answer is blank, the question's help (identical in
     both `copier.yml`s, as a CLI test requires) suggests GitHub's noreply address, and each suite
     has a test generating with a blank email.
   - [x] **`finish_branch.py` drops commit bodies when it squashes**: the canary's rename lost its
     explanation. Fixed 2026-10-15: the squashed commit is MESSAGE, then each commit's body in
     order (a repeated paragraph once), then their trailers once each as the last paragraph, where
     git reads them. The merge commit keeps the subject alone. Reaches the canary on its next base
     update.
9. [x] **The uv-script skill** (2026-10-16): `python-uv-script` in the base, recipe-first like
   the stack skills, with `reference/yaml_to_json.py.jinja` and its test, which a generation test
   copies where the recipe says, gates, tests, then breaks with a type error to prove ty sees it.
   What the experiments settled, each the reason for a line in the skill:
   - ty-pre-commit's `uv check` skips PEP 723 files, so ty is now a local hook (see the toolchain
     line). The per-script alternative, `uv check --script`, takes one file and checks a script
     environment that `uv run` syncs *inexactly*: a dependency dropped from the header stays
     installed until `uv run --exact`. That is why the reference test's one subprocess is
     `uv run --exact scripts/<name>.py --help`.
   - A script's dependencies are declared twice, `uv add --script` for the header and
     `uv add --dev` for the project venv, which pytest, ty and the debugger use. Tests import
     `scripts.<name>`, so `pythonpath` in both `pyproject.toml.jinja` files lists `"."` (a listed
     `scripts` in ty's `extra-paths` errors when the directory is absent; `"."` always exists).
   - The header's `requires-python` is rendered from the answer: ruff rewrites syntax to the
     project's `target-version` (py314 turned `except (A, B):` into `except A, B:`) while ty checks
     a script at its header's version, so a lower header fails ty. For the same reason the
     reference uses two `except` clauses, not a tuple: it must survive `ruff --fix` unchanged at
     every floor, or the generation test's single gate run fails on "files were modified".
   - The header goes above the docstring: `uv add --script` edits a leading block but adds a second
     one when the block sits lower. No shebang (inert on Windows, needs an exec bit); no
     `uv lock --script` (the `uv-lock` hook never refreshes a `<name>.py.lock`); `exclude-newer` as
     a full RFC 3339 timestamp is the pin.
   - The exact skill set is asserted in the CLI repo, `tests/test_template.py` `SKILLS`, so a base
     skill is two pushes and a rerun, as "Next up" describes.
   - Not yet measured by a model: the setup helper exercises the script rules at this repo's root,
     not the generated-project wiring (`scripts/`, the ty hook, `uv add --dev`). One short spec run
     in a scratch base-alone project belongs in the canary-base session, before any line is added
     to the skill on a hunch.
   - [x] **`raw-httpx-client` named a reference a base-alone project lacks.** Fixed 2026-10-17:
     the message still points to a CLI skill's `http_client.py`, then says a uv script or a
     project without one defines its own `build_client` (timeouts, User-Agent, `transport=`). The
     rule stays in the base, which owns `tools/`, and reads only the AST, so the message is static
     rather than probing for the file.
   - [x] **Acceptance test** (2026-10-17, from a session started in the canary): on a branch,
     `copier update --trust --defaults`, `uv sync`, commit, then the same with
     `-a .copier-answers.base.yml`, finished with `finish_branch.py` as `6615e62` and pushed. No
     conflicts and no `.rej`. The CLI layer changed `README.md` (the two-layer update flow) and
     `pyproject.toml` (`pythonpath`); the base brought the ty hook, the skill, the `CLAUDE.md`
     line, `finish_branch.py` and git-workflow. Both answers files changed only `_commit`, and
     both `_tasks` lists are copy-only, so `--trust` ran nothing. `prek run --all-files` green;
     273 passed, one skip. A probe script in `scripts/` with a PEP 723 header and a type error
     failed the new ty hook, so the swap checks scripts rather than merely passing. Seen again and
     harmless: the base update's `MissingFileWarning` (step 8), and copier's "Make sure Git >= 2.24
     is installed" beside git 2.56.
   - [x] **The READMEs said an agent's permission classifier refuses `--trust`.** In auto mode on
     2026-10-17 it allowed both updates. Fixed the same day in both repos' `README.md` and the CLI
     repo's `template/README.md.jinja`: the flag lets the template run its `_tasks`, which are
     copy-only, so an update runs none of them; an agent runs it with `--defaults` and explicit
     answers to new questions, since it cannot answer prompts.
   - [x] **Every hook with no `stages` ran at every installed stage**, so a commit listed the
     whole gate again at `commit-msg`, and ty, `always_run`, checked the whole project twice per
     commit. Fixed 2026-10-17: `default_stages: [pre-commit, pre-merge-commit, manual]` in the
     generated config and the root's. Checked against `main`'s config with `prek run -c`:
     `commit-msg` now runs only the message check, and `pre-merge-commit` and the default
     `prek run --all-files` select exactly the hooks they did. A hook's own `stages` still wins,
     so `no-commit-to-branch` and `generation-tests` are untouched. Reaches the canary on its next
     base update.
   **Later in the phase**: `python-canary-base` to exercise the skill; seed
   `python-template-cli-stdlib` from `archive/cli-stdlib`.

### Before step 6

What the 2026-10-16 session learned that step 6 depends on. Settle the first two with the author
before moving a file.

1. **How the new repo is gated.** The root of this repo borrows the base: its
   `.claude/settings.json` hooks and its `conventions` hook run `template/tools/*.py`, and its
   `CLAUDE.md` imports `@template/CLAUDE.md`. The new repo has none of those files. D12 rejected
   copying `tools/` per repo (drift), so the options are a root gate with no tools at all (prek
   hygiene, ruff, rumdl and the generation tests only), or fetching the base's `tools/` at a pinned
   commit. Decide first; it shapes the new repo's `CLAUDE.md`, hooks and pre-commit config.
2. **Where `examples/` and the spec-run material go.** `examples/` and "Spec runs" below test a
   model building CLIs on the typer scaffold, so they belong with the CLI repo, but `TODO.md`
   stays here. Moving them is a call about where the benchmark lives.
3. **Seed by plain clone, never `git filter-repo`.** filter-repo rewrites every hash, and the point
   of seeding from history is that the canary's recorded `_commit` (an old, single-template
   commit) must still exist. A clone keeps the hashes: clone, `git rm` the base-owned files, move
   `use-cases/cli-typer/*` to the root in one commit, point `origin` at the new repo. Old commits
   keep the old layout, which is what `copier update` re-renders at step 8.
4. **The base must be on GitHub first.** The use case's `base_template` defaults to
   `gh:GrndZero101/python-template` (the name until step 7), and the new repo's CI needs the base
   at `HEAD`. `main` was pushed on 2026-10-16; push again if it has moved before the first CI run.
5. **Splitting `tests/test_template.py`.** Tests of the base alone (the base passes its own gate,
   its questions are defined in the use case) stay here. Everything generated through the use case
   moves, with `USE_CASE_DIR` becoming the repo root and the base coming from an environment
   variable naming a checkout (default: the GitHub URL). The three contract tests need both
   templates, so they run in the CLI repo's suite and this repo's CI runs that suite against the
   base commit under test (checkout the CLI repo, set the variable, `uv run pytest`). The helpers
   `_snapshot`, `_snapshot_base` and `_snapshot_use_case` copy a template into a throwaway git repo
   because copier cannot update from a subdirectory; in the CLI repo the use case is a git root,
   so it can be cloned directly.
6. **CI.** Copy `.github/workflows/ci.yml` (actions pinned by SHA, `fetch-depth: 0`, git identity in
   the environment) and add a second `actions/checkout` of the base into `base/`. Its `paths:`
   filter must list what `generation-tests` lists. The Windows and macOS jobs are the only check of
   the portability rules, so do not trim the matrix. (Superseded 2026-10-16: Windows is opt-in.)
7. **Leftovers named for step 7.** The base's bootstrap commit message, the `base_template`
   default, `tests/` assertions on "python-template" and the README's Path A (which says to clone
   and copy the use case) all change with the rename or the split. All done in step 7.

## Setup helper (after step 9)

Raised 2026-10-16. One command takes a machine from nothing to ready, and later keeps it current:
`uv`, the tools, copier's settings, and both layers' updates of a project. Two files, because the
first step has to run before anything is installed and everything after it is easier in Python.
Not a template file: it runs before any project exists, so it lives at this repo's root and is
linted by the root gate.

Decided 2026-10-16: the gate is hard, `uv` is pinned rather than chased to the latest release,
the shim is POSIX `sh` (not zsh), and step 9's skill is written first so the helper is built by
following it. **The pin is superseded by D16** (2026-10-17): the pin, the shim's version check and
`pins` below describe what was built. "Next up" step 2 removed them from the base on 2026-10-18.

**The `uv` pin.** One version, the floor every part of the system needs, kept in step everywhere it
is written down, with a test asserting they agree:

- `UV_VERSION=` in the shim, the one place a shell has to read it from;
- `[tool.uv] required-version = ">=<pin>"` in each `pyproject.toml` the templates render, and in
  this repo's. uv itself then refuses to run below the floor (checked 2026-10-16: "Required uv
  version `>=0.13.1` does not match the running version `0.12.21`. Update `uv` by running `uv self
  update`"), so every `uv run` — the hooks, the gate, the agent's commands — is gated, not only
  the helper. A hook that fails this way fails closed and names the fix;
- the `version` input of `astral-sh/setup-uv` in both repos' CI, so CI runs the floor it enforces.

A newer `uv` passes; the pin is a floor, not an exact match, so a user who updated is never pushed
back. Moving it is the helper's job (`pins`, below), not a hand edit in four files.

**The shim: a POSIX `sh` script, as thin as it can be.** Its only job is a `uv` it can trust:

1. **No `uv` on PATH:** say so, and with consent (`--yes` when there is no TTY; refuse otherwise)
   run the official installer at the pinned version,
   `curl -LsSf https://astral.sh/uv/$UV_VERSION/install.sh | sh`, falling back to `wget -qO-`.
   Then use `$HOME/.local/bin/uv` by absolute path for the rest of the run, since PATH in this
   process has not changed.
2. **`uv self update --dry-run`, exit code non-zero:** stop. Exit 2 means this `uv` cannot update
   itself — Homebrew, pip, a distro package, or a second copy shadowing the standalone one; the
   error says which (seen 2026-10-16: "Self-update is only available for uv binaries installed via
   the standalone installation scripts", plus "Are multiple copies of uv installed?"). Print it,
   and how to move to the standalone install (`brew uninstall uv`, then step 1). A network failure
   also lands here: stop and say the check could not run. A `uv` older than 0.7.3 has no
   `--dry-run` and errors on the flag: treat it as below the pin, step 3.
3. **`uv self version --short` below `UV_VERSION`:** offer `uv self update $UV_VERSION`, which
   takes a target version; stop if declined. Equal or newer passes. The comparison is numeric per
   dot-separated field, in `awk`: `sort -V` is not POSIX. No output text is parsed anywhere — the
   exit code and `--short` are the whole interface.
4. **Hand off:** `exec uv run --script <helper> "$@"`. From a clone, `<helper>` is the file beside
   the shim; piped from the web, a `raw.githubusercontent.com` URL at the same pinned ref as the
   shim, which `uv run` accepts.

Hard means hard: no `--skip-uv-check`, and no allowance for Homebrew or pip installs. The helper
may then assume a standalone `uv` at or above the pin. Never
`set -o pipefail` or `[[ ]]`, `local` or arrays: `/bin/sh` is `dash` on Ubuntu (and on the
author's WSL) and macOS's `sh` is bash in POSIX mode, so CI covers both.

**The helper: a `uv run` script with PEP 723 inline metadata.** `requires-python` and its
dependencies in the header, plus `[tool.uv] exclude-newer` so a run months later resolves the same
versions. Subcommands, each re-runnable:

- `doctor`: report, change nothing. `uv` (already gated), `copier` and `prek` as uv tools and
  their versions, git identity, copier's settings file, `gh` installed and authenticated.
- `setup`: `uv tool install` or `uv tool upgrade` copier and prek; write copier's settings file
  from `git config`, offering the GitHub noreply address from `gh api user` (`id` and `login`)
  when `gh` is authenticated, since its default token cannot read a private email. Never
  overwrite a settings file without showing the diff and asking.
- `new <dir>`: `copier copy --trust` from the CLI template, after `doctor` passes.
- `pins`: show each pin beside the latest release — `uv` first, later the hook revisions and
  the dependency floors that phase 8's pin automation names — and with `--update <name>` move one
  everywhere it is written, on a branch, ready for the gate and `finish_branch.py`. The easy,
  deliberate update that the pin trades for always-latest; a scheduled workflow can call it later.
- `update`: in a project, the README's two-layer flow — clean tree, branch, `copier update`, `uv
  sync`, commit, the base the same way, then `tools/finish_branch.py`. Stops at a conflict and
  says how to resume. The flow is spelled out in both READMEs, so this replaces prose a user had to
  follow by hand.

It is held to the template's own rules (no `print`, a stderr logger, functions small enough to
step through), so it is a real example of the uv-script skill from step 9: build the skill first,
then this by following it.

**What step 9 settled for the helper** (2026-10-16). The skill's rules hold here with three
differences from a generated project. The root `.pre-commit-config.yaml` has no ty hook, so the
helper needs the same local hook the template now ships (it will then check
`tests/test_template.py` too, for the first time). Its tests import it as a top-level module from
the root, so the root `pyproject.toml` needs `pythonpath = ["."]`. And its header's
`requires-python` must be the root's floor, 3.14, unless the root's ruff `target-version` is
lowered with it: ruff rewrites syntax up to the target and ty checks the script at the header's
version. The header goes first in the file; the shim's `exec uv run --script <helper>` and the URL
form are unaffected.

**Decided 2026-10-17** (were open):

- **Names: `bootstrap.sh` and `bootstrap.py`**, at the root. Neutral, says what it does, and
  avoids `setup.py`, which reads as setuptools.
- **Stdlib `argparse`, no dependencies.** Nothing to download on a bare machine and nothing to
  declare twice (header and the root's dev group); five subcommands do not need typer.
- **copier as a uv tool the helper drives**, not a library: `setup` installs it anyway, and the
  READMEs' `copier update` commands stay true.
- **Run from a clone only, for now.** `curl … | sh` needs a tag or a commit in the URL, never
  `main`, so it waits for phase 8's tagging. The shim's step 4 has the clone form only until then.

**Built so far** (2026-10-17, branch `feat/bootstrap-shim`): `bootstrap.sh`, `bootstrap.py`
with `doctor`, `tests/test_bootstrap_sh.py` and `tests/test_bootstrap.py`; shellcheck
(`shellcheck-py`, `--shell=sh`) and the template's local ty hook in the root gate; the pin in the
root and template pyprojects and both setup-uv steps here. What differs from the plan above, and
why:

- **The pin is 0.12.21**, the uv every test had run on, not the latest (0.13.1): a floor, so
  nobody is pushed to update for nothing. `pins --update uv` moved it to 0.12.24 on 2026-10-17.
- **The shim checks the version first, then `--dry-run` only at or above the pin.** In the
  planned order, a uv older than 0.7.3 fails `--dry-run` with the same exit 2 as a Homebrew uv,
  and telling them apart would mean parsing text. Below the pin, `uv self update <pin>` is itself
  the self-update check; a uv too old for `self version` reads as `0` and takes that path.
- **The shim puts uv's directory first on PATH before the hand-off.** A uv it just installed is
  on no PATH, so the helper's own `uv` calls failed (`FileNotFoundError`), found only by running
  it on a bare HOME: `env -i HOME=<empty> PATH=/usr/bin:/bin sh bootstrap.sh --yes doctor`.
  The CI-only test now runs `doctor` that way, not `--help`, which never called uv.
- **The installer's output goes to stderr**: stdout is the helper's report.
- **`--yes` and `-v` go before the command** (`sh bootstrap.sh --yes setup`): the shim reads only
  `$1`, and argparse takes top-level options only there. The helper accepts `--yes` already;
  `setup` is the first command to use it.
- **`doctor`** reports uv, copier and prek from `uv tool list` (the one parsed output: lines
  `name vX.Y.Z`), git's `user.name` and `user.email`, copier's settings file (copier's own
  per-platform path, or `COPIER_SETTINGS_PATH`) and `gh auth status`. The settings file and gh
  are advice (`warn`) and never fail it; anything else exits 1. Every probe of the machine is a
  `Probe` field, so the tests run it on a fake machine.
- **`setup`** (branch `feat/bootstrap-setup`) runs `uv tool upgrade` for each tool `uv tool list`
  shows and `uv tool install` for the rest, then writes copier's settings: `defaults:` with
  `author_name` and `author_email` from `git config`, as JSON-quoted strings, which are valid YAML,
  so there is still no dependency. It ends with `doctor`'s report and exits 1 if a step failed even
  when the report is clean. Tool installs ask nothing: running `setup` is the consent. Only
  replacing a settings file that differs asks, after a unified diff on stderr; with no terminal and
  no `--yes` it refuses, names `--yes` and exits 1; a "no" at the prompt leaves the file and is not
  a failure. No `user.name` means no settings file. The noreply address
  (`<id>+<login>@users.noreply.github.com`, from `gh api user` as JSON) is offered only at a
  terminal and only when it differs from git's email; `setup --noreply` takes it without asking,
  and with no terminal git's email wins. `Probe` gained `confirm` and `interactive` for this. Run
  for real through the shim with `UV_TOOL_DIR`, `UV_TOOL_BIN_DIR` and `COPIER_SETTINGS_PATH`
  pointed at a scratch directory: first run, rerun (`unchanged`) and refusal all as designed.
- **`new <dir>`** (branch `feat/bootstrap-new`) runs `doctor` and stops on a failed required
  check, with the report on stderr and `setup` named as the fix; refuses a destination that is a
  file or a directory with anything in it; then runs `copier copy --trust <template> <dir>` with
  the terminal attached, copier's stdout sent to stderr, so the helper's stdout is only the new
  project's absolute path (`cd "$(sh bootstrap.sh new my-project)"`). `--template` (default the
  CLI template's `gh:` URL) points it at a local checkout; anything after `--` goes to copier as
  is. `Probe` gained `attach`, the run that keeps the terminal. copier missing from PATH while a
  uv tool names `uv tool update-shell`. Run for real through the shim against both local checkouts,
  with `--defaults --data ...` after `--`: exit 0, path on stdout, both answers files agree.
- **`pins`** (branch `feat/bootstrap-pins`) shows the uv pin beside PyPI's latest
  (`pypi.org/pypi/uv/json`, no token), as `warn` when behind, exit 0 either way. `--update uv`
  (`--to VERSION`, default the latest; `--cli-repo`, default the sibling clone) moves every copy,
  here and in the CLI repo, on `build/uv-<version>` cut from `main` in each, committed with
  `SKIP=generation-tests` (the CLI repo's suite would test against the base on GitHub, whose pin
  has not moved), then prints the finish-and-push order. Nothing changes until both checkouts are
  clean and every copy holds the current pin. The copies are the `PinSite` table in
  `bootstrap.py`; the agreement tests in both repos stay independent of it, so they check its
  work. Run for real on scratch clones with a uv 0.13.1 installed there (its receipt kept there by
  `XDG_CONFIG_HOME`): both branches committed, and both went through `finish_branch.py`, the CLI's
  with `BASE_TEMPLATE_DIR`, full suites green. That run found three things the fakes could not:
  - **A floor above the running uv stops every `uv run`**, the commit's own `ty` hook first, so
    `--update` refuses until `uv self version` reaches the target, naming `uv self update <v>`.
  - **`uv-pre-commit`'s `rev` is a copy too**: its `uv-lock` hook runs the uv of its rev, which the
    floor refuses, so a generated project's gate failed. It is an `at_least` site, raised only
    when below the new pin (an autoupdate may run it ahead), and the base's agreement test now
    asserts rev ≥ pin. The CLI template's `uv_build>=0.12.21,<0.13.0` is not a copy: its suite
    passed at 0.13.1 as it is. It belongs with phase 8's dependency floors.
  - **Never `git commit --all` where a hook runs git elsewhere.** It hands hooks a temporary
    `GIT_INDEX_FILE`, which every git they start inherits, so the generation suite's projects
    failed with `invalid object` and `unable to read`. `pins` stages by name; so should anyone
    committing here by hand while `generation-tests` is in the gate.
- **`update <project>`** (branch `feat/bootstrap-update`) runs the README's two-layer flow:
  `doctor` and copier on PATH, as `new`; a clean checkout on `main` or `chore/template-update`
  (anything else is refused, so a resumed run is the same command); then each answers file present,
  `.copier-answers.base.yml` first (the use case went first until the canary's run, above), as
  `copier update --trust -a <file> [args after --] <project>` at the terminal, `uv sync`, and
  `git add --all` plus a commit named for the layer and its new `_commit` (`_src_path`'s last
  part: `python-template-base`). The branch is made only at the first commit or conflict, so an
  update that changes nothing leaves none. Checked by hand on scratch copies (2026-10-17) before
  it was written: **copier exits 0 on a conflict**, writing markers and recording each file as
  unmerged, so the helper reads `git diff --name-only --diff-filter=U`; an
  update already current exits 0 and changes nothing; an unknown `--data` key is ignored, so args
  after `--` go to both layers; and `git switch --create` carries unmerged paths along. A conflict,
  a failed `uv sync` or a commit the hooks refuse stops it with the steps to carry on (resolve,
  `uv sync`, commit with the message it names, rerun). stdout is one report line per layer reached
  (`a -> b`, or `already at`); `--finish` runs the project's `finish_branch.py`, otherwise it
  prints that command. Run for real through the shim on a project generated from scratch clones of
  both templates: no-op, conflict stop, resume with `--finish` (merged `--no-ff`), and a second
  update without it. That run found **`uv run --script` exports `VIRTUAL_ENV`** for the helper's
  own environment, and every uv in the project warned it was ignoring it; `uv sync`, the commit
  and `finish_branch.py` now run without it. `Probe.attach` takes `env` for that, as `run` does.
- **`update` end to end** (CLI repo, branch `test/bootstrap-update`):
  `test_the_setup_helper_updates_both_layers_on_a_branch` snapshots both templates, moves each
  forward, and runs `uv run --script <base_checkout>/bootstrap.py update <project> -- --defaults`;
  it asserts both markers, the branch, one commit per layer by subject (the use case's newest) and a
  clean tree. About five seconds warm. Not CI-only after all: it skips locally unless copier and
  prek are uv tools, and on CI both workflows `uv tool install` them for it. doctor's git identity
  comes from `git config`, which never sees CI's `GIT_AUTHOR_*`, so the test hands the helper a
  `GIT_CONFIG_GLOBAL` file. The CLI README now names `sh bootstrap.sh update` beside the manual
  flow, linking to the base README's details; the generated `README.md.jinja` does not, since a
  project ships no `bootstrap.sh` and its README already links to the CLI README's section.
- **Not a bug after all: copier settings and the base layer's author defaults.** The `setup`
  session read copier's `settings.defaults.get(name, question.default)` and concluded a settings
  file overrides the base's `_external_data` defaults when the CLI task applies the base, so
  `.copier-answers.base.yml` would disagree with `.copier-answers.yml`; it planned a `--data` fix
  in the CLI repo's `_tasks`. Running it disproved that: with a settings file naming other values,
  the base recorded the use case's answers. The reason: on `copy`, copier reads *last answers*
  from `-a`, or else `.copier-answers.yml` — never from the template's `_answers_file`
  (`Worker.subproject`, unchanged in 9.18.2 and 9.19.1). So the base's copy sees the use case's
  answers file as its own last answers, and last answers outrank settings. Nothing to fix. It
  also means the base's `_external_data` defaults never decide a layered copy; whether they still
  earn their place is for a later review, not the helper.

**Tests:** shellcheck with `--shell=sh` in the root gate. The shim's branches tested with a stub
`uv` on PATH for each case (missing, not self-updatable, below the pin, at it, above it), plus one
against the real `uv` on CI. A test that every copy of the pin agrees. The helper's
subcommands tested with `git`, `gh` and copier stubbed or pointed at a tmp directory; `update`
end-to-end in the CLI repo's suite, which already has projects to update.

## Phase 8 — CI, releases and updates (after phase 10)

Done: CI for this repo (2026-10-15), under "Done" above.

- [ ] **CI shipped in generated projects**: `prek run --all-files` and `uv run pytest`, so a
  generated tool is checked away from its author's machine too. Base-owned, so it waits only so
  that nothing under `template/` moves twice. **A consumer's private repo pays for it**: a Free
  account has 2,000 minutes a month, and Windows and macOS burn the quota faster, macOS at about
  ten times Linux. Ship Linux only, with Windows and macOS commented in; run on pushes to `main`
  and on pull requests, not on every branch push.
- [ ] **Pin automation.** Mostly superseded by D16: step 3 left no hook rev to move. What is left
  is the dependency floors, which drifted 10–20 releases in two months and live in each use case.
  A scheduled workflow or Renovate, gated by the generation suite.
- [ ] **Tagging** (D5), one tag series per repo. **Once any tag exists, `copier update` moves to
  the latest PEP 440 tag rather than `HEAD`** unless given `--vcs-ref HEAD` — right for stable
  releases, wrong while iterating, because fixes stop reaching the canary until tagged. Stay
  untagged until the canary settles, then cut `v0.1.0`. The README's example now pins a commit.
- [ ] **Per-release update notes.** The README's "Keeping it in sync" covers the update mechanics.
  A release should also say what a conflict never will: which features were absorbed from
  consumers (`typer_entrypoint.py` superseded the canary's own version, with changed semantics),
  and which interface moves a consumer's own commands must follow (`-v/--verbose` went global, so
  `tdf-cli weather -v cleve` became `tdf-cli -v weather cleve`, and nothing warned).

## Later

- **A `seal` command for downstream projects** (D16). A project that has settled, and wants its
  toolchain frozen, runs one command that records what it runs now: an exact `required-version`,
  exact `uv tool` versions for prek and copier, and the hook revs as they stand. It runs in a
  generated project, never in the templates. Open: where it lives (`bootstrap.py`, or `tools/` in
  the base), and how a sealed project's `copier update` keeps the seal when the base's files move.
- **The Textual console**, attached through `TEXTUAL=devtools,debug`, is unverified by hand. The
  mechanism is read from `textual_dev/cli.py`; it needs two real terminals to see.
- **DebugMCP on Windows native.** The agent-session half is done in WSL. Still unverified, and
  needing a session started on Windows itself: the `cmd /c` registration, `uv` resolving as the
  adapter command, and both adapters launching through it, including the `python` adapter's
  launcher, proven so far only on Linux. CI proved on 2026-10-15 that the exec-form hooks' `uv`
  and `git` resolve there. Known CLI gaps, worked around in the skill rather than fixed: it ignores
  `launch.json`; it always sets `program`, so pytest and every `src/` module need a launcher, and it
  cannot pass program arguments; complex values render as dunder trees unless wrapped in `repr()`;
  the debuggee's output and logpoint output are not captured.
- **The DebugMCP VS Code extension.** Deferred by choice. It drives VS Code's own debugger over
  HTTP on `localhost:3001` and reuses `launch.json`, but uses the interpreter selected for the
  *open window*: from a `python-template` window it launched the system Python and failed to import
  the package. Open: two windows contending for one port, and coexisting with the CLI, since
  `debugmcp configure` keeps a single `debugmcp` entry.
