"""tests/agent/test_repl_input_controller.py — ReplInputController: sole stdin owner."""

from __future__ import annotations

import asyncio
import threading

import pytest
from agent import repl_input_controller as ric
from agent.repl_input_controller import (
    InputBusyError,
    InputOutcome,
    InputRequest,
    InputState,
    InterruptAction,
    PromptKind,
    ReplInputController,
    get_input_controller,
    reset_input_controller,
)
from agent.stdin_reader import StdinReader


class _Script:
    """A scripted read function; ``block`` makes every read wait for ``release``."""

    def __init__(self, outcomes: list[object], block: bool = False) -> None:
        self.outcomes = list(outcomes)
        self.prompts: list[str] = []
        self.release = threading.Event()
        if not block:
            self.release.set()

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        self.release.wait(5)
        outcome = self.outcomes.pop(0) if self.outcomes else ""
        if isinstance(outcome, BaseException):
            raise outcome
        assert isinstance(outcome, str)
        return outcome


def _controller(script: _Script) -> ReplInputController:
    return ReplInputController(StdinReader(read_fn=script))


def _req(prompt: str = "> ", **kw: object) -> InputRequest:
    return InputRequest(PromptKind.NORMAL, prompt, **kw)  # type: ignore[arg-type] — kwargs are InputRequest fields


class TestOutcomes:
    @pytest.mark.asyncio
    async def test_completed_carries_text_and_request_identity(self) -> None:
        ctl = _controller(_Script(["hello"]))
        request = _req(operation_id="op-1")
        result = await ctl.submit(request)
        assert result.outcome is InputOutcome.COMPLETED
        assert result.text == "hello"
        assert result.request is request
        assert len(request.request_id) == 32
        assert request.operation_id == "op-1"

    @pytest.mark.asyncio
    async def test_request_ids_are_unique(self) -> None:
        assert _req().request_id != _req().request_id

    @pytest.mark.asyncio
    async def test_eof_and_interrupt_exceptions_map_to_eof(self) -> None:
        ctl = _controller(_Script([EOFError(), KeyboardInterrupt()]))
        assert (await ctl.submit(_req())).outcome is InputOutcome.EOF
        assert (await ctl.submit(_req())).outcome is InputOutcome.EOF

    @pytest.mark.asyncio
    async def test_timeout_ends_the_request_and_drops_the_late_line(self) -> None:
        script = _Script(["late-y", "fresh"], block=True)
        ctl = _controller(script)
        timed = await ctl.submit(_req(timeout_s=0.05))
        assert timed.outcome is InputOutcome.TIMED_OUT
        assert timed.text == ""
        follow = asyncio.ensure_future(ctl.submit(_req("next> ")))
        await asyncio.sleep(0.05)
        script.release.set()
        result = await asyncio.wait_for(follow, 1.0)
        assert result.text == "fresh"

    @pytest.mark.asyncio
    async def test_cancel_current_ends_the_request_as_cancelled(self) -> None:
        script = _Script(["x"], block=True)
        ctl = _controller(script)
        pending = asyncio.ensure_future(ctl.submit(_req()))
        await asyncio.sleep(0.05)
        assert ctl.cancel_current() is True
        assert (await pending).outcome is InputOutcome.CANCELLED
        script.release.set()

    @pytest.mark.asyncio
    async def test_shutdown_ends_the_request_as_shutdown(self) -> None:
        script = _Script(["x"], block=True)
        ctl = _controller(script)
        pending = asyncio.ensure_future(ctl.submit(_req()))
        await asyncio.sleep(0.05)
        ctl.shutdown()
        assert (await pending).outcome is InputOutcome.SHUTDOWN
        assert ctl.state is InputState.SHUTDOWN
        script.release.set()

    @pytest.mark.asyncio
    async def test_cancel_current_without_a_request_is_a_no_op(self) -> None:
        assert _controller(_Script([])).cancel_current() is False


class TestSingleOwner:
    @pytest.mark.asyncio
    async def test_a_second_request_while_one_is_active_is_refused(self) -> None:
        script = _Script(["a"], block=True)
        ctl = _controller(script)
        first = asyncio.ensure_future(ctl.submit(_req()))
        await asyncio.sleep(0.05)
        with pytest.raises(InputBusyError):
            await ctl.submit(_req())
        script.release.set()
        assert (await first).text == "a"

    @pytest.mark.asyncio
    async def test_destructive_request_is_refused_while_a_read_is_orphaned(
        self,
    ) -> None:
        script = _Script(["stale", "yes"], block=True)
        ctl = _controller(script)
        timed = await ctl.submit(_req(timeout_s=0.05))
        assert timed.outcome is InputOutcome.TIMED_OUT
        with pytest.raises(InputBusyError):
            await ctl.submit(
                InputRequest(PromptKind.MEMORY_DELETE, "Delete? ", destructive=True)
            )
        script.release.set()
        await asyncio.sleep(0.1)
        answer = await ctl.submit(
            InputRequest(PromptKind.MEMORY_DELETE, "Delete? ", destructive=True)
        )
        assert answer.text == "yes"

    @pytest.mark.asyncio
    async def test_outer_cancellation_cancels_the_read(self) -> None:
        script = _Script(["x"], block=True)
        ctl = _controller(script)
        pending = asyncio.ensure_future(ctl.submit(_req()))
        await asyncio.sleep(0.05)
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
        script.release.set()
        await asyncio.sleep(0.05)
        assert (await ctl.submit(_req())).outcome is InputOutcome.COMPLETED


