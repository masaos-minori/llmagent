# Implementation Procedure: Delete RagDbMaintenanceService from scripts/rag/maintenance.py

## Goal

Delete the dead-code `RagDbMaintenanceService` class and all three methods (`rotate`, `rebuild_fts`, `vacuum`) from `scripts/rag/maintenance.py`. This eliminates a latent risk of silent FTS5 corruption if the class were ever wired up as a caller.

## Scope

Delete the entire `RagDbMaintenanceService` class definition (lines 8-52) from `scripts/rag/maintenance.py`. After deletion, the file will contain only the module docstring and imports.

## Assumptions

- The production-called implementation is `RagMaintenanceService.rebuild_fts()` in `scripts/agent/services/rag_maintenance_service.py`, which correctly uses `content='chunks', content_rowid='chunk_id'` mapping.
- No other code depends on `RagDbMaintenanceService` — confirmed via `rg -n "RagDbMaintenanceService"` showing only `scripts/rag/maintenance.py` and `tests/db/test_db_maintenance.py` as references.
- The `SQLiteHelper` import on line 5 remains needed for other potential future use; do not remove it unless vulture confirms it is also unused after this change.

## Design decisions

- **Delete vs. refactor**: Deletion is preferred over refactoring because the class has no callers and its divergent behavior would cause silent corruption if wired up incorrectly.
- **Import cleanup**: If `SQLiteHelper` is unused after removing the class, remove the import as well.

## Alternatives considered

- **Refactor to align with production schema**: Would require adding `content='chunks', content_rowid='chunk_id'` to the FTS5 table creation and recreating all three triggers. Not worth the effort for dead code.
- **Deprecate and migrate callers gradually**: No callers exist today, so gradual migration is unnecessary.

## Implementation

### Target file

`scripts/rag/maintenance.py`

### Procedure

1. Delete the entire `RagDbMaintenanceService` class (line 8 to end of file, line 52).
2. Check if the `SQLiteHelper` import (line 5) is still needed. If the file becomes empty except for the module docstring and possibly the import, evaluate whether to keep or remove the import.
3. If `SQLiteHelper` is unused after deletion, remove the import line.

### Method

Edit `scripts/rag/maintenance.py` using the Write tool to replace the file content with the module docstring and any remaining necessary imports (if any).

### Details

Current file structure:
```
Line 1: """scripts/rag/maintenance.py — RAG-specific database maintenance operations."""
Line 2: <blank>
Line 3: from __future__ import annotations
Line 4: <blank>
Line 5: from db.helper import SQLiteHelper
Line 6: <blank>
Lines 8-52: class RagDbMaintenanceService: ...
```

After deletion:
- If `SQLiteHelper` is still used elsewhere in the file (it is not — the class was the only consumer), keep the import.
- If `SQLiteHelper` is unused, the resulting file is:
```
"""scripts/rag/maintenance.py — RAG-specific database maintenance operations."""

from __future__ import annotations
```

Verify with `uv run vulture scripts/rag/maintenance.py --min-confidence 60` that no new unused-import warnings appear.

## Compatibility considerations

- The `RagDbMaintenanceService` class is not part of any public API and has no production callers. Deleting it does not affect existing integrations.
- The real implementation `RagMaintenanceService` in `scripts/agent/services/rag_maintenance_service.py` is unaffected.

## Security considerations

N/A: Dead-code removal has no security impact.

## Rollback considerations

To rollback, restore the deleted class from git history:
```bash
git checkout HEAD~1 -- scripts/rag/maintenance.py
```
No data migration or configuration changes are involved.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| scripts/rag/maintenance.py | Verify class removed | Manual review + rg | `rg -n "RagDbMaintenanceService" scripts/rag/maintenance.py` returns no results |
| scripts/rag/maintenance.py | Lint check | `uv run ruff check scripts/rag/maintenance.py` | No errors |
| scripts/rag/maintenance.py | Type check | `uv run mypy scripts/rag/maintenance.py` | No type errors |
| scripts/rag/maintenance.py | Unused import check | `uv run vulture scripts/rag/maintenance.py --min-confidence 60` | No new unused-import warnings |

## Completion criteria

- `RagDbMaintenanceService` class and all three methods are removed from `scripts/rag/maintenance.py`.
- The file passes `ruff check` with no errors.
- The file passes `mypy` with no type errors.
- No new unused-import warnings from vulture.

## Out of scope

- Modifying `scripts/agent/services/rag_maintenance_service.py` — the real, production-called implementation must remain untouched.
- Modifying `scripts/db/schema_sql.py` — defines the correct schema.
- Reconciling the two `rebuild_fts()` implementations — deletion is the preferred approach.
- Updating `tests/db/test_db_maintenance.py` — covered by a separate procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete RagDbMaintenanceService class and all three methods from scripts/rag/maintenance.py | Pending | — | — | |
| 2 | Run lint/type checks on scripts/rag/maintenance.py | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260920-211327_dead_code_RagDbMaintenanceService_diverges_from_production_schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-213943_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-060545
- **Related target files**: scripts/rag/maintenance.py
