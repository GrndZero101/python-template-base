---
id: D-0004
title: 'D4: cli-stdlib is its own repo'
kind: adr
status: approved
tasks:
- T-0014
created_at: '2026-11-22T21:44:44Z'
updated_at: '2026-11-22T21:46:03Z'
---

Decided 2026-10-05, replacing 2026-10-04.

A stdlib-only CLI is its own use-case repo, `python-template-cli-stdlib` (D13's name), not a
project type here. A scaffold was built for it on 2026-10-05 and parked on the local branch
`archive/cli-stdlib` (`4098f9e`) to seed that repo. On 2026-11-23 that branch was in neither the
Windows nor the WSL clone, nor on GitHub; the seeding task says so.
