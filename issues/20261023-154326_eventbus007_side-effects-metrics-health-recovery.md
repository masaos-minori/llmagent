# Clarify side-effect delivery semantics and complete metrics, health, and DLQ recovery

## Priority
Medium

## Summary
Make the publish and requeue side effects observable and unambiguous, make health and metrics measure what their names claim, separate liveness, readiness and integrity, and provide a supported DLQ file reconciliation path.

## Background
Re-verified against HEAD; several memo claims are stale or only partly true:
- Confirmed: the database health check is `SELECT 1` only (`check_db` in `scripts/eventbus/db_conn.py`); `/health` mixes liveness, readiness and capacity into one 200/503 status (`scripts/eventbus/health_route.py`).
- Confirmed: `Broker.slow_consumer_count()` (`scripts/eventbus/broker.py`) calls `_slow_consumer_total.inc(count)` every time it is called, and `health_check` calls it on every poll, so a read-only health request inflates the cumulative counter while a consumer stays slow.
- Confirmed: in `run_with_db_lock` (`scripts/eventbus/route_helpers.py`) the query duration timer starts before the lock is acquired, so `_db_query_duration` includes lock wait; the separately measured `lock_wait` includes thread dispatch and queuing. The `lock_wait_high` and `query_duration_high` degraded reasons are therefore not independent measurements.
- Stale/partly true: JSONL append and broker notification failures are not log-only. `scripts/eventbus/publish_route.py` already increments `_jsonl_append_failure_counter` and `_broker_notify_failure_counter` (prometheus counters). However, no metrics exposition endpoint or exporter exists in `scripts/eventbus/` (no `/metrics`, no `generate_latest`, no `start_http_server`), and `/health` reports only the lock contention counter, so the counters are in-process and not observable. No DLQ file write failure counter was found.
- DLQ promotion writes the file first (`_atomic_write`) and then sets `dlq_at` in SQLite (`scripts/eventbus/dlq.py`), so a crash between the two leaves an orphan file with `dlq_at IS NULL`, which the next sweep re-promotes; it self-heals. The unrecoverable cases are a file deleted or corrupted after promotion, and any divergence the memo describes beyond that is not confirmed. A write failure inside `sweep_orphans` aborts the rest of that sweep cycle (caught by `_dlq_loop` as `OSError`).
- Not found: the memo's `published_at` comment inaccuracy (no comment about idempotency equality was found next to `published_at` in `scripts/eventbus/`).
Aggregated from the memo's publish/requeue side effects item and its metrics, health and DLQ file recovery item.

## Problem
Requeue creates a SQLite event and relies on consumer replay rather than live broker push, which is not stated for operators; side-effect failure counters exist but are not exported; a read-only health request mutates `_slow_consumer_total`; lock-wait and query-duration measurements overlap, producing misleading degraded reasons; the database health check does not distinguish liveness, readiness and integrity; and a DLQ file deleted or corrupted after promotion has no reconciliation path.

## Reason for Change
Liveness, readiness and integrity are different operational questions, and SQLite and DLQ-file divergence needs a deterministic recovery path.

## Implementation Intent
Keep the existing SQLite durability boundary unless an owner changes it. Document (and where useful return) that requeue is delivered through replay, expose side-effect failure metrics, represent the current slow-consumer count as a gauge or count transitions, stop mutating metrics from health reads, separate thread-dispatch, lock-wait, DB-execution and total duration, define liveness, readiness and integrity checks, and add a DLQ reconciliation tool or deterministic recovery procedure.

## Target Files or Areas
`scripts/eventbus/publish_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/broker.py`, `scripts/eventbus/route_helpers.py`, `scripts/eventbus/health_route.py`, `scripts/eventbus/db_conn.py`, tests `tests/eventbus/test_eventbus_health.py`, `test_eventbus_route_helpers_metrics.py`, `test_eventbus_slow_consumer.py`, `test_eventbus_dlq.py`, `test_eventbus_replay_subscribe.py`, monitoring and alert configuration (location not confirmed), `docs/24_eventbus/`.

## Required Changes
- Document, and where useful return in the response, that requeue is delivered through consumer replay rather than immediate broker push; record the owner decision on immediate notification.
- Export the existing JSONL and broker failure counters (and add a DLQ file write failure counter) through a metrics exposition endpoint or equivalent, or state that they are intentionally log-only.
- Make the slow-consumer figure a gauge of the current count, or increment the counter only on state transitions; never mutate metrics from health reads.
- Start the query-duration timer after the lock is acquired and measure dispatch, lock wait, DB execution and total separately.
- Define liveness, readiness and integrity checks separately; readiness should not imply schema integrity unless integrity is checked.
- Add a DLQ reconciliation tool or deterministic recovery procedure for DLQ files that are missing or corrupted relative to `dlq_at` rows, and for orphan files.

## Constraints
Existing health response fields consumed by monitors stay backward compatible unless the owner agrees otherwise.

## Acceptance Criteria
- Requeue delivery timing is unambiguous.
- Monitoring detects side-effect failures without log scraping alone and repeated health polls do not inflate cumulative counters.
- Lock and query degraded reasons use distinct measurements; readiness does not imply schema integrity unless integrity is checked.
- Missing and orphaned DLQ files have a supported recovery path.
- Side-effect failure counters (JSONL, broker, DLQ file) are observable outside the process log, or are documented as intentionally log-only.

## Testing Expectations
JSONL append failure after commit; broker notification failure after commit; requeue followed by reconnect and replay; slow consumer enters, remains, recovers and re-enters; slow query without contention and contention with a short query; missing and orphaned DLQ files; disk-full, permission, commit and process-crash fault injection. Then ruff and mypy.

## Documentation Impact
Yes: requeue delivery semantics, metric definitions, health tiers and the DLQ recovery procedure.

## Out of Scope
Changing the SQLite durability boundary; the requeue transaction fix (H-01).

## Dependencies
Related to H-01 (requeue) and H-03 (integrity check). No open issue under `issues/` overlaps. Large item: consider splitting into delivery semantics, health/metrics and DLQ recovery at plan time.
The readiness definition feeds the deployment gate in H-03 (`eventbus003`); coordinate the response fields so H-03 can rely on them.

## Unresolved Questions
- Is immediate broker notification on requeue required? Owner decision.
- Is a metrics exposition endpoint wanted at all (the counters exist today but nothing scrapes them)? Owner decision; the loopback and authentication model applies to a new route.
- The memo's `published_at` comment claim and the exact DLQ divergence scenarios beyond file deletion or corruption are not confirmed; verify before implementing item 8.

## AI Implementation Instruction
- Read the listed implementation, tests, and design documents before editing; keep changes minimal and do not rewrite unrelated files.
- Preserve the existing public contract unless this issue explicitly names a contract change; an unresolved owner decision is reported, not guessed.
- Do not resolve an implementation defect by changing documentation alone.
- Keep transaction, locking, authorization, durability and fail-closed boundaries explicit.
- Add or update automated tests for every acceptance criterion; do not implement out-of-scope items.

## Traceability
- **Workflow phase**: `issue-creator` (converted from `memo-issue.md`, task `M-02`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-154326
- **Related target files**: `scripts/eventbus/publish_route.py`, `scripts/eventbus/health_route.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/broker.py`
