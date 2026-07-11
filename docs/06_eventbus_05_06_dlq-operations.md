---
title: "Event Bus: DLQ Operations"
category: eventbus
tags:
  - event-bus
  - dlq
  - dead-letter-queue
  - requeue
  - background-loop
  - sweep
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_03_nack-health-dlq.md
  - 06_eventbus_02_04_dlq-background-loop.md
  - 06_eventbus_05_05_delivery-operations.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: DLQ Operations

## DLQ オペレーション

### DLQ ファイル作成タイミング

DLQ ファイルは、インラインプロモーション時（`/nack` 呼び出し時）に
`{deadletter_dir}/{event_id}.json` として即座に作成される。バックグラウンド DLQ
ループ（60 秒間隔）は、リトライしきい値に達したがインラインでプロモートされな
かったイベント（例: 競合状態が原因）を捕捉するためのセーフティスイープである。

### バックグラウンド DLQ ループの役割

バックグラウンド DLQ ループは 60 秒ごとに実行され、`delivery_failure_count >=
max_retry AND dlq_at IS NULL` を満たすイベントを検索する。楽観的ロックを使用し
ており、`dlq_at` がまだ NULL であるイベントのみを対象とすることで二重プロモー
ションを防いでいる。スイープで孤立イベントが見つかった場合、
`"dlq_loop: swept %d orphan(s) missed by inline promotion"` というログが出力
される。スイープ件数が 0 でない場合は、インラインプロモーションに問題がある
可能性がある。

### DLQ 再投入（requeue）の動作

`POST /dlq/{event_id}/requeue` による DLQ イベントの再投入は、`dlq_at` をクリ
アし、`dlq_requeue_count` を 1 増加させる。**重要**: `delivery_failure_count`
は再投入時にリセットされない。イベントの `delivery_failure_count >= max_retry`
である場合、次回のバックグラウンドループのティック（60 秒以内）で即座に DLQ
に再プロモートされる。再投入は `delivery_failure_count < max_retry` である
イベントに対してのみ有効に機能する。

### スイープ結果の監視

孤立 DLQ プロモーションはアプリケーションログに
`"dlq_loop: swept %d orphan(s) missed by inline promotion"` として記録される。
スイープ件数が 0 でない場合はログを確認すること — インラインプロモーションに
問題がある可能性があり、調査が必要である。ヘルスエンドポイントは
`dlq_sweep_count` フィールドを公開していないため、監視にはログ分析が必要で
ある。

## Related Documents

- `06_eventbus_02_03_nack-health-dlq.md`
- `06_eventbus_02_04_dlq-background-loop.md`
- `06_eventbus_05_05_delivery-operations.md`

## Keywords

event-bus
dlq
dead-letter-queue
requeue
background-loop
sweep
