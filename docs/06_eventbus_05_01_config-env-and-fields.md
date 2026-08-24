---
title: "Event Bus: Configuration Fields and Environment Variables"
area: eventbus
tags:
  - event-bus
  - configuration
  - environment-variables
  - config-fields
  - toml
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_02_bind-address-and-start.md
  - 06_eventbus_05_03_health-endpoint-semantics.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: Configuration Fields and Environment Variables

## Configuration

Loaded from a TOML file (default: `/opt/llm/config/eventbus.toml`).

### Environment Variables

- `EVENTBUS_CONFIG_PATH` — Path to the TOML file
- `EVENTBUS_SCHEMA_PATH` — Path to the event envelope JSON Schema

### Configuration Fields

- `port` — HTTP listening port (startup fails if outside 1024–65535)
- `db_path` — SQLite DB path
- `storage_dir` — JSONL archive directory
- `offsets_dir` — Consumer offset directory
- `deadletter_dir` — DLQ directory
- `max_retry` — Retry threshold before DLQ promotion (startup fails if < 1)
- `host` — Listening address (default: `127.0.0.1`)
- `allow_public_bind` — Allow public binding (default: false)

Validation for `port` and `max_retry` is performed in `EventBusConfig.__post_init__()`.

### Deprecated Keys

Startup fails if `poll_interval_ms` or `offset_checkpoint_interval` remain in the configuration file.

## Related Documents

- `06_eventbus_05_02_bind-address-and-start.md`
- `06_eventbus_05_03_health-endpoint-semantics.md`
