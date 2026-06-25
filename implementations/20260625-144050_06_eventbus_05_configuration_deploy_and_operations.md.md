# Implementation: docs/06_eventbus_05_configuration_deploy_and_operations.md — Delivery Operations section (req #34)

## Goal

Add a `## Delivery Operations` section to the ops doc covering retry policy, DLQ promotion/requeue policy, consumer responsibilities, how to investigate retry backlog and DLQ lag, and timeout handling. This makes the delivery semantics operable without reading source code.

## Scope

- Add `## Delivery Operations` section after "Validation status"
- Subsections: Retry policy, DLQ promotion policy, Consumer responsibility, Investigating retry backlog and DLQ lag, Requeue policy, Timeout handling

## Assumptions

- req #19, #24–#31 are implemented before this doc is published
- `/health` exposes `retry_backlog`, `dlq_orphan_count`, `total_delivery_failures`
- No automatic timeout-based nack exists; consumers are responsible for nack on timeout

## Implementation

### Target file

`docs/06_eventbus_05_configuration_deploy_and_operations.md`

### Procedure

1. Append `## Delivery Operations` section at the end of the file

### Method

Append new section to existing file content.

### Details

**New section to append:**

```markdown
## Delivery Operations

### Retry policy

Events are retried when consumers call `POST /events/{id}/nack`. Each nack increments
`delivery_failure_count`. When `delivery_failure_count >= max_retry`, the event is
promoted to the DLQ inline (no delay).

| Config field | Effect |
|---|---|
| `max_retry` | Number of nacks before DLQ promotion. No default — must be set explicitly. |

### DLQ promotion policy

**Primary path**: Inline promotion via nack endpoint (immediate; no delay).

**Safety-net sweep**: Background loop (every 60 s) promotes any events that reached the
threshold but were not caught inline. Under normal operation, the sweep promotes 0 events.
Non-zero sweep count indicates a bug — check logs for "swept N orphan(s)" messages.

### Consumer responsibility

Consumers MUST:
1. Call `POST /events/{id}/nack` when processing fails (including on timeout)
2. Call `POST /events/{id}/ack?consumer_id=X` on success (also advances offset)

Consumers MUST NOT:
- Silently discard events without calling ack or nack
- Assume that offset advancement happens on delivery (it requires explicit ack)

### Investigating retry backlog and DLQ lag

Use `GET /health` to inspect delivery health indicators:

| Field | Meaning | Action if non-zero |
|---|---|---|
| `retry_backlog` | Events with ≥1 failure, not yet at threshold, not acked | Investigate consumer errors |
| `dlq_orphan_count` | Events at threshold but not promoted | File a bug; check inline promotion logs |
| `total_delivery_failures` | Cumulative failure count across all events | Monitor for sudden increases |

A `degraded_reasons` entry of `retry_backlog_high` (>10 events) or `dlq_orphan_detected` (>0)
indicates a delivery health problem.

### Requeue policy

`POST /dlq/{event_id}/requeue`:
- Clears `dlq_at` (returns event to live state)
- Increments `dlq_requeue_count` (does NOT reset `delivery_failure_count`)
- If `delivery_failure_count` is still >= `max_retry`, the next nack will immediately re-promote

To allow sustained re-delivery after requeue:
- The consumer must succeed (call ack) before the next nack
- Or `max_retry` must be increased in config and the service restarted

### Timeout handling

There is currently no automatic timeout-based nack. Consumers are responsible for detecting
processing timeouts and calling nack explicitly. Recommended pattern:

```python
import asyncio

async def process_with_timeout(event_id: str, process_fn, timeout_s: float) -> None:
    try:
        await asyncio.wait_for(process_fn(), timeout=timeout_s)
        requests.post(f"{BASE_URL}/events/{event_id}/ack", params={"consumer_id": CONSUMER_ID})
    except (asyncio.TimeoutError, Exception):
        requests.post(f"{BASE_URL}/events/{event_id}/nack")
```
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Section exists | `grep "## Delivery Operations" docs/06_eventbus_05_configuration_deploy_and_operations.md` | 1 result |
| Retry policy present | `grep "delivery_failure_count" docs/06_eventbus_05_configuration_deploy_and_operations.md` | match |
| Requeue policy present | `grep "dlq_requeue_count" docs/06_eventbus_05_configuration_deploy_and_operations.md` | match |
| Timeout section present | `grep "Timeout" docs/06_eventbus_05_configuration_deploy_and_operations.md` | match |
