---
id: D-0020
title: 'D20: The setup helper'
kind: adr
status: approved
tasks:
- T-0018
created_at: '2026-11-22T21:45:01Z'
updated_at: '2026-11-22T21:46:03Z'
---

Decided 2026-10-16 and 10-17; built 2026-10-17. The uv pin it once enforced is gone (D16).

One command takes a machine from nothing to ready and keeps it current: `bootstrap.sh`, a POSIX `sh`
shim, then `bootstrap.py`, a uv script. Two files, because the first step must run before anything
is installed. It lives at this repo's root, not in the template: it runs before any project exists.

**The shim** only gets a `uv` it can trust: with consent (`--yes` when there is no TTY) it runs the
official installer (curl, else wget), with the installer's output on stderr; it runs
`uv self update` on every run, and a uv that cannot update itself (Homebrew, pip, a shadowing copy)
stops it; it puts uv's directory first on PATH, then `exec uv run --script bootstrap.py "$@"`. No
`pipefail`, `[[ ]]`, `local` or arrays: `/bin/sh` is dash on Ubuntu and bash in POSIX mode on
macOS. shellcheck runs with `--shell=sh`. `--yes` and `-v` go before the command.

**The helper** is stdlib `argparse` with no dependencies, held to the template's own rules, and
drives copier as a uv tool rather than a library. Every probe of the machine is a `Probe` field, so
its tests run on a fake machine. Subcommands: `doctor` (reports, changes nothing), `setup` (installs
or upgrades copier and prek, writes copier's settings from git config, offering the GitHub noreply
address), `new <dir>` (`copier copy --trust`, stdout only the new path) and `update <project>` (the
README's two-layer flow on `chore/template-update`, base first per D21, stopping at a conflict with
the steps to resume; `--finish` runs `finish_branch.py`). Run from a clone only until a tag exists
(D5).
