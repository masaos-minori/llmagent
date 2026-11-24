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

All functions accept the typed configuration supplied by the process that owns `config/agent.toml`, plus the `SQLiteHelper` instance where a database is involved, and delegate low-level operations to it. No `db/` module reads a configuration file.

- `checkpoint_wal` flushes the WAL. The default mode comes from `DbMaintenanceConfig.wal_checkpoint_mode`, which the owning process builds from `config/agent.toml::sqlite_wal_checkpoint_mode` (a code-level default applies when the key is absent); an invalid mode raises `ValueError`.
- `vacuum_db` delegates to `db.vacuum()` and must be called outside an active transaction. In BEST_EFFORT mode it catches any `sqlite3.Error` (not only `OperationalError`) plus `RuntimeError`.
- `purge_old_sessions` performs age-based and count-based session purging as one `BEGIN IMMEDIATE` transaction: both delete rules commit together, and a failure in either rule rolls back the whole purge — a failed BEST_EFFORT purge reports zero counts and leaves the sessions table unchanged. When an active-session guard is supplied, the guarded session is exempt from both retention rules and the exemption is reported in the result data.
- `prune_old_memories` is retired with the `/memory prune` command and removal-pending (SHARED-003); it is not a supported maintenance operation.

Each of `vacuum_db` and `purge_old_sessions` takes a `MaintenanceMode` and returns a `MaintenanceResult` (`success`, `action`, `mode`, optional failure `detail` and `data`).

**Mode Semantics:**
- **STRICT (Default):** Behaves as before mode introduction—exceptions propagate directly. A successful operation returns `MaintenanceResult(success=True)`.
- **BEST_EFFORT:** Database and filesystem errors are caught and logged as `ERROR`, then returned as `MaintenanceResult(success=False, detail=str(exc))`. Callers **MUST** check `result.success`. Configuration-construction failures (`DbMaintenanceConfig.from_mapping()` and `build_db_config()`) are the deliberate exception: the config file is read by the process that owns it, and `db/` validates only the mapping it is given, so a wrong-typed or negative value raises before the maintenance call and propagates in **both** modes, because a persistent misconfiguration must not hide behind per-run logs. The same holds for the retention `ValueError`s the delete helpers raise on negative limits — they are not `sqlite3.Error`s, so they propagate in both modes and the purge transaction rolls back with no partial deletions.

`RetentionConfig` defines the session retention limits (`max_sessions` and `max_age_days`; `0` disables the corresponding rule). The values come from `DbMaintenanceConfig`, the typed configuration supplied by the process that owns `config/agent.toml`; `RetentionConfig.from_typed()` is a pure projection of that object, and `from_mapping()` is where the keys are read as typed integers. A wrong type (including `bool`) or a negative value raises a key-naming `ValueError` at that construction. The delete helpers re-apply the same non-negative contract, so directly constructed configs fail the same way. Cutoffs compare against the canonical `T/Z` (UTC) stored timestamp format, and the count rule resolves equal-`created_at` ties deterministically: the lowest `session_id` is deleted first. Defaults are in the dataclass. When the purge comes from the agent command path, the session currently active in the agent is guarded and therefore exempt from both rules; when the exemption fires, the kept session count may exceed `max_sessions` by one.

---

## 7. DB Rotation (`db/rotation.py`)

`db/rotation.py` archives databases with a timestamp suffix using the SQLite online backup API: per-database rotation for session, workflow and eventbus, `rotate_all_dbs()` for all four databases (ADR-008), and `rotate_db()` for rag and session only.

The archive directory comes from `DbMaintenanceConfig.archive_dir`, which the process that owns `config/agent.toml` builds from that file's `sqlite_archive_dir` key; `rotation._resolve_archive_dir()` applies the documented code-level fallback when the key is absent. The rotation format is `{stem}_{YYYYMMDD_HHMMSS}{suffix}` in the `archive_dir`. It uses the SQLite online backup API to ensure WAL integrity is preserved during rotation.

**Corrupt-archive retention (`CorruptArchiveRetentionConfig`, `db/maintenance.py`):** timestamped `*_corrupt_*` archives that `db.recovery` creates before restoring a database are pruned by two optional `config/agent.toml` keys. `sqlite_corrupt_archive_max_files` keeps the most recent N archives per source database, and `sqlite_corrupt_archive_max_age_days` deletes archives older than N days (`0` disables the corresponding rule). Both values are typed integers read by the process that owns `config/agent.toml`, which supplies them to `db/` as a `DbMaintenanceConfig`; `CorruptArchiveRetentionConfig.from_typed()` projects that object, so no `db/` module reads the file. The same fail-closed contract applies at that construction (wrong type or negative value raises a key-naming `ValueError`), values fall back to in-code defaults when the keys are absent, and `ProductionConfigValidator` accepts the keys as known `config/agent.toml` keys because they are derived from `DbMaintenanceConfig`'s fields.

