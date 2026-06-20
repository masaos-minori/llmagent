# Implementation: rag_maintenance_service.py (new file)

## Goal

Extract all rag.sqlite-targeted operations from `DbMaintenanceService` into a new
`RagMaintenanceService` class, so RAG-layer maintenance has a clear, single-responsibility
service boundary separate from session.sqlite operations.

## Scope

**In:**
- Create `scripts/agent/services/rag_maintenance_service.py` with methods:
  `stats_rag()`, `rebuild_fts()`, `consistency()`, `recover()`
- Each method operates exclusively on `SQLiteHelper("rag")`
- Import and use `RagMaintenanceService` from `cmd_db.py` for RAG-targeted subcommands

**Out:**
- Changing `db/maintenance.py` core functions
- Modifying `DbStats` data model
- Adding new MCP servers

## Assumptions

- `SQLiteHelper("rag")` opens `rag.sqlite` at the configured path
- `db.maintenance` functions (`check_rag_consistency`, `rebuild_fts`, `recover_corruption`,
  `is_consistent`, `summarize_issues`) are stable and do not change
- `DbMaintenanceService` will be updated in a separate step to remove the methods moved here
- `cmd_db.py` imports `RagMaintenanceService` in addition to (or instead of)
  `DbMaintenanceService` for RAG subcommands

## Implementation

### Target file

`scripts/agent/services/rag_maintenance_service.py`

### Procedure

1. Create `rag_maintenance_service.py` in `scripts/agent/services/`
2. Move `rebuild_fts()`, `consistency()`, `recover()` from `DbMaintenanceService`
3. Add `stats_rag()` returning only `docs` and `chunks` counts (subset of current `stats()`)
4. Ensure no imports from `agent.*` (avoid circular); only import from `db.*`

### Method

New class `RagMaintenanceService` with the following public methods:

```python
from db.helper import SQLiteHelper
from db.maintenance import (
    check_rag_consistency,
    is_consistent,
    recover_corruption,
    summarize_issues,
)
from agent.services.models import DbRecoverResult

class RagMaintenanceService:
    def stats_rag(self) -> tuple[int, int]:
        """Return (docs, chunks) counts from rag.sqlite."""
        ...

    def rebuild_fts(self) -> None:
        """Rebuild the FTS5 search index in rag.sqlite."""
        ...

    def consistency(self) -> tuple[bool, list[str]]:
        """Run search index synchronization check; return (ok, issues)."""
        ...

    def recover(self, backup_path: str | None) -> DbRecoverResult:
        """Integrity check; restore from backup_path if corruption found."""
        ...
```

### Details

- `stats_rag()` executes `SELECT COUNT(*) FROM documents` and `SELECT COUNT(*) FROM chunks`
  on `SQLiteHelper("rag").open(row_factory=True)`; returns `(docs, chunks)` as a plain tuple
  or a dedicated `RagStats` dataclass if `DbStats` is split in a subsequent step
- `rebuild_fts()` executes `INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')` — identical
  to the current `DbMaintenanceService.rebuild_fts()` body
- `consistency()` delegates to `check_rag_consistency(db)` + `is_consistent(report)` +
  `summarize_issues(report)` — identical to current body
- `recover()` delegates to `recover_corruption(backup_path)` — identical to current body
- Module docstring must state: "Operates exclusively on rag.sqlite."
- No type: ignore or noqa suppressions needed

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Import succeeds | `python -c "from agent.services.rag_maintenance_service import RagMaintenanceService"` | No error |
| Layer contract | `uv run lint-imports` | 0 violations |
| Type check | `uv run mypy scripts/agent/services/rag_maintenance_service.py` | 0 errors |
| Lint | `uv run ruff check scripts/agent/services/rag_maintenance_service.py` | 0 errors |
| Unit tests | `uv run pytest tests/test_db_maintenance.py -x` | all pass |
| No rag.sqlite ref in DbMaintenanceService after split | `grep -n "rag" scripts/agent/services/db_maintenance_service.py` | 0 matches |
