# Implementation: scripts/agent/mdq_rag_classifier.py (new file)

## Goal

Create a lightweight, deterministic query classifier that returns `MdqRagMode`
(`AUTO`, `MDQ`, or `RAG`) based on heuristic keyword detection, enabling the agent to
guide tool selection between MDQ (Markdown-structural) and RAG (semantic/general).

## Scope

**In:**
- `MdqRagMode` enum with values `AUTO`, `MDQ`, `RAG`
- `classify_query(query: str) -> MdqRagMode`: heuristic classifier
- `resolve_mode(query: str, config_mode: str | None) -> MdqRagMode`: combines classifier
  with config override

**Out:**
- LLM calls or async I/O (classifier is pure, synchronous, and deterministic)
- Changes to `ToolRouteResolver` or any other module

## Assumptions

- The module lives in `scripts/agent/` and imports only from `shared` or stdlib
  (no imports from `mcp`, `rag`, or `db` layers — avoids layer violations)
- `config_mode` values are `"auto"`, `"mdq"`, `"rag"` (lowercase strings from TOML)
- The classifier is intentionally coarse — false positives/negatives are acceptable
  because the override mechanism provides a reliable escape hatch
- Import layer: `agent → shared` is allowed; no circular risk

## Implementation

### Target file

`scripts/agent/mdq_rag_classifier.py`

### Procedure

1. Define `MdqRagMode` as a `str` enum (compatible with TOML config values)
2. Define `_MDQ_KEYWORDS` as a frozen set of Markdown-structural terms
3. Implement `classify_query()` — lowercases query, checks for any MDQ keyword
4. Implement `resolve_mode()` — config override takes precedence over classifier

### Method

```python
"""agent/mdq_rag_classifier.py
Lightweight query classifier for MDQ vs RAG tool selection.
"""
from __future__ import annotations

from enum import Enum


class MdqRagMode(str, Enum):
    AUTO = "auto"
    MDQ  = "mdq"
    RAG  = "rag"


_MDQ_KEYWORDS: frozenset[str] = frozenset({
    "heading", "headings", "outline", "hierarchy", "section",
    "markdown structure", "toc", "table of contents", ".md",
    "structure", "formatting",
})


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
            pass  # unknown config value → fall through to classifier
    return classify_query(query)
```

### Details

- `MdqRagMode(str, Enum)` means enum members compare equal to their string values
  (`MdqRagMode.MDQ == "mdq"` is `True`) — simplifies TOML config comparison
- `_MDQ_KEYWORDS` is a `frozenset` for O(1) lookup; keywords are all lowercase to
  match the lowercased query
- `resolve_mode()` silently ignores unknown config values and falls back to the
  classifier — prevents startup errors from typos in `agent.toml`
- No logging in this module; the caller (orchestrator) logs the resolved mode
- Module docstring must state: "Operates on query strings only; no I/O, no LLM calls."

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Import succeeds | `python -c "from agent.mdq_rag_classifier import MdqRagMode, classify_query, resolve_mode"` | No error |
| MDQ keywords trigger MDQ | `classify_query("show me the outline of X.md")` | `MdqRagMode.MDQ` |
| General query returns RAG | `classify_query("find information about Python")` | `MdqRagMode.RAG` |
| Config override "mdq" bypasses classifier | `resolve_mode("general query", "mdq")` | `MdqRagMode.MDQ` |
| Config override "rag" bypasses classifier | `resolve_mode("show outline", "rag")` | `MdqRagMode.RAG` |
| Unknown config falls back to classifier | `resolve_mode("show outline", "unknown")` | `MdqRagMode.MDQ` |
| Layer contract | `uv run lint-imports` | 0 violations |
| Lint | `uv run ruff check scripts/agent/mdq_rag_classifier.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/mdq_rag_classifier.py` | 0 errors |
| Unit tests | `uv run pytest tests/test_mdq_rag_classifier.py -v` | all pass (new test file required) |
