## Goal
- Migrate the test patches of `agent.workflow_engine_adapter.create_task` and `get_task_by_id` in `tests/integration/test_orchestrator_integration.py` to the `StateStore` seam, without changing what any test asserts (`REQ-004`, `REQ-006`).

## Scope
**Release unit**: adapter-seam
- Edits only `tests/integration/test_orchestrator_integration.py`. It lands together with procedure `_02_scripts_agent_workflow_engine_adapter.py.md`.

## Assumptions
- The module autouse fixture already patches both `agent.orchestrator.StateStore` and `agent.workflow_engine_adapter.StateStore`; the adapter uses the orchestrator's store in `execute_turn` and its own `StateStore()` only in `_init_workflow_task` with no store.
- Full-turn tests pass the orchestrator's store, so its `get_task_by_id` and `create_task` are what the resume tests must configure.

## Design decisions
- Same three patterns as procedure `_04`: the autouse fixture hands out the mock task through the patched store classes; direct `_init_workflow_task` resume tests pass a mock store; `execute_turn` resume tests configure the store class they patch.
- Assertions stay as written.

## Alternatives considered
- Passing `store=` in every test: not possible for `execute_turn` tests, which use the orchestrator's own store, so those configure the patched class instead.

## Implementation
### Target file
`tests/integration/test_orchestrator_integration.py`

### Procedure
1. Autouse fixture `_patch_workflow_loader`: bind `patch("agent.orchestrator.StateStore")` and `patch("agent.workflow_engine_adapter.StateStore")` `as` two names, delete the `patch("agent.workflow_engine_adapter.create_task", return_value=mock_task)` entry, and before `yield` set `create_task.return_value = mock_task` on `return_value` of both classes.
2. In `TestWorkflowResumeWithRealDB`, tests `test_resume_reuses_existing_workflow_task`, `test_resume_does_not_audit_for_existing_task`, and `test_resume_rejects_halted_task`, which call `_init_workflow_task` directly: build `store = MagicMock()` with `store.get_task_by_id.return_value` set to the existing or halted task, drop the two adapter-function patches, pass `store=store`, and replace `mock_create.assert_not_called()` with `store.create_task.assert_not_called()` where present.
3. In `test_resumed_task_prepares_once` and `test_resumed_task_prepares_once_under_execute_retry`, which call `execute_turn`: bind `patch("agent.orchestrator.StateStore")` `as state_store_cls`, drop the two adapter-function patches, set `state_store_cls.return_value.get_task_by_id.return_value = existing_task` inside the `with` block, set `mock_create = state_store_cls.return_value.create_task`, and keep the later `mock_create.assert_not_called()`.

### Method
- Keep test names, docstrings' claims, expected values, and the order of operations unchanged.
- Keep `patch("agent.workflow_engine_adapter.audit_workflow_start")` as it is.

### Details
- After the edit `rg "workflow_engine_adapter\.(create_task|get_task_by_id)" tests/integration/test_orchestrator_integration.py` must find nothing.
- If `create_task` is imported at module level only for these patches, remove that import.

## Compatibility considerations
- Test-only. Full-turn tests still receive the same mock task.

## Security considerations
- N/A: test-only.

## Rollback considerations
- Revert with procedure `_02` (one release unit).

## Validation plan
- `uv run pytest tests/integration/test_orchestrator_integration.py` passes with every pre-existing assertion unchanged; run it once before editing to record the baseline.
- `uv run ruff check tests/integration/test_orchestrator_integration.py`; `uv run python tools/check_mock_patch_targets.py`.

## Completion criteria
- No patch of the removed adapter names remains, no unused import, and the suite result matches the baseline.

## Out of Scope
- Production code and `tests/agent/test_orchestrator.py` (`_04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the baseline result of `tests/integration/test_orchestrator_integration.py` | Completed | 20261105-132311 | 20261105-132311 | Baseline: 38 passed. |
| 2 | Migrate the fixture and the five resume tests | Completed | 20261105-132311 | 20261105-132311 | Configured both patched store classes; migrated the three direct-resume and two execute_turn tests to the store seam. |
| 3 | Run the validation sequence (`rules/toolchain.md`) after procedure `_02` is applied | Completed | 20261105-132311 | 20261105-132311 | 38 pass, unchanged assertions; ruff clean; mock-patch-targets no findings. |

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
- **Related target files**: `tests/integration/test_orchestrator_integration.py`