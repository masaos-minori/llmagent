---
title: "Event Bus: DLQ Operations"
category: eventbus
tags:
  - event-bus
  - dlq
  - dead-letter-queue
  - requeue
  - background-loop
  - sweep
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_nack-health-dlq.md
  - 06_eventbus_02_dlq-background-loop.md
  - 06_eventbus_05_delivery-operations.md
source:
  - 06_eventbus_05_configuration_deploy_and_operations.md
---

# Event Bus: DLQ Operations

## DLQ Operations

### DLQ file creation timing

DLQ files are created immediately during inline promotion (on `/nack` call) at `{deadletter_dir}/{event_id}.json`. The background DLQ loop (60-second interval) is a safety sweep that catches events which reached the retry threshold but were not promoted inline (e.g., due to a race condition).

### Background DLQ loop role

The background DLQ loop runs every 60 seconds and queries for events with `delivery_failure_count >= max_retry AND dlq_at IS NULL`. It uses an optimistic lock: only counts events where `dlq_at` is still NULL, preventing double-promotion. If the sweep finds orphans, it logs `"dlq_loop: swept %d orphan(s) missed by inline promotion"`. Non-zero sweep results may indicate an inline promotion issue.

### DLQ requeue behavior

Requeueing a DLQ event via `POST /dlq/{event_id}/requeue` clears `dlq_at` and increments `dlq_requeue_count` by 1. **Important**: `delivery_failure_count` is NOT reset on requeue. If the event's `delivery_failure_count >= max_retry`, it will be immediately re-promoted to DLQ on the next background loop tick (within 60 seconds). Requeue only works for events with `delivery_failure_count < max_retry`.

### Monitoring sweep results

Orphan DLQ promotions are logged to the application log as `"dlq_loop: swept %d orphan(s) missed by inline promotion"`. Check the logs for non-zero sweep counts — this may indicate an inline promotion issue and should be investigated. The health endpoint does not expose a `dlq_sweep_count` field; monitoring requires log analysis.

## Related Documents

- `06_eventbus_02_nack-health-dlq.md`
- `06_eventbus_02_dlq-background-loop.md`
- `06_eventbus_05_delivery-operations.md`

## Keywords

event-bus
dlq
dead-letter-queue
requeue
background-loop
sweep
