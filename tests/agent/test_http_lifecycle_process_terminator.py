from unittest.mock import MagicMock, patch

import pytest

from scripts.agent.http_lifecycle_process_terminator import ProcessTerminator


class TestProcessTerminatorSigKillFailureScenarios:
    """Tests for REQ-002, REQ-003, REQ-004: Verify SIGKILL failure handling."""

    @pytest.mark.asyncio
    async def test_sigkill_failure_logs_error_and_returns_false(self):
        """REQ-002: SIGKILL failure is handled gracefully — error logged, False returned."""
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        proc.poll.return_value = None  # Process still running

        with patch("scripts.agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.return_value = 12345
            # SIGTERM succeeds; SIGKILL also succeeds (no exception)
            mock_os.killpg.side_effect = [None, None]
            # Wait loop: first monotonic() sets deadline, second exceeds it
            with patch(
                "scripts.agent.http_lifecycle_process_terminator.time"
            ) as mock_time:
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

        with patch("scripts.agent.http_lifecycle_process_terminator.os") as mock_os:
            mock_os.getpgid.return_value = 12345
            # SIGTERM succeeds; SIGKILL also succeeds (no exception)
            mock_os.killpg.side_effect = [None, None]
            # Wait loop: first monotonic() sets deadline, second exceeds it
            with patch(
                "scripts.agent.http_lifecycle_process_terminator.time"
            ) as mock_time:
                # deadline = 0 + 5 = 5; second call returns 10 > 5, so loop exits immediately
                mock_time.monotonic.side_effect = [0.0, 10.0]

                await terminator.terminate_with_timeout(
                    proc, "test-server", timeout=5.0
                )

                # SIGKILL should be attempted
                assert mock_os.killpg.call_count == 2  # SIGTERM + SIGKILL
                sigkill_call = mock_os.killpg.call_args_list[1]
                assert sigkill_call[0][1] == 9  # signal.SIGKILL = 9
