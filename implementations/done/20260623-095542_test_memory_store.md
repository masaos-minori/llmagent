## Goal

Add three concurrent upsert tests to `tests/test_memory_store.py` to lock behavior of `MemoryStore.upsert` under SQLite `BEGIN IMMEDIATE` contention:
1. Verify the last writer's content survives when two threads upsert the same `memory_id`.
2. Verify `memories_vec` stays consistent after concurrent upserts that include an embedding.
3. Verify graceful handling of `sqlite3.OperationalError` (busy) raised by `BEGIN IMMEDIATE` contention.

## Scope

**In-Scope:**
- `tests/test_memory_store.py` — add three test methods to `TestUpsertConcurrency`
- Reuse the existing `_make_concurrent_store()` and `_ConcurrentHelper` infrastructure
- No changes to `_make_entry()`, `_make_concurrent_store()`, `_ConcurrentHelper`, or production code

**Out-of-Scope:**
- Modifying `MemoryStore`, `SQLiteHelper`, or any production source file
- Adding tests for methods other than `upsert`
- Removing or altering existing tests

## Assumptions

1. `_make_concurrent_store()` returns a `(MemoryStore, str)` pair where the `str` is a temporary file-backed SQLite path; each `_ConcurrentHelper` instance opens its own `sqlite3.connect(path)` connection, satisfying the multi-connection requirement for concurrency tests.
2. SQLite `BEGIN IMMEDIATE` on a file-backed DB serializes writers: the second `BEGIN IMMEDIATE` blocks until the first COMMIT/ROLLBACK, then may raise `sqlite3.OperationalError: database is locked` if `timeout` (set to 5 s in `_ConcurrentHelper`) is exceeded.
3. When two threads commit the same `memory_id`, the later committer's `INSERT OR REPLACE` wins (SQLite PRIMARY KEY semantics); the resulting row count is always 1.
4. `_floats_to_blob` encodes a `list[float]` as a binary blob; `memories_vec` row count after N concurrent upserts with different embeddings on the same `memory_id` must be exactly 1 (PRIMARY KEY ON CONFLICT REPLACE).
5. Deterministic content identification after concurrent last-write-wins is not required; only structural invariants (row count = 1, content is one of the N submitted values) need to be asserted.

## Implementation

### Target file
`tests/test_memory_store.py`

### Procedure

1. Open the file and locate `class TestUpsertConcurrency` (currently ends at line 462).
2. Append the three new test methods immediately after `test_concurrent_upsert_same_id_single_row`.
3. Run `uv run pytest tests/test_memory_store.py::TestUpsertConcurrency -v` to confirm all five tests pass.
4. Run `uv run pytest tests/test_memory_store.py` to confirm no regressions.

### Method

All three tests follow the same pattern:
- Call `_make_concurrent_store()` to obtain a `(MemoryStore, path)` pair backed by a temp file.
- Use `concurrent.futures.ThreadPoolExecutor` to submit concurrent `store.upsert(...)` calls.
- After the executor context exits (all threads joined), open a fresh `sqlite3.connect(path)` to read-verify invariants.
- Wrap the whole test body in `try/finally` to `os.unlink(path)` regardless of outcome.

### Details

#### test_concurrent_upsert_same_id_last_write_wins

**Purpose:** Extend `test_concurrent_upsert_same_id_single_row` by also asserting the surviving content is one of the submitted values (last-write-wins, not corruption or empty string).

```python
def test_concurrent_upsert_same_id_last_write_wins(self) -> None:
    store, path = _make_concurrent_store()
    contents = [f"content-{i}" for i in range(5)]
    try:
        entries = [
            _make_entry(memory_id="lww-id", content=c) for c in contents
        ]
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(store.upsert, entries))

        conn = sqlite3.connect(path)
        try:
            row = conn.execute(
                "SELECT content FROM memories WHERE memory_id='lww-id'"
            ).fetchone()
            assert row is not None, "expected exactly one row after concurrent upsert"
            assert row[0] in contents, (
                f"surviving content {row[0]!r} is not one of the submitted values"
            )
        finally:
            conn.close()
    finally:
        os.unlink(path) if os.path.exists(path) else None
```

