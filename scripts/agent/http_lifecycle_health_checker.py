"""scripts/agent/http_lifecycle_health_checker.py

HTTP health check for verifying server readiness.

HttpServerLifecycleManager delegates all health check operations to this module.
Timeout values are passed as parameters rather than imported from
http_lifecycle.py to avoid circular imports.

Owns the startup readiness poll loop (`poll_until_ready`), the report-based
readiness helpers (`parse_report`, `is_ready`), and the shutdown-aware poll sleep
(`_interruptible_poll_sleep`). The poll loop delegates tracking cleanup, health
observation, startup-failure raising, and termination back to the manager it is
given, mirroring how ShutdownCoordinator delegates cleanup.

Readiness is decided from the parsed `/health` report, not from the status code:
the caller supplies the server's catalog `required_capability` (this module does not
read `config/tool_catalog.toml`), and each request timeout is capped by the time
left to the deadline (REQ-002).
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import time
from typing import TYPE_CHECKING, Any

import httpx
from shared.mcp_config import McpServerConfig, get_effective_health_timeout
from shared.mcp_health_contract import (
    CAPABILITY_STATE_OK,
    HealthReport,
    parse_health_body,
)

from agent.http_lifecycle_errors import TerminationOutcome
from agent.secrets_masker import _mask_secrets, redact_url

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpServerLifecycleManager

logger = logging.getLogger(__name__)

HEALTH_RECHECK_INTERVAL_SEC = 10.0
_DEFAULT_HEALTH_URL = "http://localhost:8080/health"


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


async def _terminate_for_startup_failure(
    manager: HttpServerLifecycleManager,
    server_key: str,
    proc: subprocess.Popen[bytes],
    terminate_timeout_sec: float,
) -> TerminationOutcome:
    """Terminate the live child on a startup-failure path, proving or disproving its exit.

    A terminator exception is logged and classified EXIT_UNCONFIRMED so it never
    masks the HttpStartupError the caller raises next (no-masking).
    """
    try:
        return await manager.process_terminator.terminate_with_timeout(
            proc, server_key, timeout=terminate_timeout_sec
        )
    except Exception as e:  # noqa: BLE001 — must not mask the startup error raised next
        logger.warning(
            "Lifecycle: terminating %r on startup failure failed (%s); "
            "treating the exit as unconfirmed",
            server_key,
            e,
        )
        return TerminationOutcome.EXIT_UNCONFIRMED


class HealthChecker:
    """Performs HTTP health checks against a running server."""

    @staticmethod
    def parse_report(resp: httpx.Response) -> HealthReport | None:
        """Parse a `/health` body through the shared contract.

        Returns None when the body is not JSON, is not an object, or violates the
        contract: an unparseable body is not readiness proof, so the poll keeps
        running instead of crashing startup.
        """
        try:
            body = resp.json()
        except (ValueError, httpx.DecodingError):
            return None
        try:
            return parse_health_body(body)
        except ValueError:
            return None

    @staticmethod
    def is_ready(report: HealthReport, required_capability: str | None) -> bool:
        """Return True iff the report proves readiness for this server (REQ-005, D-6).

        The proof is the server's catalog `required_capability` reported `ok`. A legacy
        body (no capability block) falls back to its `ready` flag, and a server with no
        declared `required_capability` is read the same way. `liveness` alone is never
        proof.
        """
        if required_capability is None or report.is_legacy:
            return report.ready
        state = report.capabilities.get(required_capability)
        return state is not None and state.state == CAPABILITY_STATE_OK

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
        required_capability: str | None = None,
    ) -> None:
        """Poll /health endpoint until the server becomes healthy or timeout expires.

        Polls the health endpoint in a loop, checking for early exit and shutdown
        events between polls. Raises HttpStartupError on early exit, shutdown,
        or timeout.

        Each request timeout is `min(request_timeout_sec, remaining time to the
        deadline)` (REQ-002); no request starts once the deadline has passed.
        Readiness is the parsed report proving `required_capability` is `ok`, or a
        legacy body with `ready` true (REQ-005, D-6).

        On a live-child failure (shutdown or timeout) the child is terminated
        first and tracking is dropped only when the termination confirms the exit;
        an unconfirmed exit keeps the process tracked for shutdown_all().

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
            request_timeout_sec: Upper bound for a single health-check request, the
                server's effective health timeout supplied by the caller (seq 04).
            terminate_timeout_sec: Termination timeout applied on poll timeout.
            required_capability: The server's catalog capability identifier resolved
                by the caller; None reads the body through the legacy `ready` fallback.

        Raises:
            HttpStartupError: On early exit, shutdown, or timeout.
        """
        health_url = cfg.url.rstrip("/") + "/health"
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout=request_timeout_sec),
            headers=cfg.auth_headers(),
        ) as client:
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    stderr_full = manager._cleanup_server_resources(server_key)
                    logger.error(
                        "Lifecycle: %r exited early; stderr (%s chars): %s",
                        server_key,
                        len(stderr_full),
                        # REQ-003 (AC-2): mask before truncating, so a truncated tail
                        # cannot cut a masked value open.
                        _mask_secrets(stderr_full)[:500],
                    )
                    manager._raise_startup_failure(
                        server_key, "exited early", stderr_full
                    )
                remaining_sec = deadline - time.monotonic()
                if remaining_sec <= 0:
                    break
                try:
                    resp = await client.get(
                        health_url,
                        timeout=httpx.Timeout(
                            timeout=min(request_timeout_sec, remaining_sec)
                        ),
                    )
                    report = HealthChecker.parse_report(resp)
                    if report is not None and HealthChecker.is_ready(
                        report, required_capability
                    ):
                        manager._mark_health_checked(server_key)
                        logger.info(
                            "Lifecycle: HTTP subprocess %r ready",
                            server_key,
                        )
                        return
                except (httpx.HTTPError, OSError) as e:
                    logger.info("Lifecycle: health-check poll %r: %s", server_key, e)
                if await _interruptible_poll_sleep(poll_interval_sec, shutdown_event):
                    outcome = await _terminate_for_startup_failure(
                        manager, server_key, proc, terminate_timeout_sec
                    )
                    if outcome.confirmed:
                        stderr_full = manager._cleanup_server_resources(server_key)
                        manager._raise_startup_failure(
                            server_key, "shutdown requested", stderr_full
                        )
                    else:
                        stderr_full = manager._stderr_log_manager.read_tail(
                            server_key
                        ).decode(errors="replace")
                        manager._raise_startup_failure_unconfirmed(
                            server_key,
                            "shutdown requested",
                            stderr_full,
                            outcome,
                        )

            outcome = await _terminate_for_startup_failure(
                manager, server_key, proc, terminate_timeout_sec
            )
            timeout_reason = f"did not become healthy within {cfg.startup_timeout_sec}s"
            if outcome.confirmed:
                stderr_full = manager._cleanup_server_resources(server_key)
                manager._raise_startup_failure(server_key, timeout_reason, stderr_full)
            else:
                stderr_full = manager._stderr_log_manager.read_tail(server_key).decode(
                    errors="replace"
                )
                manager._raise_startup_failure_unconfirmed(
                    server_key, timeout_reason, stderr_full, outcome
                )

    @staticmethod
    async def verify_running_async(
        server_key: str,
        cfg: McpServerConfig,
        *,
        url: str | None = None,
        timeout: float | None = None,
        **client_kwargs: Any,
    ) -> bool:
        """Verify that the server identified by *server_key* is reachable.

        Uses the ``health_url`` attribute on *cfg* when available; falls back
        to ``_DEFAULT_HEALTH_URL``.

        The request timeout is the server's effective health timeout
        (`get_effective_health_timeout(cfg)`) unless the caller supplies one, and the
        Authorization header comes from `cfg.auth_headers()` only — the single auth
        path (REQ-003). Callers MUST NOT pass `headers` in *client_kwargs*. The token
        is never interpolated into a log line.

        Args:
            server_key: Unique identifier for the server.
            cfg: Server configuration.
            url: Optional override URL for the health check endpoint.
            timeout: Optional per-request timeout override; the effective per-server
                health timeout is used when it is not supplied.
            **client_kwargs: Additional keyword arguments passed to httpx.AsyncClient().
        """
        target_url = url or getattr(cfg, "health_url", _DEFAULT_HEALTH_URL)
        if target_url is None:
            target_url = _DEFAULT_HEALTH_URL
        # REQ-003 (AC-2): the request keeps the real endpoint; only the logged form is
        # redacted, and redaction happens before any truncation of the logged value.
        logged_url = redact_url(target_url)
        request_timeout = (
            timeout if timeout is not None else get_effective_health_timeout(cfg)
        )
        try:
            async with httpx.AsyncClient(
                timeout=request_timeout, headers=cfg.auth_headers(), **client_kwargs
            ) as client:
                response = await client.get(target_url)
                if response.status_code == 200:
                    logger.debug("Health check passed at %s", logged_url)
                    return True
                logger.debug(
                    "Health check returned status %d at %s",
                    response.status_code,
                    logged_url,
                )
                return False
        except httpx.RequestError as exc:
            logger.debug("Health check failed at %s: %s", logged_url, exc)
            return False
        except Exception as exc:  # noqa: BLE001 — health check must never propagate an unexpected error to the caller
            logger.warning("Unexpected error during health check: %s", exc)
            return False
