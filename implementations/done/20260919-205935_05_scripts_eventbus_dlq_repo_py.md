## Goal

Create `scripts/eventbus/dlq_repo.py` — DLQ operations per REQ-001. Extracts `requeue_event()`, `redeliver_event()` from `db.py`.

## Scope

New file containing dead-letter queue operations. Uses parameterized queries exclusively for values.

## Assumptions

- Shared column constants (`_COL_EVENT_ID`, `_COL_DLQ_AT`) imported from `_constants.py`.
- Layer-owned columns (`_COL_DLQ_REQUEUE_COUNT`, `_COL_REDISTRIBUTED_FROM`) scoped to this layer.
- `sqlite3.Connection` passed as first argument to all functions.

## Design decisions

- DLQ repository owns all DLQ operations.
- Column names remain as module-level constants within each layer.
- Parameterized queries used for all values.

## Alternatives considered

- Keeping everything in `db.py` rejected because DLQ operations are a distinct concern from normal event flow.

## Implementation

### Target file

`scripts/eventbus/dlq_repo.py`

### Procedure

Extract DLQ operations from `db.py` into this module.

### Method

1. Import shared column constants from `_constants.py`.
2. Import layer-owned column constants (defined locally).
3. Implement `requeue_event(conn, event_id)` — requeue an event from DLQ.
4. Implement `redeliver_event(conn, event_id)` — redeliver an event from DLQ.
5. Export public symbols.

### Details

```python
"""DLQ repository: dead-letter queue operations."""

from sqlite3 import Connection

# Shared column constants
from eventbus._constants import _COL_DLQ_AT, _COL_EVENT_ID

# Layer-owned column constants
_COL_DLQ_REQUEUE_COUNT = "dlq_requeue_count"
_COL_REDISTRIBUTED_FROM = "redelivered_from"

def requeue_event(conn: Connection, event_id: str) -> bool:
    """Requeue an event from the DLQ back to the events table."""
    cur = conn.execute(
        f"UPDATE events SET {_COL_DLQ_AT} = NULL, {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1 WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL",  # nosec B608
        (event_id,),
    )
    conn.commit()
    return cur.rowcount > 0

def redeliver_event(conn: Connection, event_id: str) -> bool:
    """Redeliver an event from the DLQ (mark as redelivered)."""
    cur = conn.execute(
        f"UPDATE events SET {_COL_REDISTRIBUTED_FROM} = 'dlq', {_COL_DLQ_AT} = NULL WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL",  # nosec B608
        (event_id,),
    )
    conn.commit()
    return cur.rowcount > 0
```

## Compatibility considerations

- All function signatures match existing `db.py` exports.
- Return types unchanged: `bool`.

## Security considerations

- All SQL statements use parameterized queries for values.
- Column names come from module-level constants (not user input) — safe from SQL injection.

## Rollback considerations

- If any function fails validation, revert to original `db.py` implementation.
- Keep original `db.py` until full test suite passes.

## Validation plan

- Run full eventbus test suite: `uv run pytest tests/eventbus/` — 311 collected tests.
- Verify `requeue_event()` requeues correctly.
- Verify `redeliver_event()` redelivers correctly.

## Completion criteria

- Both functions exist under `scripts/eventbus/dlq_repo.py`.
- All 311 eventbus tests pass.
- No behavioral regression in DLQ operations.

## Out of scope

- Changing HTTP API surface.
- Adding new database indexes beyond `_migrate()`.
- Migrating from SQLite to another engine.
- Adding connection pooling/async drivers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create dlq_repo.py with shared constant imports | Pending | — | — | |
| 2 | Implement requeue_event() | Pending | — | — | |
| 3 | Implement redeliver_event() | Pending | — | — | |
| 4 | Run full eventbus test suite | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260919-160141_refactor_001_eventbus_db_py_refactoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-170923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-205935
- **Related target files**: scripts/eventbus/dlq_repo.py
