---
title: "Event Bus: Known Inconsistencies and Issues"
category: eventbus
tags:
  - event-bus
  - known-issues
  - inconsistencies
  - spec-conflicts
  - deferred-items
  - ack-offset
  - monotonicity
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_subscribe-ack.md
  - 06_eventbus_02_dlq-background-loop.md
  - 06_eventbus_04_dlq_offsets_and_delivery_semantics.md
source:
  - index.md
---

# Event Bus: Known Inconsistencies and Issues

## Active Items

These items represent unresolved issues that require implementation changes or have active impact on users.

### Ack Offset Not Monotonically Enforced

| Item | Safe interpretation | Recommended action |
|---|---|---|
| `write_offset()` in `offsets.py` does not enforce monotonic offset advancement (no max(current, new) check) | Acknowledging an older event seq moves the consumer offset backward — consumers may receive duplicate events on reconnect | Consumers must handle potential offset rollback; no server-side fix planned |

## Docs-Only Items

These items are documentation improvements that do not require implementation changes.

### /replay?format=json Returns Paginated Object

| Item | Safe interpretation |
|---|---|
| `GET /replay?format=json` returns `{total, limit, offset, items}` not a raw array | Clients can paginate through replay results using limit/offset parameters |

### DLQ Promotion Is Inline-on-nack Plus Safety Sweep

| Item | Safe interpretation |
|---|---|
| Primary DLQ promotion is inline on `/nack` when `delivery_failure_count >= max_retry`; background loop is a safety sweep for orphans | The background DLQ loop catches events that reached the threshold but were not promoted inline; non-zero sweep results may indicate an inline promotion issue |

## Deferred Items

Agent runtime integration with Event Bus is intentionally not implemented at this time.

| Item | Status | Notes |
|---|---|---|
| Agent event publishing | Deferred | No Agent-side event producer is implemented. The Event Bus HTTP API supports publishing from any HTTP client; Agent-specific producers will be added in a future release. |
| Agent SSE subscription | Deferred | No Agent-side subscriber for consuming events via `/subscribe` SSE. Agent-side consumers will be added in a future release. |
| Agent event topics | Deferred | No Agent-defined topics exist today. Topic conventions for Agent lifecycle events will be defined when Agent integration is implemented. |

## Schema vs Implementation Differences

| Field | Schema definition | Runtime behavior | Status |
|---|---|---|---|
| `acked_at` | TEXT | Set during ack (idempotent — will not overwrite existing value) | Used — see `db.py::ack_event()` |
| `delivery_failure_count` | INTEGER NOT NULL DEFAULT 0 | Incremented on nack; triggers DLQ promotion at `>= max_retry` | Used — see `db.py::nack_event()` |
| `dlq_requeue_count` | INTEGER NOT NULL DEFAULT 0 | Incremented on DLQ requeue; does not reset `delivery_failure_count` | Used — see `db.py::requeue_event()` |
| `dlq_at` | TEXT | Set when event is promoted to DLQ (inline or background sweep) | Used — set during DLQ promotion |

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_subscribe-ack.md`
- `06_eventbus_02_dlq-background-loop.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

## Keywords

event-bus
known-issues
inconsistencies
spec-conflicts
deferred-items
ack-offset
monotonicity
