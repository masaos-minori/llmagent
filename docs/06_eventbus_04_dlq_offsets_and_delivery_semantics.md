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

### 主な昇格経路: nack時のインライン処理

コンシューマーが `POST /nack?event_id=...` を呼び出すと、サーバーは `delivery_failure_count` をインクリメントする。新しい値が `max_retry` に達した場合、そのイベントはnackレスポンスの一部として**即座に**DLQへ昇格する。この場合、レスポンスには `"dlq_promoted": true` が含まれる。

### セーフティスイープ: バックグラウンドDLQループ

バックグラウンドDLQループは60秒ごとに実行され、`delivery_failure_count >= max_retry AND dlq_at IS NULL` を満たすイベントを検索する。これにより、再試行の閾値に達したものの（例えばnackとループ間の競合状態により）インライン処理では昇格されなかったイベントを捕捉する。

このループは楽観的ロックを使用する。`dlq_at` がまだNULLのイベントのみをカウント対象とすることで、両経路が競合した際の二重昇格を防止する。スイープで孤立イベントが見つかった場合、`"dlq_loop: swept %d orphan(s) missed by inline promotion"` というログが出力される。スイープ結果が0件でない場合、インライン昇格処理に問題がある可能性を示す。

### 昇格処理（両経路共通）

1. `{deadletter_dir}/{event_id}.json` にJSONファイルをアトミックに書き込む（tempfile + `os.replace`）
2. SQLiteのeventsテーブルの行に `dlq_at` を設定する

一貫性のため、インライン処理とバックグラウンド処理は同じアトミック書き込み機構を使用する。

### Requeue

`POST /dlq/{event_id}/requeue` は `dlq_at` をクリアし、`dlq_requeue_count` を1インクリメントする（`delivery_failure_count` は**リセットしない**）。

**重要**: イベントの `delivery_failure_count` が既に `max_retry` 以上の場合、requeueすると次のDLQループのtick（60秒以内）で即座に再昇格する。requeueは閾値に達したイベントに対する「セカンドチャンス」ではない — `delivery_failure_count < max_retry` のイベントに対してのみ機能する。

## コンシューマーオフセット

オフセットファイルは `{offsets_dir}/{sanitized_consumer_id}` に保存される（プレーンテキストで、1ファイルに1つの整数）。`consumer_id` は、パストラバーサル攻撃を防ぐために `..`、`.`、`/` を（この順序で）`_` に置換してサニタイズされる。置換は文字列全体の全出現箇所に適用される。結果が空文字列になった場合は `"default"` が使用される。注意: バックスラッシュ文字はサニタイズされず、そのまま通過する。

### オフセットの復元

`/subscribe` において、`consumer_id` が設定されており `since_seq == 0` の場合、保存済みオフセットが読み取られ開始シーケンスとして使用される。

### Ack専用のオフセットモデル

コンシューマーオフセットは、コンシューマーが `POST /events/{event_id}/ack?consumer_id={consumer_id}` により明示的にイベントをackした場合にのみ進む。ストリーミング中にオフセットが自動的に進むことはない。

`consumer_id` が指定されていても、対象イベントが既にack済みの場合（冪等な二重ack）はオフセットファイルへの書き込みは行われない — オフセット更新は「新規にackされた」場合のみ発生する（根拠分類: Explicit in code — `scripts/eventbus/ack_route.py` の `_do_ack()`）。

**再接続時の再開**

再接続時には、（`since_seq` を指定せずに）`consumer_id` を指定することで、最後にackされたオフセットから再開できる。subscribeハンドラーは接続時に `read_offset(offsets_dir, consumer_id)` を呼び出し、保存されたseqをSQLiteのreplayクエリの `start_seq` として使用する。

再接続フローの例:
1. コンシューマーが接続: `GET /subscribe?consumer_id=svc-A`
2. seq=1..10のイベントを受信し、seq=10をack: `POST /events/{id}/ack?consumer_id=svc-A`
3. 切断
4. 再接続: `GET /subscribe?consumer_id=svc-A` → replayはseq=11から開始

**コンシューマーIDの安定性要件**: オフセットの再開を機能させるには、コンシューマーIDが再起動をまたいで安定している必要がある。プロセスの生存期間中のみ安定なID（例: PIDベース）は再起動を生き延びない — オフセットは再開されない。推奨: アプリケーションレベルの識別子（例: サービス名+インスタンスID）をconsumer_idとして使用すること。

**注記（2026-07-10）**: `offset_checkpoint_interval` は削除された（no-opフィールドであり、オフセットのチェックポイント処理はack専用モデルに置き換えられた）。このキーを `eventbus.toml` に設定すると、現在はEvent Busが起動時に失敗する — 設定ファイルから削除すること。

## 配送保証

| 特性 | 値 |
|---|---|
| 配送保証レベル | At-least-once |
| publish時の重複抑制 | あり — SQLiteの `event_id` UNIQUE制約により、重複publishは黙って無視される |
| コンシューマー側での重複配送 | 発生し得る — クラッシュ前にackが書き込まれていなかった場合、クラッシュ後にコンシューマーが同じイベントを再受信する可能性がある |
| 順序保証 | トピック単位の順序は保持される（seq昇順）。トピック間の順序は保証されない |

## 信頼性の限界

- SQLiteが唯一の永続ストアである。DBファイルが失われると全イベントが失われる
- JSONLアーカイブは補助的なものであり、追記に失敗するとSQLiteと内容が乖離する可能性がある
- DLQループは60秒ごとに実行される。`delivery_failure_count >= max_retry` のイベントが有効なイベントとして見え続けるウィンドウが存在する

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_03_nack-health-dlq.md`
- `06_eventbus_02_04_dlq-background-loop.md`
- `06_eventbus_03_persistence_schema_and_replay.md`

## Keywords

event-bus
dlq
dead-letter-queue
consumer-offset
delivery-semantics
at-least-once
idempotent
