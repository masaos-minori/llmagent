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

昇格処理の内容はインライン処理と同じである。JSONLファイルをアトミックに書き込み、SQLite内で `dlq_at` を設定する。

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
