import logging
import os
import signal
import subprocess
import sys
import time
from unittest.mock import MagicMock

import pytest
from agent.http_lifecycle_errors import TerminationOutcome
from agent.http_lifecycle_process_terminator import ProcessTerminator


class _FakeGroup:
    """Replace os.getpgid/os.killpg so each signal kind behaves as scripted.

    Each of ``term``/``kill``/``probe`` is None (the call succeeds) or an exception
    instance to raise. ``probe`` is the ``killpg(pgid, 0)`` liveness check, so
    ``ProcessLookupError()`` there means "the group is gone".
    """

    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        pgid: int | OSError = 777,
        term: BaseException | None = None,
        kill: BaseException | None = None,
        probe: BaseException | None = None,
    ) -> None:
        self.calls: list[tuple[int, int]] = []
        self._script = {signal.SIGTERM: term, signal.SIGKILL: kill, 0: probe}

        def fake_getpgid(pid: int) -> int:
            if isinstance(pgid, OSError):
                raise pgid
            return pgid

        def fake_killpg(pg: int, sig: int) -> None:
            self.calls.append((pg, sig))
            err = self._script[sig]
            if err is not None:
                raise err

        monkeypatch.setattr(os, "getpgid", fake_getpgid)
        monkeypatch.setattr(os, "killpg", fake_killpg)

    @property
    def signals(self) -> list[int]:
        return [sig for _, sig in self.calls]


def _proc(*, poll: object = None, pid: int = 12345) -> MagicMock:
    proc = MagicMock()
    proc.pid = pid
    proc.poll.return_value = poll
    return proc


def _fast_terminator() -> ProcessTerminator:
    return ProcessTerminator(
        terminate_poll_interval_sec=0.001, kill_confirm_timeout_sec=0.02
    )


