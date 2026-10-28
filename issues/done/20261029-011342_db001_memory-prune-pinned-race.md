# Memory prune can delete a memory re-pinned between selection and deletion

## Priority
Medium

## Summary
`SQLiteMemoryDeleteStore.delete_memories_before()` selects the memories to delete in an autocommit query and only afterwards acquires the write lock via `begin_immediate()`. A memory that is re-pinned (or whose `updated_at` is refreshed) in the gap is still removed, because the `DELETE` matches on `memory_id IN (...)` alone. Make the selection and the deletion atomic so the pinned-exclusion and age guards cannot be bypassed by a concurrent writer.

## Background
`prune_old_memories()` in `scripts/db/maintenance.py` drives deletion through `SQLiteMemoryDeleteStore`: it calls `collect_prunable_ids()` and then `delete_memories_before()`. `mem001` (`issues/done/20261014-155503_mem001_implement-memory-command-spec.md`) implemented the spec's pinned-exclusion requirement as a static `AND pinned = 0` predicate in the `SELECT`, and made the four-table removal atomic by wrapping the `DELETE`s in `begin_immediate()`. That guard is correct in isolation, but the selection and the locked deletion are not a single atomic unit.

## Problem
In `scripts/db/store_impl.py`, `delete_memories_before()` runs:

```
rows = SELECT memory_id FROM memories WHERE updated_at < datetime('now', ?) AND pinned = 0   # autocommit, no lock
mids = [row[0] for row in rows]
with begin_immediate():
    DELETE FROM memories WHERE memory_id IN (mids)   # lock acquired here, after the SELECT
```

The `SELECT` executes in autocommit and holds no write lock. Between that `SELECT` and `begin_immediate()` acquiring the lock, a concurrent transaction can `UPDATE memories SET pinned = 1` (or refresh `updated_at`) for any selected `memory_id`. Because the `DELETE` matches only on `memory_id IN (...)`, it removes that memory regardless of its current `pinned`/`updated_at` state. The retention policy's promise — "prune never deletes pinned memories" — is therefore violated under concurrency.

## Reason for Change
The invariant is a data-safety guarantee, not a best-effort optimization, yet it is not atomically enforced. The fix is small (select inside the locked section, or re-apply the guards in the `DELETE` `WHERE`), but the current code gives false assurance: the static `pinned = 0` predicate reads as a complete guard while a concurrent writer can defeat it, and no test exercises the selection-to-delete window.

## Implementation Intent
Make the id selection and the cross-table deletion one atomic unit. Prefer re-running the `SELECT ... AND pinned = 0` query *after* entering the `begin_immediate()` transaction so the guard is evaluated under the write lock; alternatively add `AND pinned = 0 AND updated_at >= ...` back onto the `DELETE` `WHERE` clause so a re-pinned or refreshed row is not matched. Preserve the existing cross-table atomicity (memories, memories_fts, memories_vec, memory_links) and the pinned/exclusion semantics. Do not change the retention policy values or the `MaintenanceResult` shape returned to `prune_old_memories()`.

## Target Files or Areas
- `scripts/db/store_impl.py` — `SQLiteMemoryDeleteStore.delete_memories_before()`
- `scripts/db/maintenance.py` — `prune_old_memories()` (caller, reference only)
- `tests/db/test_db_store_impl.py` — `TestMemoryDeleteStoreRealSqlite`

## Required Changes
- Evaluate the `pinned = 0` / age selection inside the `begin_immediate()` write lock (move the `SELECT` into the `with` block), or re-check `pinned = 0` and the age predicate in the `DELETE` `WHERE` clause.
- Add a regression test that re-pins (and refreshes `updated_at` of) a selected memory between selection and deletion and asserts it is retained.
- Keep the four-table deletion atomic within the same transaction.

## Constraints
- Preserve cross-table atomicity: all four tables must be removed in one transaction.
- Preserve pinned exclusion and `updated_at` age semantics exactly; do not widen or narrow the retention window.
- Keep queries parameterized (no string interpolation of ids beyond the existing `?` placeholders).
- Do not change the public contract of `delete_memories_before()` / `MemoryDeleteResult` or the `MaintenanceResult` returned by `prune_old_memories()`.

## Acceptance Criteria
- A memory re-pinned after it was selected by the prune query is not deleted.
- A memory whose `updated_at` is refreshed to be recent after selection is not deleted.
- Existing prune behavior (old unpinned memories removed, pinned/recent kept, cross-table cleanup) is unchanged.
- The deletion remains atomic across all four memory tables.

## Testing Expectations
- Unit/integration test in `tests/db/test_db_store_impl.py` using real SQLite that simulates a concurrent re-pin / `updated_at` refresh between selection and deletion and asserts the memory is retained.
- Full `pytest tests/db` suite passes.
- `ruff check scripts/db`, `mypy --no-namespace-packages scripts/db`, and `bandit -ll` remain clean.

## Documentation Impact
N/A: no user-facing or operational documentation describes this internal atomicity detail. If `docs/` documents prune atomicity or the pinned-exclusion guarantee at a behavioral level, add a Known Issues / Needs Confirmation note about the concurrency caveat.

## Out of Scope
- Retention policy values (`RetentionConfig`, `sqlite_retention_*` keys).
- The redundant double-selection in `prune_old_memories()` (`collect_prunable_ids()` followed by the re-select inside `delete_memories_before()`).
- Other stores or delete paths (`SQLiteVectorStore`, `SQLiteDocumentStore`).

## Dependencies
N/A: none. `mem001` implemented the static pinned guard and four-table atomicity but not the selection-to-delete race; no open issue covers this gap.

## Unresolved Questions
- Practical impact is likely low: the gap between the autocommit `SELECT` and `begin_immediate()` is very small and `prune_old_memories()` typically runs as an idle maintenance operation, so observing a concurrent re-pin in that window is unlikely. Confirm whether prune runs concurrently with active `/memory pin` / `unpin` in production before sizing the effort.
- Whether to select inside the lock (cleaner, closes the race fully) versus re-checking in the `DELETE` `WHERE` (smaller diff) — depends on whether `begin_immediate()` serialization is already relied upon elsewhere in the prune path.

## AI Implementation Instruction
Make the minimal change that makes selection and deletion atomic: move the `SELECT memory_id ... AND pinned = 0` inside the `begin_immediate()` block in `delete_memories_before()`, or add the `pinned = 0` and age predicates back onto the `DELETE` `WHERE`. Add a real-SQLite regression test that re-pins a selected memory mid-operation and asserts it survives. Do not alter retention semantics, the `?`-placeholder binding, or any public result type. Run `ruff`, `mypy --no-namespace-packages scripts/db`, and `pytest tests/db` before finishing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-011342
- **Related target files**: scripts/db/store_impl.py, scripts/db/maintenance.py, tests/db/test_db_store_impl.py
