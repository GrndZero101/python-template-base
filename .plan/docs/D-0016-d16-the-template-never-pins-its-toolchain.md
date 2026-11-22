---
id: D-0016
title: 'D16: The template never pins its toolchain'
kind: adr
status: approved
tasks:
- T-0019
- T-0021
created_at: '2026-11-22T21:44:57Z'
updated_at: '2026-11-22T21:46:03Z'
---

Decided 2026-10-17, replacing the 2026-10-16 pin-and-floor design.

uv, prek, copier and the gate's tools run at their latest, on users' machines and on CI alike.
There are no users to protect from an upgrade, and the pin's copies across two repos and two layers
caused the canary's failed update rather than preventing one. The cost is accepted: CI loses
reproducibility, and an upstream release will sometimes break a run, which is fixed forward. A
weekly CI run in each repo surfaces that. A downstream project that wants a frozen toolchain gets a
`seal` command later; the template never seals itself.

How (2026-10-18, settled by trying each option in a generated project):

- **Every hook but the builtins is local, `uv run --no-project --with <tool>`, no version.** uv
  trusts its cached copy of PyPI's simple page for its `max-age=600`, so a release reaches the gate
  within ten minutes. Warm, the gate took 0.21 s against 0.19 s pinned. Offline with a stale cache
  it fails after 4 s of retries, as a pinned `--with` already did. `uvx ruff` was rejected (reuses
  an installed tool, never floats), and `uvx ruff@latest` hits the network every run.
- **`prek autoupdate` rejected**: a later `copier update` merged cleanly only when the base had
  moved to the same tag, and it cannot move ty's `==`.
- **prek left both dev groups**; CI installs it with `uv tool install` and puts `uv tool dir --bin`
  on `$GITHUB_PATH`.
- **copier cannot leave the dev group**: pytest-copie depends on it, and under `uv run` the venv's
  copier shadows the uv tool's. CI syncs with `--upgrade` instead of `--locked`.
- **The setup helper's `update` upgrades the uv tools first** and stops if one will not upgrade.
- **Unchanged by decision:** a generated project's `uv.lock` and dev-group floors are its own
  dependencies, not the toolchain; the uv-script skill's `exclude-newer` stays (a script's
  substitute for a lock); GitHub Actions stay pinned by SHA, for supply-chain hygiene.
