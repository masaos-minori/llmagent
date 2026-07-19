## Goal

Add regression test coverage for the new `_rag_consistency` method / `rag-consistency` dispatch
entry in `scripts/agent/commands/cmd_session.py` (paired doc:
`implementations/20260719-102923_cmd_session.py.md`), so the new subcommand's consistent/inconsistent
output paths and its argument-tolerance behavior are verified.

## Scope

**In scope**
- Add a `TestCmdSessionRagConsistency` class to `tests/test_agent_cmd_session.py` with three test
  methods:
  (a) consistent case — no issues printed, `is_consistent` shown as `True`;
  (b) inconsistent case — `is_consistent` shown as `False` and each issue string printed;
  (c) `/session rag-consistency` with extra trailing args does not error (mirrors
  `test_stats_ignores_extra_args`).

**Out of scope**
- Any change to `TestCmdSessionHealth`, `TestCmdSessionStats`, or any other existing test class in
  this file.
- Any change to production code — this doc only adds tests.

## Assumptions

1. `patch` is not imported at module level in this test file (confirmed: file imports at lines 1-11
   are `from __future__ import annotations`, `from types import SimpleNamespace`,
   `from unittest.mock import AsyncMock, MagicMock`, `import pytest`,
   `from agent.commands.cmd_session import _SessionMixin`). Every existing test method instead does
   a local `from unittest.mock import patch` inside the test body (no `@patch` decorators anywhere in
   this file). The new tests must follow this same local-import style for consistency, not add a
   module-level `patch` import or decorator-style patching.
2. The correct patch target for the new tests is `"agent.commands.cmd_session.RagMaintenanceService"`
   — NOT `"agent.commands.db_session_ops.DbMaintenanceService"` (the target used by
   `TestCmdSessionHealth`, because `health` dispatches through `self._db_session_ops`, a
   `DbSessionOps` instance that imports its own `DbMaintenanceService`). `rag-consistency` dispatches
   directly to `self._rag_consistency` (defined in `cmd_session.py` itself, per the paired doc), which
   calls `RagMaintenanceService()` using the module-level import added to `cmd_session.py` directly —
   this matches `TestCmdSessionStats`'s pattern (`patch("agent.commands.cmd_session.DbMaintenanceService")`,
   used because `stats` dispatches to `self._db_session_stats`, also defined in `cmd_session.py`
   itself). This distinction (module-vs.-instance patch target) was confirmed by reading both
   `TestCmdSessionHealth.test_health_prints_metrics` (patches
   `agent.commands.db_session_ops.DbMaintenanceService`) and `TestCmdSessionStats.test_stats_prints_counts`
   (patches `agent.commands.cmd_session.DbMaintenanceService`) side by side.
3. `cmd = _make_cmd()` (helper defined earlier in this file, used by all existing dispatch tests) is
   the correct fixture to construct the test subject; invocation is `cmd._cmd_session("rag-consistency")`
   (matching `cmd._cmd_session("stats")` / `cmd._cmd_session("health")` in the existing classes).
4. `RagMaintenanceService().consistency()` returns a `RagConsistencyResult`
   (`scripts/agent/services/models.py:165-171`, fields `is_consistent: bool`, `issues: list[str]`,
   `report: RagConsistencyReport`) — confirmed by direct read of
   `scripts/agent/services/rag_maintenance_service.py:46-54`. The mock's `.consistency.return_value`
   must be an actual `RagConsistencyResult(...)` instance (or a `MagicMock` with `.is_consistent` and
   `.issues` attributes set), matching how `TestCmdSessionStats` mocks `.stats.return_value` as an
   actual `DbStats(...)` instance rather than a bare `MagicMock`.
5. The output-printing shape depends on the paired `cmd_session.py` doc's chosen implementation
   (`self._out.write_kv([("is_consistent", str(result.is_consistent))])` followed by
   `self._out.write(issue)` per issue). Assertions should check for the substring `"is_consistent"`
   and `"True"`/`"False"` in captured stdout (mirroring `TestCmdSessionHealth`'s assertion style:
   `assert "integrity_ok" in out` / `assert "True" in out`), plus, for the inconsistent case, that
   each issue string appears verbatim in the output.

## Implementation

### Target file

`tests/test_agent_cmd_session.py`.

### Procedure

