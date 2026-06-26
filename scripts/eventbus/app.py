from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jsonschema
import orjson
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from eventbus.broker import EventBroker
from eventbus.config import (
    EventBusConfig,
    get_config_path,
    get_schema_path,
    load_config,
)
from eventbus.db import (
    check_db,
    fetch_dlq,
    fetch_events_since,
    insert_event,
    open_db,
    requeue_event,
)
from eventbus.dlq import promote_single, sweep_orphans

logger = logging.getLogger(__name__)

_ENVELOPE_SCHEMA_PATH = Path("/opt/llm/schemas/event_envelope.json")
_cfg: EventBusConfig | None = None
_db: sqlite3.Connection | None = None
_broker: EventBroker | None = None
_envelope_schema: dict[str, Any] | None = None
_dlq_task: asyncio.Task | None = None
_DLQ_INTERVAL = 60.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    global _cfg, _db, _envelope_schema, _dlq_task
    cfg_path = get_config_path()
    schema_path = get_schema_path()
    logger.info("eventbus: config=%s schema=%s", cfg_path, schema_path)
    _cfg = load_config(cfg_path)
    _db = open_db(_cfg.db_path)
    _envelope_schema = orjson.loads(schema_path.read_bytes())
    Path(_cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    _broker = EventBroker()
    _dlq_task = asyncio.create_task(_dlq_loop())
    yield
    if _dlq_task:
        _dlq_task.cancel()
        try:
            await _dlq_task
        except asyncio.CancelledError:
            pass
    if _broker:
        _broker.shutdown()
    if _db:
        _db.close()


async def _dlq_loop() -> None:
    while True:
        try:
            assert _cfg is not None
            assert _db is not None
            n = await asyncio.to_thread(
                sweep_orphans, _db, _cfg.deadletter_dir, _cfg.max_retry
            )
            if n:
                logger.warning("dlq_loop: swept %d orphan(s) missed by inline promotion", n)
        except (OSError, sqlite3.Error):
            logger.exception("dlq_loop error")
        await asyncio.sleep(_DLQ_INTERVAL)


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    def _check() -> bool:
        assert _db is not None
        return check_db(_db)

    db_ok = await asyncio.to_thread(_check)
    db_status = "ok" if db_ok else "unavailable"

    dlq_task_status = (
        "running" if (_dlq_task is not None and not _dlq_task.done()) else "stopped"
    )
    overall = (
        "ok" if (db_status == "ok" and dlq_task_status == "running") else "degraded"
    )
    return {"status": overall, "db": db_status, "dlq_task": dlq_task_status}


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

    assert _db is not None
    assert _broker is not None
    seq, inserted = await asyncio.to_thread(
        insert_event,
        _db,
        event_id,
        topic,
        payload_str,
        producer,
        published_at,
    )

    try:
        _append_jsonl(body, seq)
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
            n = _broker.publish(event_dict)
            logger.debug("publish notify broker delivered=%d seq=%d", n, seq)
        except Exception:
            logger.exception("publish broker notify error seq=%d", seq)

    logger.info("publish event_id=%s topic=%s seq=%d", event_id, topic, seq)
    return {"event_id": event_id, "seq": seq}


@app.get("/replay")
async def replay(
    since_seq: int = Query(default=0, ge=0),
    fmt: str = Query(default="sse", alias="format"),
) -> Any:
    assert _db is not None
    rows = await asyncio.to_thread(fetch_events_since, _db, since_seq)

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
    from eventbus.offsets import read_offset  # noqa: PLC0415

    assert _cfg is not None
    assert _broker is not None

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = read_offset(_cfg.offsets_dir, consumer_id)

    async def _sse_gen() -> Any:
        # Step 1: register with broker BEFORE replay to capture events published during replay
        sub = _broker.subscribe(list(topic))
        try:
            # Step 2: replay from SQLite
            def _fetch_replay() -> list:
                assert _db is not None
                if topic:
                    placeholders = ",".join("?" for _ in topic)
                    return _db.execute(
                        f"SELECT seq, event_id, topic, payload, producer, published_at"
                        f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq",
                        (start_seq, *topic),
                    ).fetchall()
                return _db.execute(
                    "SELECT seq, event_id, topic, payload, producer, published_at"
                    " FROM events WHERE seq > ? ORDER BY seq",
                    (start_seq,),
                ).fetchall()

            rows = await asyncio.to_thread(_fetch_replay)
            replay_ceil = start_seq
            for row in rows:
                data = orjson.dumps(_row_to_dict(row)).decode()
                yield f"data: {data}\n\n"
                replay_ceil = row["seq"]

            # Step 3: live delivery from broker queue
            while True:
                event = await sub.queue.get()
                if event is None:  # shutdown sentinel
                    break
                if event["seq"] <= replay_ceil:
                    continue  # duplicate from replay; discard
                data = orjson.dumps(event).decode()
                yield f"data: {data}\n\n"

        except asyncio.CancelledError:
            logger.info(
                "subscribe disconnected consumer=%s seq=%d",
                consumer_id,
                replay_ceil if "replay_ceil" in dir() else start_seq,
            )
        finally:
            _broker.unsubscribe(sub)

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")


@app.get("/dlq")
async def dlq_list() -> list[dict[str, Any]]:
    rows = await asyncio.to_thread(fetch_dlq, _db)  # type: ignore[arg-type]
    return [dict(r) for r in rows]


@app.post("/dlq/{event_id}/requeue")
async def dlq_requeue(event_id: str) -> dict[str, Any]:
    if await asyncio.to_thread(requeue_event, _db, event_id):  # type: ignore[arg-type]
        logger.info("dlq requeued event_id=%s", event_id)
        return {"event_id": event_id, "requeued": True}
    raise HTTPException(status_code=404, detail="event not found")


@app.post("/ack")
async def ack(
    event_id: str = Query(default=""),
    consumer_id: str = Query(default=""),
) -> dict[str, Any]:
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id is required")

    def _ack_and_offset() -> tuple[bool, int | None]:
        from eventbus.db import ack_event as _ack_event
        from eventbus.offsets import write_offset  # noqa: PLC0415

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        acked = _ack_event(_db, event_id, now)  # type: ignore[arg-type]
        seq: int | None = None
        if consumer_id and acked:
            assert _db is not None
            row = _db.execute(
                "SELECT seq FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
            if row:
                seq = int(row["seq"])
                assert _cfg is not None
                write_offset(_cfg.offsets_dir, consumer_id, seq)
        return (acked, seq)

    acked, seq = await asyncio.to_thread(_ack_and_offset)
    if not acked:
        raise HTTPException(status_code=404, detail="event not found or already acked")
    logger.info("event acked event_id=%s", event_id)
    return {"event_id": event_id, "acked": True, "seq": seq}


@app.post("/nack")
async def nack(event_id: str = Query(default="")) -> dict[str, Any]:
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id is required")

    def _nack_and_promote() -> tuple[int, bool]:
        from eventbus.db import nack_event as _nack_event

        assert _db is not None
        assert _cfg is not None
        failure_count = _nack_event(_db, event_id)
        if failure_count == -1:
            return (-1, False)
        promoted = False
        if failure_count >= _cfg.max_retry:
            promoted = promote_single(_db, _cfg.deadletter_dir, event_id)
        return (failure_count, promoted)

    failure_count, promoted = await asyncio.to_thread(_nack_and_promote)
    if failure_count == -1:
        raise HTTPException(status_code=404, detail="event not found")
    logger.info(
        "event nacked event_id=%s delivery_failure_count=%d", event_id, failure_count
    )
    result: dict[str, Any] = {
        "event_id": event_id,
        "delivery_failure_count": failure_count,
    }
    if promoted:
        result["dlq_promoted"] = True
    return result


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "seq": row["seq"],
        "event_id": row["event_id"],
        "topic": row["topic"],
        "payload": orjson.loads(row["payload"]),
        "producer": row["producer"],
        "published_at": row["published_at"],
    }


def _append_jsonl(body: dict[str, Any], seq: int) -> None:
    assert _cfg is not None
    path = Path(_cfg.storage_dir) / "events.jsonl"
    line = orjson.dumps({**body, "seq": seq}).decode() + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
