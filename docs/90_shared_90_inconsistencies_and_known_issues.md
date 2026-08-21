---
title: "Shared/DB Inconsistencies and Known Issues"
category: shared
tags:
  - shared
  - db
  - inconsistency
  - known issue
  - bug
  - documentation gap
  - design concern
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_03_overview-constraints-and-reference.md
  - 90_shared_02_01_types_and_protocols-core-types.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
source:
  - 90_shared_90_inconsistencies_and_known_issues.md
---

## Migration Notes

Migration date: 2026-07-23; Source format: existing bullet format (Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference); Destination format: common template (17 fields); Note: existing entry content preserved; missing fields filled with 'unconfirmed'.

# Shared/DB Inconsistencies and Known Issues

This file records all known inconsistencies between documents, implementation bugs, undocumented areas, unimplemented features, and undefined behaviors within the `shared/` and `db/` layers.

Each item follows this format:
- **Type:** `Document Inconsistency` / `Implementation Bug` / `Undocumented` / `Unimplemented` / `Undefined` / `Needs Confirmation`

---

### SHARED-001: `recover_corruption()` propagates `sqlite3.DatabaseError` instead of catching it during physical page corruption

`recover_corruption()` propagates `sqlite3.DatabaseError` instead of catching it during physical page corruption. Status: open / Severity: High / Type: implementation-bug. Impact: An exception may occur when dealing with physically corrupted files. Action: Add `sqlite3.DatabaseError` (or the common base `sqlite3.Error`) to the `except` clause of `_run_integrity_check()`. Design reference: [90_shared_05_04 §9.4 Exception policy](90_shared_05_04_db_api_and_operations-recovery-and-reference.md#94-exception-policy).

---

### SHARED-002: Backup restoration is not validated, not atomic, and not re-verified after restore

`_restore_from_backup()` restores from a backup file whose own integrity is never checked (only `Path.exists()` is verified), copies directly onto the live target path via `shutil.copy2()` instead of through a temporary file with an atomic rename, and does not reopen or re-run an integrity check on the restored database before reporting `success=True`. Status: open / Severity: High / Type: design-gap. Impact: a corrupted backup can be restored unconditionally; a failure mid-copy can leave the target database partially written; a restore that produces a still-broken database is reported as successful. Action: validate the backup independently before use, restore through a temporary file with an atomic replace, and re-run integrity verification against the restored file before returning success. Design reference: [90_shared_05_04 §9.5 Safe restoration sequence](90_shared_05_04_db_api_and_operations-recovery-and-reference.md#95-safe-restoration-sequence).

---

### SHARED-003: `workflow.sqlite` and `eventbus.sqlite` have no physical-corruption recovery path

`recover_corruption()` only supports `target='rag'` or `target='session'`; passing any other value produces a mismatched display path while still opening an unintended database file. Neither `workflow.sqlite` (task/approval state) nor `eventbus.sqlite` (event delivery state) has any corruption-recovery or backup-rotation coverage — `rotate_all_dbs()` excludes both, and no other recovery path exists for either file. Status: open / Severity: High / Type: design-gap. Impact: physical corruption of workflow or event-delivery state has no recovery procedure at all; the only observed startup behavior for a broken session/workflow store is a fatal `RuntimeError` that stops the agent. Action: extend `target` validation to reject unsupported values explicitly (fail fast instead of falling back to a mismatched path), and decide and implement a recovery policy for the workflow and event-bus domains before relying on them as recoverable state. Design reference: [90_shared_05_04 §9.7 Persistence-domain policy](90_shared_05_04_db_api_and_operations-recovery-and-reference.md#97-persistence-domain-policy).

---
