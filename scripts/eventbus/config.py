from __future__ import annotations

import ipaddress
import os
import tomllib
import warnings
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_CONFIG_PATH = Path("/opt/llm/config/eventbus.toml")
_DEFAULT_SCHEMA_PATH = Path("/opt/llm/schemas/event_envelope.json")


def get_config_path() -> Path:
    return Path(os.environ.get("EVENTBUS_CONFIG_PATH", _DEFAULT_CONFIG_PATH))


def get_schema_path() -> Path:
    return Path(os.environ.get("EVENTBUS_SCHEMA_PATH", _DEFAULT_SCHEMA_PATH))


def _is_public_host(host: str) -> bool:
    """Return True if host is a public/wildcard address (0.0.0.0, ::)."""
    try:
        addr = ipaddress.ip_address(host)
        return (
            addr.is_unspecified
            or addr == ipaddress.IPv4Address("0.0.0.0")
            or addr == ipaddress.IPv6Address("::")
        )
    except ValueError:
        # If it's not a valid IP address, treat as public (e.g., hostname that resolves to 0.0.0.0)
        return True


@dataclass(frozen=True)
class EventBusConfig:
    port: int
    db_path: str
    storage_dir: str
    offsets_dir: str
    deadletter_dir: str
    max_retry: int
    host: str = "127.0.0.1"
    allow_public_bind: bool = False
    poll_interval_ms: int = (
        500  # deprecated: no longer used; push-mode delivery via EventBroker
    )
    offset_checkpoint_interval: int = (
        10  # deprecated: offset checkpointing removed; ack-only model
    )

    def __post_init__(self) -> None:
        if not 1024 <= self.port <= 65535:
            raise ValueError(f"port must be 1024-65535, got {self.port}")
        if self.max_retry < 1:
            raise ValueError(f"max_retry must be >= 1, got {self.max_retry}")
        if self.poll_interval_ms < 1:
            raise ValueError(
                f"poll_interval_ms must be >= 1, got {self.poll_interval_ms}"
            )
        if self.offset_checkpoint_interval < 1:
            raise ValueError(
                f"offset_checkpoint_interval must be >= 1, got {self.offset_checkpoint_interval}"
            )
        if _is_public_host(self.host) and not self.allow_public_bind:
            raise ValueError(
                f"Event Bus bound to public address {self.host} without allow_public_bind=true. "
                "The API has no authentication — this is a security risk."
            )
        if self.poll_interval_ms != 500:
            warnings.warn(
                "poll_interval_ms is deprecated and has no effect; push-mode delivery via EventBroker",
                DeprecationWarning,
                stacklevel=2,
            )
        if self.offset_checkpoint_interval != 10:
            warnings.warn(
                "offset_checkpoint_interval is deprecated and has no effect; ack-only model in place",
                DeprecationWarning,
                stacklevel=2,
            )


def load_config(path: Path | None = None) -> EventBusConfig:
    p = path or _DEFAULT_CONFIG_PATH
    with p.open("rb") as f:
        data = tomllib.load(f)
    return EventBusConfig(
        port=data["port"],
        db_path=data["db_path"],
        storage_dir=data["storage_dir"],
        offsets_dir=data["offsets_dir"],
        deadletter_dir=data["deadletter_dir"],
        max_retry=data["max_retry"],
        host=data.get("host", "127.0.0.1"),
        allow_public_bind=data.get("allow_public_bind", False),
        poll_interval_ms=data.get("poll_interval_ms", 500),
        offset_checkpoint_interval=data.get("offset_checkpoint_interval", 10),
    )
