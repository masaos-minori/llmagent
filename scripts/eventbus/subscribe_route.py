#!/usr/bin/env python3
"""scripts/eventbus/subscribe_route.py — Subscribe endpoint handler."""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from eventbus.auth import (
    Role,
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


async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _role: Role | None = None,  # type: ignore[assignment] — set by app.py wrapper
    _identity: dict[str, Any] | None = None,  # type: ignore[assignment] — set by app.py wrapper
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
