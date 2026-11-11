---
title: "DB API and Operations - Recovery and Reference"
area: shared
tags:
  - shared
  - db
  - corruption-recovery
  - error-handling
  - verification
  - ai-reference
related:
  - shared_00_document-guide.md
  - db_04_api_and_operations-module-boundaries-and-helper.md
  - db_05_api_and_operations-protocol-and-backend.md
  - db_06_api_and_operations-maintenance-and-rotation.md
  - db_01_architecture_and_schema-overview-and-config.md
  - adr_02_05_008_db-sqlite-4db-separation.md
---

# DB API and Operations

- Schema → [db_01_architecture_and_schema-overview-and-config.md](db_01_architecture_and_schema-overview-and-config.md)

## 9. Corruption Recovery

### 9.1 Purpose

Database recovery exists to restore a usable persistence state after physical corruption without destroying the only recoverable copy, and without misclassifying transient operational failures (lock contention, permission errors, disk I/O or capacity errors) as physical corruption that warrants backup restoration.

### 9.2 Responsibility boundaries

- **Integrity checking** (`_run_integrity_check()`): determines whether the target database can be opened and runs SQLite integrity verification. It MUST NOT itself replace the database, delete the damaged file, or select an unverified backup.
- **physical-recovery coordinator** (`recover_corruption()`): interprets the integrity result, applies recovery policy, and returns a structured `RecoveryResult`.
- **restore file staging** (`scripts/db/recovery_restore.py`, `_stage_restore()` and its helpers): performs the filesystem steps a restore needs — quarantine the stale `-wal`/`-shm` sidecars (resolved from the full database filename: `rag.sqlite` → `rag.sqlite-wal` / `rag.sqlite-shm`), archive the damaged file, and stage the backup plus its sidecars at a temporary candidate location. Staging only: it does NOT perform the atomic swap — activation is performed by `recover_corruption()` in `db/recovery.py` after candidate verification. Staging is fail-closed: a quarantine/copy/move failure raises `OSError` for the caller's cleanup handler instead of logging a warning and proceeding. It applies no recovery policy and returns no `RecoveryResult`; `db/recovery.py` decides when and whether staging runs.
- **logical verification** (`scripts/db/recovery_verification.py`, `_run_logical_verification()` and its verifiers): dispatches the target to the consistency contract defined for its domain (`check_rag_consistency`/`check_session_consistency`) — on the staged candidate before activation and again as the post-activation re-check — and summarizes an inconsistent report as counts/identifiers only. It decides no policy and returns no `RecoveryResult`; a mandatory logical-verification gap fails closed as `verification_unavailable` (a database this stage cannot open, or a mandatory domain with no registered verifier) and blocks activation; `db/recovery.py` maps it to the `verification_unavailable` action value. Non-mandatory targets (`workflow`, `eventbus`) keep the skip result.
- **Backup provider**: the caller-supplied `backup_path`. Nothing in the current implementation validates the backup's own integrity before it is used — see 9.4 and 9.5.
- **Startup orchestration**: no current caller invokes `recover_corruption()` during agent startup (invocation sites are limited to the manual `/session recover` CLI path). Startup-time DB failures are handled by a separate, unrelated path (9.8).

### 9.3 Integrity-result model

Current implementation produces a structured classification via the `DbCondition` enum (`scripts/db/recovery.py`). `_run_integrity_check()` returns `tuple[DbCondition, str | None]`; callers distinguish outcomes by the `DbCondition` value, not by `RecoveryResult.action`/`detail` alone. The enum distinguishes: `HEALTHY`, `CORRUPTION`, `LOCK_CONTENTION`, `PERMISSION_FAILURE`, `INVALID_FORMAT`, and `UNKNOWN`. Downstream recovery policy depends on this structured classification, not on free-form error text.

### 9.4 Exception policy

