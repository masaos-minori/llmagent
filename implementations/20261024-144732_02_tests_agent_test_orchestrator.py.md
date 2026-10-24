## Goal

Give `tests/agent/test_orchestrator.py` a real-engine / real-store test class that pins `tasks.status`
for every exit path of `WorkflowEngineAdapter.execute_turn`, and migrate the one test that currently
pins the adapter's `completed` write to that harness instead of deleting it (`REQ-001`-`REQ-006`,
`REQ-009`, `REQ-011`; `AC-1`-`AC-8`, `AC-10`).

## Scope

- `tests/agent/test_orchestrator.py`:
  - add module-level private helpers for a real `StateStore` on a temporary `workflow.sqlite`
    (new: `_ProbeStateStore` (new), `_status_harness` (new));
  - add one new test class `TestTaskStatusPerTurnOutcome` (new) with eight tests, one per row of the
    Plan's `Problem` table plus the error-level log case;
  - migrate `test_writes_completed_on_normal_success` (`:2012-2052`) in place from the mocked engine to
    that harness.
- No other test file changes. `tests/agent/workflow/` and
  `tests/integration/test_orchestrator_integration.py` are in the Plan's forbidden edit scope and are
  run unchanged as guards.

## Assumptions

- The Plan's `Problem` table (cases A-H) is confirmed at HEAD `6fcbb7e0c`; the expected final statuses
  and `attempts` rows used by these tests are the measured ones, restated in `Details`.
- The suite's autouse `_patch_workflow_loader` fixture (`:91-128`) replaces `WorkflowEngine` and
  `create_task` inside the adapter for every test in this file, so a real-engine test must restore
  them with `monkeypatch.setattr` the way `:394-399` does.
- `_make_ctx()` (`:35`) and `_make_orchestrator(ctx, on_error=...)` (`:130-133`) build a real
  `Orchestrator` with a `MagicMock` context; `orch._workflow_adapter.execute_turn(...)` is the entry
  point the existing status tests drive (`:1957`, `:2049`, `:2092`).
- The engine-side transitions are already tested independently
  (`tests/agent/workflow/test_workflow_engine.py:282`
  `test_execute_success_verify_failure_marks_task_failed`) and must keep passing unchanged.

### Procedure-local findings

- The Plan's test anchors are accurate: `TestHandleWorkflowEngineStatusPreservation` spans `:1922-2095`
  (class header `:1922`, mock store at `:1933-1935`), `test_writes_completed_on_normal_success` is
  `:2012-2052` with the `assert_called_with("task-1", "completed")` at `:2052`, and
  `test_writes_failed_on_execute_failure` is `:2054-2095` with its assertion at `:2095`.
- A usable real-engine + temp-DB harness exists at `:258-358`: temp DB paths and `create_workflow_schema()`
  under `patch("db.helper.build_db_config", ...)` (`:270-283`), `class TempStateStore(StateStore)`
  (`:286-291`), real-class restoration at `:394-399`, and real `WorkflowDef` injection at `:314-324`.
- The file measures 2276 lines / 89977 B today and ends with `TestSingleLlmTurnExecutorOwnership`
  (`:2263-2276`); the new class is appended after `:2276`. No test-file size gate exists
  (`tools/check_module_size.py` scans `scripts/` only).
- `AC-1`'s `attempts` triple is `(stage_id, status, error_kind)` and the engine writes
  `error_kind="exception"` (`workflow_engine.py:26`, `:241`) or `"timeout"` (`:25`, `:230`). Tests must
  assert those values, not `error_msg`, which holds the exception text.
- Only one existing test breaks when the adapter stops writing `completed`. `test_writes_failed_on_execute_failure`
  (`:2054-2095`) keeps passing with a mocked engine because `REQ-004` preserves that write.
- `check_mock_patch_targets.py` (`T-6`): the patch target
  `agent.workflow_engine_adapter.WorkflowEngine` is still used by the preserved tests at `:1946-1957`
  and `:2043-2045`, so removing it from the migrated test does not orphan the target. The check must
  stay green; if it reports the target as unresolvable, the fix is to drop the stale `patch(...)` call,
  not to invent a symbol.
- Sequencing: this row is red until
  `implementations/20261024-144732_01_scripts_agent_workflow_engine_adapter.py.md` lands, and the Plan's
  Phase 1 requires the new class to be committed as the witness of the defect. Also
  `implementations/20261024-083059_01/_02/_04` (turn002) and
  `implementations/20261024-100151_06_tests_agent_test_orchestrator.py.md` (turn005) edit this same
  file; land this class after the turn002 call-site migrations listed in `083059_02` and re-check the
  `:2012-2052` / `:2054-2095` anchors before editing.

