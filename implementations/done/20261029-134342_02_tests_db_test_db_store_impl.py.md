## Goal

Add real-SQLite regression tests for the selection-to-deletion race window (T1, T2) and
adapt the mock-based delete-store tests to the new `DELETE ... RETURNING` statement shape
(T3), pinning REQ-001, REQ-002, REQ-004, REQ-005.

## Scope

- `TestMemoryDeleteStoreRealSqlite` (`tests/db/test_db_store_impl.py:490-549`): add T1/T2
  mid-window re-pin / refresh regression tests plus the `_RaceDeleteDB` (new) test wrapper.
- `TestSQLiteMemoryDeleteStore` (`tests/db/test_db_store_impl.py:395-473`): adapt the
  mock delete tests to the new statement shape; add one SQL-shape assertion test.
- `TestPruneOldMemories` (`tests/db/test_db_maintenance.py:381-433`): adapt the
  caller-level mock fixtures to the new cursor shape. Discovered at execution time: its
  `_make_db` cursor mock depended on the old `rowcount`/`IN (...)` statement shape
  (MagicMock `__iter__` defaults to empty, silently zeroing the deleted-id list), so the
  Plan's "unchanged gate" expectation was incomplete — the same sanctioned mock coupling
  applies here.

## Assumptions

- This document is Phase 2: it is executed after the sibling procedure document
  `implementations/20261029-134342_01_scripts_db_store_impl.py.md` lands, because the new
  assertions describe the post-change statement shape.
- `T1`/`T2` would fail against the pre-fix implementation (the injected pin/refresh would
  be deleted via the stale `IN (...)` list) — that is what makes them regression locks;
  confirmed by running them once before and once after the store change if the executor
  wants explicit proof.
- A deterministic mid-window injection does not need threads: injecting a committed
  `UPDATE` between the fast-path `fetchall()` and `begin_immediate()` reproduces exactly
  the AC-1/AC-2 semantics (a write that lands after selection and before the `DELETE`).

## Design decisions

- Race injection via a wrapper class `_RaceDeleteDB` (new) subclassing `_RealDeleteDB`
  (`tests/db/test_db_store_impl.py:475`): its `fetchall()` runs the real selection, and
  on the first `SELECT memory_id FROM memories` call it executes an injected mutation
  callback and `commit()`s it before returning — i.e. after selection, before
  `begin_immediate()`. Deterministic, single connection, in-memory DB, no timing sleeps.
- Keep existing SQL-shape assertions in the mock tests (T3 per the Plan): the fast-path
  `fetchall()` shape assertions in `test_delete_memories_before_selects_by_updated_at`
  (`tests/db/test_db_store_impl.py:463`) stay valid because the fast path is retained.

## Alternatives considered

- Two-connection/threaded concurrency test: rejected — timing-dependent and flaky; the
  wrapper injection pins the same ordering deterministically.
- Deleting `TestSQLiteMemoryDeleteStore` and rewriting from scratch: rejected — the Plan
  requires adapting them while preserving their existing SQL-shape assertions (T3).

## Implementation
### Target file

`tests/db/test_db_store_impl.py`

### Procedure

1. Add `_RaceDeleteDB` (new) after `_RealDeleteDB` (around
   `tests/db/test_db_store_impl.py:488`).
2. Add `test_repin_between_selection_and_delete_is_retained` (new) and
   `test_updated_at_refresh_between_selection_and_delete_is_retained` (new) to
   `TestMemoryDeleteStoreRealSqlite`, reusing its existing schema/seed helper shape.
3. Adapt `test_old_entries_trigger_delete_and_commit` and
   `test_fts_and_vec_cleanup_called_per_deleted_entry` in `TestSQLiteMemoryDeleteStore`
   to the cursor-`fetchall()` deleted-id retrieval.
4. Add `test_delete_statement_reapplies_guards_and_returns_ids` (new) asserting the
   `DELETE` SQL shape and bind parameter.

### Method

Wrapper:

```python
class _RaceDeleteDB(_RealDeleteDB):
    """Runs an injected committed mutation right after the fast-path selection."""

    def __init__(self, conn: sqlite3.Connection, inject) -> None:
        super().__init__(conn)
        self._inject = inject
        self._armed = True

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        rows = super().fetchall(sql, params)
        if self._armed and sql.startswith("SELECT memory_id FROM memories"):
            self._armed = False
            self._inject()
            self.conn.commit()
        return rows
```

T1 (re-pin retained):

```python
def test_repin_between_selection_and_delete_is_retained(self) -> None:
    # seed as in test_prunes_only_old_unpinned_by_updated_at: m1 old unpinned with
    # memories_fts / memories_vec / memory_links rows
    def _inject() -> None:
        conn.execute("UPDATE memories SET pinned = 1 WHERE memory_id = 'm1'")

    store = SQLiteMemoryDeleteStore(_RaceDeleteDB(conn, _inject))  # type: ignore[arg-type]
    result = store.delete_memories_before(30)

    assert result.deleted == 0
    assert conn.execute(
        "SELECT pinned FROM memories WHERE memory_id = 'm1'"
    ).fetchone() == (1,)
    assert conn.execute("SELECT memory_id FROM memories_fts WHERE memory_id='m1'").fetchall() == [("m1",)]
    assert conn.execute("SELECT memory_id FROM memories_vec WHERE memory_id='m1'").fetchall() == [("m1",)]
    assert conn.execute("SELECT * FROM memory_links WHERE src_id='m1' OR dst_id='m1'").fetchall() != []
```

