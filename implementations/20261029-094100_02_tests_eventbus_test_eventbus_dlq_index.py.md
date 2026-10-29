## Goal

Rewrite `tests/eventbus/test_eventbus_dlq_index.py` so it never runs DDL, asserts the
canonical DLQ index *shape* (failing when one is dropped in a throwaway copy), asserts the
query *plan* over the exact SQL `fetch_dlq()`/`count_dlq()` execute, and fixes the data
setup to publish with a publisher-role token and assert success.

## Scope

Test-only edit to `tests/eventbus/test_eventbus_dlq_index.py`. No production code, no docs.

## Assumptions

- Canonical indexes are `idx_events_dlq_at` and `idx_events_dlq_seq` (`scripts/eventbus/schema.sql`;
  cited, not a modification target).
- Verified planner facts (project SQLite, plan cycle 2026-10-28): `count_dlq`'s statement
  plans as `SEARCH events USING COVERING INDEX idx_events_dlq_seq`; `fetch_dlq`'s statement
  (`... ORDER BY seq [LIMIT ? OFFSET ?]`) plans as `SCAN events` with **no** temporary
  B-tree sort (`seq` is rowid order).
- The plan's claim that the current test publishes with the shared `auth_token` and ignores
  the response (verified 403) holds; the fix adds a `publisher_token` to the fixture.
- `test_dlq_pagination_concurrent_mutation` (new) is created by seq 01 in the same plan;
  this row does not depend on it.

## Design decisions

- Split into three focused cases: (1) schema-shape present, (2) schema-shape absent when a
  canonical index is dropped in a throwaway copy (negative), (3) plan over captured
  production SQL. Schema-shape and plan stay separate test functions (REQ-003).
- Extract the shape check into a module-level helper `_canonical_index_assertion` (new) that
  takes a connection and raises `AssertionError` when an index is missing, so the positive
  and negative tests share one assertion.
- Capture production SQL with `sqlite3.Connection.set_trace_callback` during real
  `fetch_dlq()`/`count_dlq()` calls; never hand-write or `CREATE INDEX`.

## Alternatives considered

- Asserting the OLD synthetic `ORDER BY dlq_at DESC` query: rejected — it is not
  `fetch_dlq()`'s SQL and plans differently (REQ-003).
- Dropping the index on the live `app.state.db`: rejected — that mutates the shared test
  database; the negative case must use a throwaway copy (REQ-002).

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq_index.py`

### Procedure

1. Open `tests/eventbus/test_eventbus_dlq_index.py`.
2. Extend the `client` fixture config: add `publisher_token="publisher-token"`,
   `consumer_token="consumer-token"`, `operator_token="operator-token"` alongside the
   existing `auth_token`, so the setup publish is authorised (REQ-004).
3. Replace the whole `test_dlq_query_uses_index` function with three new functions below.
4. Add `import shutil` after the existing imports (marked `(new)`).
5. Run `stale_detector.py` on this document (cite `scripts/eventbus/event_repo.py` and
   `scripts/eventbus/schema.sql` by full leading-slash path; mark the new test/helper
   names `(new)`).

### Method

Add the module-level helper after the `_event` helper (before the first test):

```python
def _canonical_index_names(conn: Any) -> set[str]:
    rows = conn.execute(
        'SELECT name FROM sqlite_master WHERE type="index" AND tbl_name="events"'
    ).fetchall()
    return {name for (name,) in rows}


def _assert_canonical_dlq_indexes(conn: Any) -> None:
    """REQ-002: both canonical DLQ indexes exist on the examined connection."""
    indexes = _canonical_index_names(conn)
    assert "idx_events_dlq_at" in indexes, f"missing idx_events_dlq_at: {sorted(indexes)}"
    assert "idx_events_dlq_seq" in indexes, f"missing idx_events_dlq_seq: {sorted(indexes)}"
```

Replace `test_dlq_query_uses_index` with:

```python
def test_dlq_index_shape_present(client: TestClient) -> None:
    """REQ-002: canonical DLQ indexes present under the open_db schema; no DDL runs."""
    assert client.app.state.db is not None
    _assert_canonical_dlq_indexes(client.app.state.db)


def test_dlq_index_shape_fails_when_dropped(client: TestClient) -> None:
    """REQ-002 negative: dropping a canonical index in a throwaway copy is detected."""
    import tempfile
    from pathlib import Path

    con = client.app.state.db
    assert con is not None
    db_path = con.execute("PRAGMA database_file").fetchone()[0]
    with tempfile.TemporaryDirectory() as tmp:
        copy_path = Path(tmp) / "copy.sqlite"
        shutil.copyfile(db_path, copy_path)
        copy_conn = sqlite3.connect(copy_path)
        try:
            copy_conn.execute("DROP INDEX IF EXISTS idx_events_dlq_at")
            with pytest.raises(AssertionError):
                _assert_canonical_dlq_indexes(copy_conn)
        finally:
            copy_conn.close()


