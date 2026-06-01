"""RAG pipeline debug printers and context utility functions.

Pure module-level helpers with no AgentContext dependency.
Extracted from agent/repl.py to reduce per-task load cost.
"""

from collections.abc import Callable

from rag.types import LLMMessage, RagHit

# ── RAG debug printers ────────────────────────────────────────────────────────
# Called when ctx.debug_mode is True; injected via _make_debug_fn().

_DebugFn = Callable[[list[str], list[list[RagHit]], list[RagHit], list[RagHit]], None]


def _print_debug_mqe(queries: list[str]) -> None:
    print(f"  [debug] MQE queries ({len(queries)}):")
    for i, q in enumerate(queries, 1):
        print(f"    {i}: {q}")


def _print_debug_search(all_results: list[list[RagHit]]) -> None:
    total = sum(len(r) for r in all_results)
    print(
        f"  [debug] search: {len(all_results)} result lists, {total} total candidates",
    )


def _print_debug_rrf(merged: list[RagHit]) -> None:
    print(f"  [debug] RRF merge: {len(merged)} unique candidates (top 5):")
    for c in merged[:5]:
        print(
            f"    chunk_id={c['chunk_id']}"
            f" rrf={c.get('rrf_score', 0):.4f}"
            f" url={c['url'][:60]}",
        )


def _print_debug_rerank(reranked: list[RagHit]) -> None:
    print(f"  [debug] reranked top-{len(reranked)}:")
    for c in reranked:
        score = c.get("rerank_score", c.get("rrf_score", 0))
        print(f"    chunk_id={c['chunk_id']} score={score:.4f} url={c['url'][:60]}")


def _make_debug_fn() -> _DebugFn:
    """Return a callback that prints all four RAG pipeline debug steps."""

    def _fn(
        queries: list[str],
        all_results: list[list[RagHit]],
        merged: list[RagHit],
        reranked: list[RagHit],
    ) -> None:
        _print_debug_mqe(queries)
        _print_debug_search(all_results)
        _print_debug_rrf(merged)
        _print_debug_rerank(reranked)

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
