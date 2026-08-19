---
title: "Event Bus: Reference API — Broker and Offsets"
category: eventbus
tags:
  - event-bus
  - api-reference
  - broker
  - offsets
  - eventbroker
  - subscriber
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_06_01_reference-api-core-modules.md
  - 06_eventbus_06_02_reference-api-route-handlers.md
source:
  - 06_eventbus_06_01_reference-api-core-modules.md
---

# Event Bus: Reference API — Broker and Offsets

## scripts/eventbus/broker.py

`_Subscriber`: キューとトピックリストを保持する内部データ構造。`EventBroker`: トピック対応ファンアウトインメモリpub/subブローカー。

メソッド: `subscribe(topics→_Subscriber)`, `unsubscribe(sub→None)`, `publish(event→int)`, `shutdown()`, `subscriber_count()→int`, `max_queue_depth()→int`, `slow_consumer_count()→int`。

## scripts/eventbus/offsets.py

`read_offset(offsets_dir, consumer_id)→int`: 保存オフセット読み込み（未発見時は0）。`write_offset(offsets_dir, consumer_id, seq)→None`: seq が現在のコミット済みオフセットより大きい場合のみファイル書き込み。seq <= current の場合は警告ログを出力してスキップ（単調性保証）。

## Related Documents

- `06_eventbus_06_01_reference-api-core-modules.md`
- `06_eventbus_06_02_reference-api-route-handlers.md`
