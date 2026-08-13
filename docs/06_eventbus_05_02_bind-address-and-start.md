---
title: "Event Bus: Bind Address and Start Command"
category: eventbus
tags:
  - event-bus
  - bind-address
  - startup
  - security
  - public-bind
  - loopback
  - wildcard
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_01_config-env-and-fields.md
  - 06_eventbus_05_07_validation-status.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: Bind Address and Start Command

## バインドアドレス

本番では `127.0.0.1` にバインドすべき。`0.0.0.0` は認証なしでAPIが公開されるためセキュリティリスク。

### アドレス分類

- ループバック (`127.0.0.1`, `::1`) / プライベートIP — 許可
- ワイルドカード (`0.0.0.0`, `::`) — `ValueError`
- ホスト名 — public扱い

`allow_public_bind: true` で検証を回避可能だが推奨されない。

### 起動コマンド

```bash
EVENTBUS_CONFIG_PATH=/opt/llm/config/eventbus.toml python -m eventbus.app
```

または `uvicorn eventbus.app:app --host 127.0.0.1 --port 8010`。

## Related Documents

- `06_eventbus_05_01_config-env-and-fields.md`
- `06_eventbus_05_07_validation-status.md`