class TestMultiline:
    @pytest.fixture(autouse=True)
    def _short_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ric, "MULTILINE_TIMEOUT_S", 0.05)

    @pytest.mark.asyncio
    async def test_continuation_lines_are_joined(self) -> None:
        ctl = _controller(_Script(["two\\", "three"]))
        result = await ctl.collect_multiline("one\\", lambda _m: None, True)
        assert result.outcome is InputOutcome.COMPLETED
        assert result.text == "one\ntwo\nthree"

    @pytest.mark.asyncio
    async def test_empty_line_and_eof_end_the_continuation(self) -> None:
        ctl = _controller(_Script([""]))
        assert (await ctl.collect_multiline("a\\", lambda _m: None, True)).text == "a"
        ctl = _controller(_Script([EOFError()]))
        assert (await ctl.collect_multiline("b\\", lambda _m: None, True)).text == "b"

    @pytest.mark.asyncio
    async def test_timeout_non_interactive_discards_partial_text(self) -> None:
        notes: list[str] = []
        ctl = _controller(_Script(["late"], block=True))
        result = await ctl.collect_multiline("keep\\", notes.append, False)
        assert result.outcome is InputOutcome.TIMED_OUT
        assert result.text == ""
        assert any("discarded" in n for n in notes)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("answer", "outcome", "text"),
        [
            ("s", InputOutcome.COMPLETED, "keep"),
            ("d", InputOutcome.TIMED_OUT, ""),
            ("", InputOutcome.TIMED_OUT, ""),
        ],
    )
    async def test_timeout_interactive_offers_send_continue_discard(
        self, answer: str, outcome: InputOutcome, text: str
    ) -> None:
        script = _Script(["dropped", answer], block=True)
        ctl = _controller(script)
        notes: list[str] = []
        task = asyncio.ensure_future(
            ctl.collect_multiline("keep\\", notes.append, True)
        )
        await asyncio.sleep(0.2)
        script.release.set()
        result = await asyncio.wait_for(task, 2.0)
        assert result.outcome is outcome
        assert result.text == text
        assert any("timed out" in n for n in notes)

    @pytest.mark.asyncio
    async def test_continue_choice_keeps_collecting(self) -> None:
        script = _Script(["dropped", "c", "more"], block=True)
        ctl = _controller(script)
        task = asyncio.ensure_future(
            ctl.collect_multiline("keep\\", lambda _m: None, True)
        )
        await asyncio.sleep(0.2)
        script.release.set()
        result = await asyncio.wait_for(task, 2.0)
        assert result.text == "keep\nmore"

    @pytest.mark.asyncio
    async def test_cancel_discards_partial_text(self) -> None:
        script = _Script(["x"], block=True)
        ctl = _controller(script)
        monkey = asyncio.ensure_future(
            ctl.collect_multiline("keep\\", lambda _m: None, True)
        )
        await asyncio.sleep(0.01)
        ctl.cancel_current()
        result = await asyncio.wait_for(monkey, 2.0)
        assert result.outcome is InputOutcome.CANCELLED
        assert result.text == ""
        script.release.set()


class TestInterruptState:
    def test_prompt_state_discards_input(self) -> None:
        ctl = _controller(_Script([]))
        assert ctl.handle_interrupt() is InterruptAction.DISCARD_INPUT

    def test_turn_state_cancels_the_turn(self) -> None:
        ctl = _controller(_Script([]))
        calls: list[str] = []
        ctl.begin_turn(lambda: calls.append("turn"))
        assert ctl.state is InputState.TURN
        assert ctl.handle_interrupt() is InterruptAction.CANCEL_TURN
        assert calls == ["turn"]
        ctl.end_turn()
        assert ctl.state is InputState.PROMPT

    def test_job_state_cancels_the_job_and_restores_the_state(self) -> None:
        ctl = _controller(_Script([]))
        calls: list[str] = []
        ctl.begin_turn(lambda: calls.append("turn"))
        ctl.begin_job(lambda: calls.append("job"))
        assert ctl.handle_interrupt() is InterruptAction.CANCEL_JOB
        assert calls == ["job"]
        ctl.end_job()
        assert ctl.state is InputState.TURN

    def test_shutdown_state_reports_shutdown_in_progress(self) -> None:
        ctl = _controller(_Script([]))
        ctl.shutdown()
        assert ctl.handle_interrupt() is InterruptAction.SHUTDOWN_IN_PROGRESS
        ctl.begin_turn(lambda: None)
        assert ctl.state is InputState.SHUTDOWN


class TestSharedAccessor:
    def test_same_instance_until_reset(self) -> None:
        reset_input_controller()
        first = get_input_controller()
        assert get_input_controller() is first
        reset_input_controller()
        assert get_input_controller() is not first
        reset_input_controller()
