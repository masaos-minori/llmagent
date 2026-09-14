# Implementation Procedure: Verify EventBus's fail-closed behavior for missing config; confirm CI-005 resolution

## Goal

Update `scripts/eventbus/config.py` to verify EventBus's fail-closed behavior for missing config and confirm CI-005 resolution.

## Scope

- Verify EventBus's fail-closed behavior for missing config.
- Confirm CI-005 as resolved for EventBus specifically.

## Assumptions

- A: The existing `scripts/eventbus/audit.py` module provides the infrastructure for structured audit logging — confirmed by `audit.py:45-145`.
- B: The `log_auth_failure()` and `log_privileged_action()` functions already exist with the correct signature — confirmed by `audit.py:94-145`.
- C: The `_build_audit_record()` function accepts `consumer_id`, `route`, `target`, `outcome`, `error_type`, and optional `detail` — confirmed by `audit.py:59-91`.
- D: The `X-Request-Id` header is already injected by the auth middleware — confirmed by `auth.py:276-281`.
- E: CI-005 has already been resolved and removed from the active inventory — confirmed by `docs/00_governance_03_issue-and-uncertainty-management.md:313-315`.

## Design decisions

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

#### Step 1: Verify EventBus's fail-closed behavior for missing config (REQ-005, REQ-006)

Read the current `load_config()` function to verify fail-closed behavior:

Current code (lines 163-230):
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

    # Validate per-role tokens: at least one must be configured
    if not any(
        [
            data.get("consumer_token"),
            data.get("operator_token"),
            data.get("admin_token"),
        ]
    ):
        raise ValueError("At least one per-role token must be configured")

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
def load_config(path: Path | None = None) -> EventBusConfig:
    """Load and validate the EventBus TOML configuration file. Callers must always pass get_config_path()'s return value — this function does not itself restrict which path is read; see tests/eventbus/test_eventbus_config.py for the call-site regression test that locks this invariant."""
    p = path or _DEFAULT_CONFIG_PATH
    
    # NEW: Fail-closed behavior for missing config file
    if not p.exists():
        raise FileNotFoundError(
            f"eventbus config file not found: {p}. "
            "This is a critical error — the service cannot start without configuration."
        )
    
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

    # Validate per-role tokens: at least one must be configured
    if not any(
        [
            data.get("consumer_token"),
            data.get("operator_token"),
            data.get("admin_token"),
        ]
    ):
        raise ValueError("At least one per-role token must be configured")

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

Key changes:
- Added fail-closed check for missing config file before attempting to load it.
- Raises `FileNotFoundError` when the config file doesn't exist.

### Details

- REQ-005: CI-005 scope reviewed against EventBus's actual configuration-loading behavior.
- REQ-006: CI-005 confirmed as resolved for EventBus specifically.

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

- [ ] Fail-closed check added for missing config file.
- [ ] CI-005 confirmed as resolved for EventBus specifically.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-010).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify EventBus's fail-closed behavior for missing config | Pending | — | — | |

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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/20260914-102405_eventbus05_structured-auth-audit-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-173340_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-225449
- **Related target files**: scripts/eventbus/config.py
