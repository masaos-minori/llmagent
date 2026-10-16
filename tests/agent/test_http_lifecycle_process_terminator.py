import signal
from unittest.mock import MagicMock, patch

import pytest
from agent.http_lifecycle_process_terminator import ProcessTerminator


class TestProcessTerminatorSigKillFailureScenarios:
    """Tests for REQ-002, REQ-003, REQ-004: Verify SIGKILL failure handling."""

    @pytest.mark.asyncio
    async def test_sigkill_failure_logs_error_and_returns_false(self):
        """REQ-002: SIGKILL failure is handled gracefully — error logged, False returned."""
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        proc.poll.return_value = None  # Process still running

        with patch("agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.return_value = 12345
            # SIGTERM succeeds; SIGKILL also succeeds (no exception)
            mock_os.killpg.side_effect = [None, None]
            # Wait loop: first monotonic() sets deadline, second exceeds it
            with patch("agent.http_lifecycle_process_terminator.time") as mock_time:
                # deadline = 0 + 5 = 5; second call returns 10 > 5, so loop exits immediately
                mock_time.monotonic.side_effect = [0.0, 10.0]

                await terminator.terminate_with_timeout(
                    proc, "test-server", timeout=5.0
                )

                # SIGKILL should be attempted next
                assert mock_os.killpg.call_count == 2  # SIGTERM + SIGKILL
                sigkill_call = mock_os.killpg.call_args_list[1]
                assert sigkill_call[0][1] == 9  # signal.SIGKILL = 9

    @pytest.mark.asyncio
    async def test_normal_sigkill_path_no_regression(self):
        """REQ-004: Normal SIGKILL path works correctly — no regression."""
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        proc.poll.return_value = None  # Process still running

        with patch("agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.return_value = 12345
            # SIGTERM succeeds; SIGKILL also succeeds (no exception)
            mock_os.killpg.side_effect = [None, None]
            # Wait loop: first monotonic() sets deadline, second exceeds it
            with patch("agent.http_lifecycle_process_terminator.time") as mock_time:
                # deadline = 0 + 5 = 5; second call returns 10 > 5, so loop exits immediately
                mock_time.monotonic.side_effect = [0.0, 10.0]

                await terminator.terminate_with_timeout(
                    proc, "test-server", timeout=5.0
                )

                # SIGKILL should be attempted
                assert mock_os.killpg.call_count == 2  # SIGTERM + SIGKILL
                sigkill_call = mock_os.killpg.call_args_list[1]
                assert sigkill_call[0][1] == 9  # signal.SIGKILL = 9


class TestProcessTerminatorPgidResolution:
    """REQ-001/002/003/008: signal the real group resolved via os.getpgid."""

    @pytest.mark.asyncio
    async def test_killpg_targets_resolved_group_when_pid_differs(self):
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        proc.poll.return_value = None

        with patch("agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.return_value = 777
            mock_os.killpg.side_effect = [None, None]
            with patch("agent.http_lifecycle_process_terminator.time") as mock_time:
                mock_time.monotonic.side_effect = [0.0, 10.0]
                await terminator.terminate_with_timeout(
                    proc, "test-server", timeout=5.0
                )

            mock_os.getpgid.assert_called_once_with(12345)
            calls = mock_os.killpg.call_args_list
            assert [c[0][0] for c in calls] == [777, 777]
            assert [c[0][1] for c in calls] == [signal.SIGTERM, signal.SIGKILL]

    @pytest.mark.asyncio
    async def test_wait_exited_uses_resolved_group(self):
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345

        with patch("agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.return_value = 777
            mock_os.killpg.side_effect = ProcessLookupError

            exited = await terminator.wait_exited(proc, "test-server", timeout=1.0)

            assert exited is True
            mock_os.killpg.assert_called_with(777, 0)

    @pytest.mark.asyncio
    async def test_unresolvable_pgid_falls_back_to_proc_terminate(self):
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        proc.poll.return_value = None

        with patch("agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.side_effect = OSError("no such process")

            result = await terminator.terminate_with_timeout(proc, "test-server")

            assert result is True
            proc.terminate.assert_called_once()
            mock_os.killpg.assert_not_called()

    @pytest.mark.asyncio
    async def test_already_exited_process_returns_true_without_terminate(self):
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        proc.poll.return_value = 0  # exited and reaped

        with patch("agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.side_effect = ProcessLookupError

            result = await terminator.terminate_with_timeout(proc, "test-server")

            assert result is True
            proc.terminate.assert_not_called()
            mock_os.killpg.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_integer_pid_takes_fallback_without_raising(self):
        terminator = ProcessTerminator()
        proc = MagicMock()  # pid is a MagicMock, not an int
        proc.poll.return_value = None

        with patch("agent.http_lifecycle_process_terminator.os") as mock_os:
            result = await terminator.terminate_with_timeout(proc, "test-server")

            assert result is True
            proc.terminate.assert_called_once()
            mock_os.getpgid.assert_not_called()

    @pytest.mark.asyncio
    async def test_resolved_group_with_exited_process_returns_true(self):
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        proc.poll.return_value = 0

        with patch("agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.return_value = 777

            result = await terminator.terminate_with_timeout(proc, "test-server")

            assert result is True
            mock_os.killpg.assert_not_called()
            proc.terminate.assert_not_called()

    @pytest.mark.asyncio
    async def test_poll_error_is_treated_as_still_running(self):
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        proc.poll.side_effect = OSError("poll failed")

        with patch("agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.return_value = 777
            mock_os.killpg.side_effect = [None, None]
            with patch("agent.http_lifecycle_process_terminator.time") as mock_time:
                mock_time.monotonic.side_effect = [0.0, 10.0]
                await terminator.terminate_with_timeout(
                    proc, "test-server", timeout=5.0
                )

            assert mock_os.killpg.call_args_list[0][0] == (777, signal.SIGTERM)

    @pytest.mark.asyncio
    async def test_proc_without_poll_is_treated_as_still_running(self):
        terminator = ProcessTerminator()
        proc = MagicMock(spec=["pid", "terminate"])
        proc.pid = 12345

        with patch("agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.return_value = 777
            mock_os.killpg.side_effect = [None, None]
            with patch("agent.http_lifecycle_process_terminator.time") as mock_time:
                mock_time.monotonic.side_effect = [0.0, 10.0]
                await terminator.terminate_with_timeout(
                    proc, "test-server", timeout=5.0
                )

            assert mock_os.killpg.call_args_list[0][0] == (777, signal.SIGTERM)
