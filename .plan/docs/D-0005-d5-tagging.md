---
id: D-0005
title: 'D5: Tagging'
kind: adr
status: draft
tasks:
- T-0016
created_at: '2026-11-22T21:44:45Z'
updated_at: '2026-11-22T21:46:03Z'
---

Open. Needed by phase 8.

**Once any tag exists, `copier update` moves to the latest PEP 440 tag rather than `HEAD`**,
unless given `--vcs-ref HEAD`. That is right for stable releases and wrong while iterating, because
fixes stop reaching the canary until they are tagged.

Recommendation: stay untagged until the canary settles, then cut `v0.1.0`, one tag series per
repo. The READMEs' example already pins a commit. Two things wait on it: per-release update notes,
and the setup helper's `curl … | sh` form, which needs a tag or commit in its URL, never `main`.
