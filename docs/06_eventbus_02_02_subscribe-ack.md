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

**フェーズ 1 — リプレイ**: 接続時に、トピックフィルタに一致する `seq > start_seq` のすべてのイベントを SQLite に問い合わせる。各イベントは即座に `data:` SSE 行として出力される。

**フェーズ 2 — ライブ push**: リプレイが完了すると、接続はプロセス内の `EventBroker` を subscribe する。`POST /publish` で publish された新しいイベントは、1 イベントループティック以内に SSE ストリームへ push される — ポーリングによる遅延はない。

**再接続時のセマンティクス**: `consumer_id` を指定すると、最後に ack されたオフセットから再開する。ハンドラは保存済みオフセットを `start_seq` として読み込み、切断中に取り損なったイベントが再接続時に自動的に replay されるようにする。

**競合のない遷移**: ブローカーへの subscribe 登録は、リプレイのクエリよりも*先に*行われる。リプレイフェーズ中に publish されたイベントはキューに保持され、ライブフェーズ開始時に `replay_ceil`（リプレイの最終 seq）と重複排除される — イベントの欠落や重複は発生しない。

**クエリパラメータ:**
- `topic` (list[str]、デフォルトは全件): トピックによる絞り込み
- `since_seq` (int、デフォルト 0): 開始シーケンス。`consumer_id` が指定され `since_seq == 0` の場合は保存済みオフセットで上書きされる
- `consumer_id` (str、任意): オフセット永続化のためのコンシューマ識別子

オフセットは ack（`POST /events/{event_id}/ack` を参照）を通じてのみ前進する。切断時にはオフセットは書き込まれない — コンシューマがイベントを ack せずに切断した場合、そのイベントは再接続時に再度 replay される。

---

## POST /events/{event_id}/ack [canonical]

イベントを ack する。`consumer_id` が指定されている場合、コンシューマオフセットをそのイベントの `seq` に更新する。冪等性あり — 重複した ack は `already_acked: true` を伴う 200 を返す。イベントが存在しない場合のみ 404 を返す。

**パスパラメータ:**
- `event_id` (str、必須): ack するイベント ID

**クエリパラメータ:**
- `consumer_id` (str、任意): コンシューマ識別子。指定されており、かつイベントが新規に ack された場合、そのイベントの `seq` をコンシューマオフセットとして書き込む

**レスポンス 200（新規 ack）:** `{"event_id": "...", "acked": true, "seq": <int>}` — `seq` はイベントのシーケンス番号（consumer_id が指定されなかった場合は None）
**レスポンス 200（既に ack 済み）:** `{"event_id": "...", "acked": true, "already_acked": true}` — `seq` フィールドはなし
**レスポンス 404:** イベントが見つからない。

**オフセットの挙動**: オフセットは、`consumer_id` が指定されており、かつそのイベントが新規に ack された場合（以前に ack されていない場合）にのみ更新される。イベントが既に ack されていた場合、consumer_id の有無に関わらず `already_acked: true` を伴う 200 が返る。

**単調性に関する注記**: オフセットの前進は単調性が保証されて**いない**。より小さい `seq` を持つ古いイベントを ack すると、コンシューマオフセットはその `seq` まで後退する。コンシューマ側でイベントを順序どおりに ack するか、再接続時にオフセットの巻き戻りを処理するようにすること。

---

**注記 (2026-07-10):** `POST /ack`（クエリパラメータ方式の互換エイリアス）は削除された。`POST /events/{event_id}/ack` のみを使用すること。

## Related Documents

- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_03_nack-health-dlq.md`

## Keywords

event-bus
http-api
subscribe
ack
nack
sse
streaming
consumer-offset
idempotent
