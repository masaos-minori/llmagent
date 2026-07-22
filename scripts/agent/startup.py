"""agent/startup.py

Startup orchestration for AgentREPL.

Extracted from agent/repl.py so that AgentREPL contains only input loop,
command dispatch, and output display logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.logger import Logger
from shared.mcp_config import SecurityProfile, StartupMode, TransportType

from agent.context import AgentContext
from agent.factory import build_agent_context, init_tracer
from agent.orchestrator import Orchestrator
from agent.output_tags import OutputTag
from agent.repl_health import (
    audit_security_defaults,
    check_readiness,
    check_routing_drift,
    check_routing_safety_tiers,
    check_workflow_definition,
)
from agent.services.mcp_tool_discovery import McpToolDiscoveryService
from agent.services.rag_maintenance_service import RagMaintenanceService
from agent.shared.health_models import StartupCheckStatus, StartupValidationResult
from agent.workflow.approval_ops import find_all_pending_approvals
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
        """Initialize with agent context and REPL view for output."""
        self._ctx = ctx
        self._view = view
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None

    async def run(self) -> tuple[CommandRegistry, Orchestrator]:
        """Execute full startup sequence; return (cmds, orchestrator)."""
        self._initialize()
        _servers_started = False
        try:
            await self._start_servers()
            _servers_started = True
            await self._check_services()
            await self._recover_pending_approvals()
            await self._setup_prompt()
        except Exception as setup_err:
            if _servers_started:
                try:
                    await self._ctx.services_required.lifecycle.shutdown_all()
                except Exception as shutdown_err:
                    logger.error(
                        "CRITICAL: Startup rollback FAILED — subprocesses may be orphaned: %s",
                        shutdown_err,
                    )
            raise setup_err
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
        from shared.llm_client import build_llm_url

        ctx.conv.llm_url = build_llm_url(ctx.cfg.llm.llm_url)
        self._init_command_registry()
        self._check_workflow_definition()
        self._check_workflow_schema()
        self._init_orchestrator()

    def _init_command_registry(self) -> None:
        """Build the command registry from the context."""
        from agent.commands.registry import (
            CommandRegistry,  # noqa: PLC0415 — lazy: deferred to avoid circular import at module level
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

    async def _start_servers(self) -> None:
        """Spawn subprocesses for HTTP subprocess MCP servers.

        Handles:
        - http  + startup_mode='subprocess': start HTTP server subprocess, poll /health
        - Persistent-mode servers: externally managed, excluded here.
        - Subprocess-mode servers with startup_mode='subprocess': started at agent init.
        - Other subprocess-mode servers: start on first tool call via ensure_ready().
        """
        ctx = self._ctx
        if ctx.services_required.tools is None:
            raise RuntimeError("tools service not initialized")
        if ctx.services_required.lifecycle is None:
            raise RuntimeError("lifecycle service not initialized")
        for key, cfg in ctx.cfg.mcp.mcp_servers.items():
            if (
                cfg.startup_mode == StartupMode.SUBPROCESS
                and cfg.transport == TransportType.HTTP
            ):
                try:
                    await ctx.services_required.lifecycle.start_http_subprocess(
                        key, cfg
                    )
                except (OSError, RuntimeError) as e:
                    if ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION:
                        msg = f"{OutputTag.FATAL} MCP subprocess {key!r} failed to start: {e}"
                        logger.error(msg)
                        raise RuntimeError(msg) from e
                    logger.error(
                        "Failed to start HTTP subprocess MCP server %r: %s",
                        key,
                        e,
                    )
                    self._view.write_warning(
                        f"{OutputTag.NON_FATAL} HTTP subprocess MCP server {key!r} failed to start: {e}"
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
        from agent.repl_health import check_workflow_schema  # noqa: PLC0415

        result = check_workflow_schema()
        if not result.valid:
            logger.error("Workflow schema preflight failed: %s", result.error)
            raise RuntimeError(result.error)

    def _check_embedding_dimensions(self) -> None:
        """Verify embedding dimension consistency between memory config and db config."""
        from db.config import build_db_config  # noqa: PLC0415 — lazy

        ctx = self._ctx
        memory_dim = ctx.cfg.memory.memory_embed_dim
        db_dim = build_db_config().embedding_dims
        if memory_dim != db_dim:
            logger.error(
                "Embedding dimension mismatch: memory=%d, db=%d. Fix config/memory.toml or db/config.py.",
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
        pipeline = StartupValidationResult()

        # 1. Security audit
        try:
            warnings = audit_security_defaults(ctx, production_mode=production_mode)
            for msg in warnings:
                pipeline.add_warning("security_audit", msg)
            pipeline.add_ok("security_audit")
        except RuntimeError as exc:
            pipeline.add_fatal(
                "security_audit",
                str(exc),
                remediation="Fix MCP server auth_token or sandbox config.",
            )

        # 2. Embedding dimensions
        try:
            self._check_embedding_dimensions()
            pipeline.add_ok("embedding_dimensions")
        except RuntimeError as exc:
            pipeline.add_fatal("embedding_dimensions", str(exc))

        # 3. Service readiness
        try:
            result = await check_readiness(ctx, production_mode=production_mode)
            for msg in result.warning_messages():
                pipeline.add_warning("readiness", msg)
            for msg in result.error_messages():
                pipeline.add_fatal("readiness", msg)
            if not result.has_issues:
                pipeline.add_ok("readiness")
        except Exception as exc:  # noqa: BLE001
            pipeline.add_fatal("readiness", f"Readiness check failed: {exc}")

        # 4. MCP tool discovery and validation (consolidated)
        try:
            discovery = await McpToolDiscoveryService(ctx).discover_all()
            ctx.services_required.runtime_tools = discovery.registry
            # Wire RuntimeToolRegistry into ToolExecutor routing resolver.
            if discovery.registry is not None:
                ctx.services_required.tools.set_runtime_registry(discovery.registry)
            for outcome in discovery.findings:
                if outcome.status == StartupCheckStatus.FATAL:
                    pipeline.add_fatal("mcp_tool_discovery", outcome.message)
                else:
                    pipeline.add_warning("mcp_tool_discovery", outcome.message)
            for key in discovery.unreachable:
                pipeline.add_warning(
                    "mcp_tool_discovery", f"{key}: unreachable during discovery"
                )
            if not discovery.findings and not discovery.unreachable:
                pipeline.add_ok("mcp_tool_discovery")
        except Exception as exc:  # noqa: BLE001
            msg = f"MCP tool discovery failed - ALL tool calls will fail this session: {exc}"
            if production_mode:
                pipeline.add_fatal(
                    "mcp_tool_discovery",
                    msg,
                    remediation="Investigate MCP server connectivity/discovery failure before restarting.",
                )
            else:
                pipeline.add_skipped("mcp_tool_discovery", msg)

        # 5. Routing drift (static)
        try:
            for msg in check_routing_drift(
                ctx, strict=ctx.cfg.tool.routing_drift_strict
            ):
                pipeline.add_warning("routing_drift", msg)
        except RuntimeError as exc:
            pipeline.add_fatal("routing_drift", str(exc))
        except Exception as exc:  # noqa: BLE001
            pipeline.add_warning("routing_drift", f"Routing drift check failed: {exc}")

        # 5b. Routing safety tiers
        try:
            for msg in check_routing_safety_tiers(ctx):
                pipeline.add_warning("routing_safety_tiers", msg)
        except Exception as exc:  # noqa: BLE001
            pipeline.add_warning(
                "routing_safety_tiers", f"Routing safety tier check failed: {exc}"
            )

        # 6. RAG consistency
        try:
            rag_check = RagMaintenanceService().consistency()
            if rag_check.is_consistent:
                pipeline.add_ok("rag_consistency")
            else:
                for issue in rag_check.issues:
                    pipeline.add_warning(
                        "rag_consistency", f"[RAG] Consistency issue: {issue}"
                    )
        except Exception:  # noqa: BLE001
            pipeline.add_skipped("rag_consistency", "RAG consistency check skipped")

        self._display_pipeline_results(pipeline)

        if pipeline.has_fatal:
            fatal_str = "; ".join(pipeline.fatal_messages())
            logger.error(
                "FATAL pipeline outcomes: %s",
                [(o.source, o.status, o.message) for o in pipeline.outcomes],
            )
            raise RuntimeError(f"Startup validation failed: {fatal_str}")

    def _display_pipeline_results(self, pipeline: StartupValidationResult) -> None:
        """Display startup validation warnings and fatal errors via the CLI view."""
        for outcome in pipeline.outcomes:
            if outcome.status == StartupCheckStatus.WARNING:
                self._view.write_warning(f"{OutputTag.NON_FATAL} {outcome.message}")
            elif outcome.status == StartupCheckStatus.FATAL:
                self._view.write_fatal(outcome.message)
                if outcome.remediation:
                    self._view.write_fatal(f"  Remediation: {outcome.remediation}")
            elif outcome.status == StartupCheckStatus.SKIPPED:
                self._view.write_warning(f"{OutputTag.SKIPPED} {outcome.message}")

    async def _recover_pending_approvals(self) -> None:
        """Restore workflow approval-pending state from a previous session."""
        ctx = self._ctx
        if ctx.workflow is None:
            return
        store = StateStore()
        try:
            results = find_all_pending_approvals(store.get_connection())
        finally:
            store.close()
        if not results:
            return
        # Recover the most recent pending approval first
        task_id, approval = results[-1]
        ctx.workflow.approval_pending = True
        ctx.turn.pending_approval_id = approval.approval_id
        ctx.turn.pending_approval_task_id = task_id
        logger.warning(
            "Recovered %d pending approval(s); showing last: task=%s approval=%s reason=%s",
            len(results),
            task_id,
            approval.approval_id,
            approval.reason or "none",
        )
        self._view.write_warning(
            f"{OutputTag.WORKFLOW} Pending approval from previous session — "
            f"{len(results)} pending approval(s); last: task={task_id} approval={approval.approval_id} reason={approval.reason or 'none'}.\n"
            f"Use /approve {approval.approval_id} [reason] or /reject {approval.approval_id} [reason]."
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
                max_snippets = ctx.cfg.agent_memory_max_startup_snippets
                if len(memory_snippets) > max_snippets:
                    logger.warning(
                        "Startup: truncating %d memory snippets to %d for %r",
                        len(memory_snippets),
                        max_snippets,
                        ctx.session.session_id,
                    )
                    memory_snippets = memory_snippets[:max_snippets]
                memory_block = "\n\n[Relevant memories]\n" + "\n".join(
                    f"- {snippet.text}" for snippet in memory_snippets
                )
                initial_prompt = initial_prompt + memory_block
        ctx.conv.system_prompt_content = initial_prompt
        ctx.conv.history = [{"role": "system", "content": initial_prompt}]
