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
from fastapi.responses import JSONResponse, StreamingResponse

from eventbus.broker import EventBroker
from eventbus.config import (
    EventBusConfig,
    get_config_path,
    get_schema_path,
    load_config,
)
from eventbus.db import (
    check_db,
    count_dlq,
    fetch_dlq,
    fetch_events_since,
    get_db_lock,
    insert_event,
    open_db,
    requeue_event,
)
from eventbus.dlq import promote_single, sweep_orphans

logger = logging.getLogger(__name__)


def _count_events_since(conn: sqlite3.Connection, since_seq: int) -> int:
    """Return the total count of events with seq > since_seq."""
    row = conn.execute(
        "SELECT COUNT(*) FROM events WHERE seq > ?", (since_seq,)
    ).fetchone()
    return int(row[0]) if row else 0


_ENVELOPE_SCHEMA_PATH = Path("/opt/llm/schemas/event_envelope.json")
_DLQ_INTERVAL = 60.0


def _get_db(request: Request) -> sqlite3.Connection:
    db = request.app.state.db
    assert db is not None
    return db  # type: ignore[no-any-return]


def _get_broker(request: Request) -> EventBroker:
    broker = request.app.state.broker
    assert broker is not None
    return broker  # type: ignore[no-any-return]


def _get_config(request: Request) -> EventBusConfig:
    cfg = request.app.state.config
    assert cfg is not None
    return cfg  # type: ignore[no-any-return]


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    app.state.config = load_config(get_config_path())
    app.state.db = open_db(app.state.config.db_path)
    app.state.envelope_schema = orjson.loads(get_schema_path().read_bytes())
    Path(app.state.config.storage_dir).mkdir(parents=True, exist_ok=True)
    app.state.broker = EventBroker()
    app.state.dlq_task = asyncio.create_task(_dlq_loop(app))
    logger.info("eventbus starting on port=%d", app.state.config.port)
    yield
    if app.state.dlq_task:
        app.state.dlq_task.cancel()
        try:
            await app.state.dlq_task
        except asyncio.CancelledError:
            pass
    if app.state.broker:
        app.state.broker.shutdown()
    if app.state.db:
        app.state.db.close()


async def _dlq_loop(app: FastAPI) -> None:
    while True:
        try:
            cfg = app.state.config
            db = app.state.db
            assert cfg is not None
            assert db is not None

            def _sweep() -> int:
                from eventbus.db import get_db_lock  # noqa: PLC0415

                with get_db_lock():
                    return sweep_orphans(db, cfg.deadletter_dir, cfg.max_retry)

            n = await asyncio.to_thread(_sweep)
            if n:
                logger.warning(
                    "dlq_loop: swept %d orphan(s) missed by inline promotion", n
                )
        except (OSError, sqlite3.Error):
            logger.exception("dlq_loop error")
        await asyncio.sleep(_DLQ_INTERVAL)


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health(request: Request) -> JSONResponse:
    db = _get_db(request)
    broker = _get_broker(request)

    def _check() -> bool:
        with get_db_lock():
            return check_db(db)

    db_ok = await asyncio.to_thread(_check)
    db_status = "ok" if db_ok else "unavailable"

    dlq_task_status = (
        "running"
        if (
            request.app.state.dlq_task is not None
            and not request.app.state.dlq_task.done()
        )
        else "stopped"
    )

    # Broker health metrics
    active_subscribers = 0
    max_queue_depth = 0
    slow_consumers = 0
    if broker is not None:
        active_subscribers = broker.subscriber_count()
        max_queue_depth = broker.max_queue_depth()
        slow_consumers = broker.slow_consumer_count()

    degraded_reasons: list[str] = []
    if db_status != "ok":
        degraded_reasons.append("db_unavailable")
    if dlq_task_status != "running":
        degraded_reasons.append("dlq_task_stopped")
    if max_queue_depth >= 500:
        degraded_reasons.append("broker_queue_backlog_high")
    if slow_consumers > 0:
        degraded_reasons.append("slow_consumers_detected")

    overall = "ok" if not degraded_reasons else "degraded"
    status_code = 200 if overall == "ok" else 503
    return JSONResponse(
        content={
            "status": overall,
            "db": db_status,
            "dlq_task": dlq_task_status,
            "active_subscribers": active_subscribers,
            "max_queue_depth": max_queue_depth,
            "slow_consumers": slow_consumers,
            "degraded_reasons": degraded_reasons,
        },
        status_code=status_code,
    )


@app.post("/publish")
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

    db = _get_db(request)
    broker = _get_broker(request)
    def _insert() -> tuple[int, bool]:
        with get_db_lock():
            return insert_event(
                db,
                event_id,
                topic,
                payload_str,
                producer,
                published_at,
            )

    seq, inserted = await asyncio.to_thread(_insert)

    try:
        cfg = _get_config(request)
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


