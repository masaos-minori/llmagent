# Event Bus: DLQ, Offsets, and Delivery Semantics

## Dead Letter Queue (DLQ)

### Promotion criteria

An event is promoted to the DLQ when `retry_count >= max_retry AND dlq_at IS NULL`. The background loop (`_dlq_loop`) checks every 60 seconds.

### Promotion actions

1. Write a JSON file to `{deadletter_dir}/{event_id}.json` atomically (tempfile + `os.replace`)
2. Set `dlq_at` on the events row in SQLite

### Requeue

`POST /dlq/{event_id}/requeue` clears `dlq_at` and increments `retry_count` by 1. It does **not** reset `retry_count` to 0. If the event's `retry_count` is already at or above `max_retry`, the next DLQ loop tick will re-promote it.

## Consumer offsets

Offset files are stored in `{offsets_dir}/{consumer_id}` (plain text, one integer per file). The `consumer_id` is sanitized (`.` → `_`, `/` → `_`) before use as a filename.

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

**Deprecated**: `offset_checkpoint_interval` config field is no longer used.

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
- The DLQ loop runs every 60 seconds; there is a window where events with `retry_count >= max_retry` remain visible as live events
