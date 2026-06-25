# Implementation: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md — full rewrite (req #32)

## Goal

Rewrite this document to reflect the new delivery state machine (req #24–#30): explicit ack/nack API, delivery_failure_count-based DLQ promotion, inline promotion, ack-based offset advancement.

## Scope

- Full rewrite of the document
- Add delivery state machine diagram and transition table
- Add counter semantics table (delivery_failure_count, dlq_requeue_count)
- Add DLQ promotion section covering both inline and sweep paths
- Add updated offset semantics section
- Remove all references to old `retry_count >= max_retry` and 60-second-only DLQ promotion

## Assumptions

- req #24–#30 are all implemented before this doc update is published
- State transitions are: LIVE → ACKED (ack), LIVE → RETRY (nack), RETRY → DLQ (threshold), RETRY → ACKED (ack after partial failures), DLQ → LIVE (requeue)
- Offset is updated on ack (req #29); mid-stream checkpoint removed

## Implementation

### Target file

`docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

### Procedure

1. Replace full file content with new state machine documentation

### Method

Full rewrite (replace current ~46 lines with new ~80 lines).

### Details

**Full target content:**
```markdown
# Event Bus: DLQ, Offsets, and Delivery Semantics

## Delivery State Machine

Events transition through these states:

```
LIVE ──ack──────────────────────────────────────────────────► ACKED
LIVE ──nack (count < max_retry)──────────────────────────────► RETRY
RETRY ──nack (count reaches max_retry, inline)───────────────► DLQ
RETRY ──ack──────────────────────────────────────────────────► ACKED
DLQ ──requeue────────────────────────────────────────────────► LIVE
```

| Transition | Trigger | Side effect |
|---|---|---|
| LIVE → ACKED | `POST /events/{id}/ack` | `acked_at` set; offset advanced if `consumer_id` provided |
| LIVE → RETRY | `POST /events/{id}/nack` | `delivery_failure_count` incremented |
| RETRY → DLQ | nack when `delivery_failure_count >= max_retry` | `dlq_at` set; DLQ file written atomically |
| RETRY → ACKED | `POST /events/{id}/ack` after partial failures | same as LIVE → ACKED |
| DLQ → LIVE | `POST /dlq/{id}/requeue` | `dlq_at` cleared; `dlq_requeue_count` incremented |

## Delivery Counters

| Counter | When incremented | Resets? | Field |
|---|---|---|---|
| `delivery_failure_count` | Each `POST /events/{id}/nack` | Never | `events.delivery_failure_count` |
| `dlq_requeue_count` | Each `POST /dlq/{id}/requeue` | Never | `events.dlq_requeue_count` |

Note: `retry_count` is deprecated. It was previously incremented on DLQ requeue and used for
promotion threshold. It is now replaced by the two counters above.

## DLQ Promotion

**Primary path (inline)**: When `delivery_failure_count` reaches `max_retry`, the nack endpoint
immediately promotes the event to DLQ. DLQ promotion happens in the same `asyncio.to_thread()`
call as the failure count increment — no delay.

**Safety-net sweep (background)**: The background loop runs every 60 seconds and calls
`sweep_orphans()`. Under normal operation, this promotes 0 events. Non-zero sweep count
indicates a bug in the inline promotion path — check logs for "swept N orphan(s)" messages.

### Promotion actions

1. Write `{deadletter_dir}/{event_id}.json` atomically (tempfile + `os.replace`)
2. Set `dlq_at` on the events row with `WHERE dlq_at IS NULL` (idempotent)

### Requeue

`POST /dlq/{event_id}/requeue`:
- Clears `dlq_at` (event returns to LIVE state)
- Increments `dlq_requeue_count`
- Does NOT reset `delivery_failure_count`

If `delivery_failure_count` is still >= `max_retry` after requeue, the next nack will immediately
re-promote to DLQ. To allow re-delivery, either the consumer must succeed (ack) or `max_retry`
must be increased.

## Consumer Offsets

Offset files: `{offsets_dir}/{consumer_id}` (plain text integer, sanitized filename).

### Offset semantics

Offsets represent "last successfully processed event" (not "last delivered event").

The offset is advanced **only** when `POST /events/{id}/ack?consumer_id=X` is called.
There is no mid-stream automatic offset checkpoint.

On reconnect: if `consumer_id` is set and `since_seq == 0`, the saved offset is read and
used as the start sequence — resuming from the last acked event.

### Offset guarantee

| Property | Behavior |
|---|---|
| Offset advances | On explicit ack only |
| Crash recovery | Resumes from last acked seq (may re-deliver post-ack events) |
| No consumer_id | Stateless; no offset file; `since_seq` used directly |

## Delivery Guarantee

| Property | Value |
|---|---|
| Delivery guarantee | At-least-once (until acked) |
| Duplicate suppression on publish | Yes — `event_id` UNIQUE constraint |
| Duplicate delivery on consumer | Possible — after crash, events since last ack are re-delivered |
| Ordering | Per-topic seq ascending; cross-topic not guaranteed |

## Reliability Limits

- SQLite is the only durable store; if the DB file is lost, all events are lost
- JSONL archive is supplementary; may diverge from SQLite if append fails
- DLQ sweep runs every 60 s; inline promotion is immediate but depends on consumers calling nack
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| State machine present | `grep "LIVE\|RETRY\|DLQ\|ACKED" docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` | multiple matches |
| Old promotion criteria removed | `grep "retry_count >= max_retry" docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` | 0 results |
| Counter table present | `grep "delivery_failure_count" docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` | match |
| Inline promotion described | `grep "inline\|immediately" docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` | match |
