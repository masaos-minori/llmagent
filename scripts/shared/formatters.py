#!/usr/bin/env python3
"""
formatters.py
Shared output formatting utilities for MCP tool dispatch handlers.

Provides two categories:
  LLM context — token-saving representation sent as tool result context
  Terminal     — human-readable representation shown in the terminal

All MCP servers import from this module to ensure consistency across
FileopMCPServer, WebSearchMCPServer, and GithubMCPServer.
"""

# ── Constants ─────────────────────────────────────────────────────────────────

# Maximum body/snippet characters per result item for LLM context (token-saving)
MAX_SNIPPET_CHARS: int = 400


# ── Text utilities ─────────────────────────────────────────────────────────────


def truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending '...' if cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def fmt_size(size: int) -> str:
    """Return a human-readable file size string (B / KB / MB)."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size // 1024} KB"
    return f"{size // (1024 * 1024)} MB"


def fmt_md_link(text: str, url: str) -> str:
    """Return a Markdown inline link: [text](url)."""
    return f"[{text}]({url})"


# ── Structured log formatting ──────────────────────────────────────────────────


def fmt_kvlog(op: str, **kwargs: object) -> str:
    """Format a structured key=value log message (e.g. 'op=search provider=bing n=10'); None values are omitted."""
    parts = [f"op={op}"]
    for k, v in kwargs.items():
        if v is not None:
            parts.append(f"{k}={v}")
    return " ".join(parts)
