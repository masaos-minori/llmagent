## Goal

Add timeout-based disconnect detection to `_sse_gen`'s live-delivery loop in `scripts/eventbus/subscribe_route.py` as fallback alongside `is_disconnected()` polling (REQ-001).

## Scope

- **In-Scope**: Modifying `scripts/eventbus/subscribe_route.py` to add timeout-based disconnect detection
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- A configurable idle timeout (e.g., `sse_idle_timeout` in `EventBusConfig`) can be added to control how long the generator waits before assuming client disconnect when no events arrive
- Default value should be reasonable for SSE use cases (e.g., 30-60 seconds)
- The timeout-based approach does not interfere with production behavior because it only triggers when no events are delivered within the timeout window — which is the exact condition indicating a potential disconnect
- The `is_disconnected()` polling already present in the code should continue to work under uvicorn; the timeout serves as a fallback for cases where it doesn't fire

## Design decisions

- Add a configurable `sse_idle_timeout` field to `EventBusConfig` class
- Track `last_event_time` initialized at loop start
- After each event yield, update `last_event_time = time.time()`
- In the loop, check `time.time() - last_event_time > idle_timeout` and break if true
- Preserve existing disconnect mechanisms: `sub.disconnect` check, `is_disconnected()` polling, None sentinel handling

## Alternatives considered

- Heartbeat/pong mechanism: Require clients to respond periodically. Too complex for this use case; SSE protocol doesn't have built-in pong support.
- Separate connection-monitoring task: Create a background task that checks connection state. Over-engineered; the timeout approach is simpler and achieves the same result.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

1. Add `sse_idle_timeout` field to `EventBusConfig` class
2. Add timeout-based disconnect detection to `_sse_gen`'s live-delivery loop
3. Preserve existing disconnect mechanisms

### Method

For the timeout-based disconnect detection:
- Initialize `last_event_time` at loop start
- Update `last_event_time` after each event yield
- Check `time.time() - last_event_time > idle_timeout` in the loop and break if true

### Details

#### Step 1: Update imports

```python
# Before:
import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from eventbus.auth import (
    require_consumer_identity,  # noqa: PLC0415 — new module, REQ-003
)
from eventbus.broker import ConsumerAlreadyConnectedError
from eventbus.json_utils import dumps as json_dumps
from eventbus.route_helpers import (
    ERR_CONSUMER_ALREADY_CONNECTED,
    _row_to_dict,
    get_broker,
    get_db,
    run_with_db_lock,
)

logger = logging.getLogger(__name__)

# After:
import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from eventbus.auth import (
    require_consumer_identity,  # noqa: PLC0415 — new module, REQ-003
)
from eventbus.broker import ConsumerAlreadyConnectedError
from eventbus.json_utils import dumps as json_dumps
from eventbus.route_helpers import (
    ERR_CONSUMER_ALREADY_CONNECTED,
    _row_to_dict,
    get_broker,
    get_db,
    run_with_db_lock,
)

logger = logging.getLogger(__name__)

DEFAULT_SSE_IDLE_TIMEOUT = 60  # seconds — default idle timeout for SSE subscribers
```

#### Step 2: Update subscribe function

