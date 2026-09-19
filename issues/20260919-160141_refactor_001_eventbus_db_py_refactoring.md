# Refactor scripts/eventbus/db.py into layered responsibility modules

## Priority
Medium

## Summary
Split the monolithic `scripts/eventbus/db.py` (678 lines, 14 responsibilities) into separate modules by concern: schema/migration, event CRUD, consumer delivery state, DLQ operations, and offset management. Replace column-name f-string interpolation with a consistent pattern (constants are safe since no user input is involved, but the pattern should be uniform across layers).

## Background
`scripts/eventbus/db.py` was written incrementally without explicit architectural boundaries. Each new feature (per-consumer delivery tracking, DLQ promotion, legacy offset migration) was added directly into the same module. The module currently handles:
- SQLite connection lifecycle (`open_db`, `check_db`, `get_db_lock`)
- Schema initialization and additive migration (`_init_schema`, `_migrate`)
- Event CRUD operations (`insert_event`, `get_seq`, `fetch_events_since`, `fetch_dlq`, `count_dlq`)
- Ack/nack semantics (`ack_event`, `nack_event`, `ack_event_for_consumer`)
- DLQ operations (`requeue_event`, `redeliver_event`)
- Legacy offset migration (`migrate_legacy_offsets`)
- Module-level constants for column names (10+ `_COL_*` identifiers)

This violates the single-responsibility principle and makes it difficult to reason about which callers depend on which functions.

## Problem
1. **Fragile SQL pattern**: Multiple functions use `f"...{col}..."` patterns with `# nosec B608` comments. While column names come from module-level constants (not user input) and is currently safe, this pattern is fragile — any future developer adding a user-derived value would introduce a real SQL injection vulnerability.
2. **No clear ownership boundary**: A reader cannot determine which functions belong together without reading every docstring. For example, `ack_event_for_consumer` and `get_consumer_offset` both deal with per-consumer delivery state, but they are interleaved with unrelated event operations.
3. **Migration logic entangled with business logic**: `_migrate()` contains DDL statements for three different tables (`consumer_delivery`, `consumer_offsets`, plus index creation) alongside column ALTER statements. This makes schema evolution hard to audit.
4. **`migrate_legacy_offsets()` performs file I/O**: It reads `.map` and `.offset` files from disk, which is a completely different concern from database operations.
5. **Magic return-value conventions**: `nack_event()` returns `(-1, -1)` or `(-2, -2)` for error states — tuples with no type safety, requiring callers to remember magic values.

## Reason for Change
The module has grown to 678 lines across 14 public functions and 3 private helpers. Adding new features requires understanding all of these responsibilities simultaneously. The f-string column-name pattern, while currently safe, should be made uniform across layers to prevent future bugs as the team grows. A clean separation of concerns now prevents future technical debt accumulation.

## Implementation Intent
Apply a **layered architecture** approach: each layer owns its own data access and exposes only the operations consumers need. The layers are:

1. **Connection layer** (`db_conn.py`): Connection lifecycle, locking, pragma application. Only exports `open_db()`, `check_db()`, `get_db_lock()`.
2. **Schema layer** (`schema.py`): Schema definition, migration logic. Exports `_SCHEMA_PATH`, `_apply_pragmas()`, `_init_schema()`, `_migrate()`.
3. **Event repository** (`event_repo.py`): All event read/write operations. Exports `insert_event()`, `get_seq()`, `fetch_events_since()`, `fetch_dlq()`, `count_dlq()`.
4. **Delivery repository** (`delivery_repo.py`): Ack/nack semantics and per-consumer delivery state. Exports `ack_event()`, `nack_event()`, `ack_event_for_consumer()`, `get_consumer_offset()`.
5. **DLQ repository** (`dlq_repo.py`): Dead-letter queue operations. Exports `requeue_event()`, `redeliver_event()`.
6. **Offset migrator** (`offset_migrator.py`): Legacy offset migration. Exports `migrate_legacy_offsets()`.

Each layer uses parameterized queries exclusively for values. Column names may remain as module-level constants within each layer; columns shared across multiple layers (e.g., `_COL_EVENT_ID` used by all layers) may stay in a shared location. Return types should use `dataclasses` or `NamedTuple` instead of raw tuples for error states.

## Target Files or Areas
- `scripts/eventbus/db.py` (source — to be split)
- `scripts/eventbus/schema.sql` (referenced by schema layer)
- `scripts/eventbus/app.py` (consumer — imports from `db` module)
- `scripts/eventbus/dlq.py` (consumer — calls `db` functions)
- `tests/eventbus/test_eventbus_db_migration.py` (test — validates DB migration behavior)
- `tests/eventbus/conftest.py` (test fixture — may create DB connections)

