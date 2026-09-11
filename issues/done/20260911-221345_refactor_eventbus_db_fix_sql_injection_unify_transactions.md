# Refactor eventbus/db.py: eliminate SQL injection, unify transaction handling, and reduce query duplication

## Priority
High

## Summary
Fix critical SQL injection vulnerability in `fetch_events_since()`, unify transaction handling across all DB functions, and reduce duplicated two-step existence-check patterns in `ack_event()`, `nack_event()`, `requeue_event()`, and `redeliver_event()`.

## Background
`eventbus/db.py` provides the SQLite persistence layer for the Event Bus. It contains 12 public functions plus migration helpers. Several functions share a common anti-pattern: perform an UPDATE with a WHERE condition, then execute a separate SELECT to distinguish "not found" from "found but invalid state." This two-step approach is fragile under concurrent access and duplicates work that could be done atomically.

## Problem
Six concrete issues identified through line-by-line analysis:

1. **SQL injection in `fetch_events_since()`** (line 425) — `LIMIT {limit} OFFSET {offset}` concatenates unvalidated integers directly into SQL. While the code comments assert "all values bound via ? placeholders," the LIMIT/OFFSET clause bypasses parameterization entirely. An attacker controlling `limit` or `offset` can inject arbitrary SQL.

2. **No transaction wrapping in `ack_event()`** (lines 175–197) — Executes UPDATE, commits, then performs a second SELECT to check existence. If the row is deleted between commit and SELECT, the function returns `(True, False)` (already acked) instead of `(False, False)` (not found).

3. **Same transaction gap in `nack_event()`** (lines 200–232) — Identical pattern: UPDATE → commit → SELECT. Race condition produces incorrect return values under concurrency.

4. **Same transaction gap in `requeue_event()`** (lines 453–466) — SELECT to check DLQ status → UPDATE → commit. The initial SELECT is redundant; the UPDATE's WHERE clause already enforces the constraint.

5. **Redundant pre-check in `redeliver_event()`** (lines 469–499) — SELECT to find original row → UPDATE + INSERT. The UPDATE's WHERE clause (`dlq_at IS NOT NULL`) already prevents invalid transitions; the pre-check adds no safety.

6. **Inconsistent timestamp strategy** — `ack_event_for_consumer()` receives `now` as a parameter, while `redeliver_event()` calls `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` inline in SQL. Both produce slightly different timestamps for the same logical operation.

## Reason for Change
The SQL injection in `fetch_events_since()` is a production security risk — any caller controlling `limit` or `offset` parameters (e.g., HTTP API consumers) can inject SQL. The transaction gaps in `ack_event()` and `nack_event()` cause incorrect behavior under concurrent asyncio.to_thread() access, which is the documented access pattern. Reducing the two-step pattern eliminates unnecessary round-trips and race windows.

## Implementation Intent
Establish consistent patterns across all DB functions:

1. **Fix SQL injection**: Replace string interpolation in `fetch_events_since()` with parameterized queries. Use `?` placeholders for LIMIT/OFFSET by constructing the query dynamically with validated integer bounds.

2. **Unify transaction handling**: Wrap all functions that modify state (UPDATE/INSERT/DELETE) in explicit transactions using `conn.commit()` and `conn.rollback()`. For functions that currently do UPDATE → commit → SELECT, replace with UPDATE → SELECT in a single transaction.

3. **Eliminate two-step existence checks**: Replace the SELECT-after-UPDATE pattern with a single atomic query where possible. For `requeue_event()`, remove the pre-check SELECT — the UPDATE's WHERE clause is sufficient. For `redeliver_event()`, use the UPDATE's rowcount to determine success/failure instead of the pre-check SELECT.

4. **Unify timestamp strategy**: Always receive `now` as a parameter from callers. Remove inline `strftime()` calls from SQL.

5. **Extract shared constants**: Move hardcoded column names (`delivery_failure_count`, `dlq_at`, `acked_at`, etc.) to module-level constants or a schema constants module to avoid typos and enable schema evolution.

## Target Files or Areas
- `scripts/eventbus/db.py` (primary — fix injection, unify transactions, reduce duplication)
- `scripts/eventbus/schema.sql` (may need minor alignment if column names change)
- Callers of `fetch_events_since()` (verify limit/offset are always integers before passing)
- Callers of `ack_event()`, `nack_event()`, `requeue_event()`, `redeliver_event()` (verify return value semantics unchanged)

