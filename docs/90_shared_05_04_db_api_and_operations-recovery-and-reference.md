---
title: "DB API and Operations - Recovery and Reference"
category: shared
tags:
  - shared
  - db
  - corruption-recovery
  - error-handling
  - verification
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
  - 90_shared_05_02_db_api_and_operations-protocol-and-backend.md
  - 90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md
source:
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- Schema → [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md)

## 9. Corruption Recovery

### 9.1 Purpose

Database recovery exists to restore a usable persistence state after physical corruption without destroying the only recoverable copy, and without misclassifying transient operational failures (lock contention, permission errors, disk I/O or capacity errors) as physical corruption that warrants backup restoration.

### 9.2 Responsibility boundaries

- **Integrity checking** (`_run_integrity_check()`): determines whether the target database can be opened and runs SQLite integrity verification. It MUST NOT itself replace the database, delete the damaged file, or select an unverified backup.
- **Recovery coordinator** (`recover_corruption()`): interprets the integrity result, applies recovery policy, and returns a structured `RecoveryResult`.
- **Backup provider**: the caller-supplied `backup_path`. Nothing in the current implementation validates the backup's own integrity before it is used — see 9.4 and 9.5.
- **Startup orchestration**: no current caller invokes `recover_corruption()` during agent startup (Explicit in code — invocation sites are limited to the manual `/session recover` CLI path via `DbSessionOps.recover()` and `RagMaintenanceService.recover()`). Startup-time DB failures are handled by a separate, unrelated path (9.8).

### 9.3 Integrity-result model (target design)

The current implementation does not produce a structured classification; `_run_integrity_check()` returns either a check result or `None`, and callers distinguish outcomes only by inspecting `RecoveryResult.action`/`detail` (a free-form exception string) — **Needs confirmation / target design**. The target model MUST distinguish at least: healthy, confirmed corruption, temporarily unavailable (lock contention), inaccessible (permission), invalid format, and integrity-check failure of unknown cause. Downstream recovery policy MUST depend on this structured classification, not on free-form error text, once implemented.

### 9.4 Exception policy

- **Current behavior (Explicit in code, Known Issue [SHARED-001](90_shared_90_inconsistencies_and_known_issues.md)):** `_run_integrity_check()` catches only `sqlite3.OperationalError`, `ValueError`, and `RuntimeError`. `sqlite3.DatabaseError` — the exception SQLite raises for physical page corruption — is **not** caught and propagates uncaught out of `recover_corruption()`'s public boundary.
- **Target invariants:**
  - `sqlite3.DatabaseError` MUST NOT escape the public recovery boundary as an unclassified failure.
  - Catching an exception MUST NOT automatically trigger backup restoration.
  - Lock contention MUST NOT be classified as physical corruption. **Current behavior already satisfies this**: `sqlite3.OperationalError` (including "database is locked") causes `_run_integrity_check()` to return `None`, and `recover_corruption()` short-circuits to `action="error"` before reaching the restore branch (Explicit in code).
  - Permission failure MUST NOT be classified as physical corruption.
  - Disk I/O or capacity failure MUST NOT cause the target database to be overwritten.
  - Unknown errors MUST preserve the target database and require operator intervention.
- The `action="error"` result value currently conflates lock contention, permission errors, and unclassified integrity-check failures into one label; callers do not branch on cause, only on `success`/`action` (Explicit in code — this is a design weakness, not a corruption-misclassification risk).

### 9.5 Safe restoration sequence

Target sequence: detect and classify → preserve the damaged database → locate a candidate backup → validate the candidate independently → restore to a temporary location → verify the restored copy → atomically replace the target → reopen and verify → return a structured result → gate startup on the persistence-domain policy.

**Current implementation gaps against this sequence** (Explicit in code, `db/recovery.py::_restore_from_backup`):

