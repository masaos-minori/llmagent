# Event Bus: DLQ, Offsets, and Delivery Semantics

## Dead Letter Queue (DLQ)

### Primary promotion path: inline on nack

When a consumer calls `POST /nack?event_id=...`, the server increments `delivery_failure_count`. If the new value reaches `max_retry`, the event is promoted to the DLQ **immediately** as part of the nack response. The response includes `"dlq_promoted": true` when this occurs.

### Safety sweep: background DLQ loop

The background DLQ loop runs every 60 seconds and queries for events with `delivery_failure_count >= max_retry AND dlq_at IS NULL`. This catches events that reached the retry threshold but were not promoted inline (e.g., due to a race condition between nack and the loop).

The loop uses an optimistic lock: it only counts events where `dlq_at` is still NULL, preventing double-promotion when both paths race. If the sweep finds orphans, it logs `"dlq_loop: swept %d orphan(s) missed by inline promotion"`. Non-zero sweep results may indicate an inline promotion issue.

### Promotion actions (both paths)

1. Write a JSON file to `{deadletter_dir}/{event_id}.json` atomically (tempfile + `os.replace`)
2. Set `dlq_at` on the events row in SQLite

Both inline and background promotion use the same atomic write mechanism for consistency.

### Requeue

`POST /dlq/{event_id}/requeue` clears `dlq_at` and increments `dlq_requeue_count` by 1 (does **not** reset `delivery_failure_count`). 

**Important**: If the event's `delivery_failure_count` is already at or above `max_retry`, requeueing it will result in immediate re-promotion on the next DLQ loop tick (within 60 seconds). Requeue is not a "second chance" for events at the threshold — it only works for events with `delivery_failure_count < max_retry`.

## Consumer offsets

Offset files are stored in `{offsets_dir}/{sanitized_consumer_id}` (plain text, one integer per file). The `consumer_id` is sanitized by replacing `..`, `.`, and `/` with `_` (in that order) to prevent path traversal attacks. Replacement is applied to all occurrences across the full string. If the result is empty, `"default"` is used. Note: backslash characters are NOT sanitized — they pass through as-is.

### Offset restoration

On `/subscribe`, if `consumer_id` is set and `since_seq == 0`, the saved offset is read and used as the start sequence.

### Ack-only offset model

Consumer offsets advance only when the consumer explicitly acknowledges an event via `POST /events/{event_id}/ack?consumer_id={consumer_id}`. Offsets are never advanced automatically during streaming.

**Reconnect resume**

On reconnect, provide `consumer_id` (without `since_seq`) to resume from the last acknowledged offset. The subscribe handler calls `read_offset(offsets_dir, consumer_id)` at connect time and uses the stored seq as `start_seq` for the SQLite replay query.

Example reconnect flow:
1. Consumer connects: `GET /subscribe?consumer_id=svc-A`
2. Receives events seq=1..10, acks seq=10: `POST /events/{id}/ack?consumer_id=svc-A`
3. Disconnects
4. Reconnects: `GET /subscribe?consumer_id=svc-A` → replay starts from seq=11

**Consumer ID stability requirement**: Consumer IDs must be stable across restarts for offset resume to work. Process-lifetime stable IDs (e.g., PID-based) will NOT survive restarts — offsets will not resume. Recommended: use application-level identifiers (e.g., service name + instance ID) as consumer_ids.

**Deprecated**: `offset_checkpoint_interval` config field is no-op. Setting this in TOML emits a DeprecationWarning. Offset checkpointing was replaced with ack-only model.

## Delivery semantics

| Property | Value |
|---|---|
| Delivery guarantee | At-least-once |
| Duplicate suppression on publish | Yes — `event_id` UNIQUE constraint in SQLite; duplicate publishes are silently ignored |
| Duplicate delivery on consumer | Possible — consumer may re-receive events after crash if ack was not written before the crash |
| Ordering | Per-topic ordering is preserved (seq ascending); cross-topic ordering is not guaranteed |

## Reliability limits

- SQLite is the only durable store; if the DB file is lost, all events are lost
- JSONL archive is supplementary and may diverge from SQLite if append fails
- The DLQ loop runs every 60 seconds; there is a window where events with `delivery_failure_count >= max_retry` remain visible as live events
