#!/usr/bin/env python3
"""scripts/shared/http_transport.py — HTTP MCP transport implementation."""

import asyncio
import dataclasses
import logging
from typing import Any

import httpx

from shared.json_utils import parse_http_json
from shared.mcp_config import McpServerConfig
from shared.transport_dto import ToolCallResult

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


class TransportError(Exception):
    """Raised by transport layers when a transport-level failure occurs.

    Distinguishes transport failures (network down, timeout, process crash)
    from tool-level errors (MCP server responds with is_error=true).
    """
mutants_xǁHttpTransportǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁHttpTransportǁset_session_id__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHttpTransportǁ_parse_http_response__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHttpTransportǁ_transport_error__mutmut: MutantDict = {}  # type: ignore
mutants_xǁHttpTransportǁcall__mutmut: MutantDict = {}  # type: ignore


class HttpTransport:
    """Calls /v1/call_tool on a running HTTP MCP server via httpx."""

    @_mutmut_mutated(mutants_xǁHttpTransportǁ__init____mutmut)
    def __init__(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = timeout_sec
        self._session_id: str = ""

    def xǁHttpTransportǁ__init____mutmut_orig(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = timeout_sec
        self._session_id: str = ""

    def xǁHttpTransportǁ__init____mutmut_1(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 61.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = timeout_sec
        self._session_id: str = ""

    def xǁHttpTransportǁ__init____mutmut_2(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = None
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = timeout_sec
        self._session_id: str = ""

    def xǁHttpTransportǁ__init____mutmut_3(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = None
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = timeout_sec
        self._session_id: str = ""

    def xǁHttpTransportǁ__init____mutmut_4(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = base_url
        self._server_key = None
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = timeout_sec
        self._session_id: str = ""

    def xǁHttpTransportǁ__init____mutmut_5(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = None
        self._timeout = timeout_sec
        self._session_id: str = ""

    def xǁHttpTransportǁ__init____mutmut_6(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is None else ""
        self._timeout = timeout_sec
        self._session_id: str = ""

    def xǁHttpTransportǁ__init____mutmut_7(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else "XXXX"
        self._timeout = timeout_sec
        self._session_id: str = ""

    def xǁHttpTransportǁ__init____mutmut_8(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = None
        self._session_id: str = ""

    def xǁHttpTransportǁ__init____mutmut_9(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = timeout_sec
        self._session_id: str = None

    def xǁHttpTransportǁ__init____mutmut_10(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        """Initialize with HTTP client, server URL, key, and optional auth config."""
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = timeout_sec
        self._session_id: str = "XXXX"

    @_mutmut_mutated(mutants_xǁHttpTransportǁset_session_id__mutmut)
    def set_session_id(self, session_id: str) -> None:
        """Inject session ID to be forwarded as X-Session-Id header on every call."""
        self._session_id = session_id

    def xǁHttpTransportǁset_session_id__mutmut_orig(self, session_id: str) -> None:
        """Inject session ID to be forwarded as X-Session-Id header on every call."""
        self._session_id = session_id

    def xǁHttpTransportǁset_session_id__mutmut_1(self, session_id: str) -> None:
        """Inject session ID to be forwarded as X-Session-Id header on every call."""
        self._session_id = None

    @staticmethod
    @_mutmut_mutated(mutants_xǁHttpTransportǁ_parse_http_response__mutmut)
    def _parse_http_response(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_orig(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_1(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = None
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_2(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(None)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_3(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = None
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_4(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get(None)
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_5(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("XXresultXX")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_6(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("RESULT")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_7(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_8(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError(None)
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_9(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("XXMCP /v1/call_tool missing 'result' str fieldXX")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_10(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("mcp /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_11(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /V1/CALL_TOOL MISSING 'RESULT' STR FIELD")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_12(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = None
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_13(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get(None, False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_14(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", None)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_15(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get(False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_16(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", )
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_17(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("XXis_errorXX", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_18(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("IS_ERROR", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_19(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", True)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_20(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_21(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                None
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_22(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(None).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_23(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = None
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_24(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get(None, "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_25(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", None)
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_26(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_27(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", )
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_28(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("XXx-request-idXX", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_29(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("X-REQUEST-ID", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_30(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "XXXX")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_31(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=None, is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_32(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=None, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_33(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=None
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_34(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            is_error=is_error_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_35(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, request_id=x_request_id
        )

    @staticmethod
    def xǁHttpTransportǁ_parse_http_response__mutmut_36(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = parse_http_json(resp)
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, )

    _RETRYABLE_STATUS: frozenset[int] = frozenset({429, 502, 503, 504})
    _RETRY_MAX: int = 3

    @_mutmut_mutated(mutants_xǁHttpTransportǁ_transport_error__mutmut)
    def _transport_error(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_orig(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_1(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = True,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_2(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = False,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_3(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = None
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_4(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = "XXXX"
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_5(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = None
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_6(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url - "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_7(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " - self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_8(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = "XX — check XX" + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_9(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — CHECK " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_10(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "XX/healthXX"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_11(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "/HEALTH"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_12(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = None
        logger.warning(msg)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_13(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(None)
        exc = TransportError(msg)
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_14(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = None
        if break_flag:
            raise exc
        return exc

    def xǁHttpTransportǁ_transport_error__mutmut_15(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(None)
        if break_flag:
            raise exc
        return exc

    @_mutmut_mutated(mutants_xǁHttpTransportǁcall__mutmut)
    async def call(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_orig(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_1(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = None
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_2(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = None
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_3(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["XXAuthorizationXX"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_4(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_5(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["AUTHORIZATION"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_6(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = None

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_7(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["XXX-Session-IdXX"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_8(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["x-session-id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_9(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-SESSION-ID"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_10(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_11(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(None) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_12(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout >= 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_13(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 1 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_14(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = ""
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_15(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(None):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_16(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = None
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_17(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    None,
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_18(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json=None,
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_19(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=None,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_20(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=None,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_21(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_22(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_23(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_24(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_25(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"XXnameXX": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_26(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"NAME": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_27(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "XXargsXX": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_28(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "ARGS": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_29(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code not in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_30(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = None  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_31(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 * (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_32(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 3 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_33(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt + 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_34(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX + attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_35(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 2)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_36(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        None,
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_37(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        None,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_38(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        None,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_39(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        None,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_40(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        None,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_41(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        None,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_42(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_43(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_44(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_45(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_46(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_47(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_48(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "XXHTTP %s from %s; retrying in %.0fs (attempt %d/%d)XX",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_49(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "http %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_50(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %S FROM %S; RETRYING IN %.0FS (ATTEMPT %D/%D)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_51(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt - 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_52(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 2,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_53(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(None)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_54(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    break
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_55(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = None
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_56(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(None)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_57(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(None, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_58(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=None)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_59(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_60(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, )
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_61(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = None
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_62(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    None, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_63(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, None, str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_64(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", None, break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_65(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=None
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_66(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_67(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_68(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_69(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_70(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "XX[TimeoutException]XX", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_71(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[timeoutexception]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_72(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TIMEOUTEXCEPTION]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_73(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(None), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_74(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=False
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_75(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = None
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_76(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    None,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_77(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    None,
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_78(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    None,
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_79(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=None,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_80(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=None,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_81(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_82(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_83(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_84(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_85(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_86(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "XX[HTTPStatusError]XX",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_87(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[httpstatuserror]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_88(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPSTATUSERROR]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_89(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:301]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_90(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_91(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=True,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_92(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = None
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_93(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(None, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_94(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, None, str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_95(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", None)
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_96(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_97(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_98(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", )
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_99(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(None).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_100(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(None))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_101(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = None
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_102(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(None)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_103(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(None)
        raise last_exc or TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_104(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc and TransportError(f"call failed: {name}")

    async def xǁHttpTransportǁcall__mutmut_105(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(parsed, server_key=self._server_key)
            except httpx.TimeoutException as e:
                last_exc = self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True
                )
            except httpx.HTTPStatusError as e:
                last_exc = self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    f"status={e.response.status_code} response={e.response.text[:300]!r}",
                    break_flag=e.response.status_code not in self._RETRYABLE_STATUS,
                    health_check=False,
                )
            except (httpx.RequestError, ValueError) as e:
                last_exc = self._transport_error(name, f"[{type(e).__name__}]", str(e))
        else:
            msg = (
                f"[Retry exhausted] tool={name} url={self._base_url} "
                f"after {self._RETRY_MAX} attempts: {last_exc}"
            )
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(None)

mutants_xǁHttpTransportǁ__init____mutmut['_mutmut_orig'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ__init____mutmut['xǁHttpTransportǁ__init____mutmut_1'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ__init____mutmut['xǁHttpTransportǁ__init____mutmut_2'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ__init____mutmut['xǁHttpTransportǁ__init____mutmut_3'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ__init____mutmut['xǁHttpTransportǁ__init____mutmut_4'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ__init____mutmut['xǁHttpTransportǁ__init____mutmut_5'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ__init____mutmut['xǁHttpTransportǁ__init____mutmut_6'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ__init____mutmut['xǁHttpTransportǁ__init____mutmut_7'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ__init____mutmut['xǁHttpTransportǁ__init____mutmut_8'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_8 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ__init____mutmut['xǁHttpTransportǁ__init____mutmut_9'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_9 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ__init____mutmut['xǁHttpTransportǁ__init____mutmut_10'] = HttpTransport.xǁHttpTransportǁ__init____mutmut_10 # type: ignore # mutmut generated

mutants_xǁHttpTransportǁset_session_id__mutmut['_mutmut_orig'] = HttpTransport.xǁHttpTransportǁset_session_id__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHttpTransportǁset_session_id__mutmut['xǁHttpTransportǁset_session_id__mutmut_1'] = HttpTransport.xǁHttpTransportǁset_session_id__mutmut_1 # type: ignore # mutmut generated

mutants_xǁHttpTransportǁ_parse_http_response__mutmut['_mutmut_orig'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_1'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_2'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_3'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_4'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_5'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_6'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_7'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_8'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_9'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_10'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_10 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_11'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_11 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_12'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_12 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_13'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_13 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_14'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_14 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_15'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_15 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_16'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_16 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_17'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_17 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_18'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_18 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_19'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_19 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_20'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_20 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_21'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_21 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_22'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_22 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_23'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_23 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_24'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_24 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_25'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_25 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_26'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_26 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_27'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_27 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_28'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_28 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_29'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_29 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_30'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_30 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_31'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_31 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_32'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_32 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_33'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_33 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_34'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_34 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_35'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_35 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_parse_http_response__mutmut['xǁHttpTransportǁ_parse_http_response__mutmut_36'] = HttpTransport.xǁHttpTransportǁ_parse_http_response__mutmut_36 # type: ignore # mutmut generated

mutants_xǁHttpTransportǁ_transport_error__mutmut['_mutmut_orig'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_1'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_2'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_3'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_4'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_5'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_6'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_7'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_8'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_9'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_10'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_10 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_11'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_11 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_12'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_12 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_13'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_13 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_14'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_14 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁ_transport_error__mutmut['xǁHttpTransportǁ_transport_error__mutmut_15'] = HttpTransport.xǁHttpTransportǁ_transport_error__mutmut_15 # type: ignore # mutmut generated

mutants_xǁHttpTransportǁcall__mutmut['_mutmut_orig'] = HttpTransport.xǁHttpTransportǁcall__mutmut_orig # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_1'] = HttpTransport.xǁHttpTransportǁcall__mutmut_1 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_2'] = HttpTransport.xǁHttpTransportǁcall__mutmut_2 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_3'] = HttpTransport.xǁHttpTransportǁcall__mutmut_3 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_4'] = HttpTransport.xǁHttpTransportǁcall__mutmut_4 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_5'] = HttpTransport.xǁHttpTransportǁcall__mutmut_5 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_6'] = HttpTransport.xǁHttpTransportǁcall__mutmut_6 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_7'] = HttpTransport.xǁHttpTransportǁcall__mutmut_7 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_8'] = HttpTransport.xǁHttpTransportǁcall__mutmut_8 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_9'] = HttpTransport.xǁHttpTransportǁcall__mutmut_9 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_10'] = HttpTransport.xǁHttpTransportǁcall__mutmut_10 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_11'] = HttpTransport.xǁHttpTransportǁcall__mutmut_11 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_12'] = HttpTransport.xǁHttpTransportǁcall__mutmut_12 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_13'] = HttpTransport.xǁHttpTransportǁcall__mutmut_13 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_14'] = HttpTransport.xǁHttpTransportǁcall__mutmut_14 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_15'] = HttpTransport.xǁHttpTransportǁcall__mutmut_15 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_16'] = HttpTransport.xǁHttpTransportǁcall__mutmut_16 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_17'] = HttpTransport.xǁHttpTransportǁcall__mutmut_17 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_18'] = HttpTransport.xǁHttpTransportǁcall__mutmut_18 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_19'] = HttpTransport.xǁHttpTransportǁcall__mutmut_19 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_20'] = HttpTransport.xǁHttpTransportǁcall__mutmut_20 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_21'] = HttpTransport.xǁHttpTransportǁcall__mutmut_21 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_22'] = HttpTransport.xǁHttpTransportǁcall__mutmut_22 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_23'] = HttpTransport.xǁHttpTransportǁcall__mutmut_23 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_24'] = HttpTransport.xǁHttpTransportǁcall__mutmut_24 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_25'] = HttpTransport.xǁHttpTransportǁcall__mutmut_25 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_26'] = HttpTransport.xǁHttpTransportǁcall__mutmut_26 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_27'] = HttpTransport.xǁHttpTransportǁcall__mutmut_27 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_28'] = HttpTransport.xǁHttpTransportǁcall__mutmut_28 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_29'] = HttpTransport.xǁHttpTransportǁcall__mutmut_29 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_30'] = HttpTransport.xǁHttpTransportǁcall__mutmut_30 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_31'] = HttpTransport.xǁHttpTransportǁcall__mutmut_31 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_32'] = HttpTransport.xǁHttpTransportǁcall__mutmut_32 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_33'] = HttpTransport.xǁHttpTransportǁcall__mutmut_33 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_34'] = HttpTransport.xǁHttpTransportǁcall__mutmut_34 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_35'] = HttpTransport.xǁHttpTransportǁcall__mutmut_35 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_36'] = HttpTransport.xǁHttpTransportǁcall__mutmut_36 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_37'] = HttpTransport.xǁHttpTransportǁcall__mutmut_37 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_38'] = HttpTransport.xǁHttpTransportǁcall__mutmut_38 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_39'] = HttpTransport.xǁHttpTransportǁcall__mutmut_39 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_40'] = HttpTransport.xǁHttpTransportǁcall__mutmut_40 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_41'] = HttpTransport.xǁHttpTransportǁcall__mutmut_41 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_42'] = HttpTransport.xǁHttpTransportǁcall__mutmut_42 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_43'] = HttpTransport.xǁHttpTransportǁcall__mutmut_43 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_44'] = HttpTransport.xǁHttpTransportǁcall__mutmut_44 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_45'] = HttpTransport.xǁHttpTransportǁcall__mutmut_45 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_46'] = HttpTransport.xǁHttpTransportǁcall__mutmut_46 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_47'] = HttpTransport.xǁHttpTransportǁcall__mutmut_47 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_48'] = HttpTransport.xǁHttpTransportǁcall__mutmut_48 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_49'] = HttpTransport.xǁHttpTransportǁcall__mutmut_49 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_50'] = HttpTransport.xǁHttpTransportǁcall__mutmut_50 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_51'] = HttpTransport.xǁHttpTransportǁcall__mutmut_51 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_52'] = HttpTransport.xǁHttpTransportǁcall__mutmut_52 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_53'] = HttpTransport.xǁHttpTransportǁcall__mutmut_53 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_54'] = HttpTransport.xǁHttpTransportǁcall__mutmut_54 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_55'] = HttpTransport.xǁHttpTransportǁcall__mutmut_55 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_56'] = HttpTransport.xǁHttpTransportǁcall__mutmut_56 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_57'] = HttpTransport.xǁHttpTransportǁcall__mutmut_57 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_58'] = HttpTransport.xǁHttpTransportǁcall__mutmut_58 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_59'] = HttpTransport.xǁHttpTransportǁcall__mutmut_59 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_60'] = HttpTransport.xǁHttpTransportǁcall__mutmut_60 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_61'] = HttpTransport.xǁHttpTransportǁcall__mutmut_61 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_62'] = HttpTransport.xǁHttpTransportǁcall__mutmut_62 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_63'] = HttpTransport.xǁHttpTransportǁcall__mutmut_63 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_64'] = HttpTransport.xǁHttpTransportǁcall__mutmut_64 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_65'] = HttpTransport.xǁHttpTransportǁcall__mutmut_65 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_66'] = HttpTransport.xǁHttpTransportǁcall__mutmut_66 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_67'] = HttpTransport.xǁHttpTransportǁcall__mutmut_67 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_68'] = HttpTransport.xǁHttpTransportǁcall__mutmut_68 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_69'] = HttpTransport.xǁHttpTransportǁcall__mutmut_69 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_70'] = HttpTransport.xǁHttpTransportǁcall__mutmut_70 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_71'] = HttpTransport.xǁHttpTransportǁcall__mutmut_71 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_72'] = HttpTransport.xǁHttpTransportǁcall__mutmut_72 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_73'] = HttpTransport.xǁHttpTransportǁcall__mutmut_73 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_74'] = HttpTransport.xǁHttpTransportǁcall__mutmut_74 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_75'] = HttpTransport.xǁHttpTransportǁcall__mutmut_75 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_76'] = HttpTransport.xǁHttpTransportǁcall__mutmut_76 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_77'] = HttpTransport.xǁHttpTransportǁcall__mutmut_77 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_78'] = HttpTransport.xǁHttpTransportǁcall__mutmut_78 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_79'] = HttpTransport.xǁHttpTransportǁcall__mutmut_79 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_80'] = HttpTransport.xǁHttpTransportǁcall__mutmut_80 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_81'] = HttpTransport.xǁHttpTransportǁcall__mutmut_81 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_82'] = HttpTransport.xǁHttpTransportǁcall__mutmut_82 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_83'] = HttpTransport.xǁHttpTransportǁcall__mutmut_83 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_84'] = HttpTransport.xǁHttpTransportǁcall__mutmut_84 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_85'] = HttpTransport.xǁHttpTransportǁcall__mutmut_85 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_86'] = HttpTransport.xǁHttpTransportǁcall__mutmut_86 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_87'] = HttpTransport.xǁHttpTransportǁcall__mutmut_87 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_88'] = HttpTransport.xǁHttpTransportǁcall__mutmut_88 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_89'] = HttpTransport.xǁHttpTransportǁcall__mutmut_89 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_90'] = HttpTransport.xǁHttpTransportǁcall__mutmut_90 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_91'] = HttpTransport.xǁHttpTransportǁcall__mutmut_91 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_92'] = HttpTransport.xǁHttpTransportǁcall__mutmut_92 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_93'] = HttpTransport.xǁHttpTransportǁcall__mutmut_93 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_94'] = HttpTransport.xǁHttpTransportǁcall__mutmut_94 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_95'] = HttpTransport.xǁHttpTransportǁcall__mutmut_95 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_96'] = HttpTransport.xǁHttpTransportǁcall__mutmut_96 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_97'] = HttpTransport.xǁHttpTransportǁcall__mutmut_97 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_98'] = HttpTransport.xǁHttpTransportǁcall__mutmut_98 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_99'] = HttpTransport.xǁHttpTransportǁcall__mutmut_99 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_100'] = HttpTransport.xǁHttpTransportǁcall__mutmut_100 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_101'] = HttpTransport.xǁHttpTransportǁcall__mutmut_101 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_102'] = HttpTransport.xǁHttpTransportǁcall__mutmut_102 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_103'] = HttpTransport.xǁHttpTransportǁcall__mutmut_103 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_104'] = HttpTransport.xǁHttpTransportǁcall__mutmut_104 # type: ignore # mutmut generated
mutants_xǁHttpTransportǁcall__mutmut['xǁHttpTransportǁcall__mutmut_105'] = HttpTransport.xǁHttpTransportǁcall__mutmut_105 # type: ignore # mutmut generated
