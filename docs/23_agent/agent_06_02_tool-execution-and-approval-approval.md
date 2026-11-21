---
title: "Agent Tool Execution and Approval - Approval Flow"
area: agent
tags:
  - agent
  - tool-execution
  - approval-flow
related:
  - agent_00_document-guide.md
  - agent_06_04_tool-execution-and-approval-canonical.md
  - agent_06_01_tool-execution-and-approval-execution.md
  - agent_06_03_tool-execution-and-approval-concurrency-safety.md
  - security_02_high-risk-tool-common-policy.md
  - agent_03_01_turn-processing-flow-overview.md
  - mcp_03_01_dispatch-and-routing.md
---

# Agent Tool Execution and Approval

- Turn Flow → [agent_03_01_turn-processing-flow-overview.md](agent_03_01_turn-processing-flow-overview.md)
- MCP Routing → [mcp_03_01_dispatch-and-routing.md](../22_mcp/mcp_03_01_dispatch-and-routing.md)

## Purpose

Documents design decisions for approval flows, risk classification, and plan mode.

**Note**: This document covers the tool-level approval decided before a Tool executes; the workflow has no approval stage (see [agent_06_04_tool-execution-and-approval-canonical.md](agent_06_04_tool-execution-and-approval-canonical.md)). Every decision, approved or denied, is written to the audit log as a `tool_approval` event that carries the `workflow_id` and the turn ID in its `task_id` field.

## Design Intent

### Pre-checks (Immediate Rejection)

1. **`allowed_tools` Whitelist**: If the tool is not in the list (an empty list denies every tool under `explicit_allowlist`; valid under `discovered`) → Reject
2. **`allowed_root` Jail**: If path arguments are outside `cfg.approval.allowed_root` → Reject; `allowed_root` is required (an empty or absent value fails config load, so the check never skips)
3. **GitHub Repository Allowlist**: If the target repository for a write operation is not in `approval_github_allowed_repos` → Reject (**Fail-closed**)

### Operation Type Classification

`classify_operation_type(tool_name)` returns one of: `READ`, `WRITE`, `DELETE`, `EXECUTE`, `API_WRITE`

### Risk Classification Design Decisions

`classify_risk(cfg, tool_name, args, registry)` determines base risk with the following priority:

1. The registered tool's declared `agent_safety_tier`, mapped through `_TIER_TO_RISK` (see the Tier-Risk Mapping table)
2. A tool absent from the registry, and a call without a registry, resolves to `high` (Fail-safe): with no declaration there is nothing to consult, and risk is never inferred from a tool name

**Evaluation order**: the base risk is the declared tier mapping above, evaluated in `classify_risk()` (`agent/tool_policy.py`). **A base of `RiskLevel.NONE` returns before Special Risk Overrides and Risk Escalation** — a tier-derived `none` (see the Tier-Risk Mapping table) is never raised by a protected path or a special-case flag. The removed per-tool config maps no longer contribute: the declared tier is the single risk source (ADR-003, agentcfg003).

**Vocabulary**: the *safety tier* (`READ_ONLY`/`WRITE_SAFE`/`WRITE_DANGEROUS`/`ADMIN`, the `agent_safety_tier` each tool declares) and the *approval risk* (`none`/`medium`/`high`, `RiskLevel`) are distinct. Only the approval risk decides whether a prompt is shown; the tier maps to it through `_TIER_TO_RISK` (for example, `write_file` declares `WRITE_SAFE` and resolves to `none`, `delete_file` declares `WRITE_DANGEROUS` and resolves to `medium`).

**Design judgment**: each tool's tier is declared by its producer and validated against the closed tier value set at registration, so an untiered or mis-typed tool never reaches classification. A tool absent from the registry entirely is classified `high` (**Fail-safe**).

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

### Special Risk Overrides

If base risk is anything other than `none`, the following are evaluated before escalation conditions and directly replace the resulting risk if they match:

| Condition | Risk |
|---|---|
| `delete_directory` and `recursive=True` | `high` |
| Any of `force` / `overwrite` / `clobber` argument is `True` | `high` |
| `shell_run` whose executable is in `approval_shell_safe_prefixes` and whose parsed arguments match the agent-side read-only safe-shape rule (read-only `git` subcommands: `log`, `status`, `show`, `diff`, and list-only `branch`; `cat`, `echo`, `ls`, `pwd`, `grep`, `find` without denied flags) | `none` |
| `shell_run` and does not match above | `high` |

