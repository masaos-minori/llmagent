---
title: "Settings with High Operational Impact"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration_and_operations.md
source:
  - 04_mcp_06_configuration_and_operations.md
---

# Settings with High Operational Impact

## Settings with High Operational Impact

| Setting | Impact |
|---|---|
| `allowed_dirs` = `[]` | File access completely denied |
| `allowed_repos` = `[]` + `fail_closed` | All GitHub writes denied |
| `command_allowlist` = `[]` | All shell commands denied |
| `repo_allowlist` = `[]` | All cicd-mcp access denied |
| `allowed_repo_paths` = `[]` | All git-mcp access denied |
| `read_only = true` (git-mcp) | git writes blocked even if `allowed_repo_paths` is set |
| `tool_definitions_strict = true` | Agent startup aborts on tool name mismatch |
| `mcp_watchdog_interval = 0` | No auto-restart of failed subprocess servers (LOCAL profile default; PRODUCTION default is 30.0) |

---


## Related Documents

- [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

configuration
