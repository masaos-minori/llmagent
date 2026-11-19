# Align MDQ write approval, dry-run previews, and structured response metadata

## Priority
High

## Summary
Raise MDQ write approval risk and implement safe dry-run previews using the structured file outcomes and transaction semantics from the earlier issues.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 7).

Evidence (`Explicit in code`, by `rg`): `config/agent.toml:337-338` sets `index_paths` and `refresh_index` to `WRITE_SAFE`. Forced-refresh escalation, generic preview truncation, and the absence of MDQ `dry_run` are backlog claims and `Needs confirmation`. The general execution-context and dry-run contract is `issues/20261119-140512_mcpai005_structured-execution-context.md`; this issue covers the MDQ-specific approval and preview behavior only.

## Problem
MDQ writes modify indexed state but are automatically approved; forced refresh does not escalate; previews cannot show planned file-level effects.

## Reason for Change
User-safety: approval must match risk, and previews must be accurate; they need reliable outcomes first.

## Implementation Intent
Index and normal refresh require MEDIUM approval, forced refresh HIGH. Dry-run shares scan, authorization, and decision logic with real execution but never opens a write transaction. Previews are structured and non-sensitive, separate from persistent audit.

## Target Files or Areas
- `config/agent.toml`, `scripts/agent/tool_policy.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_result_formatter.py`
- MDQ write request and result models and service
- `tests/agent/test_tool_result_formatter.py`, `tests/agent/test_tool_audit.py`; new `tests/mcp_servers/mdq/test_mdq_dry_run.py` (absent); an MDQ dry-run design document (none exists, create it)

## Required Changes
- Set index and normal refresh to MEDIUM and forced refresh to HIGH; apply a MEDIUM floor to write tools unless a reviewed exception exists; evaluate force and protected paths before NONE-risk short-circuits.
- Add `dry_run` to write requests and public schemas; reuse scan, authorization, and decision logic without a write transaction; return planned add, update, delete, skip, warning, and failure counts; show common roots and representative paths without persisting every absolute path; add MDQ-specific approval formatting; keep approval display and persistent audit redaction separate.

## Constraints
- Dry-run performs no database or state mutation.
- Follow the execution-mode and result-metadata contract of `issues/20261119-140512_mcpai005_structured-execution-context.md`.

## Acceptance Criteria
- [ ] Approval risk matches operation mode.
- [ ] Dry-run performs no mutation; preview counts match subsequent execution decisions when the filesystem is unchanged.
- [ ] Absolute path lists are not persisted in audit logs.
- [ ] Existing automatic-approval tests are replaced.

## Testing Expectations
- Index, normal refresh, forced refresh, and protected-path approval tests; dry-run no-op and preview and execution parity tests; preview redaction and large-path-list tests.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Safety tiers, approval rules, operator examples, preview fields, and filesystem-change caveats.

## Out of Scope
- The shared execution context and dispatcher dry-run detection (`issues/20261119-140512_mcpai005_structured-execution-context.md`).

## Dependencies
- Depends on `issues/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md` and `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`; related to `issues/20261119-140512_mcpai005_structured-execution-context.md`. Blocks `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`.

## Unresolved Questions
- `不明`: whether a reviewed exception to the MEDIUM floor is needed for any write tool.
- `不明`: preview field names, which must follow the shared result metadata decided in the mcpai005 plan.

## AI Implementation Instruction
Write approval-risk tests per mode first. Do not add output-marker dry-run detection. Stop and report if the shared contract is not yet decided.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-142129
- **Related target files**: `config/agent.toml`, `scripts/agent/tool_policy.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_result_formatter.py`
