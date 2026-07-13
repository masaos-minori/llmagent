---
title: "Event Bus: DLQ Background Loop"
category: eventbus
tags:
  - event-bus
  - dlq
  - dead-letter-queue
  - background-loop
  - safety-sweep
  - optimistic-lock
  - orphan-promotion
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_03_nack-health-dlq.md
  - 06_eventbus_05_06_dlq-operations.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: DLQ Background Loop

起動時、DLQスイープのバックグラウンドループはasyncioタスクとして動作し、60秒ごとにポーリングする。`delivery_failure_count >= max_retry AND dlq_at IS NULL` を満たすイベントを検索する。これらは再試行の閾値に達したが、インライン処理では（例えば競合状態により）DLQに昇格されなかったイベントである。

このループは楽観的ロックを使用する。`dlq_at` がまだNULLのイベントのみをカウント対象とすることで、二重昇格を防止する。スイープで孤立イベントが見つかった場合、`"dlq_loop: swept %d orphan(s) missed by inline promotion"` というログが出力される。スイープ結果が0件でない場合、インライン昇格処理に問題がある可能性を示す。

昇格処理の内容はインライン処理と同じである。JSONファイルをアトミックに書き込み、SQLite内で `dlq_at` を設定する。

**実装の詳細（Explicit in code）**: `_dlq_loop` が呼び出す実体は `dlq.py` の `sweep_orphans()` であり、抽出条件の `SELECT` に加え、`UPDATE ... WHERE event_id = ? AND dlq_at IS NULL` として更新自体にも `dlq_at IS NULL` 条件を付け、`cur.rowcount` を見て実際に更新できた場合のみ昇格件数としてカウントする。この二段構えにより、`SELECT` から `UPDATE` までの間に別経路（nack のインライン昇格など）が先に `dlq_at` を設定していた場合でも二重昇格しない。同モジュールには条件の弱い `promote_to_dlq()` という関数も存在するが、これはアプリケーションのどこからも呼び出されていない（コード上デッドコード）。呼び出されているのは常に `sweep_orphans()` である。

## Related Documents

- `06_eventbus_02_03_nack-health-dlq.md`
- `06_eventbus_05_06_dlq-operations.md`

## Keywords

event-bus
dlq
dead-letter-queue
background-loop
safety-sweep
optimistic-lock
orphan-promotion
