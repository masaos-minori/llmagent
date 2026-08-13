---
title: "Event Bus: Reference API — Route Handlers"
category: eventbus
tags:
  - event-bus
  - api-reference
  - route-handlers
  - publish-route
  - ack-route
  - dlq-route
  - replay-route
  - subscribe-route
  - health-route
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_06_01_reference-api-core-modules.md
  - 06_eventbus_06_03_reference-api-broker-and-offsets.md
source:
  - 06_eventbus_06_01_reference-api-core-modules.md
---

# Event Bus: Reference API — Route Handlers

## scripts/eventbus/publish_route.py

`publish(request)`: POST /publish。JSON Schema 検証 → DB 挿入 → JSONL 追記 → Broker 通知。JSONL 追記失敗は HTTP エラーとして表面化しない（警告ログ + 200）。

## scripts/eventbus/ack_route.py

`ack_event(request, event_id, consumer_id)`: POST /events/{event_id}/ack。`nack(request, event_id)`: POST /nack。失敗回数増加、`>= max_retry` で DLQ 昇格。

## scripts/eventbus/dlq_route.py

`dlq_list(request, limit=100, offset=0)`: GET /dlq。`dlq_requeue(request, event_id)`: POST /dlq/{event_id}/requeue。failure_count >= max_retry の場合、再DLQ化の可能性あり。

## scripts/eventbus/replay_route.py

`replay(request, since_seq=0, fmt=sse, limit=100, offset=0)`: GET /replay。SSEストリームまたはページネーションJSON。

## scripts/eventbus/subscribe_route.py

`subscribe(request, topic=[], since_seq=0, consumer_id="")`: GET /subscribe。SSEストリーミング + replay+push。

## scripts/eventbus/health_route.py

`health_check(request)`: GET /health。

## EventBroker クラス

`scripts/eventbus/broker.py` に存在。メソッド: subscribe, unsubscribe, publish, shutdown, subscriber_count, max_queue_depth, slow_consumer_count。

## _Subscriber データクラス

`scripts/eventbus/broker.py` に存在。サブスクライバー情報を保持する内部データ構造。

## offsets.py 関数

`scripts/eventbus/offsets.py` に存在。関数: read_offset, write_offset。

## HTTP エンドポイント

`/publish`(POST), `/replay`(GET), `/subscribe`(GET), `/health`(GET), `/dlq`(GET), `/dlq/{id}/requeue`(POST), `/events/{id}/ack`(POST), `/nack`(POST)。

## Related Documents

- `06_eventbus_06_01_reference-api-core-modules.md`
- `06_eventbus_06_03_reference-api-broker-and-offsets.md`
