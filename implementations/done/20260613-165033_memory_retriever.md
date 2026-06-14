# Implementation: agent/memory/retriever.py — FTS5 token quoting

## Goal

Add double-quote escaping to all tokens in `_build_fts_query()` so that FTS5 reserved words (AND, OR, NOT, NEAR) are treated as literals, without adding a `content:` column filter.

## Scope

- `scripts/agent/memory/retriever.py` — `_build_fts_query()` only (lines 96–101)
- `scripts/rag/repository.py` — no change (already quotes tokens)
- No test file changes expected; existing tests should pass after the change

## Assumptions

- `memories_fts` has 3 columns: `content`, `summary`, `tags`; adding `content:` filter would drop summary/tags search — must NOT be added
- `chunks_fts` has only `content` column; column filter would be redundant
- Token regex `re.findall(r"\w+", text)` remains unchanged
- Change is purely in the join expression: `" OR ".join(tokens)` → `" OR ".join(f'"{t}"' for t in tokens)`
- No import changes needed

## Implementation

### Target file

- `scripts/agent/memory/retriever.py`

### Procedure

1. Open `scripts/agent/memory/retriever.py`
2. Locate `_build_fts_query()` at line 96
3. Replace the return expression on line 101

### Method

- Single-line Edit on the return statement

### Details

**Current (lines 96–101):**
```python
def _build_fts_query(text: str) -> str:
    """Build an FTS5 MATCH query from free-form text; quotes multi-word tokens."""
    tokens = re.findall(r"\w+", text)
    if not tokens:
        return '""'
    return " OR ".join(tokens)
```

**After:**
```python
def _build_fts_query(text: str) -> str:
    """Build FTS5 MATCH query with token quoting to escape reserved terms.

    All tokens are double-quoted to escape AND/OR/NOT/NEAR as literals.
    No column filter: memories_fts searches content, summary, and tags.
    """
    tokens = re.findall(r"\w+", text)
    if not tokens:
        return '""'
    return " OR ".join(f'"{t}"' for t in tokens)
```

The docstring is updated to explain why `content:` is absent — this is a non-obvious invariant.

## Validation plan

- `uv run pytest tests/test_memory_retriever.py -v` — all pass
- `uv run mypy scripts/agent/memory/retriever.py` — 0 new errors
- `uv run ruff check scripts/agent/memory/retriever.py` — 0 errors
- Manual check: `python -c "import re; tokens = re.findall(r'\w+', 'NOT NEAR test'); print(' OR '.join(f'\"{t}\"' for t in tokens))"` → `"NOT" OR "NEAR" OR "test"`
