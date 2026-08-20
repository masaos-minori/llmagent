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

A hybrid model combining replay and push, streaming events to the caller.

**Phase 1 — Replay**: Upon connection, all events matching the topic filter where `seq > start_seq` are retrieved from SQLite and output as `data:` SSE lines.

**Phase 2 — Live Push**: After replay completion, the process subscribes to the internal `EventBroker` and streams new events published via `POST /publish` to the SSE stream in real-time.

**Queue Overflow**: If the consumer is slow and the queue becomes full, the event is discarded (only a WARNING is logged). Use `since_seq`/`GET /replay` for recovery.

**Reconnection**: Specifying a `consumer_id` allows resuming from the last acknowledged offset. Offsets are not saved upon disconnection, so events that were not acknowledged before disconnecting will be re-delivered upon reconnection.

**Query Parameters:** `topic` (topic filtering), `since_seq` (>=0, default 0), `consumer_id` (for offset persistence).

---

## POST /events/{event_id}/ack [canonical]

Acknowledges an event. When a `consumer_id` is specified, the consumer offset is updated. Idempotent.

**Path Parameters:** `event_id` (required)
**Query Parameters:** `consumer_id` (optional)

**Response:** On success, returns `{event_id, acked: true, seq: <int>}`. If already acknowledged, returns `{event_id, acked: true, already_acked: true}`. A 404 error indicates the event was not found.

**Note on Monotonicity:** Offset advancement is not guaranteed to be monotonic. Acknowledging older events can cause the offset to regress. Consumers should acknowledge in order or handle regressions upon reconnection.

---

## ACK/NACK 状態遷移表

以下の表は、ACK と NACK の各操作に対する現在のコード挙動をまとめたものです。NACK 側の詳細（重複 NACK、NACK 後 ACK 等）は `docs/06_eventbus_02_03_nack-health-dlq.md` も参照してください。

| シナリオ | 現在のコード挙動 | HTTP ステータス | レスポンスボディ | 永続化への副作用 |
|---|---|---|---|---|
| 初回 ACK | `ack_event` が `(True, True)` を返す | 200 | `{event_id, acked: true, seq: <int>}` | `acked_at` を設定、`consumer_id` 指定時はオフセット書き込み |
| 重複 ACK | `ack_event` が `(True, False)` を返す | 200 | `{event_id, acked: true, already_acked: true}` | 追加書き込みなし、オフセット再書き込みなし |
| 初回 NACK | `nack_event` が `delivery_failure_count` を 0→1 に増加 | 200 | `{event_id, delivery_failure_count}` | `delivery_failure_count` 増加；`>= max_retry` で DLQ 昇格 |
| 重複 NACK | `nack_event` に冪等性ガードなし；呼び出し毎に `delivery_failure_count` 再増加 | 200 | `{event_id, delivery_failure_count}` | カウンタが増加し続け、後続の重複呼び出しで DLQ 昇格を誘発する可能性 — **実装修正必要** |
| NACK 後 ACK | `ack_event` の `WHERE acked_at IS NULL` は一致し続ける（NACK は `acked_at` を設定しない） | 200 | `{event_id, acked: true, seq: <int>}` | ACK 成功、`delivery_failure_count` は NACK 時の値のまま — 再調整なし |
| ACK 後 NACK | `nack_event` に `acked_at` チェックなし | 200 | `{event_id, delivery_failure_count}` | 既に ACK 済みでも NACK が「成功」し `delivery_failure_count` 増加 — **実装修正必要** |
| 不明なイベント ID (ACK) | `ack_event` が `(False, False)` を返す | 404 | `ERR_EVENT_NOT_FOUND` | なし |
| 不明なイベント ID (NACK) | `nack_event` が `-1` を返す | 404 | `ERR_EVENT_NOT_FOUND` | なし |
| 同時 ACK/NACK | 双方が `run_with_db_lock` を経由し DB 層で直列化 | 200/200 | ロック順序に依存 | 真の競合なし — ロックが全順序を強制し、2 番目の呼び出しは 1 番目のコミット済み状態を観測 |

### `since_seq`/オフセット優先順位ルール

`subscribe_route.py` の L32-34 における正確なロジックは以下の通りです：

```
start_seq = since_seq
if consumer_id and start_seq == 0:
    start_seq = read_offset(cfg.offsets_dir, consumer_id)
```

ルール: 明示的な `since_seq=0` と、省略された `since_seq`（`Query(default=0)` 宣言によりデフォルト 0）は、`consumer_id` 指定時には区別不能です。両者とも「保存済みオフセットから読み出す」に解決されます。`consumer_id` を渡しつつ完全なフルリプレイを行いたいクライアントは、現状その意図を表現できません。

### 不明/ミスマッチしたコンシューマの扱い

`schema.sql` にコンシューマ/イベント所有権カラムは存在しません。`consumer_id` は任意の文字列として受け入れられ、`write_offset`/`read_offset` のみに使用されます。`/subscribe` と `/events/{event_id}/ack` の両方が、イベント所有権レジストリとの検証なしに任意の文字列を受け入れます。実装指示 #1/#3 に従い、明示的に「未検知・未実施（設計上）」と文書化し、黙って省略しないこととします。

---

## Related Documents

- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_03_nack-health-dlq.md`
