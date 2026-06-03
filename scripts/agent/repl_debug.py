"""RAG pipeline debug data builder and context utility functions.

Pure module-level helpers with no AgentContext dependency.
Extracted from agent/repl.py to reduce per-task load cost.

Debug output goes through CLIView.write_debug_rag(); these helpers build
structured dicts so the data can be serialised, logged, or rendered by
any presenter.
"""

from collections.abc import Callable

from rag.types import LLMMessage, RagHit

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


# ── Two-stage context detection ───────────────────────────────────────────────

# Phrases that indicate the LLM is requesting additional document context.
# Used by the two-stage fetch feature to trigger full-document expansion.
_MORE_CONTEXT_TRIGGERS: frozenset[str] = frozenset(
    {
        "追加情報が必要",
        "詳細が不足",
        "情報が不足",
        "全文が必要",
        "詳しい情報が必要",
        "need more context",
        "need additional context",
        "insufficient context",
        "more information needed",
        "need the full document",
    },
)


def _needs_more_context(text: str) -> bool:
    """Return True when the LLM response signals that it needs more context."""
    if not text:
        return False
    lower = text.lower()
    return any(phrase in lower for phrase in _MORE_CONTEXT_TRIGGERS)


_RAG_PREFIX = "[Reference documents]"
_QUESTION_SEP = "\n\nQuestion: "


def _extract_history_context(history: list[LLMMessage], n: int = 2) -> str:
    """Return the last n raw user queries joined by newline for MQE context.

    Strips the '[Reference documents]...\n\nQuestion: ' prefix from augmented
    messages so only the raw query text is passed to MQE. This keeps history
    context clean and avoids leaking large RAG blocks into the MQE prompt.
    """
    user_msgs: list[str] = [
        str(m["content"])
        for m in history
        if m.get("role") == "user" and m.get("content") is not None
    ]
    recent = user_msgs[-n:] if len(user_msgs) >= n else user_msgs
    raw: list[str] = []
    for msg in recent:
        if msg.startswith(_RAG_PREFIX) and _QUESTION_SEP in msg:
            raw.append(msg.split(_QUESTION_SEP, 1)[1])
        else:
            raw.append(msg)
    return "\n".join(raw)
