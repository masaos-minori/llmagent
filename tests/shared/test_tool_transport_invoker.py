"""tests/shared/test_tool_transport_invoker.py
Tests for ToolTransportInvoker.invoke(): health, lifecycle, semaphore, recording.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from shared.http_transport import HttpTransport, TransportError
from shared.mcp_config import (
    McpServerConfig,
    McpServerHealthRegistry,
    StartupMode,
    TransportType,
)
from shared.mcp_health import McpServerHealthState
from shared.tool_transport_invoker import ToolTransportInvoker
from shared.transport_dto import ToolCallResult


def _http_cfg(
    url: str = "http://127.0.0.1:8000", call_timeout_sec: float = 60.0
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        call_timeout_sec=call_timeout_sec,
        auth_token="test-token",
        startup_mode=StartupMode.PERSISTENT,
    )


def _make_invoker(
    configs: dict[str, McpServerConfig] | None = None,
    concurrency_limits: dict[str, int] | None = None,
) -> ToolTransportInvoker:
    http = MagicMock(spec=httpx.AsyncClient)
    return ToolTransportInvoker(
        http=http,
        server_configs=configs or {"srv": _http_cfg()},
        concurrency_limits=concurrency_limits,
    )


class TestToolTransportInvoker:
    @pytest.mark.asyncio
    async def test_health_unavailable_returns_error_result(self) -> None:
        invoker = _make_invoker()
        registry = McpServerHealthRegistry(failure_threshold=1)
        registry.record_failure(
            "srv"
        )  # state -> UNAVAILABLE immediately at threshold=1
        invoker.set_health_registry(registry)

        result = await invoker.invoke("srv", "some_tool", {})

        assert result.is_error is True
        assert result.error_type == "tool"
        assert "unavailable" in result.output.lower()

    @pytest.mark.asyncio
    async def test_lifecycle_ensure_ready_called(self) -> None:
        invoker = _make_invoker()
        lifecycle = AsyncMock()
        invoker.set_lifecycle(lifecycle)

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="srv"
            )
        )
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        await invoker.invoke("srv", "some_tool", {})

        lifecycle.ensure_ready.assert_awaited_once_with("srv")

    @pytest.mark.asyncio
    async def test_success_records_health_success(self) -> None:
        invoker = _make_invoker()
        registry = McpServerHealthRegistry()
        registry.record_success = MagicMock(wraps=registry.record_success)  # type: ignore[method-assign]
        invoker.set_health_registry(registry)

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="srv"
            )
        )
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        await invoker.invoke("srv", "some_tool", {})

        assert registry.record_success.call_count == 1

    @pytest.mark.asyncio
    async def test_tool_error_increments_stat_tool_errors(self) -> None:
        invoker = _make_invoker()

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="tool err",
                is_error=True,
                request_id="",
                server_key="srv",
                error_type="tool",
            )
        )
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        await invoker.invoke("srv", "some_tool", {})

        assert invoker.stat_tool_errors.get("srv", 0) == 1

    @pytest.mark.asyncio
    async def test_transport_error_increments_stat_transport_errors(self) -> None:
        invoker = _make_invoker()

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=TransportError("failed"))
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        await invoker.invoke("srv", "some_tool", {})

        assert invoker.stat_transport_errors.get("srv", 0) == 1

    @pytest.mark.asyncio
    async def test_transport_error_records_health_failure(self) -> None:
        invoker = _make_invoker()
        registry = McpServerHealthRegistry()
        registry.record_failure = MagicMock(wraps=registry.record_failure)  # type: ignore[method-assign]
        invoker.set_health_registry(registry)

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=TransportError("failed"))
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        await invoker.invoke("srv", "some_tool", {})

        assert registry.record_failure.call_count == 1

    @pytest.mark.asyncio
    async def test_transport_error_returns_error_type_transport(self) -> None:
        invoker = _make_invoker()

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=TransportError("network down"))
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        result = await invoker.invoke("srv", "some_tool", {})

        assert result.is_error is True
        assert result.error_type == "transport"

    @pytest.mark.asyncio
    async def test_semaphore_applied_with_concurrency_limit(self) -> None:
        invoker = _make_invoker(concurrency_limits={"srv": 1})

        call_count = 0

        async def _slow_call(name: str, args: dict[str, Any]) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            return ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="srv"
            )

        mock_transport = MagicMock(spec=HttpTransport)
        mock_transport.call = _slow_call
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        result = await invoker.invoke("srv", "some_tool", {})

        assert result.output == "ok"
        assert call_count == 1

    def test_call_timeout_sec_zero_means_no_timeout(self) -> None:
        invoker = _make_invoker(configs={"srv": _http_cfg(call_timeout_sec=0)})
        assert invoker._transports["srv"]._timeout == 0

    def test_call_timeout_sec_positive_value_passed_through(self) -> None:
        invoker = _make_invoker(configs={"srv": _http_cfg(call_timeout_sec=30.0)})
        assert invoker._transports["srv"]._timeout == 30.0

    def test_call_timeout_sec_default_unset_falls_back_to_60(self) -> None:
        invoker = _make_invoker(configs={"srv": _http_cfg()})
        assert invoker._transports["srv"]._timeout == 60.0


class TestDisabledServerExclusion:
    @pytest.mark.asyncio
    async def test_disabled_server_transport_not_constructed(self) -> None:
        """Disabled server should not get an HttpTransport entry."""
        from shared.mcp_config import StartupMode

        disabled_cfg = _http_cfg()
        disabled_cfg.startup_mode = StartupMode.NONE
        invoker = _make_invoker(configs={"disabled_srv": disabled_cfg})

        assert "disabled_srv" not in invoker._transports

    @pytest.mark.asyncio
    async def test_invoke_rejects_disabled_server(self) -> None:
        """invoke() should reject disabled servers with an error result."""
        from shared.mcp_config import StartupMode

        disabled_cfg = _http_cfg()
        disabled_cfg.startup_mode = StartupMode.NONE
        invoker = _make_invoker(configs={"disabled_srv": disabled_cfg})

        result = await invoker.invoke("disabled_srv", "some_tool", {})

        assert result.is_error is True
        assert result.error_type == "tool"
        assert "disabled" in result.output.lower()
        assert "cannot be used" in result.output.lower()


class TestInvokeCharacterizationPin:
    """Characterization pins locking invoke()'s observable output after gate-chain unification."""

    @pytest.mark.asyncio
    async def test_invoke_healthy_returns_expected_result(self) -> None:
        """A healthy call through the real gate chain returns the expected ToolCallResult."""
        invoker = _make_invoker()
        invoker.set_health_registry(McpServerHealthRegistry())
        lifecycle = AsyncMock()
        invoker.set_lifecycle(lifecycle)
        mock_transport = AsyncMock()
        expected = ToolCallResult(
            output="ok",
            is_error=False,
            request_id="r1",
            server_key="srv",
            source="mcp",
        )
        mock_transport.call = AsyncMock(return_value=expected)
        invoker._transports["srv"] = mock_transport

        result = await invoker.invoke("srv", "some_tool", {})

        assert result.output == "ok"
        assert result.is_error is False
        assert result.server_key == "srv"
        assert lifecycle.ensure_ready.await_count == 1
        assert lifecycle.ensure_ready.await_args_list[-1].args == ("srv",)

    @pytest.mark.asyncio
    async def test_invoke_transport_error_returns_error_result(self) -> None:
        """A transport error through the real gate chain returns an error ToolCallResult."""
        invoker = _make_invoker()
        invoker.set_health_registry(McpServerHealthRegistry())
        lifecycle = AsyncMock()
        invoker.set_lifecycle(lifecycle)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=TransportError("network down"))
        invoker._transports["srv"] = mock_transport

        result = await invoker.invoke("srv", "some_tool", {})

        assert result.is_error is True
        assert result.error_type == "transport"
        assert result.server_key == "srv"
        assert invoker.stat_transport_errors.get("srv", 0) == 1


