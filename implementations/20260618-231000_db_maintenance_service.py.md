# Design: Remove document methods from DbMaintenanceService

## Goal
Remove `list_documents()` and `delete_document()` methods from `DbMaintenanceService` since they are being moved to rag-pipeline-mcp.

## Target File
- `scripts/agent/services/db_maintenance_service.py`

## Current State (lines 108-153)
```python
def list_documents(self, lang: str | None = None, limit: int = 20) -> list[dict]:
    """Return registered documents as structured data (delegates to rag.sqlite)."""
    # ... SQL query logic (lines 110-134)

def delete_document(self, url: str) -> bool:
    """Delete a document and its chunks from DB by URL (delegates to rag.sqlite)."""
    # ... SQL delete logic (lines 136-153)
```

## Implementation Steps

### Step 1: Remove list_documents method
Delete lines 108-134 (the entire `list_documents` method including docstring).

### Step 2: Remove delete_document method
Delete lines 136-153 (the entire `delete_document` method including docstring).

### Step 3: Verify no other callers
- `cmd_db.py` currently calls both methods via `DbMaintenanceService()`
- After Step 4 of the plan (rewiring cmd_db.py to use MCP), these calls will be replaced with MCP tool calls
- No other files in `scripts/agent/` reference these methods

### Step 4: Verify DbStats is unaffected
- `stats()` method (lines 36-44) uses `_count_table("documents")` and `_count_table("chunks")` — these are unrelated to list/delete document operations
- `DbStats.docs` and `DbStats.chunks` fields remain needed for `/db stats` command

## Completion Criteria
- `DbMaintenanceService` has no `list_documents()` or `delete_document()` methods
- All other methods (`stats`, `rebuild_fts`, `health`, `checkpoint`, `vacuum`, `purge`, `recover`, `consistency`) remain unchanged
- No import errors or circular dependencies introduced
