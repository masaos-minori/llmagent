import pytest
from agent.http_lifecycle_errors import HttpStartupError, StartupFailure
from agent.shared.retry_helper import retry_once_with_delay


class TestRetryHelperExceptionPreservation:
    """Tests for REQ-002, REQ-003: Verify exception type preservation through retry."""

    @pytest.mark.asyncio
    async def test_timeout_error_preserved(self):
        """REQ-002: TimeoutError raised on second attempt propagates as TimeoutError."""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("First attempt timeout")
            else:
                raise TimeoutError("Second attempt timeout")

        with pytest.raises(TimeoutError, match="Second attempt timeout"):
            await retry_once_with_delay(
                failing_func,
                delay=0.01,
                shutdown_event=None,
                interrupt_msg="interrupted",
                fatal_prefix="FATAL",
            )

    @pytest.mark.asyncio
    async def test_connection_refused_error_preserved(self):
        """REQ-003: ConnectionRefusedError raised on second attempt propagates as ConnectionRefusedError."""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionRefusedError("First attempt refused")
            else:
                raise ConnectionRefusedError("Second attempt refused")

        with pytest.raises(ConnectionRefusedError, match="Second attempt refused"):
            await retry_once_with_delay(
                failing_func,
                delay=0.01,
                shutdown_event=None,
                interrupt_msg="interrupted",
                fatal_prefix="FATAL",
            )

    @pytest.mark.asyncio
    async def test_runtime_error_preserved(self):
        """Ensure RuntimeError is also preserved (not just wrapped)."""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("First attempt runtime error")
            else:
                raise RuntimeError("Second attempt runtime error")

        with pytest.raises(RuntimeError, match="Second attempt runtime error"):
            await retry_once_with_delay(
                failing_func,
                delay=0.01,
                shutdown_event=None,
                interrupt_msg="interrupted",
                fatal_prefix="FATAL",
            )

    @pytest.mark.asyncio
    async def test_custom_runtime_error_non_string_constructor_preserved(self):
        """REQ-006: A RuntimeError subclass whose __init__ rejects a plain message
        propagates as its own type (chaining the original) instead of raising
        AttributeError after a second failed attempt."""

        class _CustomRuntimeError(RuntimeError):
            def __init__(self, code: int) -> None:
                if not isinstance(code, int):
                    raise TypeError("code must be an int, not a str")
                self.code = code

        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise _CustomRuntimeError(1)
            raise _CustomRuntimeError(2)

        with pytest.raises(_CustomRuntimeError) as exc_info:
            await retry_once_with_delay(
                failing_func,
                delay=0.01,
                shutdown_event=None,
                interrupt_msg="interrupted",
                fatal_prefix="FATAL",
            )

        assert isinstance(exc_info.value, _CustomRuntimeError)
        assert isinstance(exc_info.value.__cause__, _CustomRuntimeError)

    @pytest.mark.asyncio
    async def test_http_startup_error_reraised_without_attribute_error(self):
        """HttpStartupError needs a StartupFailure; a message must not be passed."""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise HttpStartupError(
                StartupFailure(
                    server_key="srv", reason=f"attempt {call_count}", stderr_full=""
                )
            )

        with pytest.raises(HttpStartupError) as exc_info:
            await retry_once_with_delay(
                failing_func,
                delay=0.01,
                shutdown_event=None,
                interrupt_msg="interrupted",
                fatal_prefix="FATAL",
            )

        assert exc_info.value.failure.server_key == "srv"
        assert exc_info.value.failure.reason == "attempt 2"
        assert isinstance(exc_info.value.__cause__, HttpStartupError)
