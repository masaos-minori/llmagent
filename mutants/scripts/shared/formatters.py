#!/usr/bin/env python3
"""scripts/shared/formatters.py

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

# Bytes-to-KB conversion base (powers of 1024)
_BYTES_PER_KB: int = 1024


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_truncate__mutmut: MutantDict = {}  # type: ignore


# ── Text utilities ─────────────────────────────────────────────────────────────


@_mutmut_mutated(mutants_x_truncate__mutmut)
def truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending '...' if cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


# ── Text utilities ─────────────────────────────────────────────────────────────


def x_truncate__mutmut_orig(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending '...' if cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


# ── Text utilities ─────────────────────────────────────────────────────────────


def x_truncate__mutmut_1(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending '...' if cut."""
    if len(text) < max_chars:
        return text
    return text[:max_chars] + "..."


# ── Text utilities ─────────────────────────────────────────────────────────────


def x_truncate__mutmut_2(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending '...' if cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] - "..."


# ── Text utilities ─────────────────────────────────────────────────────────────


def x_truncate__mutmut_3(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending '...' if cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "XX...XX"

mutants_x_truncate__mutmut['_mutmut_orig'] = x_truncate__mutmut_orig # type: ignore # mutmut generated
mutants_x_truncate__mutmut['x_truncate__mutmut_1'] = x_truncate__mutmut_1 # type: ignore # mutmut generated
mutants_x_truncate__mutmut['x_truncate__mutmut_2'] = x_truncate__mutmut_2 # type: ignore # mutmut generated
mutants_x_truncate__mutmut['x_truncate__mutmut_3'] = x_truncate__mutmut_3 # type: ignore # mutmut generated
mutants_x_fmt_size__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_fmt_size__mutmut)
def fmt_size(size: int) -> str:
    """Return a human-readable file size string (B / KB / MB)."""
    if size < _BYTES_PER_KB:
        return f"{size} B"
    if size < _BYTES_PER_KB * _BYTES_PER_KB:
        return f"{size // _BYTES_PER_KB} KB"
    return f"{size // (_BYTES_PER_KB * _BYTES_PER_KB)} MB"


def x_fmt_size__mutmut_orig(size: int) -> str:
    """Return a human-readable file size string (B / KB / MB)."""
    if size < _BYTES_PER_KB:
        return f"{size} B"
    if size < _BYTES_PER_KB * _BYTES_PER_KB:
        return f"{size // _BYTES_PER_KB} KB"
    return f"{size // (_BYTES_PER_KB * _BYTES_PER_KB)} MB"


def x_fmt_size__mutmut_1(size: int) -> str:
    """Return a human-readable file size string (B / KB / MB)."""
    if size <= _BYTES_PER_KB:
        return f"{size} B"
    if size < _BYTES_PER_KB * _BYTES_PER_KB:
        return f"{size // _BYTES_PER_KB} KB"
    return f"{size // (_BYTES_PER_KB * _BYTES_PER_KB)} MB"


def x_fmt_size__mutmut_2(size: int) -> str:
    """Return a human-readable file size string (B / KB / MB)."""
    if size < _BYTES_PER_KB:
        return f"{size} B"
    if size <= _BYTES_PER_KB * _BYTES_PER_KB:
        return f"{size // _BYTES_PER_KB} KB"
    return f"{size // (_BYTES_PER_KB * _BYTES_PER_KB)} MB"


def x_fmt_size__mutmut_3(size: int) -> str:
    """Return a human-readable file size string (B / KB / MB)."""
    if size < _BYTES_PER_KB:
        return f"{size} B"
    if size < _BYTES_PER_KB / _BYTES_PER_KB:
        return f"{size // _BYTES_PER_KB} KB"
    return f"{size // (_BYTES_PER_KB * _BYTES_PER_KB)} MB"


def x_fmt_size__mutmut_4(size: int) -> str:
    """Return a human-readable file size string (B / KB / MB)."""
    if size < _BYTES_PER_KB:
        return f"{size} B"
    if size < _BYTES_PER_KB * _BYTES_PER_KB:
        return f"{size / _BYTES_PER_KB} KB"
    return f"{size // (_BYTES_PER_KB * _BYTES_PER_KB)} MB"


def x_fmt_size__mutmut_5(size: int) -> str:
    """Return a human-readable file size string (B / KB / MB)."""
    if size < _BYTES_PER_KB:
        return f"{size} B"
    if size < _BYTES_PER_KB * _BYTES_PER_KB:
        return f"{size // _BYTES_PER_KB} KB"
    return f"{size / (_BYTES_PER_KB * _BYTES_PER_KB)} MB"


def x_fmt_size__mutmut_6(size: int) -> str:
    """Return a human-readable file size string (B / KB / MB)."""
    if size < _BYTES_PER_KB:
        return f"{size} B"
    if size < _BYTES_PER_KB * _BYTES_PER_KB:
        return f"{size // _BYTES_PER_KB} KB"
    return f"{size // (_BYTES_PER_KB / _BYTES_PER_KB)} MB"

