"""scripts/agent/startup_component_init.py

Component initializer: DI wiring, command registry, orchestrator, and
workflow preflight checks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.logger import Logger

from agent.context import AgentContext
from agent.factory import build_agent_context, init_tracer
from agent.orchestrator import Orchestrator
from agent.services.workflow_schema import (
    check_workflow_definition,
    check_workflow_schema,
)

if TYPE_CHECKING:
    import httpx

    from agent.cli_view import CLIView
    from agent.commands.registry import CommandRegistry

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class ComponentInitializer:
    """Owns DI wiring, command registry init, orchestrator construction, and workflow preflight."""

    def __init__(self, ctx: AgentContext, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None
        self._exposed_http: httpx.AsyncClient | None = None

    async def initialize(self) -> tuple[CommandRegistry, Orchestrator]:
        """Run full component initialization sequence.

        Returns (cmds, orchestrator) after all components are wired. On a failure
        before ctx.services is assigned, closes the httpx client exposed by the
        factory so it is not leaked, then re-raises the original exception
        unchanged (including BaseException subclasses such as StartupInterrupted).
        """
        try:
            self._initialize()
        except BaseException:
            await self._cleanup_on_failure()
            raise
        if self._cmds is None or self._orchestrator is None:
            raise RuntimeError(
                "ComponentInitializer failed to initialize cmds/orchestrator"
            )
        return self._cmds, self._orchestrator

    def _initialize(self) -> None:
        """Setup readline, wire DI, init CommandRegistry and Orchestrator."""
        ctx = self._ctx
        self._view.setup_readline()
        build_agent_context(ctx, self._view, on_client_created=self._on_client_created)
        from shared.llm_client import build_llm_url

        ctx.conv.llm_url = build_llm_url(ctx.cfg.llm.llm_url)
        self._init_command_registry()
        self._check_workflow_definition()
        self._check_workflow_schema()
        self._init_orchestrator()

    def _on_client_created(self, client: httpx.AsyncClient) -> None:
        """Remember the client the factory exposes before ctx.services is set.

        Captured so the leaked-window client can be closed if initialization
        fails before ctx.services is assigned.
        """
        self._exposed_http = client

    async def _cleanup_on_failure(self) -> None:
        """Close the exposed client when a startup failure leaks it.

        Only closes when ctx.services was never assigned (the leaked window) and
        a client was captured; a second cancellation propagates instead of being
        swallowed.
        """
        if self._ctx.services is not None or self._exposed_http is None:
            return
        await self._close_exposed_client(self._exposed_http)

    async def _close_exposed_client(self, client: httpx.AsyncClient) -> None:
        """Close the client exposed during a failed startup initialization.

        An aclose() failure is logged and contained; it never replaces the
        original startup-failure exception that triggered this cleanup.
        """
        try:
            await client.aclose()
        except Exception:  # noqa: BLE001 — an aclose() failure during startup-failure cleanup must never mask the original exception (REQ-002); a second cancellation propagates instead
            logger.warning(
                "Failed to close the httpx client exposed during a failed "
                "startup initialization",
                exc_info=True,
            )

    def _init_command_registry(self) -> None:
        """Build the command registry from the context."""
        from agent.commands.registry import (
            CommandRegistry,  # lazy: deferred to avoid circular import at module level
        )

        self._cmds = CommandRegistry(self._ctx)

    def _init_orchestrator(self) -> None:
        """Construct the Orchestrator with command registry, view, and tracing."""
        if self._cmds is None:
            raise RuntimeError("_init_orchestrator requires _cmds to be set first")
        tracer = init_tracer(self._ctx)
        self._orchestrator = Orchestrator(
            self._ctx,
            on_turn_start=self._view.write_turn_start,
            on_turn_end=self._view.write_turn_end,
            on_error=self._view.write_llm_error,
            on_first_turn=self._cmds._generate_session_title,
            on_llm_wait_start=self._view.start_spinner,
            on_llm_wait_end=self._view.stop_spinner,
            tracer=tracer,
        )

    def _check_workflow_definition(self) -> None:
        """Preflight check for workflow definition file before Orchestrator.__init__()."""
        try:
            check_workflow_definition()
        except RuntimeError as e:
            logger.error("Workflow preflight check failed: %s", e)
            raise

    def _check_workflow_schema(self) -> None:
        """Preflight check for workflow DB schema before Orchestrator.__init__()."""
        result = check_workflow_schema()
        if not result.valid:
            logger.error("Workflow schema preflight failed: %s", result.error)
            raise RuntimeError(result.error)
