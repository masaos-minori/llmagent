"""scripts/agent/repl_input_loop.py

ReplInputLoop — REPL input/dispatch responsibility extraction.

Owns: _repl_loop, _read_input, _should_exit, _dispatch_line, _abort_input.
Handles: readline, multiline continuation, shutdown event racing, command routing,
acceptance refusal once the shutdown budget stops accepting work.
"""

import asyncio
import sqlite3
import sys
from collections.abc import Callable
from enum import StrEnum
from typing import TYPE_CHECKING, Any, cast

from agent.output_tags import OutputTag
from agent.repl_input_controller import (
    InputOutcome,
    InputRequest,
    InputResult,
    PromptKind,
    ReplInputController,
    get_input_controller,
)
from agent.session import SchemaMissingError
from agent.shutdown_budget import ShutdownBudget, ShutdownPhase
from agent.turn_persistence import ConversationPersistenceError

if TYPE_CHECKING:
    from agent.cli_view import CLIView
    from agent.commands.registry import CommandRegistry
    from agent.context import AgentContext
    from agent.orchestrator import Orchestrator

_REPL_RESERVED_COMMANDS = frozenset(["/exit"])


class _TurnFlow(StrEnum):
    """How the REPL loop goes on after a turn."""

    NEXT = "next"
    CONTINUE = "continue"
    BREAK = "break"