class TestTerminationOutcomeContract:
    """Each exit of terminate_with_timeout reports only what it proved."""

    @pytest.mark.asyncio
    async def test_exited_process_is_already_exited_without_any_signal(
        self, monkeypatch
    ):
        group = _FakeGroup(monkeypatch)

        outcome = await _fast_terminator().terminate_with_timeout(
            _proc(poll=0), "srv", timeout=0.0
        )

        assert outcome is TerminationOutcome.ALREADY_EXITED
        assert group.calls == []

    @pytest.mark.asyncio
    async def test_group_gone_within_timeout_is_exited(self, monkeypatch):
        group = _FakeGroup(monkeypatch, probe=ProcessLookupError())

        outcome = await _fast_terminator().terminate_with_timeout(
            _proc(), "srv", timeout=1.0
        )

        assert outcome is TerminationOutcome.EXITED
        assert group.signals == [signal.SIGTERM, 0]

    @pytest.mark.asyncio
    async def test_group_already_gone_at_sigterm_is_already_exited(self, monkeypatch):
        _FakeGroup(monkeypatch, term=ProcessLookupError())

        outcome = await _fast_terminator().terminate_with_timeout(
            _proc(), "srv", timeout=1.0
        )

        assert outcome is TerminationOutcome.ALREADY_EXITED

    @pytest.mark.asyncio
    async def test_sigkill_with_exit_observed_is_exited(self, monkeypatch):
        probes = iter([None, ProcessLookupError()])  # still there, then gone
        group = _FakeGroup(monkeypatch)

        def probe_then_gone(pg: int, sig: int) -> None:
            group.calls.append((pg, sig))
            if sig == 0 and group.signals.count(signal.SIGKILL):
                err = next(probes)
                if err is not None:
                    raise err

        monkeypatch.setattr(os, "killpg", probe_then_gone)

        outcome = await _fast_terminator().terminate_with_timeout(
            _proc(), "srv", timeout=0.0
        )

        assert outcome is TerminationOutcome.EXITED
        assert group.signals[:2] == [signal.SIGTERM, signal.SIGKILL]

    @pytest.mark.asyncio
    async def test_sigkill_delivered_but_group_never_leaves_is_unconfirmed(
        self, monkeypatch, caplog
    ):
        group = _FakeGroup(monkeypatch)  # the liveness probe keeps succeeding
        start = time.monotonic()

        with caplog.at_level(
            logging.ERROR, logger="agent.http_lifecycle_process_terminator"
        ):
            outcome = await _fast_terminator().terminate_with_timeout(
                _proc(pid=4242), "srv", timeout=0.0
            )

        assert outcome is TerminationOutcome.EXIT_UNCONFIRMED
        assert signal.SIGKILL in group.signals
        assert time.monotonic() - start < 0.5
        assert "pid=4242" in caplog.text and "pgid=777" in caplog.text

    @pytest.mark.asyncio
    async def test_sigkill_already_gone_is_exited_and_log_is_formatted(
        self, monkeypatch, caplog
    ):
        _FakeGroup(monkeypatch, kill=ProcessLookupError())

        with caplog.at_level(
            logging.INFO, logger="agent.http_lifecycle_process_terminator"
        ):
            outcome = await _fast_terminator().terminate_with_timeout(
                _proc(), "srv", timeout=0.0
            )

        assert outcome is TerminationOutcome.EXITED
        assert "%d" not in caplog.text
        assert "pgid=777" in caplog.text

    @pytest.mark.asyncio
    async def test_sigkill_failure_after_sigterm_is_unconfirmed_and_named(
        self, monkeypatch, caplog
    ):
        group = _FakeGroup(monkeypatch, kill=PermissionError("denied"))

        with caplog.at_level(
            logging.ERROR, logger="agent.http_lifecycle_process_terminator"
        ):
            outcome = await _fast_terminator().terminate_with_timeout(
                _proc(pid=4242), "srv", timeout=0.0
            )

        assert outcome is TerminationOutcome.EXIT_UNCONFIRMED
        assert group.signals == [signal.SIGTERM, signal.SIGKILL]
        assert "srv" in caplog.text
        assert "pid=4242" in caplog.text and "pgid=777" in caplog.text

    @pytest.mark.asyncio
    async def test_sigterm_denied_and_fallback_delivered_is_unconfirmed(
        self, monkeypatch
    ):
        _FakeGroup(monkeypatch, term=PermissionError("denied"))
        proc = _proc()

        outcome = await _fast_terminator().terminate_with_timeout(
            proc, "srv", timeout=1.0
        )

        assert outcome is TerminationOutcome.EXIT_UNCONFIRMED
        proc.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_sigterm_denied_and_fallback_failing_is_not_delivered(
        self, monkeypatch
    ):
        _FakeGroup(monkeypatch, term=PermissionError("denied"))
        proc = _proc()
        proc.terminate.side_effect = PermissionError("denied")

        outcome = await _fast_terminator().terminate_with_timeout(
            proc, "srv", timeout=1.0
        )

        assert outcome is TerminationOutcome.SIGNAL_NOT_DELIVERED

    @pytest.mark.asyncio
    async def test_unresolvable_pgid_with_delivered_fallback_is_unconfirmed(
        self, monkeypatch
    ):
        group = _FakeGroup(monkeypatch, pgid=OSError("no such process"))
        proc = _proc()

        outcome = await _fast_terminator().terminate_with_timeout(
            proc, "srv", timeout=1.0
        )

        assert outcome is TerminationOutcome.EXIT_UNCONFIRMED
        proc.terminate.assert_called_once()
        assert group.calls == []

    @pytest.mark.asyncio
    async def test_unresolvable_pgid_with_failing_fallback_is_not_delivered(
        self, monkeypatch
    ):
        _FakeGroup(monkeypatch, pgid=OSError("no such process"))
        proc = _proc()
        proc.terminate.side_effect = OSError("denied")

        outcome = await _fast_terminator().terminate_with_timeout(
            proc, "srv", timeout=1.0
        )

        assert outcome is TerminationOutcome.SIGNAL_NOT_DELIVERED

    @pytest.mark.asyncio
    async def test_unresolvable_pgid_with_exited_process_is_already_exited(
        self, monkeypatch
    ):
        _FakeGroup(monkeypatch, pgid=ProcessLookupError())
        proc = _proc(poll=0)

        outcome = await _fast_terminator().terminate_with_timeout(
            proc, "srv", timeout=1.0
        )

        assert outcome is TerminationOutcome.ALREADY_EXITED
        proc.terminate.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_integer_pid_takes_fallback_without_raising(self, monkeypatch):
        group = _FakeGroup(monkeypatch)
        proc = MagicMock()  # pid is a MagicMock, not an int
        proc.poll.return_value = None

        outcome = await _fast_terminator().terminate_with_timeout(
            proc, "srv", timeout=1.0
        )

        assert outcome is TerminationOutcome.EXIT_UNCONFIRMED
        proc.terminate.assert_called_once()
        assert group.calls == []

    @pytest.mark.asyncio
    async def test_timeout_has_no_default(self):
        with pytest.raises(TypeError):
            await _fast_terminator().terminate_with_timeout(  # type: ignore[call-arg] — intentionally omitting the required timeout
                _proc(), "srv"
            )

    def test_only_confirmed_outcomes_are_confirmed(self):
        assert {o for o in TerminationOutcome if o.confirmed} == {
            TerminationOutcome.EXITED,
            TerminationOutcome.ALREADY_EXITED,
        }


