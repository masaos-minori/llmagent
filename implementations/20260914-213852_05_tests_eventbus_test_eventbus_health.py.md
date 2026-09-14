# Implementation Procedure: Add broker-unavailable degradation test; add heartbeat/idle interaction test

## Goal

Update `tests/eventbus/test_eventbus_health.py` to add a test for broker-unavailable degradation and a test for heartbeat/idle interaction behavior.

## Scope

- Add a test case for broker-unavailable degradation scenario.
- Add a test case for heartbeat/idle interaction behavior.

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

`tests/eventbus/test_eventbus_health.py`

### Procedure

#### Step 1: Add broker-unavailable degradation test (REQ-001, REQ-002, REQ-003)

Add a new test method after the existing `test_health_degraded_when_db_unavailable` method:

New code:
```python
    def test_health_broker_unavailable(self, client: TestClient) -> None:
        """Test that health endpoint returns degraded status when broker is unavailable."""
        # Simulate broker unavailability by setting broker to None
        from eventbus import app as eb_app
        
        # Save original broker reference
        original_broker = eb_app.app.state.broker
        
        # Set broker to None to simulate unavailability
        eb_app.app.state.broker = None
        
        try:
            resp = client.get("/health")
            assert resp.status_code == 503
            body = resp.json()
            assert body["status"] == "degraded"
            assert "broker_unavailable" in body["degraded_reasons"]
        finally:
            # Restore original broker reference
            eb_app.app.state.broker = original_broker
```

Key changes:
- Added test for broker-unavailable degradation scenario.
- Verifies HTTP 503 response when broker is None.
- Verifies `broker_unavailable` in degraded_reasons.

### Details

- REQ-001: `broker_unavailable` added as degraded reason when broker is None.
- REQ-002: Broker property access guarded against broker being None.
- REQ-003: Controlled HTTP 503 response ensured when broker is unavailable.

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
| scripts/eventbus/health_route.py | Unit: broker-unavailable degradation; Integration: controlled HTTP 503 | uv run pytest tests/eventbus/test_eventbus_health.py -v | New health tests pass; existing tests unchanged |
| scripts/eventbus/health_route.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/health_route.py | Type checking | uv run mypy scripts/eventbus/health_route.py | No new type errors |

## Completion criteria

- [ ] Broker-unavailable degradation test added.
- [ ] Heartbeat/idle interaction test added.
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
| 1 | Add broker-unavailable degradation test | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260914-102344_sse-lifecycle-heartbeat-idle-timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172918_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-213852
- **Related target files**: tests/eventbus/test_eventbus_health.py
