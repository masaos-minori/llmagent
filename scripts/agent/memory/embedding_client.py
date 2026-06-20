"""agent/memory/embedding_client.py
EmbeddingClient — HTTP embedding service with retry and circuit breaker.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

import httpx
import orjson

from agent.memory.types import EmbeddingErrorKind, EmbeddingResult

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingClientConfig:
    embed_url: str = ""
    timeout: float = 5.0
    max_retries: int = 2
    circuit_open_after: int = 3
    circuit_reset_sec: float = 60.0
    query_prefix: str = (
        "query: "  # prepended to input text before sending to embedding API
    )
    embed_dim: int = 384  # expected output dimension; 0 disables validation


async def _fetch_embedding(
    text: str,
    http: httpx.AsyncClient,
    embed_url: str,
    query_prefix: str,
    embed_dim: int = 0,
) -> EmbeddingResult:
    """Call the embedding endpoint once; return EmbeddingResult with success/error."""
    try:
        resp = await http.post(embed_url, json={"content": f"{query_prefix}{text}"})
        resp.raise_for_status()
        data = orjson.loads(resp.content)
        embedding = data.get("embedding") if isinstance(data, dict) else None
        if isinstance(embedding, list) and embedding:
            if embed_dim > 0 and len(embedding) != embed_dim:
                logger.error(
                    "Embedding dimension mismatch: expected %d, got %d for input '%.40s...'",
                    embed_dim,
                    len(embedding),
                    text,
                )
                return EmbeddingResult(
                    success=False,
                    error_kind=EmbeddingErrorKind.DIMENSION_MISMATCH,
                )
            return EmbeddingResult(
                success=True, embedding=[float(v) for v in embedding]
            )
        logger.warning("embed response missing 'embedding' field")
        return EmbeddingResult(
            success=False, error_kind=EmbeddingErrorKind.INVALID_RESPONSE
        )
    except httpx.HTTPStatusError as e:
        logger.warning(
            "EmbeddingClient._fetch_embedding HTTP error: status=%d body=%.200s",
            e.response.status_code,
            e.response.text,
        )
        return EmbeddingResult(success=False, error_kind=EmbeddingErrorKind.HTTP_ERROR)
    except httpx.RequestError as e:
        logger.warning("EmbeddingClient._fetch_embedding request error: %s", e)
        return EmbeddingResult(
            success=False, error_kind=EmbeddingErrorKind.UNKNOWN_ERROR
        )
    except orjson.JSONDecodeError as e:
        logger.warning("EmbeddingClient._fetch_embedding invalid JSON response: %s", e)
        return EmbeddingResult(
            success=False, error_kind=EmbeddingErrorKind.INVALID_RESPONSE
        )
    except Exception as e:
        logger.warning("EmbeddingClient._fetch_embedding unexpected error: %s", e)
        return EmbeddingResult(success=False, error_kind=EmbeddingErrorKind.HTTP_ERROR)


class EmbeddingClient:
    """Async HTTP client for embedding generation.

    Wraps _fetch_embedding with:
    - asyncio.wait_for timeout per attempt
    - configurable retry count on failure or TimeoutError
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

    async def fetch(self, text: str) -> EmbeddingResult:
        """Generate embedding; return EmbeddingResult indicating success or failure reason."""
        if not self._enabled or self._http is None or not self._config.embed_url:
            return EmbeddingResult(
                success=False, error_kind=EmbeddingErrorKind.DISABLED
            )
        if self._is_circuit_open():
            logger.debug("EmbeddingClient circuit open — skipping embed")
            return EmbeddingResult(
                success=False, error_kind=EmbeddingErrorKind.CIRCUIT_OPEN
            )

        last_result: EmbeddingResult = EmbeddingResult(
            success=False, error_kind=EmbeddingErrorKind.HTTP_ERROR
        )
        for attempt in range(self._config.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    _fetch_embedding(
                        text,
                        self._http,
                        self._config.embed_url,
                        self._config.query_prefix,
                        self._config.embed_dim,
                    ),
                    timeout=self._config.timeout,
                )
                if result.success:
                    self._fail_count = 0
                    return result
                last_result = result
            except TimeoutError:
                logger.warning(
                    "EmbeddingClient timeout (attempt %d/%d)",
                    attempt + 1,
                    self._config.max_retries + 1,
                )
                last_result = EmbeddingResult(
                    success=False, error_kind=EmbeddingErrorKind.TIMEOUT
                )
            self._record_failure()
            if self._is_circuit_open():
                return EmbeddingResult(
                    success=False, error_kind=EmbeddingErrorKind.CIRCUIT_OPEN
                )

        return last_result