**Note**: These are overrides of `RiskLevel`, not rejections. If it becomes `high`, it proceeds to the standard approval prompt; execution is not completely blocked. `shell_run` auto-approval requires both conditions: `approval_shell_safe_prefixes` gates the executable, and the agent-side safe-shape rule decides subcommand and flag acceptability. An executable without a defined read-only shape is `high` even when the config list matches it, so interpreters and test runners (`python`, `pytest`, `uv run`) always take the approval prompt.

### Risk Escalation

After special case risk determination, the following are further evaluated as escalations:

- Path is included in `approval_protected_paths` → Escalate to `high`
- GitHub branch is in `approval_high_risk_branches` → Escalate to `high`

**Protected-path scope**: escalation only ever sees paths inside `allowed_root` — a path outside the jail is rejected by `check_allowed_root()` at the pre-check stage, before risk classification runs (`check_approval()`, `agent/tool_approval.py`). Because a tier-derived base of `none` returns before escalation, escalation applies only to tools whose declared tier maps to `medium` or above: under the shipped tiers `delete_file`, `delete_directory` and the git write tools resolve to `high` on a protected path in-jail, and a protected path outside the jail never reaches the prompt: the two mechanisms stay distinct — the jail denies, the escalation prompts.

### GitOps Flags

- `gitops_push_blocked=True` → All GitHub write operations are rejected (**Fail-closed**)

### Dry Run Preview

- A tool that declares `preview_capability="dry_run"` is executed beforehand with `dry_run=True` before the approval prompt. A tool declaring `preview_capability="none"` is never pre-executed and gets a static preview.
- If dry run result is `is_error=True`, tools with `RiskLevel.HIGH` are immediately rejected.

### Handling Denials

Rejected tools receive `"Tool execution denied by user."` as their execution result.

## Plan Mode

`/plan` toggles `ctx.conv.plan_mode`:

- When `True`: only tools whose declared `agent_safety_tier` is `READ_ONLY` may run. Every other tool is rejected automatically, without a prompt and before the approval flow. A tool absent from the registry, including an unknown tool name, is rejected (fail-closed).
- Tools in `cfg.tool.plan_blocked_tools` are rejected in addition, whatever their tier. The list is an operational exception on top of the tier rule: an empty list does not relax the tier rule.
- The rule covers the file write, edit, move and delete tools, `shell_run`, the Git write tools (`git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push`), the GitHub write tools, and the RAG and MDQ index-changing tools, because none of them is `READ_ONLY`.

**Design judgment**: Plan mode lets the LLM read and reason without changing anything: it is a read-only guarantee derived from the safety tiers, not a configured name list.

## Responsibility Boundary

- **Canonical Source**: `agent/tool_policy.py`

## Key Constraints

- Fail-closed: GitHub repository allowlist, `gitops_push_blocked`
- Fail-safe: a tool absent from the registry is classified `high` at classification time and rejected in plan mode
- Base risk `none` skips the override and escalation checks and returns `none` immediately

## Known Limitations

- The dry-run preview is built by executing the tool with `dry_run=True` **before** the user approves. `check_approval` builds the preview through `_build_preview_with_dry_run` in `scripts/agent/tool_approval.py`, then emits the prompt and reads the decision. A tool with declared dry-run capability therefore runs once before approval; its server must treat `dry_run=True` as a hard no-op (no write/delete/network/database side effect).
- The `preview_capability="dry_run"` declaration is a per-tool contract: each declaring tool's server must guarantee zero write/delete/network/database side effects under `dry_run=True`, verified during the approval subsystem's tool audit. A tool that cannot guarantee a no-op must declare `preview_capability="none"` and takes the static text-only preview instead.
- GitHub write tools declare dry-run preview capability, but this path is dormant today: `approval_github_allowed_repos` is empty, so `check_allowed_repo` (in `scripts/agent/tool_policy.py`) fails closed at preflight and denies every GitHub write tool before the dry-run preview runs.

## Keywords

- approval flow
- risk classification
- plan mode
