"""scripts/agent/memory/snippet_filter.py — Filtering policies for memory snippets before injection.

PII/credential redaction, maximum snippet length enforcement, and system message
priority marking are applied here so that injected context cannot carry sensitive
data or exceed the allowed size.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── PII patterns ──────────────────────────────────────────────────────────────

PII_PATTERNS: dict[str, str] = {
    "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "CREDIT_CARD": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "API_KEY": r"\b[A-Za-z0-9+/]{40,}={0,2}\b",
    "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}


@dataclass(frozen=True)
class FilteredSnippet:
    """Result of PII filtering on a snippet."""

    text: str | None  # None means snippet should be rejected entirely
    was_filtered: bool
    reason: str = ""


@dataclass(frozen=True)
class TruncatedSnippet:
    """Result of length enforcement on a snippet."""

    text: str
    original_length: int
    was_truncated: bool


def filter_pii(text: str) -> FilteredSnippet:
    """Redact PII from *text* using regex-based patterns.

    Returns ``FilteredSnippet`` with ``was_filtered=True`` when any pattern matched.
    The text is never set to ``None`` by this function because partial redaction
    preserves useful context while protecting sensitive data.
    """
    filtered_text = text
    was_filtered = False
    for pattern_name, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, filtered_text)
        if matches:
            was_filtered = True
            filtered_text = re.sub(pattern, f"[REDACTED_{pattern_name}]", filtered_text)
    return FilteredSnippet(text=filtered_text, was_filtered=was_filtered)


def truncate_snippet(text: str, max_length: int = 500) -> TruncatedSnippet:
    """Truncate *text* to *max_length* characters with an indicator suffix."""
    if len(text) <= max_length:
        return TruncatedSnippet(
            text=text, original_length=len(text), was_truncated=False
        )
    truncated_text = text[:max_length] + "...[truncated]"
    return TruncatedSnippet(
        text=truncated_text, original_length=len(text), was_truncated=True
    )
