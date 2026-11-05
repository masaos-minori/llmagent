## Goal
- Add a real-database regression test that runs a turn through `Orchestrator._execute_turn` and then `SessionPersister.persist_session_diagnostics()`, and asserts the diagnostics see the turn's workflow rows (`REQ-002`: prove the write path and the read path agree on the session id).

## Scope
**Release unit**: N/A: not part of a release unit
- Creates one new test module. No production code, fixture file, or `conftest` is changed.
- The test must fail on the current orchestrator (it passes `""` as the session id) and pass after procedure `_02_scripts_agent_orchestrator.py.md` lands.

## Assumptions
- `tests/agent/test_orchestrator.py` defines `_make_ctx` and `_make_orchestrator`; importing them is an established pattern (`from tests.agent.test_tool_runner import _cfg, _make_ctx` exists in `tests/agent/test_tool_loop_guard_wiring.py`).
- The module-level autouse fixture `_patch_workflow_loader` of `tests/agent/test_orchestrator.py` does not apply to this module, so the orchestrator is built with real `StateStore` and real `WorkflowEngine`; only `WorkflowLoader` is patched, to avoid depending on the deployed workflow file.
- `db.helper.build_db_config` patched to a temporary `DbConfig` routes every `StateStore()` in this test, the orchestrator's and the persister's, to the same temporary `workflow.sqlite`.
- The persister is exercised with a stub diagnostic store; the saved `session_summary` JSON is the observable.

## Design decisions
- Drive the real `Orchestrator._execute_turn` (not the adapter) so the call site that carries the bug is the one under test.
- Capture the summary through a `MagicMock` diagnostic store (`fetch` returns `[]`, `save` is inspected) so no `session.sqlite` is needed.

## Alternatives considered
- Reusing `_status_harness` from `tests/agent/test_orchestrator.py`: rejected because it patches `agent.workflow_engine_adapter.create_task`, which the wfreview004 Plan removes, so the new test would be coupled to that migration.
- Asserting on the `tasks` row only: rejected because the defect is the mismatch with the persister's read, so the persister aggregation must be part of the assertion.

## Implementation
### Target file
`tests/agent/workflow/test_session_diagnostics_wiring.py` (new)

### Procedure
1. Create the module with a header docstring naming the contract: `tasks.session_id` holds the chat session id.
2. Add a fixture `wired` (new) that, for the duration of a test: creates `tmp_path / "workflow.sqlite"` through `create_workflow_schema()` under a patched `db.helper.build_db_config` returning a `DbConfig` (as `tests/agent/test_orchestrator.py` does), keeps that patch active until teardown, patches `agent.orchestrator.WorkflowLoader` so `load()` returns a three-stage `WorkflowDef` (`plan`, `execute`, `verify`, one attempt), builds `ctx = _make_ctx()` with `ctx.session.session_id = 7`, `ctx.services = None`, and `ctx.stats.stat_partial_completions = 0` (without these two the summary holds non-serializable mock values and is not saved), builds `orch = _make_orchestrator(ctx)`, replaces `orch._workflow_adapter._run_execute_stage` with an async stub returning `("answer", None, False)`, and patches `agent.workflow_engine_adapter.audit_workflow_start` and `audit_stage_completed` with `MagicMock`. It yields `(orch, ctx)` and closes `orch._state_store` at teardown.
3. Add `test_persister_sees_turn_workflow_rows` (new): await `orch._execute_turn("hello")`; build a stub diagnostic store (`MagicMock`, `fetch.return_value = []`); await `SessionPersister(ctx, stub, MagicMock()).persist_session_diagnostics()`; parse `stub.save.call_args.kwargs["content"]` with `orjson.loads`; assert `task_count == 1` and `workflow_count == 1`.
4. Add `test_task_row_carries_chat_session_id` (new): after one turn, read `tasks` through `orch._state_store.get_connection().fetchall(...)` and assert the single row's `session_id` equals `"7"`.
5. Add `test_turn_without_session_records_empty_session_id` (new): set `ctx.session.session_id = None`, run one turn, assert the stored value is `""`. Its docstring states this records the documented fallback of `format_session_id`, not a desired state.

### Method
- Imports: `_make_ctx` and `_make_orchestrator` from `tests.agent.test_orchestrator`; `SessionPersister` from `agent.session_persister`; `DbConfig`, `create_workflow_schema` from `db.config` and `db.create_schema`; `WorkflowDef`, `StageDefinition`, `RetryPolicy` from `agent.workflow`; `orjson`; `pytest`; `unittest.mock`.
- Mark the async tests with `pytest.mark.asyncio`, as the neighboring modules do.
- Keep every database path under `tmp_path` so the production-isolation guard in `tests/conftest.py` is never reached.

### Details
- The tasks table has one row per turn, so `task_count == 1` and `workflow_count == 1` are exact.
- If the real `Orchestrator` constructor needs a ctx attribute the mock does not provide, add that attribute in the fixture, not in `tests/agent/test_orchestrator.py`.
- Do not assert on audit payloads here; they are covered by the existing orchestrator tests.

## Compatibility considerations
- Test-only. It imports two private helpers of another test module; a rename there fails this module at import time, which is visible and cheap to fix.

## Security considerations
- N/A: test-only, temporary databases, no secrets.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_session_diagnostics_wiring.py -v`: before procedure `_02` it fails (assertion on `task_count` or on the stored session id); after it, it passes.
- `uv run pytest tests/agent/workflow tests/agent/test_session_persister.py tests/agent/test_orchestrator.py`.
- `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy --no-namespace-packages scripts/ tests/eventbus` is unaffected (this directory is not in the mypy scope); `uv run python tools/check_mock_patch_targets.py` for the `patch(...)` targets.

## Completion criteria
- The module exists with the three tests, ruff is clean, and the first two tests fail on the pre-fix orchestrator and pass on the fixed one.

## Out of Scope
- Changing `SessionPersister`, the adapter, `StateStore`, or any existing test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the module with the fixture and three tests | Pending | — | — | |
| 2 | Run the module and confirm the first two tests fail on the pre-fix orchestrator | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (real-DB regression test of write path plus read path)
- **Source issue**: issues/20261103-134147_wfreview001_workflow-diagnostics-empty-session-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-085618_wfreview001_workflow-diagnostics-empty-session-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-092237
- **Related target files**: `tests/agent/workflow/test_session_diagnostics_wiring.py`
