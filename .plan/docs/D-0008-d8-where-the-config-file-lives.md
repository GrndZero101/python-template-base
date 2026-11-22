---
id: D-0008
title: 'D8: Where the config file lives'
kind: adr
status: approved
tasks: []
created_at: '2026-11-22T21:44:47Z'
updated_at: '2026-11-22T21:44:48Z'
---

Decided 2026-10-04.

The config file lives in `~/.config/<script>/` on macOS as on Linux, `XDG_CONFIG_HOME` is honoured
on every platform, and `%APPDATA%` is used on Windows.
