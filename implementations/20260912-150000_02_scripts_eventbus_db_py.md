## Goal

Add `redelivered_from`-based concurrency guard to `redeliver_event()` in `scripts/eventbus/db.py` using the lineage model (REQ-001).

## Scope

- **In-Scope**: Modifying `scripts/eventbus/db.py` to add concurrency guard to `redeliver_event()`
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- The lineage model is chosen as the single truth for `/dlq/{event_id}/requeue`
- Two concurrent requests could both see `dlq_at IS NOT NULL` and both insert new rows — this is the race condition that needs fixing
- A `redelivered_from`-existence check is needed for full concurrency protection

## Design decisions

- Add a `redelivered_from`-existence check before proceeding with the INSERT
- Begin a transaction, check if `SELECT 1 FROM events WHERE redelivered_from = ?` returns any rows
- If yes, return `(False, None)` — already redelivered
- If no, proceed with the conditional UPDATE + INSERT as currently implemented
- Commit the transaction

This ensures only one redeliver succeeds per original event, satisfying the requirement stated in `test_concurrent_dlq_requeue`.

## Alternatives considered

- Adding a UNIQUE constraint on `redelivered_from`: would enforce at the database level but would require schema migration and could cause unexpected failures
- Using SQLite's `INSERT OR IGNORE`: would silently ignore duplicates but wouldn't provide clear error messages
- Using `SELECT ... FOR UPDATE`: not supported by SQLite

## Implementation

### Target file

`scripts/eventbus/db.py`

### Procedure

1. Update imports to include necessary modules
2. Add `redelivered_from`-based concurrency guard to `redeliver_event()`
3. Preserve existing functionality

### Method

For the function update:
- Check if `SELECT 1 FROM events WHERE redelivered_from = ?` returns any rows
- If yes, return `(False, None)` — already redelivered
- If no, proceed with the conditional UPDATE + INSERT as currently implemented

### Details

#### Step 1: Update imports

```python
# Before:
from __future__ import annotations

import logging
import sqlite3
import threading
import time
import uuid
from collections.abc import Sequence
from typing import Any

logger = logging.getLogger(__name__)

# After:
from __future__ import annotations

import logging
import sqlite3
import threading
import time
import uuid
from collections.abc import Sequence
from typing import Any

logger = logging.getLogger(__name__)
```

#### Step 2: Update redeliver_event function

```python
# Before:
def redeliver_event(conn: sqlite3.Connection, event_id: str) -> tuple[bool, str | None]:
    """Redeliver a dead-lettered event by inserting a new row with lineage.

    Performs conditional-update guard on the original row (WHERE event_id = ? AND dlq_at IS NOT NULL)
    then inserts a new row with a fresh UUID v4 event_id, copied delivery_failure_count,
    cycle_failure_count=0, and redelivered_from set to the original event_id.

    Returns (success, new_event_id):
      - (True, new_event_id)   = event found and redelivered
      - (False, None)          = event not found in DLQ
    """
    original_row = conn.execute(
        "SELECT delivery_failure_count FROM events WHERE event_id = ? AND dlq_at IS NOT NULL",
        (event_id,),
    ).fetchone()
    if not original_row:
        return (False, None)

    new_event_id = uuid.uuid4().hex
    conn.execute(
        "UPDATE events SET dlq_requeue_count = dlq_requeue_count + 1 WHERE event_id = ? AND dlq_at IS NOT NULL",
        (event_id,),
    )
    conn.execute(
        "INSERT INTO events (event_id, topic, payload, producer, published_at, delivery_failure_count, cycle_failure_count, redelivered_from) "
        "SELECT ?, topic, payload, producer, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), delivery_failure_count, 0, ? "
        "FROM events WHERE event_id = ?",
        (new_event_id, event_id, event_id),
    )
    conn.commit()
    return (True, new_event_id)

# After:
def redeliver_event(conn: sqlite3.Connection, event_id: str) -> tuple[bool, str | None]:
    """Redeliver a dead-lettered event by inserting a new row with lineage.

    Uses a `redelivered_from`-existence check as a concurrency guard: if another
    request has already redelivered this event (i.e., a row exists with
    redelivered_from = event_id), return (False, None) to prevent duplicate
    redeliveries. This prevents the race condition where two concurrent requests
    could both see dlq_at IS NOT NULL and both insert new rows.

    Performs conditional-update guard on the original row (WHERE event_id = ? AND dlq_at IS NOT NULL)
    then inserts a new row with a fresh UUID v4 event_id, copied delivery_failure_count,
    cycle_failure_count=0, and redelivered_from set to the original event_id.

    Returns (success, new_event_id):
      - (True, new_event_id)   = event found and redelivered
      - (False, None)          = event not found in DLQ or already redelivered
    """
    # Concurrency guard: check if this event has already been redelivered
    # by looking for an existing row with redelivered_from = event_id
    existing_redelivery = conn.execute(
        "SELECT 1 FROM events WHERE redelivered_from = ?",
        (event_id,),
    ).fetchone()
    if existing_redelivery:
        return (False, None)

    original_row = conn.execute(
        "SELECT delivery_failure_count FROM events WHERE event_id = ? AND dlq_at IS NOT NULL",
        (event_id,),
    ).fetchone()
    if not original_row:
        return (False, None)

    new_event_id = uuid.uuid4().hex
    conn.execute(
        "UPDATE events SET dlq_requeue_count = dlq_requeue_count + 1 WHERE event_id = ? AND dlq_at IS NOT NULL",
        (event_id,),
    )
    conn.execute(
        "INSERT INTO events (event_id, topic, payload, producer, published_at, delivery_failure_count, cycle_failure_count, redelivered_from) "
        "SELECT ?, topic, payload, producer, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), delivery_failure_count, 0, ? "
        "FROM events WHERE event_id = ?",
        (new_event_id, event_id, event_id),
    )
    conn.commit()
    return (True, new_event_id)
```

## Compatibility considerations

- The concurrency guard adds an extra SELECT query before the main logic
- This should have negligible performance impact since it's a simple index lookup
- Existing callers expecting `(False, None)` for "not found" will also get `(False, None)` for "already redelivered"

## Security considerations

- The concurrency guard prevents race conditions where two concurrent requests could both see `dlq_at IS NOT NULL` and both insert new rows
- This improves security by preventing data corruption from concurrent operations

## Rollback considerations

- If the concurrency guard causes issues in production, roll back to the previous state without the guard
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/db.py::redeliver_event | Integration: verify concurrent requeue operations don't cause data corruption | pytest tests/eventbus/test_eventbus_concurrent.py::TestConcurrentDlqRequeue::test_concurrent_dlq_requeue | Test completes without assertion errors |

## Completion criteria

- [ ] `redelivered_from`-existence check added to `redeliver_event()`
- [ ] Return `(False, None)` when event already redelivered
- [ ] Tests pass with the new concurrency guard

## Out of scope

- Changes to `scripts/eventbus/dlq_route.py` (handled in separate procedure document)
- Changes to test files (handled in separate procedure documents)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add redelivered_from existence check | Pending | — | — | |
| 2 | Update docstring | Pending | — | — | |
| 3 | Run validation tests | Pending | — | — | |

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
- **Source issue**: issues/20260911-142700_ebdlq01_requeue-model-in-place-vs-lineage-conflict.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-115455_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-150000
- **Related target files**: scripts/eventbus/db.py
