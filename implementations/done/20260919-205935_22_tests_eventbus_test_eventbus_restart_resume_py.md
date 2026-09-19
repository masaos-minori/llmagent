## Goal

Update import paths in `tests/eventbus/test_eventbus_restart_resume.py` per REQ-006. Caller of `open_db`, `ack_event_for_consumer`, `get_consumer_offset`, `insert_event`.

## Scope

Update import statements to point to new module locations after `db.py` split.

## Assumptions

- New modules exist under `scripts/eventbus/`: `db_conn.py`, `delivery_repo.py`, `event_repo.py`.

## Design decisions

- Import from new layer modules directly where possible.
- Keep backward-compatible imports via `eventbus.db` re-export stub for symbols that will be re-exported there.

## Alternatives considered

- Updating all imports to point to new layer modules rejected because it would break backward compatibility during transition period.
- Keeping all imports via `eventbus.db` accepted because re-export stub preserves backward compatibility.

## Implementation

### Target file

`tests/eventbus/test_eventbus_restart_resume.py`

### Procedure

Update import paths in `test_eventbus_restart_resume.py` to point to new module locations.

### Method

1. Read current import statements:
   - `from eventbus.db import open_db`
   - `from eventbus.db import ack_event_for_consumer`
   - `from eventbus.db import get_consumer_offset`
   - `from eventbus.db import insert_event`
2. Replace with imports from new layer modules:
   - `from eventbus.db_conn import open_db`
   - `from eventbus.delivery_repo import ack_event_for_consumer, get_consumer_offset`
   - `from eventbus.event_repo import insert_event`
3. Update any other imports as needed.

### Details

```python
# Before:
# from eventbus.db import open_db
# from eventbus.db import ack_event_for_consumer
# from eventbus.db import get_consumer_offset
# from eventbus.db import insert_event

# After:
from eventbus.db_conn import open_db
from eventbus.delivery_repo import ack_event_for_consumer, get_consumer_offset
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
- Keep original test file until full test suite passes.

## Validation plan

- Run full eventbus test suite: `uv run pytest tests/eventbus/` — 311 collected tests.
- Verify test file still imports correctly.
- Verify no behavioral regression.

## Completion criteria

- Import paths updated in `tests/eventbus/test_eventbus_restart_resume.py`.
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
| 1 | Update import paths in test_eventbus_restart_resume.py | Pending | — | — | |
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
- **Related target files**: tests/eventbus/test_eventbus_restart_resume.py