mutants_x_fmt_size__mutmut['_mutmut_orig'] = x_fmt_size__mutmut_orig # type: ignore # mutmut generated
mutants_x_fmt_size__mutmut['x_fmt_size__mutmut_1'] = x_fmt_size__mutmut_1 # type: ignore # mutmut generated
mutants_x_fmt_size__mutmut['x_fmt_size__mutmut_2'] = x_fmt_size__mutmut_2 # type: ignore # mutmut generated
mutants_x_fmt_size__mutmut['x_fmt_size__mutmut_3'] = x_fmt_size__mutmut_3 # type: ignore # mutmut generated
mutants_x_fmt_size__mutmut['x_fmt_size__mutmut_4'] = x_fmt_size__mutmut_4 # type: ignore # mutmut generated
mutants_x_fmt_size__mutmut['x_fmt_size__mutmut_5'] = x_fmt_size__mutmut_5 # type: ignore # mutmut generated
mutants_x_fmt_size__mutmut['x_fmt_size__mutmut_6'] = x_fmt_size__mutmut_6 # type: ignore # mutmut generated


def fmt_md_link(text: str, url: str) -> str:
    """Return a Markdown inline link: [text](url)."""
    return f"[{text}]({url})"
mutants_x_fmt_kvlog__mutmut: MutantDict = {}  # type: ignore


# ── Structured log formatting ──────────────────────────────────────────────────


@_mutmut_mutated(mutants_x_fmt_kvlog__mutmut)
def fmt_kvlog(op: str, **kwargs: object) -> str:
    """Format a structured key=value log message (e.g. 'op=search provider=bing n=10'); None values are omitted."""
    parts = [f"op={op}"]
    for k, v in kwargs.items():
        if v is not None:
            parts.append(f"{k}={v}")
    return " ".join(parts)


# ── Structured log formatting ──────────────────────────────────────────────────


def x_fmt_kvlog__mutmut_orig(op: str, **kwargs: object) -> str:
    """Format a structured key=value log message (e.g. 'op=search provider=bing n=10'); None values are omitted."""
    parts = [f"op={op}"]
    for k, v in kwargs.items():
        if v is not None:
            parts.append(f"{k}={v}")
    return " ".join(parts)


# ── Structured log formatting ──────────────────────────────────────────────────


def x_fmt_kvlog__mutmut_1(op: str, **kwargs: object) -> str:
    """Format a structured key=value log message (e.g. 'op=search provider=bing n=10'); None values are omitted."""
    parts = None
    for k, v in kwargs.items():
        if v is not None:
            parts.append(f"{k}={v}")
    return " ".join(parts)


# ── Structured log formatting ──────────────────────────────────────────────────


def x_fmt_kvlog__mutmut_2(op: str, **kwargs: object) -> str:
    """Format a structured key=value log message (e.g. 'op=search provider=bing n=10'); None values are omitted."""
    parts = [f"op={op}"]
    for k, v in kwargs.items():
        if v is None:
            parts.append(f"{k}={v}")
    return " ".join(parts)


# ── Structured log formatting ──────────────────────────────────────────────────


def x_fmt_kvlog__mutmut_3(op: str, **kwargs: object) -> str:
    """Format a structured key=value log message (e.g. 'op=search provider=bing n=10'); None values are omitted."""
    parts = [f"op={op}"]
    for k, v in kwargs.items():
        if v is not None:
            parts.append(None)
    return " ".join(parts)


# ── Structured log formatting ──────────────────────────────────────────────────


def x_fmt_kvlog__mutmut_4(op: str, **kwargs: object) -> str:
    """Format a structured key=value log message (e.g. 'op=search provider=bing n=10'); None values are omitted."""
    parts = [f"op={op}"]
    for k, v in kwargs.items():
        if v is not None:
            parts.append(f"{k}={v}")
    return " ".join(None)


# ── Structured log formatting ──────────────────────────────────────────────────


def x_fmt_kvlog__mutmut_5(op: str, **kwargs: object) -> str:
    """Format a structured key=value log message (e.g. 'op=search provider=bing n=10'); None values are omitted."""
    parts = [f"op={op}"]
    for k, v in kwargs.items():
        if v is not None:
            parts.append(f"{k}={v}")
    return "XX XX".join(parts)

mutants_x_fmt_kvlog__mutmut['_mutmut_orig'] = x_fmt_kvlog__mutmut_orig # type: ignore # mutmut generated
mutants_x_fmt_kvlog__mutmut['x_fmt_kvlog__mutmut_1'] = x_fmt_kvlog__mutmut_1 # type: ignore # mutmut generated
mutants_x_fmt_kvlog__mutmut['x_fmt_kvlog__mutmut_2'] = x_fmt_kvlog__mutmut_2 # type: ignore # mutmut generated
mutants_x_fmt_kvlog__mutmut['x_fmt_kvlog__mutmut_3'] = x_fmt_kvlog__mutmut_3 # type: ignore # mutmut generated
mutants_x_fmt_kvlog__mutmut['x_fmt_kvlog__mutmut_4'] = x_fmt_kvlog__mutmut_4 # type: ignore # mutmut generated
mutants_x_fmt_kvlog__mutmut['x_fmt_kvlog__mutmut_5'] = x_fmt_kvlog__mutmut_5 # type: ignore # mutmut generated
