## Goal

Update import paths in `scripts/eventbus/publish_route.py` per REQ-006. Caller of `insert_event`.

## Scope

Update import statements to point to new module locations after `db.py` split.

## Assumptions

- New modules exist under `scripts/eventbus/`: `event_repo.py`.

## Design decisions

- Import from new layer modules directly where possible.
- Keep backward-compatible imports via `eventbus.db` re-export stub for symbols that will be re-exported there.

## Alternatives considered

- Updating all imports to point to new layer modules rejected because it would break backward compatibility during transition period.
- Keeping all imports via `eventbus.db` accepted because re-export stub preserves backward compatibility.

## Implementation

### Target file

`scripts/eventbus/publish_route.py`

### Procedure

Update import paths in `publish_route.py` to point to new module locations.

### Method

1. Read current import statement: `from eventbus.db import insert_event` (line 13).
2. Replace with imports from new layer modules:
   - `from eventbus.event_repo import insert_event`
3. Update any other imports as needed.

### Details

```python
# Before (line 13):
# from eventbus.db import insert_event

# After:
from eventbus.event_repo import insert_event
```

## Compatibility considerations

- Function signatures unchanged.
- Return types unchanged.
- Backward compatibility maintained via re-export stub (if using `eventbus.db`).

## Security considerations

- No security impact — only import path changes.

## Rollback considerations

- If import changes cause regressions, revert to original imports.
- Keep original `publish_route.py` until full test suite passes.

## Validation plan

- Run full eventbus test suite: `uv run pytest tests/eventbus/` — 311 collected tests.
- Verify `publish_route.py` still imports correctly.
- Verify no behavioral regression.

## Completion criteria

- Import paths updated in `scripts/eventbus/publish_route.py`.
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
| 1 | Update import paths in publish_route.py | Pending | — | — | |
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
- **Related target files**: scripts/eventbus/publish_route.py
