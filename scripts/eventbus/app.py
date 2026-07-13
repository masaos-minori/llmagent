from __future__ import annotations

import asyncio
import logging
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import orjson
from eventbus.ack_route import ack_event as ack_event_route
from eventbus.ack_route import nack as nack_route
from eventbus.broker import EventBroker
from eventbus.config import (
    _is_public_host,
    get_config_path,
    get_schema_path,
    load_config,
)
from eventbus.db import open_db
from eventbus.dlq import sweep_orphans
from eventbus.dlq_route import dlq_list as dlq_list_route
from eventbus.dlq_route import dlq_requeue as dlq_requeue_route
from eventbus.health_route import health_check
from eventbus.publish_route import publish as publish_route
from eventbus.replay_route import replay as replay_route
from eventbus.route_helpers import app_get_config as get_config
from eventbus.route_helpers import app_get_db as get_db
from eventbus.route_helpers import run_with_db_lock
from eventbus.subscribe_route import subscribe as subscribe_route
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


_ENVELOPE_SCHEMA_PATH = Path("/opt/llm/schemas/event_envelope.json")
_DLQ_INTERVAL = 60.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    app.state.config = load_config(get_config_path())
    app.state.db = open_db(app.state.config.db_path)
    app.state.envelope_schema = orjson.loads(get_schema_path().read_bytes())
    Path(app.state.config.storage_dir).mkdir(parents=True, exist_ok=True)
    app.state.broker = EventBroker()
    app.state.dlq_task = asyncio.create_task(_dlq_loop(app))
    if _is_public_host(app.state.config.host):
        logger.warning(
            "eventbus bound to public address %s:%d without authentication",
            app.state.config.host,
            app.state.config.port,
        )
    else:
        logger.info(
            "eventbus starting on %s:%d", app.state.config.host, app.state.config.port
        )
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
            cfg = get_config(app)
            db = get_db(app)

            def _sweep() -> int:
                result: int = sweep_orphans(db, cfg.deadletter_dir, cfg.max_retry)
                return result

            n = await run_with_db_lock(_sweep)
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
    result: JSONResponse = await health_check(request)
    return result


@app.post("/publish")
async def publish(request: Request) -> dict[str, Any]:
    result: dict[str, Any] = await publish_route(request)
    return result


@app.get("/replay")
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: str = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return await replay_route(
        request, since_seq=since_seq, fmt=fmt, limit=limit, offset=offset
    )


@app.get("/subscribe")
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
) -> Any:
    return await subscribe_route(
        request, topic=topic, since_seq=since_seq, consumer_id=consumer_id
    )


@app.get("/dlq")
async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    result: dict[str, Any] = await dlq_list_route(request, limit=limit, offset=offset)
    return result


@app.post("/dlq/{event_id}/requeue")
async def dlq_requeue(request: Request, event_id: str) -> dict[str, Any]:
    result: dict[str, Any] = await dlq_requeue_route(request, event_id)
    return result


@app.post("/events/{event_id}/ack")
async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(default=""),
) -> dict[str, Any]:
    result: dict[str, Any] = await ack_event_route(
        request, event_id=event_id, consumer_id=consumer_id
    )
    return result


@app.post("/nack")
async def nack(
    request: Request,
    event_id: str = Query(default=""),
) -> dict[str, Any]:
    result: dict[str, Any] = await nack_route(request, event_id=event_id)
    return result


def _main() -> None:
    """Start the Event Bus with config-based host binding."""
    import uvicorn  # noqa: PLC0415

    cfg = load_config(get_config_path())
    logger.info("eventbus starting on port=%d host=%s", cfg.port, cfg.host)
    uvicorn.run(
        "eventbus.app:app",
        host=cfg.host,
        port=cfg.port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    _main()
