# Implementation: tests/integration/conftest.py (add `hanging_stdio_process` and `corrupt_wal_db` fixtures)

Source plan: `plans/20260716-135105_plan.md`

Note: this is a distinct change from the original conftest-authoring
implementation doc (`implementations/done/20260625-105400_conftest_integration.py.md`,
which produced the 4 fixtures currently in `tests/integration/conftest.py`:
`stdio_echo_server`, `tmp_sqlite_db`, `make_llm_stream`/`hold_write_lock`).
This doc adds 2 new fixtures alongside them — the 4 existing fixtures are
not modified.

## Goal

Add `hanging_stdio_process` (a proper pytest fixture wrapping the
Example-Test-Skeleton pattern used ad hoc in
`tests/integration/test_mcp_transport_crash.py`) and `corrupt_wal_db` (a
fixture producing a byte-truncated, corrupted WAL-mode SQLite file) to
`tests/integration/conftest.py`, for use by the new
`test_session_recovery.py` test file (and optionally by
`test_mcp_transport_crash.py` if refactored to use the fixture instead of
its local helper).

## Scope

**In:**
- Add `hanging_stdio_process` fixture — same subprocess-hang pattern as
  `_hanging_stdio_server()` in the source plan's Example Test Skeleton,
  but as a proper `@pytest.fixture` with `yield` + teardown (kill + reap),
  matching the existing `stdio_echo_server` fixture's teardown style
  (lines 32-35 of the current `conftest.py`).
- Add `corrupt_wal_db` fixture — builds a valid WAL-mode session-schema
  SQLite DB (reusing the exact schema-building approach already
  demonstrated in `tests/integration/test_session_sqlite.py`'s
  `_build_session_memory_db()` helper), then byte-truncates it to produce
  a file that fails `PRAGMA integrity_check` without failing
  `sqlite3.connect()` itself outright (resolves the source plan's UNK-02
  empirically during this same implementation step).

**Out:**
- The 4 existing fixtures (`stdio_echo_server`, `tmp_sqlite_db`,
  `make_llm_stream`, `hold_write_lock`) — do not modify their bodies,
  signatures, or docstrings.
- `tests/integration/test_session_sqlite.py`'s own local helpers
  (`_init_wal_db`, `_build_session_memory_db`, `_immediate`) — these remain
  local to that file; `corrupt_wal_db` may replicate
  `_build_session_memory_db`'s schema-building call but must not import
  private helpers across test modules (Python test-file-to-test-file
  imports of underscore-prefixed helpers are fragile; replicate the
  schema-building call directly using `db.schema_sql.build_session_schema_sql`,
  matching how `_build_session_memory_db` itself does it, per direct read).

## Assumptions

1. `tests/integration/test_session_sqlite.py`'s `_build_session_memory_db()`
   (lines 39-52) already demonstrates the exact schema-building call
   needed: `conn.executescript(build_session_schema_sql(4))` wrapped in a
   try/except for the optional `memories_vec` table (sqlite-vec extension
   may be absent) — `corrupt_wal_db` should build its base (pre-corruption)
   DB the same way, to produce a realistic session-schema file rather than
   a toy 2-table schema.
2. UNK-02 (source plan) — the exact truncation offset that reliably
   produces an `integrity_check` failure without a `sqlite3.connect()`
   failure — must be resolved empirically while writing this fixture: a
   common, reliable technique is to write valid data, commit, then
   truncate the file to roughly half its size (`f.seek(size // 2);
   f.truncate()`), which corrupts b-tree page structure without touching
   the SQLite header magic bytes (first 16 bytes) that `sqlite3.connect()`
   itself checks. Confirm this technique empirically (open the truncated
   file with `sqlite3.connect()` — must succeed; then run
   `PRAGMA integrity_check` — must return a non-`"ok"` row) before
   finalizing the fixture; if the chosen offset instead causes
   `sqlite3.connect()` to fail, adjust the offset (e.g. truncate less
   aggressively, preserving more of the header/schema pages) until the
   target failure mode (connect succeeds, integrity_check fails) is
   reproduced.
