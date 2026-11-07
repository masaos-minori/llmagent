# EventBus Module

Layered SQLite-based event bus for managing event persistence, delivery, and dead-letter queue operations.

## Architecture

The module follows a layered architecture:

1. **Connection layer** (`db_conn.py`): SQLite connection lifecycle, locking, pragma application
2. **Schema layer** (`schema.py`): Schema definition and creation
3. **Event repository** (`event_repo.py`): All event read/write operations
4. **Delivery repository** (`delivery_repo.py`): Ack/nack semantics and per-consumer delivery state
5. **DLQ repository** (`dlq_repo.py`): Dead-letter queue operations

## Module Import Pattern

Each layer module is the public import surface for its own operations: connection
operations from `db_conn.py`, event operations from `event_repo.py`, delivery
operations from `delivery_repo.py`, and DLQ operations from `dlq_repo.py`.

**Rule**: Import each operation from its owning layer module. Do not add re-export
stubs.

**Decision (2026-11-07)**: The `db.py` stub facade and its "Retain this facade"
decision (2026-10-27) are reversed: all consumers, including
`scripts/agent/services/*`, import the layer modules directly.
