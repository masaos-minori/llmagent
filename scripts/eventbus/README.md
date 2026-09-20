# EventBus Module

Layered SQLite-based event bus for managing event persistence, delivery, and dead-letter queue operations.

## Architecture

The module follows a layered architecture:

1. **Connection layer** (`db_conn.py`): SQLite connection lifecycle, locking, pragma application
2. **Schema layer** (`schema.py`): Schema definition, migration logic
3. **Event repository** (`event_repo.py`): All event read/write operations
4. **Delivery repository** (`delivery_repo.py`): Ack/nack semantics and per-consumer delivery state
5. **DLQ repository** (`dlq_repo.py`): Dead-letter queue operations

## Stub Module Pattern

`db.py` is a stub module that re-exports functions from the layer modules above. It provides a single entry point for consumers of the eventbus module.

**Rule**: Do not add new functions here. Add them to the appropriate layer module and re-export from this stub.