## Design decisions

- Assert the durable outcome, not the call sequence: every test reads `tasks.status` back from the
  temporary database. `attempts` rows are asserted only where they carry meaning (`AC-1`, `AC-3`,
  `AC-4`).
- Record the writes anyway (`_ProbeStateStore.calls`) so `AC-2`'s "exactly one `completed` write, made
  by the engine" is testable, and so a future re-introduction of the adapter write fails loudly.
- Keep the migrated test's name and position (`:2012-2052`) rather than folding it into the new class:
  the Plan says it is the only test that pins the success path and must not be deleted (`T-1`).
- Drive `orch._workflow_adapter.execute_turn(...)` directly instead of `orch.handle_turn(...)`: the
  status question lives in the adapter, and going through `handle_turn` pulls in the LLM stream and the
  REPL callbacks (`:300-350`) that this row must not depend on.
- Use a real `WorkflowDef` built in the test (mirrors `:314-324`) with `backoff_sec=0` and sub-second
  stage timeouts, so the retry-exhausted and timeout cases are fast and deterministic.

## Alternatives considered

- Keep a `MagicMock` store and assert `update_task_status` call lists: cannot show that the engine's
  write and the adapter's write land on the same row, which is the defect. The Plan requires a real
  store (`T-2`).
- Add the new class to `tests/agent/workflow/`: that directory is in the Plan's forbidden edit scope,
  and `execute_turn` is adapter behavior, not engine behavior.
- Delete `test_writes_completed_on_normal_success` and let `TestTaskStatusPerTurnOutcome` (new) case A cover
  it: rejected by `T-1` — the regression must stay pinned under the name that documented the old
  behavior.
- Use `executescript(build_workflow_schema_sql())` to build the temp DB (verified to reproduce all eight
  cases): rejected for the committed tests because it skips `_record_workflow_schema_version`
  (`scripts/db/create_schema.py:99`) and diverges from the harness already in this file (`:275-283`).

## Implementation
### Target file

`tests/agent/test_orchestrator.py`

- 2276 lines / 89977 B at HEAD `6fcbb7e0c`.
- Regions in scope: the end of file (append after `:2276`), and the in-place migration at `:2012-2052`.

### Procedure

- Phase 1 step 1 (Plan `Implementation steps` item 1): add the helpers and `TestTaskStatusPerTurnOutcome` (new)
  first, run them against the unmodified adapter, and record the failures on cases A, B, E and the
  log case as the witness for `AC-1`-`AC-6`, `AC-8`. Keep that failing run in the commit message or in
  `Execution Status` notes; do not commit a red suite.
- Phase 3 step 1: migrate `test_writes_completed_on_normal_success` (`:2012-2052`) and run
  `tools/check_mock_patch_targets.py`.
- Ordering: Phase 1 of this row runs before
  `implementations/20261024-144732_01_scripts_agent_workflow_engine_adapter.py.md` Phase 2, and Phase 3
  of this row runs in the same commit as that row.

### Method

