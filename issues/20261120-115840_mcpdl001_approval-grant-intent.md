# Bind approval to the logical call and persist Agent intent before dispatch

## Priority
High

## Summary
Make approval a capability that the gateway verifies against the concrete logical call, and record durable Agent intent before any side-effecting HTTP dispatch, failing closed when the required state or audit cannot be written.

## Background
Source: consolidated MCP deduplication two-layer defense backlog (`memo-issue.md`, Issue 1). The part of that item that unifies the logical call identifier is carried by `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`, which was updated to hold it; only the approval, intent, and failure-policy parts are filed here.

Evidence (`Explicit in code`, by reading and `rg`): `scripts/agent/repository_gateway.py` (docstring, lines 6-14 and 59-68) states that approval is enforced upstream by the call order in `tool_runner`, and that callers must route write or risky calls through the approval gate; the gateway does not verify an approval itself. `scripts/agent/tool_runner.py` (lines 189 and 209) catches any exception from state recording with the comment that a recording failure must not break tool execution, so durable state recording is fail-open for side-effecting calls. The tool-call state values are `pending`, `completed`, `failed`, and `interrupted` (`scripts/agent/workflow/tool_call_state_ops.py`, line 30). `ApprovalGrant` and the proposed intent states appear nowhere in the repository. That audit persistence is fail-open for side-effecting calls is a backlog claim and `Needs confirmation`.

## Problem
Approval is guaranteed by call ordering only. If arguments change after approval, or a caller invokes the gateway directly, a side effect can bypass the authorization boundary. When Agent state or audit persistence fails, the call still executes, so after a lost response there is no durable evidence that it was approved and dispatched.

## Reason for Change
Authorization and recovery correctness for side effects. Recovery after response loss (`issues/20261120-115843_mcpdl004_call-state-control-api.md`) depends on durable intent evidence.

## Implementation Intent
Create an immutable grant bound to the logical call, tool, canonical argument hash, risk level, decision, issue and expiry time, and execution mode. The gateway verifies the grant immediately before execution. The Agent persists intent before dispatch and fails closed for side-effecting calls when state or mandatory audit cannot be written. The grant check is Agent-side only; the Git MCP server's own validation stays independent of Agent approval.

## Target Files or Areas
- `scripts/agent/tool_approval.py`, `scripts/agent/repository_gateway.py`, `scripts/agent/tool_runner.py`, `scripts/agent/tool_audit.py`
- `scripts/agent/workflow/tool_call_state_ops.py` and the workflow tool-call state DDL and event models (exact files `Unknown`)
- `tests/agent/test_repository_gateway.py`, `tests/agent/test_tool_runner.py`

## Required Changes
- Add an immutable `ApprovalGrant` bound to logical call id, tool name, canonical argument hash, risk level, decision, issue time, expiry, and execution mode.
- Require a valid grant for write, delete, external API write, and every other side-effect classification; verify it in `RepositoryGateway` before execution; reject tool, argument, mode, call, expiry, and reuse mismatches.
- Persist Agent intent before dispatch with explicit states (for example `prepared`, `dispatch_starting`, `dispatched`, `response_received`, `completed`, `outcome_unknown`, `reconciliation_required`).
- Fail closed for side-effecting calls when state recording or mandatory audit is unavailable; allow best-effort audit only for explicitly read-only calls.
- Record the logical call id in approval, workflow state, execution audit, and diagnostics; keep raw arguments, credentials, signed URLs, and raw exceptions out of audit rows.
- Treat response loss after send as `outcome_unknown`, never as an automatic retry.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change (`governance_01`, `governance_05`); do not write or simulate that approval. ADR-012 INV-04 (Git MCP validation independent of Agent approval) must hold.
- Removing the fail-open recording changes behavior on purpose; list the newly failing paths.
- Follow the Current-Specification-Only policy: no compatibility path for unapproved side-effecting calls.

## Acceptance Criteria
- [ ] An unapproved write cannot execute through `RepositoryGateway`.
- [ ] Arguments cannot change after approval; a grant cannot be reused.
- [ ] A side effect is rejected when durable state or mandatory audit cannot be written.
- [ ] A post-send response loss becomes `outcome_unknown` and is not retried automatically.
- [ ] Approval, state, and audit rows carry the same logical call id.

## Testing Expectations
- Direct gateway invocation without approval; argument and execution-mode mismatch; expiry and reuse; audit and state store outage for side-effecting and read-only calls; correlation across approval, state, and audit.
- Run ruff, mypy, import-linter, and the full test suite.

## Documentation Impact
Yes. The approval capability, the intent states, and the fail-closed failure behavior.

## Out of Scope
- Logical call id generation and propagation (`issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`); MCP-side ledger ownership (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`); reconciliation and result replay (issues/20261120-115843_mcpdl004_call-state-control-api.md).

## Dependencies
- Depends on `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md` for the logical call id. Blocks issues/20261120-115843_mcpdl004_call-state-control-api.md and issues/20261120-115845_mcpdl006_two-layer-failure-verification.md.
- Related: `issues/20261119-140514_mcpai007_dedup-audit-observability.md` (audit identifiers), `issues/20261119-140512_mcpai005_structured-execution-context.md` (execution mode).

## Unresolved Questions
- `不明`: the exact set of Agent state values, and the migration of existing `tool_call_state` rows.
- `不明`: grant lifetime and whether it is configured in `agent.toml` (see issues/20261120-115842_mcpdl003_dedup-config-isolation.md).
- `不明`: whether audit writes are already mandatory for side-effecting calls today.

## AI Implementation Instruction
Write the bypass and outage tests first. Keep grant verification in the Agent and leave the MCP-side validation independent. Do not write ADR approval statements. Stop and report if a caller cannot obtain a grant.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-115840
- **Related target files**: `scripts/agent/tool_approval.py`, `scripts/agent/repository_gateway.py`, `scripts/agent/tool_runner.py`, `scripts/agent/tool_audit.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `tests/agent/test_repository_gateway.py`, `tests/agent/test_tool_runner.py`
