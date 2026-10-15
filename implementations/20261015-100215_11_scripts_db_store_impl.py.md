## Goal

Make `SQLiteMemoryDeleteStore.delete_memories_before()` exclude pinned memories
and remove `memory_links` atomically, and expose the prunable id list for the
prune-change-event flow (REQ-004, REQ-005).

## Scope

Modify `scripts/db/store_impl.py` only: tighten `delete_memories_before()` and
add an additive `collect_prunable_ids()` method.

## Assumptions

- Pinned memories must never be pruned (REQ-005): the prune predicate is
  "older than N days AND `pinned = 0`".
- `memory_links` rows reference `memories(memory_id)` in either column and SQLite
  leaves FK enforcement off, so both columns must be cleared explicitly
  (schema in `schema_sql.py`).
- `MemoryDeleteResult` and the `MemoryDeleteStore` Protocol live in
  `db/store_protocols.py`, which is NOT a modification target; their shapes are
  fixed. Therefore ids cannot be returned via `MemoryDeleteResult`, and a new
  additive (non-Protocol) method is used instead.

## Design decisions

- Add `AND pinned = 0` to the `delete_memories_before()` SELECT so pinned rows are
  excluded before deletion.
- Delete `memory_links` (both columns) inside the same `begin_immediate()`
  transaction as the `memories`/`fts`/`vec` deletes — one atomic operation.
- Add `collect_prunable_ids(older_than_days) -> list[str]` returning the ids that
  match the prune predicate; its predicate is the single source of truth shared
  with `delete_memories_before`. It is not part of the Protocol, so it does not
  affect the contract.

## Alternatives considered

- Returning ids via `MemoryDeleteResult`: rejected. That dataclass is defined in
  the non-target `store_protocols.py` and frozen; adding a field would violate the
  one-file-per-row scope. An additive method avoids touching it.

## Implementation

### Target file

`scripts/db/store_impl.py`

### Procedure

1. Exclude pinned memories in `delete_memories_before()`.
2. Remove `memory_links` atomically within the same transaction.
3. Add `collect_prunable_ids()`.

### Method

- In `delete_memories_before()`, change the SELECT to:

  ```python
  rows = self._db.fetchall(
      "SELECT memory_id FROM memories "
      "WHERE created_at < datetime('now', ?) AND pinned = 0",
      (f"-{older_than_days} days",),
  )
  ```

- Inside the `with self._db.begin_immediate():` block, after the `memories_vec`
  cleanup loop, add the link cleanup:

  ```python
  for mid in mids:
      self._db.execute("DELETE FROM memory_links WHERE src_id=?", (mid,))
  for mid in mids:
      self._db.execute("DELETE FROM memory_links WHERE dst_id=?", (mid,))
  ```

- Add the additive method (after `delete_memories_before()`):

  ```python
  def collect_prunable_ids(self, older_than_days: int) -> list[str]:
      """Return memory_ids older than older_than_days that are not pinned."""
      rows = self._db.fetchall(
          "SELECT memory_id FROM memories "
          "WHERE created_at < datetime('now', ?) AND pinned = 0",
          (f"-{older_than_days} days",),
      )
      return [row[0] for row in rows]
  ```

### Details

- `mids` now contains only non-pinned ids, so the `memory_links` deletes cover
  exactly what is removed.
- `collect_prunable_ids` uses the identical predicate; keep them in sync.
- Do not modify `MemoryDeleteResult` or the `MemoryDeleteStore` Protocol.

## Compatibility considerations

`delete_memories_before()` keeps its `MemoryDeleteResult` return and Protocol
signature. It now deletes fewer rows (pinned excluded) and also clears
`memory_links`; tests asserting the old behavior must be updated.

## Security considerations

N/A: bound by `memory_id`; parameters are bound throughout.

## Rollback considerations

Revert the commit; the predicate change, link deletes, and new method are
adjustable.

## Validation plan

- `pytest tests/db/test_db_store_impl.py` covers pinned exclusion and
  `memory_links` removal.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`delete_memories_before(mid_old)` removes `memories`/`memories_fts`/`memories_vec`
and both `memory_links` columns for that id, leaving pinned memories untouched;
`collect_prunable_ids()` returns the matching non-pinned ids.

## Out of scope

The prune orchestration + event emission (`maintenance.py`, `memory_data_ops.py`)
are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Exclude pinned + atomic memory_links removal; add collect_prunable_ids | Pending | — | — | REQ-004, REQ-005 |
| 2 | Add/update store_impl prune tests | Pending | — | — | `test_db_store_impl.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`, `REQ-005`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/db/store_impl.py
