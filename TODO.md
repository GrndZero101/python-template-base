# Plan board — python-template-base

> 30 tasks · 1 done · 0 doing · 7 blocked

## M-0001 Faster suites for local loops (0/3)

- [ ] T-0002 Check the CLI suite is safe to run under pytest-xdist
- [ ] T-0003 Run the CLI repo's suite on pytest-xdist, timed against the 9 minutes — waiting on T-0002
- [ ] T-0004 Find out why Windows CI takes ten times Linux's time

## M-0002 Windows native: the first real project's untried paths (0/2)

- [ ] T-0005 Walk the setup's untried parts on Windows native
- [ ] T-0006 DebugMCP on Windows native

## M-0003 Brownfield adoption: what issue #1's web app shows (0/3)

- [ ] T-0007 Support a second test suite in the gate and finish_branch.py — blocked: Waiting for issue #1's web app to show it in use; unblock when it does.
- [ ] T-0008 PLR0913 against FastAPI handlers with several dependencies — blocked: Waiting for issue #1's web app to show it in use; unblock when it does.
- [ ] T-0009 Gate only changed files in a brownfield repo — blocked: Waiting for a brownfield repo's legacy code to fail the gate on main (D15: no machinery before then).

## M-0004 Spec runs and skill wording (0/3)

- [ ] T-0010 Rerun the spec runs to measure the fixes since the currency run
- [ ] T-0011 Skill lines from the spend run, on a second occurrence — blocked: Waiting for a second occurrence in a spec run; act on each item only then.
- [ ] T-0012 Declare each setting once — blocked: Waiting for a spec run that shows a model fumbling 'Recipe: add a setting'.

## M-0005 More layers: the base's canary and cli-stdlib (ask first) (0/3)

- [ ] T-0013 Create python-canary-base to exercise the uv-script skill
- [ ] T-0014 Seed python-template-cli-stdlib
- [ ] T-0015 Review whether the base's _external_data defaults earn their place

## M-0006 Releases and updates (phase 8's rest; ask first) (0/4)

- [ ] T-0016 Cut v0.1.0 in both template repos — blocked: D5 is open: stay untagged until the canary settles; the author decides when.
- [ ] T-0017 Per-release update notes — waiting on T-0016
- [ ] T-0018 Run the setup helper piped from the web, at a tag — waiting on T-0016
- [ ] T-0019 Automate the dependency floors' updates

## M-0007 Later (0/4)

- [ ] T-0020 gitlab as a ci choice
- [ ] T-0021 A seal command for downstream projects
- [ ] T-0022 Verify the Textual console by hand
- [ ] T-0023 The DebugMCP VS Code extension — blocked: Deferred by the author's choice.

## Other tasks

- [x] T-0001 Move the three repos' work from TODO.md into tp — done 2026-11-22

## Blockers

- T-0007: Waiting for issue #1's web app to show it in use; unblock when it does.
- T-0008: Waiting for issue #1's web app to show it in use; unblock when it does.
- T-0009: Waiting for a brownfield repo's legacy code to fail the gate on main (D15: no machinery before then).
- T-0011: Waiting for a second occurrence in a spec run; act on each item only then.
- T-0012: Waiting for a spec run that shows a model fumbling 'Recipe: add a setting'.
- T-0016: D5 is open: stay untagged until the canary settles; the author decides when.
- T-0023: Deferred by the author's choice.
