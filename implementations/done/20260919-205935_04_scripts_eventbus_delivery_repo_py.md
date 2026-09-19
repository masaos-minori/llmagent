## Goal

Create `scripts/eventbus/delivery_repo.py` — Ack/nack semantics and per-consumer delivery state per REQ-001, REQ-003. Extracts `ack_event()`, `nack_event()`, `ack_event_for_consumer()`, `get_consumer_offset()` from `db.py`. Creates `NackResult` dataclass per REQ-003.

## Scope

New file containing ack/nack operations and per-consumer delivery state. Includes `NackResult` dataclass replacing magic tuples.

## Assumptions

- Shared column constants (`_COL_EVENT_ID`, `_COL_SEQ`, `_COL_ACKED_AT`, `_COL_DLQ_AT`) imported from `_constants.py`.
- Layer-owned columns (`_COL_DELIVERY_FAILURE_COUNT`, `_COL_CYCLE_FAILURE_COUNT`, `_COL_CONSUMER_DELIVERY_FAILURE_COUNT`, `_COL_CONSUMER_ID`, `_COL_OFFSET`) scoped to this layer.
- `NackResult(frozen=True)` prevents accidental mutation of error state.
- `Literal[-1]` / `Literal[-2]` make error states explicit at the type level.

## Design decisions

- Delivery repository owns ack/nack semantics and per-consumer delivery state.
- `NackResult` dataclass replaces `tuple[int, int]` return type of `nack_event()`.
- `frozen=True` prevents accidental mutation of error state.
- `Literal[-1]` / `Literal[-2]` make error states explicit at the type level.
- Exception-based approach rejected because it breaks backward compatibility with existing callers using tuple unpacking.
- `Enum` rejected because error states are not mutually exclusive.

## Alternatives considered

- Keeping everything in `db.py` rejected because delivery state is orthogonal to event storage.
- Using exception-based approach for `nack_event()` error states rejected because it breaks backward compatibility.

## Implementation

### Target file

`scripts/eventbus/delivery_repo.py`

### Procedure

Extract ack/nack operations and per-consumer delivery state from `db.py` into this module. Create `NackResult` dataclass.

### Method

1. Define `NackResult` dataclass with `Literal[-1]` / `Literal[-2]` fields.
2. Import shared column constants from `_constants.py`.
3. Import layer-owned column constants (defined locally).
4. Implement `ack_event(conn, event_id, now)` — acknowledge an event.
5. Implement `nack_event(conn, event_id, consumer_id=None)` — nack an event, returns `NackResult`.
6. Implement `ack_event_for_consumer(conn, consumer_id, event_id, now)` — acknowledge for a specific consumer.
7. Implement `get_consumer_offset(conn, consumer_id)` — get last-committed offset for a consumer.
8. Export public symbols including `NackResult`.

### Details

