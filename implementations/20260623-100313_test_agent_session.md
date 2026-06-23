## Goal

Fix `TestSessionIdConcurrency` in `tests/test_agent_session.py` so that `AgentSession.start()` is called inside `ThreadPoolExecutor` rather than sequentially after it exits, enabling genuine concurrent session ID generation to be tested.

## Scope

**In-Scope:**
- `tests/test_agent_session.py` — modify two test methods in `TestSessionIdConcurrency`:
  - `test_concurrent_starts_produce_unique_ids`
  - `test_concurrent_starts_all_persisted`
- Add a module-local helper `_make_and_start` inside each test (or as a shared closure) that combines `AgentSession()` construction and `start()` into one callable for `executor.map`

**Out-of-Scope:**
- `scripts/agent/session.py` — no production code changes
- Any other test class in the file
- DB schema or configuration files

## Assumptions

1. The three `patch` context managers (`agent.session.SQLiteHelper`, `agent.session_message_repo.SQLiteHelper`, `agent.note_repo.SQLiteHelper`) wrap the entire `ThreadPoolExecutor` block, so they remain active when `start()` executes inside worker threads.
2. `sqlite3.connect(":memory:", check_same_thread=False, timeout=5)` serializes concurrent writes via SQLite's internal mutex; no test-level lock is needed.
3. `cur.lastrowid` is cursor-local and not overwritten by concurrent INSERTs from other threads.
4. `_FakeSQLiteHelper` has no thread-safety issues because `check_same_thread=False` is already set on the shared connection.
5. Using a named inner function `_make_and_start` avoids Python closure-capture issues that can occur with `lambda` in `executor.map`.

## Implementation

### Target file
`tests/test_agent_session.py`

### Procedure

1. In `test_concurrent_starts_produce_unique_ids` (line ~399):
   - Define `_make_and_start()` inside the `with patch(...)` block.
   - Replace `executor.map(lambda _: AgentSession(), range(8))` with `executor.map(lambda _: _make_and_start(), range(8))`.
   - Remove the sequential `for s in results: s.start(); sessions.append(s)` loop.
   - Replace it with `sessions = list(results)` (executor already returns started sessions).

2. Apply the identical change to `test_concurrent_starts_all_persisted` (line ~425).

3. Run validation commands.

### Method

Both tests follow the same transformation pattern:

**Before (both tests, current lines 399–403 / 425–429):**
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(lambda _: AgentSession(), range(8)))
for s in results:          # sequential — not concurrent
    s.start()
    sessions.append(s)
```

**After:**
```python
def _make_and_start(_: int = 0) -> AgentSession:
    s = AgentSession()
    s.start()
    return s

with ThreadPoolExecutor(max_workers=4) as executor:
    sessions = list(executor.map(_make_and_start, range(8)))
```

### Details

#### test_concurrent_starts_produce_unique_ids — full replacement

```python
def test_concurrent_starts_produce_unique_ids(self) -> None:
    conn = sqlite3.connect(":memory:", check_same_thread=False, timeout=5)
    conn.executescript(_SCHEMA_SQL)
    conn.commit()

    def _make(target: str = "rag") -> _FakeSQLiteHelper:  # noqa: ARG001
        return _FakeSQLiteHelper(conn)

    with (
        patch("agent.session.SQLiteHelper", side_effect=_make),
        patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
        patch("agent.note_repo.SQLiteHelper", side_effect=_make),
    ):
        from concurrent.futures import ThreadPoolExecutor

        def _make_and_start(_: int = 0) -> AgentSession:
            s = AgentSession()
            s.start()
            return s

        with ThreadPoolExecutor(max_workers=4) as executor:
            sessions = list(executor.map(_make_and_start, range(8)))

    ids = [s.session_id for s in sessions]
    assert all(isinstance(sid, int) for sid in ids)
    assert len(set(ids)) == 8
```

Key changes:
- `_make_and_start` defined inside `with patch(...)` so patches are active during `start()` in worker threads
- `executor.map` now calls both construction and `start()` concurrently
- Sequential `for` loop removed; `sessions` populated directly from executor results

#### test_concurrent_starts_all_persisted — full replacement

```python
def test_concurrent_starts_all_persisted(self) -> None:
    conn = sqlite3.connect(":memory:", check_same_thread=False, timeout=5)
    conn.executescript(_SCHEMA_SQL)
    conn.commit()

    def _make(target: str = "rag") -> _FakeSQLiteHelper:  # noqa: ARG001
        return _FakeSQLiteHelper(conn)

    with (
        patch("agent.session.SQLiteHelper", side_effect=_make),
        patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
        patch("agent.note_repo.SQLiteHelper", side_effect=_make),
    ):
        from concurrent.futures import ThreadPoolExecutor

        def _make_and_start(_: int = 0) -> AgentSession:
            s = AgentSession()
            s.start()
            return s

        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(_make_and_start, range(8)))

    count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    assert count == 8
```

Key changes:
- Same `_make_and_start` pattern as the first test
- Return value of `executor.map` is consumed but not stored (only the DB count assertion matters)

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Run target tests | `uv run pytest tests/test_agent_session.py::TestSessionIdConcurrency -v` | 2 tests PASSED |
| Full file regression | `uv run pytest tests/test_agent_session.py -v` | All 37 tests PASSED |
| Type check | `uv run mypy tests/test_agent_session.py --ignore-missing-imports` | No new errors |
| Lint | `uv run ruff check tests/test_agent_session.py` | 0 errors |
| Architecture | `uv run lint-imports` | 0 violations |
