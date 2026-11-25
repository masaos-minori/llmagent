"""scripts/agent/startup.py

Startup orchestration for AgentREPL.

ADR-004 Decision #14: Safety/integrity failures route through unconditional
FATAL paths in the validation pipeline; environment name must not weaken them.
"""

from __future__ import annotations

import asyncio
import subprocess
from collections.abc import Awaitable
from typing import TYPE_CHECKING, TypeVar

from shared.logger import Logger

from agent.context import AgentContext
from agent.orchestrator import Orchestrator
from agent.shared.health_models import StartupCheckStatus, StartupValidationResult
from agent.startup_component_init import ComponentInitializer
from agent.startup_mcp_starter import McpServerStarter
from agent.startup_prompt_setup import PromptSetup
from agent.startup_reporter import ReadinessReporter
from agent.startup_validation import StartupValidationPipeline

T = TypeVar("T")


class StartupInterrupted(BaseException):
    """Raised when a SIGINT/SIGTERM shutdown request interrupts the startup sequence."""


if TYPE_CHECKING:
    from agent.cli_view import CLIView
    from agent.commands.registry import CommandRegistry
    from agent.shutdown_budget import ShutdownBudget

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class StartupOrchestrator:
    """Runs the full agent startup sequence before the REPL input loop begins.

    Handles: component init, MCP server spawning, service health checks,
    startup validation (readiness and Security Posture), tool definition
    validation, and initial system prompt setup.
    """

    def __init__(
        self,
        ctx: AgentContext,
        view: CLIView,
        shutdown_event: asyncio.Event | None = None,
        *,
        budget: ShutdownBudget | None = None,
    ) -> None:
        """Initialize with agent context, REPL view, an optional shutdown event, and the
        optional shutdown budget that bounds the rollback of started servers.
        """
        self._ctx = ctx
        self._view = view
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None
        self._shutdown_event = shutdown_event
        self._budget = budget
        self._mcp_starter = McpServerStarter(ctx, view, shutdown_event)
        self._validation_pipeline = StartupValidationPipeline(ctx, view)
        self._reporter = ReadinessReporter(ctx, view)
        self._prompt_setup = PromptSetup(ctx, view)

    async def run(self) -> tuple[CommandRegistry, Orchestrator]:
        """Execute full startup sequence; return (cmds, orchestrator)."""
        self._cmds, self._orchestrator = await ComponentInitializer(
            self._ctx, self._view
        ).initialize()
        self._check_config()
        try:
            self._raise_if_shutdown_requested("at startup")
            await self._start_servers()
            self._raise_if_shutdown_requested("after MCP subprocess start")
            await self._verify_mcp_health()
            self._raise_if_shutdown_requested("after MCP health validation")
            await self._run_stage("service validation", self._check_services())
            self._raise_if_shutdown_requested("after service validation")
            await self._run_stage("prompt setup", self._setup_prompt())
            self._raise_if_shutdown_requested("after prompt setup")
        except StartupInterrupted:
            await self._rollback_servers("startup interrupted")
            raise
        except Exception as setup_err:
            await self._rollback_servers(f"{type(setup_err).__name__}: {setup_err}")
            raise setup_err
        if self._cmds is None or self._orchestrator is None:
            raise RuntimeError(
                "StartupOrchestrator.run() failed to initialize cmds/orchestrator"
            )
        return self._cmds, self._orchestrator

    def _raise_if_shutdown_requested(self, boundary: str) -> None:
        """Abort the startup sequence at a stage boundary when a shutdown was requested."""
        if self._shutdown_event is not None and self._shutdown_event.is_set():
            raise StartupInterrupted(f"shutdown requested {boundary}")

    async def _run_stage(self, name: str, coro: Awaitable[T]) -> T:
        """Await a startup stage, cancelling it if the shutdown event fires first.

        When the event wins, the stage task is cancelled and awaited so its cleanup
        runs, and StartupInterrupted names the stage. Stage exceptions are propagated
        as raised; a shutdown seen at the same moment is honored at the next boundary
        check. With no event configured the stage is simply awaited.
        """
        if self._shutdown_event is None:
            return await coro
        stage_task = asyncio.ensure_future(coro)
        wait_task = asyncio.ensure_future(self._shutdown_event.wait())
        try:
            done, _ = await asyncio.wait(
                {stage_task, wait_task}, return_when=asyncio.FIRST_COMPLETED
            )
        except asyncio.CancelledError:
            # run() itself was cancelled: stop both tasks before propagating.
            stage_task.cancel()
            wait_task.cancel()
            await asyncio.gather(stage_task, wait_task, return_exceptions=True)
            raise
        if not wait_task.done():
            wait_task.cancel()
        if stage_task in done:
            return stage_task.result()
        stage_task.cancel()
        try:
            await stage_task
        except asyncio.CancelledError:
            pass
        raise StartupInterrupted(f"shutdown requested during {name}")

    async def _rollback_servers(self, cause: str) -> None:
        """Stop the servers started so far; report anything that could not be stopped.

        Termination is owned by lifecycle.shutdown_all(), bounded here by the shutdown
        budget when the REPL supplied one, so a rollback cannot run past the deadline
        the shutdown request already set (REQ-010). A failure here is reported on the
        console and never replaces the startup error being propagated.
        """
        try:
            unconfirmed = await self._ctx.services_required.lifecycle.shutdown_all(
                budget=self._budget
            )
        except Exception as shutdown_err:  # noqa: BLE001 — rollback shutdown failure must not mask the original startup error
            logger.error(
                "CRITICAL: Startup rollback FAILED — subprocesses may be orphaned: %s",
                shutdown_err,
            )
            self._view.write_fatal(
                "CRITICAL: Startup rollback FAILED — subprocesses may be orphaned "
                f"(after {cause}; rollback error {type(shutdown_err).__name__}: {shutdown_err})"
            )
            return
        if unconfirmed:
            keys = ", ".join(f"{key} ({outcome})" for key, outcome in unconfirmed)
            self._view.write_fatal(
                "CRITICAL: Startup rollback could not confirm these servers stopped "
                f"and they may be orphaned: {keys} (after {cause})"
            )

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

    def _check_config(self) -> None:
        """Run the config-only validation stage before any MCP subprocess is spawned."""
        self._finish_validation_stage(
            self._validation_pipeline.check_config(), report_readiness=False
        )

    async def _check_services(self) -> None:
        """Probe LLM/Embed health, validate MCP readiness and Security Posture, validate tool definitions."""
        pipeline = await self._validation_pipeline.check_services()
        self._finish_validation_stage(pipeline, report_readiness=True)

    def _finish_validation_stage(
        self, pipeline: StartupValidationResult, *, report_readiness: bool
    ) -> None:
        """Display a stage's outcomes, optionally report readiness, and abort on a FATAL."""
        self._display_pipeline_results(pipeline)
        if report_readiness:
            self._report_readiness(pipeline)

        if pipeline.has_fatal:
            fatal_parts: list[str] = []
            for o in pipeline.outcomes:
                if o.status == StartupCheckStatus.FATAL:
                    part = o.message
                    if o.remediation:
                        part += f"\nRemediation: {o.remediation}"
                    fatal_parts.append(part)
            fatal_str = "\n\n".join(fatal_parts)
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

    async def _setup_prompt(self) -> None:
        """Inject semantic memories into the initial system prompt."""
        await self._prompt_setup.setup_prompt()
