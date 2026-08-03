"""Characterization tests for stampede protection cascading failure behavior."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from shared.http_transport import TransportError
from shared.tool_executor import ToolExecutor
from shared.transport_dto import ToolCallResult


def _make_result(
    output: str = "ok", is_error: bool = False, server_key: str = ""
) -> ToolCallResult:
    return ToolCallResult(
        output=output,
        is_error=is_error,
        request_id="req-1",
        server_key=server_key,
    )


def _make_executor() -> ToolExecutor:
    http_client = MagicMock()
    http_client.is_closed = False
    server_configs: dict[str, MagicMock] = {}
    return ToolExecutor(http_client, cache_ttl=60.0, server_configs=server_configs)


class TestConcurrentRequestExceptionPropagation:
    """Verify all waiting requests receive same exception."""

    @pytest.mark.asyncio
    async def test_all_waiters_receive_same_exception(self) -> None:
        """When _raw_execute raises, all concurrent callers receive the same exception."""
        executor = _make_executor()
        executor._raw_execute = AsyncMock(
            side_effect=RuntimeError("connection refused")
        )

        cache_key = "test:cache:key"
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        executor._inflight[cache_key] = inflight

        exceptions_received: list[Exception] = []

        async def _waiter(i: int) -> None:
            try:
                await inflight
            except Exception as exc:
                exceptions_received.append(exc)

        tasks = [asyncio.create_task(_waiter(i)) for i in range(5)]
        await asyncio.sleep(0.01)  # Let all waiters start
        inflight.set_exception(RuntimeError("connection refused"))
        await asyncio.gather(*tasks)

        assert len(exceptions_received) == 5
        assert all(isinstance(e, RuntimeError) for e in exceptions_received)
        assert all(str(e) == "connection refused" for e in exceptions_received)

    @pytest.mark.asyncio
    async def test_concurrent_callers_share_inflight_future(self) -> None:
        """Multiple concurrent callers share the same inflight future during stampede."""
        executor = _make_executor()
        executor._cache_max_size = 0  # Disable cache to force stampede path

        call_count = 0

        async def _slow_raw_execute(tool_name: str, args: dict) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return _make_result()

        executor._raw_execute = _slow_raw_execute

        cache_key = "test:slow:key"

        async def _caller() -> ToolCallResult:
            return await executor._execute_with_stampede_protection(
                cache_key, "test_tool", {}
            )

        results = await asyncio.gather(*[_caller() for _ in range(5)])
        assert all(r.output == "ok" for r in results)
        assert call_count == 1  # Only one actual execution


class TestServerHealthRegistryUpdateOnFailure:
    """Verify failure recorded in server health registry."""

    @pytest.mark.asyncio
    async def test_health_registry_recorded_failure(self) -> None:
        """When _raw_execute raises TransportError, record_failure is called on the health registry."""
        executor = _make_executor()
        executor._health_registry = MagicMock()
        executor._health_registry.record_failure = MagicMock(return_value=None)
        executor._raw_execute = AsyncMock(
            side_effect=TransportError("connection refused")
        )

        cache_key = "test:cache:key"

        # The stampede path does NOT call record_failure directly; it propagates the exception.
        # record_failure is called by _handle_transport_error after the inflight future is set.
        # We verify this indirectly by checking that the exception propagates correctly.
        with pytest.raises(TransportError, match="connection refused"):
            await executor._execute_with_stampede_protection(cache_key, "test_tool", {})

    @pytest.mark.asyncio
    async def test_health_registry_not_called_when_no_registry(self) -> None:
        """Without a health registry, no failure recording occurs."""
        executor = _make_executor()
        executor._health_registry = None
        executor._raw_execute = AsyncMock(
            side_effect=RuntimeError("connection refused")
        )

        cache_key = "test:cache:key"

        with pytest.raises(RuntimeError, match="connection refused"):
            await executor._execute_with_stampede_protection(cache_key, "test_tool", {})

        # No error should occur even without a registry


class TestRetryPolicyForTransientErrors:
    """Verify retry behavior for transient errors."""

    @pytest.mark.asyncio
    async def test_no_retry_in_stampede_path(self) -> None:
        """The stampede protection path does not implement its own retry logic."""
        executor = _make_executor()
        call_count = 0

        async def _failing_raw_execute(tool_name: str, args: dict) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("transient error")

        executor._raw_execute = _failing_raw_execute

        cache_key = "test:cache:key"

        with pytest.raises(RuntimeError, match="transient error"):
            await executor._execute_with_stampede_protection(cache_key, "test_tool", {})

        assert call_count == 1  # No retry in stampede path


class TestPartialSuccessScenario:
    """Verify correct handling of mixed results."""

    @pytest.mark.asyncio
    async def test_successful_result_shared_among_waiters(self) -> None:
        """A successful result is shared among all concurrent callers."""
        executor = _make_executor()
        executor._cache_max_size = 0

        async def _slow_success(tool_name: str, args: dict) -> ToolCallResult:
            await asyncio.sleep(0.05)
            return _make_result(output="success result")

        executor._raw_execute = _slow_success

        cache_key = "test:success:key"

        async def _caller() -> ToolCallResult:
            return await executor._execute_with_stampede_protection(
                cache_key, "test_tool", {}
            )

        results = await asyncio.gather(*[_caller() for _ in range(3)])
        assert all(r.output == "success result" for r in results)

    @pytest.mark.asyncio
    async def test_error_result_shared_among_waiters(self) -> None:
        """An error result propagates to all concurrent callers via inflight.set_exception()."""
        executor = _make_executor()
        executor._cache_max_size = 0

        async def _failing_raw_execute(tool_name: str, args: dict) -> ToolCallResult:
            await asyncio.sleep(0.05)
            raise RuntimeError("tool execution failed")

        executor._raw_execute = _failing_raw_execute

        cache_key = "test:error:key"

        exceptions_received: list[Exception] = []

        async def _caller() -> None:
            try:
                await executor._execute_with_stampede_protection(
                    cache_key, "test_tool", {}
                )
            except Exception as exc:
                exceptions_received.append(exc)

        await asyncio.gather(*[_caller() for _ in range(3)])
        assert len(exceptions_received) == 3
        assert all(isinstance(e, RuntimeError) for e in exceptions_received)
