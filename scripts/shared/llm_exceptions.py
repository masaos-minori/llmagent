#!/usr/bin/env python3
"""shared/llm_exceptions.py

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


class LLMTransportError(Exception):
    """Structured exception for all LLM HTTP/SSE transport failures; partial_text holds content before failure; retryable signals reconnect eligibility."""

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
