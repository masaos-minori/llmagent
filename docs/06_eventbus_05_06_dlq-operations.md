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

### DLQ ファイル作成

インライン（`/nack` 時）またはバックグラウンドループ（60秒ごと）で `{deadletter_dir}/{event_id}.json` を作成。バックグラウンドは安全網。

### requeue

`POST /dlq/{event_id}/requeue` は `dlq_at` をクリアし `dlq_requeue_count` を増加。`delivery_failure_count` はリセットしない。`>= max_retry` の場合、次回のループで再昇格。

### 監視

スイープ結果はログに記録されるが、ヘルスエンドポイントでは公開されていない。

## Related Documents

- `06_eventbus_02_03_nack-health-dlq.md`
- `06_eventbus_02_04_dlq-background-loop.md`
- `06_eventbus_05_05_delivery-operations.md`
