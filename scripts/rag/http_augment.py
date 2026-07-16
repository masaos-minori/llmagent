"""HTTP augment for RAG pipeline."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from rag.pipeline_service import call_rag_service

if TYPE_CHECKING:
    import httpx

    from rag.models_data import TwoStageFetchResult  # noqa: TCH004
from rag.stage import StageResult


class HttpAugmentResult:
    """Result of an HTTP augment attempt."""

    def __init__(
        self,
        result: str | None,
        status_code: int | None,
        latency_ms: float,
        http_result_kind: Literal[
            "remote_nonempty", "remote_empty", "in_process_fallback"
        ],
    ) -> None:
        self.result = result
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.http_result_kind = http_result_kind


class HttpAugment:
    """Handles HTTP RAG augment delegation.

    When rag_service_url is configured, delegates augment to an external
    RAG service instead of running the in-process pipeline.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    async def run(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
            query,
            history_context,
            auth_token=self._auth_token,
            set_fetch_result=lambda fr: self._set_fetch_result(fr),
            set_fallback_reason=http_fallback_reasons.append,
        )
        elapsed = time.perf_counter() - t0
        http_status: Literal["success", "fallback"] = (
            "success" if result is not None else "fallback"
        )
        http_fallback_reason = (
            http_fallback_reasons[0] if http_fallback_reasons else "in-process fallback"
        )
        self._stage_result = StageResult(
            stage_name="HttpAugment",
            status=http_status,
            elapsed_seconds=elapsed,
            fallback_reason=(http_fallback_reason if result is None else None),
        )
        self._http_result_kind: Literal[
            "remote_nonempty", "remote_empty", "in_process_fallback"
        ] = (
            "remote_nonempty"
            if result and len(result) > 0
            else "remote_empty"
            if result == ""
            else "in_process_fallback"
        )
        return HttpAugmentResult(
            result=result,
            status_code=status_code,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    @property
    def stage_result(self) -> StageResult | None:
        """Return the HTTP augment stage result."""
        return getattr(self, "_stage_result", None)

    @property
    def http_result_kind(
        self,
    ) -> Literal["remote_nonempty", "remote_empty", "in_process_fallback"] | None:
        """Return the HTTP result kind."""
        return getattr(self, "_http_result_kind", None)