## Required Changes
- Fix `fetch_events_since()`: replace `f" LIMIT {limit} OFFSET {offset}"` with parameterized query — construct query conditionally based on whether limit/offset are provided, always using `?` placeholders
- Add explicit `try/finally` with `conn.rollback()` to `ack_event()` around the UPDATE+SELECT sequence
- Add explicit `try/finally` with `conn.rollback()` to `nack_event()` around the UPDATE+SELECT sequence
- Remove pre-check SELECT from `requeue_event()` — rely on UPDATE's WHERE clause and rowcount
- Replace pre-check SELECT in `redeliver_event()` with UPDATE rowcount check
- Unify timestamp handling: require `now` parameter in `redeliver_event()`, remove `strftime('now')` from SQL
- Extract column name constants: define `_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"` etc. at module level
- Update all SQL strings to use extracted constants instead of inline column names
- Ensure all return value conventions remain backward compatible

## Constraints
- Do not change the public API contract: all function signatures must remain identical
- Return value conventions must be preserved:
  - `ack_event()`: `(found, newly_acked)` tuple
  - `nack_event()`: `(delivery_failure_count, cycle_failure_count)` or `(-1,-1)/(-2,-2)` error codes
  - `ack_event_for_consumer()`: `(found, newly_acked, seq)` tuple
  - `insert_event()`: `(seq, inserted, status)` tuple
  - `requeue_event()`: `bool`
  - `redeliver_event()`: `(success, new_event_id)` tuple
- `get_db_lock()` must continue to return the same module-level lock
- `_apply_eventbus_pragmas()` must apply the same pragmas
- Schema migration logic in `_migrate()` must remain idempotent
- No behavioral changes to WAL mode, busy_timeout, or foreign_keys settings

## Acceptance Criteria
- [ ] `fetch_events_since()` uses parameterized queries for all values including LIMIT/OFFSET — no string interpolation in SQL
- [ ] `ack_event()` wraps UPDATE+SELECT in a single transaction with rollback on failure
- [ ] `nack_event()` wraps UPDATE+SELECT in a single transaction with rollback on failure
- [ ] `requeue_event()` no longer performs a pre-check SELECT before UPDATE
- [ ] `redeliver_event()` determines success from UPDATE rowcount rather than pre-check SELECT
- [ ] All functions use `now` parameter for timestamps — no inline `strftime('now')` in SQL
- [ ] Column names are defined as module-level constants and referenced consistently
- [ ] Existing tests pass without modification
- [ ] No regression in eventbus DLQ/requeue/redeliver behavior under concurrent access

## Testing Expectations
- Run existing unit tests for `eventbus/db.py` and ensure they pass
- Verify `fetch_events_since()` rejects non-integer limit/offset values (or validates them internally)
- Verify `requeue_event()` correctly handles events not in DLQ (returns False)
- Verify `redeliver_event()` correctly handles events not in DLQ (returns `(False, None)`)
- Concurrent test: simulate asyncio.to_thread() access to confirm no race conditions in ack/nack
- Type check the modified file
- Lint check the modified file

## Documentation Impact
Update the module docstring to document the unified transaction model and timestamp convention. Update function docstrings to clarify that all modifying functions operate within explicit transactions. Document the column name constants for schema maintainability.

## Out of Scope
- Adding new columns or tables to the schema
- Changing the Event Bus WAL/busy_timeout configuration
- Migrating away from SQLite
- Adding connection pooling beyond the current single-shared-connection model
- Refactoring the offset migration logic in `migrate_legacy_offsets()`
- Adding TTL-based archival support (documented as "Not yet implemented")
- Changing the `consumer_delivery` and `consumer_offsets` table schemas

## Dependencies
N/A: none

## Unresolved Questions
- Should `fetch_events_since()` validate `limit`/`offset` at the Python level and raise `ValueError` for negative values, or should it silently clamp them to zero?
- Is the current `check_same_thread=False` + `get_db_lock()` pattern sufficient for asyncio.to_thread() concurrency, or should we consider per-thread connections with connection pooling?
- Should `redeliver_event()`'s `now` parameter default to `None` and fall back to `strftime('now')` for backward compatibility with existing callers?

## AI Implementation Instruction
Do not rewrite unrelated files. Keep changes minimal and focused on: (1) fixing the SQL injection in fetch_events_since(), (2) adding explicit transaction management to ack_event and nack_event, (3) removing redundant pre-checks from requeue_event and redeliver_event, (4) unifying timestamp handling, and (5) extracting column name constants. After each change, verify that return value semantics match the documented contract. Before removing any pre-check SELECT, confirm the UPDATE's WHERE clause provides equivalent protection. Use the delegated modules consistently — do not introduce hybrid patterns where both the inline and delegated versions coexist. After changes, run existing tests and type check.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260911-221345
- **Related target files**: scripts/eventbus/db.py
