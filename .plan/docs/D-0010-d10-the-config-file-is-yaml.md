---
id: D-0010
title: 'D10: The config file is YAML'
kind: adr
status: approved
tasks: []
created_at: '2026-11-22T21:44:50Z'
updated_at: '2026-11-22T21:44:50Z'
---

Decided 2026-10-04, for flexibility as configs grow. It is parsed with `yaml.safe_load`, not
pydantic-settings' `YamlConfigSettingsSource`, which has no runtime path and lets a list-shaped file
escape as a bare `ValueError`.