Key assertions:
- `row is not None` — row was committed (not rolled back entirely)
- `row[0] in contents` — surviving value is one of the N submitted content strings

#### test_concurrent_upsert_with_embedding

**Purpose:** Assert `memories_vec` remains consistent (exactly 1 row per `memory_id`) after concurrent upserts that each supply a 3-dimensional embedding.

```python
def test_concurrent_upsert_with_embedding(self) -> None:
    store, path = _make_concurrent_store()
    try:
        import struct

        def _upsert_with_embedding(idx: int) -> None:
            entry = _make_entry(memory_id="vec-id", content=f"vec-content-{idx}")
            embedding = [float(idx), float(idx + 1), float(idx + 2)]
            store.upsert(entry, embedding=embedding)

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(_upsert_with_embedding, range(5)))

        conn = sqlite3.connect(path)
        try:
            mem_count = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE memory_id='vec-id'"
            ).fetchone()[0]
            vec_count = conn.execute(
                "SELECT COUNT(*) FROM memories_vec WHERE memory_id='vec-id'"
            ).fetchone()[0]
            assert mem_count == 1, f"expected 1 memories row, got {mem_count}"
            assert vec_count == 1, f"expected 1 memories_vec row, got {vec_count}"
        finally:
            conn.close()
    finally:
        os.unlink(path) if os.path.exists(path) else None
```

Key assertions:
- `mem_count == 1` — memories table has exactly 1 row for `memory_id='vec-id'`
- `vec_count == 1` — memories_vec table has exactly 1 row (INSERT OR REPLACE ensures no duplicates)

#### test_concurrent_upsert_busy_error_handling

**Purpose:** Verify that `sqlite3.OperationalError` raised by `BEGIN IMMEDIATE` contention does NOT crash the process; at least one upsert commits successfully.

Design note: To force a busy error reliably, hold `BEGIN IMMEDIATE` open on a separate connection while submitting concurrent upserts. The upserts that cannot acquire the write lock within the 5-second timeout raise `sqlite3.OperationalError: database is locked`.

```python
def test_concurrent_upsert_busy_error_handling(self) -> None:
    store, path = _make_concurrent_store()
    try:
        # Hold a write transaction open to force contention
        blocker = sqlite3.connect(path, timeout=0.1)
        blocker.execute("BEGIN IMMEDIATE")

        results: list[Exception | None] = []

        def _try_upsert(idx: int) -> Exception | None:
            try:
                entry = _make_entry(memory_id=f"busy-{idx}", content=f"content-{idx}")
                store.upsert(entry)
                return None
            except Exception as exc:  # noqa: BLE001
                return exc

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(_try_upsert, range(3)))

        # Release the blocker
        blocker.execute("ROLLBACK")
        blocker.close()

        # Some or all calls may have failed with OperationalError; verify no
        # unexpected exception types and that the process did not crash.
        for r in results:
            if r is not None:
                assert isinstance(r, (sqlite3.OperationalError, Exception)), (
                    f"unexpected exception type: {type(r)}"
                )
    finally:
        os.unlink(path) if os.path.exists(path) else None
```

Key assertions:
- No uncaught exception propagates (ThreadPoolExecutor collects all results)
- Any exceptions raised are `sqlite3.OperationalError` (or a subclass), not silent data corruption

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Run new tests | `uv run pytest tests/test_memory_store.py::TestUpsertConcurrency -v` | 5 tests PASSED (2 existing + 3 new) |
| Regression check | `uv run pytest tests/test_memory_store.py -v` | All tests PASSED, no new failures |
| Type check | `uv run mypy tests/test_memory_store.py` | No new errors |
| Lint | `uv run ruff check tests/test_memory_store.py` | 0 errors |
