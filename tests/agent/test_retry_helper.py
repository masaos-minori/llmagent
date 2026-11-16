import asyncio
import time

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


class TestRetryHelperSkipFirstAttempt:
    """Tests for REQ-003, REQ-004: the skip_first_attempt option."""

    @pytest.mark.asyncio
    async def test_skip_first_attempt_calls_fn_once_after_delay(self):
        """REQ-003: with skip_first_attempt=True, fn runs exactly once, after the delay."""
        call_count = 0
        fn_start = 0.0

        async def failing_func():
            nonlocal call_count, fn_start
            call_count += 1
            fn_start = time.monotonic()
            raise RuntimeError("first attempt lost")

        begin = time.monotonic()
        with pytest.raises(RuntimeError):
            await retry_once_with_delay(
                failing_func,
                delay=0.01,
                shutdown_event=None,
                interrupt_msg="interrupted",
                skip_first_attempt=True,
                fatal_prefix="FATAL",
            )

        assert call_count == 1
        assert fn_start - begin >= 0.01

    @pytest.mark.asyncio
    async def test_skip_first_attempt_failure_preserves_type_and_masks(self):
        """REQ-003: the single failure raises the original type, fatal-prefixed and masked, chained."""

        async def failing_func():
            raise RuntimeError("token=ABCDEF")

        with pytest.raises(RuntimeError) as exc_info:
            await retry_once_with_delay(
                failing_func,
                delay=0.01,
                shutdown_event=None,
                interrupt_msg="interrupted",
                skip_first_attempt=True,
                fatal_prefix="FATAL",
            )

        assert isinstance(exc_info.value.__cause__, RuntimeError)
        assert "FATAL" in str(exc_info.value)
        assert "***MASKED***" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_skip_first_attempt_shutdown_before_delay_raises(self):
        """REQ-003: a shutdown event already set raises StartupInterrupted without calling fn."""
        import agent.startup

        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1

        event = asyncio.Event()
        event.set()

        with pytest.raises(agent.startup.StartupInterrupted):
            await retry_once_with_delay(
                failing_func,
                delay=0.01,
                shutdown_event=event,
                interrupt_msg="interrupted",
                skip_first_attempt=True,
                fatal_prefix="FATAL",
            )

        assert call_count == 0

    @pytest.mark.asyncio
    async def test_skip_first_attempt_shutdown_during_delay_raises(self):
        """REQ-003: a shutdown event set during the delay raises StartupInterrupted without calling fn."""
        import agent.startup

        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1

        async def set_later():
            await asyncio.sleep(0.02)
            event.set()

        event = asyncio.Event()
        asyncio.ensure_future(set_later())

        with pytest.raises(agent.startup.StartupInterrupted):
            await retry_once_with_delay(
                failing_func,
                delay=0.1,
                shutdown_event=event,
                interrupt_msg="interrupted",
                skip_first_attempt=True,
                fatal_prefix="FATAL",
            )

        assert call_count == 0

    @pytest.mark.asyncio
    async def test_default_mode_still_calls_fn_first(self):
        """REQ-003: default mode calls fn first (count 2 on persistent failure, 1 on first success)."""
        persistent_count = 0

        async def persistent_func():
            nonlocal persistent_count
            persistent_count += 1
            raise RuntimeError("always fails")

        with pytest.raises(RuntimeError):
            await retry_once_with_delay(
                persistent_func,
                delay=0.01,
                shutdown_event=None,
                interrupt_msg="interrupted",
                fatal_prefix="FATAL",
            )
        assert persistent_count == 2

        success_count = 0

        async def success_func():
            nonlocal success_count
            success_count += 1
            return "ok"

        result = await retry_once_with_delay(
            success_func,
            delay=0.01,
            shutdown_event=None,
            interrupt_msg="interrupted",
            fatal_prefix="FATAL",
        )
        assert result == "ok"
        assert success_count == 1
