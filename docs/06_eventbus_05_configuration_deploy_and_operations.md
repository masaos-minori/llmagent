# Event Bus: Configuration, Deploy and Operations

## Configuration

Event Bus configuration is loaded from a TOML file (default: `/opt/llm/config/eventbus.toml`).

### Environment variable overrides

| Variable | Default | Purpose |
|---|---|---|
| `EVENTBUS_CONFIG_PATH` | `/opt/llm/config/eventbus.toml` | TOML config file path |
| `EVENTBUS_SCHEMA_PATH` | `/opt/llm/schemas/event_envelope.json` | JSON Schema for event envelopes |

### Config fields

| Field | Type | Default | Description |
|---|---|---|---|
| `port` | int | — | HTTP listen port |
| `db_path` | str | — | SQLite database file path |
| `storage_dir` | str | — | JSONL event archive directory |
| `offsets_dir` | str | — | Consumer offset file directory |
| `deadletter_dir` | str | — | Dead-letter queue JSONL directory |
| `max_retry` | int | — | Retry threshold before DLQ promotion |
| `poll_interval_ms` | int | 500 | Subscribe poll interval (ms) |
| `offset_checkpoint_interval` | int | 10 | Write offset every N delivered events |

## Deployment

### Bind Address

The EventBus server should bind to `127.0.0.1` (loopback) in production, not
`0.0.0.0`. Binding to `0.0.0.0` exposes the EventBus API to the local network,
which is a security risk (no authentication layer on the EventBus HTTP endpoints).

```toml
# config/eventbus.toml
host = "127.0.0.1"
port = 8765
```

If remote access is required, use a reverse proxy with authentication.

### Start command

```bash
EVENTBUS_CONFIG_PATH=/opt/llm/config/eventbus.toml uvicorn eventbus.app:app --host 127.0.0.1 --port 8010
```

## Validation status

Event Bus module CI verification:

| Check | Command | Status |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/` | 0 errors |
| Type check | `uv run mypy scripts/eventbus/` | no errors |
| Tests | `uv run pytest tests/test_eventbus*.py` | all pass |

Last verified: 2026-06-24
