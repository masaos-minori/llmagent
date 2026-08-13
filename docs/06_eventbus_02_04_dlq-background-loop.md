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

起動時、DLQスイープのバックグラウンドループはasyncioタスクとして動作し、60秒ごとにポーリングする。`delivery_failure_count >= max_retry AND dlq_at IS NULL` のイベントを検索し、インライン処理で見逃したイベントを捕捉する安全網として機能する。

楽観的ロックにより `dlq_at IS NULL` のみを対象とし、二重昇格を防ぐ。孤立イベントが見つかった場合はログに記録される。0件でない場合はインライン昇格処理に問題がある可能性がある。

昇格処理はインライン処理と同じ（JSONファイルの原子書き込み + SQLite の `dlq_at` 設定）。

## Related Documents

- `06_eventbus_02_03_nack-health-dlq.md`
- `06_eventbus_05_06_dlq-operations.md`
