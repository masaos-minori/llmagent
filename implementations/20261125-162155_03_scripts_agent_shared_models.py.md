## Goal

Add `turn_id` to the two audit event dataclasses and `task_linkage` to `ToolApprovalEvent` (REQ-004, the events have only `task_id`, which carries the turn id).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- UNK-01 resolved (option B, 20261125): `task_id` keeps its current value (the turn id, ADR-001 INV-11); the new fields are additive.
- New fields are appended after the existing defaults so positional constructions keep working; consumers construct by keyword (Plan consumer scan).

## Design decisions

- Both new fields are `str` with `""` defaults, so records written before the change remain parseable (REQ-006).
- `task_linkage` on `ToolExecEvent` already exists (`models.py:59`, the `current_task_id` linkage); this row reuses it and adds the same field to `ToolApprovalEvent`.

## Alternatives considered

Re-pointing `task_id` to the workflow task id (option A of UNK-01) was rejected by the owner: it breaks ADR-001 INV-11 and `TestAuditApprovalInv11`.

## Implementation
### Target file
`scripts/agent/shared/models.py`
### Procedure
Add the defaulted fields to the two event dataclasses.

### Method
- Add `turn_id: str = ""` (new) as the last field of `ToolApprovalEvent` (line 13) and `ToolExecEvent` (line 39).
- Add `task_linkage: str = ""` to `ToolApprovalEvent`, after `idempotency_key` and before the existing trailing fields, matching the `ToolExecEvent` comment style (workflow task id).

### Details
- Update the field comments to state that `turn_id` is the turn id and `task_linkage` is the workflow task id (`ctx.workflow.current_task_id`).
- `ApprovalGrant` and the rest of the module are unchanged.

## Compatibility considerations

Defaulted fields only; older call sites and older audit records stay valid (REQ-006, AC-4). Field-set tests are updated by the row 10 and row 11 procedures.

## Security considerations

N/A: the fields carry identifiers already present in the events, no arguments or credentials.

## Rollback considerations

N/A: revert the commit; the fields are additive and defaulted.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_audit_log_format.py` (covered by the row 10 and row 11 procedures)
- `uv run mypy scripts/agent/shared/models.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- Both dataclasses expose `turn_id`; `ToolApprovalEvent` exposes `task_linkage`; all default to `""`.
- Existing event construction tests pass unchanged.

## Out of Scope

- Populating the fields from context (row 4, `scripts/agent/tool_audit.py`).
- Test updates (rows 10, 11 — separate documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Tests are covered by rows 10 and 11 |

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
- **Requirement ID**: REQ-004 (event `turn_id` and approval `task_linkage`), REQ-006 (additive defaults)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `scripts/agent/shared/models.py`
