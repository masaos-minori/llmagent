#!/usr/bin/env python3
"""scripts/shared/llm_exceptions.py

Structured exception for LLM HTTP/SSE transport failures.

Defines LLMErrorKind literal and LLMTransportError with per-failure
metadata (kind, phase, url, status_code, retryable, partial_text, detail).
"""

from __future__ import annotations

from typing import Literal

LLMErrorKind = Literal[
    "HTTP_STATUS_RETRYABLE",
    "HTTP_STATUS_FATAL",
    "CONNECT_ERROR",
    "READ_TIMEOUT",
    "HEARTBEAT_TIMEOUT",
    "MALFORMED_SSE_FRAME",
    "UTF8_PARTIAL_DECODE_ERROR",
    "PREMATURE_EOF",
    "UNKNOWN_STREAM_ERROR",
]


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁLLMTransportErrorǁ__init____mutmut: MutantDict = {}  # type: ignore


class LLMTransportError(Exception):
    """Structured exception for all LLM HTTP/SSE transport failures; partial_text holds content before failure; retryable signals reconnect eligibility."""

    @_mutmut_mutated(mutants_xǁLLMTransportErrorǁ__init____mutmut)
    def __init__(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_orig(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_1(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = True,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_2(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "XXXX",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_3(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "XXXX",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_4(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(None)
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_5(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = None
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_6(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = None
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_7(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = None
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_8(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = None
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_9(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = None
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_10(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = None
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_11(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = None
        self.stat_heartbeat_timeouts: int = 0

    def xǁLLMTransportErrorǁ__init____mutmut_12(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = None

    def xǁLLMTransportErrorǁ__init____mutmut_13(
        self,
        kind: LLMErrorKind,
        phase: Literal["pre_stream", "in_stream"],
        url: str,
        status_code: int | None = None,
        retryable: bool = False,
        partial_text: str = "",
        detail: str = "",
    ) -> None:
        """Initialize with error kind, phase, URL, and optional metadata."""
        super().__init__(f"{kind} phase={phase} retryable={retryable}")
        self.kind: LLMErrorKind = kind
        self.phase: Literal["pre_stream", "in_stream"] = phase
        self.url = url
        self.status_code = status_code
        self.retryable = retryable
        self.partial_text = partial_text
        self.detail = detail
        self.stat_heartbeat_timeouts: int = 1

mutants_xǁLLMTransportErrorǁ__init____mutmut['_mutmut_orig'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_1'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_2'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_3'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_4'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_5'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_6'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_7'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_8'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_9'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_10'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_11'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_12'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMTransportErrorǁ__init____mutmut['xǁLLMTransportErrorǁ__init____mutmut_13'] = LLMTransportError.xǁLLMTransportErrorǁ__init____mutmut_13 # type: ignore # mutmut generated
