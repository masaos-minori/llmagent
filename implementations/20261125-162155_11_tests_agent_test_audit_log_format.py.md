## Goal

Add the new fields to the approval and exec audit-log format contracts (REQ-004, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Execute after rows 3 and 4; the existing contract test `test_approval_event_carries_idempotency_key_field` (line 551) is the pattern to extend.

## Design decisions

- The format contract asserts the serialized payload contains `turn_id` and `task_linkage` with the documented values, not only that the keys exist.

## Alternatives considered

N/A: test-only change.

## Implementation
### Target file
`tests/agent/test_audit_log_format.py`
### Procedure
Extend the approval and exec format contract tests.

### Method
- Add approval-format cases: `turn_id` equals the turn id and `task_linkage` equals the workflow task id.
- Add exec-format cases: the same two fields, plus the conditional `dedup_state` key (present only when non-empty).

### Details
- Older-shape compatibility case: a payload without the new fields still parses (REQ-006, AC-4).

## Compatibility considerations

N/A: tests only.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_audit_log_format.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- AC-3 and AC-4 are pinned on the format-contract side.

## Out of Scope

- The writers and event dataclasses (rows 3, 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | Execute after rows 3 and 4 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-006 (format-contract pins)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `tests/agent/test_audit_log_format.py`