class ReplInputLoop:
    """Manages REPL input reading, dispatch, and exit conditions.

    Owns the main input/dispatch loop, readline integration, multiline
    continuation, shutdown event racing, and command routing.

    Shutdown coordination:
        - shutdown_event is the single source of truth for shutdown signaling
        - _shutdown_watcher sets shutdown_done when shutdown_event fires
        - _read_input checks shutdown_done to decide whether to abort input
        - Signal handler delegates cancellation to shutdown_event.set() (see signal_handler.py)
        - the shutdown budget decides acceptance: no command or turn is dispatched
          once its phase is not accepting, and the graceful window is its remaining
          deadline rather than a window owned here

    _cmds lifecycle:
        - Set once after startup via bind(), together with the orchestrator
        - Immutable after binding — never reassigned
        - Checked in _repl_loop as the single authoritative precondition
    """

    _GRACEFUL_TIMEOUT_S: float = 10.0

    def __init__(
        self,
        ctx: "AgentContext",
        view: "CLIView",
        shutdown_event: asyncio.Event | None,
        *,
        budget: ShutdownBudget | None = None,
    ) -> None:
        self._ctx = ctx
        self._view = view
        self._shutdown_event = shutdown_event
        self._budget = budget
        self._turn_active: bool = False
        self._input_coro: asyncio.Task[InputResult] | None = None
        self._input: ReplInputController = get_input_controller()
        self._turn_cancel_requested: bool = False
        self._refusal_reported: bool = False
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None

    def bind(self, cmds: "CommandRegistry", orchestrator: "Orchestrator") -> None:
        """Attach the startup results; _repl_loop refuses to run until this is called."""
        self._cmds = cmds
        self._orchestrator = orchestrator

    async def run(self, banner_callback: Callable[[], None]) -> None:
        """Run the main REPL loop.

        Persistence is not owned here: AgentREPL.run() persists on every exit path.
        Each error is reported to the operator exactly once.
        """
        ctx = self._ctx
        reported = False
        try:
            banner_callback()
            try:
                ctx.session.start()
            except SchemaMissingError as e:
                reported = True
                self._view.write_fatal(str(e))
                raise
            except RuntimeError as e:
                reported = True
                self._view.write_fatal(f"Session start failed: {e}")
                raise
            except sqlite3.Error as e:
                reported = True
                self._view.write_fatal(
                    f"Database unavailable during session start ({e.__class__.__name__}): {e}. Check DB connectivity or run: bash deploy/init_db.sh"
                )
                raise RuntimeError(
                    f"Database unavailable ({e.__class__.__name__}): {e}"
                ) from None
            if (
                ctx.services_required.tools is not None
                and ctx.session.session_id is not None
            ):
                ctx.services_required.tools.set_session_id(str(ctx.session.session_id))
            await self._repl_loop()
        except RuntimeError as e:
            if not reported:
                self._view.write_fatal(str(e))
            raise

    def _abort_input(self) -> None:
        """Signal end-of-turn display and clear the tracked input task."""
        self._view.write_turn_end()
        self._input_coro = None

    def _accepts_work(self) -> bool:
        """True while the shutdown budget still accepts new commands and turns."""
        return self._budget is None or self._budget.phase is ShutdownPhase.ACCEPTING

    def _graceful_window(self) -> float:
        """How long a running turn may finish for once shutdown began."""
        if self._budget is not None:
            return self._budget.remaining()
        return self._GRACEFUL_TIMEOUT_S

    def _report_shutdown_refusal(self) -> None:
        """State once per shutdown that new commands and turns are refused."""
        if self._budget is None or self._refusal_reported:
            return
        self._refusal_reported = True
        self._view.write_warning(
            f"Shutdown in progress ({self._budget.phase.value}); "
            "new commands and turns are refused."
        )

    def _report_degraded_refusal(self, ctx: "AgentContext") -> "_TurnFlow":
        """Refuse one turn while the session is degraded (REQ-004, AC-3).

        The state is read from the session object, not a local flag, so the refusal
        holds across turns until the UNK-01 clearing seam is implemented. The loop
        stays responsive: the refusal writes a warning and returns NEXT without
        dispatching a turn.
        """
        self._view.write_warning(
            "Session is degraded (compensation failed); turn refused."
        )
        return _TurnFlow.NEXT

    def _report_interrupted_loop(self) -> None:
        """State that an interrupt after shutdown began ends the input loop."""
        self._view.write_warning("Interrupted during shutdown; ending the input loop.")

    def _stop_accepting_input(self) -> None:
        """Release a pending approval or transition wait with the shutdown outcome."""
        self._input.shutdown()

    def _log_graceful_shutdown_timeout(self, window: float) -> None:
        """Log a warning when graceful shutdown times out, naming the window used."""
        self._view.write_warning(f"Graceful shutdown timed out after {window}s")

    def _surface_turn_error(self, exc: Exception) -> None:
        """Surface an unexpected per-turn error through the CLI view.

        Called from _repl_loop when a turn raises a non-shutdown, non-timeout
        exception, so the operator sees the failure and the loop stays usable.
        """
        self._view.write_fatal(f"{exc.__class__.__name__}: {exc}")

    def _map_outcome(self, result: InputResult) -> str | None:
        """Map a read outcome to a line, or None when the loop must end.

        A cancelled or timed-out request is discarded: an empty line makes the loop
        prompt again. The abandoned read still owns the terminal line, so the line
        typed next is consumed and dropped before the new prompt reads.
        """
        if result.outcome is InputOutcome.COMPLETED:
            return result.text.strip()
        if result.outcome in (InputOutcome.EOF, InputOutcome.SHUTDOWN):
            self._abort_input()
            return None
        self._view.write_warning(
            "Input discarded; press Enter once, the next line you type is dropped."
        )
        return ""

    async def _read_input(self, loop: asyncio.AbstractEventLoop) -> str | None:
        """Read a single input line through the controller, with multiline continuation."""
        request = InputRequest(PromptKind.NORMAL, "> ")
        shutdown_event = self._shutdown_event
        if shutdown_event is not None:
            input_coro = asyncio.ensure_future(self._input.submit(request))
            self._input_coro = input_coro
            shutdown_done = False

            async def _shutdown_watcher() -> None:
                """Wait for shutdown event and signal completion."""
                nonlocal shutdown_done
                await shutdown_event.wait()
                shutdown_done = True

            shutdown_coro = asyncio.ensure_future(_shutdown_watcher())
            try:
                done, pending = await asyncio.wait(
                    {input_coro, shutdown_coro},
                    return_when=asyncio.FIRST_COMPLETED,
                )
            except Exception:
                input_coro.cancel()
                shutdown_coro.cancel()
                raise
            # _read_input performs cancellation on the shutdown-done branch
            if shutdown_done or shutdown_coro in done:
                input_coro.cancel()
                try:
                    await input_coro
                except asyncio.CancelledError:
                    pass
                self._abort_input()
                return None
            try:
                result = input_coro.result()
            except asyncio.CancelledError:
                # Input was cancelled by signal handler — treat as shutdown
                self._abort_input()
                return None
        else:
            result = await self._input.submit(request)
        line = self._map_outcome(result)
        if line is None or not line.endswith("\\"):
            return line
        multiline = await self._input.collect_multiline(
            line, self._view.write_warning, sys.stdin.isatty()
        )
        return self._map_outcome(multiline)

    def _turn_cancel_pending(self) -> bool:
        """True when Ctrl-C (not shutdown) cancelled the running turn."""
        return self._turn_cancel_requested

    def _turn_cancelled(self) -> None:
        """Report a Ctrl-C turn cancellation and clear its flag."""
        self._turn_cancel_requested = False
        self._view.write_warning("Turn cancelled (Ctrl-C).")

    def _flow_after_interrupt(self) -> "_TurnFlow":
        """Decide how the loop goes on after Ctrl-C cancelled the running turn.

        While the budget accepts work the session keeps prompting. Once shutdown has
        begun the interrupt means the running step was stopped, so the loop ends and
        the coordinator's sequence advances instead of prompting again.
        """
        if self._accepts_work():
            return _TurnFlow.CONTINUE
        self._report_interrupted_loop()
        return _TurnFlow.BREAK

    def _should_exit(self, line: str, ctx: "AgentContext") -> bool:
        """Return True when the REPL loop should terminate."""
        if ctx.conv.shutdown_requested:
            self._view.write_warning("Shutdown requested, exiting...")
            return True
        if line == "/exit":
            return True
        return False

    async def _dispatch_line(self, line: str, ctx: "AgentContext") -> None:
        """Dispatch a non-empty, non-exit line to commands or the orchestrator."""
        if self._orchestrator is None:
            raise RuntimeError("_dispatch_line called before _init_components()")
        if not self._accepts_work():
            # The last gate before the router and the orchestrator: a line read
            # before shutdown began is refused here rather than started.
            self._report_shutdown_refusal()
            return
        if line.startswith("/"):
            cmds = cast("CommandRegistry", self._cmds)
            matched = await cmds.dispatch(line)
            if not matched:
                # Echo only the command token (REQ-006): arguments may carry a secret
                # or a path and must not reach the terminal or the forwarded logs.
                token = line.split(None, 1)[0]
                self._view.write_warning(
                    f"Unknown command: {token}  (type /help for commands)"
                )
        else:
            _prev_partial = ctx.stats.stat_partial_completions
            await self._orchestrator.handle_turn(line)
            if ctx.stats.stat_partial_completions > _prev_partial:
                self._view.write_warning(
                    "Partial LLM completion stored. Use /stats to see count."
                )

    def _begin_turn_state(self, dispatch_task: "asyncio.Future[None]") -> None:
        """Tell the controller a turn runs; Ctrl-C then cancels exactly this task."""

        def _cancel_turn() -> None:
            self._turn_cancel_requested = True
            if (
                self._budget is not None
                and self._budget.phase is not ShutdownPhase.ACCEPTING
            ):
                # An interrupt after shutdown began is routed to the shared budget so
                # the step the coordinator is running stops too, not only this turn.
                self._budget.request_interrupt()
            dispatch_task.cancel()

        self._turn_cancel_requested = False
        self._input.begin_turn(_cancel_turn)

    async def _await_turn(
        self, dispatch_task: "asyncio.Future[Any]", ctx: "AgentContext"
    ) -> "_TurnFlow":
        """Wait for one turn, racing it against shutdown; report how the loop goes on."""
        if self._shutdown_event is not None and not self._shutdown_event.is_set():
            shutdown_task: asyncio.Future[Any] = asyncio.ensure_future(
                self._shutdown_event.wait()
            )
            done, pending = await asyncio.wait(
                {dispatch_task, shutdown_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if dispatch_task in done and shutdown_task not in done:
                # dispatch finished first and shutdown has not (yet)
                # fired — the normal, no-shutdown-race case.
                if dispatch_task.cancelled() and self._turn_cancel_pending():
                    shutdown_task.cancel()
                    self._turn_cancelled()
                    return self._flow_after_interrupt()
                dispatch_task.result()  # propagate exception if any
                if shutdown_task in pending:
                    shutdown_task.cancel()
                return _TurnFlow.CONTINUE
            # shutdown_task completed first, or both completed in the
            # same tick (dispatch finishing right as shutdown fires) —
            # either way, exit rather than looping back to _read_input.
            if dispatch_task in done:
                dispatch_task.result()  # propagate exception if any
            if shutdown_task in pending:
                shutdown_task.cancel()
            if dispatch_task in pending:
                window = self._graceful_window()
                dispatch_task.cancel()
                try:
                    await asyncio.wait_for(dispatch_task, timeout=window)
                except asyncio.CancelledError:
                    pass
                except TimeoutError:
                    self._log_graceful_shutdown_timeout(window)
            return _TurnFlow.BREAK
        # _shutdown_event is None or already set — await the already-created dispatch_task
        shutting_down = ctx.conv.shutdown_requested or (
            self._shutdown_event is not None and self._shutdown_event.is_set()
        )
        bounded: float | None = self._graceful_window() if shutting_down else None
        try:
            await asyncio.wait_for(dispatch_task, timeout=bounded)
        except TimeoutError:
            if shutting_down:
                self._log_graceful_shutdown_timeout(bounded or 0.0)
                return _TurnFlow.BREAK
            raise
        return _TurnFlow.NEXT

    async def _guarded_turn(self, line: str, ctx: "AgentContext") -> "_TurnFlow":
        """Run one turn, containing per-turn errors so the session stays usable."""
        self._turn_active = True
        ctx.conv.is_processing = True
        try:
            dispatch_task = asyncio.ensure_future(self._dispatch_line(line, ctx))
            self._begin_turn_state(dispatch_task)
            return await self._await_turn(dispatch_task, ctx)
        except TimeoutError:
            if ctx.conv.shutdown_requested:
                self._log_graceful_shutdown_timeout(self._graceful_window())
                return _TurnFlow.BREAK
            raise
        except asyncio.CancelledError:
            if not self._turn_cancel_pending():
                raise
            self._turn_cancelled()
            if not self._accepts_work():
                self._report_interrupted_loop()
                return _TurnFlow.BREAK
        except ConversationPersistenceError as exc:  # seq 10: compensated turn; surface distinctly before the generic handler
            self._view.write_turn_not_persisted()
            # AC-3: the surfaced message reports which compensation outcome happened.
            self._view.write_warning(f"compensation: {exc.compensation}")
        except Exception as exc:  # noqa: BLE001 — contain unexpected per-turn errors so the interactive session stays usable after a failing turn
            self._surface_turn_error(exc)
        finally:
            self._turn_active = False
            self._input.end_turn()
            self._turn_cancel_requested = False
            ctx.conv.is_processing = False
        return _TurnFlow.NEXT

    async def _repl_loop(self) -> None:
        """Process user input lines until /exit, EOF, or shutdown request."""
        ctx = self._ctx
        if self._cmds is None:
            raise RuntimeError("_repl_loop called before _init_components()")
        if self._orchestrator is None:
            raise RuntimeError("_repl_loop called before _init_components()")
        loop = asyncio.get_running_loop()
        while True:
            if not self._accepts_work():
                # Shutdown began: stop offering prompts, release any pending approval
                # with the shutdown outcome, and let the coordinator's sequence run.
                self._report_shutdown_refusal()
                self._stop_accepting_input()
                break
            line = await self._read_input(loop)
            if line is None:
                break
            if not line:
                continue
            if self._should_exit(line, ctx):
                break
            # Warn once about disabled memory
            if ctx.conv.memory_disabled and not ctx.conv.memory_warning_shown:
                ctx.conv.memory_warning_shown = True
                self._view.write_warning(
                    f"{OutputTag.NON_FATAL} Memory is disabled for this session."
                )
            if ctx.session.is_degraded:
                flow = self._report_degraded_refusal(ctx)
            else:
                flow = await self._guarded_turn(line, ctx)
            if flow is _TurnFlow.BREAK:
                break
            if flow is _TurnFlow.CONTINUE:
                continue
            if ctx.conv.shutdown_requested:
                break
