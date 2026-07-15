# Implementation Procedure: test_agent_cmd_session.py

## Goal

Add behavior-lock test coverage for `_cmd_session`'s 7 new subcommands (`export`,
`stats`, `health`, `checkpoint`, `vacuum`, `purge`, `recover`), rewritten (not
copy-pasted) from the corresponding session-scoped tests in `tests/test_agent_cmd_db.py`
before that file is deleted, so `/session ...` has proven parity with the removed
`/export`/`/db session ...` commands.

## Scope

### In scope
- Add `TestSessionExport` (new — markdown + json output, with/without filename;
  no direct `test_agent_cmd_db.py` predecessor since export was previously tested,
  if at all, under `/export`'s own test coverage, not `/db`'s — check for an existing
  `tests/test_cmd_rag_export.py` or similar and treat this as net-new coverage if none
  exists for `_cmd_export`'s Markdown/JSON branching).
- Add `TestSessionHealth` (2 tests, migrated from `TestDbHealth`).
- Add `TestSessionCheckpoint` (2 tests, migrated from `TestDbCheckpoint`).
- Add `TestSessionVacuum` (2 tests, migrated from `TestDbVacuum`).
- Add `TestSessionPurge` (4 tests, migrated from `TestDbPurge`).
- Add `TestSessionDbScope` (3 tests, migrated from `TestCmdDbSessionScope`).
- Add `TestSessionRecover` (2 tests: `test_recover_success`/`test_recover_failure`,
  migrated from the session half of `TestCmdDbBackwardCompat`).

### Out of scope
- The existing `TestCmdSessionList`, `TestCmdSessionDelete`, `TestCmdSessionRename`,
  `TestCmdSessionUsage`, `TestGenerateSessionTitle*`, `TestGenerateSessionTitleVisibility`
  classes (current lines 60-324) — untouched, but `TestCmdSessionUsage::test_unknown_subcommand_shows_usage`
  (current lines 176-182) should be re-verified to still pass once the fallback
  message text is extended (it asserts on `"usage" in ... .lower()`, which remains
  true as long as the word "usage"-adjacent text like "Use:" or similar convention is
  preserved — confirm exact wording against `cmd_session.py`'s updated
  `write_validation_error` call).
- Any `/db rag`-scoped test content from `test_agent_cmd_db.py` — not migrated (out
  of this plan's scope; see that file's own implementation doc).

## Assumptions

- `_make_cmd()` (current lines 29-57) already builds a fully-wired `_SessionMixin`
  test double via `object.__new__(_SessionMixin)` + manual `_ctx`/`_title_gen`
  assignment — the new tests reuse this exact helper, extending `ctx` as needed (e.g.
  none of the new DB-op branches need anything beyond what `_make_cmd()` already
  provides, since `DbSessionOps`/`_db_session_stats` only touch `DbMaintenanceService`,
  not `ctx` state directly — these must be mocked at the `DbMaintenanceService` level,
  matching the pattern presumably used in `test_agent_cmd_db.py`'s `TestDbHealth`
  etc., which should be read in full before writing the migrated versions).
- `cmd._cmd_session(...)`'s new dispatch requires `cmd._db_session_ops` (or however
  `cmd_session.py`'s implementation names the `DbSessionOps` instance) to be set — if
  `_make_cmd()` does not construct this via `_SessionMixin.__init__` (it currently
  bypasses `__init__` via `object.__new__`), the test helper must be extended to also
  set `cmd._db_session_ops = DbSessionOps(ctx, cmd._out)` (or mock it directly),
  mirroring how `cmd._title_gen` is already manually wired at line 56.

## Implementation

### Target file

`tests/test_agent_cmd_session.py`

### Procedure

1. Read `tests/test_agent_cmd_db.py`'s `TestDbHealth` (462-508), `TestDbCheckpoint`
   (508-553), `TestDbVacuum` (553-592), `TestDbPurge` (592-685), `TestCmdDbSessionScope`
   (798-840), and `TestCmdDbBackwardCompat`'s session tests (840-896) in full to
   capture exact assertions and mocking strategy (likely `unittest.mock.patch` on
   `DbMaintenanceService` or direct `MagicMock` injection — confirm which).
2. Extend `_make_cmd()` (or add a second helper, e.g. `_make_cmd_with_db_ops()`) so
   the returned `_SessionMixin` instance has a working `_db_session_ops` attribute
   (a `DbSessionOps` instance or a `MagicMock` standing in for one, matching whichever
   approach the migrated tests need).
3. Write `TestSessionExport`:
   ```python
   class TestSessionExport:
       def test_export_markdown_default(self, capsys: pytest.CaptureFixture) -> None:
           cmd = _make_cmd()
           cmd._ctx.conv.history = [{"role": "user", "content": "hi"}]
           cmd._cmd_session("export markdown")
           out = capsys.readouterr().out
           assert "# Conversation Export" in out

       def test_export_json(self, capsys: pytest.CaptureFixture) -> None:
           cmd = _make_cmd()
           cmd._ctx.conv.history = [{"role": "user", "content": "hi"}]
           cmd._cmd_session("export json")
           out = capsys.readouterr().out
           assert '"role"' in out

       def test_export_to_file(self, tmp_path: Path) -> None:
           cmd = _make_cmd()
           cmd._ctx.conv.history = [{"role": "user", "content": "hi"}]
           outfile = tmp_path / "export.md"
           cmd._cmd_session(f"export markdown {outfile}")
           assert outfile.exists()
   ```
   (Adjust for whatever mocking `render_export`/`write_export` actually requires once
   `cmd_session.py`'s real implementation is in place — these are illustrative, not
   final.)
4. Write `TestSessionHealth`, `TestSessionCheckpoint`, `TestSessionVacuum`,
   `TestSessionPurge`, `TestSessionDbScope`, `TestSessionRecover` as rewritten
   equivalents of their `test_agent_cmd_db.py` sources, each calling
   `cmd._cmd_session("health")`, `cmd._cmd_session("checkpoint FULL")`,
   `cmd._cmd_session("vacuum")`, `cmd._cmd_session("purge --max-sessions 5")`, etc.,
   with the same mock-target assertions as the originals (e.g. asserting
   `DbMaintenanceService().health.assert_called_once()` or equivalent, translated to
   whatever mocking seam `cmd_session.py`'s implementation exposes).
5. Diff old vs. new assertions line-by-line before `test_agent_cmd_db.py` is deleted
   (per that file's own Risk mitigation) — run both test files side-by-side once to
   confirm behavioral equivalence.

### Method

Manual, behavior-preserving rewrite of 15 test functions plus 3 new export tests,
appended to the existing `tests/test_agent_cmd_session.py` using its established
`_make_cmd()`/`capsys`/`pytest.CaptureFixture` conventions. No existing test in this
file is modified except possibly `TestCmdSessionUsage`'s usage-message assertion if
the fallback wording changes materially.

### Details

- Import `Path` from `pathlib` if `TestSessionExport`'s file-write test is added
  (not currently imported in this file).
- Keep class/method naming consistent with the file's existing style
  (`TestCmdSession<Verb>` prefix pattern is used for the pre-existing classes, e.g.
  `TestCmdSessionList`/`TestCmdSessionDelete`/`TestCmdSessionRename`; consider
  `TestCmdSessionExport`/`TestCmdSessionHealth`/etc. instead of `TestSession*` to
  match the established convention in this specific file — reconcile the naming
  sketch above with that convention before finalizing).

## Validation plan

- `uv run pytest tests/test_agent_cmd_session.py -v` — all new and existing tests
  pass.
- Cross-check: every assertion present in the corresponding `test_agent_cmd_db.py`
  class (health, checkpoint, vacuum, purge, session-scope, backward-compat) has a
  matching assertion in the new class, confirmed by manual line-by-line diff before
  `test_agent_cmd_db.py` is deleted.
- `uv run coverage run -m pytest tests/test_agent_cmd_session.py && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`
  — new `cmd_session.py` branches (export + 6 DB ops) are covered at ≥90%.
- `uv run mypy tests/test_agent_cmd_session.py` — no new type errors.
- Manual: run the new tests once **before** deleting `test_agent_cmd_db.py`, to catch
  regressions while both the old and new coverage exist side-by-side.
