"""scripts/agent/startup.py

Startup orchestration for AgentREPL.

Extracted from agent/repl.py so that AgentREPL contains only input loop,
command dispatch, and output display logic.

ADR-004 Decision #14: Safety/integrity failures route through unconditional
FATAL paths in the validation pipeline; environment name must not weaken them.
"""

from __future__ import annotations

import asyncio
import sqlite3
import subprocess
from typing import TYPE_CHECKING

from shared.logger import Logger

from agent.context import AgentContext
from agent.orchestrator import Orchestrator
from agent.output_tags import OutputTag
from agent.shared.health_models import StartupValidationResult
from agent.startup_approval_recovery import ApprovalRecovery
from agent.startup_component_init import ComponentInitializer
from agent.startup_mcp_starter import McpServerStarter
from agent.startup_reporter import ReadinessReporter
from agent.startup_validation import StartupValidationPipeline


class StartupInterrupted(RuntimeError):
    """Raised when a SIGINT/SIGTERM shutdown request interrupts the startup sequence."""


if TYPE_CHECKING:
    from agent.cli_view import CLIView
    from agent.commands.registry import CommandRegistry

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class StartupOrchestrator:
    """Runs the full agent startup sequence before the REPL input loop begins.

    Handles: component init, MCP server spawning, service health checks,
    security audit, tool definition validation, and initial system prompt setup.
    """

    def __init__(
        self,
        ctx: AgentContext,
        view: CLIView,
        shutdown_event: asyncio.Event | None = None,
    ) -> None:
        """Initialize with agent context, REPL view for output, and an optional shutdown event."""
        self._ctx = ctx
        self._view = view
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None
        self._spawned_subprocesses: list[subprocess.Popen] = []
        self._shutdown_event = shutdown_event
        self._mcp_starter = McpServerStarter(ctx, view, shutdown_event)
        self._validation_pipeline = StartupValidationPipeline(ctx, view)
        self._reporter = ReadinessReporter(ctx, view)
        self._approval_recovery = ApprovalRecovery(ctx, view)

    async def run(self) -> tuple[CommandRegistry, Orchestrator, list[subprocess.Popen]]:
        """Execute full startup sequence; return (cmds, orchestrator, spawned_subprocesses)."""
        self._cmds, self._orchestrator = await ComponentInitializer(
            self._ctx, self._view
        ).initialize()
        try:
            self._spawned_subprocesses = await self._start_servers()
            await self._verify_mcp_health()
            await self._check_services()
            await self._recover_pending_approvals()
            await self._setup_prompt()
        except Exception as setup_err:
            try:
                await self._ctx.services_required.lifecycle.shutdown_all()
            except Exception as shutdown_err:  # noqa: BLE001 — rollback shutdown failure must not mask the original startup error
                logger.error(
                    "CRITICAL: Startup rollback FAILED — subprocesses may be orphaned: %s",
                    shutdown_err,
                )
            # Pass subprocess list to caller for termination
            raise setup_err
        if self._cmds is None or self._orchestrator is None:
            raise RuntimeError(
                "StartupOrchestrator.run() failed to initialize cmds/orchestrator"
            )
        return self._cmds, self._orchestrator, self._spawned_subprocesses

    async def _start_servers(self) -> list[subprocess.Popen]:
        """Spawn subprocesses for HTTP subprocess MCP servers.

        Delegates to McpServerStarter.start_servers().
        """
        return await self._mcp_starter.start_servers()

    async def _verify_mcp_health(self) -> None:
        """Verify health of all MCP subprocess servers after startup.

        Delegates to McpServerStarter.verify_health().
        """
        await self._mcp_starter.verify_health()

    async def _check_services(self) -> None:
        """Probe LLM/Embed health, validate tool definitions, and audit security defaults."""
        pipeline = await self._validation_pipeline.check_services()
        self._display_pipeline_results(pipeline)
        self._report_readiness(pipeline)

        if pipeline.has_fatal:
            fatal_str = "; ".join(pipeline.fatal_messages())
            logger.error(
                "FATAL pipeline outcomes: %s",
                [(o.source, o.status, o.message) for o in pipeline.outcomes],
            )
            raise RuntimeError(f"Startup validation failed: {fatal_str}")

    def _display_pipeline_results(self, pipeline: StartupValidationResult) -> None:
        """Display startup validation warnings and fatal errors via the CLI view."""
        self._reporter.display_pipeline_results(pipeline)

    def _report_readiness(self, pipeline: StartupValidationResult) -> None:
        """Report aggregated readiness status after startup checks complete."""
        self._reporter.report_readiness(pipeline)

    async def _recover_pending_approvals(self) -> None:
        """Restore workflow approval-pending state from a previous session."""
        await self._approval_recovery.recover()

    def _classify_memory_failure(self, exc: Exception) -> str:
        if isinstance(exc, (ConnectionError, TimeoutError)):
            return "NETWORK_TRANSIENT"
        if isinstance(exc, (sqlite3.Error, OSError)):
            return "DATABASE_OR_IO"
        return "UNKNOWN"

    async def _setup_prompt(self) -> None:
        """Inject semantic memories into the initial system prompt."""
        ctx = self._ctx
        initial_prompt = ctx.cfg.tool.system_prompts.get(
            ctx.conv.system_prompt_name,
            ctx.cfg.tool.system_prompt_tool,
        )
        if ctx.services_required.memory is not None:
            try:
                memory_snippets = ctx.services_required.memory.on_session_start(
                    ctx.session.session_id,
                )
                if memory_snippets:
                    max_snippets = ctx.cfg.agent_memory_max_startup_snippets
                    if len(memory_snippets) > max_snippets:
                        logger.warning(
                            "Startup: truncating %d memory snippets to %d for %r",
                            len(memory_snippets),
                            max_snippets,
                            ctx.session.session_id,
                        )
                        memory_snippets = memory_snippets[:max_snippets]
                    memory_block = "\n\n--- USER MEMORY ---\n" + "\n".join(
                        f"- {snippet.text}" for snippet in memory_snippets
                    )
                    initial_prompt = initial_prompt + memory_block
            except Exception as exc:  # noqa: BLE001 — memory injection failures are classified and downgraded; startup must proceed without memory
                ctx.conv.memory_disabled = True
                category = self._classify_memory_failure(exc)
                if category == "DATABASE_OR_IO":
                    logger.error(
                        "Memory injection failed during startup (DB/IO error): %s; continuing without memory",
                        exc,
                    )
                elif category == "NETWORK_TRANSIENT":
                    logger.warning(
                        "Memory injection failed during startup (network transient): %s; continuing without memory",
                        exc,
                    )
                else:
                    logger.info(
                        "Memory injection failed during startup (unknown error): %s; continuing without memory",
                        exc,
                    )
                self._view.write_warning(
                    f"{OutputTag.NON_FATAL} Memory injection failed: {exc}"
                )
        ctx.conv.system_prompt_content = initial_prompt
        await ctx.conv.replace_history([{"role": "system", "content": initial_prompt}])
