# Implementation Procedure — tests/agent/test_agent_session.py

## Goal

Add regression coverage for the `start()` fallback fix: a schema-missing
`OperationalError` reaching the fallback converts to `SchemaMissingError`, a non-schema
`OperationalError` still propagates, and a real unseeded DB file converts end-to-end
(REQ-001, REQ-002, REQ-003, REQ-005).

## Scope

- Append a new `TestStartSchemaMissingFallback (new)` class (3 tests) to
  `tests/agent/test_agent_session.py`, after `TestStart` (line 152 block).
- No other file is modified by this procedure (the fix under test is
  `implementations/20261025-133350_01_scripts_agent_session.py.md`).

## Assumptions

- `SQLiteHelper._execute_with_retry` calls `datetime.now()` inside the query path, so
  monkeypatching `datetime.now` to raise `sqlite3.OperationalError` injects an error at
  query time after the pre-flight has already succeeded — the accepted neutralization
  idiom precedent is `tests/agent/test_db_init.py:180-188`.
- The `session` fixture (line 130) seeds `_SCHEMA_SQL`, so the pre-flight check passes
  and the injected error lands in the `except sqlite3.OperationalError` handler.
- The dev venv runs Python 3.14 (verified: 3.14.7), so real sqlite errors carry
  `sqlite_errorcode` = 1 / `sqlite_errorname (new)` = `'SQLITE_ERROR'` (verified at HEAD).
- Caveat (Needs confirmation, non-blocking): binding a real `SQLiteHelper` to a temp
  `db_path` may attempt the sqlite-vec extension load (`_load_vec_extension` catches
  `OperationalError`, so it is safe); if it causes environment friction, fall back to
  the fake-helper injection style (tests A/B) which already covers the same matcher.
- The new test method in C uses the import statement
  `from db.helper import SQLiteHelper` (new) that `tests/agent/commands/test_memory_data_ops.py:20`
  also uses (verified present in that source).

## Design decisions

- Inject at query time via the `datetime.now` idiom rather than restructuring `start()`
  for testability — zero production surface change (plan's "if that is impractical"
  clause endorses the monkeypatch pattern).
- Message chosen for the conversion test is the real string `"no such table: sessions"`
  so the message leg of the gate is exercised; the propagation test uses
  `"table sessions is locked"` (code-less plain error) to pin REQ-005.
- Keep every existing test in the file byte-identical; the new class is pure addition.

## Alternatives considered

- Patch `SQLiteHelper.execute` directly to raise: rejected — bypasses the real sqlite3
  error object the fix keys off (`sqlite_errorcode`), weakening REQ-001 coverage.
- Trigger a genuine post-preflight failure with DB locks/triggers: rejected — flaky
  across environments.
- Add the tests to `test_repl.py`: rejected — REPL-level characterization already exists
  there (`:988-999`); unit coverage belongs next to `TestStart`.

## Implementation
### Target file
`tests/agent/test_agent_session.py`

### Procedure
Append after the `TestStart` class a new class with three tests.

### Method

```python
class TestStartSchemaMissingFallback:                     # (new)
    def test_fallback_converts_schema_error_after_preflight(self, session, monkeypatch):  # (new)
        from datetime import datetime

        def boom(*_):
            raise sqlite3.OperationalError("no such table: sessions")

        monkeypatch.setattr(datetime, "now", boom)
        with pytest.raises(SchemaMissingError, match="Session schema missing"):
            session.start()

    def test_non_schema_operational_error_propagates(self, session, monkeypatch):  # (new)
        from datetime import datetime

        def boom(*_):
            raise sqlite3.OperationalError("table sessions is locked")

        monkeypatch.setattr(datetime, "now", boom)
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            session.start()

    def test_real_db_missing_schema_raises_schema_missing(self, tmp_path):  # (new)
        # Method body starts with the import described above:
        #   from db.helper import SQLiteHelper
        with patch("agent.session.SQLiteHelper",
                   side_effect=lambda _name: SQLiteHelper("session",
                       db_path=str(tmp_path / "unseeded.db"))):
            s = AgentSession()
            with pytest.raises(SchemaMissingError, match="Session schema missing"):
                s.start()
```

(`SchemaMissingError` is already imported in this module's import block via
`agent.session`; confirm the name is importable from `agent.session` and add it to the
existing `from agent.session import AgentSession` line if needed.)

### Details
- Test A/B rely on the `session` fixture patching `agent.session.SQLiteHelper` — with
  the fixture they must NOT add a conflicting patch; the `datetime.now` patch is the
  only extra.
- Test C must NOT request the `session` fixture (its autouse-safe patches only apply
  when the fixture is requested); it constructs its own patch context with a real
  `SQLiteHelper` bound to an unseeded temp file (`db_path` bypass precedent:
  `tests/agent/commands/test_memory_data_ops.py:545`).
- `monkeypatch` restores `datetime.now` automatically at test end; keep patches inside
  each test function.
- Mark new symbols `(new)`: `TestStartSchemaMissingFallback (new)`, its three test
  methods `(new)`.

## Compatibility considerations

- All existing tests in the file (behavior locks from the 2026-09-09 procedure) stay
  unchanged and must pass.
- `test_repl.py:988-999` characterizes the REPL behavior the fix must preserve; it is
  not edited here.
- Tests A/B work on any Python (plain `OperationalError` injected); test C exercises
  the attribute legs on Python >= 3.11 (prod 3.13 / dev 3.14 both qualify).

## Security considerations

N/A: tests use in-memory and `tmp_path` DBs only; no production DB, config, or network
access.

## Rollback considerations

Delete the appended class (one contiguous block); no other test or fixture is touched.

## Validation plan

- Phase 1 gate: `uv run pytest tests/agent/test_agent_session.py tests/agent/test_repl.py -q`
  (125 collected at HEAD; 128 after this procedure).
- Red->green verification: run the new tests against the unfixed `session.py` — tests
  A and C must fail; apply procedure 01 — all pass. Confirm once and record.
- Full sequence per `rules/toolchain.md` (Step 3 gate of the plan):
  `uv run pytest tests/agent/ -q`, `uv run lint-imports`, `uv run ruff check .`,
  `uv run bandit -c pyproject.toml -r .`.

## Completion criteria

- AC-001: test A and test C green with the fix (fallback converts, real DB converts).
- AC-002: test B green (non-schema `OperationalError` propagates, not converted).
- AC-003: all pre-existing tests in the file plus `test_repl.py` pass unmodified.

## Out of Scope

- The production fix itself (procedure 01).
- `test_repl.py` changes (existing characterization is sufficient).
- `test_db_init.py` (pattern source only, not edited).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append `TestStartSchemaMissingFallback (new)` with the three tests | Pending | — | — | procedure 01 must land first |
| 2 | Run the Phase 1 gate test set | Pending | — | — | |
| 3 | Confirm red->green transition against unfixed/fixed `session.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-005
- **Source issue**: `issues/done/20261025-115550_sess002_unreachable-sqlite-error-fallback.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123145_sess002_unreachable-sqlite-error-fallback.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-133350
- **Related target files**: tests/agent/test_agent_session.py
