## Goal

Make `tests/agent/test_repl.py` assert the new behavior: the persist step is
reached before `close_resources()` on every exit path (AC-1, AC-2); a persistence
failure is contained and does not mask the propagating exception (AC-4); exactly
one operator-facing line is produced per input-loop error (AC-6); and a context
with no started session performs no `save` (AC-3). Then delete the 18
`mock_persister` fixtures whose second argument disappears with `run()`'s new
single-parameter signature (AC-5).

## Scope

Test-only change to `tests/agent/test_repl.py`. Reference reads:
`scripts/agent/repl.py` (row 1, the renamed `_persist_session_state` and the new
`finally`), `scripts/agent/repl_input_loop.py` (row 2, REQ-007). Dependent file:
`tests/agent/test_session_persister.py` (row 5).

## Assumptions

- `_make_bare_repl` (`:28-83`) stubs both persist methods
  (`:75-77`) and sets `ctx.session.session_id = 1` (`:34`), so the new `finally`
  is observable without new fixture machinery.
- `TestRunResourceCleanup._install_spies` (`:1428-1443`) records call order in a
  list; the two recording coroutines (`spy_close`, `spy_loop`) are the model for
  the persist spy added here.
- The 18 `mock_persister = AsyncMock()` assignments (`:150`, `:159`, …, `:435`) are
  passed as the second positional argument of `repl._input_loop.run(...)` and
  asserted on zero times; removing the parameter makes them unused (`F841`).

## Design decisions

- **Extend `TestRunResourceCleanup` (AC-1, AC-2, AC-4).** Add a persist spy to
  `_install_spies`, drop the `persister` parameter from `spy_loop`, and update the
  three expected call lists to persist-then-close.
- **Strengthen `test_error_message_includes_class_name` (AC-6).** Change
  `assert len(fatal_calls) >= 1` (`:770`) to `== 1` and add a `SchemaMissingError`
  variant.
- **Give `test_handles_none_session_id` its assertion (AC-3).** Assert
  `save` is not called and remove the inert `SQLiteHelper` patch.
- **Delete the 18 fixtures (AC-5).** Remove each `mock_persister = AsyncMock()`
  line and its paired second argument.

## Alternatives considered