```python
"""Delivery repository: ack/nack semantics and per-consumer delivery state."""

from dataclasses import dataclass
from sqlite3 import Connection
from typing import Literal

# Shared column constants
from eventbus._constants import _COL_ACKED_AT, _COL_EVENT_ID, _COL_SEQ

# Layer-owned column constants
_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"
_COL_CYCLE_FAILURE_COUNT = "cycle_failure_count"
_COL_CONSUMER_DELIVERY_FAILURE_COUNT = "consumer_delivery_failure_count"
_COL_CONSUMER_ID = "consumer_id"
_COL_OFFSET = "offset"

@dataclass(frozen=True)
class NackResult:
    """Return value for nack_event().

    delivery_failure_count: int | Literal[-1] — -1 if event not found, otherwise current failure count.
    cycle_failure_count: int | Literal[-2] — -2 if event in invalid state, otherwise current cycle count.
    """
    delivery_failure_count: int | Literal[-1]
    cycle_failure_count: int | Literal[-2]

def ack_event(
    conn: Connection,
    event_id: str,
    now: str,
) -> tuple[bool, bool]:
    """Acknowledge an event. Returns (acked, success)."""
    cur = conn.execute(
        f"UPDATE events SET {_COL_ACKED_AT} = ? WHERE {_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL",  # nosec B608
        (now, event_id),
    )
    conn.commit()
    return (cur.rowcount > 0, True)

def nack_event(
    conn: Connection,
    event_id: str,
    consumer_id: str | None = None,
) -> NackResult:
    """Increment delivery_failure_count and cycle_failure_count for an event.

    Only increments if the event is in Normal/Delivered state (acked_at IS NULL
    AND dlq_at IS NULL). Events that are already ACKed or DLQ'd cannot have their
    failure counts incremented.

    If consumer_id is provided, also increment the consumer-specific failure count.

    Returns NackResult with:
      - delivery_failure_count: current count on success, -1 if event not found
      - cycle_failure_count: current count on success, -2 if event in invalid state
    """
    try:
        update_clause = (
            f"{_COL_DELIVERY_FAILURE_COUNT} = {_COL_DELIVERY_FAILURE_COUNT} + 1, "
            f"{_COL_CYCLE_FAILURE_COUNT} = {_COL_CYCLE_FAILURE_COUNT} + 1"
        )
        where_clause = (
            f"{_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL AND {_COL_DLQ_AT} IS NULL"
        )
        params: list[str] = [event_id]

        if consumer_id is not None:
            update_clause += f", {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} = {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} + 1"
            where_clause += f" AND {_COL_CONSUMER_ID} = ?"
            params.append(consumer_id)

        sql = f"UPDATE events SET {update_clause} WHERE {where_clause}"
        cur = conn.execute(sql, params)
        conn.commit()
        if cur.rowcount == 0:
            existing = conn.execute(
                f"SELECT {_COL_ACKED_AT}, {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608
                (event_id,),
            ).fetchone()
            if existing:
                return NackResult(-2, -2)
            return NackResult(-1, -1)
        row = conn.execute(
            f"SELECT {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608
            (event_id,),
        ).fetchone()
        if row:
            return NackResult(int(row[0]), int(row[1]))
        return NackResult(-1, -1)
    except Exception:
        conn.rollback()
        raise

def ack_event_for_consumer(
    conn: Connection,
    consumer_id: str,
    event_id: str,
    now: str,
) -> bool:
    """Acknowledge an event for a specific consumer."""
    cur = conn.execute(
        f"INSERT OR REPLACE INTO consumer_delivery(consumer_id, event_id, acked_at) VALUES (?, ?, ?)",  # nosec B608
        (consumer_id, event_id, now),
    )
    conn.commit()
    return cur.rowcount > 0

def get_consumer_offset(conn: Connection, consumer_id: str) -> int:
    """Get last-committed sequence offset for a consumer."""
    cur = conn.execute(
        f"SELECT {_COL_OFFSET} FROM consumer_offsets WHERE {_COL_CONSUMER_ID} = ?",  # nosec B608
        (consumer_id,),
    )
    row = cur.fetchone()
    if row is None:
        return 0
    return int(row[0])
```

## Compatibility considerations

- `NackResult` replaces `tuple[int, int]` return type of `nack_event()`. Callers using attribute access (most) are unaffected. The sole tuple-unpacking caller (`ack_route.py:197`) must be updated separately (Phase 1).
- All function signatures match existing `db.py` exports.
- `NackResult` is accessible via `from eventbus.db import NackResult` (via re-export stub).

## Security considerations

- All SQL statements use parameterized queries for values.
- Column names come from module-level constants (not user input) — safe from SQL injection.
- `NackResult` uses `Literal[-1]` / `Literal[-2]` to make error states explicit at the type level.

## Rollback considerations

- If `NackResult` causes regressions, restore `tuple[int, int]` return type and update `ack_route.py:197` accordingly.
- Keep original `db.py` until full test suite passes.

## Validation plan

- Run full eventbus test suite: `uv run pytest tests/eventbus/` — 311 collected tests.
- Verify `nack_event()` returns `NackResult` instances accessible via attribute access.
- Verify `ack_event()` acknowledges correctly.
- Verify `ack_event_for_consumer()` acknowledges for specific consumer.
- Verify `get_consumer_offset()` returns correct offset.

## Completion criteria

- All 4 functions exist under `scripts/eventbus/delivery_repo.py`.
- `NackResult` dataclass exists and is accessible via `from eventbus.db import NackResult`.
- All 311 eventbus tests pass.
- No behavioral regression in ack/nack operations.

## Out of scope

- Changing HTTP API surface.
- Adding new database indexes beyond `_migrate()`.
- Migrating from SQLite to another engine.
- Adding connection pooling/async drivers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create NackResult dataclass | Pending | — | — | |
| 2 | Create delivery_repo.py with shared constant imports | Pending | — | — | |
| 3 | Implement ack_event() | Pending | — | — | |
| 4 | Implement nack_event() returning NackResult | Pending | — | — | |
| 5 | Implement ack_event_for_consumer() | Pending | — | — | |
| 6 | Implement get_consumer_offset() | Pending | — | — | |
| 7 | Update ack_route.py:197 to use NackResult attribute access | Pending | — | — | Phase 1 prerequisite |
| 8 | Run full eventbus test suite | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260919-160141_refactor_001_eventbus_db_py_refactoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-170923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-205935
- **Related target files**: scripts/eventbus/delivery_repo.py
