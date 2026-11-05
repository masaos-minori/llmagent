## Goal
- Migrate the test patches of `agent.workflow_engine_adapter.create_task` and `get_task_by_id` in `tests/agent/test_orchestrator.py` to the `StateStore` seam, without changing what any test asserts (`REQ-004`, `REQ-006`).

## Scope
**Release unit**: adapter-seam
- Edits only `tests/agent/test_orchestrator.py`. It lands together with procedure `_02_scripts_agent_workflow_engine_adapter.py.md`.

## Assumptions
- After procedure `_02` the adapter calls `store.create_task(...)` and `store.get_task_by_id(...)` on the store passed to `execute_turn` (the orchestrator's store) or, in `_init_workflow_task` with no store, on `StateStore()`.
- Overlap with `plans/20261104-115736_partialcount001_partial-completion-counter-dead.md` on this file is compatible: that Plan edits the partial-completion assertions; this procedure edits the patch sites and the module fixture. If either lands first, rebase the other.
- Tests that set `orch._workflow_adapter._workflow_engine._wdef = ...` need no change.

## Design decisions
- Three patterns cover every site: (A) the module autouse fixture hands out a mock task through the patched store class; (B) tests that restored the real `create_task` simply drop that line, because they already replace `agent.orchestrator.StateStore` with a real store subclass; (C) resume tests pass a mock store to `_init_workflow_task(..., store=...)`.
- Assertions stay as written: `assert_not_called` on create moves from the patched function to `store.create_task`.

## Alternatives considered
- Keep a module-level `create_task` name in the adapter solely so the old patches resolve: rejected because it preserves the bypass the Plan removes.

## Implementation
### Target file
`tests/agent/test_orchestrator.py`

### Procedure
1. Pattern A, the autouse fixture `_patch_workflow_loader`: bind the existing `patch("agent.orchestrator.StateStore")` in its `with (...)` tuple `as state_store_cls`, delete the `patch("agent.workflow_engine_adapter.create_task", return_value=mock_task)` entry, and before `yield mock_loader` set `state_store_cls.return_value.create_task.return_value = mock_task`.
2. Pattern B, every `monkeypatch.setattr("agent.workflow_engine_adapter.create_task", create_task)` statement (in `TestHandleTurnInvokesWorkflowEngine`, `TestExecuteStageRetryRunsTurnEntryOnce`, `TestEntryWorkFailureIsNotRetried`, `TestEntryWorkOutsideStageTimeout`, the shared helper near them, and `_status_harness`): delete the statement. Where a docstring or comment says the real `create_task` is restored, reword it to say the real store is used.
3. Remove the now-unused module import `from agent.workflow.task_ops import create_task` after step 2 (ruff F401), and confirm with `rg "\bcreate_task\b" tests/agent/test_orchestrator.py` that remaining hits are `asyncio.create_task` or comments.
4. Pattern C, the three tests of `TestInitWorkflowTaskResumeReuse` (`test_resume_reuses_existing_task_not_creates_duplicate`, `test_resume_does_not_call_audit_workflow_start_for_existing_task`, `test_resume_rejects_halted_task`): build `store = MagicMock()`, set `store.get_task_by_id.return_value` to the existing or halted task, drop the two `patch("agent.workflow_engine_adapter.get_task_by_id" / "create_task")` entries, keep `patch("agent.orchestrator.StateStore")` and `patch("agent.workflow_engine_adapter.audit_workflow_start")`, pass `store=store` to `_init_workflow_task(...)`, and replace `mock_create.assert_not_called()` with `store.create_task.assert_not_called()`.

### Method
- Do not change test names, docstrings' claims, expected values, or the order of operations in any test.
- For pattern B confirm in each test that `agent.orchestrator.StateStore` is replaced by a real `StateStore` subclass (`TempStateStore` or the probe store) before the orchestrator is built; if one is not, report it instead of editing around it.
- Keep the `_engine_run`-style helper inside the fixture unchanged.

### Details
- After the edit `rg "workflow_engine_adapter\.(create_task|get_task_by_id)" tests/agent/test_orchestrator.py` must find nothing.
- `_ProbeStateStore` records `update_task_status` calls only; `create_task` goes through `StateStore.create_task`, so `store.calls` expectations such as `["running", "completed"]` are unchanged.

## Compatibility considerations
- Test-only. The fixture still yields the same mock task (`test-task-id`, `test-workflow-id`) to full-turn tests through the patched store.

## Security considerations
- N/A: test-only.

## Rollback considerations
- Revert with procedure `_02` (one release unit).

## Validation plan
- `uv run pytest tests/agent/test_orchestrator.py` passes with every pre-existing assertion unchanged; run it once before editing to record the baseline counts.
- `uv run ruff check tests/agent/test_orchestrator.py`; `uv run python tools/check_mock_patch_targets.py`.

## Completion criteria
- No patch or setattr of the removed adapter names remains, no unused import, and the suite result matches the baseline.

## Out of Scope
- The partial-completion assertions (partialcount001 Plan), any production code, and the integration suite (`_05`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the baseline result of `tests/agent/test_orchestrator.py` | Pending | — | — | |
| 2 | Migrate the fixture (A), delete the restore lines (B), and rewrite the resume tests (C) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) after procedure `_02` is applied | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (migrate patch sites), `REQ-006` (assertions unchanged)
- **Source issue**: issues/20261103-134147_wfreview004_workflow-adapter-and-engine-private-attribute-access.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-085959_wfreview004_workflow-adapter-and-engine-private-attribute-access.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-092748
- **Related target files**: `tests/agent/test_orchestrator.py`
