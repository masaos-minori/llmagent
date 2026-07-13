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

イベントを nack（否定応答）する。`delivery_failure_count` を増加させる。`delivery_failure_count >= max_retry` の場合、そのイベントは DLQ に移行する。

**クエリパラメータ:**
- `event_id` (str、必須): nack するイベント ID

**レスポンス 200:** `{"event_id": "...", "delivery_failure_count": <int>}` — この nack でイベントが DLQ に移行した場合は `"dlq_promoted": true` が含まれることがある
**レスポンス 404:** イベントが見つからない。

**実装の詳細（Explicit in code）**: DLQ 昇格は `dlq.py` の `promote_single()` によってインラインで実行される（同モジュールの `promote_to_dlq()` はどこからも呼び出されておらず、現状デッドコードである）。`promote_single()` は先に DLQ 用 JSON ファイルをアトミックに書き込み（一時ファイル→`os.replace`）、その後に SQLite の `dlq_at` を更新する順序で実行される。これにより、ファイル書き込みが失敗した場合は DB 側も更新されず、イベントは「配信中」のまま残る（矛盾状態を防ぐ設計）。

---

## GET /health

各コンポーネントのヘルス状態を返す。`ok` の場合は HTTP 200、`degraded`/`unhealthy` の場合は HTTP 503。

```json
{"status": "ok|degraded", "db": "ok|unavailable", "dlq_task": "running|stopped", "active_subscribers": 0, "max_queue_depth": 0, "slow_consumers": 0, "degraded_reasons": []}
```

`status` はすべてのコンポーネントが健全な場合にのみ `"ok"` となる。ブローカーのメトリクスである `active_subscribers`、`max_queue_depth`、`slow_consumers` は、プロセス内の EventBroker の状態を反映する。`degraded_reasons` には具体的な障害要因が列挙される（例: `db_unavailable`、`dlq_task_stopped`、`broker_queue_backlog_high`、`slow_consumers_detected`）。

**実装の詳細（Explicit in code）**: `broker_queue_backlog_high` は `max_queue_depth >= 500` で判定される。`slow_consumers_detected` は、いずれかのコンシューマのキュー滞留数（`qsize()`）が `_SLOW_CONSUMER_THRESHOLD = 100` 以上のコンシューマが1件でも存在する場合に発生する。両閾値ともコード内定数であり、設定ファイルからの変更はできない。コンシューマキューの上限は `maxsize=1000`（`broker.py`）— これを超えるとイベントは配信されずに破棄される（詳細は `06_eventbus_02_02_subscribe-ack.md` を参照）。

---

## GET /dlq

デッドレターキュー内のイベント一覧を取得する（`dlq_at IS NOT NULL` のイベント）。

**クエリパラメータ:**
- `limit` (int、デフォルト: 100、最小: 1、最大: 1000): 返す件数の最大値
- `offset` (int、デフォルト: 0、最小: 0): ページネーションのためにスキップする件数

**レスポンス:** 以下のフィールドを持つページネーションオブジェクト:
- `total` (int): DLQ イベントの総数
- `limit` (int): リクエストされた limit
- `offset` (int): リクエストされた offset
- `items` ([{seq, event_id, topic, producer, published_at, delivery_failure_count, dlq_requeue_count, dlq_at}]): このページの DLQ イベント一覧

- `delivery_failure_count`: 直前の ack 成功以降の nack 回数
- `dlq_requeue_count`: このイベントが requeue された回数（requeue してもリセットされない）

---

## POST /dlq/{event_id}/requeue

イベントを DLQ から取り出し、通常の配信に戻す。`dlq_requeue_count` を 1 増加させる（`delivery_failure_count` はリセットされ**ない**）。再移行ロジック実行後に `delivery_failure_count >= max_retry` であれば、次回の DLQ ループティックでそのイベントは再び DLQ に入る。

**パスパラメータ:**
- `event_id` (str、必須): requeue するイベント ID

**レスポンス 200:** `{"event_id": "...", "requeued": true}` — requeue 後に `delivery_failure_count >= max_retry` であれば `"dlq_imminent": true` が含まれることがある
**レスポンス 409 Conflict:** イベントは存在するが DLQ には入っていない（dlq_at IS NULL）。
**レスポンス 404:** イベントが見つからない。

**エッジケース:**
- イベントが DLQ に入っていない場合（dlq_at IS NULL）: 409 Conflict を返す
- 同一イベントを繰り返し requeue した場合: dlq_requeue_count はそのたびに増加する
- delivery_failure_count が max_retry 以上のイベント: requeue 自体は成功するが、次回の DLQ ループティックで再度 DLQ に移行する

## Related Documents

- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_04_dlq-background-loop.md`

## Keywords

event-bus
http-api
nack
health
dlq
dead-letter-queue
requeue
error-handling
