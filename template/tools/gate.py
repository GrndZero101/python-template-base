"""Run the quality gate against the file a tool just edited.

Claude Code `PostToolUse` hook. Exit 0 lets the edit stand; exit 2 blocks it and feeds
stderr back to the agent as the error to fix.

Delegates to `prek run --files <path>` rather than invoking ruff, ty and rumdl directly. That
matters for two reasons:

- **One list, not two.** The checks are declared once in `.pre-commit-config.yaml` and used by
  both this hook and the git hooks, so the edit-time gate and the commit-time gate cannot
  drift apart. The previous shell one-liner duplicated the list inside `settings.json`.
- **Portability.** A single executable invocation with no shell operators runs identically on
  Windows, Linux, macOS and in containers. The chained `&&` version needed a POSIX shell and
  failed *open* where none existed.

`prek run --all-files` is deliberately not used: it only sees tracked files, so a newly
created file — exactly what an agent produces — would go unchecked. Naming the path explicitly
covers untracked files too.

While any file still holds conflict markers — mid-way through a `copier update` or a merge — the
gate pauses and lists those files instead. `ty` checks the whole project, so every edit to one
conflicted file would otherwise reprint the syntax errors from all the others, burying the one
result that mattered.

Three things keep what the agent reads short and true:

- **Only failures, concisely.** `prek --quiet` drops the passed and skipped lines, and ruff and
  ty are told to print one line per finding. That is set here only, so the commit-time gate keeps
  the full code frames a person wants.
- **A re-run when prek only fixed things.** When a hook rewrites a tracked file — a reformat, a
  sorted import — prek reports "files were modified by this hook" and fails, although nothing is
  left to fix. The gate runs once more and reports that second result, so the agent is not sent
  to fix a problem that no longer exists.
- **No silent fail-open.** If prek cannot run at all, the edit still stands, but the agent is told
  the gate is off so it can tell the user, rather than carrying on as if it were checked.

One kind of failure is reported without blocking: an unused import or an undefined name, and
nothing else. A change spread over several edits passes through both — the import lands one edit
ahead of its first use, or the use one edit ahead of its import — and blocking there sent the agent
to "fix" a change it had not finished. The edit stands and the findings reach the agent as context.
The stop gate and the commit still fail on them, so one left behind cannot reach `main`.

Every run appends one line to `.gate.log` (see `gate_log.py`).
"""

import argparse
import dataclasses
import functools
import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from gate_log import HOOK_ID_LINE, Entry, Outcome, failed_hooks, record
from hook_payload import find_gate_root, find_repo_root, notice, owning_repo, target_path

BLOCK = 2
# The branch guard owns branch protection; running it here would fail every edit made on main.
SKIP_HOOKS = "no-commit-to-branch"
# The opening and closing markers git and copier both write, matched as check-merge-conflict
# matches them: at the start of a line, followed by a space and the side's label.
CONFLICT_PATTERN = "^(<<<<<<<|>>>>>>>) "
# One line per finding instead of a code frame. Read by ruff and ty in the gate's subprocess only.
CONCISE_ENV = {"RUFF_OUTPUT_FORMAT": "concise", "TY_OUTPUT_FORMAT": "concise"}
# prek's report for a hook that changed files, which it counts as a failure.
MODIFIED_MARK = "files were modified by this hook"
# prek repeats each hook's description under its name; it is the same text on every run.
DESCRIPTION_PREFIX = "- description: "
# What a change half-way through several edits looks like, as ruff and ty name it. Only these are
# deferred, and only from the hooks below; any other failure blocks as before.
DEFERRED_RULES = frozenset({"unused-import", "undefined-name", "unresolved-reference"})
DEFERRABLE_HOOKS = frozenset({"ruff-check", "ty"})
# One finding in concise output: `path:line:col: rule-name: ...` from ruff, and
# `path:line:col: error[rule-name] ...` from ty. A path may hold a drive letter's colon.
FINDING_LINE = re.compile(r"^\s*\S.*?:\d+:\d+: (?:\w+\[(?P<ty>[\w-]+)\]|(?P<ruff>[\w-]+):)")


