from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_CONFIG_PATH = "/opt/llm/config/eventbus.toml"
_DEFAULT_SCHEMA_PATH = "/opt/llm/schemas/event_envelope.json"


def get_config_path() -> str:
    return os.environ.get("EVENTBUS_CONFIG_PATH", _DEFAULT_CONFIG_PATH)


def get_schema_path() -> str:
    return os.environ.get("EVENTBUS_SCHEMA_PATH", _DEFAULT_SCHEMA_PATH)


@dataclass(frozen=True)
class EventBusConfig:
    port: int
    db_path: str
    storage_dir: str
    offsets_dir: str
    deadletter_dir: str
    max_retry: int
    poll_interval_ms: int = 500
    offset_checkpoint_interval: int = 10


def load_config(path: Path | str | None = None) -> EventBusConfig:
    p = Path(path) if path else Path(get_config_path())
    with p.open("rb") as f:
        data = tomllib.load(f)
    return EventBusConfig(
        port=data["port"],
        db_path=data["db_path"],
        storage_dir=data["storage_dir"],
        offsets_dir=data["offsets_dir"],
        deadletter_dir=data["deadletter_dir"],
        max_retry=data["max_retry"],
        poll_interval_ms=data.get("poll_interval_ms", 500),
        offset_checkpoint_interval=data.get("offset_checkpoint_interval", 10),
    )
