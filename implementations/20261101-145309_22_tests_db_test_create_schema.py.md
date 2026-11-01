<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "tests/db/test_create_schema.py", "target_kind": "test", "seq": 22} -->

## Goal

Update the workflow DDL copy in `tests/db/test_create_schema.py` and add the constraint and migration behavior tests (REQ-008, REQ-011 / AC-10).

## Scope

- `_WORKFLOW_SCHEMA_NO_VEC0` (`test_create_schema.py:375-421`, tasks copy at `:379-386`): mirror the new `CHECK` constraints, `attempt_number`, unique index, and ledger columns.
- New tests: `CHECK` rejects out-of-vocabulary status; the unique index rejects duplicate (task, stage, attempt_number); migration of a v1-shaped database (built from the pre-change DDL copy) preserves rows and backfills `attempt_number` by `ROW_NUMBER() OVER (PARTITION BY task_id, stage_id ORDER BY started_at, rowid)`; migration precondition refuses a database containing out-of-vocabulary status rows, listing the offending rows; `PRAGMA foreign_key_check` clean after rebuild.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- The pre-change (v1-era) shape already present at `:391` (attempts without `attempt_number`) doubles as the migration fixture source.

## Design decisions

- Migration behavior is tested through the public runner API (row 26's registered specs), not by calling private helpers.

## Alternatives considered

- Fixture databases copied from production dumps: rejected — not available under `rules/ai-execution.md` repository tool usage.

## Implementation
### Target file
`tests/db/test_create_schema.py`

### Procedure
1. Update the embedded DDL copy.
2. Add `TestWorkflowConstraints` and `TestWorkflowMigration` classes.

### Method
Direct edit plus new test classes.

### Details
- Existing assertions in this file guard fresh-create behavior; they must keep passing after the row-10 DDL change in the same commit.

## Compatibility considerations

- Note for the owner: `tests/db/test_migrations_workflow.py` (620 lines, registry expectations for head version 2) is outside the frozen table but will fail when `WORKFLOW_TARGET_VERSION` bumps — flag as a follow-up target at landing (no unauthorized edits).

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Revert with rows 10/26.

## Validation plan

- `uv run pytest tests/db/ -v`.
- Migration tests must run valid and invalid databases end-to-end (REQ-011).

## Completion criteria

- Fresh-shape constraints, migration of valid databases, and fail-closed rejection of invalid databases are all proven (AC-10).

## Out of Scope

- Startup required-column checks (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 2 (Schema and migration)
- **Requirement ID**: `REQ-008`, `REQ-011`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `tests/db/test_create_schema.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`