- The damaged database is preserved (`shutil.copy2` to a timestamped `_corrupt_` archive) only on the path where `_run_integrity_check()` returns a failed-but-parseable result and a `backup_path` was supplied — not on the `sqlite3.DatabaseError`-propagation path or the no-backup path.
- The backup candidate is checked only for existence (`Path.exists()`); its own integrity is never verified before use. A corrupted backup is restored unconditionally.
- Restoration copies the backup directly onto the target path (`shutil.copy2(backup, db_path)`); it does not go through a temporary file, so the replacement is **not atomic**. A failure mid-copy can leave the target in a partially written state.
- The restored database is not reopened or re-verified after restoration; `RecoveryResult(success=True, action="restored")` is returned without confirming the copy is actually usable.

The target design's atomicity, backup-validation, and post-restore-verification requirements are open implementation gaps, not yet satisfied.

### 9.6 Dry Run contract

- `dry_run=True` MUST NOT move, replace, truncate, delete, or rewrite the target database — **current behavior satisfies this on the normal path**: `_handle_dry_run()` returns before either `_vacuum_db()` or `_restore_from_backup()` is called (Verified by test — `test_dry_run_returns_recovery_result`, `test_dry_run_integrity_failure`).
- On the physical-corruption path, `sqlite3.DatabaseError` propagates out of `_run_integrity_check()` before the dry-run branch is reached at all (9.4); the target file happens to remain unmodified, but this is a side effect of the uncaught exception, not a designed dry-run guarantee (Strongly implied by code — target design should not rely on this coincidence).

### 9.7 Persistence-domain policy

Recovery policy differs by data ownership; `recover_corruption()` itself only covers a subset of the persistence domains listed below.

- **Reconstructable derived data** (RAG full-text/vector indexes): authoritative source is the `chunks` table. `RagMaintenanceService`'s consistency check and rebuild operations reconstruct these indexes independently of `recover_corruption()`.
- **Session data**: covered by `recover_corruption(target='session')`. Passing any value other than `'rag'` or `'session'` to `target` is unsafe — the display-path branch falls back to the session path label while the real connection is opened against whatever string was passed to `SQLiteHelper(target)`, so callers MUST NOT pass `'workflow'` or `'eventbus'` (Explicit in code).
- **Workflow and approval data** (`workflow.sqlite`): has **no physical-corruption recovery path**. Startup only runs an application-level state rebuild (`_recover_pending_approvals()`) that assumes the database file itself opens successfully; it does not handle physical corruption.
- **Event delivery state** (`eventbus.sqlite`): has **no corruption-recovery or backup-rotation coverage at all** — `rotate_all_dbs()` and `recover_corruption()` both exclude this domain (Explicit in code, absence confirmed by inspection).

Failure to recover required workflow or event-delivery state MUST NOT be silently hidden by automatic reinitialization; today neither domain has an automatic reinitialization path, so this invariant holds by absence of implementation rather than by design enforcement — tracked as an open gap.

### 9.8 Operational considerations

- `recover_corruption()` is never invoked automatically; it is a manual, operator-triggered CLI action. There is no bounded retry loop or retry-count concept in the implementation (Explicit in code).
- At startup, a `sqlite3.Error` raised while opening the session store is treated as fatal: the REPL reports the failure and re-raises as `RuntimeError`, stopping startup without attempting automatic recovery (Explicit in code, `agent/repl.py`).
- At startup, a failed RAG *logical* consistency check (unrelated to physical corruption) is treated as a non-critical, skippable finding and does not stop startup (Explicit in code, `agent/startup.py` — comment: "non-critical maintenance check must not abort startup").
- Log and error-detail fields observed in this code path carry file paths, archive names, and raw SQLite exception text; no code path was found that writes row-level DB content (message bodies, approval reasons) into logs (Strongly implied by code — absence confirmed by inspection, not by exhaustive proof).

### 9.9 Implementation references

- `recover_corruption()`
- `_run_integrity_check()`
- `RecoveryResult`
- `_restore_from_backup()`
- `RagMaintenanceService`

---

## 10. Error Handling

