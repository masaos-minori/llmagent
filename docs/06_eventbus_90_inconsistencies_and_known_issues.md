---
title: "Event Bus: Known Inconsistencies and Issues"
category: eventbus
tags:
  - event-bus
  - known-issues
  - inconsistencies
  - spec-conflicts
  - deferred-items
  - ack-offset
  - monotonicity
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_02_04_dlq-background-loop.md
  - 06_eventbus_04_dlq_offsets_and_delivery_semantics.md
source:
  - index.md
---

# Event Bus: Known Inconsistencies and Issues

## 対応が必要な項目

### EVENTBUS-001: Ack オフセットの単調性欠如 (High/open)

write_offset() に `max(current, new)` チェックなし。再接続時に重複受信の可能性あり。サーバー側修正予定なし。

## ドキュメント対応のみ

### EVENTBUS-002: /replay?format=json ページネーション形式 (Low/open)

`{total, limit, offset, items}` を返す。ドキュメントに明記必要。

### EVENTBUS-003: DLQ promotion の2経路 (Medium/open)

/nack インライン + バックグラウンドスweep。両経路をドキュメントに明記。

### EVENTBUS-004: promote_to_dlq() デッドコード (Low/open)

`sweep_orphans()` / `promote_single()` のみ正規経路。

## 保留中

Agent 統合は意図的に未実装。

### EVENTBUS-005: Agent publish / EVENTBUS-006: Agent SSE / EVENTBUS-007: Agent トピック

すべて Low/deferred。今後追加予定。

## スキーマと実装の差異

`acked_at`(冪等), `delivery_failure_count`(nack時増加), `dlq_requeue_count`(requeue時増加), `dlq_at`(DLQ昇格時) — いずれも使用中。

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_04_dlq-background-loop.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
