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

Consumer ID は常にクライアントが `consumer_id` クエリパラメータで指定するものであり、
サーバ側で自動生成されることはない。

再起動後にオフセットの再開（resume）を機能させるには、consumer は再起動をまたいで
永続する安定した consumer_id を使用しなければならない。

2 つの consumer が同じ consumer_id を使用した場合、オフセットファイルに対しては
最後に書き込んだものが優先される（衝突検知は行われない）。

## Related Documents

- `06_eventbus_05_03_health-endpoint-semantics.md`
- `06_eventbus_05_05_delivery-operations.md`

## Keywords

event-bus
consumer-id
offset-resume
reconnect
stability
