---
title: "Settings with High Operational Impact"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Settings with High Operational Impact

| 設定 | 影響 |
|---|---|
| `allowed_dirs` = `[]` | ファイルアクセスが完全に拒否される |
| `allowed_repos` = `[]` + `fail_closed` | すべてのGitHub書き込みが拒否される |
| `command_allowlist` = `[]` | すべてのshellコマンドが拒否される |
| `repo_allowlist` = `[]` | すべてのcicd-mcpアクセスが拒否される |
| `allowed_repo_paths` = `[]` | すべてのgit-mcpアクセスが拒否される |
| `read_only = true`（git-mcp） | `allowed_repo_paths` が設定されていてもgitの書き込みがブロックされる |
| `tool_definitions_strict = true` | tool名の不一致でagentの起動が中断される |

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