@dataclasses.dataclass(frozen=True)
class GateResult:
    """Outcome of one gate run.

    `ran` is False when the command could not be started at all. `rerun` is True when the first
    run failed only on prek's own fixes and this is the second run's result.
    """

    code: int
    output: str
    ran: bool = True
    rerun: bool = False


Runner = Callable[[Sequence[str], Path], GateResult]
Scanner = Callable[[Path], list[str]]


def run_subprocess(
    command: Sequence[str], cwd: Path, extra_env: Mapping[str, str] | None = None
) -> GateResult:
    """Execute `command` in `cwd` and capture its combined output.

    The default runner. Injected as a parameter everywhere else so tests never shell out.
    `extra_env` is laid over the inherited environment rather than replacing it.
    """
    env = {**os.environ, **extra_env} if extra_env else None
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return GateResult(code=0, output=f"cannot run {command[0]}: {exc}", ran=False)
    merged = f"{completed.stdout}{completed.stderr}".strip()
    return GateResult(code=completed.returncode, output=merged)


run_concise = functools.partial(run_subprocess, extra_env=CONCISE_ENV)


def condense(output: str) -> str:
    """Drop the lines of prek's report that say nothing about this run."""
    kept = [line for line in output.splitlines() if not line.startswith(DESCRIPTION_PREFIX)]
    return "\n".join(kept).strip()


def build_command(paths: Sequence[Path], skip: str = SKIP_HOOKS) -> list[str]:
    """Return the prek invocation that checks exactly `paths`, reporting only failures.

    `skip` is comma-separated, but prek's `--skip` flag takes exactly one hook id and is
    repeated for more — only the `SKIP` environment variable splits on commas. Passed whole,
    `a,b` names a hook that does not exist, and prek skips nothing.
    """
    command = ["prek", "run", "--quiet", "--files", *(str(path) for path in paths)]
    for hook_id in skip.split(","):
        stripped = hook_id.strip()
        if stripped:
            command.extend(["--skip", stripped])
    return command


def find_conflicted(root: Path, runner: Runner = run_subprocess) -> list[str]:
    """Return the files under `root`, tracked or untracked, that still hold conflict markers.

    `git grep` prints paths relative to `root`. Anything in its output that does not name a file
    there is a diagnostic — git missing, `root` not a work tree — and the scan fails open on it.
    """
    command = ["git", "grep", "--untracked", "-I", "-l", "-E", CONFLICT_PATTERN]
    result = runner(command, root)
    if result.code != 0:
        return []
    lines = result.output.splitlines()
    return [line for line in lines if (root / line).is_file()]


def paused_message(conflicted: Sequence[str]) -> str:
    """Return what the agent is told while conflict markers remain."""
    listing = "\n".join(f"  {name}" for name in conflicted)
    return (
        f"gate paused: {len(conflicted)} file(s) still hold conflict markers, so every check "
        f"would report only their syntax errors. The full gate resumes once these are "
        f"resolved:\n{listing}"
    )


def check(paths: Sequence[Path], root: Path, skip: str, runner: Runner) -> GateResult:
    """Run the gate on `paths`, once more if the first run only applied fixes."""
    command = build_command(paths, skip)
    first = runner(command, root)
    if first.code == 0 or MODIFIED_MARK not in first.output:
        return first
    return dataclasses.replace(runner(command, root), rerun=True)


def _hook_sections(output: str) -> dict[str, list[str]]:
    """Group the lines of prek's report under the id of the hook that printed them.

    Each hook's name line precedes its id, so it lands at the end of the hook before. It is no
    finding, so where it lands does not matter.
    """
    sections: dict[str, list[str]] = {}
    current: list[str] = []
    for line in output.splitlines():
        match = HOOK_ID_LINE.match(line)
        if match is None:
            current.append(line)
        else:
            current = sections.setdefault(match.group(1), [])
    return sections


