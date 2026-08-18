"""scripts/shared/llm_client.py

LLM communication layer with robust SSE streaming.

Key components:
  LLMClient — HTTP retry, payload construction, reconnect-aware SSE streaming
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import httpx

from shared.llm_exceptions import LLMTransportError
from shared.llm_hot_config import LlmHotConfigHandler
from shared.llm_payload import LlmPayloadHandler
from shared.llm_reconnect import LlmReconnectHandler
from shared.llm_retry import LlmRetryHandler
from shared.llm_types import LLMResponse
from shared.types import LLMMessage

logger = logging.getLogger(__name__)

CHAT_COMPLETIONS_PATH = "/v1/chat/completions"
EMBEDDING_PATH = "/embedding"


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_build_llm_url__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_build_llm_url__mutmut)
def build_llm_url(base_url: str) -> str:
    """Append the chat completions endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.rstrip("/")
    return f"{base}{CHAT_COMPLETIONS_PATH}"


def x_build_llm_url__mutmut_orig(base_url: str) -> str:
    """Append the chat completions endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.rstrip("/")
    return f"{base}{CHAT_COMPLETIONS_PATH}"


def x_build_llm_url__mutmut_1(base_url: str) -> str:
    """Append the chat completions endpoint path to a base URL."""
    if base_url:
        return ""
    base = base_url.rstrip("/")
    return f"{base}{CHAT_COMPLETIONS_PATH}"


def x_build_llm_url__mutmut_2(base_url: str) -> str:
    """Append the chat completions endpoint path to a base URL."""
    if not base_url:
        return "XXXX"
    base = base_url.rstrip("/")
    return f"{base}{CHAT_COMPLETIONS_PATH}"


def x_build_llm_url__mutmut_3(base_url: str) -> str:
    """Append the chat completions endpoint path to a base URL."""
    if not base_url:
        return ""
    base = None
    return f"{base}{CHAT_COMPLETIONS_PATH}"


def x_build_llm_url__mutmut_4(base_url: str) -> str:
    """Append the chat completions endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.rstrip(None)
    return f"{base}{CHAT_COMPLETIONS_PATH}"


def x_build_llm_url__mutmut_5(base_url: str) -> str:
    """Append the chat completions endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.lstrip("/")
    return f"{base}{CHAT_COMPLETIONS_PATH}"


def x_build_llm_url__mutmut_6(base_url: str) -> str:
    """Append the chat completions endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.rstrip("XX/XX")
    return f"{base}{CHAT_COMPLETIONS_PATH}"

mutants_x_build_llm_url__mutmut['_mutmut_orig'] = x_build_llm_url__mutmut_orig # type: ignore # mutmut generated
mutants_x_build_llm_url__mutmut['x_build_llm_url__mutmut_1'] = x_build_llm_url__mutmut_1 # type: ignore # mutmut generated
mutants_x_build_llm_url__mutmut['x_build_llm_url__mutmut_2'] = x_build_llm_url__mutmut_2 # type: ignore # mutmut generated
mutants_x_build_llm_url__mutmut['x_build_llm_url__mutmut_3'] = x_build_llm_url__mutmut_3 # type: ignore # mutmut generated
mutants_x_build_llm_url__mutmut['x_build_llm_url__mutmut_4'] = x_build_llm_url__mutmut_4 # type: ignore # mutmut generated
mutants_x_build_llm_url__mutmut['x_build_llm_url__mutmut_5'] = x_build_llm_url__mutmut_5 # type: ignore # mutmut generated
mutants_x_build_llm_url__mutmut['x_build_llm_url__mutmut_6'] = x_build_llm_url__mutmut_6 # type: ignore # mutmut generated
mutants_x_build_embed_url__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_build_embed_url__mutmut)
def build_embed_url(base_url: str) -> str:
    """Append the embedding endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.rstrip("/")
    return f"{base}{EMBEDDING_PATH}"


def x_build_embed_url__mutmut_orig(base_url: str) -> str:
    """Append the embedding endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.rstrip("/")
    return f"{base}{EMBEDDING_PATH}"


