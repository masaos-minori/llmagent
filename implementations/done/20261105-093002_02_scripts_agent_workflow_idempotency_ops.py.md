## Goal
- Document, at the `INSERT INTO attempts` of `begin_stage_if_new`, why it does not call `attempt_ops.start_attempt`, so a later reader does not "consolidate" it and split the transaction (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit
- One comment in `scripts/agent/workflow/idempotency_ops.py`; no behavior change.

## Assumptions
- `begin_stage_if_new` inserts the attempt and the `processed_events` row inside one `with db.begin_immediate():` block, after `is_event_processed`; `attempt_ops.start_attempt` commits on its own and cannot join that transaction.

## Design decisions
- Comment only; the transaction and SQL stay exactly as they are.

## Alternatives considered
- N/A: comment-only change.

## Implementation
### Target file
`scripts/agent/workflow/idempotency_ops.py`

### Procedure
1. Add a short English comment immediately above the `db.execute(...)` that runs `INSERT INTO attempts` inside `begin_stage_if_new`.

### Method
- Content: this insert is deliberately not `attempt_ops.start_attempt`; it must stay in the same `begin_immediate()` transaction as the `processed_events` check and insert, whereas `start_attempt` commits on its own; the two share the column set, so change them together.
- Keep it to three lines; do not reflow code.

### Details
- After the edit the file still has exactly one `INSERT INTO attempts`, and `git diff` shows only comment lines.

## Compatibility considerations
- N/A: comment-only change.

## Security considerations
- N/A: comment-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow`; `uv run ruff check scripts/agent/workflow/idempotency_ops.py`; `rg "INSERT INTO attempts|UPDATE attempts" scripts` matches the counts in the Plan (two inserts: `attempt_ops.py` and this file).

## Completion criteria
- The comment is present, the insert and its transaction are unchanged, and the checks above pass.

## Out of Scope
- `state_store.py` (procedure `_01`) and any change to `attempt_ops.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the comment above the `INSERT INTO attempts` | Completed | 20261105-142144 | 20261105-142144 | STEP: comment added above INSERT INTO attempts; diff is comment-only (3 lines); ruff/format/mypy clean |
| 2 | Run the validation commands and confirm a comment-only diff | Completed | 20261105-142149 | 20261105-142149 | STEP: 154 workflow tests + full suite 11556 passed; diff-cover 100%; rg counts match plan (2 INSERT INTO attempts, 2 UPDATE attempts) |

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
- **Requirement ID**: `REQ-003` (cross-reference comment, transaction unchanged)
- **Source issue**: issues/20261103-134148_wfreview006_duplicate-attempt-crud-apis.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-090240_wfreview006_duplicate-attempt-crud-apis.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-093002
- **Related target files**: `scripts/agent/workflow/idempotency_ops.py`