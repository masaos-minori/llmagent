"""scripts/agent/startup.py

Startup orchestration for AgentREPL.

Extracted from agent/repl.py so that AgentREPL contains only input loop,
command dispatch, and output display logic.
"""

from __future__ import annotations

import asyncio
import sqlite3
import subprocess
import time
from typing import TYPE_CHECKING

import httpx
from shared.logger import Logger
from shared.mcp_config import (
    McpServerHealthState,
    SecurityProfile,
    StartupMode,
    TransportType,
)

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
from agent.secrets_masker import _mask_secrets
from agent.services.mcp_tool_discovery import McpToolDiscoveryService
from agent.services.rag_maintenance_service import RagMaintenanceService
from agent.shared.health_models import StartupCheckStatus, StartupValidationResult
from agent.workflow.approval_ops import find_all_pending_approvals
from agent.workflow.state_store import StateStore

HEALTH_CHECK_RETRY_DELAY_SEC = 1.0


class StartupInterrupted(RuntimeError):
    """Raised when a SIGINT/SIGTERM shutdown request interrupts the startup sequence."""


if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig

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

    async def _interruptible_sleep(self, delay: float) -> bool:
        """Sleep for `delay` seconds, racing against `_shutdown_event`.

        Returns True iff the shutdown event fired before `delay` elapsed (caller
        should raise `StartupInterrupted`); returns False if the full delay elapsed
        normally or no `shutdown_event` was configured.
        """
        if self._shutdown_event is None:
            await asyncio.sleep(delay)
            return False
        sleep_task = asyncio.ensure_future(asyncio.sleep(delay))
        shutdown_task = asyncio.ensure_future(self._shutdown_event.wait())
        done, pending = await asyncio.wait(
            {sleep_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        return shutdown_task in done

    async def run(self) -> tuple[CommandRegistry, Orchestrator, list[subprocess.Popen]]:
        """Execute full startup sequence; return (cmds, orchestrator, spawned_subprocesses)."""
        self._initialize()
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

    async def _start_http_subprocess_once(
        self, key: str, cfg: McpServerConfig
    ) -> float | None:
        """Attempt one start_http_subprocess() call.

        On success, tracks the spawned process and returns the new
        last_startup_time (`time.monotonic()`); returns None when the
        lifecycle manager reports no process was started.
        """
        proc = await self._ctx.services_required.lifecycle.start_http_subprocess(
            key, cfg, shutdown_event=self._shutdown_event
        )
        if proc is not None:
            self._spawned_subprocesses.append(proc)
            return time.monotonic()
        return None

    async def _start_servers(self) -> list[subprocess.Popen]:
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
        last_startup_time = 0.0
        for key, cfg in ctx.cfg.mcp.mcp_servers.items():
            if self._shutdown_event is not None and self._shutdown_event.is_set():
                raise StartupInterrupted(
                    f"shutdown requested before starting MCP subprocess {key!r}"
                )
            if (
                cfg.startup_mode == StartupMode.SUBPROCESS
                and cfg.transport == TransportType.HTTP
            ):
                if last_startup_time > 0 and cfg.startup_stagger_delay_sec > 0:
                    elapsed = time.monotonic() - last_startup_time
                    stagger_delay = max(0.0, cfg.startup_stagger_delay_sec - elapsed)
                    if stagger_delay > 0:
                        if await self._interruptible_sleep(stagger_delay):
                            raise StartupInterrupted(
                                f"shutdown requested during startup stagger delay for {key!r}"
                            )
                        logger.info(
                            "Staggering startup by %.1fs for %r", stagger_delay, key
                        )

                try:
                    started_at = await self._start_http_subprocess_once(key, cfg)
                    if started_at is not None:
                        last_startup_time = started_at
                except (OSError, RuntimeError) as e:
                    # First attempt failure — log at INFO level
                    logger.info(
                        "First attempt failed for MCP subprocess %r: %s",
                        key,
                        _mask_secrets(str(e)),
                    )

                    # Retry after delay
                    if await self._interruptible_sleep(HEALTH_CHECK_RETRY_DELAY_SEC):
                        raise StartupInterrupted(
                            f"shutdown requested during startup retry delay for {key!r}"
                        )
                    try:
                        started_at = await self._start_http_subprocess_once(key, cfg)
                        if started_at is not None:
                            last_startup_time = started_at
                    except (OSError, RuntimeError) as retry_err:
                        # Retry attempt failure — log at WARNING level
                        if ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION:
                            msg = f"{OutputTag.FATAL} MCP subprocess {key!r} failed to start after retry: {retry_err}"
                            masked_msg = _mask_secrets(msg)
                            logger.error(masked_msg)
                            raise RuntimeError(masked_msg) from retry_err
                        logger.warning(
                            "MCP subprocess %r failed to start after retry: %s",
                            key,
                            _mask_secrets(str(retry_err)),
                        )
                        self._view.write_warning(
                            f"{OutputTag.NON_FATAL} HTTP subprocess MCP server {key!r} failed to start after retry: {retry_err}"
                        )
        return self._spawned_subprocesses

    async def _verify_mcp_health(self) -> None:
        """Verify health of all MCP subprocess servers after startup."""
        ctx = self._ctx
        if ctx.services_required.tools is None:
            raise RuntimeError("tools service not initialized")
        if ctx.services_required.lifecycle is None:
            raise RuntimeError("lifecycle service not initialized")

        subprocess_servers = [
            (key, cfg)
            for key, cfg in ctx.cfg.mcp.mcp_servers.items()
            if cfg.startup_mode == StartupMode.SUBPROCESS
            and cfg.transport == TransportType.HTTP
        ]

        for server_key, cfg in subprocess_servers:
            if self._shutdown_event is not None and self._shutdown_event.is_set():
                raise StartupInterrupted(
                    f"shutdown requested before health check for {server_key!r}"
                )
            url = cfg.url.rstrip("/") + "/health"
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url)
                    if resp.status_code != httpx.codes.OK:
                        raise RuntimeError(f"HTTP {resp.status_code}")
                    logger.info("Post-startup health check passed for %r", server_key)
            except Exception:  # noqa: BLE001 — any health-check failure (network, HTTP, timeout) triggers a retry rather than aborting startup
                # NOTE: the interruptible-sleep check is deliberately outside the
                # nested try/except below — raising StartupInterrupted from inside
                # that try would be caught by its own `except Exception as retry_err`
                # and either re-wrapped as a generic RuntimeError (production profile)
                # or swallowed as a mere warning (non-production profile), defeating
                # the prompt-interruption contract.
                if await self._interruptible_sleep(HEALTH_CHECK_RETRY_DELAY_SEC):
                    raise StartupInterrupted(
                        f"shutdown requested during post-startup health check retry delay for {server_key!r}"
                    ) from None
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        resp = await client.get(url)
                        if resp.status_code != httpx.codes.OK:
                            raise RuntimeError(f"HTTP {resp.status_code}")
                        logger.info(
                            "Post-startup health check passed for %r (after retry)",
                            server_key,
                        )
                except Exception as retry_err:
                    if ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION:
                        msg = f"{OutputTag.FATAL} MCP subprocess {server_key!r} failed post-startup health check: {retry_err}"
                        logger.error(msg)
                        raise RuntimeError(msg) from retry_err
                    logger.warning(
                        "Post-startup health check failed for %r: %s",
                        server_key,
                        retry_err,
                    )
                    self._view.write_warning(
                        f"{OutputTag.NON_FATAL} MCP subprocess {server_key!r} failed post-startup health check: {retry_err}"
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
        from agent.repl_health import (
            check_workflow_schema,  # lazy import: avoids a module-level import cycle with agent.repl_health, loaded only when the workflow schema check runs
        )

        result = check_workflow_schema()
        if not result.valid:
            logger.error("Workflow schema preflight failed: %s", result.error)
            raise RuntimeError(result.error)

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

        # 2. Service readiness
        try:
            result = await check_readiness(ctx, production_mode=production_mode)
            for msg in result.warning_messages():
                pipeline.add_warning("readiness", msg)
            for msg in result.error_messages():
                pipeline.add_fatal("readiness", msg)
            if not result.has_issues:
                pipeline.add_ok("readiness")
        except Exception as exc:  # noqa: BLE001 — an unexpected readiness-probe failure must be captured and reported as a pipeline fatal rather than crashing startup outright
            pipeline.add_fatal("readiness", f"Readiness check failed: {exc}")

        # 4. MCP tool discovery and validation (consolidated)
        try:
            discovery = await McpToolDiscoveryService(ctx).discover_all()
            ctx.services_required.runtime_tools = discovery.registry
            # Wire RuntimeToolRegistry into ToolExecutor routing resolver.
            if discovery.registry is not None:
                ctx.services_required.tools.set_runtime_registry(discovery.registry)

            if not discovery.findings and not discovery.unreachable:
                pipeline.add_ok("mcp_tool_discovery")
            else:
                for outcome in discovery.findings:
                    if outcome.status == StartupCheckStatus.FATAL:
                        pipeline.add_fatal("mcp_tool_discovery", outcome.message)
                    elif outcome.status == StartupCheckStatus.WARNING:
                        pipeline.add_warning("mcp_tool_discovery", outcome.message)
        except Exception as exc:  # noqa: BLE001 — a broad catch prevents one failing MCP server discovery from aborting the whole startup sequence
            msg = f"MCP tool discovery failed: {exc}. No MCP tools will be available this session."
            pipeline.add_fatal(
                "mcp_tool_discovery",
                msg,
                remediation="Check MCP server connectivity and configuration.",
            )

        # 5. Routing drift (static)
        try:
            for msg in check_routing_drift(
                ctx, strict=ctx.cfg.tool.routing_drift_strict
            ):
                pipeline.add_warning("routing_drift", msg)
        except RuntimeError as exc:
            pipeline.add_fatal("routing_drift", str(exc))
        except Exception as exc:  # noqa: BLE001 — unexpected routing-drift check failures are downgraded to a warning rather than allowed to abort startup
            pipeline.add_warning("routing_drift", f"Routing drift check failed: {exc}")

        # 5b. Routing safety tiers
        try:
            for msg in check_routing_safety_tiers(ctx):
                pipeline.add_warning("routing_safety_tiers", msg)
        except Exception as exc:  # noqa: BLE001 — unexpected routing-safety-tier check failures are downgraded to a warning rather than allowed to abort startup
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
        except Exception as exc:  # noqa: BLE001 — non-critical maintenance check must not abort startup
            logger.warning("RAG consistency check failed: %s", exc)
            pipeline.add_skipped(
                "rag_consistency", f"RAG consistency check skipped: {exc}"
            )

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
        for outcome in pipeline.outcomes:
            if outcome.status == StartupCheckStatus.WARNING:
                self._view.write_warning(f"{OutputTag.NON_FATAL} {outcome.message}")
            elif outcome.status == StartupCheckStatus.FATAL:
                self._view.write_fatal(outcome.message)
                if outcome.remediation:
                    self._view.write_fatal(f"  Remediation: {outcome.remediation}")
            elif outcome.status == StartupCheckStatus.SKIPPED:
                self._view.write_warning(f"{OutputTag.SKIPPED} {outcome.message}")

    def _report_readiness(self, pipeline: StartupValidationResult) -> None:
        """Report aggregated readiness status after startup checks complete."""
        mcp_ok = sum(
            1
            for o in pipeline.outcomes
            if o.source == "readiness" and o.status == StartupCheckStatus.OK
        )
        mcp_fail = sum(
            1
            for o in pipeline.outcomes
            if o.source == "readiness" and o.status == StartupCheckStatus.FATAL
        )
        mcp_skip = sum(
            1
            for o in pipeline.outcomes
            if o.source == "readiness" and o.status == StartupCheckStatus.SKIPPED
        )
        mcp_warn = sum(
            1
            for o in pipeline.outcomes
            if o.source == "readiness" and o.status == StartupCheckStatus.WARNING
        )
        rag_ok = sum(
            1
            for o in pipeline.outcomes
            if o.source == "rag_consistency" and o.status == StartupCheckStatus.OK
        )
        rag_fail = sum(
            1
            for o in pipeline.outcomes
            if o.source == "rag_consistency" and o.status == StartupCheckStatus.FATAL
        )
        rag_warn = sum(
            1
            for o in pipeline.outcomes
            if o.source == "rag_consistency" and o.status == StartupCheckStatus.WARNING
        )
        security_ok = sum(
            1
            for o in pipeline.outcomes
            if o.source == "security_audit" and o.status == StartupCheckStatus.OK
        )
        security_fail = sum(
            1
            for o in pipeline.outcomes
            if o.source == "security_audit" and o.status == StartupCheckStatus.FATAL
        )
        security_warn = sum(
            1
            for o in pipeline.outcomes
            if o.source == "security_audit" and o.status == StartupCheckStatus.WARNING
        )
        tool_disc_ok = sum(
            1
            for o in pipeline.outcomes
            if o.source == "mcp_tool_discovery" and o.status == StartupCheckStatus.OK
        )
        tool_disc_fail = sum(
            1
            for o in pipeline.outcomes
            if o.source == "mcp_tool_discovery" and o.status == StartupCheckStatus.FATAL
        )
        tool_disc_warn = sum(
            1
            for o in pipeline.outcomes
            if o.source == "mcp_tool_discovery"
            and o.status == StartupCheckStatus.WARNING
        )
        tool_disc_skip = sum(
            1
            for o in pipeline.outcomes
            if o.source == "mcp_tool_discovery"
            and o.status == StartupCheckStatus.SKIPPED
        )
        lines: list[str] = []
        lines.append("Readiness Summary:")
        lines.append(
            f"  Security audit: {'OK' if security_ok else 'FAIL'} ({security_fail} fatal, {security_warn} warnings)"
        )
        lines.append(
            f"  Service readiness: {'OK' if mcp_ok else 'FAIL'} ({mcp_fail} fatal, {mcp_warn} warnings, {mcp_skip} skipped)"
        )
        lines.append(
            f"  Tool discovery: {'OK' if tool_disc_ok else 'FAIL'} ({tool_disc_fail} fatal, {tool_disc_warn} warnings, {tool_disc_skip} skipped)"
        )
        lines.append(
            f"  RAG consistency: {'OK' if rag_ok else 'WARN'} ({rag_fail} fatal, {rag_warn} warnings)"
        )
        unreachable_count = sum(
            1
            for o in pipeline.outcomes
            if o.source == "mcp_tool_discovery" and "unreachable" in o.message.lower()
        )
        if unreachable_count > 0:
            lines.append(f"  Unreachable servers: {unreachable_count}")
        degraded_keys = []
        registry = (
            self._ctx.services_required.health_registry
            if self._ctx.services_required
            else None
        )
        if registry is not None:
            degraded_keys = [
                key
                for key in self._ctx.cfg.mcp.mcp_servers
                if registry.get_state(key) == McpServerHealthState.DEGRADED
            ]
        if degraded_keys:
            lines.append(f"  Degraded servers: {', '.join(degraded_keys)}")
        unavailable_servers: frozenset[str] = frozenset()
        runtime_tools = (
            self._ctx.services_required.runtime_tools
            if self._ctx.services_required
            else None
        )
        if runtime_tools is not None:
            unavailable_servers = runtime_tools.unavailable_servers
        if unavailable_servers:
            parts = []
            for key in sorted(unavailable_servers):
                cfg_entry = self._ctx.cfg.mcp.mcp_servers.get(key)
                policy = getattr(cfg_entry, "failure_policy", None)
                if policy is not None:
                    parts.append(f"{key} ({policy})")
                else:
                    parts.append(key)
            lines.append(f"  Excluded tools (unavailable): {', '.join(parts)}")
        self._view.write_warning("\n".join(lines))
        logger.info("Readiness summary: %s", "; ".join(lines))

    async def _recover_pending_approvals(self) -> None:
        """Restore workflow approval-pending state from a previous session."""
        ctx = self._ctx
        store = StateStore()
        try:
            results = find_all_pending_approvals(store.get_connection())
        finally:
            store.close()
        if not results:
            logger.warning(
                "No pending approvals found; existing approvals may have expired"
            )
            return
        # Recover the most recent pending approval first
        task_id, approval = results[0]
        ctx.workflow.approval_pending = True
        ctx.turn.pending_approval_id = approval.approval_id
        if ctx.turn.pending_approval_task_id is not None:
            logger.warning(
                "Overwriting pending_approval_task_id %s with %s during recovery",
                ctx.turn.pending_approval_task_id,
                task_id,
            )
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