1. Append, after `:2276`, the harness helpers:

   ```python
   class _ProbeStateStore(StateStore):
       """StateStore on a temp workflow.sqlite that records every update_task_status call."""

       def __init__(self, db_path: str) -> None:
           self._db = SQLiteHelper(db_path=db_path)
           self._db.open(write_mode=True, row_factory=True)
           self.calls: list[str] = []

       def update_task_status(self, task_id: str, status: str) -> None:
           self.calls.append(status)
           super().update_task_status(task_id, status)

       def task_status(self) -> str | None:
           rows = self._db.fetchall("SELECT status FROM tasks")
           return rows[0]["status"] if rows else None

       def attempt_rows(self) -> list[tuple[str, str, str | None]]:
           rows = self._db.fetchall("SELECT stage_id, status, error_kind FROM attempts")
           return [(r["stage_id"], r["status"], r["error_kind"]) for r in rows]


   @contextmanager
   def _status_harness(
       tmp_path: Path,
       *,
       monkeypatch: pytest.MonkeyPatch,
       execute_stage: Any,
       turn_end_stage: Any = None,
       on_error: Any = None,
       max_attempts: int = 1,
       execute_timeout_sec: float = 5,
   ):
       """Real WorkflowEngine + real StateStore + real adapter, with a temp workflow.sqlite."""
   ```

   Body of `_status_harness` (new), following the existing harness in this file:
   - create `db_path = str(tmp_path / "workflow.sqlite")` plus `rag_path` / `session_path`, and build
     the schema under `patch("db.helper.build_db_config", return_value=DbConfig(...))` calling
     `create_workflow_schema()` exactly as `:270-283`;
   - `store = _ProbeStateStore(db_path)`;
   - `ctx = _make_ctx()`, `orch = _make_orchestrator(ctx, on_error=on_error)`;
   - restore the real classes the autouse fixture patched, as at `:394-399`:
     `monkeypatch.setattr("agent.orchestrator.StateStore", _ProbeStateStore)` — pass `store` to the
     adapter instead (`orch._workflow_adapter._state_store = store`),
     `monkeypatch.setattr("agent.workflow_engine_adapter.WorkflowEngine", WorkflowEngine)`,
     `monkeypatch.setattr("agent.workflow_engine_adapter.create_task", create_task)`;
   - install a real `WorkflowDef` on both `orch._workflow_def` and
     `orch._workflow_adapter._workflow_engine._wdef` (mirrors `:314-324`): `plan` `retryable=False`
     `timeout_sec=5`, `execute` `retryable=True` `timeout_sec=execute_timeout_sec`, `verify`
     `retryable=False` `timeout_sec=5`, `RetryPolicy(max_attempts=max_attempts, backoff_sec=0)`;
   - patch `orch._workflow_adapter._process_turn` with `execute_stage` (new) and
     `orch._workflow_adapter._handle_turn_end` with `turn_end_stage` (new) (default: a no-op `AsyncMock`), so
     the execute stage is controlled without the LLM stack;
   - `patch("agent.workflow_engine_adapter.audit_workflow_start")` and
     `patch("agent.workflow_engine_adapter.audit_stage_completed")` so no audit service is required;
   - yield `(orch, store)`.

2. Append the new class, one test per exit path (names fixed here so the Validation plan's `-k` filter
   is stable):

   | Test | Case | Final `tasks.status` | Extra assertions |
   |---|---|---|---|
   | `test_success_writes_completed_exactly_once` (new) | A | `completed` | `store.calls == ["running", "completed"]` |
   | `test_verify_stage_exception_keeps_failed` (new) | B | `failed` | `pytest.raises(RuntimeError)`; `attempt_rows()` contains `("verify", "failed", "exception")`; `store.calls == ["running", "failed"]` |
   | `test_soft_turn_error_downgrades_to_failed` (new) | C | `failed` | no exception; last recorded write is `failed` |
   | `test_execute_retry_exhaustion_halts` (new) | D | `halted` | no exception; `("execute", "failed", "exception")` recorded `max_attempts` times; `store.calls == ["running", "halted"]` |
   | `test_execute_stage_timeout_halts` (new) | F | `halted` | `("execute", "failed", "timeout")` in `attempt_rows()` |
   | `test_cancellation_records_halted_and_propagates` (new) | E | `halted` | `pytest.raises(asyncio.CancelledError)`; an `("execute", "running", None)` attempt row is still open |
   | `test_failure_before_engine_start_keeps_pending` (new) | H | `pending` | `store.calls == []`; `pytest.raises(RuntimeError)` |
   | `test_status_write_failure_logs_error_without_on_error` (new) | log | unchanged | `caplog` at `ERROR` names the task id and `failed`; `execute_turn` returns normally; `on_error.assert_not_called()` |

   Construction notes per test:
   - B: `turn_end_stage=AsyncMock(side_effect=RuntimeError("verify stage failure"))`,
     `execute_stage=AsyncMock(return_value=("answer", None, False))`.
   - C: `execute_stage=AsyncMock(return_value=("partial", "CONNECT_ERROR", True))`.
   - D: `execute_stage=AsyncMock(side_effect=RuntimeError("always fails"))`, `max_attempts=2`.
   - F: `execute_stage` (new) awaits longer than `execute_timeout_sec` (new) (for example `await asyncio.sleep(0.2)`
     with `execute_timeout_sec=0.01`), mirroring `:304-320`.
   - E: `execute_stage` (new) awaits a `threading.Event`-free long sleep, then
     `task = asyncio.create_task(orch._workflow_adapter.execute_turn(...))`; `await asyncio.sleep(0.05)`;
     `task.cancel()`; `await task` inside `pytest.raises(asyncio.CancelledError)`. Cancel the adapter
     coroutine directly — not the REPL loop.
   - H: patch `agent.workflow_engine_adapter.audit_workflow_start` with
     `side_effect=RuntimeError("audit start failed")` inside the harness call, so the failure lands in
     `_init_workflow_task` (`workflow_engine_adapter.py:252-296`) after `create_task` wrote the row.
   - log case: a store subclass whose `update_task_status` raises `RuntimeError`, driven through case C
     so the adapter genuinely attempts a `failed` write; assert with
     `caplog.at_level(logging.ERROR, logger="agent.workflow_engine_adapter")`.

