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

`recover_corruption()` propagates `sqlite3.DatabaseError` instead of catching it during physical page corruption. Status: open / Severity: High / Type: implementation-bug. Impact: An exception may occur when dealing with physically corrupted files. Action: Add `sqlite3.DatabaseError` (or the common base `sqlite3.Error`) to the `except` clause of `_run_integrity_check()`.

---
