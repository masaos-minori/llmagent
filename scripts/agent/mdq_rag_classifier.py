"""agent/mdq_rag_classifier.py

Lightweight query classifier for MDQ vs RAG tool selection.
Operates on query strings only; no I/O, no LLM calls.
"""

from __future__ import annotations

from enum import StrEnum


class MdqRagMode(StrEnum):
    AUTO = "auto"
    MDQ = "mdq"
    RAG = "rag"


_MDQ_KEYWORDS: frozenset[str] = frozenset(
    {
        "heading",
        "headings",
        "outline",
        "hierarchy",
        "section",
        "markdown structure",
        "toc",
        "table of contents",
        ".md",
        "structure",
        "formatting",
    }
)


def classify_query(query: str) -> MdqRagMode:
    """Return MDQ if query contains Markdown-structural terms; RAG otherwise."""
    lower = query.lower()
    if any(kw in lower for kw in _MDQ_KEYWORDS):
        return MdqRagMode.MDQ
    return MdqRagMode.RAG


def resolve_mode(query: str, config_mode: str | None) -> MdqRagMode:
    """Config override takes precedence; AUTO falls back to classifier heuristics."""
    if config_mode and config_mode != MdqRagMode.AUTO:
        try:
            return MdqRagMode(config_mode)
        except ValueError:
            pass  # unknown config value — fall through to classifier
    return classify_query(query)
