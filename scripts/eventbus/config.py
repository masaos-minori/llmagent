from __future__ import annotations

import ipaddress
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_CONFIG_PATH = Path("/opt/llm/config/eventbus.toml")
_DEFAULT_SCHEMA_PATH = Path("/opt/llm/schemas/event_envelope.json")


def get_config_path() -> Path:
    """Return the path to the Event Bus TOML configuration file."""
    return Path(os.environ.get("EVENTBUS_CONFIG_PATH", _DEFAULT_CONFIG_PATH))


def get_schema_path() -> Path:
    """Return the path to the Event Envelope JSON schema file."""
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
    """Immutable configuration for the Event Bus service.

    Validates port range, retry count, and prevents binding to public addresses
    unless explicitly allowed via allow_public_bind.
    """

    port: int
    db_path: str
    storage_dir: str
    offsets_dir: str
    deadletter_dir: str
    max_retry: int
    host: str = "127.0.0.1"
    allow_public_bind: bool = False

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if not 1024 <= self.port <= 65535:
            raise ValueError(f"port must be 1024-65535, got {self.port}")
        if self.max_retry < 1:
            raise ValueError(f"max_retry must be >= 1, got {self.max_retry}")
        if _is_public_host(self.host) and not self.allow_public_bind:
            raise ValueError(
                f"Event Bus bound to public address {self.host} without allow_public_bind=true. "
                "The API has no authentication — this is a security risk."
            )


_REMOVED_CONFIG_KEYS = ("poll_interval_ms", "offset_checkpoint_interval")


def load_config(path: Path | None = None) -> EventBusConfig:
    """Load and validate the EventBus TOML configuration file."""
    p = path or _DEFAULT_CONFIG_PATH
    with p.open("rb") as f:
        data = tomllib.load(f)
    stale_keys = [k for k in _REMOVED_CONFIG_KEYS if k in data]
    if stale_keys:
        raise ValueError(
            f"eventbus config contains removed key(s): {', '.join(stale_keys)}. "
            "These fields were deprecated no-ops and have been removed; "
            f"delete them from {p}."
        )
    return EventBusConfig(
        port=data["port"],
        db_path=data["db_path"],
        storage_dir=data["storage_dir"],
        offsets_dir=data["offsets_dir"],
        deadletter_dir=data["deadletter_dir"],
        max_retry=data["max_retry"],
        host=data.get("host", "127.0.0.1"),
        allow_public_bind=data.get("allow_public_bind", False),
    )
