# Implementation: db_maintenance_service.py (update)

## Goal

Remove RAG-layer methods from `DbMaintenanceService` so it operates exclusively on
`session.sqlite`. After this change, `DbMaintenanceService` is the session-only service
and `RagMaintenanceService` handles all rag.sqlite operations.

## Scope

**In:**
- Remove `rebuild_fts()`, `consistency()`, `recover()` from `DbMaintenanceService`
- Update `stats()` to read only from `session.sqlite` (sessions, messages)
- Update class docstring to state "session.sqlite only"
- Remove unused imports from `db.maintenance` that were only needed by removed methods

**Out:**
- Changing `health()`, `checkpoint()`, `vacuum()`, `purge()` — they already target session.sqlite
- Modifying `DbStats` data model (deferred to a later cleanup step)
- Changing `repl.py` chunk count lookup (it calls `DbMaintenanceService().stats().chunks`;
  update it to call `RagMaintenanceService().stats_rag()` instead)

## Assumptions

- `RagMaintenanceService` is created first (see `20260620-142000_rag_maintenance_service.py.md`)
- `cmd_db.py` is updated in the same PR to import `RagMaintenanceService` for RAG subcommands
- `repl.py` line 103 uses `DbMaintenanceService().stats().chunks` — this must be updated to
  `RagMaintenanceService().stats_rag()[1]` (index 1 = chunks count) or equivalent
- `DbStats` keeps all four fields for now (docs/chunks may be set to 0 in the session-only path)
  to avoid breaking callers that expect `DbStats`; a follow-up can split the model

## Implementation

### Target file

`scripts/agent/services/db_maintenance_service.py`

### Procedure

1. Remove methods `rebuild_fts()`, `consistency()`, `recover()` from `DbMaintenanceService`
2. Update `stats()` to query only `sessions` and `messages` from `session.sqlite`;
   set `docs=0, chunks=0` in the returned `DbStats` (or adjust the return type)
3. Remove now-unused imports: `check_rag_consistency`, `is_consistent`,
   `recover_corruption`, `summarize_issues` from `db.maintenance`
4. Update class docstring: `"""Wraps maintenance operations on session.sqlite only."""`
5. Update `repl.py` line 103: replace `DbMaintenanceService().stats().chunks` with
   `RagMaintenanceService().stats_rag()[1]`; add the import for `RagMaintenanceService`

### Method

After the update, `DbMaintenanceService` retains only:

```python
class DbMaintenanceService:
    """Wraps maintenance operations on session.sqlite only."""

    def stats(self) -> DbStats:
        """Return session/message counts from session.sqlite."""
        ...  # reads sessions, messages; docs=0, chunks=0

    def health(self) -> DbHealth: ...
    def checkpoint(self, mode: str | None) -> DbCheckpointResult: ...
    def vacuum(self) -> None: ...
    def purge(self, max_sessions, max_age_days) -> DbPurgeResult: ...

    @staticmethod
    def _count_table(db, table: str) -> int: ...
```

### Details

- `stats()` body changes to open only `SQLiteHelper("session")` and return
  `DbStats(docs=0, chunks=0, sessions=sessions, messages=messages)`
- The `docs=0, chunks=0` stub avoids touching `DbStats` data model in this step
- `repl.py` import block: add
  `from agent.services.rag_maintenance_service import RagMaintenanceService`
  and replace the `.chunks` call

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No rag.sqlite access in class | `grep -n "SQLiteHelper.*rag\|rag.sqlite" scripts/agent/services/db_maintenance_service.py` | 0 matches |
| Removed methods absent | `grep -n "rebuild_fts\|consistency\|recover_corruption" scripts/agent/services/db_maintenance_service.py` | 0 matches |
| Layer contract | `uv run lint-imports` | 0 violations |
| Type check | `uv run mypy scripts/agent/services/db_maintenance_service.py scripts/agent/repl.py` | 0 errors |
| Lint | `uv run ruff check scripts/agent/services/db_maintenance_service.py` | 0 errors |
| DB maintenance tests | `uv run pytest tests/test_db_maintenance.py -x` | all pass |
| REPL smoke test (chunk count) | `uv run pytest tests/test_repl.py -x` | all pass |
