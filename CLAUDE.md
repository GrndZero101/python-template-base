# Working on this template repository

This repo is the **base** of a [copier](https://copier.readthedocs.io/) template in two layers,
applied to the same project. The root is **not** a Python project.

- **The base** is the root `copier.yml` plus `template/`: the hooks, `tools/`, `CLAUDE.md`, the
  shared skills and a fallback `pyproject.toml`. It also stands alone, for a prototype or a repo
  adopting the guards.
- **A use case** is a template of its own, in a repository of its own, with its own `copier.yml` and
  `template/`. [python-template-cli-typer](https://github.com/GrndZero101/python-template-cli-typer)
  is the typer CLI. Its one task applies the base to the same directory, so one `copier copy`
  yields both layers, each with its own answers file.

@template/CLAUDE.md

The rules imported above govern every file under `template/` — that is the code being shipped, and
it is held to exactly the standard it preaches. A use case's repository holds its own code to the
same rules. What follows is only what differs at this level.

## Layout

| Path | What it is |
|---|---|
| `template/` | The base layer of a generated project. Holds Jinja; not runnable in place. |
| `copier.yml` | The base's questions, exclusions and bootstrap tasks. |
| `tests/test_template.py` | Generates the base alone and runs its gate. CI adds the CLI repo's suite. |
| `.pre-commit-config.yaml` | Governs **this** repo. `.git` is here, so this is what the git hooks read. |
| `pyproject.toml` | Dev deps and lint config for the root. Not published, not importable. |
| `bootstrap.sh`, `bootstrap.py` | The setup helper: a POSIX `sh` shim that installs or updates `uv`, then a uv script. Not shipped. |
| `tests/test_bootstrap*.py` | The helper's tests: the shim against a stub `uv`, the script on a fake machine. |
| `.plan/` | The `tp` store for all three repos' work: tasks, ADRs and notes. Not shipped. |
| `.claude/skills/taskplan/` | How to work with `tp`, written by `tp init --claude`. Not shipped. |
| `TODO.md` | `tp`'s board, regenerated on every write to the store. Never edited by hand. |

**Every generated file has exactly one owner**: it is rendered by the base or by a use case, never
both. Two templates rendering the same path conflict on `copier update` (markers in the file), so
the split is by directory and a test in the CLI repo's suite checks it. The base owns `CLAUDE.md`,
`tools/` and its tests, `.claude/settings.json`, `.pre-commit-config.yaml`, `.gitignore`,
`.gitattributes`, `.python-version`, `LICENSE`, `.debugmcp.json`, `.vscode/`, `ruff-base.toml`, the
skills `git-workflow`, `python-debug`, `python-cli` and `python-uv-script`,
`.copier-answers.base.yml`, and `.github/workflows/ci.yml` when `ci` is `github`. The one exception
is `pyproject.toml`, which the use case owns: the base also renders a minimal one under
`_skip_if_exists`, which copier never overwrites, so it reaches only a project that has none. The
use case owns `pyproject.toml`, `README.md`, `src/`, `tests/`, `.copier-answers.yml`,
`.claude/rules/cli-typer.md` and the skills `python-cli-typer`, `python-data` and `python-tui`.

A file under a `template/` — this one, or a use case's — carries a `.jinja` suffix only when it
must name something the answers decide:

- the project files `pyproject.toml`, `README.md`, `LICENSE`, `.pre-commit-config.yaml`,
  `.copier-answers.yml`, `.copier-answers.base.yml` and `.python-version`;
- in a use case, the source and test modules that name the script or import the package, which the
  CLI repo's `CLAUDE.md` lists;
- the `python-uv-script` skill's reference script, whose header carries the project's Python floor
  and the date it was generated.

Everything else — `CLAUDE.md`, all of `tools/`, every other skill file — ships literally. The
shipped CI workflow does too, since its `${{ }}` expressions would read as Jinja; the condition is
in its directory's name, `{% if ci == 'github' %}.github{% endif %}`, which renders empty and so
is skipped under `none`.

## The two gates

`.git` sits at the root, so `prek install` wires the git hooks to the **root** config. That config
owns the commit-level rules — the message check and `no-commit-to-branch` — lints the repo's own
markdown, and lints the root's own Python and shell: the tests and the setup helper.

**`template/` is not checked in place, and cannot be.** It contains Jinja and has no
`pyproject.toml` — only `pyproject.toml.jinja` — so `ruff` would fall back to default rules and `ty`
would find no environment. Its `.pre-commit-config.yaml` is suffixed `.jinja` for the same reason:
that keeps prek from picking the directory up as a workspace member and running a gate there that
is guaranteed to fail.

What covers it instead is `tests/test_template.py`. It generates the base **alone** and runs
**that project's** gate and test suite inside it. This is the stronger check of the two — it
verifies the thing that actually ships rather than the thing it is made from — and it costs about
fifteen seconds. It runs at commit, and only when the commit touches something that can change a
generated project: `template/`, `tests/`, `copier.yml`, `pyproject.toml` or `uv.lock`. A commit of
`.plan/` and `TODO.md` alone skips it. To skip it deliberately anyway:

```bash
SKIP=generation-tests git commit -m "..."
```

Copier includes uncommitted working-tree changes when the template is a local path (it warns
`DirtyLocalWarning`), so the tests validate what you are about to commit, not the last commit.

**The base layered under a use case is not checked locally.** That is the CLI repo's suite, which
generates through the CLI template and runs the full gate, the hooks' tests and the update tests.
Run it against an unpushed base change with `BASE_TEMPLATE_DIR=$PWD uv run pytest` in a clone of
python-template-cli-typer. Most of what the base ships — the hooks, the gate, `finish_branch.py`,
the licence — is exercised only that way.

On a push that touches what `generation-tests` watches, the root gate's config or the workflow,
`.github/workflows/ci.yml` runs the root gate on Linux, then on Linux and macOS this repo's suite
and the CLI repo's, checked out into `cli/` with this checkout as the base — the only automatic
check of the layering. A docs-only push runs nothing. Push a branch to see macOS before merging.
On CI (`CI=true`) a test needing `uv`, `prek` or `copier` fails rather than skips when the tool is
missing. Nothing in the toolchain is pinned: CI installs `prek` and `copier` as uv tools, and syncs
with `--upgrade`, since the suite's own `copier` comes in through pytest-copie.

Windows runs only when asked: `gh workflow run ci.yml --ref <branch> -f windows=true`. The targets
are Unix-alikes, and Windows took ten times Linux's time, so it is checked at milestones and in work
aimed at it, not on every push. That run is the only check of the portability rules away from a
Unix-alike, so they rest on review in between.

The edit-time `PostToolUse` gate uses `find_gate_root` in `template/tools/hook_payload.py`, which
walks up from the edited file to the nearest `.pre-commit-config.yaml`, bounded by the repo root.
Inside a generated project that lands on the root, which is the case it exists to serve. In *this*
repo every file resolves to the root config, and that config excludes `^template/` — so editing
something under it is not gated as you type. The root's hook passes
`--skip no-commit-to-branch,generation-tests` explicitly, so a save never pays for the generation
suite either; the generation test catches template edits at commit instead. Editing a root file the
config does not match, such as `TODO.md`, likewise leaves the gate standing down rather than
blocking.

The `Stop` hook is registered here the same way, with `--skip no-commit-to-branch,generation-tests`
and `--no-tests`: the root's test suite *is* the generation suite, which a stop should not pay for.
It still gates every changed root file before a turn ends, and, like the edit-time gate, it cannot
see into `template/`.

## Commands

Run from the repo root:

```bash
prek run --all-files            # the whole gate, generation test included (~15 s)
uv run pytest                   # the generation test only
copier copy --trust . /tmp/scratch    # the base alone, by hand, to poke at the result
```

`template/` has no venv and nothing to run — `uv run --directory template` no longer works, because
there is no `pyproject.toml` there to run against.

The hooks no longer care where the shell is. They are exec form, launched with
`--directory ${CLAUDE_PROJECT_DIR}`, so a `cd` into `template/` or another repo cannot make them
resolve the wrong script. Prefer `git -C <dir>` anyway: it keeps every command's context explicit.

## Branching

Identical to the imported rules: never edit on `main`, branch first, `main` receives only merge
commits. The `PreToolUse` guard runs from the root and covers the whole repo, `template/` included.

Finish a branch here with the template's own script, which runs unchanged from the root:

```bash
uv run python template/tools/finish_branch.py --no-tests "feat(x): summary"
```

It runs the root's whole gate before merging, generation test included: about fifteen seconds.
`--no-tests` because that test *is* this repo's suite, so running it again would double it.

<!-- taskplan:begin -->
## Task tracking

This repo tracks work with `tp` (see .claude/skills/taskplan). Never keep plans only in context.

- Start of session / after compaction: `tp status`, then `tp next`.
- Work one task at a time: `tp start ID` → implement → `tp done ID --commit-head`.
- Record decisions and dead ends with `tp note ID "..."`.
- If stuck after 2 attempts: `tp block ID --reason "..."` and move to `tp next`.
- Never edit .plan/*.jsonl by hand.
<!-- taskplan:end -->

**One store for three repos.** `.plan/` here holds the work of this repo, of
python-template-cli-typer and of the canary, each task tagged `base`, `cli` or `canary`
(`tp list --tag cli`). A session started in the CLI repo or the canary reaches it with
`--root ../python-template-base` or `TP_ROOT`; a verify command always runs from this root, so one
for the CLI repo names `../python-template-cli-typer`. A field finding from a generated project
becomes a task tagged by the layer it touches, with `--meta source=<project>`.

- **Decisions are ADRs**: `tp doc list --kind adr`. D-0001 to D-0017 are the old decision log's D1
  to D17, which code and tests cite by number; new ones carry on from there
  (`tp doc new "D22: ..." --kind adr`). Anything waiting on an outside event is `blocked` with that
  event as its reason.
- **Read the note "Gotchas and working state"** (`tp doc list --kind note`) before a step that
  touches copier, CI, the canary or Windows: it is what earlier sessions learned the hard way. Add
  to it when something bites.
- **`TODO.md` is generated** (`board_file` in `.plan/config.toml`). The root gate leaves it alone.
- **The verify shell is `bash`.** On Windows native that is right from Claude Code's Bash tool (Git
  Bash), but from PowerShell `bash` is WSL's, so the Windows user variable `TP_VERIFY_SHELL` names
  `C:\Program Files\Git\bin\bash.exe` (D18). Write verify commands in POSIX `sh`.
- tp's own Stop hook is not registered (`max_stop_blocks = 0`): the root's Stop gate is enough.

## How work is judged

- **Three goals** (2026-10-02): well-structured DevOps and QOL CLI tools; code a person can
  maintain and step through; and token efficiency — a sonnet-class model builds a good tool cheaply
  because the skills, tooling and hooks carry the knowledge. **Sonnet is the baseline**; haiku is an
  occasional stretch run whose findings are acted on only when the fix is a cheap mechanical check
  that helps any model.
- **Machinery has a budget** (2026-10-04). Add a hook, module or stored state only for a defect
  that actually reached `main`; prefer extending an existing check (`finish_branch.py`, the
  `pre-merge-commit` hook, the stop gate) over a new one; and verify a reviewer's claim against the
  code before acting on it.
- **Prefer a mechanical check, a script or a copyable reference file** to more prose in
  `CLAUDE.md` or a skill. A specific, greppable name in `CLAUDE.md` (`build_client`) steered haiku
  where a docstring pointer did not.
- **Done means**: the generation suite and `prek run --all-files` pass; anything that changes what
  a skill tells a model has been run through a generated project's gate, not just read; and work
  that changes what generated projects receive ends with a `copier update` of the canary.
- **Format template code in a generated project before committing.** `template/` is not linted in
  place, so a formatting slip surfaces only in the generation suite, at commit. Generate a scratch
  project, copy the file in, `prek run ruff-format`, copy it back.

## How work runs

**Sequential: one session, one branch, one task at a time** (2026-10-15). No side tracks in git
worktrees: the author reviews every decision and merge, so a second track mostly adds context
switching; each session pays its own context, against goal 3; two local generation suites slow
each other down and have failed tests that pass alone; and `finish_branch.py` ends by switching to
`main`, which git refuses while another worktree has it checked out. Read-only work — a review, an
audit — is still a session started where the files are.

**A task in both template repos is one session** (2026-10-18), started here with
`--add-dir ../python-template-cli-typer` (or `/add-dir` mid-session):

- This repo's hooks, `CLAUDE.md`, skills and memory load as usual.
- The CLI repo has no `.claude/` of its own, and the base's hooks skip a file in a sibling repo by
  design (`owning_repo` in `hook_payload.py`), so its edits are ungated until commit. Its prek git
  hooks still run at commit, and `finish_branch.py` gates it in full.
- Its `CLAUDE.md` is not loaded for an added directory: read it before the first edit there.
- Git there is `git -C ../python-template-cli-typer`. Its suite and its finish run inside it,
  pointed at this checkout, each as one command:
  `cd ../python-template-cli-typer && BASE_TEMPLATE_DIR=<base> uv run pytest`, and the same with
  `uv run python <base>/template/tools/finish_branch.py --no-tests "<summary>"`.

The order of work: the base half, then the CLI half, then the pushes, base first, and the base's CI
rerun if it ran before the CLI half landed. Starting in the parent directory was rejected: it has
no `.claude/settings.json` or `.git`, so no hook would run in either repo. The canary is driven from
a session started in its own directory, since it has hooks of its own.

## Sessions and checkpoints

A long session gets slower and costlier per turn and drifts from what is written down; a fresh one
reads only `CLAUDE.md`, memory and `tp`'s session-start brief. So work is cut into sessions at
**checkpoints** (2026-10-15). At one: finish and merge the task, close it with `tp done`, and put
whatever a fresh session needs on the next task (`tp note`, `tp edit --desc`) — the store is the
hand-off, and a gap a fresh session finds is fixed there first. Then tell the user "Checkpoint:
start a new session", with the next task and the command that starts it, prompt included, and stop.

The prompt names the task by id and says what state it starts from (merged, pushed or not). Give the
command for the host the author is on (since 2026-11-23, Windows native). For a task in both
template repos, in PowerShell:

```powershell
cd C:\shares\projects\github\GrndZero101\python-template-base
claude "Do T-NNNN (tp show T-NNNN). <state>" --add-dir ..\python-template-cli-typer
```

On Linux, macOS or WSL:

```bash
cd ~/projects/github/GrndZero101/python-template-base && \
  claude "Do T-NNNN (tp show T-NNNN). <state>" --add-dir ../python-template-cli-typer
```

The prompt goes **before** `--add-dir`: that flag takes any number of directories, so a prompt
after it is read as a second directory and the session opens with no prompt.

A checkpoint falls:

- at the end of any task that ends mergeable;
- after a review is triaged and recorded — the session that made the decisions triages, since it
  holds the evidence, and a fresh one carries them out;
- when the next task needs another working directory: hooks, skills and memory all belong to the
  directory a session started in. The CLI repo does not count, since it is added to a session here,
  but the canary does;
- when `/context` shows the session past about half its window, at the next mergeable point.
