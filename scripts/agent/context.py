#!/usr/bin/env python3
"""
agent/context.py
Shared mutable runtime state injected into REPLAgent, RagPipeline,
and CommandRegistry via dependency injection.

DI boundary:
  ServiceContainer — service references (http, llm, tools, hist_mgr, rag, stdio_procs)
  AgentContext     — DI hub; all service access via ctx.services.*
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rag.types import LLMMessage

from agent.config import AgentConfig, build_agent_config
from agent.session import AgentSession
from db.tool_results import ToolResultStore

if TYPE_CHECKING:
    import httpx
    from rag.pipeline import RagPipeline
    from shared.llm_client import LLMClient
    from shared.logger import Logger
    from shared.tool_executor import StdioTransport, ToolExecutor

    from agent.history import HistoryManager
    from agent.lifecycle import ServerLifecycleManager
    from agent.memory.layer import MemoryLayer


class ServiceContainer:
    """Service references injected by AgentREPL._init_components().

    All fields are None / empty until _init_components() is called.
    Access via ctx.services.llm, ctx.services.tools, etc.
    """

    def __init__(self) -> None:
        self.http: httpx.AsyncClient | None = None
        self.llm: LLMClient | None = None
        self.tools: ToolExecutor | None = None
        self.hist_mgr: HistoryManager | None = None
        self.rag: RagPipeline | None = None
        # stdio MCP server transports (key → StdioTransport); populated by _start_stdio_servers
        self.stdio_procs: dict[str, StdioTransport] = {}
        # Audit logger writes JSON-lines turn events to audit.log; None until _init_components()
        self.audit_logger: Logger | None = None
        # Long-term / Task memory layer; None when use_memory_layer=False (default)
        self.memory: MemoryLayer | None = None
        # Lifecycle manager for ondemand stdio server startup; None until _init_components()
        self.lifecycle: ServerLifecycleManager | None = None


class AgentContext:
    """Mutable runtime state shared between REPLAgent, RagPipeline,
    and CommandRegistry.

    Components in self.services are None until REPLAgent.run() initialises them.
    All service access uses ctx.services.* directly; no property shims.
    """

    def __init__(self) -> None:
        # ── Service layer (DI boundary) ────────────────────────────────────────
        self.services: ServiceContainer = ServiceContainer()

        # ── Conversation state ─────────────────────────────────────────────────
        self.history: list[LLMMessage] = []
        self.llm_url: str = ""
        self.debug_mode: bool = False
        self.plan_mode: bool = False
        self.system_prompt_name: str = "default"
        self.shutdown_requested: bool = False

        # ── Trace IDs (reset each turn) ────────────────────────────────────────
        # UUID4 set by Orchestrator.handle_turn(); None between turns
        self.current_turn_id: str | None = None
        # UUID4 set by Orchestrator._augment_with_rag(); None when RAG is skipped
        self.current_rag_query_id: str | None = None

        # ── Session statistics ─────────────────────────────────────────────────
        self.stat_turns: int = 0
        self.stat_tool_calls: int = 0
        self.stat_rag_hits: int = 0
        self.stat_tool_errors: int = 0
        # Per-step latency samples (seconds); keyed by step name
        # (rag.mqe, rag.search, rag.rrf, rag.rerank, llm)
        self.stat_latency: dict[str, list[float]] = {}
        self.stat_semantic_cache_hits: int = 0
        # LLM token usage accumulated across turns; None = endpoint did not return usage
        self.stat_input_tokens: int | None = None
        self.stat_output_tokens: int | None = None
        # Persistent store for full tool results; /tool show <id> retrieves them
        self.tool_result_store: ToolResultStore = ToolResultStore()

        # ── Config and persistent storage ──────────────────────────────────────
        self.cfg: AgentConfig = build_agent_config()
        self.session: AgentSession = AgentSession()
