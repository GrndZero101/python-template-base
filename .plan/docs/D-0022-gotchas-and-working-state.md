---
id: D-0022
title: Gotchas and working state
kind: note
status: approved
tasks: []
created_at: '2026-11-22T21:45:04Z'
updated_at: '2026-11-22T21:45:05Z'
---

What a fresh session would otherwise relearn, carried over from the old `TODO.md` on 2026-11-23.
Each line was hit at least once. The rules themselves are in `CLAUDE.md`; the decisions are the
ADRs D-0001 on.

## The three repos and the projects

- **Base**: this repo. Its suite generates the base alone and runs that project's gate (about
  fifteen seconds warm). Finish with
  `uv run python template/tools/finish_branch.py --no-tests "<type(scope): summary>"`.
- **CLI**: `../python-template-cli-typer`, seeded from this repo's history by plain clone, so every
  old hash survives. Its suite (about 48 tests) generates through the CLI template with the base
  layered on; `BASE_TEMPLATE_DIR` names a base checkout, and without it the tests use the base on
  GitHub. It has no `tools/` and no hooks of its own, by decision, and no `.claude/`: the base's
  hooks skip a file in a sibling repo (`owning_repo` in `hook_payload.py`), so edits there are
  ungated until commit. Its `CLAUDE.md` is not loaded for an added directory: read it first.
- **The canary**: `GrndZero101/python-canary-cli-typer`, public, at `d3a04c3` (2026-11-23). Answers:
  the CLI at `0d61a6b`, the base at `da66891`; `ci: github`, kept Linux only by the author. Package
  `python_canary_cli_typer`, script `tdf-cli`. Its history was rewritten on 2026-10-15, so canary
  hashes from before then exist nowhere. **Drive it from a session started in its own directory**:
  hooks and skills load from the session's project. Rehearse an update on a scratch clone
  (`_src_path` edited, `copier update --trust --defaults --vcs-ref <branch>`); it predicts the real
  one exactly.
- **gdt**: the first real project, on Windows native. Its field reports are in gdt's memory,
  `template-findings.md`; findings 1–21 are acted on. Findings come back as template fixes made from
  a session here, never as edits to gdt's base-owned files.
- A repo can lose its git shims (the canary and the CLI repo both have). The `SessionStart` doctor
  reports it; `prek install -t pre-commit -t commit-msg -t pre-merge-commit` restores them.

## Pushing and CI

- Each repo's CI checks the other out (`base/` there, `cli/` here) and ignores that directory in
  `.gitignore`: copier reads an untracked nested repository as a submodule with no `.gitmodules`.
- The CLI repo's CI uses the base's GitHub `main`, so push the base first when a CLI change depends
  on it. A change that must land in both at once fails the base's CI whichever goes first: push the
  CLI half straight after, then `gh run rerun <id> --failed` the base's run.
- Windows CI is opt-in (`gh workflow run ci.yml --ref <branch> -f windows=true`). Warm times on
  2026-10-16 with the CLI suite: Ubuntu 1m26, macOS 4m10, Windows 14m23. `ubuntu-latest` is Ubuntu
  26.04 and has passed (2026-11-22).
- Running two generation suites at once has failed a test that passed alone. Run suites one at a
  time before reading a failure as real.

## copier

- The operation variable is `_copier_operation`; `_copier_conf.operation` renders undefined, which
  silently disables every task. Every `_task` is guarded with
  `when: "{{ _copier_operation == 'copy' }}"`, or an update re-runs them.
- **copier exits 0 on a conflict**, writing markers; read `git diff --name-only --diff-filter=U`.
- `copier update` deletes every file the old render had and the new one lacks, with no check for
  local edits (`_remove_old_files`). Renaming the package re-renders `src/<package>/` at the new
  path: the canary's `cli.py` silently lost a command's registration.
- **A project's local fix, once upstreamed, merges back as a silent duplicate, not a conflict**
  (gdt's finding 17): both versions survived the three-way merge, and only ruff's F811 caught it.
- On `copy`, copier reads last answers from `-a`, else `.copier-answers.yml`, never the template's
  `_answers_file` (`Worker.subproject`). So the base's layered copy sees the use case's answers,
  and a settings file never overrides them.
- An unknown `--data` key is ignored, so arguments after `--` in `bootstrap.sh update` reach both
  layers. Under `--defaults` a new question takes its default: pass `-d <key>=<value>`.
- On Windows, from a shell that is not a real console, copier's prompts raise
  `NoConsoleScreenBufferError`: use `--defaults`. copier's settings are at
  `%LOCALAPPDATA%\copier\settings.yml`.
- Harmless noise: `DirtyLocalWarning` from a local template, a base update's `MissingFileWarning`
  for `.copier-answers.yml`, and "Make sure Git >= 2.24 is installed" beside git 2.56.
- An agent may run `--trust` (auto mode allowed it, 2026-10-17); the tasks are copy-only, so an
  update runs none of them.

## git, uv and the hooks

- **Never `git commit --all` where a hook runs git elsewhere.** It hands hooks a temporary
  `GIT_INDEX_FILE`, which every git they start inherits; the generation suite's projects then fail
  with `invalid object`. Both repos' `tests/conftest.py` drop git's repo-local variables in
  `pytest_configure`, from `os.environ` and plumbum's `local.env`. Stage by name.
- `uv run --script` exports `VIRTUAL_ENV` for the script's own environment; strip it before running
  uv in a project, or every uv there warns.
- A directory moved on disk leaves `.venv` pointing at the old path (`Failed to spawn: pytest`):
  `rm -rf .venv && uv sync`.
- `uv tool install` leaves an installed tool at its version: use `uv tool install --upgrade`. An
  editable install keeps its old `--version` until `--reinstall`.
- Decided against (2026-10-04): a `PostToolUse` hook on `Bash`, and a per-session stop-gate
  checkpoint. Bash writes skip the edit-time gate by design; the stop gate and `finish_branch.py`
  are the backstop.

## Linters and tests

- ruff at py314 rewrites `except (A, B):` to `except A, B:`, a syntax error at a 3.12 floor. Code
  that must survive `ruff --fix` at every floor uses one `except` per type.
- `pytest.raises(match=)` is a regex: `re.escape` a Windows path's `repr()`.
- rumdl 0.3.5 added MD076; both repos use `reflow = true`, and `prek run rumdl-fmt --all-files`
  rewraps. Under the CLI layer reflow rewraps files `rumdl check` passes, so shipped markdown is
  wrapped in the template itself.
- Windows runners check out with `core.autocrlf=true`, as users' Git for Windows does; nothing broke
  on CRLF, and `.gitattributes` sets `eol=lf` anyway.

## Windows native

- From PowerShell, `bash` is WSL's: set `TP_VERIFY_SHELL` (D18). Claude Code's Bash tool is Git
  Bash.
- typer's PowerShell completion line in `$PROFILE` works only with its `Remove-Item Env:`.
- Walked on 2026-10-18 from `powershell.exe`: generation, the gate, the tests, `git switch` and
  `bootstrap.py doctor` all worked. Not walked: a fresh uv install, copier's interactive prompts,
  `setup` writing the real settings file (a task).
- The hooks run in real interactive sessions on Windows: gdt's field reports came from them, and
  its first `copier update` (2026-10-21) proved the gate's pause on conflict markers.