**Artifact retention (`ArtifactRetentionConfig`, `db/artifact_retention.py`):** the non-corrupt artifact classes — rotation archives, drill JSON audit artifacts, recovery sidecar-quarantine directories, and stale restore/drill working files — are swept by `purge_archive_artifacts()`, which runs on the same weekly schedule as `purge_corrupt_archives()` and receives the typed configuration rather than reading a file. Six optional `config/agent.toml` keys bound the first three classes: `sqlite_archive_max_files` / `sqlite_archive_max_age_days`, `sqlite_drill_artifact_max_files` / `sqlite_drill_artifact_max_age_days`, and `sqlite_quarantine_max_files` / `sqlite_quarantine_max_age_days`. Each class keeps the most recent N artifacts per source database and deletes artifacts older than N days (`0` disables the corresponding rule); the age rule runs before the count rule, and the newest archive and newest quarantine dir are never deleted even when older than the age limit (drill JSONs are pure audit history and carry no such minimum-keep protection). Stale `.tmp_` restore staging files and `_restored` drill working files older than one day are removed as a crashed-run backstop. `*_corrupt_*` archives are excluded from these sweeps — they belong to `purge_corrupt_archives()`. A quarantine directory is removed only when its full name matches the quarantine naming pattern and it is a directory. The six values follow the same typed-integer, fail-closed contract as the corrupt-retention values (wrong type, bool, or negative value raises a key-naming `ValueError` at the owner's construction; absent keys fall back to in-code defaults), reach `ArtifactRetentionConfig` through `DbMaintenanceConfig` and its `from_typed()` projection, and `ProductionConfigValidator` accepts the keys as known `config/agent.toml` keys because they are derived from `DbMaintenanceConfig`'s fields.

---

## 8. RAG Consistency Checks (`db/rag_consistency.py`)

`check_rag_consistency(db, embed_failed=0) -> RagConsistencyReport`: A read-only report containing chunk/FTS/vec row counts and orphan detection. Note that `embed_failed` (the number of embedding failures known by the caller) is passed in but not detected by this function itself.

`is_consistent(report) -> bool`: Returns `True` when every rule in the module's `_CHECKS` group is clean: `fts_gap == 0`, `fts_orphan_count == 0`, `orphan_vec_count == 0`, `vec == chunks`, `documents_without_chunks_count == 0`, `chunks_without_vec_count == 0`, `duplicate_chunk_index_count == 0`, no `url_level_mismatches`, `fk_inconsistency_count == 0`, `dimension_mismatch == 0`, `unknown_schema == 0`, no `diagnostic_errors`, `read_smoke_test_ok`, and no unverified-dimension flags (section 8.1).

`summarize_issues(report) -> list[str]`: Provides human-readable issue descriptions for the `_CHECKS` rules that are not clean, in tuple order.

`RagConsistencyReport` holds the chunk, FTS and vec row counts, orphan vector count, `fts_gap` (`chunks - fts`; positive means missing FTS entries), `fts_orphan_count` (`fts - chunks`; positive means extra FTS entries, a data-loss risk), the caller-supplied `embed_failed`, the issue strings, and up to 10 affected chunk, document and orphan identifiers for diagnosis.

**Implementation Details:**
- The rules are one `_CHECKS` tuple of `(clean predicate, issue builder)` pairs. `is_consistent` requires every predicate to hold; `summarize_issues` renders the builder of each predicate that does not. `diagnostic_errors`, `read_smoke_test_ok`, and the three unverified-dimension flags (section 8.1) are the rules with no builder, so they make a report inconsistent without adding an issue string.
- **Read-only SQL probes** (`scripts/db/rag_consistency_queries.py`): the table-level count queries, the per-URL count queries, the top-10 affected-identifier queries, and the read smoke test. `check_rag_consistency()` calls them stage by stage, turns the `sqlite3.Error` a stage raises into a `diagnostic_errors` entry, and assembles the `RagConsistencyReport`. The `_CHECKS` rules, the issue builders, and the issue text stay in `db/rag_consistency.py`.
- `check_rag_consistency` automatically calls `summarize_issues(report)` and populates the `issues` field in the report.
- Diagnostic identifier lists (`affected_*`) are only populated when `fts_gap > 0` or `orphan_vec_count > 0`.

### 8.1 Verification Status (unverified-dimension flags)

`RagConsistencyReport` carries per-dimension unverified flags `fk_unverified`, `embedding_unverified`, and `schema_unverified`, each defaulting to `False`. `check_rag_consistency` sets a flag when the corresponding probe (FK consistency, embedding dimension, schema recognition) raises `sqlite3.Error`, for example when the `sqlite-vec` extension is unavailable, and records a matching `diagnostic_errors` entry. Each probe runs under its own guard: a failed probe never cancels the other dimensions.

The flags are fail-closed `_CHECKS` rules alongside the numeric predicates above: a report with any flag set is inconsistent even when every numeric count is zero. An unverified dimension is never aggregated as a healthy zero.

Consumer expectations: recovery verification (`_verify_rag_logic`, `db/recovery_verification.py`) returns a verification failure whose count-only detail names the unverified dimension(s), and the recovery drill (`db/recovery_drill.py`) records `rag_consistency: false` in the rag artifact and fails the domain. An unverified dimension is a verification failure, not a pass.

---

## Keywords

- shared
- db
- maintenance-rotation
