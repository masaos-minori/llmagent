---
title: "Event Bus: Subscribe and Ack Endpoints"
category: eventbus
tags:
  - event-bus
  - http-api
  - subscribe
  - ack
  - nack
  - sse
  - streaming
  - consumer-offset
  - idempotent
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_01_publish-replay.md
  - 06_eventbus_02_03_nack-health-dlq.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: Subscribe and Ack Endpoints

## GET /subscribe

replay と push を組み合わせたハイブリッドモデルで、呼び出し元にイベントをストリーミングする。

**フェーズ 1 — リプレイ**: 接続時にトピックフィルタに一致する `seq > start_seq` のすべてのイベントを SQLite から取得し、`data:` SSE 行として出力する。

**フェーズ 2 — ライブ push**: リプレイ完了後、プロセス内の `EventBroker` を subscribe し、`POST /publish` で publish された新しいイベントを SSE ストリームへリアルタイム配信する。

**キュー溢れ**: コンシューマの処理が遅くキューが満杯の場合、そのイベントは破棄される（WARNING ログのみ）。再取得には `since_seq`/`GET /replay` を使用すること。

**再接続**: `consumer_id` を指定すると、最後に ack されたオフセットから再開する。切断時はオフセットは保存されないため、ack せずに切断したイベントは再接続時に再度配信される。

**クエリパラメータ**: `topic`(トピック絞り込み)、`since_seq`(>=0, デフォルト0), `consumer_id`(オフセット永続化用)。

---

## POST /events/{event_id}/ack [canonical]

イベントを ack する。`consumer_id` 指定時はコンシューマオフセットを更新する。冪等性あり。

**パスパラメータ**: `event_id`(必須)
**クエリパラメータ**: `consumer_id`(任意)

**レスポンス**: 成功時は `{event_id, acked: true, seq: <int>}`。既に ack 済みの場合は `{event_id, acked: true, already_acked: true}`。404 はイベント未発見。

**単調性に関する注記**: オフセットの前進は単調性が保証されていない。古いイベントを ack するとオフセットが後退する可能性がある。コンシューマ側で順序どおり ack か、再接続時に巻き戻りを処理すること。

---

## Related Documents

- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_03_nack-health-dlq.md`
