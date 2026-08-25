## Goal

`REQ-001`: add a test proving ADR-001 INV-03 ("execute success is verified
independently from verify success") for the previously-uncovered side — an
execute-success-then-verify-failure turn must leave the task's status as `"failed"`,
not `"completed"`.

## Scope

- **In-Scope**: add one new test case to `tests/agent/workflow/test_workflow_engine.py`
  asserting `task.status == "failed"` when `execute_fn` succeeds and `verify_fn` raises.
- **Out-of-Scope**: `scripts/agent/workflow/workflow_engine.py` — its `except Exception`
  handler (lines 153-155) already sets `"failed"` before re-raising for any stage
  failure, including verify; confirmed correct, no code change needed. The issue's
  Recommended Action (2) ("execute fails → retry succeeds → completed") — already
  covered by the existing `test_retry_succeeds_on_second_attempt`
  (`tests/agent/workflow/test_workflow_engine.py:125-144`).

## Assumptions

- Confirmed via `rg '\.status =='  tests/agent/workflow/test_workflow_engine.py` that
  the file's six existing status assertions (lines 109, 144, 161, 325, 389, 394) check
  `"completed"`, `"halted"`, `"expired"`, `"pending"` — none check `"failed"`.
- Confirmed via Read (`tests/agent/workflow/test_workflow_engine.py:447-465`,
  `test_non_retryable_verify_stage_does_not_retry_on_failure`) that this existing test
  only asserts `pytest.raises(RuntimeError, ...)` and the retry-attempt count
  (`count_attempts(...) == 1`) — it does not fetch or assert the task's `status` field at
  all.
- Confirmed via Read (`scripts/agent/workflow/workflow_engine.py:130-157`,
  `WorkflowEngine.run()`) that any exception raised by `plan_fn`/`execute_fn`/`verify_fn`
  (after exhausting retries for a retryable stage, or immediately for a non-retryable
  one) is caught by the trailing `except Exception:` clause, which calls
  `self._store.update_task_status(task.task_id, "failed")` before re-raising — this
  applies uniformly regardless of which of the three stages raised, so a verify-stage
  failure after execute success is not special-cased differently from any other stage
  failure in the implementation. This confirms the source Plan's Background claim.
- Confirmed via Read (`tests/agent/workflow/test_workflow_engine.py:1-45`) that
  `create_task`, `get_task_by_idempotency_key`, `_make_wdef`, `_noop`,
  `request_approval`/`resolve_approval` are already imported/defined at module level and
  usable directly by a new test without any new import.

## Design decisions

- Add the new test to the `verify`-related test grouping in the file (adjacent to
  `test_non_retryable_verify_stage_does_not_retry_on_failure`, per the source Plan's
  Design section), rather than creating a new test class, to keep related verify-failure
  coverage co-located.
- Use `_noop` for `plan_fn`/`execute_fn` and a small local async function raising
  `RuntimeError` for `verify_fn`, mirroring the existing
  `test_non_retryable_verify_stage_does_not_retry_on_failure` pattern exactly (same
  `_make_wdef()` call, same `create_task()` call), so the new test reads as a direct
  sibling of the existing one plus the status assertion it was missing.
- Fetch the task via `get_task_by_idempotency_key(store._db, "s:1")` after the
  `pytest.raises` block (same idempotency-key pattern as
  `test_retry_succeeds_on_second_attempt`, line ~141) and assert `found.status ==
  "failed"`.

## Alternatives considered

- Extending `test_non_retryable_verify_stage_does_not_retry_on_failure` in place with an
  added status assertion, instead of adding a new test: rejected — the source Plan's
  Implementation intent explicitly allows either approach ("既存のテストを拡張するか、
  新規テストケースを追加し"); adding a new, separately-named test
  (`test_execute_success_verify_failure_marks_task_failed`) keeps the existing test's
  single stated purpose (no-retry-on-non-retryable-stage) undiluted and gives the new
  INV-03 assertion its own clearly-named regression target, per SKILL.md's general
  preference for minimal, single-purpose test additions.

## Implementation

### Target file
`tests/agent/workflow/test_workflow_engine.py`

### Procedure
1. Add a new test method `test_execute_success_verify_failure_marks_task_failed` in the
   same test class as `test_non_retryable_verify_stage_does_not_retry_on_failure`
   (confirm the enclosing class name via Read before inserting — likely
   `TestWorkflowEngineRetry` or a sibling verify-focused class; place immediately after
   `test_non_retryable_verify_stage_does_not_retry_on_failure` for locality).
2. Inside the test: `wdef = _make_wdef(max_attempts=3, backoff_sec=0)`; `task =
   create_task(store._db, "s", 1, wdef.version, "wf-test")`; `engine =
   WorkflowEngine(wdef, store)`.
3. Define `async def failing_verify() -> str | None: raise RuntimeError("verify always
   fails")`.
4. `with pytest.raises(RuntimeError, match="verify always fails"): await engine.run(task,
   _noop, _noop, failing_verify)`.
5. `found = get_task_by_idempotency_key(store._db, "s:1"); assert found is not None;
   assert found.status == "failed"`.

### Method
Single new test method added by direct pattern-matching against two existing tests in
the same file (`test_non_retryable_verify_stage_does_not_retry_on_failure` for the
verify-failure setup, `test_retry_succeeds_on_second_attempt` for the
idempotency-key task fetch).

### Details
- Per the source Plan's AC-01, manually verify the new test actually detects a
  regression: temporarily change `WorkflowEngine.run()`'s final line to set
  `"completed"` unconditionally (or otherwise weaken the `except Exception` handler) and
  confirm the new test goes red, then revert the temporary change — do not leave this
  temporary change in the codebase.

## Compatibility considerations

N/A: test-only addition, no production code or test fixture signature changes.

## Security considerations

N/A: no security-relevant logic added.

## Rollback considerations

- Remove the single new test method; no other state depends on it.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/workflow/test_workflow_engine.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/agent/workflow/test_workflow_engine.py -v` | New test passes; all existing tests in the file remain green (no regression) |
| `scripts/agent/workflow/workflow_engine.py` | Manual regression check | Temporarily weaken the `except Exception` handler, confirm the new test fails, then revert | New test goes red under the weakened handler, confirming it actually detects the regression it targets (source Plan AC-01) |

## Completion criteria

- A new test in `tests/agent/workflow/test_workflow_engine.py` asserts
  `task.status == "failed"` for an execute-success/verify-failure turn.
- The new test passes under the current `WorkflowEngine.run()` implementation.
- The new test is manually confirmed to fail under a deliberately weakened
  implementation (per AC-01), and that temporary weakening is reverted before this
  change is finalized.
- No existing test in the file regresses.

## Out of scope

- `scripts/agent/workflow/workflow_engine.py` — no code change (see Scope).
- A test for the issue's Recommended Action (2) — already covered by
  `test_retry_succeeds_on_second_attempt`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_execute_success_verify_failure_marks_task_failed` | Pending | — | — | |
| 2 | Manually confirm the new test detects the targeted regression (AC-01), then revert the temporary weakening | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) scoped to this test file | Pending | — | — | |
| 4 | Documentation update | N/A | — | — | Not in scope for this file |

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
- **Requirement ID**: `REQ-001` — add execute-success/verify-failure → `"failed"` status test
- **Source issue**: `issues/20260822_wkfl_inv03_test_gap_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133009_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-174354
- **Related target files**: `tests/agent/workflow/test_workflow_engine.py`
