## Goal

Update import paths in `scripts/eventbus/app.py` per REQ-006. Caller of `open_db`, `migrate_legacy_offsets`, `get_db_lock`.

## Scope

Update import statements to point to new module locations after `db.py` split.

## Assumptions

- New modules exist under `scripts/eventbus/`: `db_conn.py`, `delivery_repo.py`, `offset_migrator.py`.
- `NackResult` dataclass available via `from eventbus.db import NackResult` (via re-export stub).
- `ack_route.py:197` tuple-unpacking updated separately (Phase 1 prerequisite).

## Design decisions

- Import from new layer modules directly where possible.
- Keep backward-compatible imports via `eventbus.db` re-export stub for symbols that will be re-exported there.
- Update `NackResult` import if needed.

## Alternatives considered

- Updating all imports to point to new layer modules rejected because it would break backward compatibility during transition period.
- Keeping all imports via `eventbus.db` accepted because re-export stub preserves backward compatibility.

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

Update import paths in `app.py` to point to new module locations.

### Method

1. Read current import statement: `from eventbus.db import get_db_lock, migrate_legacy_offsets, open_db` (line 34).
2. Replace with imports from new layer modules:
   - `from eventbus.db_conn import open_db, get_db_lock`
   - `from eventbus.offset_migrator import migrate_legacy_offsets`
3. Update any other imports as needed.

### Details

```python
# Before (line 34):
# from eventbus.db import get_db_lock, migrate_legacy_offsets, open_db

# After:
from eventbus.db_conn import get_db_lock, open_db
from eventbus.offset_migrator import migrate_legacy_offsets
```

## Compatibility considerations

- Function signatures unchanged.
- Return types unchanged.
- Backward compatibility maintained via re-export stub (if using `eventbus.db`).

## Security considerations

- No security impact — only import path changes.

## Rollback considerations

- If import changes cause regressions, revert to original imports.
- Keep original `app.py` until full test suite passes.

## Validation plan

- Run full eventbus test suite: `uv run pytest tests/eventbus/` — 311 collected tests.
- Verify `app.py` still imports correctly.
- Verify no behavioral regression.

## Completion criteria

- Import paths updated in `scripts/eventbus/app.py`.
- All 311 eventbus tests pass.
- No behavioral regression.

## Out of scope

- Changing HTTP API surface.
- Adding new database indexes beyond `_migrate()`.
- Migrating from SQLite to another engine.
- Adding connection pooling/async drivers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update import paths in app.py | Pending | — | — | |
| 2 | Run full eventbus test suite | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260919-160141_refactor_001_eventbus_db_py_refactoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-170923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-205935
- **Related target files**: scripts/eventbus/app.py
