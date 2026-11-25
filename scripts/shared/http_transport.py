#!/usr/bin/env python3
"""scripts/shared/http_transport.py — HTTP MCP transport implementation."""

import asyncio
import dataclasses
import logging
from typing import Any, Literal
from urllib.parse import quote

import httpx

from shared.execution_mode import EXECUTION_MODES
from shared.json_utils import parse_http_json
from shared.logger import attach_redaction_filter, register_secret
from shared.mcp_config import McpServerConfig
from shared.tool_constants import ALL_SIDE_EFFECTING_TOOLS
from shared.transport_dto import ToolCallResult, ToolExecutionContext

logger = logging.getLogger(__name__)
attach_redaction_filter(logger)


# Write/state-mutating tools: reads the shared canonical set in
# shared.tool_constants (the same set dispatch.py deduplicates against and the
# tool_policy classification uses), so the fail-closed failure-classification
# gate in `call()` covers exactly the tools the dispatch layer deduplicates.
# See ADR-004 (fail-closed on writes).
_WRITE_TOOLS: frozenset[str] = ALL_SIDE_EFFECTING_TOOLS

# Pre-send httpx errors: the connection was never established, so nothing can
# have executed server-side and retry is safe for every tool, writes included.
# A tuple (not frozenset) so the gate can use isinstance() directly.
_PRESEND_SAFE_ERRORS: tuple[type[BaseException], ...] = (
    httpx.ConnectError,
    httpx.ProxyError,
)

# Retryable statuses whose server-side outcome is ambiguous for write tools
# (post-dispatch handlers emit 502/503; 504 is gateway-class). 429 precedes
# fulfillment and has no post-dispatch emitter in this repo, so it stays
# retryable for all tools.
_AMBIGUOUS_RETRY_STATUSES: frozenset[int] = frozenset({502, 503, 504})


