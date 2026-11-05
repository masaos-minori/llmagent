## Goal
- Make `WorkflowEngineAdapter` create and fetch tasks through `StateStore.create_task` / `get_task_by_id` and read the version through `WorkflowEngine.version`, with identical SQL, task ids, and audit payloads (`REQ-002`, `REQ-003`, `REQ-006`).

## Scope
**Release unit**: adapter-seam
- Edits `scripts/agent/workflow_engine_adapter.py` only. It must land together with procedures `_04_tests_agent_test_orchestrator.py.md` and `_05_tests_integration_test_orchestrator_integration.py.md`: once the adapter stops importing `create_task` and `get_task_by_id`, the 26 test patch sites of those names fail, and before it they would fail the other way.

## Assumptions
- Procedure `_01_scripts_agent_workflow_workflow_engine.py.md` has added `WorkflowEngine.version`.
- `StateStore.create_task(session_id, turn_number, workflow_version, workflow_id)` and `get_task_by_id(task_id)` forward unchanged to `task_ops` (read in the Plan).
- `_init_workflow_task(ctx, session_id, existing_task_id=None, store=None)` keeps its signature; when `store` is `None` it still creates and later closes its own `StateStore()`.

## Design decisions
- Keep the resume error messages (`Task {id} not found`, `Task {id} is halted and cannot be automatically resumed`) byte-identical; the tests match them.
- Drop `assert self._workflow_engine._wdef is not None`: `_wdef` is typed non-optional and the constructor always sets it.

## Alternatives considered
- Keep importing `create_task` / `get_task_by_id` and only swap `store._db` for `store.get_connection()`: rejected because it leaves the task path bypassing the store's public methods, which is the Issue's second finding.

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`

### Procedure
1. Remove the import `from agent.workflow.task_ops import create_task, get_task_by_id`.
2. In `_init_workflow_task`, delete the `_wdef` assert, replace `create_task(store._db, session_id=..., turn_number=..., workflow_version=..., workflow_id=...)` with `store.create_task(session_id=..., turn_number=..., workflow_version=self._workflow_engine.version, workflow_id=workflow_id)`, and replace `get_task_by_id(store._db, existing_task_id)` with `store.get_task_by_id(existing_task_id)`.
3. In the same method, replace `self._workflow_engine._wdef.version` in the `audit_workflow_start(...)` call with `self._workflow_engine.version`.
4. In `_activate_workflow`, replace `self._workflow_engine._wdef.version` with `self._workflow_engine.version`.

### Method
- Pass the same keyword arguments in the same order; do not rename any parameter.
- Leave the `try/finally` that closes an owned store and the two `RuntimeError` raises untouched.
- Run `uv run ruff check --fix` only for the removed import; do not reformat unrelated code.

### Details
- After the edit: `rg "store\._db|_workflow_engine\._wdef|task_ops" scripts/agent/workflow_engine_adapter.py` finds nothing.
- The version is read from the engine exactly where `_wdef.version` was read, so the audit payload and `ctx.workflow.current_workflow_version` are unchanged.

## Compatibility considerations
- `execute_turn`, `init_workflow_task`, and `_init_workflow_task` keep their signatures and return values.
- Tests that patched `agent.workflow_engine_adapter.create_task` or `get_task_by_id` must be migrated (procedures `_04`, `_05`); a test that sets `engine._wdef` directly keeps working through the property.
- Tests whose engine is a `MagicMock` now see `engine.version` as a mock; the previous `_wdef.version` was a mock too.

## Security considerations
- N/A: no input handling, secrets, or trust boundary involved.

## Rollback considerations
- Revert this commit together with procedures `_04` and `_05` (one release unit).

## Validation plan
- `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py tests/agent/workflow` after all three procedures of the release unit are applied; the resume `RuntimeError` message tests must pass.
- `uv run ruff check scripts/agent/workflow_engine_adapter.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `uv run python tools/check_module_size.py`; `uv run python tools/generate_reference_table.py --check`.

## Completion criteria
- The `rg` check in Details finds nothing, the adapter has no `task_ops` import, and the orchestrator and integration suites pass with unchanged assertions.

## Out of Scope
- Test migration (`_04`, `_05`), `StateStore`, and the engine (`_01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Switch `_init_workflow_task` and `_activate_workflow` to the store methods and `engine.version`; remove dead imports | Pending | — | — | |
| 2 | Run the orchestrator and integration suites after procedures `_04` and `_05` are applied | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`); deploy only as the user's decision per `skills/deploy/SKILL.md` | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (version via engine property), `REQ-003` (store methods), `REQ-006` (no behavior change)
- **Source issue**: issues/20261103-134147_wfreview004_workflow-adapter-and-engine-private-attribute-access.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-085959_wfreview004_workflow-adapter-and-engine-private-attribute-access.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-092748
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`
