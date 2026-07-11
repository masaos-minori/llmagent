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

## ヘルスエンドポイントの意味論

| HTTP ステータス | ステータス値 | 意味 |
|---|---|---|
| 200 | `ok` | すべてのシステムが正常 |
| 503 | `degraded` | 接続されているが degraded 状態（DB が利用不可、DLQ タスクが停止、ブローカーのキュー滞留が多い、consumer の処理が遅い、など） |

`unhealthy` というステータス値は存在しない — ヘルスエンドポイントは ok 以外の
すべての状態に対して HTTP 503 を返す。JSON ボディには `status: "degraded"` と
コンポーネント単位の詳細（例: `"db": "unavailable"`）が含まれる。

**監視ツールはアラート判定に JSON ボディではなく HTTP ステータスコードを使用しなければならない。**

## Related Documents

- `06_eventbus_05_01_config-env-and-fields.md`
- `06_eventbus_05_05_delivery-operations.md`

## Keywords

event-bus
health-check
http-status-codes
monitoring
degraded
