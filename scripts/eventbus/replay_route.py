#!/usr/bin/env python3
"""eventbus/replay_route.py — Replay endpoint handler."""

import asyncio
import logging
from typing import Any

import orjson
from eventbus.db import fetch_events_since, get_db_lock
from eventbus.route_helpers import get_db
from fastapi import Query, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {
        "seq": row["seq"],
        "event_id": row["event_id"],
        "topic": row["topic"],
        "payload": orjson.loads(row["payload"]),
        "producer": row["producer"],
        "published_at": row["published_at"],
    }


def _count_events_since(conn: Any, since_seq: int) -> int:
    """Return the total count of events with seq > since_seq."""
    row = conn.execute(
        "SELECT COUNT(*) FROM events WHERE seq > ?", (since_seq,)
    ).fetchone()
    return int(row[0]) if row else 0


async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: str = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> Any:
    db = get_db(request)

    def _fetch() -> list:
        with get_db_lock():
            rows: list = fetch_events_since(db, since_seq, limit=limit, offset=offset)
            return rows

    rows = await asyncio.to_thread(_fetch)

    if fmt == "json":

        def _count() -> int:
            with get_db_lock():
                return _count_events_since(db, since_seq)

        total = await asyncio.to_thread(_count)
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_row_to_dict(r) for r in rows],
        }

    async def _sse_gen() -> Any:
        for row in rows:
            data = orjson.dumps(_row_to_dict(row)).decode()
            yield f"data: {data}\n\n"

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")
