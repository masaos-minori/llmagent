#!/usr/bin/env python3
"""scripts/eventbus/subscribe_route.py — Subscribe endpoint handler."""

import asyncio
import logging
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


async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _identity: dict = Depends(require_consumer_identity),  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.db import get_consumer_offset  # noqa: PLC0415

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    caller_topics = _identity.get("topics", set())
    for t in topic:
        if t not in caller_topics:
            raise HTTPException(
                status_code=403, detail=f"Forbidden: topic '{t}' not allowed"
            )

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = get_consumer_offset(db, consumer_id)

    try:
        sub = broker.subscribe(list(topic), consumer_id=consumer_id)
    except ConsumerAlreadyConnectedError:
        raise HTTPException(status_code=409, detail=ERR_CONSUMER_ALREADY_CONNECTED)

    async def _sse_gen() -> AsyncGenerator[str]:
        """Generate Server-Sent Events by replaying from SQLite and streaming live broker events."""
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
                        " FROM events WHERE seq > ?",
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
                get_task = asyncio.ensure_future(sub.queue.get())
                disc_task = asyncio.ensure_future(sub.disconnect.wait())
                done, pending = await asyncio.wait(
                    {get_task, disc_task}, return_when=asyncio.FIRST_COMPLETED
                )
                for p in pending:
                    p.cancel()
                if disc_task in done:
                    break
                event = get_task.result()
                if event is None:
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

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")
