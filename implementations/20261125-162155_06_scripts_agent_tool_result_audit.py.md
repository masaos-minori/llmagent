## Goal

Create the audit bridge module that writes the `tool_exec` audit line and the `transport_failure` diagnostic record with `dedup_state` and the call ids (REQ-003, REQ-005, REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- New file; `scripts/agent/` exists and importing `agent.tool_audit` and `agent.diagnostic_store` from it creates no cycle (Plan row 6 evidence).
- The event fields (`turn_id`, approval `task_linkage`) exist by then (row 3 procedure); the writers populate them from context (row 4 procedure), so the bridge passes only `dedup_state` and the ids.
- `save_transport_failure` gains the optional id keyword parameters in the row 7 procedure; execute row 7 before this document's diagnostics call is exercised.

## Design decisions

- Two functions, one per write path: `record_tool_exec(ctx, name, args, result, call_id)` and `record_transport_failure(ctx, name, result, call_id)` (Plan row 6 contract).
- In the diagnostic record, `task_id` carries the workflow task id (`ctx.workflow.current_task_id`) and `turn_id` the turn id (`ctx.turn.current_turn_id`); both keys coexist there, unlike the audit events where `task_id` is the turn id (UNK-01 option B).
- The transport-failure guard conditions from the current `_record_transport_failure` (is_error, `error_type == "transport"`, diagnostics wired, off-loop write via `asyncio.to_thread`) are carried over unchanged.

## Alternatives considered

Keeping the logic in `tool_runner.py` was rejected per REQ-007 (size gate); moving it into `tool_audit.py` was rejected because that module is audit-only and the diagnostics write needs `diagnostic_store`.

## Implementation
### Target file
`scripts/agent/tool_result_audit.py` (new)
### Procedure
Create the module with the two bridge functions.

### Method
- `record_tool_exec(ctx, name, args, result, call_id)`: call `audit_tool_exec(ctx, name, args, result.is_error, result.request_id, result.error_type, source=result.source, idempotency_key=call_id, dedup_state=result.dedup_state)`.
- `record_transport_failure(ctx, name, result, call_id)`: keep the existing guard, then call `ctx.diagnostics.save_transport_failure` with the current arguments plus `call_id`, `request_id=result.request_id`, `task_id=ctx.workflow.current_task_id or ""`, `turn_id=ctx.turn.current_turn_id or ""`.

### Details

- Module docstring names the file and its role (audit bridge extracted from `tool_runner.py`, mcpai007).
- No new dataclasses; the functions take the `ToolCallResult` from `shared.transport_dto` and `AgentContext`.

### Companion test files
- `tests/agent/test_dedup_audit_correlation.py` (new)
  - Procedure: end-to-end correlation test (REQ-009): a real `HttpTransport` over `httpx.MockTransport` returns bodies built from `mcp_servers.models.CallToolResponse`; run one call through the runner and assert request id, session id, logical call id, workflow task id, and turn id match between the response, the `tool_exec` audit line, and the `transport_failure` record (AC-7).
  - Validation: `uv run pytest tests/agent/test_dedup_audit_correlation.py`

## Compatibility considerations

New module; no existing consumers. The runner call sites change only by calling these functions (row 5 procedure).

## Security considerations

N/A: the bridge passes ids already derived from context; no raw arguments or credentials enter the records (REQ-005).

## Rollback considerations

N/A: revert the commit; deleting the new file restores the inline path.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_dedup_audit_correlation.py`
- `uv run mypy scripts/agent/tool_result_audit.py`
- `uv run ruff check` and `uv run ruff format`
- `uv run lint-imports` (no new cycle)

## Completion criteria

- Both functions exist with the stated signatures and pass `dedup_state` and the ids through (AC-1, AC-5).
- The correlation test joins the five identifiers across transport response, audit line, and diagnostics record (AC-7).

## Out of Scope

- The runner wiring (row 5 procedure).
- The `save_transport_failure` signature change (row 7 procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Execute after rows 3, 4, 7 |
| 2 | Add the companion test per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (audit carries `dedup_state`), REQ-005 (shared call identity in diagnostics), REQ-007 (extraction target for the size gate)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `scripts/agent/tool_result_audit.py`, `tests/agent/test_dedup_audit_correlation.py`
