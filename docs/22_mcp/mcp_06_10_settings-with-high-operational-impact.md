---
title: "Settings with High Operational Impact"
area: mcp
tags:
  - mcp
  - configuration
  - operations
related:
---
# Settings with High Operational Impact

| Setting | Impact |
|---|---|
| `allowed_dirs` = `[]` | File access is completely denied |
| `allowed_repos` = `[]` (fail-closed policy) | All GitHub writes are denied |
| `command_allowlist` = `[]` | All shell commands are denied |
| `repo_allowlist` = `[]` | All cicd-mcp access is denied |
| `allowed_repo_paths` = `[]` | All git-mcp access is denied |
| `read_only = true` (git-mcp) | Git writes are blocked even if `allowed_repo_paths` is set |
| `tool_definitions_strict = true` | Agent startup is interrupted due to tool name mismatch |

---



## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
