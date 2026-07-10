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
  - 06_eventbus_05_config-env-and-fields.md
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

#### Removed config fields

> **Note (2026-07-10)**: `poll_interval_ms` and `offset_checkpoint_interval` have been removed (both were no-op fields). If either key is present in `eventbus.toml`, `load_config()` raises `ValueError` at startup — delete these keys from the config file.

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
