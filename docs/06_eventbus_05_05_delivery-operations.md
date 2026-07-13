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

インメモリブローカーを有効化した後、ライブプッシュが機能していることを確認する。

```bash
# Terminal 1: subscribe (hold connection open)
curl -N "http://localhost:8015/subscribe?consumer_id=test-consumer"

# Terminal 2: publish
curl -X POST http://localhost:8015/publish \
  -H "Content-Type: application/json" \
  -d '{"event_id":"test-001","topic":"test","payload":{},"producer":"ops","published_at":"2026-06-25T12:00:00Z"}'
```

イベントは 1 イベントループティック以内（localhost では通常 1 ms 未満のレイテンシ）に
ターミナル 1 に表示されるはずである。

### 低速な consumer の監視

低速な consumer とは、プロセス内キューの深さが 100 イベント以上に達したものを指す。
ヘルスエンドポイント経由で確認する。

```bash
curl http://localhost:8015/health | jq '.slow_consumers, .max_queue_depth, .active_subscribers'
```

**しきい値:**
- `slow_consumers > 0` → `degraded_reasons` に `slow_consumers_detected` が含まれる
- `max_queue_depth >= 500` → `degraded_reasons` に `broker_queue_backlog_high` が含まれる

consumer が低速な場合、イベントはプロセス内キューから破棄される（WARNING として
ログ出力される）。consumer は再接続して SQLite から欠落したイベントをリプレイ
する必要がある。

### 再接続時の復旧

サブスクライバが切断された場合、イベントを欠落させることなく再開できる。

```bash
# Reconnect with consumer_id — replays from last acked offset automatically
curl -N "http://localhost:8015/subscribe?consumer_id=my-consumer"
```

consumer がこれまでに一度も ack していない場合、リプレイは seq=0（すべてのイベント）
から開始される。特定の位置から開始するには以下のようにする。

```bash
curl -N "http://localhost:8015/subscribe?consumer_id=my-consumer&since_seq=100"
```

### サブスクライバ数の確認

```bash
curl http://localhost:8015/health | jq '.active_subscribers'
```

サブスクライバが 0 である場合、ブローカーはアイドル状態である。イベントは
それでも SQLite に永続化されており、次回接続時にリプレイ可能である。

## Related Documents

- `06_eventbus_05_03_health-endpoint-semantics.md`
- `06_eventbus_05_04_consumer-id-stability.md`
- `06_eventbus_05_06_dlq-operations.md`

## Keywords

event-bus
delivery
verification
slow-consumer
reconnect-recovery
subscriber-count
