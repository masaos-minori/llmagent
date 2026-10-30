## Goal

Create `scripts/agent/workflow/errors.py` with the typed workflow state errors (`REQ-002`, typed not-found and transition errors; `REQ-004`, stage-already-running error).

## Scope

- Create only `scripts/agent/workflow/errors.py` (new file; the directory `scripts/agent/workflow/` exists).

## Assumptions

- Plan Dependencies (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Scope): no schema dependency; Plan Phase 1. Execution order follows the Plan's phases, not `seq`.
- The module imports nothing from the workflow package, so `lint-imports` stays at its baseline of 6 kept contracts.
- `tests/agent/test_orchestrator.py:2116` expects a `RuntimeError` whose message matches `halted` for a halted resume, so `TaskTransitionError` (new) must subclass `RuntimeError` and name the task's current status.

## Design decisions

- One small hierarchy under a common `WorkflowStateError` (new) base that subclasses `RuntimeError`, so existing `except RuntimeError` handling keeps working.
- Errors carry the identifying fields (task or attempt id, expected and actual status) as attributes and in the message.

## Alternatives considered

- N/A: lightweight row, decision fixed in the Plan Design.

## Implementation

### Target file

`scripts/agent/workflow/errors.py` (new)

### Procedure

1. Create the module with a module docstring and these classes: `WorkflowStateError` (new), `TaskNotFoundError` (new), `TaskTransitionError` (new), `AttemptTransitionError` (new), `StageAlreadyRunningError` (new).
2. Give `TaskTransitionError` (new) and `AttemptTransitionError` (new) attributes for the id, the status found, and the status expected or requested; build the message from them, including the current status word.

### Method

- Plain exception classes with an explicit `__init__` taking the fields; no logging, no I/O.

### Details

- Keep the file small (well under the 20480 B module-size gate); English docstrings and comments (`rules/coding.md`).

## Compatibility considerations

- N/A: new module; subclassing `RuntimeError` preserves existing handlers.

## Security considerations

- N/A: messages contain ids and status words only, no payload data.

## Rollback considerations

- N/A: revert the commit (delete the new file).

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` (once the transition rows use these errors)
- `uv run ruff check scripts/agent/workflow/errors.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- The five classes exist, `TaskTransitionError` (new) is a `RuntimeError`, and its message contains the current status.

## Out of Scope

- Raising these errors (`task_ops.py`, `attempt_ops.py`, `idempotency_ops.py` rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the module with the five error classes | Completed | 20261030-144808 | 20261030-144808 | Plan Phase 1 errors.py created |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-144808 | 20261030-144808 | validators passed; tests/agent/workflow/test_workflow_errors.py; full suite passed |

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
- **Requirement ID**: REQ-002 (typed transition errors), REQ-004 (stage-already-running error)
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/agent/workflow/errors.py