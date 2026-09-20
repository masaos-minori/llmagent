"""scripts/agent/http_lifecycle_health_checker.py

HTTP health check for verifying server readiness.

Timeout values are passed as parameters rather than imported from
http_lifecycle.py to avoid circular imports.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

HEALTH_RECHECK_INTERVAL_SEC = 10.0
_DEFAULT_HEALTH_URL = "http://localhost:8080/health"
_DEFAULT_TIMEOUT = 5.0
_STARTUP_MAX_RETRIES = 30
_STARTUP_INTERVAL = 1.0


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
        try:
            async with httpx.AsyncClient(timeout=timeout, **client_kwargs) as client:
                response = await client.get(target_url)
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

    @staticmethod
    async def startup_poll(
        server_key: str,
        cfg: object,
        *,
        max_retries: int = _STARTUP_MAX_RETRIES,
        interval: float = _STARTUP_INTERVAL,
        url: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        fields: dict[str, Any] | None = None,
    ) -> bool:
        """Poll until the server becomes healthy or *max_retries* expires.

        Returns ``True`` when the server responds with HTTP 200 before the
        deadline; ``False`` otherwise.

        Args:
            server_key: Unique identifier for the server.
            cfg: Configuration object with health_url attribute.
            max_retries: Maximum number of retry attempts.
            interval: Time between retries in seconds.
            url: Optional override URL for the health check endpoint.
            timeout: Timeout for individual health check requests.
            fields: Additional keyword arguments to pass to
                ``httpx.AsyncClient()``. If None, defaults to an
                empty dict.
        """
        client_kwargs: dict[str, Any] = {"timeout": timeout}
        if fields:
            client_kwargs.update(fields)
        for attempt in range(max_retries):
            healthy = await HealthChecker.verify_running_async(
                server_key, cfg, url=url, **client_kwargs
            )
            if healthy:
                logger.info(
                    "%s became healthy after %d attempt(s)", server_key, attempt + 1
                )
                return True
            logger.debug(
                "%s health check attempt %d/%d failed, retrying in %.1fs...",
                server_key,
                attempt + 1,
                max_retries,
                interval,
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(interval)

        logger.warning(
            "%s did not become healthy after %d attempts", server_key, max_retries
        )
        return False
