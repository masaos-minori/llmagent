<!-- workitem: {"kind":"implementation-procedure","batch_id":"20261101-145309","seq":2,"source_plan":"plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md","source_issue":null,"source_review":null,"target_file":"scripts/agent/workflow/errors.py","generated_at":"2026-11-01T14:53:09Z","schema_version":"1.0","schema_hash":"488513b688446992"} -->

## Goal

Create `scripts/agent/workflow/errors.py` with the three typed workflow-state errors that rows 03/04/05/06/07/08 raise (REQ-002, REQ-004 / AC-2, AC-4).

## Scope

- New file in the existing directory `scripts/agent/workflow/`: `TaskNotFoundError(KeyError)`, `TaskTransitionError(RuntimeError)`, `StageAlreadyRunningError(RuntimeError)`.
- `TaskTransitionError.__init__(current: str, target: str, ...)` builds a message that names the current status.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- `TaskTransitionError` subclasses `RuntimeError` because `tests/agent/test_orchestrator.py:2116` matches on the message containing `halted` and the adapter already surfaces `RuntimeError` (`agent_03_03` `:40`); its message format must keep the current status string in it.
- Exactly three error classes exist in this Plan; no base `WorkflowPersistenceError` hierarchy is introduced.

## Design decisions

- `TaskNotFoundError` subclasses `KeyError` so a missing task also behaves like a lookup miss for existing callers.
- `TaskTransitionError` is reused for attempt-level zero-row transitions (its docstring states it covers task and attempt status transitions); its message names the current status so the orchestrator halted test keeps passing.
- `StageAlreadyRunningError` carries `task_id`/`stage_id` attributes for the row 18 concurrency test.

## Alternatives considered

- One generic error class: rejected — REQ-002/REQ-004 name three distinct conditions (missing row, wrong current status, concurrent start) and tests assert each type.

## Implementation
### Target file
`scripts/agent/workflow/errors.py` (new)

### Procedure
1. Create the module with the three classes and docstrings stating each raise condition.
2. Message templates: `TaskNotFoundError(task_id)` names the id; `TaskTransitionError` renders `current` and `target` statuses; `StageAlreadyRunningError` names the task/stage.

### Method
New file creation (no imports from `scripts/agent/workflow/` siblings except `models` for enum typing).

### Details
- No existing workflow error module exists; engine-local `WorkflowHaltError`/`WorkflowTimeoutError` stay in `workflow_engine.py:77,81` (control-flow, not persistence-state) and are not moved.

## Compatibility considerations

- `errors.py` is imported by rows 03/04/05/06/07/08; keeping the `RuntimeError` base preserves the adapter/orchestrator error contract (row 19 tests).

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Delete the file and revert the importing rows together; nothing persists these classes.

## Validation plan

- Import smoke via the row 12/17/18 tests once those rows land; static: mypy + ruff.
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- The three classes exist, are the only state-error types, and `TaskTransitionError` instances stringify with the current status (AC-2).

## Out of Scope

- Engine control-flow errors (`WorkflowHaltError`, `WorkflowTimeoutError`); HTTP/transport errors.

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
- **Requirement ID**: `REQ-002`, `REQ-004`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `scripts/agent/workflow/errors.py`, `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`
