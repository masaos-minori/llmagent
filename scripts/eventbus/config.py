"""scripts/eventbus/config.py"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shared.config_loader import ConfigLoader
from shared.config_utils import resolve_env_ref

_DEFAULT_CONFIG_PATH = Path("/opt/llm/config/eventbus.toml")
_DEFAULT_SCHEMA_PATH = Path("/opt/llm/schemas/event_envelope.json")


def _load_config_from_path(path: Path) -> dict[str, Any]:
    """Load config from an arbitrary path using ConfigLoader's internal logic."""
    loader = ConfigLoader(config_dir=path.parent)
    return loader.load(path.name)


def get_config_path() -> Path:
    """Return the path to the Event Bus TOML configuration file."""
    return Path(os.environ.get("EVENTBUS_CONFIG_PATH", _DEFAULT_CONFIG_PATH))


def get_schema_path() -> Path:
    """Return the path to the Event Envelope JSON schema file."""
    return Path(os.environ.get("EVENTBUS_SCHEMA_PATH", _DEFAULT_SCHEMA_PATH))


def _is_public_host(host: str) -> bool:
    """Return True unless host is exactly the loopback address 127.0.0.1 or ::1."""
    return host not in ("127.0.0.1", "::1")


def authorization_baseline_hash(cfg: EventBusConfig) -> str:
    """Return a SHA-256 hex digest over the canonical authorization pair set.

    The digest covers only the union of (consumer_id, topic) pairs derived from
    consumer_authorization, never the whole config. Pairs are canonically sorted
    before hashing, so the digest is invariant under any permutation of the
    mapping (EBAUTHGEN001 AC-2).
    """
    pairs: set[tuple[str, str]] = set()
    for consumer_id, consumer_topics in (cfg.consumer_authorization or {}).items():
        pairs.update((consumer_id, topic) for topic in consumer_topics)
    canonical = json.dumps(sorted(pairs))
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class EventBusConfig:
    """Immutable configuration for the Event Bus service.

    Validates port range, retry count, loopback-only binding, and cross-field
    relationships among operational thresholds.
    """

    port: int
    db_path: str
    storage_dir: str
    deadletter_dir: str
    max_retry: int
    replay_batch_size: int = 1000
    subscriber_count: int = 10
    publish_rate: float = 100.0
    host: str = "127.0.0.1"
    auth_token: str = ""
    # Per-role tokens (optional, for role-based access control).
    # When set, each token grants only its own role (e.g., publisher_token → PUBLISHER).
    # The shared auth_token and admin_token hold only the Operator, Monitoring, and Admin roles (no Consumer or Publisher role).
    # At least one per-role token must be configured when using role-based access control.
    publisher_token: str = ""
    consumer_token: str = ""
    operator_token: str = ""
    monitoring_token: str = ""
    admin_token: str = ""
    # Per-consumer/topic authorization (optional, for fine-grained access control)
    consumer_authorization: dict[str, list[str]] | None = (
        None  # consumer_id -> [topics]
    )
    sse_heartbeat_interval: float = 30.0
    sse_idle_timeout: float = (
        60.0  # Default matches current implicit DEFAULT_SSE_IDLE_TIMEOUT
    )
    slow_consumer_threshold: int = 100
    subscriber_queue_maxsize: int = 1000
    backlog_health_threshold: int = 500
    # Authorization TTL bounds (ebauthgen001): max accepted ttl_seconds on
    # POST /admin/topics/authorization, and the interval of the TTL sweep loop.
    authz_max_ttl_seconds: int = 86400
    authz_sweep_interval_seconds: float = 60.0
    # DLQ outbox retry policy (dlqbox001): bounded attempts, exponential backoff clamped
    # at the max. Consumed by the outbox worker in eventbus.dlq.
    outbox_max_attempts: int = 5
    outbox_backoff_base_seconds: int = 30
    outbox_backoff_max_seconds: int = 900

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if not 1024 <= self.port <= 65535:
            raise ValueError(f"port must be 1024-65535, got {self.port}")
        if self.max_retry < 1:
            raise ValueError(f"max_retry must be >= 1, got {self.max_retry}")
        if _is_public_host(self.host):
            raise ValueError(
                f"Event Bus bound to non-loopback address {self.host}; "
                "only loopback addresses (127.0.0.1, ::1) are allowed."
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
        if self.replay_batch_size < 1:
            raise ValueError(
                f"replay_batch_size must be >= 1, got {self.replay_batch_size}"
            )
        if self.outbox_max_attempts < 1:
            raise ValueError(
                f"outbox_max_attempts must be >= 1, got {self.outbox_max_attempts}"
            )
        if self.outbox_backoff_base_seconds < 1:
            raise ValueError(
                f"outbox_backoff_base_seconds must be >= 1, got {self.outbox_backoff_base_seconds}"
            )
        if self.outbox_backoff_max_seconds < self.outbox_backoff_base_seconds:
            raise ValueError(
                "outbox_backoff_max_seconds must be >= outbox_backoff_base_seconds, "
                f"got {self.outbox_backoff_max_seconds}"
            )
        if self.subscriber_count < 1:
            raise ValueError(
                f"subscriber_count must be >= 1, got {self.subscriber_count}"
            )
        if self.publish_rate <= 0:
            raise ValueError(f"publish_rate must be > 0, got {self.publish_rate}")
        if self.authz_max_ttl_seconds < 1:
            raise ValueError(
                f"authz_max_ttl_seconds must be >= 1, got {self.authz_max_ttl_seconds}"
            )
        if self.authz_sweep_interval_seconds < 1.0:
            raise ValueError(
                f"authz_sweep_interval_seconds must be >= 1.0, got {self.authz_sweep_interval_seconds}"
            )

        # Validate sse_idle_timeout range
        if self.sse_idle_timeout < 1.0:
            raise ValueError(
                f"sse_idle_timeout must be >= 1.0, got {self.sse_idle_timeout}"
            )

        # Cross-field validation: sse_idle_timeout must be greater than sse_heartbeat_interval
        if self.sse_idle_timeout <= self.sse_heartbeat_interval:
            raise ValueError(
                f"sse_idle_timeout ({self.sse_idle_timeout}) must be greater than "
                f"sse_heartbeat_interval ({self.sse_heartbeat_interval})"
            )

        # Validate consumer_authorization if provided
        if self.consumer_authorization is not None:
            for consumer_id, topics in self.consumer_authorization.items():
                if not isinstance(consumer_id, str):
                    raise ValueError(
                        f"consumer_authorization key must be string, got {type(consumer_id).__name__}"
                    )
                if not isinstance(topics, list):
                    raise ValueError(
                        f"consumer_authorization value must be list, got {type(topics).__name__}"
                    )
                for topic in topics:
                    if not isinstance(topic, str):
                        raise ValueError(
                            f"consumer_authorization topic must be string, got {type(topic).__name__}"
                        )


_KNOWN_CONFIG_KEYS = frozenset(
    (
        "port",
        "db_path",
        "storage_dir",
        "deadletter_dir",
        "max_retry",
        "host",
        "auth_token",
        "publisher_token",
        "consumer_token",
        "operator_token",
        "monitoring_token",
        "admin_token",
        "sse_heartbeat_interval",
        "sse_idle_timeout",
        "slow_consumer_threshold",
        "subscriber_queue_maxsize",
        "backlog_health_threshold",
        "replay_batch_size",
        "outbox_max_attempts",
        "outbox_backoff_base_seconds",
        "outbox_backoff_max_seconds",
        "subscriber_count",
        "publish_rate",
        "consumer_authorization",
        "authz_max_ttl_seconds",
        "authz_sweep_interval_seconds",
    )
)

# Optional keys have defaults; only these are required
_REQUIRED_CONFIG_KEYS = frozenset(
    (
        "port",
        "db_path",
        "storage_dir",
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
    "deadletter_dir": str,
    "max_retry": int,
    "host": str,
    "auth_token": str,
    "publisher_token": str,
    "consumer_token": str,
    "operator_token": str,
    "monitoring_token": str,
    "admin_token": str,
    "sse_heartbeat_interval": float,
    "sse_idle_timeout": float,
    "slow_consumer_threshold": int,
    "subscriber_queue_maxsize": int,
    "backlog_health_threshold": int,
    "replay_batch_size": int,
    "outbox_max_attempts": int,
    "outbox_backoff_base_seconds": int,
    "outbox_backoff_max_seconds": int,
    "subscriber_count": int,
    "publish_rate": float,
    "authz_max_ttl_seconds": int,
    "authz_sweep_interval_seconds": float,
}

# Token keys whose value may be a "${ENV:VAR_NAME}" reference. Resolved in
# load_config() before any value is validated, so a reference can never be used
# as a literal token and an unset variable fails the load.
_TOKEN_CONFIG_KEYS: tuple[str, ...] = (
    "auth_token",
    "publisher_token",
    "consumer_token",
    "operator_token",
    "monitoring_token",
    "admin_token",
)


def load_config(path: Path | None = None) -> EventBusConfig:
    """Load and validate the EventBus TOML configuration file.

    Callers must always pass get_config_path()'s return value — this function
    does not itself restrict which path is read; see
    tests/eventbus/test_eventbus_config.py for the call-site regression test
    that locks this invariant.
    """
    p = path or _DEFAULT_CONFIG_PATH

    # Fail-closed behavior for missing config file
    if not p.exists():
        raise FileNotFoundError(
            f"eventbus config file not found: {p}. "
            "This is a critical error — the service cannot start without configuration."
        )

    data = _load_config_from_path(p)

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

    # Resolve "${ENV:VAR_NAME}" references before validating any token value
    for key in _TOKEN_CONFIG_KEYS:
        value = data.get(key)
        if isinstance(value, str):
            data[key] = resolve_env_ref(value)

    # Normalize authorization-mapping value types to the EventBusConfig annotations
    # (REQ-002): consumer_authorization values stay list[str]. A missing key stays
    # None so the empty-vs-missing distinction build_and_publish_generation()
    # depends on is preserved.
    consumer_authorization = data.get("consumer_authorization")

    cfg = EventBusConfig(
        port=data["port"],
        db_path=data["db_path"],
        storage_dir=data["storage_dir"],
        deadletter_dir=data["deadletter_dir"],
        max_retry=data["max_retry"],
        replay_batch_size=int(data.get("replay_batch_size", 1000)),
        subscriber_count=int(data.get("subscriber_count", 10)),
        publish_rate=float(data.get("publish_rate", 100.0)),
        host=data.get("host", "127.0.0.1"),
        auth_token=data["auth_token"],
        publisher_token=data.get("publisher_token", ""),
        consumer_token=data.get("consumer_token", ""),
        operator_token=data.get("operator_token", ""),
        monitoring_token=data.get("monitoring_token", ""),
        admin_token=data.get("admin_token", ""),
        consumer_authorization=consumer_authorization,
        sse_heartbeat_interval=float(data.get("sse_heartbeat_interval", 30.0)),
        sse_idle_timeout=float(data.get("sse_idle_timeout", 60.0)),
        slow_consumer_threshold=int(data.get("slow_consumer_threshold", 100)),
        subscriber_queue_maxsize=int(data.get("subscriber_queue_maxsize", 1000)),
        backlog_health_threshold=int(data.get("backlog_health_threshold", 500)),
        authz_max_ttl_seconds=int(data.get("authz_max_ttl_seconds", 86400)),
        authz_sweep_interval_seconds=float(
            data.get("authz_sweep_interval_seconds", 60.0)
        ),
        outbox_max_attempts=int(data.get("outbox_max_attempts", 5)),
        outbox_backoff_base_seconds=int(data.get("outbox_backoff_base_seconds", 30)),
        outbox_backoff_max_seconds=int(data.get("outbox_backoff_max_seconds", 900)),
    )

    return cfg
