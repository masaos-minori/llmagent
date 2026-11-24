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
  - eventbus_07_configuration-and-operations.md
---
# EventBus Publish Durability

## Canonical Store

**`eventbus.sqlite` is the only EventBus system of record.** The EventBus keeps no event replica; structured security audit records are separate operational logs, and the DLQ JSON files are derived artifacts (see Recovery Procedure). The current code still appends an `events.jsonl` file after the commit (EVENTBUS-001); it is not part of the contract.

Authority model: SQLite is canonical for events and for DLQ state (`events.dlq_at`); a committed DLQ state is paired with a durable DLQ outbox generation request committed in the same transaction; the DLQ JSON files are derived artifacts, fulfilled by the background DLQ outbox worker after the commit (see [eventbus_03](eventbus_03_dlq_operations.md)); broker notification is best-effort and recoverable through SQLite replay; the publish guarantee is the database commit.

Rationale:
1. The database commit is the publish success criterion — if the DB commit succeeds, the event is considered published.
2. Broker notification is real-time delivery — it's a side effect of publishing, not part of the durable record.

## Publish Success Criterion

A publish operation succeeds when the database commit completes successfully. The post-commit operation (broker notification) is a best-effort side effect.

The publish flow:
1. Validate envelope schema against request body.
2. Execute `run_with_db_lock(_insert)` — this performs the SQLite INSERT OR IGNORE under the DB lock.
3. If `status == "conflict"`: return HTTP 409.
4. If `inserted == True`: attempt broker notification (best-effort).
5. Return HTTP 200 with `event_id` and `seq`.

Step 2 is the **only** step that determines publish success. Step 4 is best-effort and may fail without affecting the committed event.

## Failure Scenarios

### Broker Notification Failure

When the broker notification fails after a successful database commit:
- **Event status**: Published (DB commit succeeded).
- **Observable signal**: the exception log line below is the operator-visible signal. The in-process Prometheus Counter `eventbus_broker_notify_failure_total` increments but is not exposed by any endpoint.
- **Log output**: Structured exception log: `"publish broker notify error seq={seq}"`.
- **Subscriber recovery**: Subscribers can recover missed notifications by reconnecting to `/subscribe` with `since_seq` (SQLite-backed replay). `/replay` is restricted to the operator role.

### Disk-Full Scenario

- If the disk is full before the SQLite commit, the commit fails and the publish returns a non-success response; no event is committed.
- If the commit succeeds and the broker notification fails, the event is still published; the failure is logged and counted, and subscribers recover through SQLite replay.
- A critical disk shortage is a capacity signal that makes readiness false once the capacity signals are implemented (EVENTBUS-002; see `eventbus_10_health_endpoint.md`).

### Permission Failure Scenario

A permission failure on the database file fails the SQLite commit, so the publish returns a non-success response. A retry of the same event is idempotent in SQLite: an identical retry returns the original `seq`.

## Recovery Procedure

No event replica exists, so recovery of event data means reading from SQLite (via `/subscribe` with `since_seq`, or `/replay` with the operator role). Dead-letter JSON files are derived and are rebuilt from SQLite by the background reconciliation (see `eventbus_03_dlq_operations.md`).

## Requeue Delivery Semantics

Requeue (`POST /dlq/{event_id}/requeue`) delivers events through **consumer replay** via the lineage model (`redeliver_event`). It does NOT call `broker.publish()` — the requeued event is inserted into SQLite and becomes available for consumers to pick up via `/subscribe` with `since_seq`. The response includes `"delivery": "replay"` to make this unambiguous to operators.

If immediate broker notification on requeue is required, this would be a separate change (UNK-01 owner decision).

## Metrics

The failure counters (`eventbus_broker_notify_failure_total`, `eventbus_broker_publish_failure_total`, `eventbus_dlq_file_write_failure_total`) and `eventbus_slow_consumer_current` are registered in-process only; the service exposes no scrape endpoint and `/health` does not report them.

## Keywords

- publish
- durability
- recovery
- sqlite
- metrics
- prometheus
