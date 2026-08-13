---
title: "Event Bus: Delivery Operations"
category: eventbus
tags:
  - event-bus
  - delivery
  - verification
  - slow-consumer
  - reconnect-recovery
  - subscriber-count
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_03_health-endpoint-semantics.md
  - 06_eventbus_05_04_consumer-id-stability.md
  - 06_eventbus_05_06_dlq-operations.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: Delivery Operations

## 配信オペレーション

### 配信の確認

`GET /subscribe?consumer_id=test` でライブプッシュを確認。publish後に1ループティック以内に受信される。

### 低速な consumer の監視

プロセス内キューが100イベント以上を低速と判定。ヘルスエンドポイントで確認。

- `slow_consumers > 0` → degraded
- `max_queue_depth >= 500` → broker_queue_backlog_high

低速の場合、キューからイベントが破棄される。consumerは再接続してSQLiteからリプレイが必要。

### 再接続時の復旧

consumer_id を指定して再接続すると最後にackされたオフセットから再開。一度もackしていない場合はseq=0から開始。`since_seq=N` で特定位置から開始可能。

### サブスクライバ数

0の場合、ブローカーはアイドル。イベントはSQLiteに残り、次回接続時にリプレイ可能。

## Related Documents

- `06_eventbus_05_03_health-endpoint-semantics.md`
- `06_eventbus_05_04_consumer-id-stability.md`
- `06_eventbus_05_06_dlq-operations.md`
