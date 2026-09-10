#!/usr/bin/env python3
"""scripts/eventbus/subscribe_route.py — Subscribe endpoint handler."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from eventbus.auth import require_consumer_identity  # noqa: PLC0415 — new module, REQ-003
from eventbus.json_utils import dumps as json_dumps
from eventbus.route_helpers import _row_to_dict, get_broker, get_db, run_with_db_lock

logger = logging.getLogger(__name__)


async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    _identity: Annotated[dict, Depends(require_consumer_identity)] = {},  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.offsets import read_offset  # noqa: PLC0415

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    # Validate topic access for authenticated caller
    caller_topics = _identity.get("topics", set())
    for t in topic:
        if t not in caller_topics:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: topic '{t}' not allowed"
            )

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        # Try SQLite-backed offset first, then fall back to legacy file-based
        start_seq = _get_offset_from_sqlite(db, consumer_id)
        if start_seq == 0:
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

    async def _sse_gen() -> AsyncGenerator[str]:
        """Generate Server-Sent Events by replaying from SQLite and streaming live broker events."""
        # Subscriber registration already done above, before this generator starts
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

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")


def _get_offset_from_sqlite(
    db: Any,
    consumer_id: str,
) -> int:
    """Read the last-committed sequence offset for a consumer from the SQLite store.

    Returns 0 if no offset exists for this consumer.
    """
    try:
        row = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        if row:
            return int(row["offset"])
    except Exception:
        # Table doesn't exist yet or query failed — fall through to legacy path
        pass
    return 0
