## Goal

Pin the retry and classification behavior of the workflow engine in `tests/agent/workflow/test_workflow_engine.py` (`REQ-002`, deadline versus inner timeout; `REQ-003`, retry semantics per kind and the shipped configuration; `REQ-005`, stage failures; `REQ-006`, side-effect suppression; `REQ-009`, tests).

## Scope

- Modify only `tests/agent/workflow/test_workflow_engine.py`.

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 2 tests, written with the engine row (row 01) and after the wfrecovery001 Plan's engine tests, which change numbering assertions in the same file. Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `test_workflow_engine.py` is also a target of the wfrecovery001, wflease001, wftaskapi001, and toolexec001 Plans: compatible, additive tests in different classes.
- Existing structure: `TestWorkflowEngineTimeout::test_timeout_raises_workflow_timeout_error` (`:161-185`) accepts either `WorkflowHaltError` or `WorkflowTimeoutError`, so it does not pin behavior.
- The stage definitions in this file use `retryable=True` for `execute` with small `timeout_sec`; helpers `_noop` and `create_task` exist (`:39-41`, `:172`).
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `StageFailure` (row 01 document), `retry_on` (row 02 document).

## Design decisions

- Rewrite the existing timeout test to assert `WorkflowTimeoutError` specifically with the default policy (timeout not retried: exactly one attempt row).
- Add focused tests rather than parametrizing the existing classes, so they can be written failing-first.

## Alternatives considered

- N/A: test row; the cases come from the Plan's Tests section.

## Implementation

### Target file

`tests/agent/workflow/test_workflow_engine.py`

### Procedure

1. Rewrite `test_timeout_raises_workflow_timeout_error` to assert `WorkflowTimeoutError` and one attempt row for the default policy.
2. Add: timeout then success when `retry_on` includes `timeout`; timeout exhaustion consuming the budget; exception exhaustion (existing behavior pinned); a non-retryable kind ending without retry; an inner `TimeoutError` recorded as kind `exception` and retried by default; a `StageFailure` recorded as kind llm_failure and terminal by default; the same retried when llm_failure is in `retry_on`.
3. Add: a failure with the side-effect flag set is terminal (`WorkflowHaltError`) even for an eligible kind, and a failure without the flag retries.

### Method

- Build `WorkflowDef` objects with `RetryPolicy(max_attempts=..., backoff_sec=0, retry_on=...)` and a short `execute` timeout; callbacks are async functions that raise, sleep past the deadline, or raise `StageFailure`.
- Assert persisted attempt rows through `count_attempts` and a direct `SELECT` on `attempts.error_kind`.

### Details

- Write each new test first and confirm it fails against the current engine before the engine row is implemented.
- Keep timeouts at about one second at most to keep the suite fast.

## Compatibility considerations

- N/A: tests only.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v`
- `uv run ruff format tests/agent/workflow/test_workflow_engine.py`, `uv run ruff check tests/agent/workflow/test_workflow_engine.py`

## Completion criteria

- Each case above has a test; the new tests fail before the engine row and pass after it; the rewritten timeout test pins `WorkflowTimeoutError`.

## Out of Scope

- Orchestrator-level assertions (row 10), loader tests (row 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add and rewrite the engine tests | Pending | — | — | Plan Phase 2 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-005, REQ-006, REQ-009 (engine tests)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: tests/agent/workflow/test_workflow_engine.py