3. Migrate `test_writes_completed_on_normal_success` (`:2012-2052`): keep the `@pytest.mark.asyncio`
   decorator at `:2012`, the test name at `:2013` and the class it lives in; replace the body
   (`:2014-2052`) with a `_status_harness` (new) call and the assertions
   `store.calls == ["running", "completed"]` and `store.task_status() == "completed"`. Update the
   docstring to state that the engine is the sole writer of `completed`. Delete the now-unneeded
   `MagicMock` store, the `_normal_run` mock engine (`:2022-2028`) and the
   `patch("agent.workflow_engine_adapter.WorkflowEngine", ...)` entry (`:2043-2045`) from this test only.

### Details

- Expected outcomes restated from the measurement at HEAD `6fcbb7e0c` (pre-change adapter):
  A `["running","completed","completed"]`; B `["running","failed","completed"]`;
  C `["running","completed","failed"]`; D `["running","halted"]`; E `["running","completed"]` with the
  `execute` attempt left `running`; F `["running","halted"]`; H `[]` and `pending`. After
  `implementations/20261024-144732_1_*` lands: A `["running","completed"]`, B `["running","failed"]`,
  E `["running","halted"]`, C/D/F/H unchanged.
- Imports the new code needs that this file may not yet have at module scope: `asyncio`, `logging`,
  `contextlib.contextmanager`, `pathlib.Path`, `agent.workflow.models.RetryPolicy` /
  `StageDefinition` / `WorkflowDef`, `agent.workflow.state_store.StateStore`,
  `agent.workflow.workflow_engine.WorkflowEngine`, `agent.workflow.task_ops.create_task`,
  `db.config.DbConfig`, `db.create_schema.create_workflow_schema`, `db.helper.SQLiteHelper`. Several are
  already imported (`WorkflowEngine`, `WorkflowDef`, `StageDefinition`, `RetryPolicy`, `DbConfig`,
  `create_workflow_schema`); add only the missing ones and keep the import block's existing grouping.
- Do not patch `agent.workflow.state_store.StateStore` internals: the tests must exercise the real SQL
  in `task_ops.update_task_status` (`scripts/agent/workflow/task_ops.py:60-64`), which has no guard
  against overwriting a terminal status — that is why the adapter side is the fix.
- Determinism: `backoff_sec=0`, sub-second stage timeouts, no assertion on elapsed time, no reliance on
  the production `/opt/llm/db/workflow.sqlite` (every DB path is under `tmp_path`).
- The file is `89977 B`; the addition is roughly 200-260 lines and is not gated by
  `tools/check_module_size.py`.

## Compatibility considerations

- `tests/agent/test_orchestrator.py:1922-2010` and `:2054-2095` must pass unmodified
  (`AC-5`, `AC-7`).
- `tests/agent/workflow/` and `tests/integration/test_orchestrator_integration.py:718-790`
  (`TestWorkflowResumeWithRealDB`) must pass unmodified.
- The autouse `_patch_workflow_loader` fixture (`:91-128`) must keep working for every other test in
  the file: the new tests restore real classes with `monkeypatch` (as `:394-399` does) and must not add
  or modify the fixture.
- The class name `TestTaskStatusPerTurnOutcome` (new) is new; no existing test, doc, or config references it
  (verified by `grep -rn "TestTaskStatusPerTurnOutcome" .` returning nothing at HEAD `6fcbb7e0c`).
- The migrated test keeps its name, so any external reference to
  `test_writes_completed_on_normal_success` (issue text, plan rows) stays resolvable.

## Security considerations

- Test-only change. Temporary databases live under `pytest`'s `tmp_path`; nothing reads or writes
  `/opt/llm/db/`.
- The `caplog` assertions must check that the log line contains the task id and the intended status and
  nothing derived from turn content.

## Rollback considerations

