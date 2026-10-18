---
title: "DB API and Operations — Maintenance and Rotation"
area: shared
tags:
  - shared
  - db
  - maintenance-rotation
related:
  - db_04_api_and_operations-module-boundaries-and-helper.md
  - db_05_api_and_operations-protocol-and-backend.md
  - db_01_architecture_and_schema-overview-and-config.md
---
# DB API and Operations

- Schema → [db_01_architecture_and_schema-overview-and-config.md](db_01_architecture_and_schema-overview-and-config.md)

## 6. Maintenance Functions (`db/maintenance.py`)

All functions accept a `SQLiteHelper` instance and delegate low-level operations to it. 

`checkpoint_wal(db, mode=None) -> WalCheckpointCounts`: Flushes the Write-Ahead Log (WAL). The default mode is taken from `agent.toml::sqlite_wal_checkpoint_mode` (a code-level default applies when the key is absent). Invalid strings raise a `ValueError` via the `SQLiteHelper.checkpoint()` `_CHECKPOINT_MODES` check. 

`vacuum_db(db, mode=STRICT) -> MaintenanceResult`: Delegates to `db.vacuum()`. Must be called outside of an active transaction. 

`purge_old_sessions(db, cfg=None, mode=STRICT) -> MaintenanceResult`: Performs age-based and count-based session purging; commits internally. 

`prune_old_memories(db, older_than_days, mode=STRICT) -> MaintenanceResult`: Deletes old memories via `SQLiteMemoryDeleteStore`. 

`MaintenanceMode` (StrEnum): 
- `STRICT` = `'strict'` (Default; exceptions propagate, preserving existing behavior).
- `BEST_EFFORT` = `'best_effort'` (Exceptions are caught, logged, and returned within `MaintenanceResult`).

`MaintenanceResult` (frozen dataclass): Contains `success` (bool), `action` (`'vacuum'`|`'vacuum_failed'`|`'purge'`|`'purge_failed'`|`'prune'`|`'prune_failed'`), `mode` (`MaintenanceMode`), `detail` (optional exception message on failure), and `data` (optional dictionary, e.g., `{'age_deleted': N, 'count_deleted': N}` or `{'deleted': N}`).

**Mode Semantics:**
- **STRICT (Default):** Behaves as before mode introduction—exceptions propagate directly. A successful operation returns `MaintenanceResult(success=True)`.
- **BEST_EFFORT:** Exceptions are caught and logged as `ERROR`, then returned as `MaintenanceResult(success=False, detail=str(exc))`. Callers **MUST** check `result.success`.

**Usage Example:**
```python
from db.maintenance import MaintenanceMode, MaintenanceResult, vacuum_db
result = vacuum_db(db)
assert result.success  # In STRICT mode

result = vacuum_db(db, mode=MaintenanceMode.BEST_EFFORT)
if not result.success:
    logger.error('vacuum failed: %s', result.detail)
```

`RetentionConfig` (frozen dataclass): Defines `max_sessions` (maximum sessions to retain) and `max_age_days` (purge sessions older than N days; 0 disables this). Defaults are defined in `RetentionConfig`. `RetentionConfig.from_config()` reads `agent.toml::sqlite_retention_max_sessions` and `agent.toml::sqlite_retention_max_age_days`.

---

## 7. DB Rotation (`db/rotation.py`)

From `db.rotation import rotate_session_db, rotate_workflow_db, rotate_eventbus_db, rotate_all_dbs, rotate_db`:
- `rotate_session_db(archive_dir=None) -> Path`: Archives the session database with a timestamp suffix using the SQLite online backup API.
- `rotate_workflow_db(archive_dir=None) -> Path`: Archives the workflow database with a timestamp suffix.
- `rotate_eventbus_db(archive_dir=None) -> Path`: Archives the event bus database with a timestamp suffix.
- `rotate_all_dbs(archive_dir=None) -> tuple[Path, Path, Path, Path]`: Archives all four databases (ADR-008), returning `(rag_dest, session_dest, workflow_dest, eventbus_dest)`.
- `rotate_db(archive_dir=None) -> tuple[Path, Path]`: Archives both rag and session databases, returning `(rag_dest, session_dest)`.

The archive directory is read from `agent.toml::sqlite_archive_dir`, with a code-level default when the key is absent. The rotation format is `{stem}_{YYYYMMDD_HHMMSS}{suffix}` in the `archive_dir`. It uses the SQLite online backup API to ensure WAL integrity is preserved during rotation.

**Corrupt-archive retention (`CorruptArchiveRetentionConfig`, `db/maintenance.py`):** timestamped `*_corrupt_*` archives that `db.recovery` creates before restoring a database are pruned by two optional `agent.toml` keys. `sqlite_corrupt_archive_max_files` keeps the most recent N archives per source database, and `sqlite_corrupt_archive_max_age_days` deletes archives older than N days (`0` disables the age limit). Both keys fall back to in-code defaults when absent, and `ProductionConfigValidator` accepts them as known `agent.toml` keys.

---

## 8. RAG Consistency Checks (`db/rag_consistency.py`)

From `db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues`:
```python
with SQLiteHelper('rag').open() as db:
    report = check_rag_consistency(db)
    if not is_consistent(report):
        for issue in summarize_issues(report):
            print(issue)
```

`check_rag_consistency(db, embed_failed=0) -> RagConsistencyReport`: A read-only report containing chunk/FTS/vec row counts and orphan detection. Note that `embed_failed` (the number of embedding failures known by the caller) is passed in but not detected by this function itself.

`is_consistent(report) -> bool`: Returns `True` when every rule in the module's `_CHECKS` group is clean: `fts_gap == 0`, `fts_orphan_count == 0`, `orphan_vec_count == 0`, `vec == chunks`, `documents_without_chunks_count == 0`, `chunks_without_vec_count == 0`, `duplicate_chunk_index_count == 0`, no `url_level_mismatches`, no `diagnostic_errors`, and `read_smoke_test_ok`.

`summarize_issues(report) -> list[str]`: Provides human-readable issue descriptions for the `_CHECKS` rules that are not clean, in tuple order.

**RagConsistencyReport (frozen dataclass):**
Contains `chunks` (int), `fts` (int), `vec` (int), `orphan_vec_count` (int), `fts_gap` (int: `chunks - fts`; positive means missing FTS entries), `fts_orphan_count` (int: `fts - chunks`; positive means extra FTS entries/data loss risk), `embed_failed` (int=0, caller-supplied), `issues` (tuple[str,...], populated by `summarize_issues(report)`), and optional diagnostic identifiers: `affected_chunk_ids` (up to 10 chunk IDs missing from FTS), `affected_doc_ids` (up to 10 doc IDs whose chunks are missing from FTS), and `affected_orphan_chunk_ids`/`affected_orphan_urls` (up to 10 items for orphaned vector rows).

**Implementation Details:**
- The rules are one `_CHECKS` tuple of `(clean predicate, issue builder)` pairs. `is_consistent` requires every predicate to hold; `summarize_issues` renders the builder of each predicate that does not. `diagnostic_errors` and `read_smoke_test_ok` are the two rules with no builder, so they make a report inconsistent without adding an issue string.
- `check_rag_consistency` automatically calls `summarize_issues(report)` and populates the `issues` field in the report.
- Diagnostic identifier lists (`affected_*`) are only populated when `fts_gap > 0` or `orphan_vec_count > 0`.

---

## Keywords

- shared
- db
- maintenance-rotation
