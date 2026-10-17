# /// script
# requires-python = ">=3.14"
# dependencies = []
#
# [tool.uv]
# exclude-newer = "2026-10-17T00:00:00Z"
# ///
"""Get a machine ready for this template.

Run it through the shim, never directly:

    sh bootstrap.sh doctor          # report what is installed and configured; change nothing
    sh bootstrap.sh setup           # install or upgrade the uv tools, write copier's settings
    sh bootstrap.sh new my-project  # generate a project from the CLI template, once doctor passes
    sh bootstrap.sh update my-project  # update both layers, committed on chore/template-update

bootstrap.sh has already made sure of a standalone uv and updated it to the latest, so nothing here
checks that again. Stdlib only, so there is nothing to download on a bare machine.
"""

import argparse
import difflib
import json
import logging
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)
FAILED = 1
HERE = Path(__file__).resolve().parent

# The uv tools a project's workflow runs: copier to generate and update, prek for the gate.
UV_TOOLS = ("copier", "prek")

# What `new` copies: the CLI use case, which applies the base to the same directory itself.
CLI_TEMPLATE = "gh:GrndZero101/python-template-cli-typer"

SETTINGS_HEADER = (
    "# Written by `sh bootstrap.sh setup`, from git's identity. copier uses these as the default\n"
    "# answer to every template question of the same name, in place of the template's own.\n"
)


