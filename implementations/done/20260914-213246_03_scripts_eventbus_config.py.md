# Implementation Procedure: Add sse_idle_timeout field, known keys entry, type validation, and config loader integration

## Goal

Update `scripts/eventbus/config.py` to add `sse_idle_timeout` field to the EventBusConfig dataclass, add it to the known keys list, add type validation, and integrate it into the config loader.

## Scope

- Add `sse_idle_timeout` field to EventBusConfig dataclass.
- Add `sse_idle_timeout` to known keys list.
- Add `sse_idle_timeout` to type mapping.
- Add `sse_idle_timeout` to config loader integration.
- Add cross-field validation between sse_idle_timeout and sse_heartbeat_interval.

## Assumptions

- A: REQ-007 through REQ-009 in `scripts/eventbus/config.py` are implemented before this change.
- B: The `DEFAULT_SSE_IDLE_TIMEOUT = 60` constant in `subscribe_route.py` is the current implicit default — confirmed by `subscribe_route.py:28`.
- C: The `getattr(cfg, "sse_idle_timeout", DEFAULT_SSE_IDLE_TIMEOUT)` pattern in `subscribe_route.py` means the config class doesn't have this field yet — confirmed by `subscribe_route.py:166`.
- D: `sse_heartbeat_interval` has a default of 30.0 seconds — confirmed by `config.py:55`.

## Design decisions

- **Default value**: 60 seconds (matches current `DEFAULT_SSE_IDLE_TIMEOUT` constant).
- **Valid range**: [1.0, inf] — minimum 1 second to prevent rapid reconnect storms; no upper bound (infinity allowed for persistent subscriptions).
- **Type**: `float` — consistent with `sse_heartbeat_interval` type.
- **Cross-field validation**: `sse_idle_timeout` must be greater than `sse_heartbeat_interval` — a heartbeat interval longer than the idle timeout would cause heartbeats to never fire before the connection times out.
- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Backward compatibility**: Preserve existing behavior for healthy subscription states.

## Alternatives considered

- **Keep single-token design**: Continue using only `auth_token` and per-role tokens. This was rejected because it doesn't provide the granularity needed for REQ-007—REQ-009.
- **Separate authorization config file**: Have a separate YAML/TOML file for authorization rules. This adds complexity without security benefit.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original EventBusConfig dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

#### Step 1: Add sse_idle_timeout field to EventBusConfig dataclass (REQ-007, REQ-008)

Replace the current EventBusConfig dataclass definition (lines 29-58):

Current code:
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
    admin_token: str = ""
    sse_heartbeat_interval: float = 30.0
    slow_consumer_threshold: int = 100
    subscriber_queue_maxsize: int = 1000
    backlog_health_threshold: int = 500
```

New code:
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
    admin_token: str = ""
    sse_heartbeat_interval: float = 30.0
    sse_idle_timeout: float = 60.0  # Default matches current implicit DEFAULT_SSE_IDLE_TIMEOUT
    slow_consumer_threshold: int = 100
    subscriber_queue_maxsize: int = 1000
    backlog_health_threshold: int = 500
```

Key changes:
- Added `sse_idle_timeout: float = 60.0` field after `sse_heartbeat_interval`.

#### Step 2: Update __post_object__() validation for new fields (REQ-009)

Replace the current `__post_object__()` method (lines 60-94):

Current code:
```python
    def __post_object__(self) -> None:
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

New code:
```python
    def __post_object__(self) -> None:
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
        
        # Validate sse_idle_timeout range
        if self.sse_idle_timeout < 1.0:
            raise ValueError(f"sse_idle_timeout must be >= 1.0, got {self.sse_idle_timeout}")
        
        # Cross-field validation: sse_idle_timeout must be greater than sse_heartbeat_interval
        if self.sse_idle_timeout <= self.sse_heartbeat_interval:
            raise ValueError(
                f"sse_idle_timeout ({self.sse_idle_timeout}) must be greater than "
                f"sse_heartbeat_interval ({self.sse_heartbeat_interval})"
            )
