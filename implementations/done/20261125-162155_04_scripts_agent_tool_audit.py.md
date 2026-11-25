## Goal

Populate `turn_id` and `task_linkage` from context in the two audit writers (REQ-004, the writers set `task_id` from the turn and leave `task_linkage` empty).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- UNK-01 resolved (option B, 20261125): `task_id` keeps its current value (the turn id); `turn_id` is added alongside it. No ADR-001 or INV-11 text change.
- The event dataclasses gain the fields first (row 3 procedure); execute this document after row 3.
- `audit_tool_exec` keeps its existing `task_linkage` parameter; the context value is used when the caller passes an empty string.

## Design decisions

- Both writers read `ctx.turn.current_turn_id or ""` for `turn_id` and `ctx.workflow.current_task_id or ""` for `task_linkage`, matching the existing `task_id` pattern (`tool_audit.py:141`, `:277`).
- Conditional serialization of `dedup_state` in `audit_tool_exec` (line 295) is kept as is (Plan Design); this document does not change it.

## Alternatives considered

Passing `turn_id`/`task_linkage` as new call-site parameters was rejected: the writers already have the context, and `tool_approval.py` call sites need no change (Plan Reference Files).

## Implementation
### Target file
`scripts/agent/tool_audit.py`
### Procedure
Fill the new event fields from context in `audit_approval` and `audit_tool_exec`.

### Method
- In `audit_approval` (line 111), set `turn_id=ctx.turn.current_turn_id or ""` and `task_linkage=ctx.workflow.current_task_id or ""` on the constructed `ToolApprovalEvent`.
- In `audit_tool_exec` (line 211), set `turn_id=ctx.turn.current_turn_id or ""` on the constructed `ToolExecEvent`, and use `ctx.workflow.current_task_id or ""` for `task_linkage` when the caller-supplied value is empty.

### Details
- Update the `audit_tool_exec` docstring (line 228 area) to state that `task_linkage` is populated from the workflow context when not supplied.
- The fail-closed branches (`AuditUnavailableError`) and the payload assembly are unchanged.

## Compatibility considerations

Call sites that pass no `task_linkage` now get the workflow value; records written before the change remain parseable (REQ-006). Field-set tests are updated by the row 10 and row 11 procedures.

## Security considerations

N/A: the fields carry identifiers already read from context, no arguments or credentials (mask_args path unchanged).

## Rollback considerations

N/A: revert the commit; the change is additive.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_audit_log_format.py` (covered by the row 10 and row 11 procedures)
- `uv run mypy scripts/agent/tool_audit.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- `tool_approval` and `tool_exec` payloads contain `turn_id` equal to the turn id and `task_linkage` equal to the workflow task id (AC-3).
- `TestAuditApprovalInv11` passes unchanged (`task_id` stays the turn id).

## Out of Scope

- The event dataclass fields themselves (row 3 procedure).
- Test updates (rows 10, 11 — separate documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261125 | Execute after row 3 Step 3a verified: lines 111/211/141/277/295 confirmed; ctx.workflow.current_task_id exists (context.py:330) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261125 | Tests are covered by rows 10 and 11 mypy/ruff clean; tests red pending rows 10/11 fixture updates (expected in batch mode) |

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
- **Requirement ID**: REQ-004 (populate `turn_id`/`task_linkage`), REQ-005 (shared logical call id, unchanged here)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `scripts/agent/tool_audit.py`