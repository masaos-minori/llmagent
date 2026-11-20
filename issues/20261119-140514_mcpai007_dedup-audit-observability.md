# Complete transport and audit observability for deduplication and correlation identifiers

## Priority
Medium

## Summary
Carry `dedup_state` and correctly separated workflow, task, turn, call, session, and request identifiers through transport results and Agent audit events.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 7).

Evidence (`Explicit in code`, by `rg`): `dedup_state` exists only in `scripts/mcp_servers/models.py:45` and `scripts/mcp_servers/dispatch.py`; no occurrence in `scripts/shared/` or `scripts/agent/`, so the transport DTO and Agent audit do not carry it. The turn-id-in-task-id audit mapping claim is from the review and `Needs confirmation`.

## Problem
The MCP response can contain a dedup state, but the HTTP transport and `ToolCallResult` discard it, and the audit event mapping places the turn id in the task id field (`Needs confirmation`), preventing reliable workflow correlation.

## Reason for Change
Operators cannot tell whether a result was executed, replayed, duplicated, in progress, blocked, or affected by a store error without reconstructing it from logs. No time-sensitive trigger is known.

## Implementation Intent
Make execution state and identifiers observable fields: parse `dedup_state` from successful and tool-level error responses, preserve it through gateway and executor, and record it with separated identifiers in audit.

## Target Files or Areas
- `scripts/shared/transport_dto.py`, `scripts/shared/http_transport.py`
- `scripts/agent/shared/models.py`, `scripts/agent/tool_audit.py`, `scripts/agent/tool_runner.py`

## Required Changes
- Add `dedup_state` to `ToolCallResult` and execution audit events; parse it from success and tool-level error responses.
- Add `turn_id` to approval, decision, and execution audit events; populate `task_id` from workflow state and `turn_id` from turn state.
- Keep logical key components consistent with audit fields; update downstream parsers and queries.
- Record the logical call id in approval, workflow state, execution audit, and diagnostics, and keep raw arguments, credentials, signed URLs, and raw exceptions out of audit rows.

## Constraints
- Missing optional fields must remain readable (backward compatibility documented).

## Acceptance Criteria
- [ ] Agent audit records `duplicate_hit`, `in_progress`, `replayed`, `store_error`, and `review_required`.
- [ ] Tool-level errors preserve dedup state.
- [ ] Task and turn identifiers are both present and correct; request, session, call, task, and turn can be correlated directly.
- [ ] Backward compatibility for missing optional fields is documented.
- [ ] Approval, state, audit, and diagnostic records carry the same logical call id and no raw argument or credential.

## Testing Expectations
- HTTP response parser tests for each dedup state; audit serialization tests for task and turn identifiers.
- End-to-end correlation test across Agent audit and the MCP response.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Audit event field definitions and the compatibility note (intent and boundaries; final sweep in `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`).

## Out of Scope
- Defining the dedup states (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`) or the key (`issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`).

## Dependencies
- Depends on `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (definitive dedup states) and `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md` (definitive correlation identifiers). DTO changes may start earlier; audit acceptance needs both.
- Recommended, not blocking, for `issues/20261119-140513_mcpai006_github-write-retry-policy.md`.
- Related: `issues/20261120-115840_mcpdl001_approval-grant-intent.md` makes audit and state persistence fail-closed for side-effecting calls; this issue defines the fields that persistence writes.

## Unresolved Questions
- `不明`: downstream consumers of the audit schema that need updating (not enumerated in this session).

## AI Implementation Instruction
Add fields additively and keep older records parseable. Do not change the dedup state set. Stop and report if the audit schema has a versioned consumer.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140514
- **Related target files**: `scripts/shared/transport_dto.py`, `scripts/shared/http_transport.py`, `scripts/agent/shared/models.py`, `scripts/agent/tool_audit.py`, `scripts/agent/tool_runner.py`
