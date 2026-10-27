# Correct EventBus database timing metrics and align health with deployment readiness

## Priority
Medium

## Summary
Fix the unreachable query-duration observation and the lock-wait measurement in `run_with_db_lock()`, make the slow-consumer gauge reflect current state, and make the health API and the deployment readiness check use one documented contract.

## Background
Source: `memo-issue.md` Issue 08, re-verified in part against current source on 2026-10-27.

- In `scripts/eventbus/route_helpers.py`, `_locked()` computes `elapsed` and calls `_db_query_duration.observe(elapsed)` after a `try`/`finally` whose `try` body ends in `return func()`; those two lines are unreachable, so the query-duration histogram is never observed. `Explicit in code`.
- `lock_wait` is measured from `start_time` (before lock acquisition) to the outer `finally`, so it includes query execution time; the contention counter increments when this value exceeds 1 ms. `Explicit in code`.
- The slow-consumer gauge update only for positive counts, the health payload (`integrity=None`, liveness from the DLQ task, readiness from the DB) and the deployment script that searches raw JSON text: `Needs confirmation` (not read in this verification; taken from the memo).
- Prior work: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md` and `issues/done/20261023-154326_eventbus003_startup-gate-schema-health.md` addressed earlier metrics and health items; this defect remains in current source.

## Problem
Query-duration data is never recorded, contention and wait-time metrics include query time, and (per the memo) the health fields and the deployment gate can disagree.

## Reason for Change
Alerts and gates built on these metrics are not meaningful. No outage is cited; severity is Medium (observability correctness).

## Implementation Intent
Measure lock wait only until acquisition and lock-hold/query time from acquisition to callback completion, recorded in a `finally` so it also covers exceptions. Then, after confirming the memo's health and gauge claims in source, define one health contract (liveness, readiness, which components) that the API fields, HTTP status and `deploy/` scripts all derive from.

## Target Files or Areas
- `scripts/eventbus/route_helpers.py`
- `scripts/eventbus/broker.py` (slow-consumer gauge) and the health route (`scripts/eventbus/health_route.py`), `Unknown` until confirmed
- `deploy/` scripts that check EventBus readiness (`Unknown` until confirmed)
- `tests/eventbus/`, `tests/deploy/`
- EventBus health/operations docs under `docs/24_eventbus/`

## Required Changes
- Record lock-wait time only up to lock acquisition and apply the contention threshold to it.
- Record query/lock-hold duration in a reachable `finally` path.
- Set the slow-consumer gauge on every calculation including zero, and reset broker gauges on unsubscribe, overflow disconnect and shutdown (after confirming the current behavior).
- Define liveness and readiness independently and decide what `integrity` reports (implement or remove the placeholder).
- Make the deployment readiness check parse the health JSON structurally and use the same predicate as the API contract.

## Constraints
- Do not rename existing metric names unless unavoidable; if a definition changes, document it.
- Health HTTP status semantics for capacity-only 503 responses must be documented, not silently changed.

## Acceptance Criteria
- An uncontended DB call records near-zero wait and a positive query duration.
- A contended call increments the contention counter; a raising callback still records duration.
- The slow-consumer gauge returns to zero after recovery.
- API health fields, HTTP status and the deployment gate agree on one readiness predicate.

## Testing Expectations
- Unit tests with a controlled clock or barriers for wait versus hold time and for the exception path.
- Broker tests for gauge reset; health route tests for DB, broker and DLQ-task failure states.
- A deploy-script test (or contract test) sharing the readiness predicate with the API tests.
- `uv run pytest tests/eventbus tests/deploy`, mypy, ruff.

## Documentation Impact
Yes. Document the metric definitions and the health/readiness contract in the EventBus operations docs; current behavior only.

## Out of Scope
- Adding new metrics or dashboards.
- Connection pooling or lock strategy changes (see the shutdown admission issue for shutdown behavior).
- Facade migration of `route_helpers.py` imports.

## Dependencies
N/A: none open. `plans/20261027-120858_ebcompat002_decide-eventbus-db-facade.md` edits `route_helpers.py` imports; coordinate ordering. `issues/20261027-155845_ebshutdown002_close-shutdown-admission-race.md` also edits `run_with_db_lock`; implement one after the other.

## Unresolved Questions
- Do the slow-consumer gauge, `integrity=None` and the deployment raw-text check exist as described in the memo? `Needs confirmation`: read the broker, health route and `deploy/` scripts before implementing.
- Should readiness require the broker and DLQ task, or only the DB? `Needs confirmation` (owner decision).

## AI Implementation Instruction
Start with the confirmed `run_with_db_lock` timing fix and its tests. Confirm the memo's remaining claims in source and list any that are refuted before changing code. Do not alter unrelated metrics or deployment behavior.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-155849
- **Related target files**: `scripts/eventbus/route_helpers.py`, `tests/eventbus/`, `tests/deploy/`, `docs/24_eventbus/`
