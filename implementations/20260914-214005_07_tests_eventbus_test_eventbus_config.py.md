# Implementation Procedure: Add sse_idle_timeout config loading test; add cross-field validation test

## Goal

Update `tests/eventbus/test_eventbus_config.py` to add a test for sse_idle_timeout config loading and a test for cross-field validation between sse_idle_timeout and sse_heartbeat_interval.

## Scope

- Add a test case for sse_idle_timeout config loading.
- Add a test case for cross-field validation between sse_idle_timeout and sse_heartbeat_interval.

## Assumptions

- A: REQ-001 through REQ-003 in `scripts/eventbus/health_route.py` are implemented before this change.
- B: The health endpoint already guards broker access with `if broker is not None:` — confirmed by `health_route.py:53`.
- C: Broker properties accessed in health route (subscriber_count, max_queue_depth, slow_consumer_count, overflow_disconnect_count, duplicate_rejection_count) are all safe to call when broker is not None — confirmed by broker.py method definitions.
- D: The `DEFAULT_SSE_IDLE_TIMEOUT = 60` constant in `subscribe_route.py` is the current implicit default — confirmed by `subscribe_route.py:28`.
- E: The `getattr(cfg, "sse_idle_timeout", DEFAULT_SSE_IDLE_TIMEOUT)` pattern in `subscribe_route.py` means the config class doesn't have this field yet — confirmed by `subscribe_route.py:166`.
- F: Heartbeat is emitted only during active delivery (when events arrive) — line 204-207.
- G: Idle timeout checks `last_event_time` — line 185.

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

`tests/eventbus/test_eventbus_config.py`

### Procedure

#### Step 1: Add sse_idle_timeout config loading test (REQ-007, REQ-008)

Add a new test method after the existing `test_load_config_rejects_both_stray_keys` method:

New code:
```python
def test_load_config_accepts_sse_idle_timeout(tmp_path: Path) -> None:
    """REQ-007: sse_idle_timeout should be accepted as a known key."""
    toml_path = tmp_path / "eventbus.toml"
    toml_path.write_text(
        "port = 8015\n"
        'db_path = "/tmp/e.sqlite"\n'
        'storage_dir = "/tmp/storage"\n'
        'offsets_dir = "/tmp/offsets"\n'
        'deadletter_dir = "/tmp/deadletter"\n'
        "max_retry = 3\n"
        'auth_token = "test-token"\n'
        "sse_idle_timeout = 60.0\n"
    )
    cfg = load_config(toml_path)
    assert cfg.sse_idle_timeout == 60.0
```

Key changes:
- Added test for sse_idle_timeout config loading.
- Verifies sse_idle_timeout value is correctly loaded from TOML.

#### Step 2: Add cross-field validation test (REQ-009)

Add a new test method after the previous one:

New code:
```python
def test_cross_field_validation_sse_idle_timeout_less_than_heartbeat_interval() -> None:
    """REQ-009: Cross-field validation between sse_idle_timeout and sse_heartbeat_interval."""
    # sse_idle_timeout must be greater than sse_heartbeat_interval
    with pytest.raises(ValueError, match="sse_idle_timeout.*must be greater than"):
        EventBusConfig(
            port=8015,
            db_path="",
            storage_dir="",
            offsets_dir="",
            deadletter_dir="",
            max_retry=3,
            auth_token="test-token",
            sse_idle_timeout=30.0,  # Equal to heartbeat interval
            sse_heartbeat_interval=30.0,
        )
    
    with pytest.raises(ValueError, match="sse_idle_timeout.*must be greater than"):
        EventBusConfig(
            port=8015,
            db_path="",
            storage_dir="",
            offsets_dir="",
            deadletter_dir="",
            max_retry=3,
            auth_token="test-token",
            sse_idle_timeout=10.0,  # Less than heartbeat interval
            sse_heartbeat_interval=30.0,
        )
```

Key changes:
- Added test for cross-field validation between sse_idle_timeout and sse_heartbeat_interval.
- Verifies that sse_idle_timeout must be greater than sse_heartbeat_interval.

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

- [ ] sse_idle_timeout config loading test added.
- [ ] Cross-field validation test added.
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
| 1 | Add sse_idle_timeout config loading test | Pending | — | — | |
| 2 | Add cross-field validation test | Pending | — | — | |

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
- **Generated at**: 20260914-214005
- **Related target files**: tests/eventbus/test_eventbus_config.py
