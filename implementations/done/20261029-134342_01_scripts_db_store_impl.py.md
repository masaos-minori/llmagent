## Goal

Make `SQLiteMemoryDeleteStore.delete_memories_before()` re-evaluate the `pinned = 0` and
`updated_at` age guards inside the `DELETE` under `begin_immediate()`, and key the
auxiliary-table cleanup on the ids actually deleted — closing the selection-to-deletion
race window (REQ-001, REQ-002, REQ-003).

## Scope

- Single method body: `SQLiteMemoryDeleteStore.delete_memories_before()`
  (`scripts/db/store_impl.py:177-203`).
- No signature, return type (`MemoryDeleteResult`), or Protocol change (REQ-004).

## Assumptions

- SQLite 3.53.4 supports `DELETE ... RETURNING` (confirmed in the Plan; falsified by the
  first test run if wrong).
- The pre-lock selection `fetchall()` is kept only as a cheap fast path (early return
  when nothing is prunable); it is no longer the authoritative selection.
- A concurrent re-pin/refresh that commits before `BEGIN IMMEDIATE` wins retention; a
  writer arriving after the lock is held is serialized out by `busy_timeout` (Plan
  Assumptions).

## Design decisions

- Guards are re-applied at `DELETE` time rather than moving the `SELECT` under the lock:
  the Plan's Design section shows the lock-then-SELECT variant serializes a concurrent
  re-pin *behind* the prune and contradicts AC-1/AC-2 retention semantics.
- One `DELETE ... RETURNING memory_id` statement under `begin_immediate()` yields the
  actually-deleted ids; auxiliary cleanup keys only on those ids (REQ-002).
- Reuse the exact same predicate text (`updated_at < datetime('now', ?) AND pinned = 0`)
  and the same `f"-{older_than_days} days"` bind parameter in the `DELETE` as in the
  selection `SELECT`, so the retention window cannot drift (Plan Risks mitigation).
- Deletion stays inside a single `begin_immediate()` transaction covering
  `memories`, `memories_fts`, `memories_vec`, `memory_links` (REQ-003).

## Alternatives considered

- Move the selection `SELECT` inside `begin_immediate()`: rejected — closes the window
  only by blocking late-arriving pins, which the Plan explicitly rules out (Design
  section, point 2).
- `DELETE` then `SELECT` the removed ids (changes/changelog lookup): rejected — extra
  statements, no correctness benefit over `RETURNING`.

## Implementation
### Target file

`scripts/db/store_impl.py`

### Procedure

Rewrite the body of `delete_memories_before()` (`scripts/db/store_impl.py:177-203`):
keep the fast-path `fetchall()` early return; replace the `IN (...)` delete with a
guarded `DELETE ... RETURNING memory_id` executed inside `with self._db.begin_immediate():`;
derive the actually-deleted ids from the cursor; re-key the four auxiliary cleanup loops
on those ids; return `MemoryDeleteResult` with `deleted` equal to the id count.

### Method

```python
def delete_memories_before(self, older_than_days: int) -> MemoryDeleteResult:
    """Delete memories not updated for N days atomically across all memory tables."""
    rows = self._db.fetchall(  # fast path only; guards re-applied by the DELETE below
        "SELECT memory_id FROM memories "
        "WHERE updated_at < datetime('now', ?) AND pinned = 0",
        (f"-{older_than_days} days",),
    )
    if not rows:
        return MemoryDeleteResult(deleted=0)

    param = f"-{older_than_days} days"
    with self._db.begin_immediate():
        cur = self._db.execute(
            "DELETE FROM memories "
            "WHERE updated_at < datetime('now', ?) AND pinned = 0 "
            "RETURNING memory_id",
            (param,),
        )
        deleted_ids = [row[0] for row in cur.fetchall()]
        for mid in deleted_ids:
            self._db.execute("DELETE FROM memories_fts WHERE memory_id=?", (mid,))
        for mid in deleted_ids:
            self._db.execute("DELETE FROM memories_vec WHERE memory_id=?", (mid,))
        for mid in deleted_ids:
            self._db.execute("DELETE FROM memory_links WHERE src_id=?", (mid,))
        for mid in deleted_ids:
            self._db.execute("DELETE FROM memory_links WHERE dst_id=?", (mid,))
    return MemoryDeleteResult(deleted=len(deleted_ids))
```