class TestProcessTerminatorPgidResolution:
    """signal the real group resolved via os.getpgid."""

    @pytest.mark.asyncio
    async def test_killpg_targets_resolved_group_when_pid_differs(self, monkeypatch):
        group = _FakeGroup(monkeypatch, pgid=777)

        await _fast_terminator().terminate_with_timeout(
            _proc(pid=12345), "srv", timeout=0.0
        )

        assert {pg for pg, _ in group.calls} == {777}
        assert group.signals[:2] == [signal.SIGTERM, signal.SIGKILL]

    @pytest.mark.asyncio
    async def test_wait_exited_uses_resolved_group(self, monkeypatch):
        group = _FakeGroup(monkeypatch, pgid=777, probe=ProcessLookupError())

        exited = await ProcessTerminator().wait_exited(_proc(), "srv", timeout=1.0)

        assert exited is True
        assert group.calls[-1] == (777, 0)

    @pytest.mark.asyncio
    async def test_poll_error_is_treated_as_still_running(self, monkeypatch):
        group = _FakeGroup(monkeypatch)
        proc = _proc()
        proc.poll.side_effect = OSError("poll failed")

        await _fast_terminator().terminate_with_timeout(proc, "srv", timeout=0.0)

        assert group.calls[0] == (777, signal.SIGTERM)

    @pytest.mark.asyncio
    async def test_proc_without_poll_is_treated_as_still_running(self, monkeypatch):
        group = _FakeGroup(monkeypatch)
        proc = MagicMock(spec=["pid", "terminate"])
        proc.pid = 12345

        await _fast_terminator().terminate_with_timeout(proc, "srv", timeout=0.0)

        assert group.calls[0] == (777, signal.SIGTERM)


def _spawn(code: str) -> subprocess.Popen[bytes]:
    """Start a real child as its own session leader and wait until it is ready."""
    proc = subprocess.Popen(  # nosec B603 — fixed argv built from this test's own constants, no user input
        [sys.executable, "-c", code],
        start_new_session=True,
        stdout=subprocess.PIPE,
    )
    assert proc.stdout is not None
    assert proc.stdout.readline().strip() == b"ready"
    return proc


def _cleanup(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    if proc.stdout is not None:
        proc.stdout.close()


_EXIT_ON_SIGTERM = "import time; print('ready', flush=True); time.sleep(60)"
_IGNORE_SIGTERM = (
    "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
    "print('ready', flush=True); time.sleep(60)"
)


class TestProcessTerminatorRealChild:
    """REQ-005: real-subprocess coverage of REQ-001 and REQ-004."""

    @pytest.mark.asyncio
    async def test_child_exiting_on_sigterm_is_detected_promptly(self):
        """REQ-001: an exited, unreaped child must not be waited on until timeout."""
        proc = _spawn(_EXIT_ON_SIGTERM)
        try:
            start = time.monotonic()
            result = await ProcessTerminator().terminate_with_timeout(
                proc, "test-server", timeout=10.0
            )
            elapsed = time.monotonic() - start

            assert result is TerminationOutcome.EXITED
            assert proc.poll() is not None
            assert elapsed < 5.0
        finally:
            _cleanup(proc)

    @pytest.mark.asyncio
    async def test_wait_exited_detects_an_exited_unreaped_child(self):
        """REQ-001: wait_exited shares the same liveness probe and the same flaw."""
        proc = _spawn(_EXIT_ON_SIGTERM)
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            exited = await ProcessTerminator().wait_exited(
                proc, "test-server", timeout=5.0
            )

            assert exited is True
        finally:
            _cleanup(proc)

    @pytest.mark.asyncio
    async def test_child_ignoring_sigterm_is_killed_after_timeout(self):
        """REQ-004: the SIGKILL backstop still removes a child that ignores SIGTERM."""
        proc = _spawn(_IGNORE_SIGTERM)
        try:
            result = await ProcessTerminator().terminate_with_timeout(
                proc, "test-server", timeout=1.0
            )

            assert result is TerminationOutcome.EXITED
            assert proc.wait(timeout=5) == -signal.SIGKILL
        finally:
            _cleanup(proc)
