# Implementation Procedure: scripts/eventbus/config.py + scripts/eventbus/app.py

## Goal

`EVENTBUS_CONFIG_PATH` と `EVENTBUS_SCHEMA_PATH` 環境変数でパスをオーバーライドできるようにする。

## Scope

**In:**
- `scripts/eventbus/config.py` — env var オーバーライド追加
- `scripts/eventbus/app.py` — オーバーライドパスを config loader に渡す

**Out:** config モデルの再設計

## Assumptions

1. `config.py` は現在 `/opt/llm/config/eventbus.toml` をハードコード (実装時に確認)
2. パターン: `os.environ.get("EVENTBUS_CONFIG_PATH", "/opt/llm/config/eventbus.toml")`

## Implementation

### config.py — env var lookup

```python
import os

_DEFAULT_CONFIG_PATH = "/opt/llm/config/eventbus.toml"
_DEFAULT_SCHEMA_PATH = "/opt/llm/schemas/event_envelope.json"

def get_config_path() -> str:
    return os.environ.get("EVENTBUS_CONFIG_PATH", _DEFAULT_CONFIG_PATH)

def get_schema_path() -> str:
    return os.environ.get("EVENTBUS_SCHEMA_PATH", _DEFAULT_SCHEMA_PATH)
```

### app.py — use override paths

```python
from eventbus.config import get_config_path, get_schema_path

# In lifespan:
cfg_path = get_config_path()
schema_path = get_schema_path()
logger.info("eventbus: config=%s schema=%s", cfg_path, schema_path)
_cfg = load_config(cfg_path)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/config.py scripts/eventbus/app.py` | 0 errors |
| Regression | `uv run pytest tests/test_eventbus*.py -x -q` | all pass |
| Env override | `EVENTBUS_CONFIG_PATH=/tmp/test.toml python -c "from eventbus.config import get_config_path; print(get_config_path())"` | `/tmp/test.toml` |
