---
id: D-0018
title: 'D18: The three repos'' work is tracked in taskplan'
kind: adr
status: approved
tasks:
- T-0001
created_at: '2026-11-22T21:44:59Z'
updated_at: '2026-11-22T21:46:03Z'
---

Decided by the author on 2026-11-23; the first ADR written in `tp`.

`TODO.md` had grown to 1,250 lines with about six open checkboxes, and a fresh session read all of
it to find one step. Work for all three repos — this one, python-template-cli-typer and the
canary — now lives in **one `tp` store, in this repo's root** (`.plan/`). Tasks are tagged `base`,
`cli` or `canary`; a session started in another repo reaches the store with `TP_ROOT` or `--root`.

The old file was split by kind, by judgment rather than `tp import markdown` (the hand-off was
prose, and the importer reads only headings and checkboxes):

- Open work became tasks under milestones; items waiting on the web app or on a second occurrence
  became `blocked` with that reason.
- The decision log became these ADRs, numbered so that D-0012 is the D12 the tests and `copier.yml`
  cite. D18 on are new.
- The standing rules ("How work is judged", "Sessions and checkpoints", "How work runs") moved to
  the root `CLAUDE.md`, since they are instructions.
- Gotchas still worth knowing went to the note "Gotchas and working state"; the spec-run record to
  the note "Spec runs". Finished history went: `git log` and the merge commits hold it.
- `TODO.md` is now tp's generated board (`board_file`), excluded from the root's markdown lint.
  The CLI repo's `TODO.md`, an empty field-findings inbox, is a pointer here.

Hooks: `tp hook session-start` is registered at the root only, exec form. tp's Stop hook is not
(`max_stop_blocks = 0`): the root has its own Stop gate.

**The verify shell.** tp runs a verify command as `<verify_shell> -c <command>`, and the config
says `bash`, which is right on Linux, macOS, WSL and from Claude Code's Bash tool on Windows (Git
Bash). From PowerShell, `bash` on PATH is WSL's `System32\bash.exe`, so a verify run there ran in
Linux and failed. Proven on 2026-11-23 with a probe task checking `uname -s`: PowerShell without the
variable got `Linux`; with the Windows user variable `TP_VERIFY_SHELL` set to
`C:\Program Files\Git\bin\bash.exe` it got `MINGW64_NT`, as the Bash tool does. The path stays out
of the committed config, which must work on WSL too.

Not in scope: shipping `tp` in the template to generated projects. That is decided only once it has
proved itself here. Findings about `tp` itself go to its own repo.