## Required Changes
- Split `db.py` into 6 modules as described in Implementation Intent
- Replace all `f"...{col}..."` SQL interpolation with a consistent pattern (column names are safe since no user input is involved, but the pattern should be uniform across layers — e.g., define column name constants within each layer's scope)
- Replace tuple return values `(-1, -1)` and `(-2, -2)` in `nack_event()` with a `dataclass` or `Enum`-based result type
- Move column name constants (`_COL_DELIVERY_FAILURE_COUNT`, etc.) into the layer that owns them (e.g., delivery failures → `delivery_repo.py`; DLQ timestamps → `dlq_repo.py`)
- Extract `migrate_legacy_offsets()` into `offset_migrator.py` with its own file I/O dependencies isolated
- Update all import paths in `app.py`, `dlq.py`, and test fixtures
- Preserve the existing `_db_lock` singleton and `get_db_lock()` contract exactly

## Constraints
- **Backward-compatible import paths**: `from eventbus.db import open_db, check_db, get_db_lock` must continue to work (provide re-export stubs in `db.py` that delegate to the new modules, or update all callers)
- **No behavioral change**: All existing function signatures, return types (except nack error codes), and side effects must remain identical
- **Thread-safety preserved**: The existing `_db_lock` serialization model must not change
- **SQLite WAL mode**: Must remain the default journal mode
- **No new dependencies**: Cannot add ORM libraries; must stay within `sqlite3` stdlib + `orjson`

## Acceptance Criteria
- [ ] `scripts/eventbus/db.py` no longer exists as a monolithic file (replaced by the 6-layer split)
- [ ] All existing callers (`app.py`, `dlq.py`, tests) pass without modification after import path updates
- [ ] `nack_event()` returns a typed result object instead of `(-1, -1)` / `(-2, -2)` magic tuples
- [ ] Column name constants are scoped to their owning layer where possible (shared columns like `_COL_EVENT_ID` may remain in a common location)
- [ ] `migrate_legacy_offsets()` operates in isolation from other DB concerns
- [ ] All existing tests pass (`uv run pytest tests/eventbus/`)

## Testing Expectations
- Run full eventbus test suite: `uv run pytest tests/eventbus/`
- Verify all 29 existing test files pass without modification
- Add regression tests for the new typed `nack_event()` return values
- Verify migration path works: create a DB with old schema, apply `_migrate()`, confirm new columns exist
- Verify `migrate_legacy_offsets()` handles edge cases: missing `.map` files, empty `.map` files, collision detection

## Documentation Impact
Update module docstrings in each new layer to describe its responsibility. Document the new layer boundaries in `docs/eventbus/index.md` if it describes the internal architecture. No public API documentation changes required (external HTTP endpoints unchanged).

## Out of Scope
- Changing the HTTP API surface (no endpoint additions/removals)
- Adding new database indexes beyond what `_migrate()` already creates
- Migrating from SQLite to another database engine
- Adding connection pooling or async database drivers
- Changing the `_db_lock` serialization strategy
- Modifying `schema.sql` DDL definitions

## Dependencies
- `python-code-review` findings on eventbus architecture (if any exist)
- Existing test coverage baseline: `tests/eventbus/` provides characterization tests for behavior preservation

## Unresolved Questions
- For the typed `nack_event()` return value: should it be a `dataclass` or an `Enum`-based result type? `dataclass` is more Pythonic but adds runtime overhead; `TypedDict` is lighter but less discoverable. An `Exception`-based approach (e.g., `NackEventNotFound`, `NackInvalidState`) would provide better semantics but breaks backward compatibility with tuple unpacking.
- Does `migrate_legacy_offsets()` need its own dedicated error type for the collision exception, or is raising `ValueError` sufficient?

## AI Implementation Instruction
1. Do NOT rewrite unrelated files (app.py, dlq.py, config.py, auth.py, route files, broker.py). Only modify db.py and related modules.
2. Preserve all existing function signatures exactly — do not change parameter names, order, or defaults.
3. Use `?` parameterized queries for ALL values (never f-string interpolation for values). Column names may remain as constants within each layer.
4. Create a `NackResult` dataclass with fields `delivery_failure_count: int | Literal[-1]` and `cycle_failure_count: int | Literal[-2]` for nack_event(). Alternatively, consider `NackEventNotFound` / `NackInvalidState` exceptions for better semantics, but this breaks backward compatibility with tuple unpacking.
5. After splitting, verify by running `uv run pytest tests/eventbus/` before considering the task complete.
6. If you encounter a function whose caller cannot be determined, leave a TODO comment rather than removing it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-160141
- **Related target files**: scripts/eventbus/db.py, scripts/eventbus/app.py, scripts/eventbus/dlq.py, tests/eventbus/
