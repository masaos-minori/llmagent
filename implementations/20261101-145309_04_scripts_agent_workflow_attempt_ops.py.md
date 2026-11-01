<!-- workitem: {"kind":"implementation-procedure","batch_id":"20261101-145309","seq":4,"source_plan":"plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md","source_issue":null,"source_review":null,"target_file":"scripts/agent/workflow/attempt_ops.py","generated_at":"2026-11-01T14:53:09Z","schema_version":"1.0","schema_hash":"488513b688446992"} -->

## Goal

Remove the bypass `start_attempt` from `scripts/agent/workflow/attempt_ops.py`, make the canonical attempt lifecycle (`begin_immediate` insert + terminal-only finish) the only path, and gate `finish_attempt` to terminal statuses with a conditional single-row update (REQ-003, REQ-005, REQ-012 / AC-3, AC-5, AC-9).

## Scope

- Delete `start_attempt` (`attempt_ops.py:12-31`) — the marker-less, number-less direct insert.
- Rewrite `finish_attempt` (`:34-48`): `status` restricted to `ATTEMPT_TERMINAL_STATUSES`; `UPDATE attempts SET status=?, ended_at=?, error=? WHERE attempt_id=? AND status='running'`; one updated row required.
- Keep `count_attempts` (`:50-56`) unchanged (diagnostics use).

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- The canonical attempt insert moves to `idempotency_ops.begin_immediate` (row 05); this row only removes the bypass and fixes finish.

## Design decisions

- Zero-row finish: `TaskNotFoundError` when the attempt row is absent, `TaskTransitionError` when it exists but is not `running` (its docstring covers attempt-level transitions, row 02).
- Non-terminal `status` arguments raise `ValueError` before any SQL — the docstring correction REQ-005 documents terminal-only semantics.

## Alternatives considered

- Keeping `start_attempt` as a deprecated wrapper: rejected — AC-9 forbids any caller path that bypasses the canonical transaction.

## Implementation
### Target file
`scripts/agent/workflow/attempt_ops.py`

### Procedure
1. Delete `start_attempt` and its import uses in `state_store.py` (row 06) and tests (rows 12/15).
2. Rewrite `finish_attempt` signature to `finish_attempt(db, attempt_id, status: AttemptStatus, error: str | None)` with the conditional update.
3. Fix the misleading docstring (it currently advertises idempotency the function never provided).

### Method
Direct edit; one deletion, one body rewrite.

### Details
- Callers today: `state_store.finish_attempt` (`state_store.py:149`) and engine via store (`workflow_engine.py:280,291,300`); all land in rows 06/07.
- `error` naming for recovery writes is row 06's concern (`stale recovery` kind), not this function's.

## Compatibility considerations

- Removing `start_attempt` breaks the raw test helpers in rows 12/15 in the same phase; no production caller outside `StateStore`.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.
- Status value reaches SQL only through the enum-restricted parameter.

## Rollback considerations

- Revert rows 04+05+06 as one unit; attempt rows written by the canonical path stay readable by the old code except for the new `attempt_number` column (row 10 DDL).

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py -v` (row 15).
- `rg "start_attempt" scripts tests` → no `attempt_ops`/`StateStore` bypass remains (AC-9).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- `finish_attempt` can only complete-or-fail a `running` attempt, one row; `start_attempt` no longer exists anywhere (AC-5, AC-9).

## Out of Scope

- Attempt-number allocation (row 05); recovery error-kind strings (row 06).

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
- **Workflow phase**: Phase 3 (Attempt lifecycle, ledger, and recovery)
- **Requirement ID**: `REQ-003`, `REQ-005`, `REQ-012`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`