class TestHalfOpenSingleTrialGate:
    """ACC-002/003: exactly one HALF_OPEN trial dispatches; flag released on all paths."""

    def _unavailable_registry(self) -> McpServerHealthRegistry:
        # threshold=1 + cooldown=0 lets a single record_failure() reach
        # UNAVAILABLE; the first invoke() then triggers the HALF_OPEN transition.
        return McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=0.0)

    @pytest.mark.asyncio
    async def test_first_call_after_cooldown_dispatches_as_trial(self) -> None:
        """ACC-002: the call that triggers the UNAVAILABLE->HALF_OPEN transition is the trial; it dispatches and succeeds."""
        invoker = _make_invoker()
        registry = self._unavailable_registry()
        invoker.set_health_registry(registry)

        mock_transport = AsyncMock()
        call_log: list[int] = []

        async def _rec_call(name: str, args: dict[str, Any]) -> ToolCallResult:
            call_log.append(1)
            return ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="srv"
            )

        mock_transport.call = _rec_call
        invoker._transports["srv"] = mock_transport

        result = await invoker.invoke("srv", "tool", {})

        assert result.is_error is False
        assert len(call_log) == 1  # exactly one dispatch
        assert registry.get_state("srv") == McpServerHealthState.HEALTHY
        assert registry.trial_in_flight("srv") is False

    @pytest.mark.asyncio
    async def test_half_open_in_flight_trial_rejects_dispatch(self) -> None:
        """ACC-002: once a trial is in flight (HALF_OPEN + flag set), dispatch is rejected."""
        invoker = _make_invoker()
        registry = self._unavailable_registry()
        # Simulate an in-flight trial: transition to HALF_OPEN and acquire the slot.
        registry.record_failure("srv")
        registry.is_unavailable("srv")
        assert registry.get_state("srv") == McpServerHealthState.HALF_OPEN
        assert registry.trial_in_flight("srv") is True
        invoker.set_health_registry(registry)

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="srv"
            )
        )
        invoker._transports["srv"] = mock_transport

        result = await invoker.invoke("srv", "tool", {})

        assert result.is_error is True
        assert result.error_type == "tool"
        assert "trial" in result.output.lower()
        mock_transport.call.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_trial_releases_flag(self) -> None:
        invoker = _make_invoker()
        registry = self._unavailable_registry()
        invoker.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="srv"
            )
        )
        invoker._transports["srv"] = mock_transport

        result = await invoker.invoke("srv", "tool", {})

        assert result.is_error is False
        assert registry.get_state("srv") == McpServerHealthState.HEALTHY
        assert registry.trial_in_flight("srv") is False

    @pytest.mark.asyncio
    async def test_failed_trial_releases_flag(self) -> None:
        invoker = _make_invoker()
        registry = self._unavailable_registry()
        invoker.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=TransportError("down"))
        invoker._transports["srv"] = mock_transport

        result = await invoker.invoke("srv", "tool", {})

        assert result.is_error is True
        assert registry.get_state("srv") == McpServerHealthState.UNAVAILABLE
        assert registry.trial_in_flight("srv") is False

    @pytest.mark.asyncio
    async def test_exceptioned_trial_releases_flag(self) -> None:
        invoker = _make_invoker()
        registry = self._unavailable_registry()
        invoker.set_health_registry(registry)

        async def _raising(name: str, args: dict[str, Any]) -> ToolCallResult:
            raise RuntimeError("boom")

        mock_transport = MagicMock(spec=HttpTransport)
        mock_transport.call = _raising
        invoker._transports["srv"] = mock_transport

        with pytest.raises(RuntimeError):
            await invoker.invoke("srv", "tool", {})

        # No leak: the single-trial slot is freed even though the trial raised.
        assert registry.trial_in_flight("srv") is False


