# Refactor scripts/eventbus/db.py into layered responsibility modules

## Priority
Medium

## Summary
Split the monolithic `scripts/eventbus/db.py` (678 lines, 14 responsibilities) into separate modules by concern: schema/migration, event CRUD, consumer delivery state, DLQ operations, and offset management. Replace column-name f-string interpolation with a consistent pattern (constants are safe since no user input is involved, but the pattern should be uniform across layers).

**Verification status**: Adversarial verification confirmed core claims (line count, `# nosec B608` patterns, magic tuples). Discrepancies found: 32 test files (not 29), 11 column constants (not "10+"), 311 collected tests (not 29). See [Verification Results](#verification-results) below.

## Background
`scripts/eventbus/db.py` was written incrementally without explicit architectural boundaries. Each new feature (per-consumer delivery tracking, DLQ promotion, legacy offset migration) was added directly into the same module. The module currently handles:
- SQLite connection lifecycle (`open_db`, `check_db`, `get_db_lock`)
- Schema initialization and additive migration (`_init_schema`, `_migrate`)
- Event CRUD operations (`insert_event`, `get_seq`, `fetch_events_since`, `fetch_dlq`, `count_dlq`)
- Ack/nack semantics (`ack_event`, `nack_event`, `ack_event_for_consumer`)
- DLQ operations (`requeue_event`, `redeliver_event`)
- Legacy offset migration (`migrate_legacy_offsets`)
- Module-level constants for column names (11 `_COL_*` identifiers)

This violates the single-responsibility principle and makes it difficult to reason about which callers depend on which functions.

## Verification Results
Adversarial verification against current source code (20260919):

### Confirmed claims
| Claim | Issue text | Verified | Evidence |
|---|---|---|---|
| Line count | "678 lines" | ✅ Exact match | `wc -l` → 678 |
| `# nosec B608` patterns | "Multiple functions use `f"...{col}..."` patterns" | ✅ 9 instances | Lines 49, 211, 220, 269, 276, 474, 525, 563, 571 |
| Magic tuples | "`nack_event()` returns `(-1, -1)` or `(-2, -2)`" | ✅ Confirmed | Lines 273, 274, 284 |
| File I/O in migration | "`migrate_legacy_offsets()` performs file I/O" | ✅ Confirmed | Path.iterdir(), read_text() calls (lines 578–677) |
| Entangled migration logic | "_migrate() contains DDL statements for three different tables" | ✅ Confirmed | consumer_delivery + consumer_offsets DDL + events ALTER TABLE (lines 102–181) |
| Column constants | "10+ `_COL_*` identifiers" | ✅ 11 constants | _COL_DELIVERY_FAILURE_COUNT through _COL_CONSUMER_DELIVERY_FAILURE_COUNT |
| Test file count | "29 existing test files" | ❌ Incorrect | 32 test files in `tests/eventbus/`; 311 collected tests |

### Discrepancies
1. **Test file count off by 3**: Issue states "29 existing test files"; actual count is 32. This affects scope estimation for regression testing.
2. **Caller inventory incomplete**: Issue lists only `app.py` and `dlq.py` as script consumers. Actual callers include:
   - `ack_route.py` (2 imports)
   - `health_route.py` (1 import)
   - `publish_route.py` (1 import)
   - `replay_route.py` (1 import)
   - `route_helpers.py` (1 import)
   - `subscribe_route.py` (1 import)
   - Multiple test files (20+ imports)
3. **No python-code-review findings**: No prior architecture review findings exist for eventbus (only one other eventbus-related issue exists, concerning auth, not architecture).

### Design tensions identified
- **Constraint conflict**: "Backward-compatible import paths" requires keeping `from eventbus.db import ...` working via re-export stubs, while "db.py no longer exists as a monolithic file" requires removing its contents. Both can coexist only if `db.py` becomes a thin re-export module.
- **nack_event() breaking change**: Replacing magic tuples with a typed result object will break existing tuple-unpacking callers. The issue acknowledges this but does not resolve the tension.

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
- `scripts/eventbus/ack_route.py` (consumer — imports `nack_event`, `ack_event_for_consumer`)
- `scripts/eventbus/health_route.py` (consumer — imports `check_db`)
- `scripts/eventbus/publish_route.py` (consumer — imports `insert_event`)
- `scripts/eventbus/replay_route.py` (consumer — imports `fetch_events_since`)
- `scripts/eventbus/route_helpers.py` (consumer — imports `get_db_lock`)
- `scripts/eventbus/subscribe_route.py` (consumer — imports `get_consumer_offset`)
- `tests/eventbus/test_eventbus_db_migration.py` (test — validates DB migration behavior)
- `tests/eventbus/conftest.py` (test fixture — may create DB connections)
- All 32 files under `tests/eventbus/` (import path updates required)

## Required Changes
- Split `db.py` into 6 modules as described in Implementation Intent
- Replace all `f"...{col}..."` SQL interpolation with a consistent pattern (column names are safe since no user input is involved, but the pattern should be uniform across layers — e.g., define column name constants within each layer's scope)
- Replace tuple return values `(-1, -1)` and `(-2, -2)` in `nack_event()` with a `dataclass` or `Enum`-based result type
- Move column name constants (`_COL_DELIVERY_FAILURE_COUNT`, etc.) into the layer that owns them (e.g., delivery failures → `delivery_repo.py`; DLQ timestamps → `dlq_repo.py`)
- Extract `migrate_legacy_offsets()` into `offset_migrator.py` with its own file I/O dependencies isolated
- Update all import paths in `app.py`, `dlq.py`, and test fixtures
- Preserve the existing `_db_lock` singleton and `get_db_lock()` contract exactly

## Constraints
- **Backward-compatible import paths**: `from eventbus.db import open_db, check_db, get_db_lock` must continue to work. Resolution: keep `db.py` as a thin re-export stub that delegates to the new modules. This satisfies both "monolithic file removed" and "backward-compatible imports" simultaneously.
- **No behavioral change**: All existing function signatures, return types (except nack error codes), and side effects must remain identical. Caveat: `nack_event()` return type change is intentional and documented below.
- **Thread-safety preserved**: The existing `_db_lock` serialization model must not change
- **SQLite WAL mode**: Must remain the default journal mode
- **No new dependencies**: Cannot add ORM libraries; must stay within `sqlite3` stdlib + `orjson`
- **nack_event() backward compatibility**: Replacing `(-1, -1)` / `(-2, -2)` magic tuples with a typed result object WILL break existing tuple-unpacking callers. This is an acknowledged breaking change that must be communicated before implementation. See [Resolution: nack_event() return type](#resolution-nack-event-return-type) below.

## Acceptance Criteria
- [ ] `scripts/eventbus/db.py` no longer exists as a monolithic file (replaced by 6-layer split + thin re-export stub)
- [ ] All existing callers across 6 script files (`app.py`, `dlq.py`, `ack_route.py`, `health_route.py`, `publish_route.py`, `replay_route.py`, `route_helpers.py`, `subscribe_route.py`) pass without modification after import path updates
- [ ] All 32 test files under `tests/eventbus/` pass without modification after import path updates
- [ ] `nack_event()` returns a typed result object instead of `(-1, -1)` / `(-2, -2)` magic tuples (breaking change — callers updated accordingly)
- [ ] Column name constants are scoped to their owning layer where possible (shared columns like `_COL_EVENT_ID` may remain in a common location)
- [ ] `migrate_legacy_offsets()` operates in isolation from other DB concerns
- [ ] All existing tests pass (`uv run pytest tests/eventbus/`) — 311 collected tests

## Testing Expectations
- Run full eventbus test suite: `uv run pytest tests/eventbus/`
- Verify all 32 existing test files (311 collected tests) pass without modification
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
- No prior `python-code-review` findings on eventbus architecture (verified: no such findings exist)
- Existing test coverage baseline: 32 test files / 311 collected tests in `tests/eventbus/` provide characterization tests for behavior preservation

## Unresolved Questions
- For the typed `nack_event()` return value: should it be a `dataclass` or an `Enum`-based result type? `dataclass` is more Pythonic but adds runtime overhead; `TypedDict` is lighter but less discoverable. An `Exception`-based approach (e.g., `NackEventNotFound`, `NackInvalidState`) would provide better semantics but breaks backward compatibility with tuple unpacking.

**Resolution: Use `dataclass` with `Literal` fields.** Rationale:
  - `NackResult(dataclass)` preserves type safety while remaining compatible with attribute access patterns.
  - `int | Literal[-1]` / `int | Literal[-2]` fields make error states explicit at the type level.
  - Exception-based approach rejected because it breaks backward compatibility with existing callers that use tuple unpacking (e.g., `failure_count, cycle_count = nack_event(...)`).
  - `Enum` rejected because error states are not mutually exclusive — a single call can produce different failure counts independently.

- Does `migrate_legacy_offsets()` need its own dedicated error type for the collision exception, or is raising `ValueError` sufficient?

**Resolution: Keep `ValueError`.** Rationale:
  - Collision is a data-integrity issue, not a transient failure — `ValueError` is semantically appropriate.
  - Adding a custom exception class would increase surface area without adding semantic clarity.
  - Callers already handle this via `try/except ValueError` in current code.

## AI Implementation Instruction
1. Do NOT rewrite unrelated files (config.py, auth.py, broker.py). Only modify db.py and related modules.
2. Preserve all existing function signatures exactly — do not change parameter names, order, or defaults.
3. Use `?` parameterized queries for ALL values (never f-string interpolation for values). Column names may remain as constants within each layer.
4. Create a `NackResult` dataclass with fields `delivery_failure_count: int | Literal[-1]` and `cycle_failure_count: int | Literal[-2]` for nack_event(). This is a breaking change — update all callers that destructure the tuple.
5. After splitting, verify by running `uv run pytest tests/eventbus/` before considering the task complete.
6. If you encounter a function whose caller cannot be determined, leave a TODO comment rather than removing it.
7. Keep `db.py` as a thin re-export stub module that delegates to the 6 new layers (satisfies both "monolithic file removed" and "backward-compatible imports" constraints simultaneously).
8. Update import paths in all 8 script files and all 32 test files:
   - Script files: `app.py`, `dlq.py`, `ack_route.py`, `health_route.py`, `publish_route.py`, `replay_route.py`, `route_helpers.py`, `subscribe_route.py`
   - Test files: all files under `tests/eventbus/`

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-160141
- **Related target files**: scripts/eventbus/db.py, scripts/eventbus/app.py, scripts/eventbus/dlq.py, tests/eventbus/
- **Task classification**: Path B (large task) — affects > 3 files, creates new modules, changes public interface (nack_event return type)
