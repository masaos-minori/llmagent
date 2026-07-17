#!/usr/bin/env python3
"""eventbus/replay_route.py — Replay endpoint handler."""

import logging
from typing import Any

from fastapi import Query, Request
from fastapi.responses import StreamingResponse
from shared.json_utils import dumps as json_dumps

from eventbus.db import fetch_events_since
from eventbus.route_helpers import _row_to_dict, get_db, run_with_db_lock

logger = logging.getLogger(__name__)


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
    """Replay events from a given sequence number via SSE or JSON response."""
    db = get_db(request)

    def _fetch() -> list:
        """Fetch events with seq > since_seq within limit/offset bounds."""
        rows: list = fetch_events_since(db, since_seq, limit=limit, offset=offset)
        return rows

    rows = await run_with_db_lock(_fetch)

    if fmt == "json":

        def _count() -> int:
            """Count total events with seq > since_seq for pagination."""
            return _count_events_since(db, since_seq)

        total = await run_with_db_lock(_count)
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_row_to_dict(r) for r in rows],
        }

    async def _sse_gen() -> Any:
        """Generate SSE stream events from fetched rows."""
        for row in rows:
            data = json_dumps(_row_to_dict(row))
            yield f"data: {data}\n\n"

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")