@app.get("/replay")
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: str = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> Any:
    db = _get_db(request)

    def _fetch() -> list:
        with get_db_lock():
            return fetch_events_since(db, since_seq, limit=limit, offset=offset)

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


@app.get("/subscribe")
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
) -> Any:
    from eventbus.offsets import read_offset  # noqa: PLC0415

    cfg = _get_config(request)
    broker = _get_broker(request)
    db = _get_db(request)

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = read_offset(cfg.offsets_dir, consumer_id)

    async def _sse_gen() -> Any:
        # Step 1: register with broker BEFORE replay to capture events published during replay
        sub = broker.subscribe(list(topic))
        try:
            # Step 2: replay from SQLite
            def _fetch_replay() -> list:
                with get_db_lock():
                    if topic:
                        placeholders = ",".join("?" for _ in topic)
                        return db.execute(
                            f"SELECT seq, event_id, topic, payload, producer, published_at"
                            f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq",
                            (start_seq, *topic),
                        ).fetchall()
                    return db.execute(
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
            broker.unsubscribe(sub)

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")


@app.get("/dlq")
async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    db = _get_db(request)

    def _dlq_count() -> int:
        with get_db_lock():
            return count_dlq(db)

    def _dlq_fetch() -> list:
        with get_db_lock():
            return fetch_dlq(db, limit=limit, offset=offset)

    total = await asyncio.to_thread(_dlq_count)
    rows = await asyncio.to_thread(_dlq_fetch)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [dict(r) for r in rows],
    }


@app.post("/dlq/{event_id}/requeue")
async def dlq_requeue(request: Request, event_id: str) -> dict[str, Any]:
    db = _get_db(request)

    def _requeue() -> bool:
        with get_db_lock():
            return requeue_event(db, event_id)

    if await asyncio.to_thread(_requeue):
        logger.info("dlq requeued event_id=%s", event_id)
        return {"event_id": event_id, "requeued": True}
    raise HTTPException(status_code=404, detail="event not found")


@app.post("/ack")
async def ack(
    request: Request,
    event_id: str = Query(default=""),
    consumer_id: str = Query(default=""),
) -> dict[str, Any]:
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id is required")

    db = _get_db(request)
    cfg = _get_config(request)

    def _ack_and_offset() -> tuple[bool, int | None]:
        from eventbus.db import ack_event as _ack_event
        from eventbus.offsets import write_offset  # noqa: PLC0415

        with get_db_lock():
            now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            acked = _ack_event(db, event_id, now)  # type: ignore[arg-type]
            seq: int | None = None
            if consumer_id and acked:
                row = db.execute(
                    "SELECT seq FROM events WHERE event_id = ?", (event_id,)
                ).fetchone()
                if row:
                    seq = int(row["seq"])
                    write_offset(cfg.offsets_dir, consumer_id, seq)
            return (acked, seq)

    acked, seq = await asyncio.to_thread(_ack_and_offset)
    if not acked:
        raise HTTPException(status_code=404, detail="event not found or already acked")
    logger.info("event acked event_id=%s", event_id)
    return {"event_id": event_id, "acked": True, "seq": seq}


@app.post("/events/{event_id}/ack")
async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(default=""),
) -> dict[str, Any]:
    db = _get_db(request)
    cfg = _get_config(request)

    def _ack_and_offset() -> tuple[bool, int | None]:
        from eventbus.db import ack_event as _ack_event
        from eventbus.offsets import write_offset  # noqa: PLC0415

        with get_db_lock():
            now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            acked = _ack_event(db, event_id, now)  # type: ignore[arg-type]
            seq: int | None = None
            if consumer_id and acked:
                row = db.execute(
                    "SELECT seq FROM events WHERE event_id = ?", (event_id,)
                ).fetchone()
                if row:
                    seq = int(row["seq"])
                    write_offset(cfg.offsets_dir, consumer_id, seq)
            return (acked, seq)

    acked, seq = await asyncio.to_thread(_ack_and_offset)
    if not acked:
        raise HTTPException(status_code=404, detail="event not found or already acked")
    logger.info("event acked event_id=%s", event_id)
    return {"event_id": event_id, "acked": True, "seq": seq}


@app.post("/nack")
async def nack(
    request: Request,
    event_id: str = Query(default=""),
) -> dict[str, Any]:
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id is required")

    db = _get_db(request)
    cfg = _get_config(request)

    def _nack_and_promote() -> tuple[int, bool]:
        from eventbus.db import nack_event as _nack_event

        with get_db_lock():
            failure_count = _nack_event(db, event_id)
            if failure_count == -1:
                return (-1, False)
            promoted = False
            if failure_count >= cfg.max_retry:
                promoted = promote_single(db, cfg.deadletter_dir, event_id)
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
