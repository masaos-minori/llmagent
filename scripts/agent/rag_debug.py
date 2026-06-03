"""RAG pipeline debug data builder.

Pure module-level helpers with no AgentContext dependency.
Extracted from agent/repl_debug.py to reduce per-task load cost.

Debug output goes through CLIView.write_debug_rag(); these helpers build
structured dicts so the data can be serialised, logged, or rendered by
any presenter.
"""

from collections.abc import Callable

from rag.types import RagHit

# ── RAG debug data builder ─────────────────────────────────────────────────────
# Called when ctx.debug_mode is True; injected via _make_debug_fn().

_DebugFn = Callable[[list[str], list[list[RagHit]], list[RagHit], list[RagHit]], None]


def build_debug_rag_data(
    queries: list[str],
    all_results: list[list[RagHit]],
    merged: list[RagHit],
    reranked: list[RagHit],
) -> dict:
    """Return a serialisable dict representing one RAG pipeline run."""
    return {
        "queries": list(queries),
        "all_results": [list(r) for r in all_results],
        "merged": list(merged),
        "reranked": list(reranked),
    }


def _make_debug_fn(on_debug: Callable[[dict], None] | None = None) -> _DebugFn:
    """Return a callback that builds RAG debug data and delegates rendering.

    on_debug: callable that receives the structured dict (e.g. CLIView.write_debug_rag).
    Falls back to a no-op when on_debug is None.
    """

    def _fn(
        queries: list[str],
        all_results: list[list[RagHit]],
        merged: list[RagHit],
        reranked: list[RagHit],
    ) -> None:
        if on_debug is None:
            return
        on_debug(build_debug_rag_data(queries, all_results, merged, reranked))

    return _fn