```

Key changes:
- Added validation for `sse_idle_timeout` range (must be >= 1.0).
- Added cross-field validation: `sse_idle_timeout` must be greater than `sse_heartbeat_interval`.

#### Step 3: Update _KNOWN_CONFIG_KEYS to include new field (REQ-007)

Replace the current `_KNOWN_CONFIG_KEYS` constant (after line 97):

Current code:
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
        "admin_token",
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

New code:
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
        "admin_token",
        "sse_heartbeat_interval",
        "sse_idle_timeout",
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

Key changes:
- Added `"sse_idle_timeout"` to known config keys.

#### Step 4: Update _CONFIG_KEY_TYPES to include new field (REQ-007)

Replace the current `_CONFIG_KEY_TYPES` dictionary (after line 138):

Current code:
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
    "admin_token": str,
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

New code:
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
    "admin_token": str,
    "sse_heartbeat_interval": float,
    "sse_idle_timeout": float,
    "slow_consumer_threshold": int,
    "subscriber_queue_maxsize": int,
    "backlog_health_threshold": int,
    "replay_batch_size": int,
    "subscriber_count": int,
    "retained_event_count": int,
    "publish_rate": float,
}
```

Key changes:
- Added `"sse_idle_timeout": float` to type mapping.

#### Step 5: Update load_config() to include new field (REQ-007)

Replace the current `load_config()` function return statement (line 208-230):

Current code:
```python
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
        admin_token=data.get("admin_token", ""),
        sse_heartbeat_interval=float(data.get("sse_heartbeat_interval", 30.0)),
        slow_consumer_threshold=int(data.get("slow_consumer_threshold", 100)),
        subscriber_queue_maxsize=int(data.get("subscriber_queue_maxsize", 1000)),
        backlog_health_threshold=int(data.get("backlog_health_threshold", 500)),
    )
```

New code:
```python
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
        admin_token=data.get("admin_token", ""),
        sse_heartbeat_interval=float(data.get("sse_heartbeat_interval", 30.0)),
        sse_idle_timeout=float(data.get("sse_idle_timeout", 60.0)),
        slow_consumer_threshold=int(data.get("slow_consumer_threshold", 100)),
        subscriber_queue_maxsize=int(data.get("subscriber_queue_maxsize", 1000)),
        backlog_health_threshold=int(data.get("backlog_health_threshold", 500)),
    )
```

Key changes:
- Added `sse_idle_timeout=float(data.get("sse_idle_timeout", 60.0))` to config loader.

### Details

- REQ-007: `sse_idle_timeout` added to dataclass, known keys, type mapping, and config loader.
- REQ-008: Default value of 60 seconds defined; valid range [1.0, inf].
- REQ-009: Cross-field validation between sse_idle_timeout and sse_heartbeat_interval added.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original EventBusConfig dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/config.py | Unit: sse_idle_timeout loading/validation | uv run pytest tests/eventbus/test_eventbus_config.py -v | New config tests pass |
| scripts/eventbus/config.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/config.py | Type checking | uv run mypy scripts/eventbus/config.py | No new type errors |

## Completion criteria

- [ ] `sse_idle_timeout` field added to EventBusConfig dataclass with default 60.0.
- [ ] `sse_idle_timeout` added to known keys list.
- [ ] `sse_idle_timeout` added to type mapping as float.
- [ ] `sse_idle_timeout` added to config loader integration.
- [ ] Cross-field validation between sse_idle_timeout and sse_heartbeat_interval added.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Documentation updates (handled separately per REQ-010).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add sse_idle_timeout field to EventBusConfig dataclass | Pending | — | — | |
| 2 | Update __post_object__() validation for new fields | Pending | — | — | |
| 3 | Update _KNOWN_CONFIG_KEYS to include new field | Pending | — | — | |
| 4 | Update _CONFIG_KEY_TYPES to include new field | Pending | — | — | |
| 5 | Update load_config() to include new field | Pending | — | — | |

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
- **Requirement ID**: REQ-007, REQ-008, REQ-009
- **Source issue**: issues/20260914-102344_sse-lifecycle-heartbeat-idle-timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172918_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-213246
- **Related target files**: scripts/eventbus/config.py
