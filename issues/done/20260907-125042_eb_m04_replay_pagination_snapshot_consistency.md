# Make replay pagination validated, snapshot-consistent, and bounded

## Priority
Medium

## Summary
`scripts/eventbus/app.py`'s `/replay` route declares `fmt: str = Query(default="sse",
alias="format")` with no enum/pattern constraint — confirmed by direct read, any string other
than `"json"` is treated as SSE in `replay_route.py`'s `if fmt == "json":` branch (line 43),
so e.g. `?format=xml` silently falls through to SSE instead of failing validation.
`replay_route.py`'s JSON-format branch also fetches page items (`_fetch()`, line 41) and the
total count (`_count()`, line 49) via two separate `run_with_db_lock()` calls — confirmed by
direct read, each acquires and releases the shared `_db_lock` independently, so a publish
committed between the two calls is reflected in one but not the other.

## Background
Confirmed by direct read of `scripts/eventbus/app.py` line 130
(`fmt: str = Query(default="sse", alias="format")`) and `scripts/eventbus/replay_route.py`
lines 26-63: no `Literal["sse", "json"]`/regex constraint exists on `fmt`, and OpenAPI
therefore cannot list a restricted enum for it either. `_fetch()` (line 38) and `_count()`
(line 47) are separate closures each independently wrapped in `await run_with_db_lock(...)`
(lines 41, 49) — the lock (`scripts/eventbus/db.py`'s module-level `_db_lock`) is acquired and
released twice, not held across both reads, so no read-transaction/lock scope spans the two
queries together.

## Problem
- An unsupported `format` value (anything other than `json`) is silently accepted and served
  as SSE rather than rejected with a validation error, and OpenAPI cannot document the actual
  supported values because the parameter has no closed type.
- Between the `_fetch()` and `_count()` calls in the JSON-format path, a concurrent `/publish`
  can insert a new row — the returned `items` list is a snapshot *before* that insert while
  `total` may reflect *after* it (or vice versa, depending on interleaving), so the response's
  `total`/`items` do not necessarily describe the same database state.

## Reason for Change
Make replay a stable API contract. Inputs must be strictly validated, ordering must be
deterministic, and a JSON page must describe one consistent database snapshot.

## Implementation Intent
Restrict `format` to the closed set `sse`/`json` using FastAPI's `Literal`/enum support so
unsupported values return a validation error (422) and OpenAPI documents only the supported
values. In `replay_route.py`, fetch total count and page items under one lock acquisition and
one read (e.g. a single `run_with_db_lock()` call that runs both queries inside the same
closure, so they execute back-to-back while the lock is held, rather than two separate
lock-acquire/release round trips). Keep ordering stable by `seq` (already the case via
`fetch_events_since()`'s `ORDER BY seq`, confirmed in `db.py` line 215 — preserve this).

## Target Files or Areas
- `scripts/eventbus/app.py`
- `scripts/eventbus/replay_route.py`
- `scripts/eventbus/db.py`
- `docs/06_eventbus_06_reference-api.md`

## Required Changes
- Restrict `format` to the closed set `sse` and `json`.
- Return a validation error for unsupported values and expose the enum in OpenAPI.
- Fetch total count and page items under one lock and one read (combine `_fetch()`/`_count()`
  into a single `run_with_db_lock()`-wrapped closure).
- Keep ordering stable by sequence (already implemented — verify it remains so after the
  change).
- Document paging behavior when offset exceeds the available result set and while new events
  are published.

## Constraints
- Keep unrelated behavior unchanged.
- Do not weaken fail-closed behavior, validation, or auditability.
- Update the canonical ADR or EventBus specification when the delivery contract changes.
- Do not mark this issue complete with documentation-only changes when runtime behavior is
  defective.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] Supported formats (`sse`, `json`) succeed and unsupported formats return 422.
- [ ] OpenAPI lists only the supported `format` values.
- [ ] Each JSON response's `total` and `items` represent one internally consistent database
      snapshot, verified by a test that publishes concurrently with an in-flight replay request.
- [ ] Concurrent publish tests do not produce inconsistent page metadata.
- [ ] Pagination order remains deterministic by `seq`.

## Testing Expectations
Update `tests/eventbus/test_eventbus_replay_pagination.py` to add an invalid-`format` test
(expect 422) and a concurrent-publish-during-replay snapshot-consistency test. Run the complete
EventBus test suite and the repository's linting, type checking, and documentation consistency
checks.

## Documentation Impact
Update `docs/06_eventbus_06_reference-api.md` to document the closed `format` enum and the
snapshot-consistency guarantee for JSON replay pages.

## Out of Scope
- Batch-bounded initial subscription replay and capacity limits (tracked separately in this
  batch as EB-M05) — this issue only fixes `/replay`'s format validation and snapshot
  consistency, not `/subscribe`'s unbounded initial fetch.
- Authentication/authorization for the replay endpoint (tracked separately in this batch).

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Use FastAPI's `Literal["sse", "json"]` type annotation (or an equivalent enum) for the `fmt`
query parameter rather than manual string validation, so OpenAPI generation picks it up
automatically. Combine `_fetch()`/`_count()` into one locked closure rather than only
reordering the two separate `run_with_db_lock()` calls — reordering alone does not close the
race, since the lock is still released between them.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260907-125042
- **Related target files**: see Target Files or Areas above
