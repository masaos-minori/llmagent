## Goal

Add per-role token fields to `EventBusConfig` and `load_config` for token→role/consumer mapping (REQ-002, REQ-004).

## Scope

- **In-Scope**: Modifying `scripts/eventbus/config.py` to add per-role token configuration fields
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- Per-role tokens will be added to the EventBus TOML config rather than changing the token format itself (e.g., JWT claims)
- The existing single-shared-token deployment model must not break unless a migration path is designed (REQ-005)
- The `auth_token` field will remain as a fallback for backward compatibility

## Design decisions

- Add optional per-role token fields (`publisher_token`, `consumer_token`, `operator_token`, `monitoring_token`) to `EventBusConfig`
- Populate `_TOKEN_CONSUMER_MAP` and `_TOKEN_TOPIC_MAP` from these fields at startup
- Preserve `auth_token` as a fallback for the single-token case

## Alternatives considered

- Using JWT claims instead of per-role tokens — would require significant changes to token generation and validation
- Adding a separate identity store for consumer identities — would require new infrastructure

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

1. Add per-role token fields to `EventBusConfig` dataclass
2. Update `_KNOWN_CONFIG_KEYS` to include the new fields
3. Update `_CONFIG_KEY_TYPES` to include the new fields
4. Update `load_config` to handle the new fields
5. Update `__post_init__` to validate the new fields

### Method

For each per-role token field:
- Add an optional field to `EventBusConfig` with a default value of `""`
- Add the field to `_KNOWN_CONFIG_KEYS` and `_CONFIG_KEY_TYPES`
- Handle the field in `load_config` to extract it from the TOML config

### Details

#### Step 1: Add per-role token fields to EventBusConfig

```python
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
    replay_batch_size: int = 1000
    subscriber_count: int = 10
    retained_event_count: int = 10000
    publish_rate: float = 100.0
    host: str = "127.0.0.1"
    auth_token: str = ""
    # Per-role tokens (optional, for role-based access control)
    publisher_token: str = ""
    consumer_token: str = ""
    operator_token: str = ""
    monitoring_token: str = ""
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
        if self.replay_batch_size < 1:
            raise ValueError(
                f"replay_batch_size must be >= 1, got {self.replay_batch_size}"
            )
        if self.subscriber_count < 1:
            raise ValueError(
                f"subscriber_count must be >= 1, got {self.subscriber_count}"
            )
        if self.retained_event_count < 1:
            raise ValueError(
                f"retained_event_count must be >= 1, got {self.retained_event_count}"
            )
        if self.publish_rate <= 0:
            raise ValueError(f"publish_rate must be > 0, got {self.publish_rate}")
```

#### Step 2: Update _KNOWN_CONFIG_KEYS

```python
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
        "publisher_token",
        "consumer_token",
        "operator_token",
        "monitoring_token",
        "sse_heartbeat_interval",
        "slow_consumer_threshold",
        "subscriber_queue_maxsize",
        "backlog_health_threshold",
        "replay_batch_size",
        "subscriber_count",
        "retained_event_count",
        "publish_rate",
    )
)
```

#### Step 3: Update _CONFIG_KEY_TYPES

```python
_CONFIG_KEY_TYPES: dict[str, type] = {
    "port": int,
    "db_path": str,
    "storage_dir": str,
    "offsets_dir": str,
    "deadletter_dir": str,
    "max_retry": int,
    "host": str,
    "auth_token": str,
    "publisher_token": str,
    "consumer_token": str,
    "operator_token": str,
    "monitoring_token": str,
    "sse_heartbeat_interval": float,
    "slow_consumer_threshold": int,
    "subscriber_queue_maxsize": int,
    "backlog_health_threshold": int,
    "replay_batch_size": int,
    "subscriber_count": int,
    "retained_event_count": int,
    "publish_rate": float,
}
```

#### Step 4: Update load_config

```python
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
        replay_batch_size=int(data.get("replay_batch_size", 1000)),
        subscriber_count=int(data.get("subscriber_count", 10)),
        retained_event_count=int(data.get("retained_event_count", 10000)),
        publish_rate=float(data.get("publish_rate", 100.0)),
        host=data.get("host", "127.0.0.1"),
        auth_token=data["auth_token"],
        publisher_token=data.get("publisher_token", ""),
        consumer_token=data.get("consumer_token", ""),
        operator_token=data.get("operator_token", ""),
        monitoring_token=data.get("monitoring_token", ""),
        sse_heartbeat_interval=float(data.get("sse_heartbeat_interval", 30.0)),
        slow_consumer_threshold=int(data.get("slow_consumer_threshold", 100)),
        subscriber_queue_maxsize=int(data.get("subscriber_queue_maxsize", 1000)),
        backlog_health_threshold=int(data.get("backlog_health_threshold", 500)),
    )
```

## Compatibility considerations

- The existing single-shared-token deployment model must not break unless a migration path is designed (REQ-005)
- The per-role token fields are optional — if not provided, the system falls back to the single shared token
- Existing configurations without per-role tokens will continue to work as before

## Security considerations

- Per-role tokens provide finer-grained access control compared to the single shared token
- The token→role mapping must be secure and not susceptible to replay attacks
- Consumer identity validation must prevent unauthorized topic access

## Rollback considerations

- If the per-role token configuration breaks, roll back to the previous state where authorization was bypassed (security regression)
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/config.py | Unit: verify config parsing includes per-role fields | pytest tests/eventbus/test_eventbus_config.py | Config loads with per-role fields |
| config/eventbus.toml | Integration: verify config file has required fields | Manual review + load_config() | Config loads without errors |

## Completion criteria

- [ ] `EventBusConfig` has per-role token fields (`publisher_token`, `consumer_token`, `operator_token`, `monitoring_token`)
- [ ] `_KNOWN_CONFIG_KEYS` includes the new fields
- [ ] `_CONFIG_KEY_TYPES` includes the new fields
- [ ] `load_config` handles the new fields
- [ ] Backward compatibility with single shared token is preserved
- [ ] Tests pass with the new configuration model

## Out of scope

- Changes to `scripts/eventbus/auth.py` (handled in separate procedure document)
- Changes to `config/eventbus.toml` (handled in separate procedure document)
- Changes to test files (handled in separate procedure document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add per-role token fields to EventBusConfig | Pending | — | — | |
| 2 | Update _KNOWN_CONFIG_KEYS and _CONFIG_KEY_TYPES | Pending | — | — | |
| 3 | Update load_config to handle new fields | Pending | — | — | |
| 4 | Run validation tests | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-111042_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-144827
- **Related target files**: scripts/eventbus/config.py
