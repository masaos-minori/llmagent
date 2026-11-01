<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "scripts/agent/services/workflow_schema.py", "target_kind": "source", "seq": 11} -->

## Goal

Extend the startup workflow-schema check in `scripts/agent/services/workflow_schema.py` so the new columns are required (REQ-008 / AC-10).

## Scope

- `REQUIRED_WORKFLOW_TABLES` (`workflow_schema.py:46-52`): add `attempt_number` to `attempts`, `attempt_id`/`attempt_number` to `processed_events`.
- The `PRAGMA table_info` comparison loop (`:93-100`) already consumes these lists; no new check logic.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Check grade/score (Plan blast-radius: `check_workflow_schema` grade C) is not re-scored by this row.

## Design decisions

- The check stays a column-presence check: `CHECK` constraints themselves are not validated here — the migration postcondition (row 26) and fresh DDL own constraint shape.

## Alternatives considered

- Reading `PRAGMA index_list` for the unique index: rejected — out of REQ-008's stated startup-check scope.

## Implementation
### Target file
`scripts/agent/services/workflow_schema.py`

### Procedure
1. Edit the two lists in `REQUIRED_WORKFLOW_TABLES`.
2. Verify `check_workflow_schema` failure messages list the missing column names.

### Method
Direct edit; constant change only.

### Details
- `tasks` list (`:47`) already requires `status`; the vocabulary itself is enforced by SQL, not here.

## Compatibility considerations

- Deploy/startup path: a database migrated by row 26 passes; an un-migrated old database now fails fast at startup with the missing-column error (intended fail-closed behavior).

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Constant revert; paired with the row-10 revert.

## Validation plan

- `uv run pytest tests/agent/test_repl_health.py -v` (row 20 fixtures) and `tests/unit/` startup-check tests if present; TOOLCHAIN below.
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- Startup rejects a workflow database missing `attempts.attempt_number` or the ledger correlation columns (AC-10).

## Out of Scope

- Migration execution (row 26).

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
- **Related target files**: `scripts/agent/services/workflow_schema.py`, `scripts/db/schema_sql.py`, `tests/agent/test_repl_health.py`