`sqlite3.OperationalError` (busy/locked): automatic wait via `PRAGMA busy_timeout` (default 30 seconds); `sqlite3.IntegrityError`: propagates to caller; does not occur in upsert paths; `sqlite-vec` load error: `sqlite3.OperationalError` → connection failure; schema DDL failure: exception re-thrown from `executescript()`; `prune_old_memories` failure: `STRICT` — exception propagates; `BEST_EFFORT` — returns `MaintenanceResult(success=False)`; `commit()` error: WARNING logged + `sqlite3.OperationalError` re-thrown; `close()` error: WARNING logged only; no exception thrown.

**Integrity check failure (current behavior, corrected from prior wording):** `_run_integrity_check()` logs the error and, only for `sqlite3.OperationalError`/`ValueError`/`RuntimeError`, returns a failed check result that `recover_corruption()` may act on. It does **not** "attempt restore from backup" unconditionally — `sqlite3.DatabaseError` (physical corruption) propagates uncaught instead of reaching the restore branch at all. See [§9.4 Exception policy](#94-exception-policy) and Known Issue [SHARED-001](90_shared_90_inconsistencies_and_known_issues.md).

---

## 11. DB Recreation Procedure

Schema changes require DB recreation — a migration feature does not exist. **Step 1: Archive** — execute `rotate_all_dbs()` to archive all three production DBs. **Step 2: Delete** — manually delete DB files; paths are resolved from `agent.toml` `rag_db_path`/`session_db_path`/`workflow_db_path`/`eventbus_db_path` keys (`db/config.py::DbConfig`); `create_schema()` also recreates `eventbus.sqlite`, so include `/opt/llm/db/eventbus.sqlite` if deleting (Explicit in code — `db/create_schema.py`). **Step 3: Recreate** — execute `create_schema()` to initialize empty DBs. 

**Important notes:** 
- Recreated DBs are empty — existing records are not automatically migrated.
- `create_schema()` is a wrapper calling `create_rag_schema()` $\rightarrow$ `create_session_schema()` $\rightarrow$ `create_workflow_schema()` $\rightarrow$ `create_eventbus_schema()` unconditionally and sequentially; each schema DDL is protected by `IF NOT EXISTS` so it is idempotent even against existing files (Explicit in code — `db/create_schema.py`).
- A condition "initialize only if `eventbus.sqlite` does not exist" does not exist in the implementation; if you only need to recreate one DB, use the individual functions: `create_rag_schema()`, `create_session_schema()`, `create_workflow_schema()`, `create_eventbus_schema()`.

---

## 12. Verification Plan

Schema initialization: `pytest tests/test_create_schema.py`; DB maintenance: `pytest tests/test_db_maintenance.py`; Type check: `mypy scripts/db/`; Full integration: create DB $\rightarrow$ check all tables exist — `python -c 'from db.create_schema import create_schema; create_schema()'; sqlite3 /opt/llm/db/rag.sqlite ".tables"; sqlite3 /opt/llm/db/session.sqlite ".tables"'`.

---

## 13. AI Reference Guide

Open DB connection: `with SQLiteHelper('rag').open(row_factory=True) as db:`. Write atomically: `open(write_mode=True)` context within `with db.begin_immediate():`. What does `target='workflow'` connect to: `workflow.sqlite` — the task tracking DB. How to validate an embedding BLOB: `db.store.validate_embedding_blob(blob)`. How to purge old sessions: `purge_old_sessions(db, RetentionConfig(...))` — returns `MaintenanceResult`; check `.success`. How to recover from corruption: `recover_corruption(backup_path=..., target='rag')`. Does `prune_old_memories` catch exceptions: `STRICT` (default) — propagates; `BEST_EFFORT` — caught and stored in `MaintenanceResult`. How to use `BEST_EFFORT` mode: pass `mode=MaintenanceMode.BEST_EFFORT` to `vacuum_db`, `purge_old_sessions`, `prune_old_memories`. How to verify RAG consistency: `check_rag_consistency(db)` $\rightarrow$ `is_consistent(report)` + `summarize_issues(report)`.
