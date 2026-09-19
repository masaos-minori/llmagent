## Goal

Update import paths in `scripts/eventbus/ack_route.py` per REQ-006. Caller of `nack_event`, `ack_event_for_consumer`; also destructures `nack_event()` return value as a tuple at line 197.

## Scope

Update import statements to point to new module locations after `db.py` split. Also update the sole tuple-unpacking caller of `nack_event()` to use `NackResult` attribute access (Phase 1 prerequisite, REQ-003).

## Assumptions

- New modules exist under `scripts/eventbus/`: `delivery_repo.py`.
- `NackResult` dataclass available via `from eventbus.db import NackResult` (via re-export stub).
- `ack_route.py:197` destructures `nack_event()`'s return value as a tuple: `failure_count, _cycle_count = _nack_event(db, event_id)`.

## Design decisions

- Import from new layer modules directly where possible.
- Keep backward-compatible imports via `eventbus.db` re-export stub for symbols that will be re-exported there.
- Update `NackResult` import if needed.
- Update tuple-unpacking at line 197 to use `NackResult` attribute access.

## Alternatives considered

- Updating all imports to point to new layer modules rejected because it would break backward compatibility during transition period.
- Keeping all imports via `eventbus.db` accepted because re-export stub preserves backward compatibility.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

Update import paths in `ack_route.py` to point to new module locations. Also update the tuple-unpacking call at line 197 to use `NackResult` attribute access.

### Method

1. Read current import statements:
   - Line 13: `from eventbus.db import nack_event as _nack_event`
   - Line 89: `from eventbus.db import ack_event_for_consumer`
2. Replace with imports from new layer modules:
   - `from eventbus.delivery_repo import nack_event as _nack_event, ack_event_for_consumer`
   - Add `from eventbus.delivery_repo import NackResult` if needed
3. Update line 197 tuple-unpacking:
   - Before: `failure_count, _cycle_count = _nack_event(db, event_id)`
   - After: `failure_count = _nack_event(db, event_id).delivery_failure_count; _cycle_count = _nack_event(db, event_id).cycle_failure_count`
4. Update any other imports as needed.

### Details

```python
# Before (line 13):
# from eventbus.db import nack_event as _nack_event

# After:
from eventbus.delivery_repo import nack_event as _nack_event

# Before (line 89):
# from eventbus.db import ack_event_for_consumer

# After:
from eventbus.delivery_repo import ack_event_for_consumer

# Before (line 197):
# failure_count, _cycle_count = _nack_event(db, event_id)

# After:
_nack_result = _nack_event(db, event_id)
failure_count = _nack_result.delivery_failure_count
_cycle_count = _nack_result.cycle_failure_count
```

## Compatibility considerations

- Function signatures unchanged.
- Return types changed: `tuple[int, int]` → `NackResult`.
- The sole tuple-unpacking caller must be updated to use attribute access.
- Backward compatibility maintained via re-export stub (if using `eventbus.db`).

## Security considerations

- No security impact — only import path changes and return type change.

## Rollback considerations

- If import changes cause regressions, revert to original imports.
- If `NackResult` causes regressions, restore `tuple[int, int]` return type.
- Keep original `ack_route.py` until full test suite passes.

## Validation plan

- Run full eventbus test suite: `uv run pytest tests/eventbus/` — 311 collected tests.
- Verify `ack_route.py` still imports correctly.
- Verify no behavioral regression.
- Verify `NackResult` attribute access works correctly.

## Completion criteria

- Import paths updated in `scripts/eventbus/ack_route.py`.
- Tuple-unpacking at line 197 updated to use `NackResult` attribute access.
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
| 1 | Update import paths in ack_route.py | Pending | — | — | |
| 2 | Update tuple-unpacking at line 197 to use NackResult attribute access | Pending | — | — | Phase 1 prerequisite |
| 3 | Run full eventbus test suite | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-006
- **Source issue**: issues/20260919-160141_refactor_001_eventbus_db_py_refactoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-170923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-205935
- **Related target files**: scripts/eventbus/ack_route.py