3. Both new fixtures are function-scoped (pytest's default) — no
   session-scoped state is needed or desired, since each test using them
   should get an independent subprocess/file.

## Implementation

### Target file

`tests/integration/conftest.py`

### Procedure

1. Open `tests/integration/conftest.py`.
2. After the existing `hold_write_lock()` function (the file's last
   definition), add the `hanging_stdio_process` fixture:
   ```python
   @pytest.fixture
   async def hanging_stdio_process():
       """Subprocess that reads one line from stdin, then sleeps forever.

       Used to test bounded-timeout reads against a wedged MCP server
       subprocess (see tests/integration/test_mcp_transport_crash.py).
       """
       script = (
           "import sys, time\n"
           "sys.stdin.readline()\n"
           "time.sleep(3600)\n"
       )
       proc = await asyncio.create_subprocess_exec(
           "python",
           "-c",
           script,
           stdin=asyncio.subprocess.PIPE,
           stdout=asyncio.subprocess.PIPE,
       )
       yield proc
       if proc.returncode is None:
           proc.kill()
           await proc.wait()
   ```
3. Add the `corrupt_wal_db` fixture immediately after:
   ```python
   @pytest.fixture
   def corrupt_wal_db(tmp_path: Path) -> str:
       """A WAL-mode session-schema SQLite DB, byte-truncated to fail
       PRAGMA integrity_check while still opening successfully via
       sqlite3.connect() (header intact, b-tree pages corrupted).

       Used by tests/integration/test_session_recovery.py.
       """
       from db.schema_sql import build_session_schema_sql

       db_path = str(tmp_path / "corrupt.sqlite")
       conn = sqlite3.connect(db_path)
       conn.execute("PRAGMA journal_mode=WAL")
       try:
           conn.executescript(build_session_schema_sql(4))
       except Exception:
           pass  # memories_vec may be unavailable without sqlite-vec; ignore
       conn.execute(
           "INSERT INTO sessions (session_id) VALUES (1)"
       ) if _has_table(conn, "sessions") else None
       conn.commit()
       conn.close()

       # Byte-level truncation: corrupts b-tree pages while preserving the
       # SQLite header (first 16 bytes), so sqlite3.connect() still succeeds
       # but PRAGMA integrity_check fails. Offset confirmed empirically
       # during implementation (see plan UNK-02 resolution).
       size = Path(db_path).stat().st_size
       with open(db_path, "r+b") as f:
           f.seek(size // 2)
           f.truncate()

       return db_path


   def _has_table(conn: sqlite3.Connection, name: str) -> bool:
       row = conn.execute(
           "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
       ).fetchone()
       return row is not None
   ```
   (Adjust the truncation offset/technique based on the empirical
   confirmation in Assumption 2 — the `size // 2` starting point is a
   reasonable default, not a guaranteed-correct value; verify before
   finalizing.)
4. Confirm no new top-level imports are needed beyond what `conftest.py`
   already imports (`asyncio`, `sqlite3`, `Path` are already imported per
   the existing file's header) — `db.schema_sql.build_session_schema_sql`
   is imported locally inside the fixture, matching
   `_build_session_memory_db()`'s own local-import style in
   `test_session_sqlite.py`.

### Method

Two new fixture functions appended to the end of the file — no changes to
any existing fixture, import, or module-level code above them.

### Details

- Do not add a `conftest.py`-level fixture that duplicates
  `test_session_sqlite.py`'s local `_init_wal_db`/`_immediate` helpers —
  those remain file-local; only the new `corrupt_wal_db` fixture is shared
  via `conftest.py`, since it is the one needed by a different file
  (`test_session_recovery.py`).
- Keep both new fixtures' docstrings pointing at the specific test file
  that consumes them, matching this file's existing documentation style
  (the module docstring already says "Shared fixtures for integration
  tests").

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Fixtures load without error | `uv run pytest tests/integration/ --collect-only -q` | no collection errors, both new fixtures discoverable |
| `corrupt_wal_db` produces the target failure mode | `PYTHONPATH=scripts uv run python -c "import sqlite3; c=sqlite3.connect('<path>'); print(c.execute('PRAGMA integrity_check').fetchall())"` (run manually against a fixture-produced file during implementation) | `sqlite3.connect()` succeeds; `integrity_check` returns a row other than `[('ok',)]` |
| `hanging_stdio_process` teardown reaps cleanly | `uv run pytest tests/integration/test_mcp_transport_crash.py -v` (once that file uses the fixture) | no zombie process after the test session |
| Existing 4 fixtures unaffected | `uv run pytest tests/integration/ -v` (all existing 44 tests) | all pass unchanged |
| Lint | `uv run ruff check tests/integration/conftest.py` | 0 errors |
| Type check | `uv run mypy tests/integration/conftest.py` | no new errors |
