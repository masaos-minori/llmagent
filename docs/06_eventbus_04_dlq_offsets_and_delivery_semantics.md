---
title: "Event Bus: DLQ, Offsets, and Delivery Semantics"
category: eventbus
tags:
  - event-bus
  - dlq
  - dead-letter-queue
  - consumer-offset
  - delivery-semantics
  - at-least-once
  - idempotent
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_03_nack-health-dlq.md
  - 06_eventbus_02_04_dlq-background-loop.md
  - 06_eventbus_03_persistence_schema_and_replay.md
source:
  - index.md
---

# Event Bus: DLQ, Offsets, and Delivery Semantics

## デッドレターキュー（DLQ）

### 昇格経路

nack時に `delivery_failure_count` が `>= max_retry` になると即座にDLQへ昇格する。バックグラウンドDLQループ（60秒ごと）はインラインで見逃したイベントを安全網として捕捉する。

### 昇格処理

1. `{deadletter_dir}/{event_id}.json` にJSONファイルを原子書き込み
2. SQLite の `dlq_at` を設定

### Requeue

`POST /dlq/{event_id}/requeue` は `dlq_at` をクリアし `dlq_requeue_count` を増加させる（`delivery_failure_count` はリセットしない）。`delivery_failure_count >= max_retry` の場合、次回のDLQループで再昇格する。

## コンシューマーオフセット

オフセットファイルは `{offsets_dir}/{sanitized_consumer_id}` に保存される。`consumer_id` はサニタイズ済み。

### Ack専用オフセット

コンシューマーが `POST /events/{event_id}/ack?consumer_id={consumer_id}` で明示的にackした場合のみ進む。ストリーミング中は自動進行しない。冪等な二重ackではオフセット更新は行わない。

**注記**: オフセットはack時の `seq` 値のみを進める。ack順序が `seq` 順でない場合、オフセットは非単調になる可能性がある（スキップされた `seq` は後で再取得されない）。

### 再接続時の再開

`consumer_id` を指定することで最後にackされたオフセットから再開できる。コンシューマーIDは再起動をまたいで安定している必要がある。

**注記**: `offset_checkpoint_interval` は削除済み。設定すると起動に失敗する。

## 配送保証

At-least-once。重複publishは `event_id` UNIQUE制約により抑制される。クラッシュ後の再配送は発生し得る。トピック単位で順序保持。

**重要**: コンシューマーはidempotentな処理を実装しなければならない。同一イベントの複数回配信が発生し得るため、同じ `event_id` に対する重複ackや重複処理は安全でなければならない。

## consumer_id衝突リスク

異なるクライアントが同じ `consumer_id` を使用する場合、最後の書き込みが優先され、オフセットが上書きされる。これは設計上の意図だが、衝突によるオフセット不整合を引き起こす可能性がある。

## 信頼性の限界

- DBファイル喪失で全イベント喪失
- JSONL追記失敗でSQLiteと乖離
- DLQループ間隔（60秒）内にDLQ昇格イベントが見え続ける

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_03_nack-health-dlq.md`
- `06_eventbus_02_04_dlq-background-loop.md`
- `06_eventbus_03_persistence_schema_and_replay.md`