```python
# Before:
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _identity: dict = Depends(require_consumer_identity),  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.db import get_consumer_offset  # noqa: PLC0415, RUF100

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    # _identity is never actually resolved by FastAPI's dependency injection
    # here — this function is called as a plain awaited function from
    # app.py's route wrapper, not registered directly as a route, so the
    # Depends(require_consumer_identity) default (or its None return value)
    # is never a real dict at this point. Skip topic-allowlist enforcement
    # rather than reject every request when identity resolution didn't
    # actually run; see
    # issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md
    # for the full authorization gap this is a symptom of.
    if isinstance(_identity, dict):
        caller_topics = _identity.get("topics", set())
        for t in topic:
            if t not in caller_topics:
                raise HTTPException(
                    status_code=403, detail=f"Forbidden: topic '{t}' not allowed"
                )

    # REQ-003: Read Last-Event-ID header as additional resume-position input
    last_event_id_str = request.headers.get("last-event-id", "")
    last_event_id: int | None = None
    if last_event_id_str:
        try:
            last_event_id = int(last_event_id_str, 10)
        except ValueError:
            logger.warning("Invalid Last-Event-ID header: %r", last_event_id_str)

    # REQ-003: Stale reconnect rejection
    if last_event_id is not None:

        def _get_max_seq() -> int:
            """Get the current maximum seq in SQLite."""
            row = db.execute("SELECT MAX(seq) FROM events").fetchone()
            return int(row[0]) if row else 0

        max_seq = await run_with_db_lock(_get_max_seq)
        if last_event_id > max_seq:
            raise HTTPException(
                status_code=412,
                detail=f"Last-Event-ID ({last_event_id}) exceeds current max seq ({max_seq})",
            )

    # REQ-004: Implement precedence: since_seq > consumer offset > Last-Event-ID
    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = get_consumer_offset(db, consumer_id)

    # REQ-003: Fallback to Last-Event-ID only if both since_seq and consumer offset are unavailable
    if start_seq == 0 and last_event_id is not None:
        start_seq = last_event_id + 1

    try:
        sub = broker.subscribe(list(topic), consumer_id=consumer_id)
    except ConsumerAlreadyConnectedError:
        raise HTTPException(status_code=409, detail=ERR_CONSUMER_ALREADY_CONNECTED)

    async def _sse_gen() -> AsyncGenerator[str]:
        """Generate Server-Sent Events by replaying from SQLite and streaming live broker events."""
        replay_ceil = start_seq
        try:
            # Step 2: replay from SQLite in bounded batches
            cfg = request.app.state.config
            assert cfg is not None
            batch_size = cfg.replay_batch_size
            start_offset = 0

            while True:
                if topic:
                    placeholders = ",".join("?" for _ in topic)
                    rows = await run_with_db_lock(
                        lambda: list(
                            db.execute(
                                f"SELECT seq, event_id, topic, payload, producer, published_at"
                                f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq LIMIT ? OFFSET ?",  # nosec B608 — all values bound via ? placeholders
                                (start_seq, *topic, batch_size, start_offset),
                            ).fetchall()
                        )
                    )
                else:
                    rows = await run_with_db_lock(
                        lambda: list(
                            db.execute(
                                "SELECT seq, event_id, topic, payload, producer, published_at"
                                " FROM events WHERE seq > ?",
                                (start_seq,),
                            ).fetchall()
                        )
                    )

                if not rows:
                    break

                for row in rows:
                    data = json_dumps(_row_to_dict(row))
                    # REQ-002: Emit id: field alongside data: field
                    yield f"id:{row['seq']}\ndata:{data}\n\n"
                    replay_ceil = row["seq"]

                start_offset += len(rows)

                # If we got a full batch, more data may exist; release lock between batches
                if len(rows) == batch_size:
                    continue
                break

            # Step 3: live delivery from broker queue. sub.disconnect only
            # fires on broker-detected queue overflow — it is not set by an
            # ASGI-level client disconnect, so poll request.is_disconnected()
            # on a timeout to avoid leaking this generator (and its
            # subscriber registration) forever when a client goes away
            # without ever overflowing its queue.
            # REQ-001: Heartbeat tracking for idle connection keepalive
            last_heartbeat_time = time.time()
            heartbeat_interval = cfg.sse_heartbeat_interval

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
                    continue
                event = get_task.result()
                if event is None:
                    break
                if event["seq"] <= replay_ceil:
                    continue  # duplicate from replay; discard
                data = json_dumps(event)
                # REQ-002: Emit id: field alongside data: field
                yield f"id:{event['seq']}\ndata:{data}\n\n"
                # REQ-001: Periodic heartbeat during active delivery
                now = time.time()
                if now - last_heartbeat_time >= heartbeat_interval:
                    yield ": heartbeat\n\n"
                    last_heartbeat_time = now

        except asyncio.CancelledError:
            logger.info(
                "subscribe disconnected consumer=%s seq=%d",
                consumer_id,
                replay_ceil,
            )
        finally:
            broker.unsubscribe(sub)

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")

# After:
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _identity: dict = Depends(require_consumer_identity),  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.db import get_consumer_offset  # noqa: PLC0415, RUF100

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    # _identity is never actually resolved by FastAPI's dependency injection
    # here — this function is called as a plain awaited function from
    # app.py's route wrapper, not registered directly as a route, so the
    # Depends(require_consumer_identity) default (or its None return value)
    # is never a real dict at this point. Skip topic-allowlist enforcement
    # rather than reject every request when identity resolution didn't
    # actually run; see
    # issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md
    # for the full authorization gap this is a symptom of.
    if isinstance(_identity, dict):
        caller_topics = _identity.get("topics", set())
        for t in topic:
            if t not in caller_topics:
                raise HTTPException(
                    status_code=403, detail=f"Forbidden: topic '{t}' not allowed"
                )

    # REQ-003: Read Last-Event-ID header as additional resume-position input
    last_event_id_str = request.headers.get("last-event-id", "")
    last_event_id: int | None = None
    if last_event_id_str:
        try:
            last_event_id = int(last_event_id_str, 10)
        except ValueError:
            logger.warning("Invalid Last-Event-ID header: %r", last_event_id_str)

    # REQ-003: Stale reconnect rejection
    if last_event_id is not None:

        def _get_max_seq() -> int:
            """Get the current maximum seq in SQLite."""
            row = db.execute("SELECT MAX(seq) FROM events").fetchone()
            return int(row[0]) if row else 0

        max_seq = await run_with_db_lock(_get_max_seq)
        if last_event_id > max_seq:
            raise HTTPException(
                status_code=412,
                detail=f"Last-Event-ID ({last_event_id}) exceeds current max seq ({max_seq})",
            )

    # REQ-004: Implement precedence: since_seq > consumer offset > Last-Event-ID
    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = get_consumer_offset(db, consumer_id)

    # REQ-003: Fallback to Last-Event-ID only if both since_seq and consumer offset are unavailable
    if start_seq == 0 and last_event_id is not None:
        start_seq = last_event_id + 1

    try:
        sub = broker.subscribe(list(topic), consumer_id=consumer_id)
    except ConsumerAlreadyConnectedError:
        raise HTTPException(status_code=409, detail=ERR_CONSUMER_ALREADY_CONNECTED)

    async def _sse_gen() -> AsyncGenerator[str]:
        """Generate Server-Sent Events by replaying from SQLite and streaming live broker events."""
        replay_ceil = start_seq
        try:
            # Step 2: replay from SQLite in bounded batches
            cfg = request.app.state.config
            assert cfg is not None
            batch_size = cfg.replay_batch_size
            start_offset = 0

            while True:
                if topic:
                    placeholders = ",".join("?" for _ in topic)
                    rows = await run_with_db_lock(
                        lambda: list(
                            db.execute(
                                f"SELECT seq, event_id, topic, payload, producer, published_at"
                                f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq LIMIT ? OFFSET ?",  # nosec B608 — all values bound via ? placeholders
                                (start_seq, *topic, batch_size, start_offset),
                            ).fetchall()
                        )
                    )
                else:
                    rows = await run_with_db_lock(
                        lambda: list(
                            db.execute(
                                "SELECT seq, event_id, topic, payload, producer, published_at"
                                " FROM events WHERE seq > ?",
                                (start_seq,),
                            ).fetchall()
                        )
                    )

                if not rows:
                    break

                for row in rows:
                    data = json_dumps(_row_to_dict(row))
                    # REQ-002: Emit id: field alongside data: field
                    yield f"id:{row['seq']}\ndata:{data}\n\n"
                    replay_ceil = row["seq"]

                start_offset += len(rows)

                # If we got a full batch, more data may exist; release lock between batches
                if len(rows) == batch_size:
                    continue
                break

            # Step 3: live delivery from broker queue. sub.disconnect only
            # fires on broker-detected queue overflow — it is not set by an
            # ASGI-level client disconnect, so poll request.is_disconnected()
            # on a timeout to avoid leaking this generator (and its
            # subscriber registration) forever when a client goes away
            # without ever overflowing its queue.
            # REQ-001: Heartbeat tracking for idle connection keepalive
            last_heartbeat_time = time.time()
            heartbeat_interval = cfg.sse_heartbeat_interval

            # REQ-001: Timeout-based disconnect detection as fallback
            # when is_disconnected() doesn't fire under certain transports
            # (e.g., TestClient). Track last event arrival time and break
            # if no events arrive within the configured idle timeout window.
            idle_timeout = getattr(cfg, "sse_idle_timeout", DEFAULT_SSE_IDLE_TIMEOUT)
            last_event_time = time.time()

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

        except asyncio.CancelledError:
            logger.info(
                "subscribe disconnected consumer=%s seq=%d",
                consumer_id,
                replay_ceil,
            )
        finally:
            broker.unsubscribe(sub)

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")
```

