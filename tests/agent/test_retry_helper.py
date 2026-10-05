import pytest

from scripts.agent.shared.retry_helper import retry_once_with_delay


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
