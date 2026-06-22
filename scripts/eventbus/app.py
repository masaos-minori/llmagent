from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import jsonschema
import orjson
from fastapi import FastAPI, HTTPException, Request

from eventbus.config import EventBusConfig, load_config
from eventbus.db import open_db

logger = logging.getLogger(__name__)

_ENVELOPE_SCHEMA_PATH = Path("/opt/llm/schemas/event_envelope.json")
_cfg: EventBusConfig | None = None
_db: sqlite3.Connection | None = None
_envelope_schema: dict[str, Any] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    global _cfg, _db, _envelope_schema
    _cfg = load_config()
    _db = open_db(_cfg.db_path)
    _envelope_schema = orjson.loads(_ENVELOPE_SCHEMA_PATH.read_bytes())
    Path(_cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    yield
    if _db:
        _db.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/publish")
async def publish(request: Request) -> dict[str, Any]:
    body: dict[str, Any] = await request.json()
    try:
        jsonschema.validate(body, _envelope_schema)
    except jsonschema.ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)

    event_id: str = body["event_id"]
    topic: str = body["topic"]
    payload_str: str = orjson.dumps(body["payload"]).decode()
    producer: str = body["producer"]
    published_at: str = body["published_at"]

    cur = _db.execute(  # type: ignore[union-attr]
        "INSERT OR IGNORE INTO events"
        " (event_id, topic, payload, producer, published_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (event_id, topic, payload_str, producer, published_at),
    )
    _db.commit()  # type: ignore[union-attr]

    seq: int = (
        cur.lastrowid
        if (cur.rowcount > 0 and cur.lastrowid is not None)
        else _get_seq(event_id)
    )

    _append_jsonl(body, seq)
    logger.info("publish event_id=%s topic=%s seq=%d", event_id, topic, seq)
    return {"event_id": event_id, "seq": seq}


def _get_seq(event_id: str) -> int:
    row = _db.execute(  # type: ignore[union-attr]
        "SELECT seq FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    return int(row["seq"]) if row else 0


def _append_jsonl(body: dict[str, Any], seq: int) -> None:
    assert _cfg is not None
    path = Path(_cfg.storage_dir) / "events.jsonl"
    line = orjson.dumps({**body, "seq": seq}).decode() + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