def _rules(lines: list[str]) -> set[str]:
    """Return the rule named by each finding among `lines`."""
    rules: set[str] = set()
    for line in lines:
        match = FINDING_LINE.match(line)
        if match is not None:
            rules.add(match.group("ty") or match.group("ruff"))
    return rules


def deferred_only(result: GateResult) -> bool:
    """Return whether every failure in `result` is a finding the edit-time gate only reports.

    A failed hook with no finding it can read — a crash, a config error — counts as a real failure.
    """
    if not result.ran or result.code == 0:
        return False
    sections = _hook_sections(result.output)
    if not sections:
        return False
    for hook, lines in sections.items():
        rules = _rules(lines)
        if hook not in DEFERRABLE_HOOKS or not rules or not rules <= DEFERRED_RULES:
            return False
    return True


def deferred_notice(output: str) -> str:
    """Return the non-blocking reply for findings an unfinished change passes through."""
    context = (
        "Not blocked, but not clean: an unused import or an undefined name, which a change made "
        "over several edits passes through. Finish the change. Any still here when you stop fail "
        f"the stop gate and the commit.\n{condense(output)}"
    )
    return notice("PostToolUse", context)


def skipped_notice(reason: str) -> str:
    """Return the non-blocking reply that tells the agent, and the user, the gate is off."""
    message = (
        f"The quality gate did not run, so this edit was not checked: {reason}. "
        "Install prek (`uv tool install prek`) to turn it back on."
    )
    return notice("PostToolUse", f"{message} Tell the user.", user_message=message)


def outcome_of(result: GateResult) -> Outcome:
    """Classify a gate result for the log."""
    if not result.ran:
        return "skipped"
    if deferred_only(result):
        return "deferred"
    if result.code != 0:
        return "block"
    return "fixed" if result.rerun else "pass"


def respond(result: GateResult) -> int:
    """Write what the agent should see for `result` and return the hook's exit code."""
    if not result.ran:
        sys.stdout.write(f"{skipped_notice(result.output)}\n")
        return 0
    if result.code == 0:
        return 0
    if deferred_only(result):
        sys.stdout.write(f"{deferred_notice(result.output)}\n")
        return 0
    sys.stderr.write(f"{condense(result.output)}\n")
    return BLOCK


def _build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="gate",
        description="Run the prek gate against the file a tool just edited.",
    )
    parser.add_argument(
        "--skip",
        default=SKIP_HOOKS,
        metavar="HOOKS",
        help=f"comma-separated hook ids to skip (default: {SKIP_HOOKS})",
    )
    return parser


def _relative(target: Path, root: Path) -> str:
    """Return `target` relative to `root` for the log, or as given if it is not under it."""
    try:
        return str(target.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(target)


def main(
    argv: list[str] | None = None,
    runner: Runner = run_concise,
    scanner: Scanner = find_conflicted,
) -> int:
    """Entry point. Returns an exit code; never calls sys.exit itself."""
    args = _build_parser().parse_args(argv)
    target = target_path(sys.stdin.read())
    session_root = find_repo_root()
    if target is None or session_root is None:
        return 0
    root = owning_repo(target, session_root)
    gate_root = find_gate_root(target, root) if root else None
    if gate_root is None:
        return 0
    logged_target = _relative(target, gate_root)
    conflicted = scanner(gate_root)
    if conflicted:
        record(gate_root, Entry(hook="gate", outcome="paused", target=logged_target))
        sys.stderr.write(f"{paused_message(conflicted)}\n")
        return BLOCK
    result = check([target], gate_root, args.skip, runner)
    failed = failed_hooks(result.output) if result.code != 0 else ()
    entry = Entry(hook="gate", outcome=outcome_of(result), target=logged_target, failed=failed)
    record(gate_root, entry)
    return respond(result)


if __name__ == "__main__":
    sys.exit(main())
