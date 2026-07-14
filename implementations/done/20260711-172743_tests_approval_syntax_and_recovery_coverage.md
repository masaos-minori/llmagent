# Implementation: Tests for Approval Syntax Fixes, Startup Recovery, and Approval Gate

## Goal

Add/confirm test coverage for: (1) the corrected `/approve`/`/reject` runtime warning messages and CLI syntax, (2) the startup-recovery fix restoring both `ctx.turn.pending_approval_id` and `ctx.turn.pending_approval_task_id`, and (3) the workflow approval gate blocking `verify` until resolved. Where existing tests already cover a scenario, update assertions in place rather than adding duplicates; only add new tests for genuine gaps.

## Scope

**In scope:**
- `tests/test_startup.py`: `TestStartupOrchestratorRecoverPendingApprovals` — extend `test_startup_recovery_restores_pending_approval` (or add a new assertion/test) to also assert `ctx.turn.pending_approval_task_id == "task-456"` after recovery, matching the fix in `startup.py`'s `_recover_pending_approvals()`.
- `tests/test_orchestrator.py`: `TestApprovalPendingGuard` — confirm/extend `test_handle_turn_blocked_when_approval_pending` to assert the corrected error message contains the actual approval ID, not just the literal substrings `/approve`/`/reject`.
- `tests/test_cmd_workflow_approval.py` and/or `tests/test_cmd_workflow.py`: confirm existing "no ID" error-path tests (`test_approve_single_pending_no_id_requires_id` and its `/reject` equivalent) still pass with the `/workflow status` line removed from the error message, and do not assert on the removed substring.
- `tests/test_workflow_engine.py`: confirm `TestWorkflowEngineApprovalGate` (`test_gate_always_raises_pending_on_new_task`, `test_approved_task_gate_passes`, `test_rejected_task_halts`, `test_resume_does_not_rerun_plan_or_execute`) already proves `verify` does not run until the `require_approval=True` gate is resolved; add a gap-filling test only if one of these does not already assert that `verify`/the post-gate stage is skipped/blocked pre-resolution.

**Out of scope:**
- Any production code change (this doc is test-planning only; actual test edits happen during implementation).
- New test files beyond the ones listed above unless a genuine gap is found that cannot be added to an existing file's class/module without breaking cohesion.
- Testing the doc-only fixes (docs are not executable; validated via `check_docs_consistency.py` and grep per the doc-fix implementation docs, not pytest).

## Assumptions

