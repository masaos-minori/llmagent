---
title: "Event Bus: Consumer ID Stability"
category: eventbus
tags:
  - event-bus
  - consumer-id
  - offset-resume
  - reconnect
  - stability
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_03_health-endpoint-semantics.md
  - 06_eventbus_05_05_delivery-operations.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: Consumer ID Stability

## Consumer ID の安定性

Consumer ID はクライアントが `consumer_id` パラメータで指定し、サーバー側では自動生成されない。再起動後も安定したIDを使用すること。PIDのような揮発性IDを使用してはならない。同一IDの複数consumerは最後の書き込みが優先され、サーバーは衝突を検出しない。

## Related Documents

- `06_eventbus_02_02_subscribe-ack.md` — subscribe/ack プロトコル詳細
- `06_eventbus_03_persistence_schema_and_replay.md` — オフセット永続化詳細
- `06_eventbus_05_03_health-endpoint-semantics.md`
- `06_eventbus_05_05_delivery-operations.md`
