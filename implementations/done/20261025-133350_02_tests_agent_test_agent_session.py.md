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

- (Corrected 2026-10-25 in adversarial verification) The `datetime.now` injection idiom
  does not hold at HEAD: `scripts/db/helper.py` contains no `datetime` usage and
  `tests/agent/test_db_init.py` does not exist. Injection instead goes through a
  `_FakeSQLiteHelper` subclass that lets the pre-flight `SELECT sqlite_master` pass and
  raises the injected error only on the `INSERT INTO sessions` call. The
  conversion-test error is a genuine `sqlite3.OperationalError` produced by a real
  failing query, so it carries `sqlite_errorcode` / `sqlite_errorname`; the
  propagation test uses a manually constructed `OperationalError` (no attributes).
- `_FakeSQLiteHelper.execute` lazily seeds `_SCHEMA_SQL` into its backing connection,
  so in tests A/B the pre-flight check passes against the seeded in-memory DB and the
  injected error lands in the `except sqlite3.OperationalError` handler.
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

- Inject at the helper boundary via a `_FakeSQLiteHelper` subclass that fails only the
  `INSERT INTO sessions` call rather than restructuring `start()` for testability —
  zero production surface change; the injected conversion error is a genuine sqlite3
  error object, preserving REQ-001 coverage.
- Message chosen for the conversion test is the real string `"no such table: sessions"`
  so the message leg of the gate is exercised; the propagation test uses
  `"table sessions is locked"` (code-less plain error) to pin REQ-005.
- Keep every existing test in the file byte-identical; the new class is pure addition.

## Alternatives considered

- Inject a synthetic plain `OperationalError("no such table: sessions")`: rejected —
  bypasses the `sqlite_errorcode` legs the fix keys off; only the message leg would be
  covered. The corrected design generates the conversion error from a real failing
  query instead.
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
class TestStartSchemaMissingFallback:
    """Regression coverage for start()'s OperationalError fallback."""

    @staticmethod
    def _real_no_such_table_error() -> sqlite3.OperationalError:
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute("INSERT INTO sessions (title) VALUES (NULL)")
        except sqlite3.OperationalError as err:
            return err  # genuine object: carries sqlite_errorcode / sqlite_errorname
        finally:
            conn.close()
        raise AssertionError("expected OperationalError was not raised")

    class _ExplodingHelper(_FakeSQLiteHelper):
        """Fake helper whose sessions INSERT raises a stored error."""

        injected: sqlite3.OperationalError

        def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
            if "INSERT INTO sessions" in sql:
                raise self.injected
            return super().execute(sql, params)

    def _make_exploding(self, error: sqlite3.OperationalError):
        conn = sqlite3.connect(":memory:")

        def _make(name: str = "session") -> "TestStartSchemaMissingFallback._ExplodingHelper":
            helper = TestStartSchemaMissingFallback._ExplodingHelper(conn)
            helper.injected = error
            return helper

        return _make

    def test_fallback_converts_schema_error_after_preflight(self):
        with patch(
            "agent.session.SQLiteHelper",
            side_effect=self._make_exploding(self._real_no_such_table_error()),
        ):
            s = AgentSession()
            with pytest.raises(SchemaMissingError, match="Session schema missing"):
                s.start()

    def test_non_schema_operational_error_propagates(self):
        with patch(
            "agent.session.SQLiteHelper",
            side_effect=self._make_exploding(
                sqlite3.OperationalError("table sessions is locked")
            ),
        ):
            s = AgentSession()
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                s.start()

    def test_real_db_missing_schema_raises_schema_missing(self, tmp_path):
        from db.helper import SQLiteHelper

        with patch(
            "agent.session.SQLiteHelper",
            side_effect=lambda _name: SQLiteHelper(
                "session", db_path=str(tmp_path / "unseeded.db")
            ),
        ):
            s = AgentSession()
            with pytest.raises(SchemaMissingError, match="Session schema missing"):
                s.start()
```

(`SchemaMissingError` is already imported in this module's import block via
`agent.session`; confirm the name is importable from `agent.session` and add it to the
existing `from agent.session import AgentSession` line if needed.)

### Details
- Tests A/B do NOT request the `session` fixture; they build their own
  `patch("agent.session.SQLiteHelper", ...)` context backed by a fresh in-memory
  connection seeded lazily by `_FakeSQLiteHelper` (the pre-flight passes there), and
  fail only the `INSERT INTO sessions` call.
- Test C must NOT request the `session` fixture; it constructs its own patch context
  with a real `SQLiteHelper` bound to an unseeded temp file (`db_path` bypass
  precedent: `tests/agent/commands/test_memory_data_ops.py:545`).
- `patch` contexts are per-test-function; no global state is left behind (the autouse
  `reset_fake_helper` fixture also resets the lazy-seeding ledger each test).
- `SchemaMissingError` must be added to the existing
  `from agent.session import AgentSession` import line.
- Mark new symbols `(new)`: `TestStartSchemaMissingFallback (new)`, its three test
  methods `(new)`, `_real_no_such_table_error (new)`, `_ExplodingHelper (new)`,
  `_make_exploding (new)`.

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
- Red->green verification: run the new tests against the unfixed `session.py` — test A
  must fail (the dead 1017 check re-raises the injected real error). Tests B and C are
  green before and after the fix (B pins propagation; C lands on the pre-flight arm,
  which predates the fix), so the red->green delta is test A only. Confirm once and
  record.
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
| 1 | Append `TestStartSchemaMissingFallback (new)` with the three tests | Completed | 20261025-175826 | 20261025-175826 | procedure 01 must land first |
| 2 | Run the Phase 1 gate test set | Completed | 20261025-175826 | 20261025-175826 |  |
| 3 | Confirm red->green transition against unfixed/fixed `session.py` | Completed | 20261025-175826 | 20261025-175826 | red->green confirmed: A fails unfixed, all 128 gate tests green fixed |

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