- Confirmed by direct read of `tests/test_startup.py:110-168`: `TestStartupOrchestratorRecoverPendingApprovals` currently asserts `ctx.workflow.approval_pending is True` and `ctx.turn.pending_approval_id == "approval-123"`, but does **not** assert on `ctx.turn.pending_approval_task_id` — this is the gap Phase 1's fix closes, and the gap this test-doc's Procedure step 1 closes.
- Confirmed by direct read of `tests/test_startup.py:139-168`: `test_startup_recovery_warning_contains_task_and_approval_id` already asserts both `task-456` and `approval-123` appear in the warning text — this test does NOT need new assertions for the message-syntax fix itself (it doesn't check for the literal `/approve`/`/reject` substrings), but should be re-run to confirm it still passes after the message-text edit.
- Confirmed by direct read of `tests/test_orchestrator.py:747-763`: `test_handle_turn_blocked_when_approval_pending` currently asserts only `"/approve" in str(err) or "/reject" in str(err)` — this passes both before and after the fix, so it does not by itself prove the approval_id is present. A stronger assertion (e.g. asserting the mocked `ctx.turn.pending_approval_id` value appears in `str(err)`) is needed to actually pin the fix.
- Confirmed by direct read of `tests/test_cmd_workflow_approval.py:151-160`: `test_approve_single_pending_no_id_requires_id` asserts `"Approval ID required" in errors[0]` only — it does not assert on `"/workflow status"`, so removing that line does not break this test; no change needed here beyond re-running to confirm.
- Confirmed by direct read of `tests/test_workflow_engine.py:232-274`: `TestWorkflowEngineApprovalGate` already fully exercises the `require_approval=True` gate lifecycle (pending → approved/rejected → resume), which is the scenario Phase 5's last bullet describes as "likely already covered." Treat as covered unless a specific missing assertion is found (e.g. no existing test explicitly proves the `verify` callback is never invoked pre-resolution — check `_noop` usage and add an assertion/spy if the current tests only check for the raised exception rather than a spy call count on the `verify` argument).

## Implementation

### Target file

`tests/test_startup.py`, `tests/test_orchestrator.py`, `tests/test_cmd_workflow_approval.py`, `tests/test_workflow_engine.py` (existing files — extend in place; no new file expected unless a gap surfaces during implementation)

### Procedure

1. **`tests/test_startup.py`**: In `test_startup_recovery_restores_pending_approval`, add:
   ```python
   assert ctx.turn.pending_approval_task_id == "task-456"
   ```
   after the existing `ctx.turn.pending_approval_id == "approval-123"` assertion.
2. **`tests/test_orchestrator.py`**: In `test_handle_turn_blocked_when_approval_pending`, set a known `ctx.turn.pending_approval_id` value on the mocked `ctx` before calling `handle_turn`, then strengthen the assertion to:
   ```python
   assert ctx.turn.pending_approval_id in str(err)
   ```
   in addition to (or replacing) the existing substring check, so the test actually fails if the approval_id is omitted from the message.
3. **`tests/test_cmd_workflow_approval.py`**: Re-run `test_approve_single_pending_no_id_requires_id` and its `/reject` counterpart (if present in `test_cmd_workflow.py`) after the `cmd_workflow.py` edit; no assertion change expected, but confirm no test anywhere asserts on the now-removed `"Use '/workflow status'"` substring (grep test files for `"workflow status"` first).
4. **`tests/test_workflow_engine.py`**: Review `TestWorkflowEngineApprovalGate` for a spy-based assertion that the `verify` callback (third positional arg to `engine.run(task, _noop, _noop, _noop)`) is never called before approval resolution. If none exists, add one new test using a `MagicMock`/counting function in place of the third `_noop` argument, asserting call count is 0 after `WorkflowPendingApprovalError` is raised and >0 only after `resolve_approval(..., "approved", ...)` + a follow-up `engine.run(...)` call.

### Method

Extend existing test classes/functions with additional assertions or one new test function per file; follow each file's existing fixture patterns (`store`, `workflow_db`, `_make_wdef`, `_make_ctx`/`_make_orchestrator`, `_make_mixin`) rather than introducing new fixtures.

### Details

- Do not remove or weaken any existing assertion — only add.
- Keep new/changed assertions specific (assert the actual ID value, not just a substring like `/approve`) so the tests would fail if the underlying fix regresses.
- Follow `rules/coding.md`: no bare `except`, no `print()`, English-only comments, `# noqa`/`# type: ignore` require inline justification if added (none expected for this test-only change).
- Confirm exact test filenames/line numbers again at implementation time — this doc's line numbers are best-effort from direct read during planning and may drift slightly if other concurrent test-file edits land first.

## Validation plan

Filtered from the plan's Validation plan table to the tests row:

| Check | Tool | Target |
|---|---|---|
| Tests | `uv run pytest tests/test_startup.py tests/test_startup_validation_pipeline.py -k "approval or recover" -v` | All pass, including new/updated assertions |
| Regression | `uv run pytest tests/ -k "workflow and (approve or reject or approval)" -q` | No new failures |
| Targeted | `uv run pytest tests/test_orchestrator.py -k "ApprovalPendingGuard" -v` | Passes with strengthened assertion |
| Targeted | `uv run pytest tests/test_workflow_engine.py -k "ApprovalGate" -v` | Passes, including any newly added verify-not-called test |
| Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | >= 90% on changed lines |
