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

イベントを nack（否定応答）する。`delivery_failure_count` を増加させ、`>= max_retry` で DLQ に移行する。

**クエリパラメータ**: `event_id`(必須)
**レスポンス**: 成功時は `{event_id, delivery_failure_count}`。404 はイベント未発見。

---

## GET /health

各コンポーネントのヘルス状態を返す。`ok` は HTTP 200、`degraded`/`unhealthy` は HTTP 503。

**レスポンスフィールド**: `status`、`db`、`dlq_task`、`active_subscribers`、`max_queue_depth`、`slow_consumers`、`degraded_reasons`。

`status` は全コンポーネントが健全な場合にのみ `"ok"`。`degraded_reasons` には障害要因（`db_unavailable`、`dlq_task_stopped`、`broker_queue_backlog_high`、`slow_consumers_detected`）が列挙される。

---

## GET /dlq

DLQ イベント一覧を取得する（`dlq_at IS NOT NULL` のイベント）。

**クエリパラメータ**: `limit`(1-1000, デフォルト100), `offset`(>=0, デフォルト0)
**レスポンス**: `{total, limit, offset, items}` のページネーションオブジェクト。`items` は `{seq, event_id, topic, producer, published_at, delivery_failure_count, dlq_requeue_count, dlq_at}` を含む。

---

## POST /dlq/{event_id}/requeue

DLQ イベントを通常の配信に戻す。`dlq_requeue_count` を増加させる（`delivery_failure_count` はリセットされない）。`delivery_failure_count >= max_retry` の場合、次回の DLQ ループで再び DLQ に移行する。

**パスパラメータ**: `event_id`(必須)
**レスポンス**: 成功時は `{event_id, requeued: true}`。409 は DLQ 未移行、404 は未発見。

## Related Documents

- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_04_dlq-background-loop.md`
