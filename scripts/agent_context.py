#!/usr/bin/env python3
"""
agent_context.py
Shared mutable runtime state injected into REPLAgent, RagPipeline,
and CommandRegistry via dependency injection.

DI boundary:
  ServiceContainer — service references (http, llm, tools, hist_mgr, rag, stdio_procs)
  AgentContext     — DI hub; all service access via ctx.services.*
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent_config import AgentConfig, build_agent_config
from agent_session import AgentSession
from rag_types import LLMMessage
from tool_result_store import ToolResultStore

if TYPE_CHECKING:
    import httpx
    from agent_rag import RagPipeline
    from history_manager import HistoryManager
    from llm_client import LLMClient
    from tool_executor import StdioTransport, ToolExecutor


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

        # ── Session statistics ─────────────────────────────────────────────────
        self.stat_turns: int = 0
        self.stat_tool_calls: int = 0
        self.stat_rag_hits: int = 0
        self.stat_tool_errors: int = 0
        # Per-step latency samples (seconds); keyed by step name
        # (rag.mqe, rag.search, rag.rrf, rag.rerank, llm)
        self.stat_latency: dict[str, list[float]] = {}
        self.stat_semantic_cache_hits: int = 0
        # Persistent store for full tool results; /tool show <id> retrieves them
        self.tool_result_store: ToolResultStore = ToolResultStore()

        # ── Config and persistent storage ──────────────────────────────────────
        self.cfg: AgentConfig = build_agent_config()
        self.session: AgentSession = AgentSession()
