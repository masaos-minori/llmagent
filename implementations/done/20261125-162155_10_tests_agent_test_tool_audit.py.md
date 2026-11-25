## Goal

Update the audit serialization tests for the new event fields and the conditional `dedup_state` key (REQ-004, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Execute after rows 3 and 4 (the fields and their population exist); the exact-field-set pin at lines 385-403 fails until `turn_id` is added here.

## Design decisions

- The field-set pin gains `turn_id`; `task_linkage` is already in the expected set.

## Alternatives considered

N/A: test-only change.

## Implementation
### Target file
`tests/agent/test_tool_audit.py`
### Procedure
Extend the field-set pin and the serialization cases.

### Method
- Add `turn_id` to the `expected` set in `test_existing_record_fields_byte_stable` (line 380).
- Step 3a finding: `_make_ctx` (line 73) sets `turn.current_turn_id` and `workflow.workflow_id` but not `workflow.current_task_id`; the row 4 writer now reads it, so the fixture must set `ctx.workflow.current_task_id` (a MagicMock attribute breaks JSON serialization — 42 tests red until this lands).
- Add cases: `turn_id` equals the turn id, `task_linkage` equals the workflow task id, `dedup_state` appears only when non-empty, and an older-shape record without the new fields still parses (REQ-006).

### Details
- `TestAuditApprovalInv11` (line 87) keeps asserting `task_id` is the turn id (option B); add the approval `turn_id`/`task_linkage` assertions there.

## Compatibility considerations

N/A: tests only.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- AC-3 and AC-4 are pinned by the updated tests.

## Out of Scope

- The writers and event dataclasses (rows 3, 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | — | 20261125 | Execute after rows 3 and 4 fixture sets workflow.current_task_id; field-set pin gains turn_id; new cases added |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261125 | 58 passed; ruff clean |

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
- **Requirement ID**: REQ-004, REQ-006 (audit serialization pins)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `tests/agent/test_tool_audit.py`