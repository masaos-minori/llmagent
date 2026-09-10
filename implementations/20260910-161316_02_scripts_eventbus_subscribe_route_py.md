## Goal

Modify `scripts/eventbus/subscribe_route.py` to:
1. Pass `consumer_id` from the query param into `broker.subscribe(topics, consumer_id=...)`.
2. Translate a `ValueError` raised by `broker.subscribe()` (duplicate consumer_id rejection) into an HTTP 409 response, following the existing `ERR_EVENT_NOT_IN_DLQ` 409 pattern in `dlq_route.py`.
3. Replace `_sse_gen()`'s unconditional `await sub.queue.get()` with a race between `queue.get()` and the new disconnect signal (`asyncio.Event`) using `asyncio.wait(...)`, ending the stream on whichever completes first.

## Scope

- Modify the `subscribe()` function to pass `consumer_id` to `broker.subscribe()`.
- Add error handling for `ValueError` (duplicate consumer_id) → HTTP 409.
- Modify `_sse_gen()` to race `queue.get()` against `sub.disconnect_signal.wait()`.
- Cancel the losing task in every completion order to avoid "exception never retrieved" warnings.

## Assumptions

- The `consumer_id` parameter is already accepted as a `Query` param in the current code.
- The `ValueError` raised by `broker.subscribe()` contains the message `"duplicate consumer_id: X"` (matching the Plan's design).
- The disconnect signal is only used by the SSE generator — it does not affect other code paths.

## Design decisions

- **HTTP 409 translation**: Use `fastapi.HTTPException(status_code=409)` to translate the `ValueError` into an HTTP 409 response, following the existing `ERR_EVENT_NOT_IN_DLQ` 409 pattern in `dlq_route.py`.
- **SSE generator race**: Use `asyncio.wait({queue.get(), disconnect_signal.wait()}, return_when=asyncio.FIRST_COMPLETED)` to race between the two operations. On completion, cancel the losing task and check which one won.
- **Cancellation safety**: Ensure that both tasks are properly cancelled when one wins, to avoid "exception never retrieved" warnings.

## Alternatives considered

- **Use `asyncio.gather` instead of `asyncio.wait`**: Would require catching exceptions from both tasks. Rejected because `asyncio.wait` gives more control over which task to cancel.
- **Add a separate disconnect handler**: Would add complexity without clear benefit. Rejected because the SSE generator is the natural place to handle the disconnect signal.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

1. Modify the `subscribe()` function to pass `consumer_id` to `broker.subscribe()`.
2. Add error handling for `ValueError` (duplicate consumer_id) → HTTP 409.
3. Modify `_sse_gen()` to race `queue.get()` against `sub.disconnect_signal.wait()`.

### Method

#### Step 1: Modify the `subscribe()` function

Change lines 18-34:
```python
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.offsets import read_offset  # noqa: PLC0415

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = read_offset(cfg.offsets_dir, consumer_id)
```

to:
```python
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.offsets import read_offset  # noqa: PLC0415

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = read_offset(cfg.offsets_dir, consumer_id)

    # Register with broker, passing consumer_id for connection tracking
    try:
        sub = broker.subscribe(list(topic), consumer_id=consumer_id)
    except ValueError as exc:
        # Duplicate consumer_id rejection → HTTP 409
        raise HTTPException(
            status_code=409,
            detail=f"duplicate consumer_id: {consumer_id}",
        ) from exc
```

Wait — we also need to import `HTTPException` from FastAPI. Let me revise:

First, update the imports at the top:
```python
import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from eventbus.json_utils import dumps as json_dumps
from eventbus.route_helpers import _row_to_dict, get_broker, get_db, run_with_db_lock

logger = logging.getLogger(__name__)
```

Then modify the `subscribe()` function body after the `start_seq` calculation:
```python
    # Register with broker, passing consumer_id for connection tracking
    try:
        sub = broker.subscribe(list(topic), consumer_id=consumer_id)
    except ValueError as exc:
        # Duplicate consumer_id rejection → HTTP 409
        raise HTTPException(
            status_code=409,
            detail=f"duplicate consumer_id: {consumer_id}",
        ) from exc
```

#### Step 2: Modify `_sse_gen()` to race `queue.get()` against disconnect signal

Change lines 36-88:
```python
    async def _sse_gen() -> AsyncGenerator[str]:
        """Generate Server-Sent Events by replaying from SQLite and streaming live broker events."""
        # Step 1: register with broker BEFORE replay to capture events published during replay
        sub = broker.subscribe(list(topic))
        # must be set before any await below, so the except CancelledError handler
        # below always has a value, even if cancelled during the replay fetch
        replay_ceil = start_seq
        try:
            # Step 2: replay from SQLite
            def _fetch_replay() -> list[Any]:
                """Fetch replay events from SQLite filtered by topic and sequence."""
                if topic:
                    placeholders = ",".join("?" for _ in topic)
                    return list(
                        db.execute(
                            f"SELECT seq, event_id, topic, payload, producer, published_at"
                            f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq",  # nosec B608 — all values bound via ? placeholders
                            (start_seq, *topic),
                        ).fetchall()
                    )
                return list(
                    db.execute(
                        "SELECT seq, event_id, topic, payload, producer, published_at"
                        " FROM events WHERE seq > ? ORDER BY seq",
                        (start_seq,),
                    ).fetchall()
                )

            rows = await run_with_db_lock(_fetch_replay)
            for row in rows:
                data = json_dumps(_row_to_dict(row))
                yield f"data: {data}\n\n"
                replay_ceil = row["seq"]

            # Step 3: live delivery from broker queue
            while True:
                event = await sub.queue.get()
                if event is None:  # shutdown sentinel
                    break
                if event["seq"] <= replay_ceil:
                    continue  # duplicate from replay; discard
                data = json_dumps(event)
                yield f"data: {data}\n\n"

        except asyncio.CancelledError:
            logger.info(
                "subscribe disconnected consumer=%s seq=%d",
                consumer_id,
                replay_ceil,
            )
        finally:
            broker.unsubscribe(sub)
```

to:
```python
    async def _sse_gen() -> AsyncGenerator[str]:
        """Generate Server-Sent Events by replaying from SQLite and streaming live broker events."""
        # Step 1: register with broker BEFORE replay to capture events published during replay
        # (subscriber registration already done above, before this generator starts)
        # must be set before any await below, so the except CancelledError handler
        # below always has a value, even if cancelled during the replay fetch
        replay_ceil = start_seq
        try:
            # Step 2: replay from SQLite
            def _fetch_replay() -> list[Any]:
                """Fetch replay events from SQLite filtered by topic and sequence."""
                if topic:
                    placeholders = ",".join("?" for _ in topic)
                    return list(
                        db.execute(
                            f"SELECT seq, event_id, topic, payload, producer, published_at"
                            f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq",  # nosec B608 — all values bound via ? placeholders
                            (start_seq, *topic),
                        ).fetchall()
                    )
                return list(
                    db.execute(
                        "SELECT seq, event_id, topic, payload, producer, published_at"
                        " FROM events WHERE seq > ? ORDER BY seq",
                        (start_seq,),
                    ).fetchall()
                )

            rows = await run_with_db_lock(_fetch_replay)
            for row in rows:
                data = json_dumps(_row_to_dict(row))
                yield f"data: {data}\n\n"
                replay_ceil = row["seq"]

            # Step 3: live delivery from broker queue, racing against disconnect signal
            while True:
                # Race between receiving an event and the disconnect signal
                done, pending = await asyncio.wait(
                    [
                        asyncio.ensure_future(sub.queue.get()),
                        asyncio.ensure_future(sub.disconnect_signal.wait()),
                    ],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                # Cancel the losing task(s) to avoid "exception never retrieved" warnings
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                # Check which task completed first
                if sub.disconnect_signal in done:
                    # Disconnect signal fired — end the stream
                    logger.info(
                        "subscribe disconnected overflow consumer=%s seq=%d",
                        consumer_id,
                        replay_ceil,
                    )
                    break

                # queue.get() completed — process the event
                event = done.pop().result()
                if event is None:  # shutdown sentinel
                    break
                if event["seq"] <= replay_ceil:
                    continue  # duplicate from replay; discard
                data = json_dumps(event)
                yield f"data: {data}\n\n"

        except asyncio.CancelledError:
            logger.info(
                "subscribe disconnected consumer=%s seq=%d",
                consumer_id,
                replay_ceil,
            )
        finally:
            broker.unsubscribe(sub)
```

### Details

The key changes are:

1. **Consumer ID passthrough**: The `consumer_id` query parameter is now passed to `broker.subscribe(topics, consumer_id=...)`, enabling the broker's consumer-connection registry to track active connections.

2. **HTTP 409 translation**: When `broker.subscribe()` raises `ValueError` (duplicate consumer_id), the route layer translates it into an HTTP 409 response using `fastapi.HTTPException(status_code=409)`, following the existing `ERR_EVENT_NOT_IN_DLQ` 409 pattern in `dlq_route.py`.

3. **SSE generator race**: The unconditional `await sub.queue.get()` is replaced by a race between `queue.get()` and `disconnect_signal.wait()` using `asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)`. On completion:
   - The losing task is cancelled.
   - If the disconnect signal won, the stream ends (logging the disconnect reason).
   - If the queue got an event, it's processed normally.

4. **Cancellation safety**: Both tasks are properly cancelled when one wins, to avoid "exception never retrieved" warnings (a risk noted in the Plan's Risks section).

## Compatibility considerations

- The `consumer_id` parameter is already accepted as a `Query` param in the current code — no new parameters needed.
- The `finally: broker.unsubscribe(sub)` release path is unchanged — it still runs on cancellation, disconnect, generator failure, and shutdown.
- The SSE generator loop (`while True`) is unchanged — only the inner `event = await sub.queue.get()` is modified.

## Security considerations

- No new authentication or authorization boundaries introduced.
- SQL values are bound via `?` placeholders — no injection risk.
- The `consumer_id` parameter is validated as non-empty by the caller (not the offset read itself).

## Rollback considerations

- To rollback: restore the original two-call pattern (`_ack_event` + `write_offset`).
- The rollback restores the pre-change state where the ACK and offset writes are independent operations.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/subscribe_route.py` | Structural verification | Read file, confirm single call to `ack_event_for_consumer` | Two-call pattern replaced with single call |
| `tests/eventbus/test_eventbus_crash_ack.py` | Failure injection test | `uv run pytest tests/eventbus/test_eventbus_crash_ack.py -v` | Offset-write failure after delivery-state write leaves neither committed |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass, including retained-legacy-path tests |

## Completion criteria

- `_ack_and_offset()` calls `ack_event_for_consumer()` instead of `_ack_event()` + `write_offset()`.
- The `write_offset` import is removed.
- Return value structure `(found, newly_acked, seq)` is preserved.
- No other code paths modified.

## Out of scope

- Modifying `nack()` or `_nack_and_promote()` — not affected by this change.
- Modifying `ack_event()` route handler — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add consumer_id passthrough to subscribe() | Pending | — | — | |
| 2 | Add HTTP 409 translation for ValueError | Pending | — | — | |
| 3 | Replace queue.get() with asyncio.wait race | Pending | — | — | |
| 4 | Run validation (pytest + structural check) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: scripts/eventbus/subscribe_route.py
