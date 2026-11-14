"""scripts/eventbus/app.py"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import orjson
from fastapi import FastAPI

from eventbus.ack_route import router as ack_router
from eventbus.admin_route import router as admin_router
from eventbus.audit import log_privileged_action
from eventbus.auth import (
    attach_auth_middleware,  # noqa: PLC0415 — new module, REQ-002
    build_and_publish_generation,  # noqa: PLC0415 — new module, REQ-004
    current_generation,
)
from eventbus.authz_ttl import authz_sweep_loop
from eventbus.broker import EventBroker
from eventbus.config import (
    _is_public_host,
    authorization_baseline_hash,
    get_config_path,
    get_schema_path,
    load_config,
)
from eventbus.db_conn import (
    clear_shutdown_flag,
    get_db_lock,
    open_db,
    set_shutdown_flag,
)
from eventbus.dlq import (
    process_outbox,
    reconcile_missing_dlq_files,
    sweep_orphans,
)
from eventbus.dlq_route import router as dlq_router
from eventbus.health_route import router as health_router
from eventbus.json_utils import now_iso
from eventbus.publish_route import router as publish_router
from eventbus.replay_route import router as replay_router
from eventbus.route_helpers import (
    app_get_config as get_config,
)
from eventbus.route_helpers import (
    app_get_db as get_db,
)
from eventbus.route_helpers import (
    run_with_db_lock,
)
from eventbus.subscribe_route import router as subscribe_router

logger = logging.getLogger(__name__)


_ENVELOPE_SCHEMA_PATH = Path("/opt/llm/schemas/event_envelope.json")
_DLQ_INTERVAL = 60.0
_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS = 5.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """FastAPI lifespan: initialize broker/db/lifecycle on startup; clean up on shutdown."""
    clear_shutdown_flag()  # a new lifecycle must not inherit a prior shutdown flag
    app.state.config = load_config(get_config_path())
    app.state.db = open_db(app.state.config.db_path)
    # Publish the baseline authorization generation from config
    build_and_publish_generation(app.state.config)
    # Restart-baseline audit record: documents the baseline generation
    # hash in force and that any prior runtime overrides were removed.
    baseline_gen = current_generation()
    log_privileged_action(
        consumer_id="system",
        request_id="",
        route="/startup",
        target="authz_baseline",
        detail=(
            "baseline_hash:"
            f"{baseline_gen.baseline_hash if baseline_gen is not None else authorization_baseline_hash(app.state.config)}"
            ";runtime_overrides:removed"
        ),
        actor="",
    )
    app.state.envelope_schema = orjson.loads(get_schema_path().read_bytes())
    Path(app.state.config.storage_dir).mkdir(parents=True, exist_ok=True)
    app.state.broker = EventBroker(app.state.config)
    # Last DLQ loop-cycle outcome and time, reported by /health. Initialized so a
    # /health request before the first cycle reads 'not_run' instead of failing.
    app.state.last_dlq_cycle_result = "not_run"
    app.state.last_dlq_cycle_time = None
    app.state.dlq_task = asyncio.create_task(_dlq_loop(app))
    app.state.authz_sweep_task = asyncio.create_task(authz_sweep_loop(app))
    if _is_public_host(app.state.config.host):
        logger.warning(
            "eventbus bound to public address %s:%d without loopback-only protection",
            app.state.config.host,
            app.state.config.port,
        )
    else:
        logger.info(
            "eventbus starting on %s:%d", app.state.config.host, app.state.config.port
        )
    yield
    await _shutdown_lifespan(app)


async def _shutdown_lifespan(app: FastAPI) -> None:
    """Shared shutdown sequence: stop sweeps, await the in-flight sweep,
    prove exclusive ownership of the shared connection, then close it.

    Delegated to by both lifespan() (production) and the tests/eventbus/ suite
    so they exercise one lifecycle sequence. Never closes a connection
    another worker may still own; the close-on-timeout fallback is gone.
    """
    # 1. Stop scheduling new sweep cycles and await the in-flight sweep.
    # set_shutdown_flag() makes run_with_db_lock() refuse new DB work from
    # this point on (seq 03).
    set_shutdown_flag()
    if app.state.dlq_task:
        app.state.dlq_task.cancel()
        try:
            await app.state.dlq_task
        except asyncio.CancelledError:
            pass
    # authz_sweep_task is set by lifespan(); tests that call this function with a
    # manually built app.state may not have it — getattr keeps shutdown total.
    authz_sweep_task = getattr(app.state, "authz_sweep_task", None)
    if authz_sweep_task:
        authz_sweep_task.cancel()
        try:
            await authz_sweep_task
        except asyncio.CancelledError:
            pass
    # 2. Broker shutdown (unchanged order).
    if app.state.broker:
        app.state.broker.shutdown()
    # 3. Prove exclusive ownership before closing. _dlq_loop's sweep runs on a
    #    worker thread via asyncio.to_thread(); cancelling the task above cannot
    #    interrupt a sweep already running on that thread, so acquiring the same
    #    lock run_with_db_lock() uses serializes the close behind any in-flight
    #    sweep instead of racing db.close() and segfaulting.
    if app.state.db:
        lock = get_db_lock()
        acquired = await asyncio.to_thread(
            lock.acquire, timeout=_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS
        )
        if not acquired:
            raise RuntimeError(
                f"shutdown: could not acquire db lock within "
                f"{_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS:.1f}s; refusing to close a "
                "connection another worker may own"
            )
        try:
            app.state.db.close()
        finally:
            app.state.db = None
            lock.release()


async def _dlq_loop(app: FastAPI) -> None:
    """Periodically sweep orphaned events into the dead-letter queue directory."""
    while True:
        try:
            cfg = get_config(app)
            db = get_db(app)

            def _sweep() -> int:
                """Sweep orphaned events from the DLQ table into the dead-letter directory."""
                result: int = sweep_orphans(db, cfg.max_retry)
                return result

            n = await run_with_db_lock(_sweep)
            if n:
                logger.warning(
                    "dlq_loop: swept %d orphan(s) missed by inline promotion", n
                )

            # dlqbox001: generate the DLQ artifacts requested by the promotion
            # transactions. process_outbox schedules its own locked transactions.
            outbox = await process_outbox(db, cfg.deadletter_dir, cfg, run_with_db_lock)
            if outbox["processed"]:
                logger.warning(
                    "dlq_loop: outbox processed=%d generated=%d "
                    "failed_attempts=%d terminal_failed=%d",
                    outbox["processed"],
                    outbox["generated"],
                    outbox["failed_attempts"],
                    outbox["terminal_failed"],
                )

            # Repair lost artifacts and report outbox inconsistencies.
            reconciled = await run_with_db_lock(
                lambda: reconcile_missing_dlq_files(db, cfg.deadletter_dir)
            )
            if any(
                reconciled[k]
                for k in ("rebuilt", "failed", "orphans", "interrupted_tmp", "mismatch")
            ):
                logger.warning(
                    "dlq_loop: reconcile checked=%d rebuilt=%d failed=%d "
                    "orphans=%d interrupted_tmp=%d mismatch=%d",
                    reconciled["checked"],
                    reconciled["rebuilt"],
                    reconciled["failed"],
                    reconciled["orphans"],
                    reconciled["interrupted_tmp"],
                    reconciled["mismatch"],
                )
            app.state.last_dlq_cycle_result = "ok"
            app.state.last_dlq_cycle_time = now_iso()
        except (OSError, sqlite3.Error):
            logger.exception("dlq_loop error")
            app.state.last_dlq_cycle_result = "failed"
            app.state.last_dlq_cycle_time = now_iso()
        await asyncio.sleep(_DLQ_INTERVAL)


app = FastAPI(lifespan=lifespan)
attach_auth_middleware(app)
app.include_router(health_router)
app.include_router(publish_router)
app.include_router(replay_router)
app.include_router(subscribe_router)
app.include_router(dlq_router)
app.include_router(ack_router)
app.include_router(admin_router)


def _main() -> None:
    """Start the Event Bus with config-based host binding."""
    import sys  # noqa: PLC0415

    import uvicorn  # noqa: PLC0415

    cfg = load_config(get_config_path())
    logger.info("eventbus starting on port=%d host=%s", cfg.port, cfg.host)

    class _LoopbackVerifyingServer(uvicorn.Server):
        """Verifies the actual bound socket address is loopback right after
        startup — defense-in-depth confirmation that the OS-level bind
        matches the already-validated `cfg.host`, not a substitute for
        `EventBusConfig.__post_init__`'s config-time check."""

        async def startup(self, sockets: list[Any] | None = None) -> None:
            await super().startup(sockets=sockets)
            if self.should_exit or not getattr(self, "servers", None):
                return
            for srv in self.servers:
                for sock in srv.sockets or []:
                    bound_host = sock.getsockname()[0]
                    if bound_host not in ("127.0.0.1", "::1"):
                        raise RuntimeError(
                            "Post-start verification failed: bound socket "
                            f"address is {bound_host!r}, not loopback."
                        )
            logger.info("eventbus post-start verification: bound socket is loopback")

    config = uvicorn.Config(
        "eventbus.app:app",
        host=cfg.host,
        port=cfg.port,
        log_level="info",
        access_log=True,
    )
    server = _LoopbackVerifyingServer(config=config)
    try:
        server.run()
    except KeyboardInterrupt:  # pragma: no cover — interactive-only path
        pass
    if not server.started:
        sys.exit(1)


if __name__ == "__main__":
    _main()
