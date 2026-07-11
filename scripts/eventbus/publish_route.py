#!/usr/bin/env python3
"""eventbus/publish_route.py — Publish endpoint handler."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import jsonschema
import orjson
from eventbus.db import get_db_lock, insert_event
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


async def publish(request: Request) -> dict[str, Any]:
    body: dict[str, Any] = await request.json()
    try:
        jsonschema.validate(body, request.app.state.envelope_schema)
    except jsonschema.ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)

    event_id: str = body["event_id"]
    topic: str = body["topic"]
    payload_str: str = orjson.dumps(body["payload"]).decode()
    producer: str = body["producer"]
    published_at: str = body["published_at"]

    db = request.app.state.db
    assert db is not None
    broker = request.app.state.broker
    assert broker is not None

    def _insert() -> tuple[int, bool]:
        with get_db_lock():
            insert_result: tuple[int, bool] = insert_event(
                db,
                event_id,
                topic,
                payload_str,
                producer,
                published_at,
            )
            return insert_result

    seq, inserted = await asyncio.to_thread(_insert)

    try:
        cfg = request.app.state.config
        assert cfg is not None
        path = Path(cfg.storage_dir) / "events.jsonl"
        line = orjson.dumps({**body, "seq": seq}).decode() + "\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
    except OSError as exc:
        logger.warning("eventbus: JSONL append failed (event still committed): %s", exc)

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
