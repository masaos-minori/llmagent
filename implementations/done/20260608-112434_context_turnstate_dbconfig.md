# Implementation: TurnState Extension and DbConfig Relocation

## Goal

Extend `TurnState` with `background_tasks` and `last_error_kind` fields, and relocate
`DbConfig`/`build_db_config()` from `agent/config.py` to `db/config.py`.

## Scope

**In:**
- `scripts/agent/context.py`: add `background_tasks: set[asyncio.Task[Any]]` and
  `last_error_kind: str | None` to `TurnState` dataclass
- `scripts/db/config.py`: new file; move `DbConfig` + `build_db_config()` from `agent/config.py`
  (`build_db_config` uses `ConfigLoader` directly instead of `load_config()`)
- `scripts/agent/config.py`: remove `DbConfig`/`build_db_config()` definitions; re-export from
  `db.config` for backward compat

**Out:**
- Changing the validation logic inside `DbConfig.__post_init__`
- Changing callers of `build_db_config()`

## Assumptions

- No external file imports `DbConfig` from `agent.config` (confirmed by grep: zero results)
- `db/` layer may import from `shared/` (allowed by import-linter contract)
- `asyncio.Task` field on `TurnState` will not be serialized; it is runtime-only

## Implementation

### `scripts/agent/context.py`

Add to `TurnState`:
```python
import asyncio
from typing import Any
from dataclasses import field

@dataclass
class TurnState:
    current_turn_id: str | None = None
    background_tasks: set[asyncio.Task[Any]] = field(default_factory=set)
    last_error_kind: str | None = None
```

### `scripts/db/config.py`

New file:
```python
"""db/config.py
DbConfig dataclass and builder for SQLite + embedding service paths.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from shared.config_loader import ConfigLoader

@dataclass
class DbConfig:
    ...  # same fields and __post_init__ as current agent/config.py

def build_db_config() -> DbConfig:
    cfg = ConfigLoader().load_all()
    return DbConfig(
        rag_db_path=cfg.get("rag_db_path", ""),
        ...
    )
```

### `scripts/agent/config.py`

Remove `DbConfig` class and `build_db_config()`.
Add at the end:
```python
# Re-export for backward compatibility
from db.config import DbConfig, build_db_config  # noqa: F401 — re-export
```

## Validation plan

```bash
uv run ruff check scripts/agent/context.py scripts/db/config.py scripts/agent/config.py
uv run mypy scripts/
PYTHONPATH=scripts uv run lint-imports
uv run pytest -v
```
