# Goal

Update `db_maintenance_service.py` to use typed DTO attribute access for the return values
of `checkpoint_wal()` and `purge_old_sessions()` instead of `.get(key, default)` dict access.

# Scope

- `scripts/agent/services/db_maintenance_service.py`

# Assumptions

1. `checkpoint_wal()` in `db/maintenance.py` now returns `WalCheckpointCounts`
   (Step 2 prerequisite). Field: `pages_checkpointed` (int).
2. `purge_old_sessions()` now returns `PurgeCounts` (Step 2 prerequisite).
   Fields: `age_deleted` (int), `count_deleted` (int).
3. The import of `checkpoint_wal` and `purge_old_sessions` from `db.maintenance` is unchanged.
4. `WalCheckpointCounts` and `PurgeCounts` are importable from `db.models`.

# Implementation

## Target file

`scripts/agent/services/db_maintenance_service.py`

## Procedure

1. In `checkpoint()` method (around line 63):
   ```python
   # Before:
   pages_written=raw.get("pages_checkpointed", 0),
   # After:
   pages_written=raw.pages_checkpointed,
   ```
2. In `purge()` method (around line 84):
   ```python
   # Before:
   sessions_removed=raw.get("age_deleted", 0) + raw.get("count_deleted", 0),
   # After:
   sessions_removed=raw.age_deleted + raw.count_deleted,
   ```
3. Run ruff + mypy.

## Method

Two-line attribute access change. No logic change.

## Details

Full relevant context after change:

```python
def checkpoint(self, mode: str | None) -> DbCheckpointResult:
    """Run WAL checkpoint on session.sqlite."""
    with SQLiteHelper("session").open(write_mode=True) as db:
        raw = checkpoint_wal(db, mode)
    return DbCheckpointResult(
        mode=mode or "TRUNCATE",
        pages_written=raw.pages_checkpointed,
    )

def purge(self, max_sessions: int | None, max_age_days: int | None) -> DbPurgeResult:
    """Purge old sessions per retention config."""
    ...
    with SQLiteHelper("session").open(write_mode=True) as db:
        raw = purge_old_sessions(db, cfg)
    return DbPurgeResult(
        sessions_removed=raw.age_deleted + raw.count_deleted,
    )
```

# Validation plan

- `uv run ruff check scripts/agent/services/db_maintenance_service.py`
- `uv run mypy scripts/agent/services/db_maintenance_service.py`
- `uv run pytest tests/test_db_maintenance.py -v`
