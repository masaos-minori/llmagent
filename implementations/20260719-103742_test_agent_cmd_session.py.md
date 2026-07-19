## Goal

Add regression test coverage for the new `_rag_rebuild_fts` method / `rag-rebuild-fts` dispatch entry
in `scripts/agent/commands/cmd_session.py` (paired doc:
`implementations/20260719-103526_cmd_session.py.md`), confirming
`RagMaintenanceService.rebuild_fts()` is invoked and a success message is printed.

**Builds on prior doc**: `implementations/20260719-103047_test_agent_cmd_session.py.md` already
specifies adding a `TestCmdSessionRagConsistency` class (3 methods) to this same file, patching
`"agent.commands.cmd_session.RagMaintenanceService"`. This document assumes that class already
exists in the file and adds a new, separate `TestCmdSessionRagRebuildFts` class alongside it — it
does not repeat or modify the `RagConsistency` tests.

## Scope

**In scope**
- Add a `TestCmdSessionRagRebuildFts` class to `tests/test_agent_cmd_session.py` with:
  (a) success case — confirms `RagMaintenanceService().rebuild_fts()` is called exactly once and a
  success message is printed;
  (b) extra-args tolerance case — mirrors `test_stats_ignores_extra_args`/the prior doc's
  `test_rag_consistency_ignores_extra_args`, confirming `/session rag-rebuild-fts` with trailing
  arguments does not error.

**Out of scope**
- Any change to `TestCmdSessionRagConsistency`, `TestCmdSessionCheckpoint`, `TestCmdSessionVacuum`,
  or any other existing test class in this file.
- Any change to production code — this doc only adds tests.

## Assumptions

1. Verified by direct read of `tests/test_agent_cmd_session.py` (current file, 606+ lines): module
   imports (lines 1-11) are `from __future__ import annotations`, `from types import SimpleNamespace`,
   `from unittest.mock import AsyncMock, MagicMock`, `import pytest`,
   `from agent.commands.cmd_session import _SessionMixin`. No module-level `patch` import — every
   existing test does a local `from unittest.mock import patch` inside the test body (confirmed at
   `TestCmdSessionCheckpoint`/`TestCmdSessionVacuum`, lines 366-425). The new tests follow this same
   local-import style.
2. The correct patch target is `"agent.commands.cmd_session.RagMaintenanceService"` — matching the
   prior `test_agent_cmd_session.py` doc's Assumption 2 for `TestCmdSessionRagConsistency` (both
   `rag-consistency` and `rag-rebuild-fts` dispatch directly to methods defined in `cmd_session.py`
   itself that call `RagMaintenanceService()` via the module-level import added there — not through
   `self._db_session_ops`, which is the pattern used only by `health`/`checkpoint`/`vacuum`/`purge`/
   `recover`, patched instead at `"agent.commands.db_session_ops.DbMaintenanceService"`, confirmed by
   comparing `TestCmdSessionCheckpoint`/`TestCmdSessionVacuum`, lines 373/408, against
   `TestCmdSessionStats`, which patches `"agent.commands.cmd_session.DbMaintenanceService"`).
3. `_make_cmd()` (lines 29-60, already defined in this file) is the correct fixture to construct the
   test subject; invocation is `cmd._cmd_session("rag-rebuild-fts")` (matching
   `cmd._cmd_session("checkpoint")` / `cmd._cmd_session("vacuum")` in the existing checkpoint/vacuum
   classes).
4. `RagMaintenanceService.rebuild_fts(self) -> None` (`rag_maintenance_service.py:31-44`, verified by
   direct read) returns `None` — the mock's `.rebuild_fts` needs no `return_value` configuration
   beyond the `MagicMock()` default (which already returns another `MagicMock` when called, but the
   test only needs to assert it *was* called, not inspect a return value) — matching
   `TestCmdSessionVacuum.test_vacuum_success`'s pattern (`mock_svc = MagicMock()`, no explicit
   `.vacuum.return_value` set, since `DbMaintenanceService.vacuum()` also returns `None`).
5. Per the paired `cmd_session.py` doc's Assumption 3, the success message follows the
   `"<action> complete/rebuilt. [<Tag>]"` convention (`"RAG FTS index rebuilt. [RAG]"`) — assertions
   should check for a substring that survives minor wording changes, mirroring
   `TestCmdSessionVacuum`'s style (`assert "complete" in out.lower()`, not an exact string match). For
   this method, `assert "rebuilt" in out.lower()` is the equivalent robust substring check.

## Implementation

### Target file

`tests/test_agent_cmd_session.py`.

### Procedure

Performed *after* `implementations/20260719-103047_test_agent_cmd_session.py.md`'s
`TestCmdSessionRagConsistency` class is added to this file:

1. Add a new class after `TestCmdSessionRagConsistency` (or in the same relative position as the
   other `db_dispatch`-backed test classes, e.g. directly after `TestCmdSessionVacuum`):
   ```python
   class TestCmdSessionRagRebuildFts:
       def test_rag_rebuild_fts_calls_service_and_prints_success(
           self, capsys: pytest.CaptureFixture
       ) -> None:
           from unittest.mock import patch

           cmd = _make_cmd()
           with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
               mock_svc = MagicMock()
               MockSvc.return_value = mock_svc
               cmd._cmd_session("rag-rebuild-fts")
               out = capsys.readouterr().out
               mock_svc.rebuild_fts.assert_called_once()
               assert "rebuilt" in out.lower()

       def test_rag_rebuild_fts_ignores_extra_args(
           self, capsys: pytest.CaptureFixture
       ) -> None:
           from unittest.mock import patch

           cmd = _make_cmd()
           with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
               mock_svc = MagicMock()
               MockSvc.return_value = mock_svc
               cmd._cmd_session("rag-rebuild-fts extra_arg")
               out = capsys.readouterr().out
               mock_svc.rebuild_fts.assert_called_once()
               assert "rebuilt" in out.lower()
   ```
2. Verify the exact assertion substring (`"rebuilt"`) once the paired `cmd_session.py` doc's
   implementation is landed — adjust if the landed success message uses different wording.

### Method

Plain `unittest.mock.patch`-based unit tests, following the file's existing local-import,
class-per-subcommand convention. No fixtures beyond the existing `_make_cmd()` helper and `capsys`.

### Details

No new helper functions needed; `_make_cmd()` (already defined earlier in the file) is reused as-is.
No new types — `RagMaintenanceService().rebuild_fts()` returns `None`, so no result dataclass needs
constructing (unlike `TestCmdSessionRagConsistency`, which constructs `RagConsistencyResult`
instances).

## Validation plan

| Check | Command | Target |
|---|---|---|
| New tests pass | `uv run pytest tests/test_agent_cmd_session.py -v -k RagRebuildFts` | both new tests pass |
| Full file regression | `uv run pytest tests/test_agent_cmd_session.py -v` | all tests pass, no new failures |
| Format/lint | `uv run ruff format tests/test_agent_cmd_session.py && uv run ruff check tests/test_agent_cmd_session.py` | 0 errors |
| Type check | `uv run mypy tests/test_agent_cmd_session.py` | 0 new errors vs. baseline |
| Coverage of new method | `uv run coverage run -m pytest tests/test_agent_cmd_session.py && uv run coverage report --include="*/cmd_session.py"` | `_rag_rebuild_fts` lines covered |