- **Current behavior:** `_run_integrity_check()` catches **all** exceptions (`except Exception`) and dispatches them to `_classify_error()` which classifies them into `DbCondition` values. `sqlite3.DatabaseError` — the exception SQLite raises for physical page corruption — is caught and classified as `DbCondition.CORRUPTION`.
- **Invariants satisfied** (enforced by `_classify_error()` and `recover_corruption()` in `scripts/db/recovery.py`):
  - `sqlite3.DatabaseError` does NOT escape the public recovery boundary as an unclassified failure.
  - Catching an exception does NOT automatically trigger backup restoration.
  - Lock contention is NOT classified as physical corruption: "database is locked" or "busy" maps to `DbCondition.LOCK_CONTENTION`, and `recover_corruption()` short-circuits to `action="error"` before reaching the restore branch.
  - Permission failure is NOT classified as physical corruption: "permission denied" or "readonly" maps to `DbCondition.PERMISSION_FAILURE`.
  - Disk I/O or capacity failure does NOT cause the target database to be overwritten.
  - Unknown errors preserve the target database and require operator intervention (`DbCondition.UNKNOWN`).
- The `action="error"` result value still conflates lock contention, permission errors, and unclassified integrity-check failures into one label; callers do not branch on cause, only on `success`/`action` (a design weakness, not a corruption-misclassification risk).

### 9.5 Safe restoration sequence

Target sequence: detect and classify → preserve the damaged database → locate a candidate backup → validate the candidate independently → restore to a temporary location → verify the restored copy → atomically replace the target → reopen and verify → return a structured result → gate startup on the persistence-domain policy.

**Current implementation status against this sequence** (`db/recovery.py::_restore_from_backup`, with the staging steps in `db/recovery_restore.py::_stage_restore` and activation in `db/recovery.py::_activate_candidate`):

