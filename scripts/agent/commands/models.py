"""agent/commands/models.py
Frozen dataclass ViewModels and DTOs for built-in slash-command handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StatsViewModel:
    session_id: str
    turns: int
    tool_calls: int
    tool_errors: int
    llm_retries: int
    llm_reconnects: int
    llm_heartbeat_timeouts: int
    llm_partial_completions: int
    llm_parse_errors: int
    cache_hits: int
    compress_count: int
    fallback_truncate_count: int
    memory_consistency_failures: int
    semantic_cache_hits: int
    memory_circuit_open: bool = False
    memory_fts_fallback_count: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    debug_mode: bool = False
    latency: dict[str, Any] | None = None  # presentation-only; dict intentional
    workflow_mode: str = ""


@dataclass(frozen=True)
class ToolResultView:
    result_id: int
    tool_name: str
    summary: str | None
    args_masked: dict[str, Any]  # presentation-only; dict intentional
    is_error: bool


@dataclass(frozen=True)
class McpInstallRequest:
    server_name: str


@dataclass(frozen=True)
class McpInstallRenderModel:
    server_name: str
    config_path: str
    handler_path: str
    next_steps: list[str]
