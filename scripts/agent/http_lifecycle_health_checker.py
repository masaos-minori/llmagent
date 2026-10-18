"""scripts/agent/http_lifecycle_health_checker.py

HTTP health check for verifying server readiness.

HttpServerLifecycleManager delegates all health check operations to this module.
Timeout values are passed as parameters rather than imported from
http_lifecycle.py to avoid circular imports.

Owns the startup readiness poll loop (`poll_until_ready`), the degraded-but-live
predicate (`is_degraded_but_live`), and the shutdown-aware poll sleep
(`_interruptible_poll_sleep`). The poll loop delegates tracking cleanup, health
observation, startup-failure raising, and termination back to the manager it is
given, mirroring how ShutdownCoordinator delegates cleanup.
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import time
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import httpx
from shared.mcp_config import McpServerConfig

from agent.secrets_masker import _mask_secrets

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpServerLifecycleManager

logger = logging.getLogger(__name__)

HEALTH_RECHECK_INTERVAL_SEC = 10.0
_DEFAULT_HEALTH_URL = "http://localhost:8080/health"
_DEFAULT_TIMEOUT = 5.0


async def _interruptible_poll_sleep(
    delay: float, shutdown_event: asyncio.Event | None
) -> bool:
    """Sleep for `delay` seconds, racing against `shutdown_event`.

    Returns True iff the shutdown event fired before `delay` elapsed (caller
    should abort the health-poll loop); returns False if the full delay
    elapsed normally or no `shutdown_event` was configured.
    """
    if shutdown_event is None:
        await asyncio.sleep(delay)
        return False
    sleep_task = asyncio.ensure_future(asyncio.sleep(delay))
    shutdown_task = asyncio.ensure_future(shutdown_event.wait())
    done, pending = await asyncio.wait(
        {sleep_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()
    return shutdown_task in done


class HealthChecker:
    """Performs HTTP health checks against a running server."""

    @staticmethod
    def compute_health_check_timeout(
        startup_timeout: float, mcpserver_health_timeout: float = 5.0
    ) -> float:
        """Compute the timeout for a single health-check request.

        Uses the smaller of *mcpserver_health_timeout* and the configured
        *startup_timeout* so that no individual request can block longer than
        the shorter interval.
        """
        return min(mcpserver_health_timeout, startup_timeout)

    @staticmethod
    def is_degraded_but_live(resp: httpx.Response) -> bool:
        """Return True iff a non-200 /health response is degraded-but-live.

        Mirrors McpServerStartupStarter.verify_health: a 503 with a JSON body
        whose `liveness` flag is true means the server started but an optional
        dependency (e.g. GITHUB_TOKEN) is unavailable. Such a server is alive
        and must count as ready at startup rather than abort it. The spawn and
        post-startup phases must agree on what "live" means.
        """
        if resp.status_code != HTTPStatus(503):
            return False
        if "application/json" not in resp.headers.get("content-type", ""):
            return False
        try:
            body = resp.json()
        except (json.JSONDecodeError, httpx.DecodingError):
            return False
        return bool(body.get("liveness", False))

    @staticmethod
    async def poll_until_ready(
        manager: HttpServerLifecycleManager,
        server_key: str,
        cfg: McpServerConfig,
        proc: subprocess.Popen[bytes],
        deadline: float,
        shutdown_event: asyncio.Event | None,
        *,
        poll_interval_sec: float,
        request_timeout_sec: float,
        terminate_timeout_sec: float,
    ) -> None:
        """Poll /health endpoint until the server becomes healthy or timeout expires.

        Polls the health endpoint in a loop, checking for early exit and shutdown
        events between polls. Raises HttpStartupError on early exit, shutdown,
        or timeout.

        Note: A new AsyncClient is created per call site (not reused across calls).
        This prioritizes correctness — no leaked connections on failure paths —
        over connection pooling benefits, which are marginal for short-lived
        health checks against localhost.

        Args:
            manager: Lifecycle manager whose tracking, health-observation, failure
                and termination resources the loop uses.
            server_key: Server identifier key.
            cfg: Server configuration.
            proc: Subprocess instance to monitor.
            deadline: Monotonic time at which to abort polling.
            shutdown_event: Optional event to race against poll sleep.
            poll_interval_sec: Delay between polls.
            request_timeout_sec: Upper bound for a single health-check request.
            terminate_timeout_sec: Termination timeout applied on poll timeout.

        Raises:
            HttpStartupError: On early exit, shutdown, or timeout.
        """
        health_url = cfg.url.rstrip("/") + "/health"
        hc_timeout = HealthChecker.compute_health_check_timeout(
            cfg.startup_timeout_sec, request_timeout_sec
        )
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout=hc_timeout), headers=cfg.auth_headers()
        ) as client:
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    stderr_full = manager._cleanup_server_resources(server_key)
                    logger.error(
                        "Lifecycle: %r exited early; stderr (%s chars): %s",
                        server_key,
                        len(stderr_full),
                        _mask_secrets(stderr_full[:500]),
                    )
                    manager._raise_startup_failure(
                        server_key, "exited early", stderr_full
                    )
                try:
                    resp = await client.get(health_url)
                    if resp.status_code == HTTPStatus.OK:
                        manager._mark_health_checked(server_key)
                        logger.info(
                            "Lifecycle: HTTP subprocess %r ready",
                            server_key,
                        )
                        return
                    if HealthChecker.is_degraded_but_live(resp):
                        manager._mark_health_checked(server_key)
                        logger.info(
                            "Lifecycle: HTTP subprocess %r ready (degraded but live)",
                            server_key,
                        )
                        return
                except (httpx.HTTPError, OSError) as e:
                    logger.info("Lifecycle: health-check poll %r: %s", server_key, e)
                if await _interruptible_poll_sleep(poll_interval_sec, shutdown_event):
                    stderr_full = manager._cleanup_server_resources(server_key)
                    manager._raise_startup_failure(
                        server_key, "shutdown requested", stderr_full
                    )

            stderr_full = manager._cleanup_server_resources(server_key)
            await manager.process_terminator.terminate_with_timeout(
                proc, server_key, timeout=terminate_timeout_sec
            )
            manager._raise_startup_failure(
                server_key,
                f"did not become healthy within {cfg.startup_timeout_sec}s",
                stderr_full,
            )

    @staticmethod
    async def verify_running_async(
        server_key: str,
        cfg: object,
        *,
        url: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        **client_kwargs: Any,
    ) -> bool:
        """Verify that the server identified by *server_key* is reachable.

        Uses the ``health_url`` attribute on *cfg* when available; falls back
        to ``_DEFAULT_HEALTH_URL``.

        Args:
            server_key: Unique identifier for the server.
            cfg: Configuration object with health_url attribute.
            url: Optional override URL for the health check endpoint.
            timeout: Timeout for individual health check requests.
            **client_kwargs: Additional keyword arguments passed to httpx.AsyncClient().
        """
        target_url = url or getattr(cfg, "health_url", _DEFAULT_HEALTH_URL)
        if target_url is None:
            target_url = _DEFAULT_HEALTH_URL
        # Build headers — add Bearer token if cfg has auth_token
        headers: dict[str, str] = {}
        auth_token = getattr(cfg, "auth_token", "")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        try:
            async with httpx.AsyncClient(timeout=timeout, **client_kwargs) as client:
                response = await client.get(target_url, headers=headers)
                if response.status_code == 200:
                    logger.debug("Health check passed at %s", target_url)
                    return True
                logger.debug(
                    "Health check returned status %d at %s",
                    response.status_code,
                    target_url,
                )
                return False
        except httpx.RequestError as exc:
            logger.debug("Health check failed at %s: %s", target_url, exc)
            return False
        except Exception as exc:  # noqa: BLE001 — health check must never propagate an unexpected error to the caller
            logger.warning("Unexpected error during health check: %s", exc)
            return False
