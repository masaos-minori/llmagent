"""agent/memory/embedding_client.py
EmbeddingClient — HTTP embedding service with retry and circuit breaker.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingClientConfig:
    embed_url: str = ""
    timeout: float = 5.0
    max_retries: int = 2
    circuit_open_after: int = 3
    circuit_reset_sec: float = 60.0


async def _fetch_embedding(
    text: str,
    http: httpx.AsyncClient,
    embed_url: str,
) -> list[float] | None:
    """Call the embedding endpoint once; return None on any error."""
    try:
        resp = await http.post(embed_url, json={"content": f"query: {text}"})
        resp.raise_for_status()
        embedding = resp.json().get("embedding")
        if isinstance(embedding, list) and embedding:
            return [float(v) for v in embedding]
        logger.warning("embed response missing 'embedding' field")
        return None
    except Exception as e:
        logger.warning(f"EmbeddingClient._fetch_embedding failed: {e}")
        return None


class EmbeddingClient:
    """Async HTTP client for embedding generation.

    Wraps _fetch_embedding with:
    - asyncio.wait_for timeout per attempt
    - configurable retry count on None result or TimeoutError
    - simple circuit breaker (open after N consecutive failures)
    """

    def __init__(
        self,
        config: EmbeddingClientConfig,
        http: httpx.AsyncClient | None = None,
        *,
        enabled: bool = False,
    ) -> None:
        self._config = config
        self._http = http
        self._enabled = enabled
        self._fail_count: int = 0
        self._circuit_opened_at: float | None = None

    def _is_circuit_open(self) -> bool:
        if self._circuit_opened_at is None:
            return False
        elapsed = time.monotonic() - self._circuit_opened_at
        if elapsed >= self._config.circuit_reset_sec:
            # Auto-reset
            self._fail_count = 0
            self._circuit_opened_at = None
            return False
        return True

    def _record_failure(self) -> None:
        self._fail_count += 1
        if self._fail_count >= self._config.circuit_open_after:
            self._circuit_opened_at = time.monotonic()
            logger.warning(
                "EmbeddingClient circuit opened after %d consecutive failures",
                self._fail_count,
            )

    async def fetch(self, text: str) -> list[float] | None:
        """Generate embedding; return None when disabled, circuit open, or on error."""
        if not self._enabled or self._http is None or not self._config.embed_url:
            return None
        if self._is_circuit_open():
            logger.debug("EmbeddingClient circuit open — skipping embed")
            return None

        for attempt in range(self._config.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    _fetch_embedding(text, self._http, self._config.embed_url),
                    timeout=self._config.timeout,
                )
                if result is not None:
                    self._fail_count = 0
                    return result
                # _fetch_embedding returned None (internal error) — retry
            except TimeoutError:
                logger.warning(
                    "EmbeddingClient timeout (attempt %d/%d)",
                    attempt + 1,
                    self._config.max_retries + 1,
                )
            self._record_failure()
            if self._is_circuit_open():
                return None

        return None
