# Implementation Procedure: Add heartbeat deadline evaluation; emit heartbeats independently of events; define heartbeat-idle interaction semantics

## Goal

Update `scripts/eventbus/subscribe_route.py` to add heartbeat deadline evaluation in the timeout branch of the live-delivery loop, emit heartbeats independently of event arrival, and define how heartbeat activity interacts with the idle timeout.

## Scope

- Evaluate the heartbeat deadline in the timeout branch of the live-delivery loop.
- Emit heartbeat comments independently of event arrival.
- Define how heartbeat activity interacts with the idle timeout.

## Assumptions

- A: REQ-004 through REQ-006 in `scripts/eventbus/subscribe_route.py` are implemented before this change.
- B: The `DEFAULT_SSE_IDLE_TIMEOUT = 60` constant in `subscribe_route.py` is the current implicit default — confirmed by `subscribe_route.py:28`.
- C: The `getattr(cfg, "sse_idle_timeout", DEFAULT_SSE_IDLE_TIMEOUT)` pattern in `subscribe_route.py` means the config class doesn't have this field yet — confirmed by `subscribe_route.py:166`.
- D: The current heartbeat is emitted only during active delivery (when events arrive) — line 204-207.
- E: Idle timeout checks `last_event_time` — line 185.

## Design decisions

- **Heartbeat resets idle timeout**: If a heartbeat comment is emitted within the idle window, the connection is considered active and the idle timer resets. This prevents premature disconnection of clients that are connected but receiving no events.
- **Idle timeout applies independently of heartbeat**: The idle timeout is evaluated in the timeout branch of the live-delivery loop (REQ-004). When no events arrive AND no heartbeat was recently emitted, the connection is eligible for idle timeout.
- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Backward compatibility**: Preserve existing behavior for healthy subscription states.

## Alternatives considered

- **Keep heartbeat-only during active delivery**: Continue emitting heartbeats only during active delivery. This was rejected because it doesn't provide idle connection keepalive.
- **Separate heartbeat mechanism**: Create a separate background task for heartbeat emission. This adds complexity without security benefit.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original heartbeat emission logic.
- The revert is mechanical — no semantic changes beyond restoring original code structure.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

#### Step 1: Replace the live-delivery loop with unified heartbeat/idle logic (REQ-004, REQ-005, REQ-006)

Replace the current live-delivery loop (lines 169-207):

Current code:
```python
            while True:
                get_task = asyncio.ensure_future(sub.queue.get())
                disc_task = asyncio.ensure_future(sub.disconnect.wait())
                done, pending = await asyncio.wait(
                    {get_task, disc_task},
                    timeout=1.0,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for p in pending:
                    p.cancel()
                if disc_task in done:
                    break
                if not done:
                    if await request.is_disconnected():
                        break
                    # REQ-001: Check idle timeout before continuing
                    if time.time() - last_event_time > idle_timeout:
                        logger.info(
                            "subscribe idle timeout exceeded consumer=%s timeout=%.1f",
                            consumer_id,
                            idle_timeout,
                        )
                        break
                    continue
                event = get_task.result()
                if event is None:
                    break
                if event["seq"] <= replay_ceil:
                    continue  # duplicate from replay; discard
                data = json_dumps(event)
                # REQ-002: Emit id: field alongside data: field
                yield f"id:{event['seq']}\ndata:{data}\n\n"
                # REQ-001: Update last event time after successful delivery
                last_event_time = time.time()
                # REQ-001: Periodic heartbeat during active delivery
                now = time.time()
                if now - last_heartbeat_time >= heartbeat_interval:
                    yield ": heartbeat\n\n"
                    last_heartbeat_time = now
```

New code:
```python
            while True:
                get_task = asyncio.ensure_future(sub.queue.get())
                disc_task = asyncio.ensure_future(sub.disconnect.wait())
                done, pending = await asyncio.wait(
                    {get_task, disc_task},
                    timeout=1.0,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for p in pending:
                    p.cancel()
                if disc_task in done:
                    break
                if not done:
                    if await request.is_disconnected():
                        break
                    # REQ-004: Evaluate heartbeat deadline in timeout branch
                    now = time.time()
                    elapsed_since_heartbeat = now - last_heartbeat_time
                    elapsed_since_event = now - last_event_time
                    
                    # REQ-005: Emit heartbeat if deadline reached (independent of event arrival)
                    if elapsed_since_heartbeat >= heartbeat_interval:
                        yield ": heartbeat\n\n"
                        last_heartbeat_time = now
                    
                    # REQ-006: Heartbeat activity resets idle timeout
                    # Use the later of last_event_time and last_heartbeat_time as the effective last activity time
                    last_activity_time = max(last_event_time, last_heartbeat_time)
                    if elapsed_since_event > idle_timeout:
                        logger.info(
                            "subscribe idle timeout exceeded consumer=%s timeout=%.1f",
                            consumer_id,
                            idle_timeout,
                        )
                        break
                    continue
                event = get_task.result()
                if event is None:
                    break
                if event["seq"] <= replay_ceil:
                    continue  # duplicate from replay; discard
                data = json_dumps(event)
                # REQ-002: Emit id: field alongside data: field
                yield f"id:{event['seq']}\ndata:{data}\n\n"
                # REQ-001: Update last event time after successful delivery
                last_event_time = time.time()
                # REQ-001: Periodic heartbeat during active delivery
                now = time.time()
                if now - last_heartbeat_time >= heartbeat_interval:
                    yield ": heartbeat\n\n"
                    last_heartbeat_time = now
```

Key changes:
- Added heartbeat deadline evaluation in timeout branch (REQ-004).
- Added heartbeat emission independent of event arrival (REQ-005).
- Added heartbeat-idle interaction semantics: heartbeat activity resets idle timeout (REQ-006).

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

- Revert requires restoring original heartbeat emission logic.
- The revert is mechanical — no semantic changes beyond restoring original code structure.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/subscribe_route.py | Integration: heartbeat/idle interaction behavior | uv run pytest tests/eventbus/test_eventbus_subscribe.py -v | New subscribe tests pass |
| scripts/eventbus/subscribe_route.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/subscribe_route.py | Type checking | uv run mypy scripts/eventbus/subscribe_route.py | No new type errors |

## Completion criteria

- [ ] Heartbeat deadline evaluation added to timeout branch.
- [ ] Heartbeat comments emitted independently of event arrival.
- [ ] Heartbeat activity resets idle timeout.
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
| 1 | Replace live-delivery loop with unified heartbeat/idle logic | Pending | — | — | |

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
- **Generated at**: 20260914-213138
- **Related target files**: scripts/eventbus/subscribe_route.py