class Runner(Protocol):
    """Runs a command and captures its output. `env`, when given, is the whole environment."""

    def __call__(
        self, command: list[str], env: Mapping[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run `command`."""
        ...


def _run(
    command: list[str], env: Mapping[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run `command` and capture its output. Never a shell string."""
    logger.debug("running %s", command)
    return subprocess.run(command, capture_output=True, text=True, check=False, env=env)  # noqa: S603


class Attacher(Protocol):
    """Runs a command at the terminal and returns its exit code. `env` is as for a Runner."""

    def __call__(self, command: list[str], env: Mapping[str, str] | None = None) -> int:
        """Run `command`."""
        ...


def _attach(command: list[str], env: Mapping[str, str] | None = None) -> int:
    """Run `command` at the terminal, for the questions it asks, and return its exit code.

    Its stdout goes to stderr, which is still the terminal, so the helper's own stdout stays data.
    """
    logger.debug("running %s", command)
    return subprocess.run(command, stdout=sys.stderr, check=False, env=env).returncode  # noqa: S603


def _confirm(question: str) -> bool:
    """Ask `question` on stderr, which leaves stdout to the report, and read a yes or no."""
    sys.stderr.write(f"bootstrap: {question}? [y/N] ")
    sys.stderr.flush()
    return sys.stdin.readline().strip().lower() in {"y", "yes"}


@dataclass(frozen=True)
class Probe:
    """Everything the helper reads from the machine, or asks its user, so a test can fake it."""

    run: Runner = _run
    attach: Attacher = _attach
    which: Callable[[str], str | None] = shutil.which
    env: Mapping[str, str] = field(default_factory=os.environ.copy)
    home: Path = field(default_factory=Path.home)
    system: str = field(default_factory=platform.system)
    confirm: Callable[[str], bool] = _confirm
    interactive: bool = field(default_factory=sys.stdin.isatty)


@dataclass(frozen=True)
class Check:
    """One line of the report. A check that is not `required` is advice, and cannot fail it."""

    name: str
    ok: bool
    detail: str
    required: bool = True


def parse_tool_list(text: str) -> dict[str, str]:
    """Return {name: version} from `uv tool list`, whose tools are lines like `copier v9.18.2`."""
    tools: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.startswith(("-", " ")):
            continue  # an executable the tool above installed, or a blank line
        name, _, rest = line.partition(" ")
        version = rest.split(maxsplit=1)[0] if rest else ""
        tools[name] = version.removeprefix("v")
    return tools


def copier_settings_path(env: Mapping[str, str], home: Path, system: str) -> Path:
    """Return where copier reads its settings: COPIER_SETTINGS_PATH, else the platform's default."""
    override = env.get("COPIER_SETTINGS_PATH")
    if override:
        return Path(override)
    if system == "Darwin":
        root = home / "Library" / "Application Support"
    elif system == "Windows":
        root = Path(env.get("LOCALAPPDATA") or home / "AppData" / "Local")
    else:
        root = Path(env.get("XDG_CONFIG_HOME") or home / ".config")
    return root / "copier" / "settings.yml"


def check_uv(probe: Probe) -> Check:
    """Report the running uv's version. The shim has already updated it to the latest."""
    completed = probe.run(["uv", "self", "version", "--short"])
    if completed.returncode != 0:
        return Check("uv", ok=False, detail=f"`uv self version` failed: {completed.stderr.strip()}")
    return Check("uv", ok=True, detail=completed.stdout.strip())


def check_uv_tools(probe: Probe) -> list[Check]:
    """Report copier and prek, which must be uv tools rather than anything else on PATH."""
    completed = probe.run(["uv", "tool", "list"])
    if completed.returncode != 0:
        detail = f"`uv tool list` failed: {completed.stderr.strip()}"
        return [Check(name, ok=False, detail=detail) for name in UV_TOOLS]
    installed = parse_tool_list(completed.stdout)
    checks: list[Check] = []
    for name in UV_TOOLS:
        version = installed.get(name)
        if version is None:
            checks.append(Check(name, ok=False, detail=f"not a uv tool: uv tool install {name}"))
        else:
            checks.append(Check(name, ok=True, detail=version))
    return checks


def check_git_identity(probe: Probe) -> list[Check]:
    """Report git's user.name and user.email, which every generated project commits as."""
    if probe.which("git") is None:
        return [Check("git", ok=False, detail="git is not installed")]
    checks: list[Check] = []
    for key in ("user.name", "user.email"):
        completed = probe.run(["git", "config", "--get", key])
        value = completed.stdout.strip()
        if completed.returncode != 0 or not value:
            fix = f'not set: git config --global {key} "..."'
            checks.append(Check(f"git {key}", ok=False, detail=fix))
        else:
            checks.append(Check(f"git {key}", ok=True, detail=value))
    return checks


def check_copier_settings(probe: Probe) -> Check:
    """Report copier's settings file, whose defaults answer the author questions. Advice only."""
    path = copier_settings_path(probe.env, probe.home, probe.system)
    if path.is_file():
        return Check("copier settings", ok=True, detail=str(path), required=False)
    detail = f"none at {path}, so copier asks for your name and email every time"
    return Check("copier settings", ok=False, detail=detail, required=False)


def check_gh(probe: Probe) -> Check:
    """Report the GitHub CLI and its login. Advice only: nothing needs it, it offers a noreply email."""
    if probe.which("gh") is None:
        return Check("gh", ok=False, detail="not installed (optional)", required=False)
    completed = probe.run(["gh", "auth", "status"])
    if completed.returncode != 0:
        return Check("gh", ok=False, detail="not logged in: gh auth login", required=False)
    return Check("gh", ok=True, detail="logged in", required=False)


def doctor(probe: Probe) -> list[Check]:
    """Run every check, changing nothing, in the order the report shows them."""
    if probe.which("uv") is None:
        checks = [Check("uv", ok=False, detail="not on PATH: run this as sh bootstrap.sh doctor")]
    else:
        checks = [check_uv(probe), *check_uv_tools(probe)]
    checks.extend(check_git_identity(probe))
    checks.append(check_copier_settings(probe))
    checks.append(check_gh(probe))
    return checks


def upgrade_uv_tools(probe: Probe) -> bool:
    """Install each of UV_TOOLS that is missing and upgrade the rest. Return whether all worked."""
    listed = probe.run(["uv", "tool", "list"])
    installed = parse_tool_list(listed.stdout) if listed.returncode == 0 else {}
    all_ok = True
    for name in UV_TOOLS:
        verb = "upgrade" if name in installed else "install"
        logger.info("uv tool %s %s", verb, name)
        completed = probe.run(["uv", "tool", verb, name])
        if completed.returncode != 0:
            logger.error("uv tool %s %s failed: %s", verb, name, completed.stderr.strip())
            all_ok = False
    return all_ok


def git_config(probe: Probe, key: str) -> str:
    """Return git's value for `key`, or "" when git is missing or the key is unset."""
    if probe.which("git") is None:
        return ""
    completed = probe.run(["git", "config", "--get", key])
    return completed.stdout.strip() if completed.returncode == 0 else ""


def noreply_email(probe: Probe) -> str | None:
    """Return the GitHub noreply address of gh's logged-in user, or None without one.

    Built from the account's id and login, which gh's default token can read: the account's own
    email it cannot, when that is private.
    """
    if probe.which("gh") is None:
        return None
    completed = probe.run(["gh", "api", "user"])
    if completed.returncode != 0:
        return None
    user = json.loads(completed.stdout)
    return f"{user['id']}+{user['login']}@users.noreply.github.com"


def choose_email(probe: Probe, git_email: str, *, noreply: bool) -> str:
    """Return git's email, or the GitHub noreply address when asked for it or agreed to."""
    private = noreply_email(probe)
    if private is None or private == git_email:
        return git_email
    if noreply:
        return private
    if probe.interactive and probe.confirm(
        f"Use your GitHub noreply address {private} instead of {git_email or 'no email'}"
    ):
        return private
    logger.info("using %s; setup --noreply would use %s", git_email or "no email", private)
    return git_email


def settings_text(name: str, email: str) -> str:
    """Return copier's settings file answering the author questions.

    YAML, written without a YAML library: a JSON string is a valid YAML double-quoted scalar.
    """
    return (
        f"{SETTINGS_HEADER}defaults:\n"
        f"  author_name: {json.dumps(name)}\n"
        f"  author_email: {json.dumps(email)}\n"
    )


def write_settings(probe: Probe, path: Path, text: str, *, assume_yes: bool) -> bool:
    """Write `text` to `path`, showing the diff and asking before replacing anything there.

    Return False only when consent was needed and there was no way to ask; a "no" is an answer.
    """
    old = path.read_text(encoding="utf-8") if path.is_file() else None
    if old == text:
        logger.info("copier settings unchanged: %s", path)
        return True
    if old is not None:
        diff = difflib.unified_diff(
            old.splitlines(keepends=True), text.splitlines(keepends=True), str(path), "new"
        )
        sys.stderr.writelines(diff)
        if not assume_yes and not probe.interactive:
            logger.error("replacing %s needs consent; rerun as: sh bootstrap.sh --yes setup", path)
            return False
        if not assume_yes and not probe.confirm(f"Replace {path} as above"):
            logger.info("left %s as it was", path)
            return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    logger.info("wrote copier settings: %s", path)
    return True


def setup(probe: Probe, *, assume_yes: bool, noreply: bool) -> bool:
    """Install or upgrade the uv tools and write copier's settings. Return whether all worked."""
    tools_ok = upgrade_uv_tools(probe)
    name = git_config(probe, "user.name")
    if not name:
        logger.error('no copier settings without a name: git config --global user.name "..."')
        return False
    email = choose_email(probe, git_config(probe, "user.email"), noreply=noreply)
    path = copier_settings_path(probe.env, probe.home, probe.system)
    settings_ok = write_settings(probe, path, settings_text(name, email), assume_yes=assume_yes)
    return tools_ok and settings_ok


def _occupied(path: Path) -> bool:
    """Return whether `path` is a file, or a directory with anything in it."""
    return path.exists() and (not path.is_dir() or any(path.iterdir()))


def _ready_for_copier(probe: Probe) -> bool:
    """Return whether doctor passes and copier is on PATH, saying what to do when not.

    The report goes to stderr: the commands that check this keep stdout for their own data.
    """
    checks = doctor(probe)
    failed = failed_checks(checks)
    if failed:
        sys.stderr.write(render(checks))
        logger.error("not ready (%s): run sh bootstrap.sh setup first", ", ".join(failed))
        return False
    if probe.which("copier") is None:
        logger.error("copier is not on PATH: run uv tool update-shell, then open a new shell")
        return False
    return True


def new(probe: Probe, destination: Path, *, template: str, copier_args: list[str]) -> bool:
    """Generate a project at `destination` with copier, once doctor passes. Return whether it did."""
    if not _ready_for_copier(probe):
        return False
    if _occupied(destination):
        logger.error("%s is already there and not an empty directory; name a new one", destination)
        return False
    command = ["copier", "copy", "--trust", *copier_args, template, str(destination)]
    returncode = probe.attach(command)
    if returncode != 0:
        logger.error("copier copy exited %d; its error is above", returncode)
        return False
    return True


def _git(
    probe: Probe, root: Path, *args: str, env: Mapping[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run git in `root`."""
    return probe.run(["git", "-C", str(root), *args], env)


def _clean_checkout(probe: Probe, root: Path) -> bool:
    """Return whether `root` is a git checkout with nothing uncommitted, saying why not."""
    completed = _git(probe, root, "status", "--porcelain")
    if completed.returncode != 0:
        logger.error("%s is not a git checkout: %s", root, completed.stderr.strip())
        return False
    if completed.stdout.strip():
        logger.error("%s has uncommitted changes; commit or stash them first", root)
        return False
    return True


# What `update` brings up to date, in this order: the base, then the use case over it. A project
# generated from the base alone has only the first. Base first because the use case is written
# against the base: a use-case change that needs a base change then never lands ahead of it. The
# other order once raised the use case's uv floor before the base's hook could meet it.
ANSWERS_FILES = (".copier-answers.base.yml", ".copier-answers.yml")
UPDATE_BRANCH = "chore/template-update"
UPDATE_SUMMARY = "chore(template): update from the templates"
# The two keys read from an answers file are plain scalars, so there is no YAML library to need.
_ANSWER = re.compile(r"^(?P<key>_commit|_src_path): (?P<value>.+?)\r?$", re.MULTILINE)

UPDATE_RESUME = """
To carry on, in {project}:
  1. {first}
  2. uv sync && git add -A && git commit -m "{message}"
  3. {rerun}
"""

UPDATE_NEXT_STEPS = """
Committed on {branch} in {project}. Review it: git diff main. A new key in an answers file is a
question copier answered for you. Then finish it, which squashes, gates, tests and merges:
  cd {project} && uv run python tools/finish_branch.py "{summary}"
or rerun with --finish to have this run it.
"""


@dataclass(frozen=True)
class Layer:
    """One template a project was generated from, as its answers file records it."""

    answers: str
    source: str
    commit: str

    @property
    def name(self) -> str:
        """Return the template's repository name, the last part of its source."""
        if not self.source:
            return self.answers
        return re.split(r"[/\\]", self.source.rstrip("/\\"))[-1].removesuffix(".git")


@dataclass(frozen=True)
class UpdateRun:
    """What one `update` was asked to do, which a run resumed after a stop repeats."""

    project: Path
    copier_args: tuple[str, ...] = ()
    finish: bool = False

    def rerun(self) -> str:
        """Return the command that carries on where this run stopped."""
        command = ["sh", str(HERE / "bootstrap.sh"), "update", str(self.project)]
        if self.finish:
            command.append("--finish")
        if self.copier_args:
            command.extend(["--", *self.copier_args])
        return shlex.join(command)


def read_layer(project: Path, answers: str) -> Layer | None:
    """Return the layer that `answers` records in `project`, or None when there is no such file."""
    path = project / answers
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    found = {match["key"]: match["value"].strip("'\"") for match in _ANSWER.finditer(text)}
    return Layer(answers, found.get("_src_path", ""), found.get("_commit", ""))


def _branch(probe: Probe, root: Path) -> str:
    """Return the branch checked out in `root`, or "" when there is none."""
    completed = _git(probe, root, "branch", "--show-current")
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _on_update_branch(probe: Probe, project: Path) -> bool:
    """Move onto UPDATE_BRANCH from main, taking the working tree along, unless it is there already.

    Left until there is something to commit, so an update that changes nothing leaves no branch.
    """
    if _branch(probe, project) == UPDATE_BRANCH:
        return True
    switched = _git(probe, project, "switch", "--create", UPDATE_BRANCH)
    if switched.returncode != 0:
        logger.error("%s: git switch failed: %s", project, switched.stderr.strip())
        return False
    logger.info("%s: on a new branch, %s", project, UPDATE_BRANCH)
    return True


def _layers_to_update(probe: Probe, project: Path) -> list[Layer] | None:
    """Return the project's layers in update order, or None when it cannot be updated now."""
    if not _ready_for_copier(probe) or not _clean_checkout(probe, project):
        return None
    branch = _branch(probe, project)
    if branch not in {"main", UPDATE_BRANCH}:
        logger.error(
            "%s is on %s: switch to main first; update makes its own branch", project, branch
        )
        return None
    layers: list[Layer] = []
    for answers in ANSWERS_FILES:
        layer = read_layer(project, answers)
        if layer is not None:
            layers.append(layer)
    if not layers:
        names = " or ".join(ANSWERS_FILES)
        logger.error("%s has no %s: it was not generated from these templates", project, names)
        return None
    return layers


def _project_env(probe: Probe) -> dict[str, str]:
    """Return the environment for a command that runs uv in the project, the commit's hooks too.

    `uv run --script` points VIRTUAL_ENV at the helper's own environment, and every uv run in the
    project would warn that it ignores it.
    """
    return {name: value for name, value in probe.env.items() if name != "VIRTUAL_ENV"}


def _stop(run: UpdateRun, layer: Layer, first: str) -> None:
    """Log how to carry on after this layer stopped part way, its changes left in place."""
    moved = read_layer(run.project, layer.answers) or layer
    message = f"chore(template): update {layer.name} to {moved.commit}"
    resume = UPDATE_RESUME.format(
        project=run.project, first=first, message=message, rerun=run.rerun()
    )
    sys.stderr.write(resume)


def _commit_layer(probe: Probe, run: UpdateRun, layer: Layer) -> Check:
    """Commit what updating `layer` changed, on UPDATE_BRANCH."""
    moved = read_layer(run.project, layer.answers) or layer
    if not _on_update_branch(probe, run.project):
        return Check(layer.name, ok=False, detail=f"could not switch to {UPDATE_BRANCH}")
    # Added, then committed: never `commit --all`, which hands the hooks a temporary index.
    staged = _git(probe, run.project, "add", "--all")
    if staged.returncode != 0:
        return Check(layer.name, ok=False, detail=f"git add failed: {staged.stderr.strip()}")
    message = f"chore(template): update {layer.name} to {moved.commit}"
    committed = _git(probe, run.project, "commit", "-m", message, env=_project_env(probe))
    if committed.returncode != 0:
        logger.error("the commit failed: %s", (committed.stdout + committed.stderr).strip())
        _stop(run, layer, "fix what the commit's hooks reported above")
        return Check(layer.name, ok=False, detail="the commit failed; its hooks' output is above")
    return Check(layer.name, ok=True, detail=f"{layer.commit} -> {moved.commit}")


def update_layer(probe: Probe, run: UpdateRun, layer: Layer) -> Check:
    """Bring one layer up to date and commit it. A failed check means stop here."""
    logger.info("%s: copier update from %s", layer.name, layer.commit)
    command = ["copier", "update", "--trust", "-a", layer.answers, *run.copier_args]
    returncode = probe.attach([*command, str(run.project)])
    if returncode != 0:
        detail = f"copier update exited {returncode}; its error is above, git status what it left"
        return Check(layer.name, ok=False, detail=detail)
    # copier exits 0 on a conflict: it writes the markers and records each file as unmerged.
    conflicts = _git(probe, run.project, "diff", "--name-only", "--diff-filter=U")
    if conflicts.stdout.strip():
        _on_update_branch(probe, run.project)  # so the commit that resolves them lands off main
        _stop(run, layer, 'resolve each conflict, then git add it (README: "Conflicts")')
        detail = f"conflicts in {', '.join(conflicts.stdout.splitlines())}"
        return Check(layer.name, ok=False, detail=detail)
    # Before anything checks the update: a dependency the template dropped is still in .venv.
    synced = probe.run(["uv", "sync", "--directory", str(run.project)], _project_env(probe))
    if synced.returncode != 0:
        _stop(run, layer, "fix what uv sync reported")
        return Check(layer.name, ok=False, detail=f"uv sync failed: {synced.stderr.strip()}")
    if not _git(probe, run.project, "status", "--porcelain").stdout.strip():
        return Check(layer.name, ok=True, detail=f"already at {layer.commit}")
    return _commit_layer(probe, run, layer)


def update(probe: Probe, run: UpdateRun, layers: list[Layer]) -> list[Check]:
    """Update each layer in turn, stopping at the first that does not finish cleanly."""
    checks: list[Check] = []
    for layer in layers:
        check = update_layer(probe, run, layer)
        checks.append(check)
        if not check.ok:
            break
    return checks


def finish_update(probe: Probe, project: Path) -> bool:
    """Run the project's finish_branch.py on UPDATE_BRANCH, which merges it into main."""
    command = ["uv", "run", "--directory", str(project), "python", "tools/finish_branch.py"]
    returncode = probe.attach([*command, UPDATE_SUMMARY], _project_env(probe))
    if returncode != 0:
        logger.error("finish_branch.py exited %d; its output above says what to do", returncode)
        return False
    return True


def _update(probe: Probe, args: argparse.Namespace) -> int:
    """Run `update`: each layer, a report of them on stdout, then the finish or how to do it."""
    run = UpdateRun(Path(args.project).resolve(), tuple(args.copier_args), finish=args.finish)
    # The latest copier does the update and the latest prek gates its commits, as on CI.
    if not upgrade_uv_tools(probe):
        return FAILED
    layers = _layers_to_update(probe, run.project)
    if layers is None:
        return FAILED
    checks = update(probe, run, layers)
    sys.stdout.write(render(checks))
    if failed_checks(checks):
        return FAILED
    if _branch(probe, run.project) != UPDATE_BRANCH:
        logger.info("every layer is up to date; nothing to commit")
        return 0
    if run.finish:
        return 0 if finish_update(probe, run.project) else FAILED
    next_steps = UPDATE_NEXT_STEPS.format(
        branch=UPDATE_BRANCH, project=run.project, summary=UPDATE_SUMMARY
    )
    sys.stderr.write(next_steps)
    return 0


def failed_checks(checks: list[Check]) -> list[str]:
    """Return the names of the required checks that failed."""
    return [check.name for check in checks if check.required and not check.ok]


def render(checks: list[Check]) -> str:
    """Return the report: one aligned line per check, `ok`, `FAIL`, or `warn` for advice."""
    width = max(len(check.name) for check in checks)
    lines: list[str] = []
    for check in checks:
        if check.ok:
            status = "ok"
        elif check.required:
            status = "FAIL"
        else:
            status = "warn"
        lines.append(f"{status:<5}{check.name:<{width}}  {check.detail}")
    return "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="bootstrap.sh", description="Get a machine ready for this template."
    )
    # The shim reads --yes too, so it goes first, before the command, for both to see it.
    parser.add_argument("--yes", action="store_true", help="agree to every change without asking")
    parser.add_argument("-v", "--verbose", action="store_true", help="log at DEBUG level")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="report what is installed and configured; change nothing")
    setup_parser = commands.add_parser(
        "setup", help="install or upgrade copier and prek, and write copier's settings"
    )
    setup_parser.add_argument(
        "--noreply",
        action="store_true",
        help="answer author_email with your GitHub noreply address",
    )
    new_parser = commands.add_parser(
        "new", help="generate a project from the CLI template, once doctor passes"
    )
    new_parser.add_argument("destination", help="the project's directory: new, or empty")
    new_parser.add_argument(
        "--template", default=CLI_TEMPLATE, help="the template to copy (default: %(default)s)"
    )
    new_parser.add_argument(
        "copier_args",
        nargs="*",
        metavar="-- COPIER_ARG",
        help="after --, passed to copier copy as is: -- --vcs-ref <commit>",
    )
    update_parser = commands.add_parser(
        "update",
        help="upgrade copier and prek, then update a project from both its templates on a branch",
    )
    update_parser.add_argument("project", help="the project's directory")
    update_parser.add_argument(
        "--finish", action="store_true", help="then merge the branch with tools/finish_branch.py"
    )
    update_parser.add_argument(
        "copier_args",
        nargs="*",
        metavar="-- COPIER_ARG",
        help="after --, passed to each copier update as is: -- --defaults",
    )
    return parser


def main(argv: list[str] | None = None, probe: Probe | None = None) -> int:
    """Entry point. Returns an exit code; never calls sys.exit itself."""
    args = _build_parser().parse_args(argv)
    level = logging.DEBUG if args.verbose else logging.INFO
    # force: basicConfig is a no-op once a handler exists, and a test calls main more than once.
    logging.basicConfig(
        level=level, stream=sys.stderr, format="%(levelname)s %(message)s", force=True
    )
    probe = probe or Probe()
    if args.command == "update":
        return _update(probe, args)
    if args.command == "new":
        # Resolved now, so stdout names it absolutely: cd "$(sh bootstrap.sh new my-project)".
        destination = Path(args.destination).resolve()
        if not new(probe, destination, template=args.template, copier_args=args.copier_args):
            return FAILED
        sys.stdout.write(f"{destination}\n")
        return 0
    done = True
    if args.command == "setup":
        done = setup(probe, assume_yes=args.yes, noreply=args.noreply)
    # setup ends with doctor's report too, so a run shows what it left.
    checks = doctor(probe)
    sys.stdout.write(render(checks))
    failed = failed_checks(checks)
    if failed:
        logger.error("not ready: %s", ", ".join(failed))
    if failed or not done:
        return FAILED
    return 0


if __name__ == "__main__":
    sys.exit(main())
