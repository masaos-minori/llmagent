# DB API and Operations

- Schema $\rightarrow$ [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md)

## 3. Maintenance Functions (`db/maintenance.py`)

All functions accept a `SQLiteHelper` instance and delegate low-level operations to it. 

`checkpoint_wal(db, mode=None) \rightarrow WalCheckpointCounts`: Flushes the Write-Ahead Log (WAL). The default mode is taken from `agent.toml::sqlite_wal_checkpoint_mode` (default `TRUNCATE`). Invalid strings raise a `ValueError` via the `SQLiteHelper.checkpoint()` `_CHECKPOINT_MODES` check. 

`vacuum_db(db, mode=STRICT) \rightarrow MaintenanceResult`: Delegates to `db.vacuum()`. Must be called outside of an active transaction. 

`purge_old_sessions(db, cfg=None, mode=STRICT) \rightarrow MaintenanceResult`: Performs age-based and count-based session purging; commits internally. 

`prune_old_memories(db, older_than_days, mode=STRICT) \rightarrow MaintenanceResult`: Deletes old memories via `SQLiteMemoryDeleteStore`. 

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

`RetentionConfig` (frozen dataclass): Defines `max_sessions` (int=100, maximum sessions to retain) and `max_age_days` (int=90, purge sessions older than N days; 0 disables this). `RetentionConfig.from_config()` reads `agent.toml::sqlite_retention_max_sessions` and `agent.toml::sqlite_retention_max_age_days`.

---

## 4. DB Rotation (`db/rotation.py`)

From `db.rotation import rotate_session_db, rotate_workflow_db, rotate_all_dbs, rotate_db`:
- `rotate_session_db(archive_dir=None) \rightarrow Path`: Archives the session database with a timestamp suffix using the SQLite online backup API.
- `rotate_workflow_db(archive_dir=None) \rightarrow Path`: Archives the workflow database with a timestamp suffix.
- `rotate_all_dbs(archive_dir=None) \rightarrow tuple[Path, Path, Path]`: Archives all three databases, returning `(rag_dest, session_dest, workflow_dest)`.
- `rotate_db(archive_dir=None) \rightarrow tuple[Path, Path]`: Archives both rag and session databases, returning `(rag_dest, session_dest)`.

The archive directory defaults to `/opt/llm/db/archive` (from `agent.toml::sqlite_archive_dir`). The rotation format is `{stem}_{YYYYMMDD_HHMMSS}{suffix}` in the `archive_dir`. It uses the SQLite online backup API to ensure WAL integrity is preserved during rotation.

---

## 6. RAG Consistency Checks (`db/rag_consistency.py`)

From `db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues`:
```python
with SQLiteHelper('rag').open() as db:
    report = check_rag_consistency(db)
    if not is_consistent(report):
        for issue in summarize_issues(report):
            print(issue)
```

`check_rag_consistency(db, embed_failed=0) \rightarrow RagConsistencyReport`: A read-only report containing chunk/FTS/vec row counts and orphan detection. Note that `embed_failed` (the number of embedding failures known by the caller) is passed in but not detected by this function itself.

`is_consistent(report) \rightarrow bool`: Returns `True` if there are no orphans and the FTS gap is zero.

`summarize_issues(report) \rightarrow list[str]`: Provides human-readable issue descriptions.

**RagConsistencyReport (frozen dataclass):**
Contains `chunks` (int), `fts` (int), `vec` (int), `orphan_vec_count` (int), `fts_gap` (int: `chunks - fts`; positive means missing FTS entries), `fts_orphan_count` (int: `fts - chunks`; positive means extra FTS entries/data loss risk), `embed_failed` (int=0, caller-supplied), `issues` (tuple[str,...], populated by `summarize_issues(report)`), and optional diagnostic identifiers: `affected_chunk_ids` (up to 10 chunk IDs missing from FTS), `affected_doc_ids` (up to 10 doc IDs whose chunks are missing from FTS), and `affected_orphan_chunk_ids`/`affected_orphan_urls` (up to 10 items for orphaned vector rows).

**Implementation Details:**
- `is_consistent` condition: `fts_gap == 0 and fts_orphan_count == 0 and orphan_vec_count == 0 and vec == chunks`.
- `check_rag_consistency` automatically calls `summarize_issues(report)` and populates the `issues` field in the report.
- Diagnostic identifier lists (`affected_*`) are only populated when `fts_gap > 0` or `orphan_vec_count > 0`.

---
