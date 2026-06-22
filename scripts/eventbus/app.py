from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import jsonschema
import orjson
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

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


@app.get("/replay")
async def replay(
    since_seq: int = Query(default=0, ge=0),
    fmt: str = Query(default="sse", alias="format"),
) -> Any:
    rows = _db.execute(  # type: ignore[union-attr]
        "SELECT seq, event_id, topic, payload, producer, published_at"
        " FROM events WHERE seq > ? ORDER BY seq",
        (since_seq,),
    ).fetchall()

    if fmt == "json":
        return [_row_to_dict(r) for r in rows]

    async def _sse_gen() -> Any:
        for row in rows:
            data = orjson.dumps(_row_to_dict(row)).decode()
            yield f"data: {data}\n\n"

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")


@app.get("/subscribe")
async def subscribe(
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
) -> Any:
    from eventbus.offsets import (
        read_offset,  # noqa: PLC0415 — deferred to avoid circular at module load
    )

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        assert _cfg is not None
        start_seq = read_offset(_cfg.offsets_dir, consumer_id)

    assert _cfg is not None
    interval = _cfg.poll_interval_ms / 1000.0

    async def _sse_gen() -> Any:
        current_seq = start_seq
        try:
            while True:
                if topic:
                    placeholders = ",".join("?" for _ in topic)
                    rows = _db.execute(  # type: ignore[union-attr]
                        f"SELECT seq, event_id, topic, payload, producer, published_at"  # noqa: UP032
                        f" FROM events WHERE seq > ? AND topic IN ({placeholders})"
                        f" ORDER BY seq",
                        (current_seq, *topic),
                    ).fetchall()
                else:
                    rows = _db.execute(  # type: ignore[union-attr]
                        "SELECT seq, event_id, topic, payload, producer, published_at"
                        " FROM events WHERE seq > ? ORDER BY seq",
                        (current_seq,),
                    ).fetchall()

                for row in rows:
                    data = orjson.dumps(_row_to_dict(row)).decode()
                    yield f"data: {data}\n\n"
                    current_seq = row["seq"]

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info(
                "subscribe disconnected consumer=%s seq=%d", consumer_id, current_seq
            )
            if consumer_id:
                from eventbus.offsets import write_offset  # noqa: PLC0415

                assert _cfg is not None
                write_offset(_cfg.offsets_dir, consumer_id, current_seq)

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "seq": row["seq"],
        "event_id": row["event_id"],
        "topic": row["topic"],
        "payload": orjson.loads(row["payload"]),
        "producer": row["producer"],
        "published_at": row["published_at"],
    }


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
