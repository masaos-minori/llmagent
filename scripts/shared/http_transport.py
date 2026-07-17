#!/usr/bin/env python3
"""shared/http_transport.py — HTTP MCP transport implementation."""

import asyncio
import logging
from typing import Any

import httpx

from shared.json_utils import parse_http_json
from shared.mcp_config import McpServerConfig
from shared.transport_dto import ToolCallResult

logger = logging.getLogger(__name__)


class TransportError(Exception):
    """Raised by transport layers when a transport-level failure occurs.

    Distinguishes transport failures (network down, timeout, process crash)
    from tool-level errors (MCP server responds with is_error=true).
    """


class HttpTransport:
    """Calls /v1/call_tool on a running HTTP MCP server via httpx."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = timeout_sec
        self._session_id: str = ""

    def set_session_id(self, session_id: str) -> None:
        """Inject session ID to be forwarded as X-Session-Id header on every call."""
        self._session_id = session_id

    @staticmethod
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

    _RETRYABLE_STATUS: frozenset[int] = frozenset({429, 502, 503, 504})
    _RETRY_MAX: int = 3

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
                result = self._parse_http_response(resp)
                return ToolCallResult(
                    output=result.output,
                    is_error=result.is_error,
                    request_id=result.request_id,
                    server_key=self._server_key,
                    source="mcp",
                    error_type=result.error_type,
                )
            except httpx.TimeoutException as e:
                msg = f"[TimeoutException] tool={name} url={self._base_url}: {e}"
                logger.warning(msg)
                last_exc = TransportError(msg)
                break  # timeout = non-retryable
            except httpx.HTTPStatusError as e:
                msg = (
                    f"[HTTPStatusError] tool={name} url={self._base_url}"
                    f" status={e.response.status_code}"
                    f" response={e.response.text[:300]!r}"
                    f" — check {self._base_url}/health"
                )
                logger.warning(msg)
                last_exc = TransportError(msg)
                break
            except (httpx.RequestError, ValueError) as e:
                msg = f"[{type(e).__name__}] tool={name} url={self._base_url}: {e} — check {self._base_url}/health"
                logger.warning(msg)
                last_exc = TransportError(msg)
                break
        else:
            msg = f"[Retry exhausted] tool={name} url={self._base_url} after {self._RETRY_MAX} attempts"
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")
