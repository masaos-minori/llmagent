"""tests/agent/test_stdin_reader.py — StdinReader: request-driven reads on a daemon thread."""

from __future__ import annotations

import asyncio
import subprocess  # nosec B404 — fixed argv, no shell
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.stdin_reader import StdinReader

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


class _FakeInput:
    """A scripted read function that records calls and can block until released."""

    def __init__(
        self, outcomes: list[object] | None = None, block: bool = False
    ) -> None:
        self.outcomes = list(outcomes or [])
        self.prompts: list[str] = []
        self.started = threading.Event()
        self.release = threading.Event()
        if not block:
            self.release.set()

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        self.started.set()
        self.release.wait(5)
        outcome = self.outcomes.pop(0) if self.outcomes else "line"
        if isinstance(outcome, BaseException):
            raise outcome
        assert isinstance(outcome, str)
        return outcome


class TestRequestDrivenRead:
    @pytest.mark.asyncio
    async def test_no_line_is_read_before_a_request(self) -> None:
        fake = _FakeInput(["a"])
        reader = StdinReader(read_fn=fake)
        await asyncio.sleep(0.05)
        assert fake.prompts == []
        assert reader._thread is None

    @pytest.mark.asyncio
    async def test_one_read_per_request(self) -> None:
        fake = _FakeInput(["a", "b", "c"])
        reader = StdinReader(prompt="> ", read_fn=fake)
        assert [
            await reader.read(),
            await reader.read("... "),
            await reader.read(),
        ] == [
            "a",
            "b",
            "c",
        ]
        assert fake.prompts == ["> ", "... ", "> "]

    @pytest.mark.asyncio
    async def test_second_concurrent_read_is_refused(self) -> None:
        fake = _FakeInput(["a"], block=True)
        reader = StdinReader(read_fn=fake)
        first = asyncio.ensure_future(reader.read())
        await asyncio.sleep(0.05)
        with pytest.raises(RuntimeError, match="already pending"):
            await reader.read()
        fake.release.set()
        assert await first == "a"

    @pytest.mark.asyncio
    async def test_default_read_function_is_looked_up_at_call_time(self) -> None:
        reader = StdinReader()
        with patch("builtins.input", return_value="typed") as mock_input:
            assert await reader.read("> ") == "typed"
        mock_input.assert_called_once_with("> ")


class TestCancelledRequestDelivery:
    @pytest.mark.asyncio
    async def test_line_after_cancel_goes_to_the_newest_request_without_a_second_read(
        self,
    ) -> None:
        fake = _FakeInput(["late"], block=True)
        reader = StdinReader(read_fn=fake)
        first = asyncio.ensure_future(reader.read())
        await asyncio.sleep(0.05)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        second = asyncio.ensure_future(reader.read("... "))
        await asyncio.sleep(0.05)
        fake.release.set()
        assert await asyncio.wait_for(second, 1.0) == "late"
        await asyncio.sleep(0.05)
        assert len(fake.prompts) == 1

    @pytest.mark.asyncio
    async def test_line_after_cancel_is_discarded_when_nobody_waits(self) -> None:
        fake = _FakeInput(["lost", "next"], block=True)
        reader = StdinReader(read_fn=fake)
        first = asyncio.ensure_future(reader.read())
        await asyncio.sleep(0.05)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        fake.release.set()
        await asyncio.sleep(0.1)
        assert await asyncio.wait_for(reader.read(), 1.0) == "next"

    def test_delivery_to_a_closed_loop_is_a_silent_no_op(self) -> None:
        fake = _FakeInput(["x", "again"], block=True)
        reader = StdinReader(read_fn=fake)
        loop = asyncio.new_event_loop()
        pending = loop.create_task(reader.read())
        loop.run_until_complete(asyncio.sleep(0.05))
        loop.close()
        errors: list[object] = []
        with patch.object(threading, "excepthook", errors.append):
            fake.release.set()
            time.sleep(0.1)
        assert errors == []
        assert reader._thread is not None
        assert reader._thread.is_alive()
        assert not pending.done()
        # The worker is still serviceable from a fresh loop after the closed-loop delivery.
        assert asyncio.run(reader.read()) == "again"


class TestWorkerSurvivesReadErrors:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "error",
        [EOFError(), KeyboardInterrupt(), SystemExit(), RuntimeError("boom")],
    )
    async def test_exception_reaches_the_caller_and_the_next_read_works(
        self, error: BaseException
    ) -> None:
        fake = _FakeInput([error, "ok"])
        reader = StdinReader(read_fn=fake)
        with pytest.raises(type(error)):
            await reader.read()
        assert await reader.read() == "ok"


class TestReaderUsesNoExecutorAndNoNonDaemonThread:
    @pytest.mark.asyncio
    async def test_worker_is_a_daemon_thread_and_no_executor_is_used(self) -> None:
        loop = asyncio.get_running_loop()
        before = {t for t in threading.enumerate() if not t.daemon}
        fake = _FakeInput(["a"])
        reader = StdinReader(read_fn=fake)
        with patch.object(loop, "run_in_executor") as spy:
            await reader.read()
        spy.assert_not_called()
        assert reader._thread is not None
        assert reader._thread.daemon
        assert {t for t in threading.enumerate() if not t.daemon} == before


class TestAbandonedReadDoesNotDelayProcessExit:
    @pytest.mark.integration
    def test_child_exits_promptly_while_its_read_is_still_blocked(self) -> None:
        script = (
            "import asyncio, sys\n"
            f"sys.path.insert(0, {str(_SCRIPTS)!r})\n"
            "from agent.stdin_reader import StdinReader\n"
            "async def main():\n"
            "    reader = StdinReader()\n"
            "    task = asyncio.ensure_future(reader.read('> '))\n"
            "    await asyncio.sleep(0.1)\n"
            "    task.cancel()\n"
            "    try:\n"
            "        await task\n"
            "    except asyncio.CancelledError:\n"
            "        pass\n"
            "asyncio.run(main())\n"
        )
        proc = subprocess.Popen(  # nosec B603 — fixed argv, no shell
            [sys.executable, "-c", script],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        start = time.monotonic()
        try:
            returncode = proc.wait(timeout=10)
        finally:
            if proc.poll() is None:
                proc.kill()
            if proc.stdin is not None:
                proc.stdin.close()
        elapsed = time.monotonic() - start
        assert returncode == 0, proc.stderr.read() if proc.stderr else ""
        assert elapsed < 2.0
