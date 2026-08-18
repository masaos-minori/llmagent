"""scripts/rag/http_augment.py

HTTP augment for RAG pipeline."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from rag.pipeline_service import call_rag_service

if TYPE_CHECKING:
    import httpx

    from rag.models_data import TwoStageFetchResult  # noqa: TCH004
from rag.models_result import HttpResultKind
from rag.stage import StageResult

_HTTP_RESULT_KIND_MAP: dict[str, HttpResultKind] = {
    "remote_nonempty": HttpResultKind.SUCCESS,
    "remote_empty": HttpResultKind.EMPTY,
    "in_process_fallback": HttpResultKind.ERROR,
}


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__map_http_result_kind__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__map_http_result_kind__mutmut)
def _map_http_result_kind(
    kind: Literal["remote_nonempty", "remote_empty", "in_process_fallback"]
    | str
    | None,
) -> HttpResultKind:
    if kind is None:
        return HttpResultKind.NOT_USED
    return _HTTP_RESULT_KIND_MAP[kind]


def x__map_http_result_kind__mutmut_orig(
    kind: Literal["remote_nonempty", "remote_empty", "in_process_fallback"]
    | str
    | None,
) -> HttpResultKind:
    if kind is None:
        return HttpResultKind.NOT_USED
    return _HTTP_RESULT_KIND_MAP[kind]


def x__map_http_result_kind__mutmut_1(
    kind: Literal["remote_nonempty", "remote_empty", "in_process_fallback"]
    | str
    | None,
) -> HttpResultKind:
    if kind is not None:
        return HttpResultKind.NOT_USED
    return _HTTP_RESULT_KIND_MAP[kind]

mutants_x__map_http_result_kind__mutmut['_mutmut_orig'] = x__map_http_result_kind__mutmut_orig # type: ignore # mutmut generated
mutants_x__map_http_result_kind__mutmut['x__map_http_result_kind__mutmut_1'] = x__map_http_result_kind__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHttpAugmentResultǁ__init____mutmut: MutantDict = {}  # type: ignore


class HttpAugmentResult:
    """Result of an HTTP augment attempt."""

    @_mutmut_mutated(mutants_xǁHttpAugmentResultǁ__init____mutmut)
    def __init__(
        self,
        result: str | None,
        status_code: int | None,
        latency_ms: float,
        http_result_kind: Literal[
            "remote_nonempty", "remote_empty", "in_process_fallback"
        ],
    ) -> None:
        """Initialize with result content, HTTP status, latency, and kind classification."""
        self.result = result
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.http_result_kind = http_result_kind

    def xǁHttpAugmentResultǁ__init____mutmut_orig(
        self,
        result: str | None,
        status_code: int | None,
        latency_ms: float,
        http_result_kind: Literal[
            "remote_nonempty", "remote_empty", "in_process_fallback"
        ],
    ) -> None:
        """Initialize with result content, HTTP status, latency, and kind classification."""
        self.result = result
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.http_result_kind = http_result_kind

    def xǁHttpAugmentResultǁ__init____mutmut_1(
        self,
        result: str | None,
        status_code: int | None,
        latency_ms: float,
        http_result_kind: Literal[
            "remote_nonempty", "remote_empty", "in_process_fallback"
        ],
    ) -> None:
        """Initialize with result content, HTTP status, latency, and kind classification."""
        self.result = None
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.http_result_kind = http_result_kind

    def xǁHttpAugmentResultǁ__init____mutmut_2(
        self,
        result: str | None,
        status_code: int | None,
        latency_ms: float,
        http_result_kind: Literal[
            "remote_nonempty", "remote_empty", "in_process_fallback"
        ],
    ) -> None:
        """Initialize with result content, HTTP status, latency, and kind classification."""
        self.result = result
        self.status_code = None
        self.latency_ms = latency_ms
        self.http_result_kind = http_result_kind

    def xǁHttpAugmentResultǁ__init____mutmut_3(
        self,
        result: str | None,
        status_code: int | None,
        latency_ms: float,
        http_result_kind: Literal[
            "remote_nonempty", "remote_empty", "in_process_fallback"
        ],
    ) -> None:
        """Initialize with result content, HTTP status, latency, and kind classification."""
        self.result = result
        self.status_code = status_code
        self.latency_ms = None
        self.http_result_kind = http_result_kind

    def xǁHttpAugmentResultǁ__init____mutmut_4(
        self,
        result: str | None,
        status_code: int | None,
        latency_ms: float,
        http_result_kind: Literal[
            "remote_nonempty", "remote_empty", "in_process_fallback"
        ],
    ) -> None:
        """Initialize with result content, HTTP status, latency, and kind classification."""
        self.result = result
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.http_result_kind = None

mutants_xǁHttpAugmentResultǁ__init____mutmut['_mutmut_orig'] = HttpAugmentResult.xǁHttpAugmentResultǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁHttpAugmentResultǁ__init____mutmut['xǁHttpAugmentResultǁ__init____mutmut_1'] = HttpAugmentResult.xǁHttpAugmentResultǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁHttpAugmentResultǁ__init____mutmut['xǁHttpAugmentResultǁ__init____mutmut_2'] = HttpAugmentResult.xǁHttpAugmentResultǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁHttpAugmentResultǁ__init____mutmut['xǁHttpAugmentResultǁ__init____mutmut_3'] = HttpAugmentResult.xǁHttpAugmentResultǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁHttpAugmentResultǁ__init____mutmut['xǁHttpAugmentResultǁ__init____mutmut_4'] = HttpAugmentResult.xǁHttpAugmentResultǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁHttpAugmentǁrun__mutmut: MutantDict = {}  # type: ignore


class HttpAugment:
    """Handles HTTP RAG augment delegation.

    When rag_service_url is configured, delegates augment to an external
    RAG service instead of running the in-process pipeline.
    """

    @_mutmut_mutated(mutants_xǁHttpAugmentǁ__init____mutmut)
    def __init__(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_orig(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_1(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "XXXX",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_2(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = None
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_3(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = None
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_4(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = None
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_5(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token and ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_6(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or "XXXX"
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_7(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = None
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_8(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result and (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_9(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: 0)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_10(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = None

    def xǁHttpAugmentǁ__init____mutmut_11(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason and (lambda _: None)

    def xǁHttpAugmentǁ__init____mutmut_12(
        self,
        http: httpx.AsyncClient,
        rag_url: str,
        auth_token: str = "",
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize with HTTP client, RAG URL, optional auth token, and callbacks."""
        self._http = http
        self._rag_url = rag_url
        self._auth_token = auth_token or ""
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: 0)

    @_mutmut_mutated(mutants_xǁHttpAugmentǁrun__mutmut)
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

    async def xǁHttpAugmentǁrun__mutmut_orig(self, query: str, history_context: str) -> HttpAugmentResult:
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

    async def xǁHttpAugmentǁrun__mutmut_1(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = None
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

    async def xǁHttpAugmentǁrun__mutmut_2(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = None
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

    async def xǁHttpAugmentǁrun__mutmut_3(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = None
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

    async def xǁHttpAugmentǁrun__mutmut_4(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            None,
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

    async def xǁHttpAugmentǁrun__mutmut_5(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            None,
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

    async def xǁHttpAugmentǁrun__mutmut_6(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
            None,
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

    async def xǁHttpAugmentǁrun__mutmut_7(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
            query,
            None,
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

    async def xǁHttpAugmentǁrun__mutmut_8(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
            query,
            history_context,
            auth_token=None,
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

    async def xǁHttpAugmentǁrun__mutmut_9(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
            query,
            history_context,
            auth_token=self._auth_token,
            set_fetch_result=None,
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

    async def xǁHttpAugmentǁrun__mutmut_10(self, query: str, history_context: str) -> HttpAugmentResult:
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
            set_fallback_reason=None,
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

    async def xǁHttpAugmentǁrun__mutmut_11(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
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

    async def xǁHttpAugmentǁrun__mutmut_12(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
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

    async def xǁHttpAugmentǁrun__mutmut_13(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
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

    async def xǁHttpAugmentǁrun__mutmut_14(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
            query,
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

    async def xǁHttpAugmentǁrun__mutmut_15(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
            query,
            history_context,
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

    async def xǁHttpAugmentǁrun__mutmut_16(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
            query,
            history_context,
            auth_token=self._auth_token,
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

    async def xǁHttpAugmentǁrun__mutmut_17(self, query: str, history_context: str) -> HttpAugmentResult:
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

    async def xǁHttpAugmentǁrun__mutmut_18(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
            query,
            history_context,
            auth_token=self._auth_token,
            set_fetch_result=lambda fr: None,
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

    async def xǁHttpAugmentǁrun__mutmut_19(self, query: str, history_context: str) -> HttpAugmentResult:
        """Run HTTP augment and return result."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, status_code, latency_ms = await call_rag_service(
            self._http,
            self._rag_url,
            query,
            history_context,
            auth_token=self._auth_token,
            set_fetch_result=lambda fr: self._set_fetch_result(None),
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

    async def xǁHttpAugmentǁrun__mutmut_20(self, query: str, history_context: str) -> HttpAugmentResult:
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
        elapsed = None
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

    async def xǁHttpAugmentǁrun__mutmut_21(self, query: str, history_context: str) -> HttpAugmentResult:
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
        elapsed = time.perf_counter() + t0
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

    async def xǁHttpAugmentǁrun__mutmut_22(self, query: str, history_context: str) -> HttpAugmentResult:
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
        http_status: Literal["success", "fallback"] = None
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

    async def xǁHttpAugmentǁrun__mutmut_23(self, query: str, history_context: str) -> HttpAugmentResult:
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
            "XXsuccessXX" if result is not None else "fallback"
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

    async def xǁHttpAugmentǁrun__mutmut_24(self, query: str, history_context: str) -> HttpAugmentResult:
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
            "SUCCESS" if result is not None else "fallback"
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

    async def xǁHttpAugmentǁrun__mutmut_25(self, query: str, history_context: str) -> HttpAugmentResult:
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
            "success" if result is None else "fallback"
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

    async def xǁHttpAugmentǁrun__mutmut_26(self, query: str, history_context: str) -> HttpAugmentResult:
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
            "success" if result is not None else "XXfallbackXX"
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

    async def xǁHttpAugmentǁrun__mutmut_27(self, query: str, history_context: str) -> HttpAugmentResult:
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
            "success" if result is not None else "FALLBACK"
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

    async def xǁHttpAugmentǁrun__mutmut_28(self, query: str, history_context: str) -> HttpAugmentResult:
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
        http_fallback_reason = None
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

    async def xǁHttpAugmentǁrun__mutmut_29(self, query: str, history_context: str) -> HttpAugmentResult:
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
            http_fallback_reasons[1] if http_fallback_reasons else "in-process fallback"
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

    async def xǁHttpAugmentǁrun__mutmut_30(self, query: str, history_context: str) -> HttpAugmentResult:
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
            http_fallback_reasons[0] if http_fallback_reasons else "XXin-process fallbackXX"
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

    async def xǁHttpAugmentǁrun__mutmut_31(self, query: str, history_context: str) -> HttpAugmentResult:
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
            http_fallback_reasons[0] if http_fallback_reasons else "IN-PROCESS FALLBACK"
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

    async def xǁHttpAugmentǁrun__mutmut_32(self, query: str, history_context: str) -> HttpAugmentResult:
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
        self._stage_result = None
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

    async def xǁHttpAugmentǁrun__mutmut_33(self, query: str, history_context: str) -> HttpAugmentResult:
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
            stage_name=None,
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

    async def xǁHttpAugmentǁrun__mutmut_34(self, query: str, history_context: str) -> HttpAugmentResult:
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
            status=None,
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

    async def xǁHttpAugmentǁrun__mutmut_35(self, query: str, history_context: str) -> HttpAugmentResult:
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
            elapsed_seconds=None,
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

    async def xǁHttpAugmentǁrun__mutmut_36(self, query: str, history_context: str) -> HttpAugmentResult:
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
            fallback_reason=None,
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

    async def xǁHttpAugmentǁrun__mutmut_37(self, query: str, history_context: str) -> HttpAugmentResult:
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

    async def xǁHttpAugmentǁrun__mutmut_38(self, query: str, history_context: str) -> HttpAugmentResult:
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

    async def xǁHttpAugmentǁrun__mutmut_39(self, query: str, history_context: str) -> HttpAugmentResult:
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

    async def xǁHttpAugmentǁrun__mutmut_40(self, query: str, history_context: str) -> HttpAugmentResult:
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

    async def xǁHttpAugmentǁrun__mutmut_41(self, query: str, history_context: str) -> HttpAugmentResult:
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
            stage_name="XXHttpAugmentXX",
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

    async def xǁHttpAugmentǁrun__mutmut_42(self, query: str, history_context: str) -> HttpAugmentResult:
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
            stage_name="httpaugment",
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

    async def xǁHttpAugmentǁrun__mutmut_43(self, query: str, history_context: str) -> HttpAugmentResult:
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
            stage_name="HTTPAUGMENT",
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

    async def xǁHttpAugmentǁrun__mutmut_44(self, query: str, history_context: str) -> HttpAugmentResult:
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
            fallback_reason=(http_fallback_reason if result is not None else None),
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

    async def xǁHttpAugmentǁrun__mutmut_45(self, query: str, history_context: str) -> HttpAugmentResult:
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
        ] = None
        return HttpAugmentResult(
            result=result,
            status_code=status_code,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_46(self, query: str, history_context: str) -> HttpAugmentResult:
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
            "XXremote_nonemptyXX"
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

    async def xǁHttpAugmentǁrun__mutmut_47(self, query: str, history_context: str) -> HttpAugmentResult:
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
            "REMOTE_NONEMPTY"
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

    async def xǁHttpAugmentǁrun__mutmut_48(self, query: str, history_context: str) -> HttpAugmentResult:
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
            if result or len(result) > 0
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

    async def xǁHttpAugmentǁrun__mutmut_49(self, query: str, history_context: str) -> HttpAugmentResult:
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
            if result and len(result) >= 0
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

    async def xǁHttpAugmentǁrun__mutmut_50(self, query: str, history_context: str) -> HttpAugmentResult:
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
            if result and len(result) > 1
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

    async def xǁHttpAugmentǁrun__mutmut_51(self, query: str, history_context: str) -> HttpAugmentResult:
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
            else "XXremote_emptyXX"
            if result == ""
            else "in_process_fallback"
        )
        return HttpAugmentResult(
            result=result,
            status_code=status_code,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_52(self, query: str, history_context: str) -> HttpAugmentResult:
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
            else "REMOTE_EMPTY"
            if result == ""
            else "in_process_fallback"
        )
        return HttpAugmentResult(
            result=result,
            status_code=status_code,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_53(self, query: str, history_context: str) -> HttpAugmentResult:
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
            if result != ""
            else "in_process_fallback"
        )
        return HttpAugmentResult(
            result=result,
            status_code=status_code,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_54(self, query: str, history_context: str) -> HttpAugmentResult:
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
            if result == "XXXX"
            else "in_process_fallback"
        )
        return HttpAugmentResult(
            result=result,
            status_code=status_code,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_55(self, query: str, history_context: str) -> HttpAugmentResult:
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
            else "XXin_process_fallbackXX"
        )
        return HttpAugmentResult(
            result=result,
            status_code=status_code,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_56(self, query: str, history_context: str) -> HttpAugmentResult:
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
            else "IN_PROCESS_FALLBACK"
        )
        return HttpAugmentResult(
            result=result,
            status_code=status_code,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_57(self, query: str, history_context: str) -> HttpAugmentResult:
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
            result=None,
            status_code=status_code,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_58(self, query: str, history_context: str) -> HttpAugmentResult:
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
            status_code=None,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_59(self, query: str, history_context: str) -> HttpAugmentResult:
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
            latency_ms=None,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_60(self, query: str, history_context: str) -> HttpAugmentResult:
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
            http_result_kind=None,
        )

    async def xǁHttpAugmentǁrun__mutmut_61(self, query: str, history_context: str) -> HttpAugmentResult:
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
            status_code=status_code,
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_62(self, query: str, history_context: str) -> HttpAugmentResult:
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
            latency_ms=latency_ms,
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_63(self, query: str, history_context: str) -> HttpAugmentResult:
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
            http_result_kind=self._http_result_kind,
        )

    async def xǁHttpAugmentǁrun__mutmut_64(self, query: str, history_context: str) -> HttpAugmentResult:
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

mutants_xǁHttpAugmentǁ__init____mutmut['_mutmut_orig'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_1'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_2'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_3'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_4'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_5'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_6'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_7'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_8'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_8 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_9'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_9 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_10'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_10 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_11'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_11 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁ__init____mutmut['xǁHttpAugmentǁ__init____mutmut_12'] = HttpAugment.xǁHttpAugmentǁ__init____mutmut_12 # type: ignore # mutmut generated

mutants_xǁHttpAugmentǁrun__mutmut['_mutmut_orig'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_1'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_2'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_3'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_4'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_5'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_6'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_7'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_8'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_9'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_10'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_10 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_11'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_11 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_12'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_12 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_13'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_13 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_14'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_14 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_15'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_15 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_16'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_16 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_17'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_17 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_18'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_18 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_19'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_19 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_20'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_20 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_21'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_21 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_22'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_22 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_23'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_23 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_24'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_24 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_25'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_25 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_26'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_26 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_27'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_27 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_28'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_28 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_29'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_29 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_30'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_30 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_31'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_31 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_32'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_32 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_33'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_33 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_34'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_34 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_35'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_35 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_36'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_36 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_37'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_37 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_38'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_38 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_39'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_39 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_40'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_40 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_41'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_41 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_42'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_42 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_43'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_43 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_44'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_44 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_45'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_45 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_46'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_46 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_47'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_47 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_48'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_48 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_49'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_49 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_50'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_50 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_51'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_51 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_52'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_52 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_53'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_53 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_54'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_54 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_55'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_55 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_56'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_56 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_57'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_57 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_58'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_58 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_59'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_59 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_60'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_60 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_61'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_61 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_62'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_62 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_63'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_63 # type: ignore # mutmut generated
mutants_xǁHttpAugmentǁrun__mutmut['xǁHttpAugmentǁrun__mutmut_64'] = HttpAugment.xǁHttpAugmentǁrun__mutmut_64 # type: ignore # mutmut generated