def x_build_embed_url__mutmut_1(base_url: str) -> str:
    """Append the embedding endpoint path to a base URL."""
    if base_url:
        return ""
    base = base_url.rstrip("/")
    return f"{base}{EMBEDDING_PATH}"


def x_build_embed_url__mutmut_2(base_url: str) -> str:
    """Append the embedding endpoint path to a base URL."""
    if not base_url:
        return "XXXX"
    base = base_url.rstrip("/")
    return f"{base}{EMBEDDING_PATH}"


def x_build_embed_url__mutmut_3(base_url: str) -> str:
    """Append the embedding endpoint path to a base URL."""
    if not base_url:
        return ""
    base = None
    return f"{base}{EMBEDDING_PATH}"


def x_build_embed_url__mutmut_4(base_url: str) -> str:
    """Append the embedding endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.rstrip(None)
    return f"{base}{EMBEDDING_PATH}"


def x_build_embed_url__mutmut_5(base_url: str) -> str:
    """Append the embedding endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.lstrip("/")
    return f"{base}{EMBEDDING_PATH}"


def x_build_embed_url__mutmut_6(base_url: str) -> str:
    """Append the embedding endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.rstrip("XX/XX")
    return f"{base}{EMBEDDING_PATH}"

mutants_x_build_embed_url__mutmut['_mutmut_orig'] = x_build_embed_url__mutmut_orig # type: ignore # mutmut generated
mutants_x_build_embed_url__mutmut['x_build_embed_url__mutmut_1'] = x_build_embed_url__mutmut_1 # type: ignore # mutmut generated
mutants_x_build_embed_url__mutmut['x_build_embed_url__mutmut_2'] = x_build_embed_url__mutmut_2 # type: ignore # mutmut generated
mutants_x_build_embed_url__mutmut['x_build_embed_url__mutmut_3'] = x_build_embed_url__mutmut_3 # type: ignore # mutmut generated
mutants_x_build_embed_url__mutmut['x_build_embed_url__mutmut_4'] = x_build_embed_url__mutmut_4 # type: ignore # mutmut generated
mutants_x_build_embed_url__mutmut['x_build_embed_url__mutmut_5'] = x_build_embed_url__mutmut_5 # type: ignore # mutmut generated
mutants_x_build_embed_url__mutmut['x_build_embed_url__mutmut_6'] = x_build_embed_url__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMClientǁapply_config__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMClientǁrequest_with_retry__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMClientǁbuild_payload__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMClientǁcall__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLLMClientǁstream__mutmut: MutantDict = {}  # type: ignore


class LLMClient:
    """LLM HTTP client with exponential-backoff retry and robust SSE streaming; stat_* counters accumulate for the instance lifetime."""

    @_mutmut_mutated(mutants_xǁLLMClientǁ__init____mutmut)
    def __init__(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_orig(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_1(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 31.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_2(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 3,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_3(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 2,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_4(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = False,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_5(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = True,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_6(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = None
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_7(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = None
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_8(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = None
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_9(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = None
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_10(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = None
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_11(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = None
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_12(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = None
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_13(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = None
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_14(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = None
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_15(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = None
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_16(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = None
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_17(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = None
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_18(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = None
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_19(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 1
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_20(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = None
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_21(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 1
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_22(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = None

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_23(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 1

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_24(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = None
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_25(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 1
        self.stat_partial_completions: int = 0

    def xǁLLMClientǁ__init____mutmut_26(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = None

    def xǁLLMClientǁ__init____mutmut_27(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 1

    @_mutmut_mutated(mutants_xǁLLMClientǁapply_config__mutmut)
    def apply_config(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_orig(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_1(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            None,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_2(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=None,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_3(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=None,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_4(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=None,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_5(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=None,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_6(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=None,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_7(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=None,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_8(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=None,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_9(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=None,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_10(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=None,
        )

    def xǁLLMClientǁapply_config__mutmut_11(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_12(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_13(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_14(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_15(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_16(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_17(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_18(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_19(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    def xǁLLMClientǁapply_config__mutmut_20(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            )

    # ── Retry logic ───────────────────────────────────────────────────────────

    @_mutmut_mutated(mutants_xǁLLMClientǁrequest_with_retry__mutmut)
    async def request_with_retry(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                payload,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_orig(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                payload,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_1(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                None,
                url,
                payload,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_2(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                None,
                payload,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_3(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                None,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_4(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                payload,
                None,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_5(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                payload,
                self._max_retries,
                None,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_6(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                url,
                payload,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_7(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                payload,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_8(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_9(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                payload,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_10(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                payload,
                self._max_retries,
                )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_11(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                payload,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries = 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_12(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                payload,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries -= 1
            raise

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def xǁLLMClientǁrequest_with_retry__mutmut_13(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                payload,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 2
            raise

    # ── Payload construction ──────────────────────────────────────────────────

    @_mutmut_mutated(mutants_xǁLLMClientǁbuild_payload__mutmut)
    def build_payload(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            tool_defs,
            self._temperature,
            self._max_tokens,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_orig(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            tool_defs,
            self._temperature,
            self._max_tokens,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_1(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = True,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            tool_defs,
            self._temperature,
            self._max_tokens,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_2(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            None,
            tool_defs,
            self._temperature,
            self._max_tokens,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_3(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            None,
            self._temperature,
            self._max_tokens,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_4(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            tool_defs,
            None,
            self._max_tokens,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_5(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            tool_defs,
            self._temperature,
            None,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_6(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            tool_defs,
            self._temperature,
            self._max_tokens,
            None,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_7(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            tool_defs,
            self._temperature,
            self._max_tokens,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_8(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            self._temperature,
            self._max_tokens,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_9(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            tool_defs,
            self._max_tokens,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_10(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            tool_defs,
            self._temperature,
            stream,
        )

    # ── Payload construction ──────────────────────────────────────────────────

    def xǁLLMClientǁbuild_payload__mutmut_11(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            tool_defs,
            self._temperature,
            self._max_tokens,
            )

    # ── Non-streaming call ────────────────────────────────────────────────────

    @_mutmut_mutated(mutants_xǁLLMClientǁcall__mutmut)
    async def call(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(history, tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_orig(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(history, tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_1(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = None
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_2(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            None,
            self.build_payload(history, tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_3(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            None,
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_4(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            self.build_payload(history, tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_5(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_6(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(None, tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_7(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(history, None),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_8(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_9(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(history, ),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_10(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(history, tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(None, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_11(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(history, tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, None)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_12(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(history, tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def xǁLLMClientǁcall__mutmut_13(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(history, tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, )

    # ── Streaming call with reconnect ─────────────────────────────────────────

    @_mutmut_mutated(mutants_xǁLLMClientǁstream__mutmut)
    async def stream(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_orig(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_1(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = None
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_2(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                None,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_3(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                None,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_4(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                None,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_5(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                None,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_6(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                None,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_7(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                None,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_8(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                None,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_9(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                None,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_10(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                None,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_11(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                None,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_12(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                None,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_13(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                None,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_14(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                None,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_15(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                None,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_16(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_17(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_18(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_19(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_20(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_21(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_22(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_23(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_24(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_25(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_26(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_27(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_28(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_29(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_30(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects = reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_31(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects -= reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_32(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts = heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_33(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts -= heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_34(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors = parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_35(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors -= parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_36(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(None, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_37(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, None):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_38(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr("stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_39(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, ):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_40(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "XXstat_heartbeat_timeoutsXX"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_41(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "STAT_HEARTBEAT_TIMEOUTS"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_42(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts = exc.stat_heartbeat_timeouts
            raise

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def xǁLLMClientǁstream__mutmut_43(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts -= exc.stat_heartbeat_timeouts
            raise

mutants_xǁLLMClientǁ__init____mutmut['_mutmut_orig'] = LLMClient.xǁLLMClientǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_1'] = LLMClient.xǁLLMClientǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_2'] = LLMClient.xǁLLMClientǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_3'] = LLMClient.xǁLLMClientǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_4'] = LLMClient.xǁLLMClientǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_5'] = LLMClient.xǁLLMClientǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_6'] = LLMClient.xǁLLMClientǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_7'] = LLMClient.xǁLLMClientǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_8'] = LLMClient.xǁLLMClientǁ__init____mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_9'] = LLMClient.xǁLLMClientǁ__init____mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_10'] = LLMClient.xǁLLMClientǁ__init____mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_11'] = LLMClient.xǁLLMClientǁ__init____mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_12'] = LLMClient.xǁLLMClientǁ__init____mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_13'] = LLMClient.xǁLLMClientǁ__init____mutmut_13 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_14'] = LLMClient.xǁLLMClientǁ__init____mutmut_14 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_15'] = LLMClient.xǁLLMClientǁ__init____mutmut_15 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_16'] = LLMClient.xǁLLMClientǁ__init____mutmut_16 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_17'] = LLMClient.xǁLLMClientǁ__init____mutmut_17 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_18'] = LLMClient.xǁLLMClientǁ__init____mutmut_18 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_19'] = LLMClient.xǁLLMClientǁ__init____mutmut_19 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_20'] = LLMClient.xǁLLMClientǁ__init____mutmut_20 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_21'] = LLMClient.xǁLLMClientǁ__init____mutmut_21 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_22'] = LLMClient.xǁLLMClientǁ__init____mutmut_22 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_23'] = LLMClient.xǁLLMClientǁ__init____mutmut_23 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_24'] = LLMClient.xǁLLMClientǁ__init____mutmut_24 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_25'] = LLMClient.xǁLLMClientǁ__init____mutmut_25 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_26'] = LLMClient.xǁLLMClientǁ__init____mutmut_26 # type: ignore # mutmut generated
mutants_xǁLLMClientǁ__init____mutmut['xǁLLMClientǁ__init____mutmut_27'] = LLMClient.xǁLLMClientǁ__init____mutmut_27 # type: ignore # mutmut generated

mutants_xǁLLMClientǁapply_config__mutmut['_mutmut_orig'] = LLMClient.xǁLLMClientǁapply_config__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_1'] = LLMClient.xǁLLMClientǁapply_config__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_2'] = LLMClient.xǁLLMClientǁapply_config__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_3'] = LLMClient.xǁLLMClientǁapply_config__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_4'] = LLMClient.xǁLLMClientǁapply_config__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_5'] = LLMClient.xǁLLMClientǁapply_config__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_6'] = LLMClient.xǁLLMClientǁapply_config__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_7'] = LLMClient.xǁLLMClientǁapply_config__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_8'] = LLMClient.xǁLLMClientǁapply_config__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_9'] = LLMClient.xǁLLMClientǁapply_config__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_10'] = LLMClient.xǁLLMClientǁapply_config__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_11'] = LLMClient.xǁLLMClientǁapply_config__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_12'] = LLMClient.xǁLLMClientǁapply_config__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_13'] = LLMClient.xǁLLMClientǁapply_config__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_14'] = LLMClient.xǁLLMClientǁapply_config__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_15'] = LLMClient.xǁLLMClientǁapply_config__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_16'] = LLMClient.xǁLLMClientǁapply_config__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_17'] = LLMClient.xǁLLMClientǁapply_config__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_18'] = LLMClient.xǁLLMClientǁapply_config__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_19'] = LLMClient.xǁLLMClientǁapply_config__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLLMClientǁapply_config__mutmut['xǁLLMClientǁapply_config__mutmut_20'] = LLMClient.xǁLLMClientǁapply_config__mutmut_20 # type: ignore # mutmut generated

mutants_xǁLLMClientǁrequest_with_retry__mutmut['_mutmut_orig'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_1'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_2'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_3'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_4'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_5'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_6'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_7'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_8'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_9'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_10'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_11'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_12'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMClientǁrequest_with_retry__mutmut['xǁLLMClientǁrequest_with_retry__mutmut_13'] = LLMClient.xǁLLMClientǁrequest_with_retry__mutmut_13 # type: ignore # mutmut generated

mutants_xǁLLMClientǁbuild_payload__mutmut['_mutmut_orig'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_1'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_2'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_3'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_4'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_5'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_6'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_7'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_8'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_9'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_10'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMClientǁbuild_payload__mutmut['xǁLLMClientǁbuild_payload__mutmut_11'] = LLMClient.xǁLLMClientǁbuild_payload__mutmut_11 # type: ignore # mutmut generated

mutants_xǁLLMClientǁcall__mutmut['_mutmut_orig'] = LLMClient.xǁLLMClientǁcall__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_1'] = LLMClient.xǁLLMClientǁcall__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_2'] = LLMClient.xǁLLMClientǁcall__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_3'] = LLMClient.xǁLLMClientǁcall__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_4'] = LLMClient.xǁLLMClientǁcall__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_5'] = LLMClient.xǁLLMClientǁcall__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_6'] = LLMClient.xǁLLMClientǁcall__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_7'] = LLMClient.xǁLLMClientǁcall__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_8'] = LLMClient.xǁLLMClientǁcall__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_9'] = LLMClient.xǁLLMClientǁcall__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_10'] = LLMClient.xǁLLMClientǁcall__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_11'] = LLMClient.xǁLLMClientǁcall__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_12'] = LLMClient.xǁLLMClientǁcall__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMClientǁcall__mutmut['xǁLLMClientǁcall__mutmut_13'] = LLMClient.xǁLLMClientǁcall__mutmut_13 # type: ignore # mutmut generated

mutants_xǁLLMClientǁstream__mutmut['_mutmut_orig'] = LLMClient.xǁLLMClientǁstream__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_1'] = LLMClient.xǁLLMClientǁstream__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_2'] = LLMClient.xǁLLMClientǁstream__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_3'] = LLMClient.xǁLLMClientǁstream__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_4'] = LLMClient.xǁLLMClientǁstream__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_5'] = LLMClient.xǁLLMClientǁstream__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_6'] = LLMClient.xǁLLMClientǁstream__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_7'] = LLMClient.xǁLLMClientǁstream__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_8'] = LLMClient.xǁLLMClientǁstream__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_9'] = LLMClient.xǁLLMClientǁstream__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_10'] = LLMClient.xǁLLMClientǁstream__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_11'] = LLMClient.xǁLLMClientǁstream__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_12'] = LLMClient.xǁLLMClientǁstream__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_13'] = LLMClient.xǁLLMClientǁstream__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_14'] = LLMClient.xǁLLMClientǁstream__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_15'] = LLMClient.xǁLLMClientǁstream__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_16'] = LLMClient.xǁLLMClientǁstream__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_17'] = LLMClient.xǁLLMClientǁstream__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_18'] = LLMClient.xǁLLMClientǁstream__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_19'] = LLMClient.xǁLLMClientǁstream__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_20'] = LLMClient.xǁLLMClientǁstream__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_21'] = LLMClient.xǁLLMClientǁstream__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_22'] = LLMClient.xǁLLMClientǁstream__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_23'] = LLMClient.xǁLLMClientǁstream__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_24'] = LLMClient.xǁLLMClientǁstream__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_25'] = LLMClient.xǁLLMClientǁstream__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_26'] = LLMClient.xǁLLMClientǁstream__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_27'] = LLMClient.xǁLLMClientǁstream__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_28'] = LLMClient.xǁLLMClientǁstream__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_29'] = LLMClient.xǁLLMClientǁstream__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_30'] = LLMClient.xǁLLMClientǁstream__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_31'] = LLMClient.xǁLLMClientǁstream__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_32'] = LLMClient.xǁLLMClientǁstream__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_33'] = LLMClient.xǁLLMClientǁstream__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_34'] = LLMClient.xǁLLMClientǁstream__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_35'] = LLMClient.xǁLLMClientǁstream__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_36'] = LLMClient.xǁLLMClientǁstream__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_37'] = LLMClient.xǁLLMClientǁstream__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_38'] = LLMClient.xǁLLMClientǁstream__mutmut_38 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_39'] = LLMClient.xǁLLMClientǁstream__mutmut_39 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_40'] = LLMClient.xǁLLMClientǁstream__mutmut_40 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_41'] = LLMClient.xǁLLMClientǁstream__mutmut_41 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_42'] = LLMClient.xǁLLMClientǁstream__mutmut_42 # type: ignore # mutmut generated
mutants_xǁLLMClientǁstream__mutmut['xǁLLMClientǁstream__mutmut_43'] = LLMClient.xǁLLMClientǁstream__mutmut_43 # type: ignore # mutmut generated
