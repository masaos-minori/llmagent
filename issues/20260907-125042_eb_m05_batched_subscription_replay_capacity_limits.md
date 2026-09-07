# Batch subscription replay and define EventBus capacity limits

## Priority
Medium

## Summary
`scripts/eventbus/subscribe_route.py`'s `_fetch_replay()` (lines 45-62) loads every event with
`seq > start_seq` via a single `.fetchall()` with no `LIMIT`/batching — confirmed by direct
read. All EventBus database operations share one SQLite connection and one module-level
`threading.Lock` (`scripts/eventbus/db.py`'s `_db_lock`, confirmed by direct read of
`get_db_lock()`/`open_db()`), so a subscriber with an old offset replaying a large backlog holds
that lock (via `run_with_db_lock()`) for the full duration of its `.fetchall()`, blocking
publish/ACK/NACK/DLQ/health operations that also route through the same lock. No configuration
field exists for supported publish rate, subscriber count, retained-event count, or replay
batch size.

## Background
Confirmed by direct read: `subscribe_route.py`'s `_fetch_replay()` executes one unbounded query
inside `run_with_db_lock()` (line 64), and `scripts/eventbus/route_helpers.py`'s
`run_with_db_lock()` (lines 66-75) wraps every DB-touching route (`publish_route.py`,
`ack_route.py`, `dlq_route.py`, `replay_route.py`, `health_route.py`) in the same
`asyncio.to_thread(_locked)` pattern, all contending for the same `_db_lock`.
`scripts/eventbus/config.py`'s `EventBusConfig` dataclass has no field for replay batch size,
subscriber count, retained-event count, or publish rate — confirmed by direct read of its
field list (lines 36-42).

## Problem
- A reconnecting consumer with a far-behind offset causes `_fetch_replay()` to load
  potentially the entire event history into memory in one `.fetchall()` call, and to hold the
  shared lock for that call's full duration — during which every other route (`publish`, `ack`,
  `nack`, `dlq`, `health`) is blocked waiting on the same lock.
- No operating envelope (publish rate, subscriber count, retained-event count, replay size,
  latency objectives) is defined or enforced anywhere, so there is no evidence-based basis for
  deciding when the system is approaching its limits versus operating normally.
- `health_route.py`'s `max_queue_depth() >= 500` threshold (line 51) and `broker.py`'s
  `_SLOW_CONSUMER_THRESHOLD = 100` (line 12) are the only capacity-adjacent signals that exist
  today, and neither is derived from a documented capacity model — they are hardcoded values
  with no stated rationale (tracked separately in this batch as the operational-thresholds
  issue).

## Reason for Change
Bound resource use and establish an evidence-based operating envelope. Initial replay must not
monopolize memory or the global database lock, and operators must be able to observe
contention before it becomes an outage.

## Implementation Intent
Read initial replay in bounded, configurable batches (e.g. fetch and yield in chunks rather
than one `.fetchall()`), releasing and reacquiring `_db_lock` between batches so other routes
are not blocked for the full replay duration. Preserve the existing register-before-replay
ordering (`subscribe_route.py` already subscribes to the broker before starting replay, at line
39, specifically to avoid losing events published during replay — keep this property while
batching). Define supported publish rate, subscriber count, retained-event count, replay size,
and latency objectives based on representative load testing, and decide from measurements
whether the current single-connection/single-lock model needs separate read connections or a
connection manager.

## Target Files or Areas
- `scripts/eventbus/subscribe_route.py`
- `scripts/eventbus/db.py`
- `scripts/eventbus/route_helpers.py`
- `scripts/eventbus/health_route.py`
- `scripts/eventbus/broker.py`

## Required Changes
- Read initial replay in bounded, configurable batches.
- Preserve register-before-replay behavior without losing or duplicating events published
  during replay.
- Define supported publish rate, subscriber count, retained-event count, replay size, and
  latency objectives.
- Instrument database-lock wait time, query duration, replay backlog, and batch progress.
- Run representative load and concurrency tests.
- Decide from measurements whether separate read connections or a connection manager are
  required.

## Constraints
- Keep unrelated behavior unchanged.
- Do not weaken fail-closed behavior, validation, or auditability.
- Update the canonical ADR or EventBus specification when the delivery contract changes.
- Do not mark this issue complete with documentation-only changes when runtime behavior is
  defective.
- Do not invent configuration values, migration history, or approval evidence — capacity
  numbers must come from actual measurement, not assumption.

## Acceptance Criteria
- [ ] Initial replay has bounded memory use (no single unbounded `.fetchall()` for a large
      backlog).
- [ ] Events published during replay are neither lost nor delivered twice — the existing
      register-before-replay + `replay_ceil` duplicate-discard logic in `subscribe_route.py`
      (lines 39-76) continues to hold under batching.
- [ ] Publish and ACK latency remain within documented targets during large replay and DLQ
      activity.
- [ ] Capacity limits and their test methodology are documented.
- [ ] Health or metrics expose material database-lock contention.

## Testing Expectations
Add load/concurrency tests that measure publish/ACK latency while a subscriber replays a large
backlog, confirming batching keeps the lock-hold time bounded. Run the complete EventBus test
suite and the repository's linting, type checking, and documentation consistency checks.

## Documentation Impact
Document the batched-replay design, the measured capacity limits, and the test methodology
used to derive them in `docs/06_eventbus_05_configuration-and-operations.md` or the equivalent
canonical operations specification.

## Out of Scope
- `/replay` endpoint's own pagination/snapshot-consistency issue (tracked separately in this
  batch as EB-M04) — this issue is specifically about `/subscribe`'s initial-replay path.
- Centralizing the currently-hardcoded operational thresholds (`_SLOW_CONSUMER_THRESHOLD`,
  queue `maxsize`, health's `500` backlog threshold) into validated configuration — tracked
  separately in this batch.

## Dependencies
N/A: none, though the operational-thresholds-centralization issue in this batch should consume
whatever batch-size/capacity constants this issue introduces.

## Unresolved Questions
Whether separate read connections or a connection-pool/manager are needed depends on load-test
results this issue is expected to produce — do not decide this in advance of measurement.

## AI Implementation Instruction
Preserve `subscribe_route.py`'s existing register-before-replay-then-live-delivery ordering and
its `replay_ceil`-based duplicate-discard logic exactly — batching the SQLite fetch must not
change when the broker subscription is registered relative to the replay query. Measure before
deciding on connection-pooling changes; do not implement a connection manager speculatively.
