"""scripts/rag/http_augment.py

HTTP augment for RAG pipeline."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal

from rag.pipeline_service import CallRagKind, CallRagResult, call_rag_service

if TYPE_CHECKING:
    import httpx
from rag.models_result import HttpResultKind
from rag.stage import PipelineContext, StageResult

logger = logging.getLogger(__name__)

_HTTP_RESULT_KIND_MAP: dict[str, HttpResultKind] = {
    "remote_nonempty": HttpResultKind.SUCCESS,
    "remote_empty": HttpResultKind.EMPTY,
    "in_process_fallback": HttpResultKind.ERROR,
    "auth_error": HttpResultKind.AUTH_ERROR,
}

_KIND_TO_RESULT_KIND: dict[
    CallRagKind,
    Literal["remote_nonempty", "remote_empty", "in_process_fallback", "auth_error"],
] = {
    "success": "remote_nonempty",
    "empty": "remote_empty",
    "auth_error": "auth_error",
    "transient_failure": "in_process_fallback",
}


def _map_http_result_kind(
    kind: Literal[
        "remote_nonempty", "remote_empty", "in_process_fallback", "auth_error"
    ]
    | str
    | None,
) -> HttpResultKind:
    if kind is None:
        return HttpResultKind.NOT_USED
    return _HTTP_RESULT_KIND_MAP[kind]


class HttpAugmentResult:
    """Result of an HTTP augment attempt."""

    def __init__(
        self,
        result: str | None,
        status_code: int | None,
        latency_ms: float,
        http_result_kind: Literal[
            "remote_nonempty", "remote_empty", "in_process_fallback", "auth_error"
        ],
    ) -> None:
        """Initialize with result content, HTTP status, latency, and kind classification."""
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
        set_fetch_result: Callable[[list[dict[str, Any]]], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def get_status(
        self, ctx: PipelineContext
    ) -> tuple[Literal["success", "fallback"], str | None]:
        """Return execution status of this stage with optional reason string."""
        if not ctx.augment_result:
            return "fallback", "no augment result"
        return "success", None

    async def run(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result.

        Return value contract (``HttpAugmentResult.result`` / ``http_result_kind``):
          - ``str`` (non-empty): valid augmented result
          - ``""`` (empty string): valid but empty result; caller should fall back
            to in-process search
          - ``None`` with ``http_result_kind == "in_process_fallback"``: augmentation
            failed; caller may use in-process search
          - ``None`` with ``http_result_kind == "auth_error"``: HTTP 401/403; caller
            MUST NOT fall back and must fail closed

        Identity-vs-truthiness note: ``""`` and ``None`` are both falsy but have
        different meanings.  ``""`` means the remote returned a valid response with
        no hits; ``None`` means the remote could not produce a response at all.
        Callers MUST check ``is not None`` rather than truthiness to distinguish them.
        """
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        outcome = await call_rag_service(
            self._http,
            self._rag_url,
            query,
            history_context,
            auth_token=self._auth_token,
            set_fetch_result=lambda fr: self._set_fetch_result(fr),
            set_fallback_reason=http_fallback_reasons.append,
        )
        if not isinstance(outcome, CallRagResult):
            raise TypeError(
                f"call_rag_service() returned unexpected type: {type(outcome).__name__} "
                f"({outcome!r}); expected CallRagResult"
            )
        result = outcome.result
        status_code = outcome.status_code
        latency_ms = outcome.latency_ms
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
            "remote_nonempty", "remote_empty", "in_process_fallback", "auth_error"
        ] = _KIND_TO_RESULT_KIND[outcome.kind]
        if result is None:
            if outcome.kind == "auth_error":
                logger.warning(
                    "RAG service authentication error (%s), NOT falling back to in-process",
                    self._rag_url,
                )
            else:
                self._set_fallback_reason(http_fallback_reason)
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
    ) -> (
        Literal["remote_nonempty", "remote_empty", "in_process_fallback", "auth_error"]
        | None
    ):
        """Return the HTTP result kind."""
        return getattr(self, "_http_result_kind", None)
