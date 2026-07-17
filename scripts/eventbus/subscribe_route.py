#!/usr/bin/env python3
"""eventbus/subscribe_route.py — Subscribe endpoint handler."""

import asyncio
import logging
from typing import Any

from fastapi import Query, Request
from fastapi.responses import StreamingResponse
from shared.json_utils import dumps as json_dumps

from eventbus.route_helpers import _row_to_dict, get_broker, get_db, run_with_db_lock

logger = logging.getLogger(__name__)


async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
) -> Any:
    from eventbus.offsets import read_offset  # noqa: PLC0415

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = read_offset(cfg.offsets_dir, consumer_id)

    async def _sse_gen() -> Any:
        # Step 1: register with broker BEFORE replay to capture events published during replay
        sub = broker.subscribe(list(topic))
        try:
            # Step 2: replay from SQLite
            def _fetch_replay() -> list[Any]:
                """Fetch replay events from SQLite filtered by topic and sequence."""
                if topic:
                    placeholders = ",".join("?" for _ in topic)
                    return list(
                        db.execute(
                            f"SELECT seq, event_id, topic, payload, producer, published_at"
                            f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq",
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
            replay_ceil = start_seq
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
                replay_ceil if "replay_ceil" in dir() else start_seq,
            )
        finally:
            broker.unsubscribe(sub)

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")
