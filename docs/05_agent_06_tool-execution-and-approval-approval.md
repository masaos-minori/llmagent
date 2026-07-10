---
title: "Agent Tool Execution and Approval"
category: agent
tags:
  - agent
  - agent
  - tool
  - execution
  - approval
  - safety
related:
  - 05_agent_00_document-guide.md
---

# Agent Tool Execution and Approval

 runs before each tool execution:

### Pre-flight checks (instant deny)

1. **`allowed_tools` whitelist:** if list is non-empty and tool not in list → denied
2. **`allowed_root` root jail:** if path arg is outside `cfg.allowed_root` → denied
3. **GitHub repo allowlist:** if write op on repo not in `approval_github_allowed_repos` → denied (fail-closed)

#### `check_allowed_root(cfg, tool_name, args)`

Returns `False` when any path argument is outside `cfg.approval.allowed_root`. Returns `True` when:
- `allowed_root` is not set (no restriction)
- All path arguments resolve to paths within the allowed root

#### `check_allowed_repo(cfg, tool_name, args)`

Returns `False` when a GitHub write tool targets a repo not in the allowlist. Only applies to GitHub write tools. Returns:
- `True` for non-GitHub write tools
- `False` when `allowed_repos` is empty (fail-closed)
- Result of `"owner/repo" in allowed_repos` check

### Operation type classification

`classify_operation_type(tool_name)` returns one of: `READ`, `WRITE`, `DELETE`, `EXECUTE`, `API_WRITE`.

Classification priority (first match wins):
1. `WRITE_TOOLS` → `OperationType.WRITE`
2. `DELETE_TOOLS` → `OperationType.DELETE`
3. Exec tools (`shell_run`) → `OperationType.EXECUTE`
4. API write tools (github_* tools) → `OperationType.API_WRITE`
5. Default → `OperationType.READ`

### Risk classification

Priority: `approval_risk_rules` table → `tool_safety_tiers` mapping

#### Tier-to-risk mapping

| Tier | Risk level |
|---|---|
| `READ_ONLY` | `none` |
| `WRITE_SAFE` | `none` |
| `WRITE_DANGEROUS` | `medium` |
| `ADMIN` | `high` |

Tools absent from `tool_safety_tiers` default to `WRITE_DANGEROUS` (fail-safe).

| Risk level | Behavior |
|---|---|
| `none` | Auto-approved (no prompt) |
| `medium` | Preview + `y/N` prompt |
| `high` | Preview + full `yes` input required |

### Risk escalation conditions

- Path in `approval_protected_paths` → escalate to `high`
- GitHub branch in `approval_high_risk_branches` (default: main, master) → escalate to `high`
- `gitops_force_push_blocked=True` and `force=True` arg → deny
- `gitops_push_blocked=True` → deny all GitHub write ops

#### GitHub write tools

7 GitHub write tools used for `gitops_push_blocked` check:

| Tool | Purpose |
|---|---|
| `github_push_files` | Push multiple files |
| `github_create_or_update_file` | Create or update a single file |
| `github_delete_file` | Delete a file |
| `github_merge_pull_request` | Merge a PR |
| `github_create_pull_request` | Create a PR |
| `github_update_pull_request` | Update a PR |
| `github_create_branch` | Create a branch |

When `gitops_push_blocked=True`, any of these tools are denied without prompt.

### Dry-run preview

Tools in `approval_dry_run_tools` (default: write_file, edit_file, delete_file, delete_directory,
move_file) are pre-executed with `dry_run=True` before the approval prompt. Result appended to preview.

### Denial handling

Denied tools receive `"Tool execution denied by user."` as tool result (returned to LLM as a
tool role message, so conversation continues naturally).

---

## Plan Mode

`/plan` toggles `ctx.c

onv.plan_mode`.

- When `True`: tools in `cfg.tool.plan_blocked_tools` are auto-denied (without prompt)
- Default blocked: `write_file`, `create_directory`, `delete_file`, `delete_directory`
- Purpose: allow LLM to reason and plan without executing destructive operations

---

### `build_preview(tool_name, args)`

Builds a human-readable operation preview shown before approval prompts.

| Tool category | Preview format |
|---|---|
| `write_file`, `edit_file` | `{path}\n    content: {content[:200]}` |
| `delete_file`, `delete_directory`, `create_directory` | `{path or directory_path}` |
| `move_file` | `{source} → {destination}` |
| `shell_run` | `{command}` |
| `github_*` | `{owner}/{repo} {extra args JSON[:200]}` |
| Other tools | `json.dumps(args)[:300]` |

### `TURN_LIMIT_HINT`

Hint appended to history when a tool result is dropped due to the per-turn limit. Format:

```
[Result omitted: per-turn tool result limit reached.]
```

This hint is appended when `tool_results_turn_max_chars` (see [05_agent_08_configuration-loading-agent-config.md](05_agent_08_configuration-loading-agent-config.md)) is exceeded.

---

## Tool Result Cache

`ToolExecutor`

## Related Documents

- `agent`
- `tool`
- `execution`

## Keywords

agent
tool
execution
approval
safety
