## Goal
- `REQ-008`: `SQLiteMemoryDeleteStore` selects the memories to prune by `updated_at` instead of `created_at`, as the `/memory` chapter says ("not updated for n days"), keeping the pinned exclusion and the atomic deletion.

## Scope
- The two `created_at` conditions in `SQLiteMemoryDeleteStore.delete_memories_before` and `collect_prunable_ids` in `scripts/db/store_impl.py`, and their docstrings. Tests are the next document.

## Assumptions
- `memories.updated_at` exists and is set on insert and upsert (`write_ops.py`) and on `pin` and `unpin` (`pin_ops.py`); it is never earlier than `created_at`.
- `prune_old_memories` in `scripts/db/maintenance.py` calls `collect_prunable_ids` then `delete_memories_before`, in STRICT mode; it needs no change.
- The comparison keeps the existing `datetime('now', ?)` form with the `-N days` parameter, so the (pre-existing) text-comparison behavior of ISO timestamps is unchanged.

## Design decisions
- Replace `created_at < datetime('now', ?)` with `updated_at < datetime('now', ?)` in both queries; keep `AND pinned = 0`, the parameter, the transaction, and the per-table deletions as they are.
- Both queries must stay identical in their condition so the ids collected for events equal the rows deleted.

## Alternatives considered
Renaming `delete_memories_before` to a name that mentions the update time: rejected as an interface change outside the Plan; the docstring states the behavior instead.

## Implementation
### Target file
`scripts/db/store_impl.py`

### Procedure
- In `SQLiteMemoryDeleteStore.delete_memories_before`, change the `SELECT memory_id FROM memories WHERE created_at < datetime('now', ?) AND pinned = 0` condition to `updated_at`, and update the docstring to say memories not updated for N days.
- In `SQLiteMemoryDeleteStore.collect_prunable_ids`, make the same change and update the docstring.

### Method
- Edit only the two SQL strings and the two docstrings; do not touch the deletion statements or the transaction block.

### Details
- The behavior change is intentional: a memory whose `updated_at` is recent is kept even when `created_at` is old; fewer memories are deleted than before.
- Callers: `prune_old_memories` (maintenance) and, through it, `/memory prune`; the existing maintenance tests mock the store and are unaffected.

## Compatibility considerations
- Retention semantics change in the safer direction (fewer deletions). No signature or return type changes.

## Security considerations
N/A: the SQL stays parameterized; no new inputs.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_db_store_impl.py tests/db/test_db_maintenance.py -q`
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/db/store_impl.py -c pyproject.toml`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria
- Both queries use `updated_at` and still exclude pinned memories; the deletion is unchanged and atomic.
- The store and maintenance tests pass; lint, type, architecture, and security checks report no new findings.

## Out of scope
- `maintenance.py`, `count_ops.py`, the `/memory` handlers, and any rename of the store methods.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the two prune queries and docstrings to `updated_at` | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-008 (prune by updated_at)
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-143248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145841
- **Related target files**: scripts/db/store_impl.py
