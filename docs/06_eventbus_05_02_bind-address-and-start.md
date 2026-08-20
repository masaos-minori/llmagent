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

## Bind Address

In production, you should bind to `127.0.0.1`. Binding to `0.0.0.0` poses a security risk as the API becomes publicly accessible without authentication.

### Address Classification

- Loopback (`127.0.0.1`, `::1`) / Private IP — Allowed
- Wildcard (`0.0.0.0`, `::`) — Raises `ValueError`
- Hostname — Treated as public

You can bypass validation using `allow_public_bind: true`, but this is not recommended.

## Start Command

```bash
EVENTBUS_CONFIG_PATH=/opt/llm/config/eventbus.toml python -m eventbus.app
```

Or `uvicorn eventbus.app:app --host 127.0.0.1 --port 8010`.

## Related Documents

- `06_eventbus_05_01_config-env-and-fields.md`
- `06_eventbus_05_07_validation-status.md`
