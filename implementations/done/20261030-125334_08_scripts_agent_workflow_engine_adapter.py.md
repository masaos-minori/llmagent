## Goal

Make `scripts/agent/workflow_engine_adapter.py` use the task-resume contract from `task_ops` instead of its own `halted`-only guard, and pass the persisted attempt number to the `stage_completed` audit event (`REQ-007`, one resume contract; `REQ-009`, attempt number for correlation).

## Scope

- Modify only `scripts/agent/workflow_engine_adapter.py`.
- Failure return values, stage-failure raising, and status-write limits belong to the retry Plan.

## Assumptions

- Plan Dependencies (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Scope): Plan Phase 4, after rows 03 (resume check), 07 (`current_attempt_number`), and 09 (audit parameter); it MUST NOT run before the schema and attempt-lifecycle phases.
- Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `workflow_engine_adapter.py` is also a target of `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` (failure return, stage failure, status writes): sequencing dependency, different methods of `execute_turn` and `_run_execute_stage`; the later change rebases.
- `Orchestrator._execute_turn` never passes `existing_task_id`, so the resume guard is reachable only through that unused parameter (checked in Step 3 of the Plan); the existing test `tests/agent/test_orchestrator.py:2095-2118` expects a `RuntimeError` matching `halted`.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `assert_resumable` (row 03 document), `current_attempt_number` on the engine (row 07 document).

## Design decisions

- The adapter delegates the resume decision to `assert_resumable` so the rule lives only in `task_ops`; the "task not found" `RuntimeError` stays as is.
- `audit_stage_completed` receives the engine's `current_attempt_number`; the adapter already holds the engine (`self._workflow_engine`).

## Alternatives considered

- Pass the attempt number through `ctx.workflow`: rejected, it adds a context field and a writer for one reader.

## Implementation

### Target file

`scripts/agent/workflow_engine_adapter.py`

### Procedure

1. In `_init_workflow_task` (`:249` region, the resume branch at `:273-283`), replace the explicit `if _fetched.status == "halted"` check with a call to `assert_resumable` on the fetched record.
2. In `_run_execute_stage` (`:327-375`), pass `attempt_number` taken from the engine's `current_attempt_number` to `audit_stage_completed`.
3. Add the `task_ops` import used by step 1 next to the existing `create_task, get_task_by_id` import (`:38`).

### Method

- Keep the `pending -> halted` write on turn-entry preparation failure (`:204`) and the cancellation write; both edges are in the matrix.
- `_record_exit_status` already catches all exceptions around the status write, so a typed transition error there is logged, not raised.

### Details

- Line numbers are from the pre-change file; locate by symbol.
- Module size is 15702 B (limit 20480 B); this change adds a few lines; check with `tools/check_module_size.py`.

## Compatibility considerations

- The halted-resume `RuntimeError` message must still match `halted` (the error type is a `RuntimeError` subclass whose message names the status).
- A `completed` or `running` task passed as `existing_task_id` is now rejected instead of silently accepted (intended).

## Security considerations

- N/A: no new input boundary.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py -v`
- `uv run ruff format scripts/agent/workflow_engine_adapter.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`

## Completion criteria

- Resume of `halted`, `completed`, and `running` tasks raises through `assert_resumable`; `failed` and `pending` proceed.
- The `stage_completed` audit event carries the persisted attempt number.

## Out of Scope

- Typed failure results, stage failures, status-write changes (retry Plan); the audit function itself (row 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delegate the resume guard; pass the attempt number to the audit call | Completed | 20261030-183035 | 20261030-183035 | Plan Phase 4; gated on Phases 2 and 3 Blocked: schema row (attempts.attempt_number) and dbmig001 Phase 3 not landed Gated: after schema documents 20261030-125334_10, _22, _26 are executed (Plan Phase 2) done in batch |
| 2 | Add or update tests per Validation plan | Completed | 20261030-183035 | 20261030-183035 | Test rows' documents done in batch |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-183035 | 20261030-183035 | executed in the Plan Phase 2-4 single batch; full suite 10516 passed, 1 unrelated flaky eventbus 503 (passes alone); production workflow.sqlite mtime unchanged |

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
- **Requirement ID**: REQ-007 (one resume contract), REQ-009 (attempt number in the audit event)
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/agent/workflow_engine_adapter.py