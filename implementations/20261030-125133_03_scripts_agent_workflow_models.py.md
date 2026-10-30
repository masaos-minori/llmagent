## Goal

Rename `TaskRecord.idempotency_key` to `task_nonce` (new) (`REQ-003`, accurate key name) so the field no longer implies request deduplication.

## Scope

- Modify only `scripts/agent/workflow/models.py` (the `TaskRecord` dataclass).

## Assumptions

- Plan Dependencies (`plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` Scope): the rename ships as one release unit with row 01 Step 2, the schema row (`scripts/db/schema_sql.py`), and the migration step, after dbmig001 Phase 3; this document MUST NOT run alone.
- Plan overlap judgment (Step 8b): `models.py` is also a target of `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (status enums) and `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` (`RetryPolicy` field): sequencing dependency, different dataclasses, rebase in landing order.
- `TaskRecord` is constructed with keyword arguments at `task_ops.py:53` and `:78` and in `tests/agent/workflow/test_workflow_models.py:25`; `state_store.py` constructs it only in `_row_to_task`, which row 02 deletes.

## Design decisions

- Rename in place, keeping the field's position (between `status` and `created_at`), so positional construction, if any, is unaffected.

## Alternatives considered

- N/A: the name and contract are decided in the Plan (Design, key contract).

## Implementation

### Target file

`scripts/agent/workflow/models.py`

### Procedure

1. In `TaskRecord` (`:13`), rename the field `idempotency_key: str` (`:21`) to `task_nonce` (new), keeping the type `str`.

### Method

- One-line change; no default is added, the field stays required.

### Details

- Keep the other status comment as is (`pending | running | completed | failed | halted`); status typing belongs to the wfrecovery001 Plan.

## Compatibility considerations

- Public dataclass field rename; keyword users must change in the same release (rows 01, 08, and the test rows).

## Security considerations

- N/A: naming only.

## Rollback considerations

- N/A: revert the commit together with the schema and migration rows (the migration itself is forward-only).

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_models.py -v`
- `rg idempotency_key scripts/agent/workflow/models.py` (empty)
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`

## Completion criteria

- `TaskRecord` exposes `task_nonce` (new) and no `idempotency_key`.

## Out of Scope

- Constructors, DDL, migration, tests, and docs (other rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the `TaskRecord` field | Pending | — | — | Gated: release unit with the schema row, after dbmig001 Phase 3 |
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
- **Requirement ID**: REQ-003 (rename the task key)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125133
- **Related target files**: scripts/agent/workflow/models.py