- Counting `persist_session_memories` and `persist_session_diagnostics` calls
  separately — rejected: the plan records the step once as `persist_session_state`
  (the method `run()` awaits), which is what AC-2 ("persist appearing exactly once
  per exit") measures.
- Leaving `assert len(fatal_calls) >= 1` — rejected: it tolerates the duplicate
  report this Plan removes (Design → Why the current tests pass).

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

1. **Update `_install_spies`** (`:1428-1443`). Replace it with:
   ```python
   @staticmethod
   def _install_spies(
       repl: AgentREPL,
       calls: list[str],
       loop_error: Exception | None = None,
       persist_error: Exception | None = None,
   ) -> None:
       async def spy_close() -> None:
           calls.append("close_resources")

       async def spy_persist() -> None:
           calls.append("persist_session_state")
           if persist_error is not None:
               raise persist_error

       async def spy_loop(banner) -> None:
           calls.append("input_loop.run")
           if loop_error is not None:
               raise loop_error

       repl._shutdown = MagicMock()
       repl._shutdown.close_resources = spy_close
       repl._persist_session_state = spy_persist
       repl._input_loop.run = spy_loop
   ```
   `spy_loop` now takes one parameter (matching `run()`'s new signature); the
   persist spy records `"persist_session_state"` and can raise to drive the AC-4
   case.
2. **Update the three expected call lists:**
   - `test_cleanup_runs_after_input_loop_on_success` (`:1457`):
     `assert calls == ["input_loop.run", "persist_session_state", "close_resources"]`
   - `test_cleanup_runs_once_when_startup_fails` (`:1472`):
     `assert calls == ["persist_session_state", "close_resources"]` — this is the
     AC-2 witness: the persist step now appears on the startup-failure path, where
     it was absent at HEAD.
   - `test_cleanup_runs_once_when_input_loop_raises` (`:1488`):
     `assert calls == ["input_loop.run", "persist_session_state", "close_resources"]`
3. **Add the AC-4 case** to `TestRunResourceCleanup` (persist raises while the
   loop raises; the loop's exception must propagate):
   ```python
   @pytest.mark.asyncio
   async def test_persist_failure_does_not_mask_loop_error(self) -> None:
       repl = _make_bare_repl()
       calls: list[str] = []
       self._install_spies(
           repl,
           calls,
           loop_error=RuntimeError("loop failed"),
           persist_error=RuntimeError("persist failed"),
       )
       with patch("agent.repl.StartupOrchestrator") as MockStartup:
           MockStartup.return_value.run = AsyncMock(
               return_value=(MagicMock(), MagicMock())
           )
           with pytest.raises(RuntimeError, match="loop failed"):
               await repl.run()
       assert calls == ["input_loop.run", "persist_session_state", "close_resources"]
       repl._view.write_warning.assert_called_once()
   ```
4. **Strengthen `test_error_message_includes_class_name`** (`:738-772`). Change
   `:770` from `assert len(fatal_calls) >= 1` to `assert len(fatal_calls) == 1`.
   Then add a `SchemaMissingError` variant beside it:
   ```python
   @pytest.mark.asyncio
   async def test_error_message_includes_class_name_schema_missing(self, tmp_path) -> None:
       """A SchemaMissingError produces exactly one operator-facing line."""
       from agent.session import SchemaMissingError

       from db.config import DbConfig

       repl = _make_bare_repl()
       repl._orchestrator = MagicMock()
       repl._cmds = MagicMock()

       valid_cfg = DbConfig(
           rag_db_path=str(tmp_path / "rag.sqlite"),
           session_db_path=str(tmp_path / "session.db"),
           workflow_db_path=str(tmp_path / "workflow.sqlite"),
           eventbus_db_path=str(tmp_path / "eventbus.sqlite"),
       )
       with (
           patch("db.helper.build_db_config", return_value=valid_cfg),
           patch("agent.repl.StartupOrchestrator") as MockStartup,
       ):
           MockStartup.return_value.run = AsyncMock(
               return_value=(MagicMock(), MagicMock())
           )
           with patch.object(repl._ctx.session, "start") as mock_start:
               mock_start.side_effect = SchemaMissingError("schema missing")
               try:
                   await repl.run()
               except RuntimeError:
                   pass

       fatal_calls = repl._view.write_fatal.call_args_list
       assert len(fatal_calls) == 1
       assert "schema missing" in str(fatal_calls[-1][0][0])
   ```
5. **Give `test_handles_none_session_id` its assertion** (`:505-512`). Replace the
   body with:
   ```python
   @pytest.mark.asyncio
   async def test_handles_none_session_id(self):
       repl = self._make_repl()
       repl._ctx.session.session_id = None
       repl._ctx.services = None

       await repl._persister.persist_session_diagnostics()

       # Gate (row 3): no started session means no save call.
       repl._diagnostic_store.save.assert_not_called()
   ```
   The inert `patch("agent.wal_checkpoint_manager.SQLiteHelper")` is removed
   (`SessionPersister` never touches `wal_checkpoint_manager`).
6. **Delete the 18 fixtures.** For each of the 18 sites (`:150`, `:159`, `:167`,
   `:179`, `:189`, `:211`, `:223`, `:232`, `:242`, `:266`, `:280`, `:294`,
   `:313`, `:326`, `:354`, `:390`, `:410`, `:435`):
   - delete the `mock_persister = AsyncMock()` line, and
   - drop the second argument from the corresponding
     `repl._input_loop.run(mock_banner, mock_persister)` call, leaving
     `repl._input_loop.run(mock_banner)`. For the three `wait_for` sites
     (`:360`, `:396`, `:463`) this means
     `repl._input_loop.run(mock_banner, mock_persister)` inside
     `asyncio.wait_for(repl._input_loop.run(mock_banner), timeout=5.0)`.
   No assertion in those 18 cases changes.

### Method

Read-only reference reads of `scripts/agent/repl.py` (row 1) confirm the renamed
`_persist_session_state` and the persist-then-close `finally`; `scripts/agent/
session.py` (`session_id` at `:148`) confirms the gate the new assertions cover.

### Details

- **Ordering dependency on row 2 (REQ-007).** Steps 2 and 4 (`== 1`, persist-
  then-close ordering) pass only after `repl_input_loop.py`'s single-report rule
  is applied. If these assertions fail before row 2, that is expected — implement
  row 2 first. The mutation requirement "restoring the duplicate report fails a
  test (AC-6)" relies on this.
- **Shared collision with `repl003` (`:334-368`).** Those test cases share the
  `mock_persister` argument this step deletes. Implement `repl003`
  (`plans/20261022-043008_plan.md`) before this step and re-anchor the site
  numbers against the file as it stands; the fixture deletions are what keep ruff
  `F841` clean after `run()` loses its second parameter.
- `TestRunBindsStartupResultsToInputLoop` (`:712-730`) patches
  `repl._input_loop.run` with `AsyncMock()` and passes no persister, so it is
  unaffected by the signature change. `TestRunStartupInterrupted` (`:810-873`) and
  `TestCloseResourcesWALCheckpoint` (`:879-1030`) are not edited (owned by
  `shutdown001`).

## Compatibility considerations

- The 11 `await repl.run()` call sites in the class under change now reach the
  persist step via `run()`'s `finally` (row 1); `_make_bare_repl` stubs both
  persist methods (`:75-77`) so the new `finally` is observable without new
  fixture machinery.
- `test_repl_error_handling.py`, `test_regression_diagnostic_persist.py`,
  `test_import_smoke.py` are unchanged and must stay green (AC-7).

## Security considerations

- N/A: test-only change.

## Rollback considerations

- Single logical commit; `git checkout -- tests/agent/test_repl.py` restores HEAD.
  Reversible; touches no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_repl.py -q` (AC-1, AC-2, AC-4, AC-6 once row 2
  is applied).
- `uv run pytest tests/agent/test_repl_error_handling.py
  tests/agent/test_regression_diagnostic_persist.py tests/agent/test_import_smoke.py
  -q` (AC-7).
- `uv run ruff check tests/agent/test_repl.py` (no `F841` left by the removed
  arguments; AC-5), `uv run mypy --no-namespace-packages tests/agent/test_repl.py`.
- `uv run python tools/check_mock_patch_targets.py` (the removed `SQLiteHelper`
  patch was inert).

## Completion criteria

`TestRunResourceCleanup` asserts persist → close on all three paths with the
startup-failure path now including the persist step; `test_error_message_includes
_class_name` asserts exactly one fatal line and a `SchemaMissingError` variant
covers that path; `test_handles_none_session_id` asserts no `save` call; the 18
`mock_persister` fixtures are gone and ruff `F841` is clean; AC-1/AC-2/AC-4/AC-5/
AC-6/AC-7 hold.

## Out of Scope

- The production bracket and rename — row 1. The single-report rule — row 2. The
  new mirror test file — row 5. Docs — rows 6/7.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `_install_spies` with persist spy; drop `persister` from `spy_loop` | Pending | — | — | REQ-001, AC-4 |
| 2 | Update the three expected call lists to persist-then-close | Pending | — | — | AC-1, AC-2 |
| 3 | Add AC-4 case (persist raises while loop raises) | Pending | — | — | AC-4 |
| 4 | Strengthen `test_error_message_includes_class_name` to `== 1` + `SchemaMissingError` variant | Pending | — | — | AC-6 (needs row 2) |
| 5 | Give `test_handles_none_session_id` its assertion; remove inert patch | Pending | — | — | AC-3 |
| 6 | Delete the 18 `mock_persister` fixtures + paired args | Pending | — | — | AC-5 |
| 7 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2,4 | Shared file edited by five Frozen Plans. This Plan owns `:150-435` (fixture deletion), `:505-512`, `:739-775`, `:1423-1490`. Real collision at `:334-368` with `repl003` (`20261022-043008`): implement `repl001`/`repl002`/`repl003`/`shutdown001` first, then re-anchor line numbers. | No | — |
| 4 | AC-6 (`== 1`) passes only after row 2 (REQ-007) applies. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | 6 | Ordering | Open | implementer | after `plans/20261022-043008_plan.md` implemented |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-004, REQ-007, REQ-011
- **Source issue**: `issues/20261021-093421_shutdown002-session-persistence-skipped-on-startup-failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-071052_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-093504
- **Related target files**: `tests/agent/test_repl.py`
