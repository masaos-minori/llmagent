---
title: "EventBus Publish Durability"
area: eventbus
tags:
  - publish
  - durability
  - recovery
  - metrics
related:
---
# EventBus Publish Durability

## Canonical Store

**SQLite is the canonical event store.** JSONL is derived data that can be rebuilt from SQLite using the reconcile mechanism described below.

Rationale:
1. The database commit is the publish success criterion — if the DB commit succeeds, the event is considered published.
2. JSONL is appended after the DB commit and can be rebuilt from SQLite.
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
- **Observable signal**: `eventbus_jsonl_append_failure_total` Prometheus Counter increments.
- **Log output**: Structured warning: `"eventbus: JSONL append failed (event still committed): {exc}"`.
- **Recovery**: Run `python scripts/eventbus/reconcile.py <db_path> <jsonl_path>` to rebuild JSONL from SQLite.

Affected file paths:
- `config/eventbus.toml` → `storage_dir` key defines the JSONL file location (e.g., `/opt/llm/storage/events.jsonl`).

### Broker Notification Failure

When the broker notification fails after a successful database commit:
- **Event status**: Published (DB commit succeeded).
- **Observable signal**: `eventbus_broker_notify_failure_total` Prometheus Counter increments.
- **Log output**: Structured exception log: `"publish broker notify error seq={seq}"`.
- **Subscriber recovery**: Subscribers can recover missed notifications through SQLite-backed replay via the `/replay` endpoint.

### Both Failures Simultaneously

Both failures can occur simultaneously. Each is independently observable via its own Prometheus metric. The event is still published — only the side effects fail.

### Disk-Full Scenario

- DB commit succeeds → event is published (canonical store updated).
- JSONL append fails with `OSError` → metric incremented, warning logged.
- Broker notification may succeed or fail independently → metric incremented if failed.
- Subscriber can recover via SQLite replay.

### Permission Failure Scenario

Same as disk-full — DB commit succeeds, JSONL append fails. No retry attempt (idempotent by nature — JSONL append is append-only). Reconciliation mechanism can restore JSONL when permissions are restored.

## Recovery Procedure

To rebuild JSONL from SQLite:

```bash
python scripts/eventbus/reconcile.py /opt/llm/db/eventbus.sqlite /opt/llm/storage/events.jsonl
```

The reconcile script:
1. Reads all events from SQLite ordered by sequence number.
2. Compares each line against existing JSONL content.
3. Writes missing lines to JSONL.
4. Returns statistics: `{reconciled: int, skipped: int, errors: int}`.

Partial lines in JSONL (from interrupted writes) are naturally excluded by line-based comparison.

## Metrics Reference

| Metric Name | Type | Description |
|-------------|------|-------------|
| `eventbus_jsonl_append_failure_total` | Counter | Number of JSONL append failures after successful database commit |
| `eventbus_broker_notify_failure_total` | Counter | Number of broker notification failures after successful database commit |
| `eventbus_broker_publish_failure_total` | Counter | Number of broker publish failures to individual subscribers |
| `eventbus_slow_consumer_total` | Counter | Number of slow consumer events detected (existing) |

## Related Documents

- [DLQ Operations Reference](01_dlq_operations.md)
- [DLQ Requeue API Reference](02_dlq_requeue_api.md)
- [Replay Operations Reference](03_replay_operations.md)
- [Event Bus Overview](../06_eventbus_01_system-overview.md)
- [Event Bus DLQ/Offsets/Delivery Semantics](../06_eventbus_04_dlq_offsets_and_delivery_semantics.md)

## Keywords

publish
durability
recovery
jsonl
sqlite
metrics
prometheus
