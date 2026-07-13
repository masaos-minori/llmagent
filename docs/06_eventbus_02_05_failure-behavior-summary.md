---
title: "Event Bus: Failure Behavior Summary"
category: eventbus
tags:
  - event-bus
  - error-handling
  - failure-behavior
  - http-status-codes
  - validation
  - json-schema
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_01_publish-replay.md
  - 06_eventbus_02_03_nack-health-dlq.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: Failure Behavior Summary

| 失敗要因 | 動作 |
|---|---|
| publish時のJSON Schema検証失敗 | 422、イベントは保存されない |
| SQLiteコミット後のJSONL追記失敗 | 200を返す、WARNINGをログ出力、イベントはSQLiteに存在 |
| `/health` でDBが利用不可 | `{"status": "degraded", "db": "unavailable", ...}` |
| `/health` でDLQタスクが停止中 | `{"status": "degraded", ..., "dlq_task": "stopped"}` |
| requeue時に未知の `event_id` | 404 |
| requeue時にイベントは存在するがDLQに無い | 409 Conflict |
| publish時に`event_id`が重複（冪等スキップ） | 200を返す（既存の`seq`）、SQLite再挿入なし、broker通知（新規subscribeへのpush）もスキップされる |
| subscribeコンシューマのキュー（maxsize=1000）が満杯 | イベントは黙って破棄、WARNINGをログ出力、HTTPエラーにはならない（`/health`の`slow_consumers`/`max_queue_depth`で兆候を検知可能） |

**根拠分類:** 上記2行は `Explicit in code`（`publish_route.py`・`broker.py` を参照）。

## Related Documents

- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_03_nack-health-dlq.md`

## Keywords

event-bus
error-handling
failure-behavior
http-status-codes
validation
json-schema
