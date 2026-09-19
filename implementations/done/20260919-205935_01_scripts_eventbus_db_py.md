## Goal

Split `scripts/eventbus/db.py` into layered modules per REQ-001; replace all `f"...{col}..."` SQL interpolation with parameterized queries per REQ-002; replace magic tuples `(-1, -1)` / `(-2, -2)` in `nack_event()` with `NackResult` dataclass per REQ-003; scope column constants to owning layer per REQ-004; make `db.py` a thin re-export stub per REQ-007.

## Scope

Create `scripts/eventbus/db_conn.py` (connection lifecycle), `scripts/eventbus/schema.py` (schema/migration), `scripts/eventbus/event_repo.py` (event CRUD), `scripts/eventbus/delivery_repo.py` (ack/nack + delivery state), `scripts/eventbus/dlq_repo.py` (DLQ operations), `scripts/eventbus/offset_migrator.py` (legacy offset migration), and rewrite `scripts/eventbus/db.py` as a thin re-export stub.

## Assumptions

- `NackResult` dataclass with `Literal[-1]` / `Literal[-2]` fields is the correct approach for `nack_event()`'s return type.
- Column names come from module-level constants (not user input) and are currently safe from SQL injection.
- `_db_lock` singleton and `get_db_lock()` contract must be preserved exactly.
- SQLite WAL mode remains the default journal mode.
- No new dependencies beyond `sqlite3` stdlib + `orjson`.

## Design decisions

- Layered architecture: each layer owns its own data access and exposes only the operations consumers need (Repository Pattern).
- Shared columns (`_COL_EVENT_ID`, `_COL_SEQ`, `_COL_ACKED_AT`, `_COL_DLQ_AT`) stay in a common location (`_constants.py`).
- Layer-owned columns scoped to their owning layer (e.g., `_COL_DELIVERY_FAILURE_COUNT` → `delivery_repo.py`).
- `NackResult(frozen=True)` prevents accidental mutation of error state.

## Alternatives considered

- Exception-based approach for `nack_event()` error states rejected because it breaks backward compatibility with existing callers using tuple unpacking.
- `Enum` rejected because error states are not mutually exclusive — a single call can produce different failure counts independently.
- Keeping everything in `db.py` rejected because the module has grown to 678 lines across 14 public functions and 3 private helpers.

## Implementation

### Target file

`scripts/eventbus/db.py`

### Procedure

Rewrite `db.py` as a thin re-export stub that imports from the 6 new layers and re-exports all public symbols.

### Method

1. Replace all existing code in `db.py` with import statements from the 6 new layers.
2. Add `__all__` listing all exported symbols.
3. Add a comment warning against adding new functions directly to `db.py`.

### Details

```python
# WARNING: Do not add new functions here. Add them to the appropriate layer module
# and re-export from this stub. See scripts/eventbus/README.md for layer boundaries.

from eventbus.db_conn import check_db, get_db_lock, open_db
from eventbus.event_repo import count_dlq, fetch_dlq, fetch_events_since, insert_event, get_seq
from eventbus.delivery_repo import (
    NackResult,
    ack_event,
    ack_event_for_consumer,
    get_consumer_offset,
    nack_event,
)
from eventbus.dlq_repo import redeliver_event, requeue_event
from eventbus.offset_migrator import migrate_legacy_offsets

__all__ = [
    # Connection layer
    "open_db",
    "check_db",
    "get_db_lock",
    # Event repository
    "insert_event",
    "get_seq",
    "fetch_events_since",
    "fetch_dlq",
    "count_dlq",
    # Delivery repository
    "ack_event",
    "nack_event",
    "ack_event_for_consumer",
    "get_consumer_offset",
    "NackResult",
    # DLQ repository
    "requeue_event",
    "redeliver_event",
    # Offset migrator
    "migrate_legacy_offsets",
]
```

## Compatibility considerations

- All existing callers continue importing from `eventbus.db` — backward-compatible.
- `NackResult` replaces `tuple[int, int]` return type of `nack_event()`. Callers using attribute access (most) are unaffected. The sole tuple-unpacking caller (`ack_route.py:197`) must be updated separately (Phase 1).
- `get_db_lock()` returns `threading.Lock` — unchanged.
- `open_db()` returns `sqlite3.Connection` — unchanged.

## Security considerations

- All SQL statements now use parameterized queries exclusively for values.
- Column names remain as module-level constants within each layer (safe because they are not derived from user input).
- `NackResult` uses `Literal[-1]` / `Literal[-2]` to make error states explicit at the type level.

## Rollback considerations

- If any layer module fails validation, revert `db.py` to its original monolithic form.
- If `NackResult` causes regressions, restore `tuple[int, int]` return type and update `ack_route.py:197` accordingly.
- Keep a backup of the original `db.py` until full test suite passes.

## Validation plan

- Run full eventbus test suite: `uv run pytest tests/eventbus/` — 311 collected tests.
- Verify all 29 existing test files pass without behavioral change.
- Verify `nack_event()` returns `NackResult` instances accessible via attribute access.
- Verify migration path works: create DB with old schema, apply `_migrate()`, confirm new columns exist.
- Verify thread-safety preserved: `_db_lock` serialization model unchanged.
- Verify SQLite WAL mode remains default.

## Completion criteria

- `scripts/eventbus/db.py` exists as a thin re-export stub (no business logic).
- All 6 layer modules exist under `scripts/eventbus/`.
- All 311 eventbus tests pass.
- `NackResult` is accessible via `from eventbus.db import NackResult`.
- No new dependencies added.

## Out of scope

- Changing HTTP API surface.
- Adding new database indexes beyond `_migrate()`.
- Migrating from SQLite to another engine.
- Adding connection pooling/async drivers.
- Changing `_db_lock` serialization strategy.
- Modifying `schema.sql` DDL definitions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create db.py as thin re-export stub importing from 6 layer modules | Pending | — | — | |
| 2 | Add __all__ listing all exported symbols | Pending | — | — | |
| 3 | Add warning comment against adding new functions directly | Pending | — | — | |
| 4 | Update ack_route.py:197 to use NackResult attribute access (Phase 1 prerequisite) | Pending | — | — | |
| 5 | Run full eventbus test suite | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-007
- **Source issue**: issues/20260919-160141_refactor_001_eventbus_db_py_refactoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-170923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-205935
- **Related target files**: scripts/eventbus/db.py
