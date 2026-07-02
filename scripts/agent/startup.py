"""agent/startup.py
Startup orchestration for AgentREPL.

Extracted from agent/repl.py so that AgentREPL contains only input loop,
command dispatch, and output display logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.logger import Logger
from shared.mcp_config import SecurityProfile

from agent.context import AgentContext
from agent.factory import build_agent_context, init_tracer
from agent.orchestrator import Orchestrator
from agent.repl_health import (
    audit_security_defaults,
    check_readiness,
    check_routing_drift,
    check_tool_definitions_startup,
    check_workflow_definition,
)
from agent.services.rag_maintenance_service import RagMaintenanceService
from agent.workflow.state_store import StateStore

if TYPE_CHECKING:
    from agent.cli_view import CLIView
    from agent.commands.registry import CommandRegistry

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class StartupOrchestrator:
    """Runs the full agent startup sequence before the REPL input loop begins.

    Handles: component init, MCP server spawning, service health checks,
    security audit, tool definition validation, and initial system prompt setup.
    """

    def __init__(self, ctx: AgentContext, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None

    async def run(self) -> tuple[CommandRegistry, Orchestrator]:
        """Execute full startup sequence; return (cmds, orchestrator)."""
        self._initialize()
        await self._start_servers()
        await self._check_services()
        await self._recover_pending_approvals()
        await self._setup_prompt()
        if self._cmds is None or self._orchestrator is None:
            raise RuntimeError(
                "StartupOrchestrator.run() failed to initialize cmds/orchestrator"
            )
        return self._cmds, self._orchestrator

    def _initialize(self) -> None:
        """Setup readline, wire DI, init CommandRegistry and Orchestrator."""
        ctx = self._ctx
        self._view.setup_readline()
        build_agent_context(ctx, self._view)
        ctx.conv.llm_url = ctx.cfg.llm.llm_url
        self._init_command_registry()
        self._check_workflow_definition()
        self._init_orchestrator()

    def _init_command_registry(self) -> None:
        from agent.commands.registry import (
            CommandRegistry,  # noqa: PLC0415 — lazy: deferred to avoid circular import at module level
        )

        self._cmds = CommandRegistry(self._ctx)

    def _init_orchestrator(self) -> None:
        if self._cmds is None:
            raise RuntimeError("_init_orchestrator requires _cmds to be set first")
        tracer = init_tracer(self._ctx)
        self._orchestrator = Orchestrator(
            self._ctx,
            on_turn_start=self._view.write_turn_start,
            on_turn_end=self._view.write_turn_end,
            on_error=self._view.write_llm_error,
            on_first_turn=self._cmds._generate_session_title,
            tracer=tracer,
            workflow_mode=self._ctx.cfg.workflow_mode,
        )

    async def _start_servers(self) -> None:
        """Spawn subprocesses for HTTP subprocess MCP servers.

        Handles:
        - http  + startup_mode='subprocess': start HTTP server subprocess, poll /health
        Ondemand servers are excluded; they start on first tool call via ensure_ready().
        """
        ctx = self._ctx
        if ctx.services_required.tools is None:
            raise RuntimeError("tools service not initialized")
        if ctx.services_required.lifecycle is None:
            raise RuntimeError("lifecycle service not initialized")
        for key, cfg in ctx.cfg.mcp.mcp_servers.items():
            if cfg.startup_mode == "subprocess" and cfg.transport == "http":
                try:
                    await ctx.services_required.lifecycle.start_http_subprocess(
                        key, cfg
                    )
                except (OSError, RuntimeError) as e:
                    logger.error(
                        "Failed to start HTTP subprocess MCP server %r: %s",
                        key,
                        e,
                    )
                    self._view.write_warning(
                        f"[non-fatal] HTTP subprocess MCP server {key!r} failed to start: {e}"
                    )

    def _check_workflow_definition(self) -> None:
        """Preflight check for workflow definition file before Orchestrator.__init__()."""
        ctx = self._ctx
        try:
            warnings = check_workflow_definition(ctx.cfg.workflow_mode)
            for msg in warnings:
                self._view.write_warning(msg)
        except RuntimeError as e:
            logger.error("Workflow preflight check failed: %s", e)
            raise

    def _check_embedding_dimensions(self) -> None:
        """Verify embedding dimension consistency between memory config and db config."""
        from db.config import build_db_config  # noqa: PLC0415 — lazy

        ctx = self._ctx
        memory_dim = ctx.cfg.memory.memory_embed_dim
        db_dim = build_db_config().embedding_dims
        if memory_dim != db_dim:
            logger.error(
                "Embedding dimension mismatch: memory=%d, db=%d. "
                "Fix config/memory.toml or db/config.py.",
                memory_dim,
                db_dim,
            )
            raise RuntimeError(
                f"Embedding dimension mismatch: memory={memory_dim}, db={db_dim}"
            )
        logger.info("Embedding dimensions consistent: %d", memory_dim)

    async def _check_services(self) -> None:
        """Probe LLM/Embed health, validate tool definitions, and audit security defaults."""
        ctx = self._ctx
        production_mode = ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
        audit_security_defaults(ctx, production_mode=production_mode)
        self._check_embedding_dimensions()
        result = await check_readiness(ctx, production_mode=production_mode)
        for msg in result.warning_messages():
            self._view.write_warning(msg)
        tool_result = await check_tool_definitions_startup(ctx)
        for msg in tool_result.warning_messages():
            self._view.write_warning(f"[non-fatal] {msg}")  # non-fatal in local profile
        for msg in check_routing_drift(ctx):
            self._view.write_warning(f"[non-fatal] {msg}")  # non-fatal in local profile
        try:
            rag_check = RagMaintenanceService().consistency()
            if rag_check.is_consistent:
                logger.info("RAG consistency: OK")
            else:
                for issue in rag_check.issues:
                    self._view.write_warning(
                        f"[non-fatal] [RAG] Consistency issue: {issue}"
                    )  # non-fatal in local profile
        except Exception as e:  # noqa: BLE001 — skip if rag.sqlite absent or unreadable
            logger.debug("RAG consistency check skipped: %s", e)

    async def _recover_pending_approvals(self) -> None:
        """Restore workflow approval-pending state from a previous session."""
        ctx = self._ctx
        if ctx.workflow is None:
            return
        store = StateStore()
        try:
            result = store.find_latest_pending_approval()
        finally:
            store.close()
        if result is None:
            return
        task_id, approval = result
        ctx.workflow.approval_pending = True
        ctx.turn.pending_approval_id = approval.approval_id
        logger.warning(
            "Recovered pending approval: task=%s approval=%s reason=%s",
            task_id,
            approval.approval_id,
            approval.reason or "none",
        )
        self._view.write_warning(
            f"[workflow] Pending approval from previous session — "
            f"task={task_id} approval={approval.approval_id} reason={approval.reason or 'none'}.\n"
            f"Use /approve [reason] or /reject [reason]."
        )

    async def _setup_prompt(self) -> None:
        """Inject semantic memories into the initial system prompt."""
        ctx = self._ctx
        initial_prompt = ctx.cfg.tool.system_prompts.get(
            ctx.conv.system_prompt_name,
            ctx.cfg.tool.system_prompt_tool,
        )
        if ctx.services_required.memory is not None:
            memory_snippets = ctx.services_required.memory.on_session_start(
                ctx.session.session_id,
            )
            if memory_snippets:
                memory_block = "\n\n[Relevant memories]\n" + "\n".join(
                    f"- {snippet.text}" for snippet in memory_snippets
                )
                initial_prompt = initial_prompt + memory_block
        ctx.conv.system_prompt_content = initial_prompt
        ctx.conv.history = [{"role": "system", "content": initial_prompt}]