T2 (refresh retained): same seed and wrapper, injecting
`UPDATE memories SET updated_at = datetime('now') WHERE memory_id = 'm1'`; assert
`result.deleted == 0`, the row and all auxiliary rows are retained.

T3 mock adaptations (MagicMock `db`):

- `test_old_entries_trigger_delete_and_commit`: keep
  `mock_db.fetchall.return_value = [("uuid-1",), ("uuid-2",)]` (fast path); set
  `mock_cur.fetchall.return_value = [("uuid-1",), ("uuid-2",)]` on the execute cursor;
  keep `assert result.deleted == 2` and `begin_immediate.assert_called_once()`; drop the
  `rowcount` fixture.
- `test_fts_and_vec_cleanup_called_per_deleted_entry`: set the execute cursor's
  `fetchall.return_value = [("uuid-abc",)]`; keep the existing `any(...)` assertions and
  add `assert any("memory_links" in c for c in calls)`.
- `test_no_old_entries_returns_deleted_zero` and `test_delete_memories_before_selects_by_updated_at`
  pass unchanged (fast path retained).

### Details

- New mock test `test_delete_statement_reapplies_guards_and_returns_ids` (new):
  `mock_db.fetchall` fast-path rows `[("uuid-1",)]`; after calling
  `delete_memories_before(30)`, assert the first `mock_db.execute` call's SQL contains
  `DELETE FROM memories`, `updated_at < datetime('now', ?)`, `pinned = 0`,
  `RETURNING memory_id`, and its params are `("-30 days",)` — the same predicate text
  and bind parameter as the selection `SELECT`.
- Seed data for T1/T2 mirrors the existing `test_prunes_only_old_unpinned_by_updated_at`
  helper (`_iso(days_ago)` + the four-row insert and auxiliary rows); factor the seed
  into a local helper only if it avoids duplication, otherwise inline it.
- Auxiliary-retention assertions are the REQ-002 half of AC-3: without cursor-keyed
  cleanup the injected-pin row would survive in `memories` while losing its auxiliary
  rows, which these assertions forbid.
- `collect_prunable_ids` mock tests (`test_collect_prunable_ids_filters_pinned`,
  `test_collect_prunable_ids_empty`, `test_collect_prunable_ids_uses_updated_at`) are
  untouched.

## Compatibility considerations

- Test-only change; no production importer.
- Mock tests keep their existing names and assertion intent (T3), so historical failure
  reports remain comparable.

## Security considerations

- The new shape assertion pins that the cutoff reaches SQLite as a bind parameter
  (`("-30 days",)`), preserving the parameterization guarantee (REQ-004).

## Rollback considerations

- Revert the commit alongside the store change; T1/T2 revert with it (they fail against
  the pre-fix store implementation by design).

## Validation plan

- `uv run pytest tests/db/test_db_store_impl.py -v` — T1/T2/T3 tests pass.
- `uv run pytest tests/db` — full db suite green (REQ-004, AC-5).
- `uv run ruff check tests` — clean.

## Completion criteria

- T1/T2 demonstrate: a committed re-pin (AC-1) or `updated_at` refresh (AC-2) landing
  between selection and `DELETE` retains the memory and every auxiliary row (AC-3).
- The adapted mock tests pass against the new statement shape and assert the re-applied
  guards and `RETURNING` ids (AC-5).
- Full `tests/db` suite green with no previously-passing test weakened or removed.

## Out of Scope

- `scripts/db/store_impl.py` itself (sibling procedure document).
- `tests/db/test_db_maintenance.py` — only the `TestPruneOldMemories` mock-fixture
  adaptation recorded in Scope; no other maintenance tests are modified.
- Concurrency stress/load testing beyond the deterministic window injection.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_RaceDeleteDB` (new), T1/T2 real-SQLite regression tests | Completed | 20261029-143734 | 20261029-144156 | REQ-001, REQ-002, REQ-005 |
| 2 | Adapt `TestSQLiteMemoryDeleteStore` mock tests; add DELETE-shape test | Completed | 20261029-144156 | 20261029-144156 | REQ-004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-144210 | 20261029-145006 | REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (atomic guard re-evaluation), REQ-002 (cleanup keyed on
  actually-deleted ids), REQ-004 (contract preservation), REQ-005 (real-SQLite race
  regression coverage)
- **Source issue**: issues/20261029-011342_db001_memory-prune-pinned-race.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-073753_db001_memory-prune-pinned-race.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-134342
- **Related target files**: tests/db/test_db_store_impl.py