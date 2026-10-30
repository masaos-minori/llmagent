## Goal

Give `scripts/agent/workflow/workflow_engine.py` per-kind retry eligibility, a correct stage-deadline classification, and one routing path for stage failures (`REQ-002`, deadline versus inner timeout; `REQ-003`, retry semantics per kind; `REQ-005`, LLM-level failure results enter the engine; `REQ-006`, side-effect suppression in the engine; `REQ-007`, stable attempt error kinds).

## Scope

- Modify only `scripts/agent/workflow/workflow_engine.py`.
- Persisted attempt numbering and the task claim are the wfrecovery001 Plan's work in the same functions.

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): this row is Plan Phase 2 and follows `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Phase 4 (its row 07 document makes the retry loop use persisted attempt numbers); it also needs row 02 (`RetryPolicy.retry_on`) of this Plan. Execution order follows the Plan's phases, not `seq` (row 02 and 03 and 04, Phase 1, run first).
- Plan overlap judgments (Step 8b): `workflow_engine.py` is also a target of the wfrecovery001 Plan, `plans/20261030-114516_wflease001_stale-attempt-lease.md` (passes the lease at attempt start), and `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` (turn-entry pending-call detection): sequencing dependency; the designs do not contradict and the later change rebases.
- Owner decisions (2026-10-30): timeouts and LLM-level failure results are not retried by default (`retry_on` defaults to exception only); the defaults preserve today's behavior.
- Verified in Step 2 of the Plan (Python 3.13.5): an inner `TimeoutError` raised by the stage callback is currently caught by `except TimeoutError` and labeled a stage timeout; `asyncio.timeout()` reports `expired()` false for it and true when the deadline fires.
- Names created by earlier rows or Plans, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `retry_on` and `RETRY_ON_KINDS` (row 02 document), `side_effects_started` (row 06 document), the persisted attempt number and `current_attempt_number` (wfrecovery001 Plan row 07 document).

## Design decisions

- Define `StageFailure` (new) in this module beside `WorkflowHaltError` and `WorkflowTimeoutError`; it carries the result `error_kind`, the answer, the partial flag, and a `side_effects` (new) flag, so the adapter (row 05) can raise it and the engine can route it.
- Classify each failed attempt: `timeout` (deadline expired), `llm_failure` (new) (a `StageFailure` (new)), otherwise `exception`; persist exactly these in `attempts.error_kind` (`_ERROR_KIND_LLM_FAILURE` (new) joins the two existing constants), never the outward turn kinds.
- Retry only when the kind is in `policy.retry_on` and the failure did not follow a side effect; a failure that is ineligible because of a side effect ends as `WorkflowHaltError`; an ineligible kind ends as today (timeout raises `WorkflowTimeoutError`, others re-raise the original exception so the task is `failed`).
- Every failed attempt consumes one unit of `max_attempts`; exhaustion of an eligible kind raises `WorkflowHaltError` as now.

## Alternatives considered

- Compare elapsed time to detect a deadline: rejected, `asyncio.timeout().expired()` answers directly without clocks.
- Retry after side effects when the tool is idempotent: rejected for now, the replay protocol of the tool-call idempotency Plan does not exist yet.

## Implementation

### Target file

`scripts/agent/workflow/workflow_engine.py`

### Procedure

1. Add `StageFailure` (new) and the `_ERROR_KIND_LLM_FAILURE` (new) constant next to the existing exception classes and error-kind constants.
2. In `_run_stage` (`:188`), replace `asyncio.wait_for(fn(), timeout=timeout)` (`:224`) with an `asyncio.timeout(timeout)` block; on `TimeoutError` branch on the block's `expired()`: true takes the existing timeout path (attempt `failed` with kind `timeout`, raise `WorkflowTimeoutError`); false is handled as an ordinary exception (kind `exception`).
3. In the exception handler, record kind `llm_failure` (new) when the exception is a `StageFailure` (new) (keeping the result kind in `error_detail`), otherwise `exception`.
4. In `_run_stage_with_retry` (`:134`), decide eligibility after each failure: kind from the raised exception, membership in `policy.retry_on`, and the exception's side-effect flag; ineligible failures leave the loop as described in Design decisions; remove the unconditional `except WorkflowTimeoutError: raise` shortcut in favor of the same decision.

### Method

- The backoff, retry span attributes, and halt message stay as they are; add the failure kind to the retry span (`retry.error_type` already records the exception class).
- A `WorkflowTimeoutError` from an eligible `timeout` kind consumes the budget like any other kind; its exhaustion raises `WorkflowHaltError`.

### Details

- Keep `run()` unchanged: a `StageFailure` (new) falls into the generic `except Exception` branch and the task is written `failed` once.
- Non-retryable stages (`plan`, `verify`) still run once and re-raise their original exception.
- Module size is 9644 B before this change; run `tools/check_module_size.py` (limit 20480 B).

## Compatibility considerations

- With the shipped configuration (`retry_on` defaults to exception only) retry behavior is unchanged for timeouts and exceptions; the new side-effect rule is an intended behavior change: an exception after a non-READ tool call is no longer retried.
- Existing exception class names and `attempts.error_kind` values `timeout` and `exception` are kept; `llm_failure` (new) is added.

## Security considerations

- The side-effect rule prevents re-running non-READ tool calls (including unclassified ones) after a partial failure.

## Rollback considerations

- N/A: revert the commit (persisted `llm_failure` (new) rows remain valid text).

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v` (timeout then success when configured, exhaustion for each kind, non-retryable kind, inner `TimeoutError`, `StageFailure` (new), side-effect suppression)
- `uv run ruff format scripts/agent/workflow/workflow_engine.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`

## Completion criteria

- With the shipped configuration a timed-out execute stage is not retried and an exception is retried up to `max_attempts`; with `timeout` in `retry_on` the timeout consumes the budget identically.
- An inner `TimeoutError` is recorded as kind `exception`; a deadline expiry as `timeout`.
- A failure after a non-READ tool call is terminal (`WorkflowHaltError`) regardless of `retry_on`.

## Out of Scope

- Persisted numbering, the task claim, the lease (other Plans); the adapter's use of `StageFailure` (new) (row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `StageFailure` (new) and the kind constant; deadline classification; eligibility and side-effect rule | Pending | — | — | Plan Phase 2; after wfrecovery001 Phase 4 and row 02 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Row 08 document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (deadline versus inner timeout), REQ-003 (retry semantics), REQ-005 (stage failures), REQ-006 (side-effect suppression), REQ-007 (stable attempt kinds)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: scripts/agent/workflow/workflow_engine.py