### Details

- The `placeholders` join and the `# nosec B608` suppression comment
  (`scripts/db/store_impl.py:188-192`) are deleted: the method no longer builds any
  `IN (...)` SQL text.
- The deleted-id rows use positional access (`row[0]`), consistent with
  `collect_prunable_ids()` (`scripts/db/store_impl.py:212`).
- If the `DELETE` retains rows (a concurrent pin/refresh won the window),
  the deleted-id list is empty, the auxiliary loops run zero times, and the retained row keeps
  its `memories_fts` / `memories_vec` / `memory_links` rows (AC-3).
- `collect_prunable_ids()` is left untouched (reference-only; its preview semantics are
  out of scope per the Plan).
- The docstring and signature of `delete_memories_before()` stay byte-identical
  (REQ-004); reference files `scripts/db/helper.py`, `scripts/db/store_protocols.py`,
  `scripts/db/maintenance.py` are read-only context.

## Compatibility considerations

- Public contract unchanged: `delete_memories_before()` signature, `MemoryDeleteResult`,
  and `prune_old_memories()`'s `MaintenanceResult` shape (REQ-004); the two callers
  (`scripts/db/maintenance.py:401`, `scripts/agent/commands/memory_data_ops.py`) need no
  edits.
- Single-writer behavior is unchanged: same selection semantics, same auxiliary cleanup,
  same early return when nothing matches.
- The mock-coupled `TestSQLiteMemoryDeleteStore` tests break with the new statement
  shape; they are adapted in the sibling procedure document (T3), not here.

## Security considerations

- All predicates and the cutoff remain `?`-bind parameters (REQ-004).
- The only string-built SQL in this method (the `IN (...)` placeholder join with its
  `# nosec B608` suppression) is removed, so bandit `-ll` has one fewer suppression to
  audit.

## Rollback considerations

- Revert the single commit: no schema, data, or config migration is involved; the old
  method body restores cleanly.

## Validation plan

- `uv run pytest tests/db/test_db_store_impl.py -v` — new T1/T2 real-SQLite regression
  tests pass; re-pinned/refreshed rows and their auxiliary rows retained.
- `uv run pytest tests/db` — full db suite green (includes the unmodified
  `TestPruneOldMemories` caller-level regression in `tests/db/test_db_maintenance.py`).
- `uv run ruff check scripts/db`; `uv run mypy --no-namespace-packages scripts/db`;
  `uv run bandit -r scripts/ -c pyproject.toml -ll` — no errors, no medium/high findings.
- `PYTHONPATH=scripts uv run lint-imports` — no import-layer violations.
- `uv run coverage run -m pytest tests/`; `uv run coverage xml`;
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — >= 90% on
  changed lines.

## Completion criteria

- A re-pin or `updated_at` refresh committed between the selection and the `DELETE`
  retains the row *and* all of its auxiliary rows (AC-1, AC-2, AC-3).
- A deleted memory has its `memories_fts` / `memories_vec` / `memory_links` rows removed
  in the same `begin_immediate()` transaction, all-or-nothing (AC-3, AC-4).
- Public contract, retention window semantics, and parameterization are unchanged; all
  validation gates pass (AC-5).

## Out of Scope

- Retention policy values (`RetentionConfig`, `sqlite_retention_*` keys).
- The redundant double-selection in `prune_old_memories()` (`collect_prunable_ids()`
  followed by the re-selection here) — explicitly out of scope in the Plan.
- Other stores/delete paths (`SQLiteVectorStore`, `SQLiteDocumentStore`),
  `scripts/db/store_protocols.py`, `scripts/db/maintenance.py`, and all `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `delete_memories_before()` body per Procedure/Method/Details | Completed | 20261029-143314 | 20261029-143633 | REQ-001, REQ-002, REQ-003 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-143633 | 20261029-145006 | REQ-004; test adaptation is covered by the sibling document Static gates and targeted run pass; full-suite+diff-cover deferred to sibling procedure T3 adaptation gate |

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
  actually-deleted ids), REQ-003 (single-transaction atomicity), REQ-004 (contract
  preservation)
- **Source issue**: issues/20261029-011342_db001_memory-prune-pinned-race.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-073753_db001_memory-prune-pinned-race.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-134342
- **Related target files**: scripts/db/store_impl.py