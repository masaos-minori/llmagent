---
title: "Event Bus: Health Endpoint Semantics"
category: eventbus
tags:
  - event-bus
  - health-check
  - http-status-codes
  - monitoring
  - degraded
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_01_config-env-and-fields.md
  - 06_eventbus_05_05_delivery-operations.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: Health Endpoint Semantics

## ヘルスエンドポイント

HTTP 200 = `ok`、それ以外 = HTTP 503 + `status: "degraded"` + コンポーネント詳細。`unhealthy` は存在しない。

**503 はプロセスダウンではなくデグレード状態を示す。**

**監視は HTTP ステータスコードで判定すること。** デグレード時は `reasons` を確認（DB接続不可、DLQタスク停止、キューバックログ、遅延コンシューマーなど）。

## Related Documents

- `06_eventbus_05_01_config-env-and-fields.md`
- `06_eventbus_05_05_delivery-operations.md`
