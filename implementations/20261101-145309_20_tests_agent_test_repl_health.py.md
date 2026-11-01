<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "tests/agent/test_repl_health.py", "target_kind": "test", "seq": 20} -->

## Goal

Update the minimal workflow-table fixtures in `tests/agent/test_repl_health.py` so they match the new required columns (REQ-008 / AC-10).

## Scope

- `_create_workflow_db` (`test_repl_health.py:523` region, CREATE TABLE fixtures at `:535-554`): add `attempt_number` to `attempts`, `attempt_id`/`attempt_number` to `processed_events`.
- Missing-column diagnostic tests (`:548-554`, `missing_column` at `:548-549`; example INSERT at `:599`): extend to the new columns so the health report names them.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- This suite intentionally builds divergent minimal tables (not `schema_sql` DDL) to exercise the health check — fixtures must stay hand-written copies, kept shape-current by this row.

## Design decisions

- Fixture divergence stays deliberate: the tests' value is detecting drift between a real database and the required-column list (row 11).

## Alternatives considered

- Importing `_WORKFLOW_SCHEMA` into the fixtures: rejected — the suite's purpose is testing the checker against drifted schemas.

## Implementation
### Target file
`tests/agent/test_repl_health.py`

### Procedure
1. Update the CREATE TABLE statements.
2. Add one negative case: table missing `attempt_number` is reported.

### Method
Direct edit of fixture SQL and assertions.

### Details
- INSERT fixtures (`:599` region) gain the new columns to stay valid.

## Compatibility considerations

- Must land with rows 10/11 in Phase 2 or the health-check assertions drift.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Revert with rows 10/11.

## Validation plan

- `uv run pytest tests/agent/test_repl_health.py -v`.

## Completion criteria

- Health-report fixtures and diagnostics cover the new required columns (AC-10).

## Out of Scope

- Real-migration fixtures (row 22).

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
- **Requirement ID**: `REQ-008`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `tests/agent/test_repl_health.py`, `scripts/agent/services/workflow_schema.py`, `scripts/db/schema_sql.py`