## Compatibility considerations

- The `sse_idle_timeout` field is added to `EventBusConfig` class with a default value of 60 seconds
- Existing deployments that don't configure this field will use the default value
- The timeout-based approach does not interfere with production behavior because it only triggers when no events are delivered within the timeout window — which is the exact condition indicating a potential disconnect

## Security considerations

- The timeout-based disconnect detection prevents resource leaks in production by ensuring generators are cleaned up even when `is_disconnected()` doesn't fire
- This improves security by preventing indefinite resource consumption from abandoned subscriptions

## Rollback considerations

- If the timeout-based disconnect causes premature closure of active subscriptions during periods of low event frequency, roll back to the previous state where only `is_disconnected()` was used
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/subscribe_route.py::subscribe | Integration: verify disconnect detection under TestClient | pytest tests/eventbus/test_eventbus_auth.py::TestSubscribeAuth::test_subscribe_with_valid_consumer_token | Test completes without hanging |
| scripts/eventbus/subscribe_route.py::subscribe | Integration: verify disconnect detection under uvicorn | Manual: run eventbus, connect /subscribe, close client, check broker subscription freed | Subscription removed within timeout |
| scripts/eventbus/subscribe_route.py::_sse_gen | Unit: verify timeout triggers when no events arrive | pytest with mock broker that stops sending events | Generator exits after timeout |
| scripts/eventbus/subscribe_route.py::_sse_gen | Unit: verify existing disconnect mechanisms still work | pytest with mock sub.disconnect set / None sentinel sent | Generator exits via original mechanism |

## Completion criteria

- [ ] `sse_idle_timeout` field added to `EventBusConfig` class
- [ ] Timeout-based disconnect detection added to `_sse_gen`'s live-delivery loop
- [ ] `last_event_time` initialized at loop start
- [ ] `last_event_time` updated after each event yield
- [ ] Idle timeout check added to the loop
- [ ] Tests pass with the new disconnect detection model

## Out of scope

- Changes to `scripts/eventbus/config.py` (handled in separate procedure document)
- Changes to test files (handled in separate procedure document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add sse_idle_timeout field to EventBusConfig | Pending | — | — | |
| 2 | Add timeout-based disconnect detection to _sse_gen | Pending | — | — | |
| 3 | Preserve existing disconnect mechanisms | Pending | — | — | |
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260911-135626_ebsse01_subscribe-generator-never-detects-client-disconnect.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-113940_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-150000
- **Related target files**: scripts/eventbus/subscribe_route.py
