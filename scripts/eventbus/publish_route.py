#!/usr/bin/env python3
"""scripts/eventbus/publish_route.py — Publish endpoint handler."""

import logging
import os
from pathlib import Path
from typing import Any

import jsonschema
from fastapi import HTTPException, Request

from eventbus.db import insert_event
from eventbus.json_utils import dumps as json_dumps
from eventbus.route_helpers import (
    ERR_EVENT_CONFLICT,
    get_broker,
    get_config,
    get_db,
    run_with_db_lock,
)

logger = logging.getLogger(__name__)


async def publish(request: Request) -> dict[str, Any]:
    """Publish an event after validating its envelope against the configured schema."""
    body: dict[str, Any] = await request.json()
    try:
        jsonschema.validate(body, request.app.state.envelope_schema)
    except jsonschema.ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)

    event_id: str = body["event_id"]
    topic: str = body["topic"]
    payload_str: str = json_dumps(body["payload"])
    producer: str = body["producer"]
    published_at: str = body["published_at"]

    db = get_db(request)
    broker = get_broker(request)

    def _insert() -> tuple[int | None, bool, str]:
        """Insert the event into the database under the DB lock."""
        insert_result: tuple[int | None, bool, str] = insert_event(
            db,
            event_id,
            topic,
            payload_str,
            producer,
            published_at,
        )
        return insert_result

    seq, inserted, status = await run_with_db_lock(_insert)

    # Handle conflict before JSONL append
    if status == "conflict":
        raise HTTPException(status_code=409, detail=ERR_EVENT_CONFLICT)

    # Only append JSONL for newly inserted events
    if inserted:
        try:
            cfg = get_config(request)
            path = Path(cfg.storage_dir) / "events.jsonl"
            line = json_dumps({**body, "seq": seq}) + "\n"
            with path.open("a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
        except OSError as exc:
            logger.warning(
                "eventbus: JSONL append failed (event still committed): %s", exc
            )

    if inserted:
        event_dict = {
            "seq": seq,
            "event_id": event_id,
            "topic": topic,
            "payload": body["payload"],
            "producer": producer,
            "published_at": published_at,
        }
        try:
            n = broker.publish(event_dict)
            logger.debug("publish notify broker delivered=%d seq=%d", n, seq)
        except Exception:
            logger.exception("publish broker notify error seq=%d", seq)

    logger.info("publish event_id=%s topic=%s seq=%d", event_id, topic, seq)
    return {"event_id": event_id, "seq": seq}
