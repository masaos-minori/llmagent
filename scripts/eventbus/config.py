"""scripts/eventbus/config.py"""

from __future__ import annotations

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
    """Return True unless host is exactly the loopback address 127.0.0.1 or ::1."""
    return host not in ("127.0.0.1", "::1")


@dataclass(frozen=True)
class EventBusConfig:
    """Immutable configuration for the Event Bus service.

    Validates port range, retry count, loopback-only binding, and cross-field
    relationships among operational thresholds.
    """

    port: int
    db_path: str
    storage_dir: str
    offsets_dir: str
    deadletter_dir: str
    max_retry: int
    host: str = "127.0.0.1"
    auth_token: str = ""
    sse_heartbeat_interval: float = 30.0
    slow_consumer_threshold: int = 100
    subscriber_queue_maxsize: int = 1000
    backlog_health_threshold: int = 500

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if not 1024 <= self.port <= 65535:
            raise ValueError(f"port must be 1024-65535, got {self.port}")
        if self.max_retry < 1:
            raise ValueError(f"max_retry must be >= 1, got {self.max_retry}")
        if _is_public_host(self.host):
            raise ValueError(
                f"Event Bus bound to non-loopback address {self.host}. "
                "The API has no authentication — this is a security risk."
            )
        if not self.auth_token:
            raise ValueError("auth_token is required but not configured")
        if self.slow_consumer_threshold >= self.subscriber_queue_maxsize:
            raise ValueError(
                "slow_consumer_threshold must be less than subscriber_queue_maxsize"
            )
        if self.backlog_health_threshold > self.subscriber_queue_maxsize:
            raise ValueError(
                "backlog_health_threshold must be less than or equal to subscriber_queue_maxsize"
            )


_KNOWN_CONFIG_KEYS = frozenset(
    (
        "port",
        "db_path",
        "storage_dir",
        "offsets_dir",
        "deadletter_dir",
        "max_retry",
        "host",
        "auth_token",
        "sse_heartbeat_interval",
        "slow_consumer_threshold",
        "subscriber_queue_maxsize",
        "backlog_health_threshold",
    )
)

# Optional keys have defaults; only these are required
_REQUIRED_CONFIG_KEYS = frozenset(
    (
        "port",
        "db_path",
        "storage_dir",
        "offsets_dir",
        "deadletter_dir",
        "max_retry",
        "auth_token",
    )
)

_OPTIONAL_CONFIG_KEYS = _KNOWN_CONFIG_KEYS - _REQUIRED_CONFIG_KEYS

_CONFIG_KEY_TYPES: dict[str, type] = {
    "port": int,
    "db_path": str,
    "storage_dir": str,
    "offsets_dir": str,
    "deadletter_dir": str,
    "max_retry": int,
    "host": str,
    "auth_token": str,
    "sse_heartbeat_interval": float,
    "slow_consumer_threshold": int,
    "subscriber_queue_maxsize": int,
    "backlog_health_threshold": int,
}


def load_config(path: Path | None = None) -> EventBusConfig:
    """Load and validate the EventBus TOML configuration file. Callers must always pass get_config_path()'s return value — this function does not itself restrict which path is read; see tests/eventbus/test_eventbus_config.py for the call-site regression test that locks this invariant."""
    p = path or _DEFAULT_CONFIG_PATH
    with p.open("rb") as f:
        data = tomllib.load(f)

    # Reject unknown keys
    unknown_keys = set(data.keys()) - _KNOWN_CONFIG_KEYS
    if unknown_keys:
        raise ValueError(
            f"eventbus config contains unknown key(s): {', '.join(sorted(unknown_keys))}. "
            f"Known keys are: {', '.join(sorted(_KNOWN_CONFIG_KEYS))}."
        )

    # Validate required keys exist
    missing_keys = _REQUIRED_CONFIG_KEYS - set(data.keys())
    if missing_keys:
        raise ValueError(
            f"eventbus config missing required key(s): {', '.join(sorted(missing_keys))}."
        )

    # Validate types for all known keys that are present
    for key, expected_type in _CONFIG_KEY_TYPES.items():
        if key in data:
            value = data[key]
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"eventbus config key '{key}' has type {type(value).__name__}, "
                    f"expected {expected_type.__name__}."
                )

    # Validate auth_token is non-empty
    if not data["auth_token"]:
        raise ValueError("eventbus config 'auth_token' must not be empty.")

    return EventBusConfig(
        port=data["port"],
        db_path=data["db_path"],
        storage_dir=data["storage_dir"],
        offsets_dir=data["offsets_dir"],
        deadletter_dir=data["deadletter_dir"],
        max_retry=data["max_retry"],
        host=data.get("host", "127.0.0.1"),
        auth_token=data["auth_token"],
        sse_heartbeat_interval=float(data.get("sse_heartbeat_interval", 30.0)),
        slow_consumer_threshold=int(data.get("slow_consumer_threshold", 100)),
        subscriber_queue_maxsize=int(data.get("subscriber_queue_maxsize", 1000)),
        backlog_health_threshold=int(data.get("backlog_health_threshold", 500)),
    )
