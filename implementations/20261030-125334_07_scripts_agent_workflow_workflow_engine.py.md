## Goal

Make `scripts/agent/workflow/workflow_engine.py` claim tasks through the transition contract, use persisted attempt numbers and a persisted retry budget, and expose the current attempt number (`REQ-007`, claim and persisted budget; `REQ-009`, attempt number for correlation).

## Scope

- Modify only `scripts/agent/workflow/workflow_engine.py`.
- Retry eligibility by error kind, timeout classification, and failure routing belong to the retry Plan and are not changed here.

## Assumptions

- Plan Dependencies (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Scope): Plan Phase 4, after the schema row (its procedure documents `20261030-125334_10`, `_22`, and `_26` exist since 2026-10-30) and rows 01-06. This document MUST NOT be executed before the Phase 2 schema and Phase 3 rows exist.
- Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `workflow_engine.py` is also a target of `plans/20261030-114516_wflease001_stale-attempt-lease.md` (passes the lease at attempt start), `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` (eligibility, timeout classification, failure routing, in the same functions), and `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` (pending-call detection at turn entry): sequencing; this document lands first of the engine edits, the others rebase.
- Owner decision (2026-10-30): resume contract is `pending` and `failed` claimable.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `StageAlreadyRunningError` and `TaskTransitionError` (row 02 document), `max_attempt_number` and `AttemptRecord.attempt_number` (rows 04 and 01 documents), `complete_stage_attempt` (row 05 document), `claim_task` on `StateStore` (row 06 document).

## Design decisions

- `run()` claims the task with `StateStore.claim_task` before the `try` block, so a rejected claim (`running`, `completed`, `halted`) raises `TaskTransitionError` without touching status; later status writes use the validated `update_task_status`.
- The retry loop takes the attempt number from the persisted `AttemptRecord` returned by `begin_stage_if_new`, and checks the budget against `max_attempt_number` before starting a new attempt, so a restart cannot reset it.
- `StageAlreadyRunningError` is a conflict, not a stage failure: it is not retried.

## Alternatives considered

- Keep the in-memory counter and seed it from the database: rejected, two sources of truth.

## Implementation

### Target file

`scripts/agent/workflow/workflow_engine.py`

### Procedure

1. In `run()` (`:108`), replace the unconditional `update_task_status(task_id, "running")` (`:121`) with `claim_task`; keep the `halted`, `failed`, and `completed` writes on their existing branches.
2. In `_run_stage_with_retry` (`:134`), remove the local `attempt = 0` counter (`:148`); before each attempt compare `max_attempt_number` with `policy.max_attempts` and raise `WorkflowHaltError` when exhausted; after a failure, halt when the attempt's persisted number has reached `policy.max_attempts`.
3. In `_run_stage` (`:188`), drop the `attempt` parameter and the in-memory `event_id` (`:208`); call `begin_stage_if_new` with `(db, task_id, stage_id, workflow_id)`; on a returned record keep its persisted `attempt_number` in the span attributes (`workflow.attempt`, `retry.attempt`) and in an engine attribute behind a read-only `current_attempt_number` (new) property.
4. On success call `complete_stage_attempt` instead of `finish_attempt("completed")`, then `record_artifact` with the persisted `attempt_number`; on timeout or exception keep `finish_attempt(..., "failed", ...)`.
5. Let `StageAlreadyRunningError` propagate without retry.

### Method

- `begin_stage_if_new` returns `None` only for a stage already completed; log the skip as before.
- Non-retryable stages (`plan`, `verify`) still run once; their attempt number is also persisted.

### Details

- Keep the existing `except WorkflowTimeoutError: raise` ordering; timeout semantics are changed by the retry Plan, not here.
- The module is 9644 B; run `tools/check_module_size.py` after the edit (limit 20480 B).

## Compatibility considerations

- `_run_stage` loses its `attempt` argument (private); tests in `tests/agent/workflow/test_workflow_engine.py` (54 references to `WorkflowEngine` in 3 files) assume in-memory numbering and are updated in their row.
- Resume now depends on the claim contract: tasks in `running`, `completed`, or `halted` are rejected.

## Security considerations

- N/A: no external input.

## Rollback considerations

- Revert the commit together with the schema and attempt-lifecycle rows; no data change of its own.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py tests/agent/workflow/test_workflow_recovery.py tests/agent/test_orchestrator.py -v`
- `uv run ruff format scripts/agent/workflow/workflow_engine.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`

## Completion criteria

- A restarted engine continues attempt numbering from the persisted maximum and does not exceed `max_attempts`.
- Resuming a `completed`, `running`, or `halted` task is rejected; `pending` and `failed` are claimed.
- `current_attempt_number` (new) returns the persisted number of the attempt in progress.

## Out of Scope

- Retry eligibility, timeout classification, failure routing, lease passing (other Plans), adapter and audit wiring (their rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Claim in `run()`; persisted attempt numbers and budget; `current_attempt_number` (new); ledger completion | Pending | — | — | Plan Phase 4; gated on Phases 2 and 3 Blocked: schema row (attempts.attempt_number) and dbmig001 Phase 3 not landed Gated: after schema documents 20261030-125334_10, _22, _26 are executed (Plan Phase 2) |
| 2 | Add or update tests per Validation plan | Pending | — | — | Test rows' documents |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-007 (claim and persisted budget), REQ-009 (attempt number exposed for correlation)
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/agent/workflow/workflow_engine.py