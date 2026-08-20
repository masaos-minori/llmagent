---
title: "Event Bus: Nack, Health, and DLQ Endpoints"
category: eventbus
tags:
  - event-bus
  - http-api
  - nack
  - health
  - dlq
  - dead-letter-queue
  - requeue
  - error-handling
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_01_publish-replay.md
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_02_04_dlq-background-loop.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: Nack, Health, and DLQ Endpoints

## POST /nack

Sends a NACK (Negative Acknowledgement) for an event. Increases `delivery_failure_count`, and moves the event to the DLQ once `delivery_failure_count >= max_retry`.

**Query Parameters:** `event_id` (required)
**Response:** On success, returns `{event_id, delivery_failure_count}`. A 404 error indicates the event was not found.

### NACK 側状態遷移行

以下は NACK 操作に対する現在のコード挙動です。ACK 側の行（初回 ACK、重複 ACK、NACK 後 ACK 等）は `docs/06_eventbus_02_02_subscribe-ack.md` を参照してください。

| シナリオ | 現在のコード挙動 | HTTP ステータス | レスポンスボディ | 永続化への副作用 |
|---|---|---|---|---|
| 初回 NACK | `nack_event` が `delivery_failure_count` を 0→1 に増加（以上） | 200 | `{event_id, delivery_failure_count}` | `delivery_failure_count` 増加；`>= max_retry` で DLQ 昇格 |
| 重複 NACK | `nack_event` に冪等性ガードなし；呼び出し毎に `delivery_failure_count` 再増加 | 200 | `{event_id, delivery_failure_count}` | カウンタが増加し続け、後続の重複呼び出しで DLQ 昇格を誘発する可能性 — **実装修正必要** |
| ACK 後 NACK | `nack_event` に `acked_at` チェックなし | 200 | `{event_id, delivery_failure_count}` | 既に ACK 済みでも NACK が「成功」し `delivery_failure_count` 増加 — **実装修正必要** |
| 不明なイベント ID (NACK) | `nack_event` が `-1` を返す | 404 | `ERR_EVENT_NOT_FOUND` | なし |

> ACK 側の遷移行（初回 ACK、重複 ACK、NACK 後 ACK、不明なイベント ID ACK、同時 ACK/NACK、コンシューマミスマッチ）については `docs/06_eventbus_02_02_subscribe-ack.md` を参照してください。

---

## GET /health

Returns the health status of each component. `ok` corresponds to HTTP 200, while `degraded`/`unhealthy` corresponds to HTTP 503.

**Response Fields:** `status`, `db`, `dlq_task`, `active_subscribers`, `max_queue_depth`, `slow_consumers`, `degraded_reasons`.

The `status` is `"ok"` only when all components are healthy. `degraded_reasons` lists failure causes (`db_unavailable`, `dlq_task_stopped`, `broker_queue_backlog_high`, `slow_consumers_detected`).

---

## GET /dlq

Retrieves a list of DLQ events (events where `dlq_at IS NOT NULL`).

**Query Parameters:** `limit` (1-1000, default 100), `offset` (>=0, default 0)
**Response:** A pagination object containing `{total, limit, offset, items}`. `items` includes `{seq, event_id, topic, producer, published_at, delivery_failure_count, dlq_requeue_count, dlq_at}`.

---

## POST /dlq/{event_id}/requeue

Moves a DLQ event back to normal delivery. Increases `dlq_requeue_count` (`delivery_failure_count` is not reset). If `delivery_failure_count >= max_retry`, the event will be moved to the DLQ again during the next DLQ loop.

**Path Parameters:** `event_id` (required)
**Response:** On success, returns `{event_id, requeued: true}`. A 409 error indicates the event has not been moved to the DLQ, and a 404 error indicates it was not found.

## Related Documents

- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_04_dlq-background-loop.md`
