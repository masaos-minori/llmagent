---
title: "EventBus Publish Durability"
area: eventbus
tags:
  - publish
  - durability
  - recovery
  - metrics
related:
  - eventbus_03_dlq_operations.md
  - eventbus_04_dlq_endpoint.md
  - eventbus_11_replay_endpoint.md
  - eventbus_01_system-overview.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
---
# EventBus Publish Durability

## Canonical Store

**SQLite is the canonical event store.** JSONL is derived data; no automated reconcile or rebuild tool exists (see Recovery Procedure).

Rationale:
1. The database commit is the publish success criterion — if the DB commit succeeds, the event is considered published.
2. JSONL is appended after the DB commit and is never read as primary data.
3. Broker notification is real-time delivery — it's a side effect of publishing, not part of the durable record.

## Publish Success Criterion

A publish operation succeeds when the database commit completes successfully. Post-commit operations (JSONL append, broker notification) are best-effort side effects.

The publish flow in `publish_route.py`:
1. Validate envelope schema against request body.
2. Execute `run_with_db_lock(_insert)` — this performs the SQLite INSERT OR IGNORE under the DB lock.
3. If `status == "conflict"`: return HTTP 409.
4. If `inserted == True`: attempt JSONL append (best-effort).
5. If `inserted == True`: attempt broker notification (best-effort).
6. Return HTTP 200 with `event_id` and `seq`.

Step 2 is the **only** step that determines publish success. Steps 4-5 are best-effort and may fail independently.

## Failure Scenarios

### JSONL Append Failure

When the JSONL append fails after a successful database commit:
- **Event status**: Published (DB commit succeeded).
- **Observable signal**: the warning log line below is the operator-visible signal. The in-process Prometheus Counter `eventbus_jsonl_append_failure_total` increments, but no endpoint exposes it (the service serves no Prometheus scrape endpoint and `/health` does not return this counter; see [eventbus_07](eventbus_07_configuration-and-operations.md)). (Explicit in code — `scripts/eventbus/publish_route.py`, `scripts/eventbus/health_route.py`)
- **Log output**: Structured warning: `"eventbus: JSONL append failed (event still committed): {exc}"`.
- **Recovery**: None automated. SQLite remains complete; the JSONL archive is missing the affected line.

Affected file paths:
- `config/eventbus.toml` → `storage_dir` key defines the JSONL file location.

### Broker Notification Failure

When the broker notification fails after a successful database commit:
- **Event status**: Published (DB commit succeeded).
- **Observable signal**: the exception log line below is the operator-visible signal. The in-process Prometheus Counter `eventbus_broker_notify_failure_total` increments but is not exposed by any endpoint.
- **Log output**: Structured exception log: `"publish broker notify error seq={seq}"`.
- **Subscriber recovery**: Subscribers can recover missed notifications by reconnecting to `/subscribe` with `since_seq` (SQLite-backed replay). `/replay` is restricted to the operator role.

### Both Failures Simultaneously

Both failures can occur simultaneously. Each is independently recorded by its own in-process counter and its own log line; only the log lines are visible to an operator. The event is still published — only the side effects fail.

### Disk-Full Scenario

- DB commit succeeds → event is published (canonical store updated).
- JSONL append fails with `OSError` → counter incremented, warning logged.
- Broker notification may succeed or fail independently → counter incremented if failed.
- Subscriber can recover via SQLite replay.

### Permission Failure Scenario

Same as disk-full — DB commit succeeds, JSONL append fails. No retry attempt (idempotent by nature — JSONL append is append-only). JSONL lines that failed to append are not restored automatically when permissions are restored.

## Recovery Procedure

No reconcile or rebuild script exists in the repository. A failed JSONL append is not retried and is not backfilled, so the JSONL archive can diverge from SQLite. Because SQLite is the canonical store, recovery of event data means reading from SQLite (via `/subscribe` with `since_seq`, or `/replay` with the operator role), not from JSONL. Any rebuild of the JSONL archive from SQLite must be done manually.

## Metrics Reference

These counters are registered in-process only; the service exposes no scrape endpoint and `/health` does not report them.

| Metric Name | Type | Description |
|-------------|------|-------------|
| `eventbus_jsonl_append_failure_total` | Counter | Number of JSONL append failures after successful database commit |
| `eventbus_broker_notify_failure_total` | Counter | Number of broker notification failures after successful database commit |
| `eventbus_broker_publish_failure_total` | Counter | Number of broker publish failures to individual subscribers |
| `eventbus_slow_consumer_total` | Counter | Number of slow consumer events detected (existing) |

## Keywords

- publish
- durability
- recovery
- jsonl
- sqlite
- metrics
- prometheus
