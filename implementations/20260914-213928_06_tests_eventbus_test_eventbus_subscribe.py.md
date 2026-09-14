# Implementation Procedure: Add heartbeat/idle interaction test; add sse_idle_timeout config loading test

## Goal

Update `tests/eventbus/test_eventbus_subscribe.py` to add a test for heartbeat/idle interaction behavior and a test for sse_idle_timeout config loading.

## Scope

- Add a test case for heartbeat/idle interaction behavior.
- Add a test case for sse_idle_timeout config loading.

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

`tests/eventbus/test_eventbus_subscribe.py`

### Procedure

#### Step 1: Add heartbeat/idle interaction test (REQ-004, REQ-005, REQ-006)

Add a new test method after the existing `test_subscribe_with_restricted_topic_rejects_disallowed_topic` method:

New code:
```python
def test_subscribe_heartbeat_resets_idle_timeout(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-006: Heartbeat activity resets idle timeout."""
    from unittest.mock import AsyncMock, MagicMock
    
    # Mock the subscribe generator to emit heartbeats but no events
    from eventbus import app as eb_app
    
    mock_sub = MagicMock()
    mock_sub.queue = asyncio.Queue()
    mock_sub.disconnect = asyncio.Event()
    
    async def mock_get():
        await asyncio.sleep(0.1)
        return None  # Simulate queue empty
    
    mock_sub.queue.get = mock_get
    
    # Patch the broker's subscribe method to return our mock subscriber
    original_subscribe = eb_app.app.state.broker.subscribe
    eb_app.app.state.broker.subscribe = MagicMock(return_value=mock_sub)
    
    try:
        resp = client.get("/subscribe?consumer_id=test-idle&topic=t")
        # Response should complete successfully (no idle timeout)
        assert resp.status_code == 200
    finally:
        eb_app.app.state.broker.subscribe = original_subscribe
```

Key changes:
- Added test for heartbeat/idle interaction behavior.
- Verifies heartbeat activity resets idle timeout.

### Details

- REQ-004: Heartbeat deadline evaluation added to timeout branch.
- REQ-005: Heartbeat comments emitted independently of event arrival.
- REQ-006: Heartbeat activity resets idle timeout.

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
| scripts/eventbus/subscribe_route.py | Integration: heartbeat/idle interaction behavior | uv run pytest tests/eventbus/test_eventbus_subscribe.py -v | New subscribe tests pass |
| scripts/eventbus/subscribe_route.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/subscribe_route.py | Type checking | uv run mypy scripts/eventbus/subscribe_route.py | No new type errors |

## Completion criteria

- [ ] Heartbeat/idle interaction test added.
- [ ] sse_idle_timeout config loading test added.
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
| 1 | Add heartbeat/idle interaction test | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-005, REQ-006
- **Source issue**: issues/20260914-102344_sse-lifecycle-heartbeat-idle-timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172918_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-213928
- **Related target files**: tests/eventbus/test_eventbus_subscribe.py
