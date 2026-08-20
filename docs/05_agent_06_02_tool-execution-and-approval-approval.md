---
title: "Agent Tool Execution and Approval - Approval Flow"
category: agent
tags:
  - agent
  - tool-execution
  - approval-flow
related:
  - 05_agent_00_document-guide.md
  - 05_agent_06_04_tool-execution-and-approval-canonical.md
source:
  - 05_agent_06_02_tool-execution-and-approval-approval.md
---

# Agent Tool Execution and Approval

- Turn Flow → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCP Routing → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)

## Purpose

Documents design decisions for approval flows, risk classification, and plan mode.

**Note**: This document only covers **pre-execution approval** (tool-level). For **post-execution approval** (workflow-level), see [05_agent_06_04_tool-execution-and-approval-canonical.md](05_agent_06_04_tool-execution-and-approval-canonical.md).

## Design Intent

### Pre-checks (Immediate Rejection)

1. **`allowed_tools` Whitelist**: If the list is not empty and the tool is not in the list → Reject
2. **`allowed_root` Jail**: If path arguments are outside `cfg.allowed_root` → Reject
3. **GitHub Repository Allowlist**: If the target repository for a write operation is not in `approval_github_allowed_repos` → Reject (**Fail-closed**)

### Operation Type Classification

`classify_operation_type(tool_name)` returns one of: `READ`, `WRITE`, `DELETE`, `EXECUTE`, `API_WRITE`

### Risk Classification Design Decisions

`classify_risk(cfg, tool_name, args)` determines base risk with the following priority:

1. `approval_risk_rules[tool_name]` (Explicit rules)
2. `tool_safety_tiers[tool_name]` (Tier mapping)
3. Fallback to `tool_constants.py` classification: `DELETE_TOOLS`/`SHELL_TOOLS` → `high`, `WRITE_TOOLS` → `medium`, others → `medium` (default)

**Design judgment**: Tools not found in `tool_safety_tiers` default to `WRITE_DANGEROUS` (**Fail-safe**)

#### Tier-Risk Mapping

| Tier | Risk level |
|---|---|
| `READ_ONLY` | `none` |
| `WRITE_SAFE` | `none` |
| `WRITE_DANGEROUS` | `medium` |
| `ADMIN` | `high` |

#### Risk Level Behavior

| Risk level | Behavior |
|---|---|
| `none` | Automatic approval (no prompt) |
| `medium` | Preview + `y/N` prompt |
| `high` | Preview + full `yes` input required |

**Design judgment**: If base risk is `none`, subsequent override/escalation checks are skipped and `none` is returned immediately.

### Special Risk Overrides

If base risk is anything other than `none`, the following are evaluated before escalation conditions and directly replace the resulting risk if they match:

| Condition | Risk |
|---|---|
| `delete_directory` and `recursive=True` | `high` |
| Any of `force` / `overwrite` / `clobber` argument is `True` | `high` |
| `shell_run` and `command` starts with any of `approval_shell_safe_prefixes` | `none` |
| `shell_run` and does not match above | `high` |

**Note**: These are overrides of `RiskLevel`, not rejections. If it becomes `high`, it proceeds to the standard approval prompt; execution is not completely blocked.

### Risk Escalation

After special case risk determination, the following are further evaluated as escalations:

- Path is included in `approval_protected_paths` → Escalate to `high`
- GitHub branch is in `approval_high_risk_branches` → Escalate to `high`

### GitOps Flags

- `gitops_push_blocked=True` → All GitHub write operations are rejected (**Fail-closed**)

### Dry Run Preview

- Tools in `approval_dry_run_tools` are executed beforehand with `dry_run=True` before the approval prompt.
- If dry run result is `is_error=True`, tools with `RiskLevel.HIGH` are immediately rejected.

### Handling Denials

Rejected tools receive `"Tool execution denied by user."` as their execution result.

## Plan Mode

`/plan` toggles `ctx.conv.plan_mode`:

- When `True`: Tools in `cfg.tool.plan_blocked_tools` are automatically rejected (without prompt)
- Blocked by default: `write_file`, `create_directory`, `delete_file`, `delete_directory`

**Design judgment**: Allows LLM to reason and plan without executing destructive operations.

## Responsibility Boundary

- **Canonical Source**: `agent/tool_policy.py`
- **Preview Format**: Code reference (omitted due to mechanical details)

## Key Constraints

- Fail-closed: GitHub repository allowlist, `gitops_push_blocked`
- Fail-safe: Undefined tools in `tool_safety_tiers` default to `WRITE_DANGEROUS`
- Base risk `none` skips escalation

## Operational Notes

- Unknown

## Known Limitations

- Since GitHub tools are not included in `approval_dry_run_tools` by default, this path is currently dormant.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `05_agent_06_04_tool-execution-and-approval-canonical.md`
- `00_security_02_high-risk-tool-common-policy.md` — High-risk MCP tool common policy (approval-risk tier mapping)

## Keywords

approval flow
risk classification
plan mode
tool result cache
