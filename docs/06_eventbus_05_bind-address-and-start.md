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
  - 06_eventbus_05_config-env-and-fields.md
  - 06_eventbus_05_validation-status.md
source:
  - 06_eventbus_05_configuration_deploy_and_operations.md
---

# Event Bus: Bind Address and Start Command

### Bind Address

The EventBus server should bind to `127.0.0.1` (loopback) in production, not
`0.0.0.0`. Binding to `0.0.0.0` exposes the EventBus API to the local network,
which is a security risk (no authentication layer on the EventBus HTTP endpoints).

#### Address classification

The startup guard validates the bind address at config load time:

| Category | Addresses | Allowed without override? |
|---|---|---|
| Loopback | `127.0.0.1`, `::1` | Yes |
| Private IP | `192.168.x.x`, `10.x.x.x`, `172.16.x.x–172.31.x.x` | Yes |
| Wildcard IPv4 | `0.0.0.0` | No — raises `ValueError` |
| Wildcard IPv6 | `::` | No — raises `ValueError` |
| Hostname (non-IP) | Any hostname (e.g., `example.com`) | No — treated as public; `ipaddress.ip_address()` raises ValueError for non-IP strings, which is caught and treated as public |

#### Public bind override

Setting `allow_public_bind: true` in the TOML config bypasses the validation. This is **not recommended** unless you have authentication via a reverse proxy or other mechanism. The error message when rejected is:

```
Event Bus bound to public address {host} without allow_public_bind=true.
The API has no authentication — this is a security risk.
```

If remote access is required, use a reverse proxy with authentication.

### Start command

```bash
EVENTBUS_CONFIG_PATH=/opt/llm/config/eventbus.toml python -m eventbus.app
```

The app starts uvicorn programmatically using the config's `host` and `port` values.
Alternatively: `uvicorn eventbus.app:app --host 127.0.0.1 --port 8010` (CLI overrides).

### TOML example

```toml
port = 8010
db_path = "/opt/llm/data/eventbus.sqlite"
storage_dir = "/opt/llm/data/eventbus-storage"
offsets_dir = "/opt/llm/data/eventbus-offsets"
deadletter_dir = "/opt/llm/data/eventbus-deadletter"
max_retry = 3
host = "127.0.0.1"
allow_public_bind = false
```

## Related Documents

- `06_eventbus_05_config-env-and-fields.md`
- `06_eventbus_05_validation-status.md`

## Keywords

event-bus
bind-address
startup
security
public-bind
loopback
wildcard