class TransportError(Exception):
    """Raised by transport layers when a transport-level failure occurs.

    Distinguishes transport failures (network down, timeout, process crash)
    from tool-level errors (MCP server responds with is_error=true).

    `stage` records how far the failed call reached (AC-6 dispatch-stage
    signal, consumed by the invoker and the intent-state writer):
    ``""`` nothing was sent, ``"sent"`` the request left the client with no
    response, ``"response"`` an HTTP response was received.
    """

    def __init__(self, message: str, *, stage: Literal["", "sent", "response"] = ""):
        super().__init__(message)
        self.stage: Literal["", "sent", "response"] = stage


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
        """Initialize with HTTP client, server URL, key, and optional auth config.

        Args:
            http: AsyncHTTPClient instance for making requests.
            base_url: Base URL of the MCP server.
            server_key: Server key for identifying this connection.
            cfg: Optional MCP server configuration.
            timeout_sec: Timeout in seconds. If <= 0, httpx's default timeout (10s) is used.
        """
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        if cfg is None:
            raise ValueError(
                "HttpTransport requires a non-None 'cfg' argument; "
                "a transport without credentials silently disables auth"
            )
        self._auth_token: str = cfg.auth_token
        if self._auth_token:
            register_secret(self._auth_token)
        self._timeout = timeout_sec
        self._session_id: str = ""

    def set_session_id(self, session_id: str) -> None:
        """Inject session ID to be forwarded as X-Session-Id header on every call."""
        self._session_id = session_id

    @staticmethod
    def _parse_http_response(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid, including an
        execution_mode outside the closed vocabulary or a wrong metadata type.
        Absent metadata fields default to "" and False. ``dedup_state`` is
        extracted tolerantly: a missing or non-string value yields "" and
        never raises or changes error classification (mcpai007 REQ-002).
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
        execution_mode = data.get("execution_mode", "")
        if not isinstance(execution_mode, str):
            raise ValueError(
                f"MCP 'execution_mode' must be str, got {type(execution_mode).__name__}"
            )
        if execution_mode and execution_mode not in EXECUTION_MODES:
            # Protocol error: a value outside the closed vocabulary never becomes
            # metadata. The value is not echoed into the message.
            raise ValueError("MCP 'execution_mode' is outside the closed vocabulary")
        side_effect_applied = data.get("side_effect_applied", False)
        if not isinstance(side_effect_applied, bool):
            raise ValueError(
                f"MCP 'side_effect_applied' must be bool, got "
                f"{type(side_effect_applied).__name__}"
            )
        dedup_state = data.get("dedup_state", "")
        if not isinstance(dedup_state, str):
            # Tolerant extraction (mcpai007 REQ-002): a non-string value yields
            # "" and never raises or changes error classification.
            dedup_state = ""
        return ToolCallResult.from_transport(
            output=result_val,
            is_error=is_error_val,
            request_id=x_request_id,
            execution_mode=execution_mode,
            side_effect_applied=side_effect_applied,
            dedup_state=dedup_state,
        )

    _RETRYABLE_STATUS: frozenset[int] = frozenset({429, 502, 503, 504})
    _RETRY_MAX: int = 3
    _TOOL_LEVEL_STATUSES: frozenset[int] = frozenset({400, 403, 404, 409, 422})

    @staticmethod
    def _tool_error_result(resp: httpx.Response) -> ToolCallResult:
        """Build a tool-level error result from a tool-level status response body.

        Tolerant parsing: any body parse failure falls back to the first 512 chars
        of the raw text; a malformed body at a tool-level status must not re-enter
        the transport path (healthcascade001). A missing or non-string
        ``dedup_state`` yields "" (mcpai007 REQ-002).
        """
        dedup_state = ""
        try:
            data = parse_http_json(resp)
            reason = data.get("detail") or data.get("result") or ""
            if not isinstance(reason, str) or not reason:
                reason = resp.text[:512]
            raw_dedup = data.get("dedup_state", "")
            if isinstance(raw_dedup, str):
                dedup_state = raw_dedup
        except ValueError:
            reason = resp.text[:512]
        return ToolCallResult.from_transport(
            output=str(reason),
            is_error=True,
            request_id=resp.headers.get("x-request-id", ""),
            dedup_state=dedup_state,
        )

    def _transport_error(
        self,
        name: str,
        prefix: str,
        detail: str,
        *,
        break_flag: bool = False,
        health_check: bool = True,
        stage: Literal["", "sent", "response"] = "",
    ) -> TransportError:
        suffix = ""
        if health_check:
            suffix = " — check " + self._base_url + "/health"
        msg = f"{prefix} tool={name} url={self._base_url}: {detail}{suffix}"
        logger.warning(msg)
        exc = TransportError(msg, stage=stage)
        if break_flag:
            raise exc
        return exc

    def _build_exhaustion_message(
        self,
        tool_name: str,
        last_retryable_status: int | None,
        last_error: str | None = None,
    ) -> str:
        """Build a safe retry-exhaustion diagnostic without exposing raw response bodies."""
        parts = [f"[Retry exhausted] tool={tool_name}"]
        if last_retryable_status is not None:
            parts.append(f"status={last_retryable_status}")
        if last_error is not None:
            parts.append(f"last_error={last_error}")
        return " ".join(parts) + f" after {self._RETRY_MAX} attempts"

    async def call(
        self,
        name: str,
        args: dict[str, Any],
        context: ToolExecutionContext | None = None,
    ) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses). Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.

        `context` carries the logical call id sent as X-Idempotency-Key (AC-1:
        one opaque uuid7 per logical call, reused unchanged across every
        retry) and the execution mode sent as X-Execution-Mode. A call with no
        context or an empty `call_id` is refused before any HTTP send (AC-3 gate
        at the wire boundary) and returns an error result with
        `error_type="routing"` and `dispatch_stage=""` instead of raising.
        """
        if context is None or not context.call_id:
            # AC-3: sending without a logical id re-creates the identical-args
            # collision the derived key used to cause — refuse at the wire gate.
            msg = f"Refused: tool={name} has no logical call id for X-Idempotency-Key"
            logger.error(msg)
            return ToolCallResult(
                output=msg,
                is_error=True,
                request_id="",
                server_key=self._server_key,
                source="mcp",
                error_type="routing",
                context=context,
                dispatch_stage="",
            )
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id
        headers["X-Idempotency-Key"] = context.call_id
        headers["X-Execution-Mode"] = context.execution_mode

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_retryable_status: int | None = None
        last_request_error: str | None = None  # last RequestError "<class>: <message>"
        # Per-logical-call gating: this loop may issue multiple HTTP attempts
        # (retryable statuses in _RETRYABLE_STATUS, up to _RETRY_MAX=3) but each
        # attempt reuses the single context.call_id header above unchanged
        # (retry-invariance, AC-1) and does NOT re-enter
        # the pre-call gates. The health/lifecycle/semaphore gates run once per
        # logical call in ToolTransportInvoker._run_precall_gates; they are not
        # re-evaluated between these attempts.
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    if (
                        name in _WRITE_TOOLS
                        and resp.status_code in _AMBIGUOUS_RETRY_STATUSES
                    ):
                        raise TransportError(
                            f"Transport returned {resp.status_code} for write tool '{name}' "
                            f"on attempt {attempt}; dispatch may already have executed, "
                            "retry suppressed (fail-closed, ADR-004)",
                            stage="response",
                        )
                    last_retryable_status = resp.status_code
                    wait_sec = 2**attempt  # 1, 2 (increasing)
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    if attempt < self._RETRY_MAX - 1:
                        await asyncio.sleep(wait_sec)
                    continue
                if resp.status_code in self._TOOL_LEVEL_STATUSES:
                    result = self._tool_error_result(resp)
                    return dataclasses.replace(
                        result,
                        server_key=self._server_key,
                        error_type="tool",
                        context=context,
                        dispatch_stage="response",
                    )
                resp.raise_for_status()
                parsed = self._parse_http_response(resp)
                return dataclasses.replace(
                    parsed,
                    server_key=self._server_key,
                    context=context,
                    dispatch_stage="response",
                )
            except httpx.TimeoutException as e:
                raise self._transport_error(
                    name, "[TimeoutException]", str(e), break_flag=True, stage="sent"
                )
            except httpx.HTTPStatusError as e:
                req_id = e.response.headers.get("x-request-id", "")
                detail = f"status={e.response.status_code} request_id={req_id!r}"
                raise self._transport_error(
                    name,
                    "[HTTPStatusError]",
                    detail,
                    break_flag=True,
                    health_check=False,
                    stage="response",
                )
            except ValueError as e:
                raise self._transport_error(
                    name,
                    f"[{type(e).__name__}]",
                    str(e),
                    break_flag=True,
                    stage="response",
                )
            except httpx.RequestError as e:
                # classification gate (ADR-004): for write tools, only
                # pre-send errors (_PRESEND_SAFE_ERRORS) keep the retry path —
                # the connection was never established, so nothing executed
                # server-side. Any other RequestError is post-send ambiguous
                # and raises immediately; the server-side _duplicate_cache
                # (dispatch.py) cannot cover that window because dispatch never
                # caches errors. Reads keep the current retry path unchanged.
                # Retried errors record their cause in last_request_error,
                # surfaced in the exhaustion message as last_error=<class>:
                # <message>.
                if name in _WRITE_TOOLS and not isinstance(e, _PRESEND_SAFE_ERRORS):
                    raise TransportError(
                        f"Transport failed for write tool '{name}' after attempt {attempt} "
                        f"({type(e).__name__}: {e}); server-side execution outcome is ambiguous "
                        "and client-side retry is suppressed (fail-closed, ADR-004)",
                        stage="sent",
                    ) from e
                self._transport_error(name, f"[{type(e).__name__}]", str(e))
                last_request_error = f"{type(e).__name__}: {e}"
                continue
        msg = self._build_exhaustion_message(
            name, last_retryable_status, last_request_error
        )
        logger.error(msg)
        raise TransportError(msg)


# Success label for the control client; it is the "none" member of the shared
# control error vocabulary. The other labels are fixed strings, so a caller can
# branch on them without ever seeing a response body or exception text.
CONTROL_SUCCESS_LABEL = "none"


@dataclasses.dataclass(frozen=True)
class ControlCallResult:
    """Typed outcome of one control-plane request (mcpdl004 REQ-001).

    `error` is a fixed label: `none`, `control_unconfigured`, `timeout`,
    `transport_error`, `bad_response`, or `http_<status>`. `payload` is the parsed
    JSON object on success only; no failed-response body is carried, and no raw
    exception text is stored.
    """

    ok: bool
    status_code: int
    payload: dict[str, Any] | None
    error: str


class ControlClient:
    """Single-attempt client for GET /v1/call_state/{key} and its reconcile POST.

    Synchronous by design: the stale-call classification path that uses it runs
    inside a running event loop and cannot await an async transport. Control reads
    are never retried here; the caller decides. The tool Bearer token is never sent
    on a control path (mcpdl004 REQ-002).
    """

    def __init__(
        self, base_url: str, control_token: str, timeout_sec: float = 3.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._control_token = control_token
        self._timeout = timeout_sec
        if control_token:
            register_secret(control_token)

    def get_call_state(self, key: str) -> ControlCallResult:
        """Read the call state for one logical call id."""
        return self._request("GET", f"/v1/call_state/{quote(key, safe='')}")

    def request_reconcile(self, key: str) -> ControlCallResult:
        """Ask the owning server to reconcile one call; the request has no payload."""
        return self._request("POST", f"/v1/call_state/{quote(key, safe='')}/reconcile")

    def _request(self, method: str, path: str) -> ControlCallResult:
        """One request, typed result, no raise. Logs the path and a fixed label only."""
        if not self._control_token:
            return self._refuse(method, path, 0, "control_unconfigured")
        try:
            # Context manager per call: no connection outlives the request.
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.request(
                    method,
                    f"{self._base_url}{path}",
                    headers={"Authorization": f"Bearer {self._control_token}"},
                )
        except httpx.TimeoutException:
            return self._refuse(method, path, 0, "timeout")
        except httpx.RequestError:
            return self._refuse(method, path, 0, "transport_error")
        if not resp.is_success:
            return self._refuse(
                method, path, resp.status_code, f"http_{resp.status_code}"
            )
        try:
            data = parse_http_json(resp)
        except ValueError:
            return self._refuse(method, path, resp.status_code, "bad_response")
        if not isinstance(data, dict):
            return self._refuse(method, path, resp.status_code, "bad_response")
        return ControlCallResult(True, resp.status_code, data, CONTROL_SUCCESS_LABEL)

    @staticmethod
    def _refuse(
        method: str, path: str, status_code: int, label: str
    ) -> ControlCallResult:
        """Log the fixed label and the request path only: no body, no exception text."""
        suffix = f" status={status_code}" if status_code else ""
        logger.warning(f"Control request {label}: {method} {path}{suffix}")
        return ControlCallResult(False, status_code, None, label)