class TestRetryGatesRunOnce:
    @pytest.mark.asyncio
    async def test_gates_run_once_across_retries(self, monkeypatch) -> None:
        """A logical call that retries 3 HTTP attempts runs each pre-call gate once."""
        invoker = _make_invoker(concurrency_limits={"srv": 10})
        lifecycle = AsyncMock()
        invoker.set_lifecycle(lifecycle)

        http = MagicMock(spec=httpx.AsyncClient)
        transport = HttpTransport(
            http=http,
            base_url="http://127.0.0.1:8000",
            server_key="srv",
            cfg=_http_cfg(),
        )
        resp = MagicMock()
        resp.status_code = 503  # in _RETRYABLE_STATUS -> retryable on every attempt
        http.post = AsyncMock(return_value=resp)
        invoker._transports["srv"] = transport  # type: ignore[assignment]

        invoker._check_health = MagicMock(wraps=invoker._check_health)  # type: ignore[method-assign]
        invoker._maybe_semaphore = MagicMock(wraps=invoker._maybe_semaphore)  # type: ignore[method-assign]
        monkeypatch.setattr("shared.http_transport.asyncio.sleep", AsyncMock())

        result = await invoker.invoke("srv", "some_tool", {})

        assert http.post.call_count == 3  # retries exhausted on persistent 503
        assert invoker._check_health.call_count == 1  # health gate runs once
        assert lifecycle.ensure_ready.call_count == 1  # lifecycle gate runs once
        assert invoker._maybe_semaphore.call_count == 1  # semaphore gate runs once
        assert result.is_error is True  # exhaustion -> transport error result
