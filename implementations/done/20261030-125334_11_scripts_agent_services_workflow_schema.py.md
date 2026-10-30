## Goal

Extend `REQUIRED_WORKFLOW_TABLES` with the new columns and point the version-mismatch message at the migration CLI (`REQ-008`, startup check covers the new schema).

## Scope

- Modify only `scripts/agent/services/workflow_schema.py`.

## Assumptions

- Generated after implementation inside the user-approved single-batch run of Plan Phases 2-4 (one release unit: the schema change cannot land without the write-path change); this document records what was executed.
- The wfrecovery001 write-path change (rows 04-08, 10, 26) is one release unit with this row.
- Names that `tools/stale_detector.py` flags are created by other rows of this Plan and exist when the rows run in Plan phase order.

## Design decisions

- N/A: lightweight row.

## Alternatives considered

- N/A: lightweight row.

## Implementation

### Target file

`scripts/agent/services/workflow_schema.py`

### Procedure

1. Add `attempt_number` to the required `attempts` columns and `attempt_id`, `attempt_number` to `processed_events`.
2. Change the version-mismatch error text from recreate-the-database to migrate with `scripts/db/migrate_db.py --apply`.

### Method

- Change only what Procedure names; keep neighbouring code and tests untouched.

### Details

- Fallout in neighbouring tests is corrected in the same release unit.

## Compatibility considerations

- Behavior is stricter by design (typed transitions, persisted numbering); see the Plan.

## Security considerations

- N/A: no new input boundary.

## Rollback considerations

- N/A: revert the commit together with the schema row (the migration itself is forward-only).

## Validation plan

- `uv run pytest tests/agent tests/db -v`
- `uv run ruff check scripts/agent/services/workflow_schema.py`

## Completion criteria

- A database without the new columns or at another version fails the startup check with the migration hint.

## Out of Scope

- Other rows of the Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply Procedure | Completed | 20261030-183035 | 20261030-183035 | Plan Phase 2-4 batch done in batch |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-183035 | 20261030-183035 | executed in the Plan Phase 2-4 single batch; full suite 10516 passed, 1 unrelated flaky eventbus 503 (passes alone); production workflow.sqlite mtime unchanged |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/agent/services/workflow_schema.py