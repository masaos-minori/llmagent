---
title: "DB API - Memory Operations and Maintenance Functions"
category: shared
tags:
  - db
  - api
  - memory
  - maintenance
  - purge
  - vacuum
  - rotation
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
  - 90_shared_05_db_module_boundaries_and_sqlitehelper.md
  - 90_shared_05_db_store_protocols.md
source:
  - 90_shared_05_db_module_boundaries_and_sqlitehelper.md
---

# DB API - Memory Operations and Maintenance Functions

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)
- Schema → [90_shared_04_db_overview_and_config.md](90_shared_04_db_overview_and_config.md)

---

## 6. Memory-Related Tables and Operations (`MemoryStore`)

`MemoryStore` is defined in `agent/memory/store.py` (NOT `db/`). It uses `SQLiteHelper("session")`.

Key methods:

| Method | Description |
|---|---|
| `add(entry, embedding=None)` | Insert into `memories` + `memories_fts`; optionally `memories_vec` |
| `upsert(entry, embedding=None)` | `INSERT OR REPLACE` + sync FTS/vec |
| `delete(memory_id)` | Delete 1 entry; returns `True` if found |
| `search_by_type(type, limit)` | Filter by `memory_type`; ordered `importance DESC, pinned DESC` |
| `pin(memory_id)` / `unpin(memory_id)` | Toggle pinned flag |
| `clear_by_session(session_id)` | Delete all entries for session |
| `count_vec()` | Row count in `memories_vec`; returns `0` if vec0 not loaded |

`prune_old_memories(db, older_than_days)` in `maintenance.py` delegates to
`SQLiteMemoryDeleteStore` for cross-table deletion.

---

## 7. Maintenance Functions (`db/maintenance.py`)

All functions accept a `SQLiteHelper` instance and delegate low-level operations back to it.

| Function | Signature | Description |
|---|---|---|
| `checkpoint_wal(db, mode=None)` | `-> WalCheckpointCounts` | WAL flush; default mode from `agent.toml::sqlite_wal_checkpoint_mode` (default `TRUNCATE`) |
| `vacuum_db(db, mode=STRICT)` | `-> MaintenanceResult` | Delegates to `db.vacuum()`; call outside transaction |
| `purge_old_sessions(db, cfg=None, mode=STRICT)` | `-> MaintenanceResult` | Age-based + count-based session purge; commits internally |
| `prune_old_memories(db, older_than_days, mode=STRICT)` | `-> MaintenanceResult` | Delete old memories via `SQLiteMemoryDeleteStore` |

### `MaintenanceMode` and `MaintenanceResult`

```python
class MaintenanceMode(StrEnum):
    STRICT = "strict"        # Exceptions propagate (default; preserves existing behavior)
    BEST_EFFORT = "best_effort"  # Exceptions caught, logged, returned in MaintenanceResult

@dataclass(frozen=True)
class MaintenanceResult:
    success: bool
    action: str              # "vacuum" | "vacuum_failed" | "purge" | "purge_failed" | "prune" | "prune_failed"
    mode: MaintenanceMode
    detail: str | None = None  # Exception message on failure
    data: dict | None = None   # e.g. {"age_deleted": N, "count_deleted": N} or {"deleted": N}
```

**Mode semantics:**
- `STRICT` (default): behavior unchanged from pre-mode code — exceptions propagate; on success a `MaintenanceResult(success=True)` is returned
- `BEST_EFFORT`: exceptions are caught, logged as ERROR, and returned as `MaintenanceResult(success=False, detail=str(exc))`; callers MUST check `result.success`

```python
from db.maintenance import MaintenanceMode, MaintenanceResult, vacuum_db

# STRICT mode (default) — raises on error
result = vacuum_db(db)
assert result.success

# BEST_EFFORT mode — caller checks result
result = vacuum_db(db, mode=MaintenanceMode.BEST_EFFORT)
if not result.success:
    logger.error("vacuum failed: %s", result.detail)
```

### `RetentionConfig`

```python
@dataclass(frozen=True)
class RetentionConfig:
    max_sessions: int = 100   # max sessions to retain
    max_age_days: int = 90    # purge sessions older than N days (0 = disabled)
```

`RetentionConfig.from_config()` reads `agent.toml::sqlite_retention_max_sessions` /
`sqlite_retention_max_age_days`.

### `purge_old_sessions` behavior

1. If `max_age_days > 0`: delete sessions older than N days (`age_deleted`)
2. If remaining count > `max_sessions`: delete oldest excess sessions (`count_deleted`)
3. Assumes `messages` has `ON DELETE CASCADE`
4. Calls `db.conn.commit()` at end
5. Returns `MaintenanceResult(success=True, data={"age_deleted": N, "count_deleted": N})`

### `prune_old_memories` behavior

1. Collect `memory_id` values older than `older_than_days`
2. Delete from `memories`, `memories_fts`, `memories_vec`
3. Call `db.commit()`
4. Returns `MaintenanceResult(success=True, data={"deleted": N})`
5. On failure in STRICT mode: exception propagates; in BEST_EFFORT mode: returns `success=False`

---

## 7a. DB Rotation (`db/rotation.py`)

```python
from db.rotation import rotate_session_db, rotate_workflow_db, rotate_all_dbs, rotate_db

# Archive only session DB
session_dest = rotate_session_db()

# Archive rag + session DBs
rag_dest, session_dest = rotate_db()

# Archive all three DBs
rag_dest, session_dest, workflow_dest = rotate_all_dbs()
```

| Function | Signature | Description |
|---|---|---|
| `rotate_session_db(archive_dir=None)` | `-> Path` | Archive `session.sqlite` with timestamp suffix via SQLite online backup API |
| `rotate_workflow_db(archive_dir=None)` | `-> Path` | Archive `workflow.sqlite` with timestamp suffix |
| `rotate_all_dbs(archive_dir=None)` | `-> tuple[Path, Path, Path]` | Archive all three DBs; returns `(rag_dest, session_dest, workflow_dest)` |
| `rotate_db(archive_dir=None)` | `-> tuple[Path, Path]` | Archive both rag and session DBs; returns `(rag_dest, session_dest)` |

Archive directory defaults to `/opt/llm/db/archive` (from `agent.toml::sqlite_archive_dir`).

---

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md)
- [90_shared_05_db_store_protocols.md](90_shared_05_db_store_protocols.md)
- [90_shared_05_db_recovery_and_verification.md](90_shared_05_db_recovery_and_verification.md)
- [90_shared_04_db_overview_and_config.md](90_shared_04_db_overview_and_config.md)

## Keywords

memory
maintenance
purge
vacuum
rotation
