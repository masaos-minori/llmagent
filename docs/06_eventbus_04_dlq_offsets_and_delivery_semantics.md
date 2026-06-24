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

### Checkpoint writes

The offset is written:
1. **On disconnect**: when the SSE generator receives `asyncio.CancelledError`
2. **Mid-stream checkpoint**: every `offset_checkpoint_interval` (default 10) delivered events, for crash recovery before disconnect

## Delivery semantics

| Property | Value |
|---|---|
| Delivery guarantee | At-least-once |
| Duplicate suppression on publish | Yes — `event_id` UNIQUE constraint in SQLite; duplicate publishes are silently ignored |
| Duplicate delivery on consumer | Possible — consumer may re-receive events after crash if checkpoint was not written before the crash |
| Ordering | Per-topic ordering is preserved (seq ascending); cross-topic ordering is not guaranteed |

## Reliability limits

- SQLite is the only durable store; if the DB file is lost, all events are lost
- JSONL archive is supplementary and may diverge from SQLite if append fails
- The DLQ loop runs every 60 seconds; there is a window where events with `retry_count >= max_retry` remain visible as live events
