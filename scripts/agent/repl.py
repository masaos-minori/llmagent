#!/usr/bin/env python3
"""scripts/agent/repl.py

AgentREPL — thin composition facade over extracted REPL concern classes.

Delegates REPL input/dispatch to ReplInputLoop, session persistence to
SessionPersister, WAL operations to WalCheckpointManager, resource shutdown
to ResourceShutdownCoordinator, startup display to StartupBanner, and signal
handling to SignalHandler.

Architecture (dependency injection via AgentContext):
  AgentContext   — shared mutable state container (agent/context.py)
  CLIView        — readline, multiline input display (agent/cli_view.py)
  LLMClient      — HTTP retry, payload build, SSE stream (shared/llm_client.py)
  ToolExecutor   — MCP routing, error handling, TTL cache (shared/tool_executor.py)
  HistoryManager — character counting, LLM-based compression (agent/history.py)
  CommandRegistry — slash-command dispatch (agent/commands/registry.py)
  Orchestrator   — per-turn task control: LLM loop, tool dispatch (agent/orchestrator.py)
  AgentConfig    — mutable runtime config dataclass (agent/config.py)

Imported by agent.py as the entry point.
Slash-command handlers live in agent/commands/registry.CommandRegistry.
Turn-level orchestration (LLM loop, tool dispatch) lives in agent/orchestrator.py.
"""

import asyncio
import subprocess
from functools import cached_property

from agent.cli_view import CLIView
from agent.context import AgentContext
from agent.diagnostic_store import DiagnosticStore
from agent.output_tags import OutputTag
from agent.repl_input_loop import ReplInputLoop
from agent.resource_shutdown_coordinator import ResourceShutdownCoordinator
from agent.session_persister import SessionPersister
from agent.signal_handler import SignalHandler
from agent.startup import StartupOrchestrator
from agent.startup_banner import StartupBanner
from agent.wal_checkpoint_manager import WalCheckpointManager

_REPL_RESERVED_COMMANDS = frozenset(["/exit"])


def builtin_command_names() -> frozenset[str]:
    """Return names of all built-in commands from _COMMANDS."""
    from agent.commands.command_defs_list import _COMMANDS

    return frozenset(cmd.name for cmd in _COMMANDS)


def reserved_repl_command_names() -> frozenset[str]:
    """Return names of REPL-reserved commands."""
    return _REPL_RESERVED_COMMANDS


def completion_command_names() -> frozenset[str]:
    """Return all commands available for tab completion."""
    return builtin_command_names() | reserved_repl_command_names()


class AgentREPL:
    """Thin composition facade over extracted REPL concern classes.

    Delegates REPL input/dispatch to ReplInputLoop, session persistence to
    SessionPersister, WAL operations to WalCheckpointManager, resource shutdown
    to ResourceShutdownCoordinator, startup display to StartupBanner, and signal
    handling to SignalHandler.
    """

    @cached_property
    def SLASH_COMMANDS(self) -> frozenset[str]:
        """Tab completion candidates derived from _COMMANDS + REPL-reserved commands."""
        return completion_command_names()

    def __init__(self) -> None:
        """Initialize REPL agent with empty context and view."""
        self._ctx = AgentContext()
        self._view = CLIView(list(self.SLASH_COMMANDS))
        self._diagnostic_store = DiagnosticStore()
        self._turn_active: bool = False
        self._shutdown_event: asyncio.Event | None = None
        self._input_coro: asyncio.Task[str] | None = None
        # Wire extracted components via DI
        self._input_loop = ReplInputLoop(self._ctx, self._view, self._shutdown_event)
        self._persister = SessionPersister(
            self._ctx, self._diagnostic_store, self._view
        )
        self._wal = WalCheckpointManager(self._ctx)
        self._shutdown = ResourceShutdownCoordinator(self._ctx, self._view, self._wal)
        self._banner = StartupBanner(self._ctx, self._view)
        self._signal = SignalHandler(self._ctx, self._shutdown_event)

    @property
    def _prompt(self) -> str:
        """REPL input prompt string."""
        return "> "

    @property
    def _n_tools(self) -> int:
        """Number of tools available at runtime (excludes unavailable/degraded servers)."""
        rt = self._ctx.services_required.runtime_tools
        return len(rt.all_tools()) if rt else 0

    async def _persist_after_loop(self) -> None:
        """Persist session data after the REPL loop ends."""
        await self._persister.persist_session_memories()
        await self._persister.persist_session_diagnostics()

    async def run(self) -> None:
        """Start the interactive REPL."""
        loop = asyncio.get_running_loop()
        self._shutdown_event = asyncio.Event()
        self._signal.set_shutdown_event(self._shutdown_event)

        # Register signal handlers
        self._signal.register(loop)

        # Run startup orchestration
        startup = StartupOrchestrator(
            self._ctx, self._view, shutdown_event=self._shutdown_event
        )
        _spawned_subprocesses: list[subprocess.Popen] = []
        try:
            self._cmds, self._orchestrator, _spawned_subprocesses = await startup.run()
        except Exception as e:
            self._view.write_fatal(f"Startup failed: {e}")
            all_procs = _spawned_subprocesses
            if hasattr(startup, "_spawned_subprocesses"):
                all_procs = list(all_procs) + list(startup._spawned_subprocesses)
            for proc in all_procs:
                if proc.poll() is None:
                    proc.terminate()
            raise
        finally:
            await self._shutdown.close_resources()

        # Show memory disabled warning immediately after startup if applicable
        if self._ctx.conv.memory_disabled and not self._ctx.conv.memory_warning_shown:
            self._ctx.conv.memory_warning_shown = True
            self._view.write_warning(
                f"{OutputTag.NON_FATAL} Memory is disabled for this session."
            )

        # Delegate to input loop
        await self._input_loop.run(
            lambda: self._banner.print_startup_banner(),
            self._persist_after_loop,
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the interactive REPL."""
    asyncio.run(AgentREPL().run())


if __name__ == "__main__":
    main()
