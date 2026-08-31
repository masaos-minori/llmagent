"""scripts/agent/repl_input_loop.py

ReplInputLoop — REPL input/dispatch responsibility extraction.

Owns: _repl_loop, _read_input, _should_exit, _dispatch_line, _abort_input.
Handles: readline, multiline continuation, shutdown event racing, command routing.
"""

import asyncio
import sqlite3
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

from agent.output_tags import OutputTag
from agent.session import SchemaMissingError

if TYPE_CHECKING:
    from agent.cli_view import CLIView
    from agent.commands.registry import CommandRegistry
    from agent.context import AgentContext
    from agent.orchestrator import Orchestrator

_REPL_RESERVED_COMMANDS = frozenset(["/exit"])


class ReplInputLoop:
    """Manages REPL input reading, dispatch, and exit conditions.

    Owns the main input/dispatch loop, readline integration, multiline
    continuation, shutdown event racing, and command routing.
    """

    _GRACEFUL_TIMEOUT_S: float = 10.0

    def __init__(
        self,
        ctx: "AgentContext",
        view: "CLIView",
        shutdown_event: asyncio.Event | None,
    ) -> None:
        self._ctx = ctx
        self._view = view
        self._shutdown_event = shutdown_event
        self._turn_active: bool = False
        self._input_coro: asyncio.Task[str] | None = None
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None

    async def run(
        self,
        banner_callback: Callable[[], None],
        persister_callback: Callable[[], None]
        | Callable[[], "Coroutine[Any, Any, None]"]
        | None = None,
    ) -> None:
        """Run the main REPL loop."""
        ctx = self._ctx
        try:
            banner_callback()
            try:
                ctx.session.start()
            except SchemaMissingError as e:
                self._view.write_fatal(str(e))
                raise
            except RuntimeError as e:
                self._view.write_fatal(f"Session start failed: {e}")
                raise
            except sqlite3.Error as e:
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
            self._view.write_fatal(str(e))
            raise
        finally:
            if persister_callback is not None:
                result = persister_callback()
                if asyncio.iscoroutine(result):
                    await result

    def _abort_input(self) -> None:
        """Signal end-of-turn display and clear the tracked input task."""
        self._view.write_turn_end()
        self._input_coro = None

    def _log_graceful_shutdown_timeout(self) -> None:
        """Log a warning when graceful shutdown times out."""
        self._view.write_warning(
            f"Graceful shutdown timed out after {self._GRACEFUL_TIMEOUT_S}s"
        )

    async def _read_input(self, loop: asyncio.AbstractEventLoop) -> str | None:
        """Read a single input line, handling EOF/keyboard interrupt and multiline continuation."""
        shutdown_event = self._shutdown_event
        if shutdown_event is not None:

            async def _input_task() -> str:
                """Read one line of user input via executor."""
                return await loop.run_in_executor(None, lambda: input("> "))

            input_coro = asyncio.ensure_future(_input_task())
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
            for t in pending:
                t.cancel()
            if shutdown_done or shutdown_coro in done:
                self._abort_input()
                return None
            try:
                raw = input_coro.result()
            except asyncio.CancelledError:
                # Input was cancelled by signal handler — treat as shutdown
                self._abort_input()
                return None
            except EOFError:
                self._abort_input()
                return None
            except KeyboardInterrupt:
                self._abort_input()
                return None
        else:
            try:
                raw = await loop.run_in_executor(None, lambda: input("> "))
            except (EOFError, KeyboardInterrupt):
                self._view.write_turn_end()
                return None
        line = raw.strip()
        if line.endswith("\\"):
            line = await self._view.read_multiline(loop, line)
            line = line.strip()
        return line

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
        if self._cmds is None:
            raise RuntimeError("_dispatch_line called before _init_components()")
        if self._orchestrator is None:
            raise RuntimeError("_dispatch_line called before _init_components()")
        if line.startswith("/"):
            matched = await self._cmds.dispatch(line)
            if not matched:
                self._view.write_warning(
                    f"Unknown command: {line}  (type /help for commands)"
                )
        else:
            _prev_partial = ctx.stats.stat_partial_completions
            await self._orchestrator.handle_turn(line)
            if ctx.stats.stat_partial_completions > _prev_partial:
                self._view.write_warning(
                    "Partial LLM completion stored. Use /stats to see count."
                )

    async def _repl_loop(self) -> None:
        """Process user input lines until /exit, EOF, or shutdown request."""
        ctx = self._ctx
        if self._cmds is None:
            raise RuntimeError("_repl_loop called before _init_components()")
        if self._orchestrator is None:
            raise RuntimeError("_repl_loop called before _init_components()")
        loop = asyncio.get_running_loop()
        while True:
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
            self._turn_active = True
            ctx.conv.is_processing = True
            try:
                dispatch_task = asyncio.ensure_future(self._dispatch_line(line, ctx))
                if (
                    self._shutdown_event is not None
                    and not self._shutdown_event.is_set()
                ):
                    shutdown_task = asyncio.ensure_future(self._shutdown_event.wait())
                    done, pending = await asyncio.wait(
                        {dispatch_task, shutdown_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if dispatch_task in done:
                        dispatch_task.result()  # propagate exception if any
                        continue
                    # shutdown_task completed first — cancel both tasks and exit
                    assert shutdown_task in pending or shutdown_task in done
                    if shutdown_task in pending:
                        shutdown_task.cancel()
                    if dispatch_task in pending:
                        dispatch_task.cancel()
                        try:
                            await dispatch_task
                        except asyncio.CancelledError:
                            pass
                    break
                else:
                    # _shutdown_event is None or already set — await the already-created dispatch_task
                    try:
                        await asyncio.wait_for(
                            dispatch_task,
                            timeout=self._GRACEFUL_TIMEOUT_S
                            if ctx.conv.shutdown_requested
                            or (
                                self._shutdown_event is not None
                                and self._shutdown_event.is_set()
                            )
                            else None,
                        )
                    except TimeoutError:
                        if ctx.conv.shutdown_requested or (
                            self._shutdown_event is not None
                            and self._shutdown_event.is_set()
                        ):
                            self._log_graceful_shutdown_timeout()
                            break
                        raise
            except TimeoutError:
                if ctx.conv.shutdown_requested:
                    self._log_graceful_shutdown_timeout()
                    break
                raise
            finally:
                self._turn_active = False
                ctx.conv.is_processing = False
            if ctx.conv.shutdown_requested:
                break
