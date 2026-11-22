---
id: D-0009
title: 'D9: Secrets in a data command''s output'
kind: adr
status: approved
tasks: []
created_at: '2026-11-22T21:44:48Z'
updated_at: '2026-11-22T21:44:49Z'
---

Decided 2026-10-04.

A data command's JSON emits secrets raw, as `terraform output -json` and `gh auth token` do, via an
explicit `.get_secret_value()`. Incidental exposure — `repr`, logs, whole-model dumps such as
`about` — is masked by `SecretStr`, as `gh auth status` and `kubectl config view` mask. Checked:
pydantic-settings masks `repr` and `model_dump(mode="json")`.
