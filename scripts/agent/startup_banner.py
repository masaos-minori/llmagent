#!/usr/bin/env python3
"""scripts/agent/startup_banner.py

StartupBanner — startup display and banner printing.

Responsibilities:
  - Printing the startup banner (DB chunks, tool count, workflow status)
"""

from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING

from agent.cli_view import CLIView
from agent.context import AgentContext
from agent.services.rag_maintenance_service import RagMaintenanceService

if TYPE_CHECKING:
    from agent.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class StartupBanner:
    """Handles startup display and banner printing.

    Encapsulates ``_print_startup_banner``, ``_get_chunk_count``,
    and ``_get_workflow_status`` extracted from AgentREPL.

    Initialization ordering:
        Must be created after build_agent_context() completes, ensuring
        AgentContext.services is initialized before any property access.
    """

    def __init__(self, ctx: AgentContext, view: CLIView) -> None:
        """Initialize with AgentContext and CLIView references."""
        self._ctx = ctx
        self._view = view

    @property
    def n_tools(self) -> int:
        """Number of tools available at runtime (excludes unavailable/degraded servers).

        Requires AgentContext.services to be initialized before use. If called
        before initialization, logs a warning and returns 0 instead of raising
        RuntimeError. This prevents crashes but may hide misconfiguration issues.
        """
        if self._ctx.services is None:
            logger.warning(
                "StartupBanner.n_tools called before services initialized — "
                "returning 0; call build_agent_context() first"
            )
            return 0
        rt = self._ctx.services_required.runtime_tools
        return len(rt.all_tools()) if rt else 0

    def print_startup_banner(self, orchestrator: Orchestrator | None) -> None:
        """Print the startup line showing DB chunks, tool count, and workflow status.

        orchestrator is the REPL's own _orchestrator attribute, passed in
        explicitly since StartupBanner is constructed before startup.run()
        assigns it — there is no ctx-level place to stash it.
        """
        chunk_count = self._get_chunk_count()
        workflow_status = self._get_workflow_status(orchestrator)
        mem_cfg = self._ctx.cfg.memory
        memory_mode = "enabled" if mem_cfg.use_memory_layer else "disabled"
        self._view.write_startup_banner(
            chunk_count,
            self.n_tools,
            workflow_status,
            memory_mode=memory_mode,
        )

    def _get_chunk_count(self) -> str:
        """Return formatted chunk count from DB, or '?' on error."""
        try:
            count = RagMaintenanceService().stats_rag()[1]
            return f"{count:,}"
        except (sqlite3.Error, OSError, RuntimeError) as e:
            logger.debug("Failed to get chunk count: %s", e)
            return "?"

    def _get_workflow_status(self, orchestrator: Orchestrator | None) -> str:
        """Return a human-readable workflow status string for the startup banner.

        Orchestrator has no real workflow_status() method today — see
        issues/20260911-153000_replbanner01_orchestrator-workflow-status-unimplemented.md.
        getattr(..., None) keeps this from raising AttributeError against the
        real class while still exercising the intended "enabled"/"not loaded"
        branches wherever a caller (real or test double) does provide one.
        """
        if orchestrator is None:
            return "unknown"
        get_status = getattr(orchestrator, "workflow_status", None)
        if get_status is None:
            return "not loaded"
        status = get_status()
        if status["tracking"] == "enabled":
            return "enabled"
        return "not loaded"
