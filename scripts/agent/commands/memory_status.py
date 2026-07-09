"""status.py — Memory layer status display logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass
class MemoryStatus:
    """Structured representation of memory layer status for display."""

    mode: str = ""
    memory_layer_enabled: bool = False
    embedding_enabled: bool = False
    local_only: bool = False
    circuit_open: bool = False
    circuit_detail: str = ""
    consecutive_failures: int = 0
    fts_fallback_count: int = 0
    last_retrieval_mode: str = ""
    total_entries: int = 0
    semantic_entries: int = 0
    episodic_entries: int = 0
    embed_skip_count: int = 0
    by_source: dict[str, int] = field(default_factory=dict)


def build_status_table(status: MemoryStatus) -> list[list[str]]:
    """Build a table of rows for display."""
    circuit_display = "closed"
    if status.circuit_open:
        circuit_display = f"OPEN  [circuit breaker active{status.circuit_detail}]"

    mode_display = status.last_retrieval_mode
    if status.last_retrieval_mode == "fts_only":
        mode_display = "fts_only  [DEGRADED — embedding unavailable]"

    rows: list[list[str]] = []

    # Compute mode label based on field combinations
    if not status.memory_layer_enabled:
        mode_label = "Memory layer disabled"
    elif status.circuit_open:
        mode_label = "Degraded mode (circuit open, FTS fallback)"
    elif status.embedding_enabled:
        mode_label = "Hybrid mode (semantic + FTS)"
    else:
        mode_label = "Memory enabled, embedding disabled (FTS-only)"

    rows.append(["Mode", mode_label])
    rows.append(
        ["Memory layer", "enabled" if status.memory_layer_enabled else "disabled"]
    )
    rows.append(["Embedding enabled", "Yes" if status.embedding_enabled else "No"])
    rows.append(["Local-only", "enabled" if status.local_only else "disabled"])
    rows.append(["Circuit", circuit_display])
    rows.append(["Consecutive failures", str(status.consecutive_failures)])
    rows.append(["FTS fallback count", str(status.fts_fallback_count)])
    rows.append(["Last retrieval mode", mode_display])
    rows.append(["Entries (total)", str(status.total_entries)])
    rows.append(["  semantic", str(status.semantic_entries)])
    rows.append(["  episodic", str(status.episodic_entries)])
    rows.append(["Embed skip count", str(status.embed_skip_count)])
    for src, cnt in status.by_source.items():
        rows.append([f"  source:{src}", str(cnt)])
    return rows


def build_memory_status(
    mem: Any,  # MemoryServices | None
) -> MemoryStatus | None:
    """Build a MemoryStatus from a MemoryServices instance."""
    if mem is None:
        return None

    embed_client = mem.retriever.embed_client
    if embed_client is None:
        stats = mem.get_stats()
        return MemoryStatus(
            mode=mem.get_activation_mode(),
            memory_layer_enabled=True,
            embedding_enabled=False,
            local_only=False,
            circuit_open=False,
            circuit_detail="",
            consecutive_failures=0,
            fts_fallback_count=mem.retriever.fts_fallback_count,
            last_retrieval_mode=mem.retriever.last_retrieval_mode,
            total_entries=stats["total"],
            semantic_entries=stats["semantic"],
            episodic_entries=stats["episodic"],
            embed_skip_count=0,
            by_source=stats.get("by_source", {}),
        )

    status_info = embed_client.get_status()
    circuit_detail = ""
    if status_info.circuit_open and status_info.resets_in_sec is not None:
        circuit_detail = f" (resets in {status_info.resets_in_sec:.0f}s)"

    retrieval_mode = mem.retriever.last_retrieval_mode
    stats = mem.get_stats()

    return MemoryStatus(
        mode=mem.get_activation_mode(),
        memory_layer_enabled=True,
        embedding_enabled=status_info.enabled,
        local_only=status_info.local_only,
        circuit_open=status_info.circuit_open,
        circuit_detail=circuit_detail,
        consecutive_failures=status_info.fail_count,
        fts_fallback_count=mem.retriever.fts_fallback_count,
        last_retrieval_mode=retrieval_mode,
        total_entries=stats["total"],
        semantic_entries=stats["semantic"],
        episodic_entries=stats["episodic"],
        embed_skip_count=stats["embed_skip"],
        by_source=stats["by_source"],
    )
