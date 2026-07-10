---
title: "DB API and Operations - Maintenance and Rotation"
category: shared
tags:
  - shared
  - db
  - maintenance
  - rotation
  - rag-consistency
related:
  - 90_shared_00_document-guide.md
  - 90_shared_05_db_api_and_operations-module-boundaries-and-helper.md
  - 90_shared_05_db_api_and_operations-protocol-and-backend.md
  - 90_shared_05_db_api_and_operations-recovery-and-reference.md
source:
  - 90_shared_05_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- Schema → [90_shared_04_db_architecture_and_schema-overview-and-config.md](90_shared_04_db_architecture_and_schema-overview-and-config.md)

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

## 7b. RAG Consistency Checks (`db/rag_consistency.py`)

```python
from db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues

with SQLiteHelper("rag").open() as db:
    report: RagConsistencyReport = check_rag_consistency(db)
    if not is_consistent(report):
        for issue in summarize_issues(report):
            print(issue)
```

| Function | Signature | Description |
|---|---|---|
| `check_rag_consistency(db)` | `-> RagConsistencyReport` | Read-only: chunks/FTS/vec row counts + orphan detection |
| `is_consistent(report)` | `-> bool` | True if no orphans and FTS gap = 0 |
| `summarize_issues(report)` | `-> list[str]` | Human-readable issue descriptions |

### `RagConsistencyReport`

```python
@dataclass(frozen=True)
class RagConsistencyReport:
    chunks: int
    fts: int
    vec: int
    orphan_vec_count: int
    fts_gap: int              # chunks - fts; positive = missing FTS entries
    fts_orphan_count: int     # fts - chunks; positive = extra FTS entries (data loss risk)
```

**Usage:**

```python
from db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues

report: RagConsistencyReport = check_rag_consistency(db)
if not is_consistent(report):
    for issue in summarize_issues(report):
        print(issue)
```

- `fts_gap > 0` → FTS trigger missed some inserts; fix: `/db rag rebuild-fts`
- `orphan_vec_count > 0` → vec trigger failed; fix: re-ingest affected URLs
- Read-only; does not repair inconsistencies.

**Recovery flow:**
1. `PRAGMA integrity_check` on `target` DB
2. `dry_run=True` → return result without modifying DB
3. Result `"ok"` → run VACUUM; return `action="vacuum"` (or `"vacuum_failed"`)
4. Result not `"ok"` → archive corrupt file as `{stem}_corrupt_{timestamp}{suffix}`; copy `backup_path`; return `action="restored"` (or `"no_backup"` / `"error"`)

**Rotate archive format:** `{stem}_{YYYYMMDD_HHMMSS}{suffix}` in `archive_dir`
(default: `agent.toml::sqlite_archive_dir` → `/opt/llm/db/archive`).
Uses SQLite online backup API to preserve WAL integrity.

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_05_db_api_and_operations-module-boundaries-and-helper.md`
- `90_shared_05_db_api_and_operations-protocol-and-backend.md`
- `90_shared_05_db_api_and_operations-recovery-and-reference.md`

## Keywords

maintenance functions
db/maintenance.py
db rotation
RAG consistency checks