- The damaged database IS preserved (`shutil.copy2` to a timestamped `_corrupt_` archive) on all recovery paths, including the no-backup path where `_run_integrity_check()` returns a failed-but-parseable result.
- Backup integrity IS verified before use (`_run_integrity_check(backup, target)`). A corrupted backup is detected and rejected.
- Restoration IS atomic and verifies before activating: `_stage_restore()` copies the backup and its `-wal`/`-shm` sidecars to a temporary candidate location, `_verify_candidate()` runs `_run_integrity_check` and `_run_logical_verification` on the staged candidate, and only a fully verified candidate is activated by a single atomic `os.replace` of the database plus a move of each sidecar to its final full-filename location (`<db>.sqlite-wal` / `<db>.sqlite-shm`). A candidate that fails verification is never activated: the live database is untouched and the result reports `active_db_state="preserved_original"`. A mid-staging failure raises for `_restore_from_backup()`'s `OSError` handler, which cleans up the half-written temp files and preserves the archive.
- The restored database IS reopened and re-verified before success is reported (`_run_integrity_check(db_path, target)` followed by the logical re-check in `_post_restore_failure()`).
- The logical-verification stage runs on the candidate before activation and again after activation; a failure before activation leaves the original in place, and a post-activation failure triggers a rollback that restores the archived original (`active_db_state="preserved_original"`, actions `restore_verify_failed` / `logical_verify_failed` / `verification_unavailable`). If the rollback itself fails the result reports `action="rollback_failed"` with `active_db_state="non_serviceable"`, preserving every artifact.
- Result contract: `RecoveryResult.active_db_state` ∈ {`restored`, `preserved_original`, `non_serviceable`} names the database state that is actually active after the attempt, and `logical_ok` is a definite `True`/`False` on every restore path. The `verification_unavailable` action value marks a mandatory logical-verification gap; `rollback_failed` marks a failed rollback.
- Exclusive-access requirement: a restore assumes no other writer on the target database while it runs. No stop/lock helper implementing this exists in `scripts/db/` or the service layer; the requirement is met by the operator triggering recovery manually (ADR-008's operator-intervention posture), not by an implemented exclusive-access mechanism.

### 9.5a Automated vs. operator-only breakdown

`check_rag_consistency()` / `check_session_consistency()` run automatically after a restore and check FTS index health and chunk-to-FTS referential integrity (RAG), table existence and orphaned messages / memory links (Session); both domains verify read-only. The logical-verification stage only **recommends** repair and never performs it. Repair is operator-triggered: `/session rag-rebuild-fts`, `/session rag-rebuild-vec`, or manual session data repair.

### 9.6 Dry Run contract

- `dry_run=True` MUST NOT move, replace, truncate, delete, or rewrite the target database — **current behavior satisfies this on the normal path**: `_result_for_condition()` returns `_dry_run_integrity_ok()` before either `_vacuum_db()` or `_restore_from_backup()` is called (verified by the dry-run tests in `tests/db/`).
- On the physical-corruption path, `sqlite3.DatabaseError` is caught by `_classify_error()` and classified as `DbCondition.CORRUPTION` (9.4); the dry-run branch then returns a `RecoveryResult` without modifying the target file (the dry-run guarantee holds by design, not coincidence).

### 9.7 Persistence-domain policy

Recovery policy differs by data ownership; `recover_corruption()` supports multiple targets via the `target` parameter. See [ADR-008](../10_adr/adr_02_05_008_db-sqlite-4db-separation.md) Decision Details #20 for the canonical physical-recovery policy across all four DB domains. See ADR-008's Recovery Policy Matrix for the full per-domain policy comparison.

- **Reconstructable derived data** (RAG full-text/vector indexes): authoritative source is the `chunks` table. `RagMaintenanceService`'s consistency check and rebuild operations reconstruct these indexes independently of `recover_corruption()`. Post-restoration logical verification (`check_rag_consistency()`) runs automatically after recovery and reports FTS/index inconsistencies as operator-only recommendations (see §9.5).
- **Session data**: covered by `recover_corruption(target='session')`. Backup restoration is performed for this domain only inside an operator-initiated `recover_corruption()` call (ADR-008); it is never triggered automatically. Post-restoration logical verification (`check_session_consistency()`) runs automatically after recovery and reports orphaned records as operator-only recommendations (see §9.5).
- **RAG data**: covered by `recover_corruption(target='rag')` (default). Backup restoration is performed for this domain only inside an operator-initiated `recover_corruption()` call (ADR-008); it is never triggered automatically. Post-restoration logical verification (`check_rag_consistency()`) runs automatically after recovery and reports FTS/index inconsistencies as operator-only recommendations (see §9.5).
- **Workflow data** (`workflow.sqlite`): has **no automatic physical-corruption recovery path**. Calling `recover_corruption(target='workflow')` returns `no_recovery_allowed` (ADR-008 Decision Details #20).
- **Event delivery state** (`eventbus.sqlite`): has **no corruption-recovery path**, but **is included in backup rotation**. Calling `recover_corruption(target='eventbus')` returns `unsupported_target` (eventbus is not an Agent-side target); `rotate_all_dbs()` archives the rag, session, and workflow databases and the EventBus-owned tool archives `eventbus.sqlite` (`python -m eventbus.db_tools rotate`), but no automated *restoration* path consumes that archive for this domain (ADR-008 Decision Details #20).

Failure to recover required workflow or event-delivery state MUST NOT be silently hidden by automatic reinitialization; neither domain has an automatic reinitialization path, so this invariant holds by design enforcement (`recover_corruption()` returns `no_recovery_allowed` for `workflow`/`eventbus` targets).

This physical policy is distinct from the automatic **logical** recovery of stale workflow attempts at agent startup, which touches no file-level restore: `StateStore.recover_stale_attempts()` (invoked from `agent/orchestrator.py` construction) marks lease-expired running attempts — and lease-less rows past the legacy age threshold — `failed` via a compare-and-swap UPDATE and deletes the `processed_events` rows of their (`task_id`, `stage_id`) pair in the same transaction, so a resumed stage re-executes instead of being permanently skipped; attempts with a live lease are left running. In the same transaction, every task whose last live attempt was just failed — still `running` with no remaining live attempt — is reconciled to `failed` through the validated task-ops helper; the recovery report counts gain a reconciled-task count `tasks_reconciled` (new) alongside the attempt-recovery counts, and `halted` or `completed` tasks are never reconciled. `StateStore.purge_finished_workflow_events()` then deletes `processed_events` rows whose task is terminal (`completed`/`failed`/`halted`) with `updated_at` past a fixed 30-day horizon and logs the deleted count; `tasks`/`attempts` rows are never pruned (schema-level retention narrative: [db_02 section 7](db_02_architecture_and_schema-schema-reference.md#7-workflowsqlite-schema)).

### 9.8 Operational considerations

- `recover_corruption()` is never invoked automatically; it is a manual, operator-triggered CLI action. There is no bounded retry loop or retry-count concept in the implementation.
- At startup, a `sqlite3.Error` raised while opening the session store is treated as fatal: the REPL reports the failure and re-raises as `RuntimeError`, stopping startup without attempting automatic recovery (`agent/repl.py`).
- At startup, a failed RAG *logical* consistency check (unrelated to physical corruption) is treated as a non-critical, skippable finding and does not stop startup (`agent/startup.py`).
- Log and error-detail fields observed in this code path carry file paths, archive names, and raw SQLite exception text; inspection found no code path that writes row-level DB content (message bodies) into logs (strongly implied by code, not an exhaustive proof).

### 9.9 Implementation references

Representative enforcement points: `recover_corruption()`, `_run_integrity_check()` and `_restore_from_backup()` in `scripts/db/recovery.py`.

---

## 10. Error Handling

Busy/locked `sqlite3.OperationalError` waits automatically via `PRAGMA busy_timeout` (from `agent.toml::sqlite_busy_timeout_ms`). `sqlite3.IntegrityError` propagates to the caller. A `sqlite-vec` load error fails the connection with `sqlite3.OperationalError`. Schema DDL failures are re-thrown from `executescript()`. Maintenance failures follow the `STRICT` (propagate) / `BEST_EFFORT` (return `MaintenanceResult(success=False)`) contract in `db_06`; `commit()` and `close()` error semantics are in `db_04`.

**Integrity check failure:** physical corruption is classified as `DbCondition.CORRUPTION` and never propagates uncaught; `recover_corruption()` acts on the classification, not the raw exception. See [section 9.4 Exception policy](#94-exception-policy).

---

## 11. DB Recreation Procedure

Schema changes require DB recreation — a migration feature does not exist. Automatic migration and version stamping are not supported for any domain: a database whose shape does not match the current canonical schema by the shared fingerprint is never repaired in place, stamped, or rewritten. It must be archived (step 1) before it is removed (step 2), then recreated from the current schema (step 3). **Step 1: Archive** — execute `rotate_all_dbs()` to archive the rag, session, and workflow databases and `python -m eventbus.db_tools rotate` to archive `eventbus.sqlite`. **Step 2: Delete** — manually delete DB files; paths are resolved from `agent.toml` `rag_db_path`/`session_db_path`/`workflow_db_path` keys (`db/config.py::DbConfig`); the `eventbus.sqlite` path is the `db_path` of `config/eventbus.toml`, and `deploy/init_db.sh` recreates it through `python -m eventbus.db_tools ensure`, so include that file if deleting **Step 3: Recreate** — execute `create_schema()` to initialize empty DBs. 

**Important notes:** 
- Recreated DBs are empty — existing records are not automatically migrated.
- `create_schema()` is a wrapper calling `create_rag_schema()` → `create_session_schema()` → `create_workflow_schema()` unconditionally and sequentially; each schema DDL is protected by `IF NOT EXISTS` so it is idempotent even against existing files.
- If you only need to recreate one DB, use the individual functions: `create_rag_schema()`, `create_session_schema()`, `create_workflow_schema()`; `eventbus.sqlite` is created or validated by `python -m eventbus.db_tools ensure`.
- **Archived files are verified recovery points.** `rotate_all_dbs()` archives each database through `_archive_db_file()`, which runs the integrity check on every domain and the domain-identity check where a required table is defined before returning the copy; a failing archive raises and is left in place, named in the error, for re-rotation or investigation. Recovery drills (section 12) restore from these verified archives.

### 11a. Identifying a Database's Current Schema

To see which schema a database has without changing it, open the file read-only (`mode=ro`). Replace each placeholder with the path from the configuration (`mdq.sqlite`: `db_path` in `config/mdq_mcp_server.toml`). The supported baseline is defined in [DB migration and scaling](db_03_architecture_and_schema-migration-and-scaling.md) (section 8e).

```bash
# workflow.sqlite: table inventory — the five task tables must be present
sqlite3 "file:<workflow_db_path>?mode=ro" \
  "SELECT group_concat(name) FROM sqlite_master WHERE type='table';"

# eventbus.sqlite: column names of its three tables
sqlite3 "file:<eventbus db_path from config/eventbus.toml>?mode=ro" \
  "SELECT group_concat(name) FROM pragma_table_info('events');
   SELECT group_concat(name) FROM pragma_table_info('consumer_delivery');
   SELECT group_concat(name) FROM pragma_table_info('consumer_offsets');"

# mdq.sqlite: first column of the chunk table
sqlite3 "file:<mdq_db_path>?mode=ro" \
  "SELECT name FROM pragma_table_info('chunks') LIMIT 1;"
```

A database at the supported baseline shows:

- `workflow.sqlite`: `tasks`, `attempts`, `processed_events`, `artifacts`, `tool_call_state` present and the whole shape matching the canonical workflow DDL by the shared fingerprint; a fingerprint mismatch fails startup.
- `eventbus.sqlite`: `events` without `retry_count`; `consumer_delivery` with `acked` and without `acked_at`; `consumer_offsets` with `offset`.
- `mdq.sqlite`: `chunk_id` as the first `chunks` column.

A database that does not match is recreated (section 11), not migrated. The EventBus service accepts `eventbus.sqlite` only when its shape matches the canonical DDL by the shared fingerprint; a mismatch is refused.

---

## 12. Recovery Drills

A recovery drill exercises the restore path for each persistence domain without touching the live database. The harness (`scripts/db/recovery_drill.py`) takes a recovery point through the rotation code path, restores it into an isolated copy, runs per-domain verification against that copy only, and writes one JSON audit artifact per domain. The live database file is never rewritten: the backup is a WAL-consistent read-only copy produced by the SQLite online backup API.

Run the full sweep across all four domains:

```bash
scripts/db/recovery_drill.py --domain all
```

Drill a single domain:

```bash
scripts/db/recovery_drill.py --domain workflow
scripts/db/recovery_drill.py --domain eventbus
scripts/db/recovery_drill.py --domain rag
scripts/db/recovery_drill.py --domain session
```

Exit code is `0` when every drilled domain passes and `1` when any domain fails. Deploy/init can invoke this as an opt-in hook after restore (deploy row 13) so a failing drill surfaces at deploy time.

**Artifact location and fields.** Each domain writes `{drill_dir}/{domain}_{timestamp}.json`, where `drill_dir` defaults to `<archive-dir>/drills` and `archive_dir` resolves from the `agent.toml` `sqlite_archive_dir` key (`rotation.py` falls back to a hardcoded default when the key is unset; the directory may not exist until the first rotation). Fields:

| Field | Meaning for RPO / RTO reading |
|-------|-------------------------------|
| `domain` | Persistence domain drilled. |
| `policy` | `recreate` for every domain: the drill records the current-schema-only recovery policy (the former per-domain `migrate` policy and its ledger fields were removed by the compatrm001 plan). |
| `archive_path` / `archive_ts` | The verified recovery point and the time it was taken. |
| `rto_seconds` | Measured restore-and-verify wall time (restore start to completion). Measurement semantics, not a threshold. |
| `backup_duration_seconds` | Archive elapsed time: archive completion minus archive start. The field formerly (mis)labeled `rpo_window_seconds`. Measurement semantics, not a threshold. |
| `rpo_seconds` | Recovery-point age at the assumed failure time: assumed-failure timestamp minus archive completion (staleness of the recovery point). Measurement semantics, not a threshold. The assumed-failure event is a documented operational decision (see UNK-05). |
| `integrity` | Boolean: the restored copy passed the integrity check. |
| `verification` | Per-domain checks (`integrity`, `required_table_<domain>`, plus per-domain fields). |
| `error` | Populated when the drill could not complete; the artifact is still written. |

> The drill artifact field `rpo_window_seconds` was renamed to
> `backup_duration_seconds`; `rpo_seconds` and `rto_seconds` are now defined as
> distinct measurements derived from recorded event timestamps.

Frequency and artifact retention are owner decisions tracked under UNK-01; this section states the procedure only. {defer the drill cadence and the artifact retention window until UNK-01}

---

## 13. Verification Plan

Schema initialization and DB maintenance are covered by `tests/db/` (`pytest tests/db/`), with `mypy scripts/db/` for type checking. The full integration check is: create the DBs with `create_schema()`, then confirm all expected tables exist with `sqlite3 <db_path> ".tables"` for each database path configured in `agent.toml`.

---

## Keywords

- shared
- db
- corruption-recovery
- error-handling
- verification
- ai-reference
