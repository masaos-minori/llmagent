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

- `checkpoint_wal` flushes the WAL. The default mode comes from `agent.toml::sqlite_wal_checkpoint_mode` (a code-level default applies when the key is absent); an invalid mode raises `ValueError`.
- `vacuum_db` delegates to `db.vacuum()` and must be called outside an active transaction.
- `purge_old_sessions` performs age-based and count-based session purging and commits internally.
- `prune_old_memories` deletes old memories via `SQLiteMemoryDeleteStore`.

Each of `vacuum_db`, `purge_old_sessions` and `prune_old_memories` takes a `MaintenanceMode` and returns a `MaintenanceResult` (`success`, `action`, `mode`, optional failure `detail` and `data`).

**Mode Semantics:**
- **STRICT (Default):** Behaves as before mode introduction—exceptions propagate directly. A successful operation returns `MaintenanceResult(success=True)`.
- **BEST_EFFORT:** Exceptions are caught and logged as `ERROR`, then returned as `MaintenanceResult(success=False, detail=str(exc))`. Callers **MUST** check `result.success`.

`RetentionConfig` defines the session retention limits (`max_sessions` and `max_age_days`; 0 disables the age limit). `RetentionConfig.from_config()` reads them from `agent.toml::sqlite_retention_max_sessions` and `sqlite_retention_max_age_days`; defaults are in the dataclass.

---

## 7. DB Rotation (`db/rotation.py`)

`db/rotation.py` archives databases with a timestamp suffix using the SQLite online backup API: per-database rotation for session, workflow and eventbus, `rotate_all_dbs()` for all four databases (ADR-008), and `rotate_db()` for rag and session only.

The archive directory is read from `agent.toml::sqlite_archive_dir`, with a code-level default when the key is absent. The rotation format is `{stem}_{YYYYMMDD_HHMMSS}{suffix}` in the `archive_dir`. It uses the SQLite online backup API to ensure WAL integrity is preserved during rotation.

**Corrupt-archive retention (`CorruptArchiveRetentionConfig`, `db/maintenance.py`):** timestamped `*_corrupt_*` archives that `db.recovery` creates before restoring a database are pruned by two optional `agent.toml` keys. `sqlite_corrupt_archive_max_files` keeps the most recent N archives per source database, and `sqlite_corrupt_archive_max_age_days` deletes archives older than N days (`0` disables the age limit). Both keys fall back to in-code defaults when absent, and `ProductionConfigValidator` accepts them as known `agent.toml` keys.

---

## 8. RAG Consistency Checks (`db/rag_consistency.py`)

`check_rag_consistency(db, embed_failed=0) -> RagConsistencyReport`: A read-only report containing chunk/FTS/vec row counts and orphan detection. Note that `embed_failed` (the number of embedding failures known by the caller) is passed in but not detected by this function itself.

`is_consistent(report) -> bool`: Returns `True` when every rule in the module's `_CHECKS` group is clean: `fts_gap == 0`, `fts_orphan_count == 0`, `orphan_vec_count == 0`, `vec == chunks`, `documents_without_chunks_count == 0`, `chunks_without_vec_count == 0`, `duplicate_chunk_index_count == 0`, no `url_level_mismatches`, no `diagnostic_errors`, and `read_smoke_test_ok`.

`summarize_issues(report) -> list[str]`: Provides human-readable issue descriptions for the `_CHECKS` rules that are not clean, in tuple order.

`RagConsistencyReport` holds the chunk, FTS and vec row counts, orphan vector count, `fts_gap` (`chunks - fts`; positive means missing FTS entries), `fts_orphan_count` (`fts - chunks`; positive means extra FTS entries, a data-loss risk), the caller-supplied `embed_failed`, the issue strings, and up to 10 affected chunk, document and orphan identifiers for diagnosis.

**Implementation Details:**
- The rules are one `_CHECKS` tuple of `(clean predicate, issue builder)` pairs. `is_consistent` requires every predicate to hold; `summarize_issues` renders the builder of each predicate that does not. `diagnostic_errors` and `read_smoke_test_ok` are the two rules with no builder, so they make a report inconsistent without adding an issue string.
- **Read-only SQL probes** (`scripts/db/rag_consistency_queries.py`): the table-level count queries, the per-URL count queries, the top-10 affected-identifier queries, and the read smoke test. `check_rag_consistency()` calls them stage by stage, turns the `sqlite3.Error` a stage raises into a `diagnostic_errors` entry, and assembles the `RagConsistencyReport`. The `_CHECKS` rules, the issue builders, and the issue text stay in `db/rag_consistency.py`.
- `check_rag_consistency` automatically calls `summarize_issues(report)` and populates the `issues` field in the report.
- Diagnostic identifier lists (`affected_*`) are only populated when `fts_gap > 0` or `orphan_vec_count > 0`.

---

## Keywords

- shared
- db
- maintenance-rotation
