<!-- workitem: {"kind":"implementation-procedure","batch_id":"20261101-145309","seq":1,"source_plan":"plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md","source_issue":null,"source_review":null,"target_file":"scripts/agent/workflow/models.py","generated_at":"2026-11-01T14:53:09Z","schema_version":"1.0","schema_hash":"488513b688446992"} -->

## Goal

Replace the free-text status comments in `scripts/agent/workflow/models.py` with typed `TaskStatus`/`AttemptStatus` enums and one canonical transition matrix that every state-writing module imports (REQ-001 / AC-1).

## Scope

- Add `TaskStatus` (`pending`, `running`, `completed`, `failed`, `halted`) and `AttemptStatus` (`running`, `completed`, `failed`).
- Add `TASK_TRANSITIONS` per the REQ-001 matrix and `ATTEMPT_TERMINAL_STATUSES` (`completed`, `failed`).
- Add `can_transition(current, target)` as the single query helper used by `task_ops.py`, `attempt_ops.py`, and the migration precondition.
- Replace the status comments at `models.py:20,34` with references to the enums.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- `TaskRecord.status`/`AttemptRecord.status` stay `str` fields; enum typing is enforced at the write sites, not by changing dataclass field types (avoids row-mapping churn).

## Design decisions

- `TASK_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]]` is the only place the matrix is written; `completed -> failed` is included and marked transitional (removed by the retry issue per REQ-001).
- `halted` and `completed` (except the transitional edge) are terminal: empty target sets.
- Enum values are plain strings identical to the SQL `CHECK` vocabulary that row 10 adds, so the REQ-001 equality test can compare enum members against the parsed DDL.

## Alternatives considered

- String constants instead of enums: rejected — the REQ-001 acceptance criterion requires an enum-to-CHECK equality test, which needs an enumerable source.

## Implementation
### Target file
`scripts/agent/workflow/models.py`

### Procedure
1. Add `class TaskStatus(str, Enum)` with the five members and `class AttemptStatus(str, Enum)` with the three members.
2. Add `TASK_TRANSITIONS` and `ATTEMPT_TERMINAL_STATUSES` constants with the REQ-001 matrix.
3. Add `can_transition(current: TaskStatus, target: TaskStatus) -> bool`.
4. Reword the comments at `:20` (task status) and `:34` (attempt status) to name the enums.

### Method
Direct edit; additive only — no existing function or dataclass field signature changes.

### Details
- Matrix edges: `pending -> {running, halted}`; `running -> {completed, failed, halted}`; `failed -> {running}`; `completed -> {failed}` (transitional); `halted -> {}`.
- `models.py` currently has no status enum (comments at `:20,34`); importers must not re-declare status literals afterwards (enforced by the row 16 test).

## Compatibility considerations

- Rows 03/06/07/08 import the enums and matrix; the SQL `CHECK` vocabulary added by row 10 must equal the enum values exactly (REQ-001 test, row 16).

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Purely additive change; revert is `git checkout -- scripts/agent/workflow/models.py` with no data impact.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_models.py -v` (row 16 adds the matrix and CHECK-vocabulary tests).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- The five/four-value vocabulary is defined once, the matrix is importable, and no other module defines its own status literal set (AC-1).

## Out of Scope

- SQL `CHECK` constraints (row 10); transition enforcement logic (rows 03/04/06).

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
- **Workflow phase**: Phase 1 (Vocabulary, errors, and task transitions)
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `scripts/agent/workflow/models.py`, `scripts/agent/workflow/errors.py`, `scripts/agent/workflow/task_ops.py`, `scripts/db/schema_sql.py`, `tests/agent/workflow/test_workflow_models.py`