- Revert with `git checkout HEAD~1 -- tests/agent/test_orchestrator.py`. If the adapter row in the same
  commit is reverted, the migrated test must be reverted with it, otherwise the mocked-engine
  assertion and the real-engine harness disagree.
- The new class is additive: if only the class is removed, the pre-change adapter behavior remains
  unpinned, which is the state the Plan explicitly rejects.

## Validation plan

- Witness run (Phase 1, before the adapter change):
  `uv run pytest tests/agent/test_orchestrator.py -k TaskStatusPerTurnOutcome -q` — expected failures
  on `test_success_writes_completed_exactly_once` (new), `test_verify_stage_exception_keeps_failed` (new),
  `test_cancellation_records_halted_and_propagates` (new) and `test_status_write_failure_logs_error_without_on_error` (new);
  the other four must already pass. Record the failure list.
- Targeted green run: same command after
  `implementations/20261024-144732_01_scripts_agent_workflow_engine_adapter.py.md` — 8 passed.
- `uv run pytest tests/agent/test_orchestrator.py -k "TaskStatusPerTurnOutcome or HandleWorkflowEngineStatusPreservation" -q`
- `uv run pytest tests/agent/test_orchestrator.py tests/agent/workflow/ tests/integration/test_orchestrator_integration.py -q`
  — 217 baseline tests (measured 2026-10-24 at HEAD `6fcbb7e0c`) plus the 8 new tests.
- `uv run pytest tests/agent -q` — no new failure against the baseline recorded at implementation time.
- `uv run python tools/check_mock_patch_targets.py` (`T-6`) — no finding naming
  `agent.workflow_engine_adapter.WorkflowEngine` or `agent.orchestrator.StateStore`.
- `uv run ruff check tests/`, `uv run ruff format --check tests/`.
- Determinism: run the new class three times (`uv run pytest tests/agent/test_orchestrator.py -k
  TaskStatusPerTurnOutcome -q --count 3` is not available; re-run the command three times) and confirm
  identical results.
- Mutation control (`AC-2`, `AC-3`): re-add `update_task_status(task.task_id, "completed")` to the
  adapter `finally` and confirm the case-A and case-B tests fail; revert. Delete the
  `except asyncio.CancelledError` branch and confirm the case-E test fails; revert.

## Completion criteria

- `TestTaskStatusPerTurnOutcome` (new) exists with the eight tests in `Method` step 2, all passing, each
  asserting a `tasks.status` value read from a real temporary database (`REQ-011`, `AC-1`-`AC-5`,
  `AC-8`).
- `test_writes_completed_on_normal_success` exists, still named the same, and asserts a single engine
  `completed` write with no adapter write (`T-1`, `AC-2`).
- The case-E test asserts `halted`, a propagated `CancelledError`, and an open `execute` attempt row
  still in `running`, recording that closing it is out of scope (`AC-3`, `UNK-02`).
- The log test asserts an `ERROR` record naming the task id and the intended status, a normal return,
  and `on_error` untouched (`AC-6`).
- `check_mock_patch_targets.py` and the 217-test baseline suites pass unchanged (`AC-7`, `T-6`).

## Out of Scope

- Closing the abandoned `attempts` row for a cancelled turn (Plan Out-of-Scope, `DR-006`, `UNK-02`);
  the tests assert that it stays `running`.
- Any change under `tests/agent/workflow/` or
  `tests/integration/test_orchestrator_integration.py` (Plan forbidden edit scope).
- REPL-level cancellation behavior and shutdown tests — owned by `turn005`
  (`implementations/20261024-100151_*`).
- Turn-end / turn-event assertions — owned by `turn004` (`implementations/20261024-092307_05_*`).
- `_process_turn` split call-site migrations — owned by
  `implementations/20261024-083059_02_tests_agent_test_orchestrator.py.md`.
- Coverage for `tasks.status` readers that do not exist in production yet.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 1 witness run must be recorded before the adapter change |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the test row; migration is Phase 3 step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Baseline: 217 passed, measured 2026-10-24 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: docs rows are `_03` and `_04` | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `083059_02` and `100151_06` edit this same file; the `:2012-2052` / `:2054-2095` anchors must be re-taken after they land | False | — |
| 1 | Phase 1 requires a deliberately failing run before the adapter row lands; the failing run must not be committed as the suite state | False | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`-`REQ-006`, `REQ-009`, `REQ-011`
- **Source issue**: `issues/20261021-093421_turn003_task-status-overwritten-after-failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-125756_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-144732
- **Related target files**: `tests/agent/test_orchestrator.py`
