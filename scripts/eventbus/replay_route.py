#!/usr/bin/env python3
"""scripts/eventbus/replay_route.py — Replay endpoint handler."""

import logging
from collections.abc import AsyncGenerator
from typing import Annotated, Any, Literal

from fastapi import Depends, Query, Request
from fastapi.responses import StreamingResponse

from eventbus.auth import Role, require_role  # noqa: PLC0415 — new module, REQ-004
from eventbus.db import fetch_events_since
from eventbus.json_utils import dumps as json_dumps
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
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _operator: Annotated[None, Depends(require_role(Role.OPERATOR))] = None,  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> Any:
    """Replay events from a given sequence number via SSE or JSON response."""
    db = get_db(request)

    def _fetch_and_count(since_seq: int, limit: int, offset: int):
        """Fetch events and count total under one lock acquisition."""
        rows: list = fetch_events_since(db, since_seq, limit=limit, offset=offset)
        total = _count_events_since(db, since_seq)
        return rows, total

    rows, total = await run_with_db_lock(
        lambda: _fetch_and_count(since_seq, limit, offset)
    )

    if fmt == "json":
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_row_to_dict(r) for r in rows],
        }

    async def _sse_gen() -> AsyncGenerator[str]:
        """Generate SSE stream events from fetched rows."""
        for row in rows:
            seq = row[0]
            data = json_dumps(_row_to_dict(row))
            yield f"id:{seq}\ndata:{data}\n\n"

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")
