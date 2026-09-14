# Implementation Procedure: Add per-consumer/topic authorization fields to EventBusConfig

## Goal

Update `scripts/eventbus/config.py` to add per-consumer/topic authorization fields to `EventBusConfig`, enabling fine-grained authorization for REQ-017.

## Scope

- Add new fields to `EventBusConfig` dataclass: `consumer_authorization`, `topic_authorization`.
- Update `__post_object__()` validation logic for new fields.
- Update `_KNOWN_CONFIG_KEYS` to include new fields.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The `Principal` dataclass has fields: roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- C: The current `EventBusConfig` dataclass has basic auth_token and per-role token fields.
- D: The current `__post_object__()` validates port range, retry count, loopback-only binding, and cross-field relationships.

## Design decisions

- **Per-consumer authorization**: Add `consumer_authorization` field that maps consumer IDs to their authorized topics.
- **Topic authorization**: Add `topic_authorization` field that defines topic-level access policies.
- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Backward compatibility**: Preserve existing behavior for tokens with empty allowed_consumer_ids/allowed_topics (means "any").

## Alternatives considered

- **Keep single-token design**: Continue using only `auth_token` and per-role tokens. This was rejected because it doesn't provide the granularity needed for REQ-017.
- **Separate authorization config file**: Have a separate YAML/TOML file for authorization rules. This adds complexity without security benefit.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `EventBusConfig` dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

#### Step 1: Add new authorization fields to EventBusConfig (REQ-017)

Replace the current `EventBusConfig` dataclass definition (lines 29-59):

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
    # Per-consumer/topic authorization (optional, for fine-grained access control)
    consumer_authorization: dict[str, list[str]] | None = None  # consumer_id -> [topics]
    topic_authorization: dict[str, set[str]] | None = None  # topic -> [consumer_ids]
    sse_heartbeat_interval: float = 30.0
    slow_consumer_threshold: int = 100
    subscriber_queue_maxsize: int = 1000
    backlog_health_threshold: int = 500
```

Key changes:
- Added `consumer_authorization` field: maps consumer IDs to their authorized topics.
- Added `topic_authorization` field: maps topics to their authorized consumer IDs.
- Both fields default to None (no restriction).

#### Step 2: Update __post_object__() validation for new fields (REQ-017)

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
    
    # Validate consumer_authorization if provided
    if self.consumer_authorization is not None:
        for consumer_id, topics in self.consumer_authorization.items():
            if not isinstance(consumer_id, str):
                raise ValueError(f"consumer_authorization key must be string, got {type(consumer_id).__name__}")
            if not isinstance(topics, list):
                raise ValueError(f"consumer_authorization value must be list, got {type(topics).__name__}")
            for topic in topics:
                if not isinstance(topic, str):
                    raise ValueError(f"consumer_authorization topic must be string, got {type(topic).__name__}")
    
    # Validate topic_authorization if provided
    if self.topic_authorization is not None:
        for topic, consumers in self.topic_authorization.items():
            if not isinstance(topic, str):
                raise ValueError(f"topic_authorization key must be string, got {type(topic).__name__}")
            if not isinstance(consumers, (list, set)):
                raise ValueError(f"topic_authorization value must be list/set, got {type(consumers).__name__}")
            for consumer_id in consumers:
                if not isinstance(consumer_id, str):
                    raise ValueError(f"topic_authorization consumer_id must be string, got {type(consumer_id).__name__}")
```

Key changes:
- Added validation for `consumer_authorization` field: keys must be strings, values must be lists of strings.
- Added validation for `topic_authorization` field: keys must be strings, values must be lists/sets of strings.

#### Step 3: Update _KNOWN_CONFIG_KEYS to include new fields (REQ-017)

Replace the current `_KNOWN_CONFIG_KEYS` constant (after line 97):

Current code:
```python
_KNOWN_CONFIG_KEYS = frozenset({
    "port", "db_path", "storage_dir", "offsets_dir", "deadletter_dir",
    "max_retry", "replay_batch_size", "subscriber_count", "retained_event_count",
    "publish_rate", "host", "auth_token",
    "publisher_token", "consumer_token", "operator_token", "monitoring_token",
    "admin_token", "sse_heartbeat_interval", "slow_consumer_threshold",
    "subscriber_queue_maxsize", "backlog_health_threshold",
})
```

New code:
```python
_KNOWN_CONFIG_KEYS = frozenset({
    "port", "db_path", "storage_dir", "offsets_dir", "deadletter_dir",
    "max_retry", "replay_batch_size", "subscriber_count", "retained_event_count",
    "publish_rate", "host", "auth_token",
    "publisher_token", "consumer_token", "operator_token", "monitoring_token",
    "admin_token", "sse_heartbeat_interval", "slow_consumer_threshold",
    "subscriber_queue_maxsize", "backlog_health_threshold",
    "consumer_authorization", "topic_authorization",
})
```

Key changes:
- Added `"consumer_authorization"` and `"topic_authorization"` to known config keys.

### Details

- REQ-017: Per-consumer/topic authorization fields added to EventBusConfig.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `EventBusConfig` dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/config.py | Unit: EventBusConfig validation logic | uv run pytest tests/eventbus/test_eventbus_config.py -v | New config tests pass; existing tests unchanged |
| scripts/eventbus/config.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/config.py | Type checking | uv run mypy scripts/eventbus/config.py | No new type errors |

## Completion criteria

- [ ] `consumer_authorization` field added to EventBusConfig.
- [ ] `topic_authorization` field added to EventBusConfig.
- [ ] `__post_object__()` validates new fields.
- [ ] `_KNOWN_CONFIG_KEYS` includes new fields.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Documentation updates (handled separately per REQ-011).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add new authorization fields to EventBusConfig | Pending | — | — | |
| 2 | Update __post_object__() validation for new fields | Pending | — | — | |
| 3 | Update _KNOWN_CONFIG_KEYS to include new fields | Pending | — | — | |

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
- **Requirement ID**: REQ-017
- **Source issue**: issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-203115
- **Related target files**: scripts/eventbus/config.py
