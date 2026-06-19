# Implementation: Remove Document Methods from DbMaintenanceService

## Goal

Remove `list_documents()` and `delete_document()` from `DbMaintenanceService`, along with unused `DocumentRow` DTO and any `DbStats` fields that become unnecessary. The agent layer should no longer directly access RAG-layer tables.

## Scope

- `scripts/agent/services/db_maintenance_service.py` — remove `list_documents()`, `delete_document()`
- `scripts/agent/services/models.py` — remove `DocumentRow`; assess `DbStats.docs` and `DbStats.chunks`

Out of scope:
- `db/maintenance.py` — low-level ops untouched
- `_db_stats`, `_db_clean`, `_db_list_urls` in `cmd_db.py` — covered in Step 4 doc

## Assumptions

1. `list_documents()` is only called by `cmd_db.py::_db_list_urls()` (confirmed from grep); after Step 4 rewires to MCP, this becomes a dead caller.
2. `delete_document()` is only called by `cmd_db.py::_db_clean()` (confirmed).
3. `DocumentRow` is only used by `list_documents()`; removing `list_documents()` makes it unused.
4. `DbStats.docs` and `DbStats.chunks` are used by `stats()` (line 36-44) and displayed by `_db_stats()`. Decision from plan: **keep** `DbStats.docs`/`DbStats.chunks` and `stats()` for backward compatibility with `/db stats` display, since stats is session+RAG combined. Reassess if Step 4 moves `/db stats` to MCP too.
5. Step 4 (`cmd_db.py` async rewire) must be done before or simultaneously with this step; otherwise `_db_clean` and `_db_list_urls` will call methods that no longer exist.

## Implementation

### Target file

`scripts/agent/services/db_maintenance_service.py`

### Procedure

1. Remove the `list_documents()` method (lines 108–135).
2. Remove the `delete_document()` method (lines 136–end of method).
3. In `models.py`, remove `DocumentRow` class.
4. In `db_maintenance_service.py`, remove the `DocumentRow` import.
5. Verify `DbStats.docs` / `DbStats.chunks` are still populated in `stats()` — keep them if `/db stats` still shows counts.

### Method

Direct deletion of method bodies and class definition. After removal, run lint and type check to catch any remaining references.

### Details

**db_maintenance_service.py — lines to remove:**
- `list_documents()` — entire method including docstring
- `delete_document()` — entire method including docstring
- Import of `DocumentRow` from models (if present)

**models.py — class to remove:**
- `DocumentRow` dataclass or TypedDict

**Verify no other callers before removing:**
```bash
grep -rn "list_documents\|delete_document\|DocumentRow" scripts/
```
Expected: only `cmd_db.py` references remain (which will be replaced in Step 4).

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-removal grep | `grep -rn "list_documents\|delete_document\|DocumentRow" scripts/` | Only cmd_db.py references (not service) |
| Lint | `ruff check scripts/agent/services/` | 0 errors |
| Type check | `mypy scripts/agent/services/` | 0 new errors |
| Unit tests | `uv run pytest tests/ -x -q` | all pass (after Step 4 also applied) |
