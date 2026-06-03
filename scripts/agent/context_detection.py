"""Two-stage context detection utilities.

Pure module-level helpers with no AgentContext dependency.
Extracted from agent/repl_debug.py to reduce per-task load cost.
"""

from rag.types import LLMMessage

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