def test_dlq_index_plan_matches_production_sql(client: TestClient) -> None:
    """REQ-003: EXPLAIN the exact SQL fetch_dlq()/count_dlq() execute."""
    import eventbus.app as eb_app
    from eventbus.event_repo import count_dlq, fetch_dlq

    con = client.app.state.db
    assert con is not None
    # Seed one DLQ row so fetch_dlq returns something.
    _seed_dlq_row(client)

    captured: list[str] = []
    con.set_trace_callback(captured.append)
    try:
        count_dlq(con)
        fetch_dlq(con, limit=2, offset=0)
    finally:
        con.set_trace_callback(None)

    count_sql = next(s for s in captured if s.startswith("SELECT COUNT(*)"))
    page_sql = next(s for s in captured if s.startswith("SELECT") and "ORDER BY seq" in s)

    count_plan = con.execute(
        f"EXPLAIN QUERY PLAN {count_sql}"
    ).fetchall()
    page_plan = con.execute(
        f"EXPLAIN QUERY PLAN {page_sql}"
    ).fetchall()

    assert any("idx_events_dlq_seq" in str(row) for row in count_plan), count_plan
    assert not any("sort" in str(row).lower() for row in page_plan), page_plan
```

Add the small seed helper next to `_seed_dlq_row` (new)'s definition (the procedure introduces
`_seed_dlq_row` (new) (new) too):

```python
def _seed_dlq_row(client: TestClient) -> None:
    """Publish and nack one event so it lands in the DLQ for the plan assertion."""
    pub_headers = {"Authorization": "Bearer publisher-token"}
    r = client.post("/publish", json=_event(), headers=pub_headers)
    assert r.status_code == 200  # REQ-004: setup publish is authorised
    con = client.app.state.db
    assert con is not None
    con.execute(
        "UPDATE events SET dlq_at = ? WHERE topic = ?",
        ("2026-10-28T00:00:00Z", "test.topic"),
    )
    con.commit()
```

### Details

- `sqlite3.Connection.set_trace_callback` records each executed SQL string with `?` placeholders; the two
  `next(...)` selectors isolate `count_dlq`'s and `fetch_dlq`'s statements from the rest.
- `count_dlq`'s SQL is `SELECT COUNT(*) FROM events WHERE dlq_at IS NOT NULL`
  (`scripts/eventbus/event_repo.py:141`); `fetch_dlq`'s is the same with `ORDER BY seq`
  and optional `LIMIT ? OFFSET ?` (`:118-138`). Both cited as references, not targets.
- The negative test copies the live test DB file (via `PRAGMA database_file`) into a
  `TemporaryDirectory`, drops `idx_events_dlq_at`, and asserts the shared helper raises —
  proving the positive case would fail on a missing canonical index. No DDL touches the
  shared connection.
- `sqlite3` is already imported transitively via `eventbus.app`; if `mypy`/ruff flags an
  unresolved `sqlite3.connect`, add `import sqlite3` (mark `(new)`) — otherwise leave it.

## Compatibility considerations

Tests only. The rewrite keeps `fetch_dlq`/`count_dlq` exercised (via direct calls and the
`/dlq` read through `_seed_dlq_row` (new)), so the plan's `event_repo.py` diff-cover baseline
(89%, unchanged) is preserved.

## Security considerations

None: no credentials logged; publisher/operator tokens are fixture header values, matching
the existing test style.

## Rollback considerations

Revert the commit (single-file test change).

## Validation plan

1. Read `tests/eventbus/test_eventbus_dlq_index.py` and confirm no `CREATE INDEX`/DDL
   remains and three cases exist (shape present, shape-dropped, plan).
2. Confirm the fixture carries a `publisher_token` and `_seed_dlq_row` (new) asserts publish 200
   (AC-4).
3. Confirm the negative test uses a throwaway copy and asserts `AssertionError` (AC-2).
4. Confirm the plan test captures SQL via `sqlite3.Connection.set_trace_callback` and asserts covering-index
   for count and no temp sort for page (AC-3).
5. Run `uv run pytest tests/eventbus/test_eventbus_dlq_index.py` (repeat 3x).
6. Run `uv run ruff check` and `uv run mypy` on the file.
7. Run `stale_detector.py` on this document (must report "not stale").

## Completion criteria

- No `CREATE INDEX`/DDL anywhere in the file (AC-2).
- Canonical-index presence asserted; a dropped-index negative test proves failure detection
  (AC-2).
- Plan assertions run over captured production SQL with both verified facts asserted (AC-3).
- Setup publish authorised with publisher token and asserted 2xx (AC-4).
- ruff/mypy clean; `stale_detector.py` clean.

## Out of Scope

- The pagination test reword + concurrent-mutation test (seq 01).
- The endpoint/replay doc boundary wording (seq 03, seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite index test: shape + plan cases (Implementation > Procedure) | Pending | — | — | REQ-002, REQ-003, REQ-004 |
| 2 | Add negative drop-index + publish-assertion tests (Validation plan) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Tests-only row |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261028-122307_ebpage003_pagination-contract-dlq-index.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-231631_ebpage003_pagination-contract-dlq-index.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-094100
- **Related target files**: `tests/eventbus/test_eventbus_dlq_index.py`