1. Add imports needed only inside test method bodies (per Assumption 1, no new module-level import):
   `from unittest.mock import patch` and `from agent.services.models import RagConsistencyResult`
   (or construct results via `MagicMock()` with explicit attributes, whichever matches the file's
   existing preference — `TestCmdSessionStats`/`TestCmdSessionHealth` both import the real dataclass
   type, e.g. `from agent.services.models import DbHealth` / `from agent.services.models import
   DbStats`, so importing `RagConsistencyResult` the same way is the consistent choice).
2. Add a new class after `TestCmdSessionStats` (or in the same relative position as the other
   `db_dispatch`-backed test classes), e.g.:
   ```python
   class TestCmdSessionRagConsistency:
       def test_rag_consistency_prints_ok_when_consistent(
           self, capsys: pytest.CaptureFixture
       ) -> None:
           from unittest.mock import patch

           from agent.services.models import RagConsistencyResult

           cmd = _make_cmd()
           with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
               mock_svc = MagicMock()
               mock_svc.consistency.return_value = RagConsistencyResult(
                   is_consistent=True, issues=[], report=MagicMock()
               )
               MockSvc.return_value = mock_svc
               cmd._cmd_session("rag-consistency")
               out = capsys.readouterr().out
               assert "is_consistent" in out
               assert "True" in out

       def test_rag_consistency_prints_issues_when_inconsistent(
           self, capsys: pytest.CaptureFixture
       ) -> None:
           from unittest.mock import patch

           from agent.services.models import RagConsistencyResult

           cmd = _make_cmd()
           with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
               mock_svc = MagicMock()
               mock_svc.consistency.return_value = RagConsistencyResult(
                   is_consistent=False,
                   issues=["[WARNING] FTS gap detected (chunks=10, fts=8, gap=2)."],
                   report=MagicMock(),
               )
               MockSvc.return_value = mock_svc
               cmd._cmd_session("rag-consistency")
               out = capsys.readouterr().out
               assert "False" in out
               assert "FTS gap detected" in out

       def test_rag_consistency_ignores_extra_args(
           self, capsys: pytest.CaptureFixture
       ) -> None:
           from unittest.mock import patch

           from agent.services.models import RagConsistencyResult

           cmd = _make_cmd()
           with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
               mock_svc = MagicMock()
               mock_svc.consistency.return_value = RagConsistencyResult(
                   is_consistent=True, issues=[], report=MagicMock()
               )
               MockSvc.return_value = mock_svc
               cmd._cmd_session("rag-consistency extra_arg")
               out = capsys.readouterr().out
               assert "is_consistent" in out
   ```
   (`RagConsistencyReport` itself is not needed for these assertions, so a plain `MagicMock()` is
   sufficient for the `report` field — matches the level of detail actually exercised by the
   equivalent `DbStats`/`DbHealth`-based tests, which likewise don't inspect every field.)
3. Verify the exact assertion strings once the paired `cmd_session.py` implementation is landed
   (the `write_kv` key name and exact issue-printing call) — adjust `"is_consistent"` / capitalization
   assertions if the landed method uses different key text.

### Method

Plain `unittest.mock.patch`-based unit tests, following the file's existing local-import,
class-per-subcommand convention. No fixtures beyond the existing `_make_cmd()` helper and `capsys`.

### Details

No new helper functions needed; `_make_cmd()` (already defined earlier in the file) is reused as-is.
No new types beyond the tests' own use of `RagConsistencyResult` (already defined in production code).

## Validation plan

| Check | Command | Target |
|---|---|---|
| New tests pass | `uv run pytest tests/test_agent_cmd_session.py -v -k RagConsistency` | all 3 new tests pass |
| Full file regression | `uv run pytest tests/test_agent_cmd_session.py -v` | all tests pass, no new failures |
| Format/lint | `uv run ruff format tests/test_agent_cmd_session.py && uv run ruff check tests/test_agent_cmd_session.py` | 0 errors |
| Type check | `uv run mypy tests/test_agent_cmd_session.py` | 0 new errors vs. baseline (mypy covers `tests/` per `rules/coding.md`) |
| Coverage of new method | `uv run coverage run -m pytest tests/test_agent_cmd_session.py && uv run coverage report --include="*/cmd_session.py"` | `_rag_consistency` lines covered |
