<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "scripts/agent/tool_audit.py", "target_kind": "source", "seq": 9} -->

## Goal

Record the persisted attempt number in the `stage_completed` audit event written by `scripts/agent/tool_audit.py` (REQ-009 / AC-8).

## Scope

- Extend `audit_stage_completed` (`tool_audit.py:125-132`) with an `attempt_number: int` parameter and add `attempt_number` to the event payload (`:136-145`).

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- The caller supplies the value from `engine.current_attempt_number` (row 08); `tool_audit` does not query the database.

## Design decisions

- `attempt_number` is emitted as a plain integer in the payload; the audit event keeps `workflow_id`/`task_id` as-is so attempt rows, ledger rows, artifact rows, and audit rows correlate on (task_id, stage_id, attempt_number).

## Alternatives considered

- Deriving the number inside `audit_stage_completed` from `attempt_id`: rejected — `attempt_id` has no numbering relation, and `tool_audit` must stay DB-free.

## Implementation
### Target file
`scripts/agent/tool_audit.py`

### Procedure
1. Add the parameter (keyword, required) and the payload field.
2. Keep the function's `ctx` handling (`:125-132`) unchanged.

### Method
Direct edit; additive signature change (single caller at `workflow_engine_adapter.py:375`).

### Details
- Existing `stage_completed` events in audit logs lack the field; no backfill is required (audit is append-only history).

## Compatibility considerations

- Audit-event consumers are read-side only (row 21 test); no schema impact.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.
- Integer value passes JSON encoding as-is; no injection surface.

## Rollback considerations

- Revert with rows 07/08; older audit rows without the field stay valid.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py -v` (row 21 adds the payload test).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- Every new `stage_completed` event carries `attempt_number` equal to the persisted attempt row number (AC-8).

## Out of Scope

- Audit schema docs beyond the payload field; historical event backfill.

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
- **Workflow phase**: Phase 4 (Engine, adapter, and audit correlation)
- **Requirement ID**: `REQ-009`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `scripts/agent/tool_audit.py`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/test_tool_audit.py`
