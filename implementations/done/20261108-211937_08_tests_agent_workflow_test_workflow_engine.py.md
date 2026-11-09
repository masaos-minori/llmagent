## Goal
Rename the retry-policy fixture key in `tests/agent/workflow/test_workflow_engine.py` and add the two behavior tests that pin the engine changes: the missing-stage typed error (`REQ-002`) and the constant retry wait (`REQ-004`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 8 only: `tests/agent/workflow/test_workflow_engine.py`.

## Assumptions
- Landing order: after procedure 02 (engine) and procedure 03 (models) — the new tests import `WorkflowStageNotFoundError` and construct `RetryPolicy` with the renamed kwarg.
- Sibling pending procedures on the same file (`implementations/20261108-170505_06_...md` and `implementations/20261108-175155_07_...md`, attempt-row/retarget edits) are text-anchored and disjoint; re-anchor the insertion point (end of `class TestWorkflowEngineRetry`) at execution time if either landed first (plan Related Documents row).
- Occurrence census re-verified at HEAD `e4b47f11e` (the original 18-site list drifted): 19 lines carry `backoff_sec` (helper def L43, `RetryPolicy(...)` kwarg L49, fixture sites L177, L205, L221, L244, L280, L319, L351, L378, L403, L424, L455, L457, L618, L639, L660, L679, and the wfaudit015 `TestEngineFacadeRouting` fixture L778); rename every occurrence remaining at execution time.
- The attempt-row counting helper in this file is `_attempt_count(db, task_id, stage_id)` (L129); there is no `count_attempts` helper (verified at HEAD `e4b47f11e`).

## Design decisions
- `_make_wdef(max_attempts: int = 3, backoff_sec: int = 0)` -> `_make_wdef(max_attempts: int = 3, retry_wait_sec: int = 0)` with the inner `RetryPolicy(max_attempts=max_attempts, retry_wait_sec=retry_wait_sec)`; all keyword call sites follow mechanically.
- The missing-stage test probes `engine._run_stage_with_retry(task, "nonexistent", _noop)` on a `_make_wdef()` definition (which has only `plan`/`execute`/`verify`): the None-stage gate routes to `_run_stage`, which now raises; `_attempt_count` proves no attempt row was created. Import `WorkflowStageNotFoundError` in the file's `from agent.workflow.workflow_engine import (...)` block.
- The constant-wait test patches `agent.workflow.workflow_engine.asyncio.sleep` (the file's existing idiom at the terminal-kind test): `max_attempts=3`, `retry_wait_sec=2` distinguishes constant from doubling — sleeps must be exactly `[2, 2]` (one sleep per retried attempt), not `[2, 4]`.

## Alternatives considered
- Drive the missing-stage test through `engine.run`: rejected — `run` hardcodes the three shipped stage ids, so only the private entry point can present an unknown stage id, matching how the contract is defined.
- Assert only sleep call counts (not values): rejected — the value sequence is what pins `REQ-004` numeric identity.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py`

### Procedure
File-wide key rename, then append two tests to `class TestWorkflowEngineRetry`.

### Method
1. Rename all `backoff_sec` occurrences per the Assumptions census (helper parameter, `RetryPolicy` kwarg at L49, the standalone `RetryPolicy(max_attempts=1, backoff_sec=0)` at L244 and `retry_policy=RetryPolicy(max_attempts=3, backoff_sec=0)` in `TestEngineFacadeRouting` at L778, and every `_make_wdef(..., backoff_sec=...)` call site).
2. Add `WorkflowStageNotFoundError` to the `from agent.workflow.workflow_engine import (...)` block (alphabetical position after `WorkflowStageFailure`).
3. Append at the end of `class TestWorkflowEngineRetry`:
   - `test_unknown_stage_raises_workflow_stage_not_found_error` (new), async, `(self, store)`: build `_make_wdef()` + `create_task`, then `with pytest.raises(WorkflowStageNotFoundError): await engine._run_stage_with_retry(task, "nonexistent", _noop)`; then `assert _attempt_count(store._db, task.task_id, "nonexistent") == 0` (no attempt row, no lease for the rejected stage).
   - `test_retry_wait_constant_across_attempts` (new), async, `(self, store)`: `_make_wdef(max_attempts=3, retry_wait_sec=2)`; handler `always_fail` raising `RuntimeError`; `with patch("agent.workflow.workflow_engine.asyncio.sleep") as mock_sleep:` and `pytest.raises(WorkflowHaltError)` around `engine.run(task, _noop, always_fail, _noop)`; `assert [c.args[0] for c in mock_sleep.await_args_list] == [2, 2]`.

4. Step 3a/4 finding (implementation pass 2026-11-09): `TestEngineFacadeRouting._single_stage_plan_wdef` defines only the `plan` stage, so `engine.run` reached `execute`/`verify` through the removed `else 60` fallback; after procedure 02 both facade-routing tests raise `WorkflowStageNotFoundError`. The helper is renamed `_routing_wdef` and defines `plan`/`execute`/`verify` (both call sites updated); assertions are unchanged. This also corrects the Plan Assumption that the fallback was reachable only through a direct unknown-stage call.

### Details
- No changes to lease-horizon assertions (`_lease_delta_sec == 35`) or attempt-kind assertions; they already encode unchanged behavior.

## Compatibility considerations
- Between procedure landings the file must not be run standalone before rows 2-4/6 (renamed kwarg/key); the plan's Phase 3 chain lands them together.

## Security considerations
- No change.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_engine.py -q` green after rows 2-4 and 6 land; the two new tests fail on HEAD (silent 60-second fallback, no typed error).
- Full `uv run pytest tests/ -q` and lint/type gates per `rules/toolchain.md` at unit completion.

## Completion criteria
- `REQ-002`/`REQ-003`/`REQ-004`/`REQ-005` for this file: no `backoff_sec` token remains; both new tests green.

## Out of Scope
- Engine facade retarget edits (owned by `170505_06`/`175155_07`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-092921 | 20261109-092921 | Changed: test_workflow_engine.py; finding: TestEngineFacadeRouting helper renamed _routing_wdef with all three stages |
| 2 | Add or update tests per Validation plan | Completed | 20261109-092921 | 20261109-092921 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-092921 | 20261109-092921 | Full suite 11904 passed; 3 pre-existing env errors in test_workflow_status_vocabulary.py (/tmp/opencode missing); diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-092921 | 20261109-092921 | N/A: docs covered by procedures 13-14 |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: tests/agent/workflow/test_workflow_engine.py
