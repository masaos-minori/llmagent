---
title: "Event Bus: Configuration Fields and Environment Variables"
category: eventbus
tags:
  - event-bus
  - configuration
  - environment-variables
  - config-fields
  - toml
  - deprecated-fields
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_bind-address-and-start.md
  - 06_eventbus_05_health-endpoint-semantics.md
source:
  - 06_eventbus_05_configuration_deploy_and_operations.md
---

# Event Bus: Configuration Fields and Environment Variables

## Configuration

Event Bus configuration is loaded from a TOML file (default: `/opt/llm/config/eventbus.toml`).

### Environment variable overrides

| Variable | Default | Purpose |
|---|---|---|
| `EVENTBUS_CONFIG_PATH` | `/opt/llm/config/eventbus.toml` | TOML config file path |
| `EVENTBUS_SCHEMA_PATH` | `/opt/llm/schemas/event_envelope.json` | JSON Schema for event envelopes |

### Config fields

#### Active config fields

| Field | Type | Default | Description |
|---|---|---|---|
| `port` | int | — | HTTP listen port |
| `db_path` | str | — | SQLite database file path |
| `storage_dir` | str | — | JSONL event archive directory |
| `offsets_dir` | str | — | Consumer offset file directory |
| `deadletter_dir` | str | — | Dead-letter queue JSONL directory |
| `max_retry` | int | — | Retry threshold before DLQ promotion |
| `host` | str | `127.0.0.1` | HTTP listen address (see Bind Address section below) |
| `allow_public_bind` | bool | `false` | Override: allow binding to public/wildcard addresses (security risk, no authentication) |

#### Deprecated config fields

> **Deprecated**: The following fields are no-op compatibility fields. Setting them to non-default values emits a `DeprecationWarning`. These fields will be removed in a future version.
>
> **Do not include these fields in TOML configuration.** They have no effect and will be removed. If you need to suppress the warning, set them to their default values (500, 10) or remove them entirely.

| Field | Type | Default | Description |
|---|---|---|---|
| `poll_interval_ms` | int | 500 | No-op. Subscribe polling was replaced with push-mode delivery via EventBroker. Non-default values emit DeprecationWarning; values <1 raise ValueError. |
| `offset_checkpoint_interval` | int | 10 | No-op. Offset checkpointing was replaced with ack-only model. Non-default values emit DeprecationWarning; values <1 raise ValueError. |

## Related Documents

- `06_eventbus_05_bind-address-and-start.md`
- `06_eventbus_05_health-endpoint-semantics.md`

## Keywords

event-bus
configuration
environment-variables
config-fields
toml
deprecated-fields
