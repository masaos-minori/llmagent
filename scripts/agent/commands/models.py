"""agent/commands/models.py

Frozen dataclass ViewModels and DTOs for built-in slash-command handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LatencySnapshot:
    """Per-tool latency stats mapping tool_name to a list of elapsed-second samples."""

    data: dict[str, list[float]]


@dataclass(frozen=True)
class MaskedArgs:
    """Decoded and masked tool arguments for display (arg_name -> masked value)."""

    data: dict[str, Any]


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
    latency: LatencySnapshot | None = None
    approval_pending: bool = False
    rag_db_configured: bool = False
