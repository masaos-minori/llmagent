# Goal

Tighten `augment.py` by changing `_format_chunks(reranked: list)` to
`list[RankedHit]` and replacing `c.get('title') or c['url']` with
`c.title if c.title else c.url`.

# Scope

- `scripts/rag/stages/augment.py`

# Assumptions

1. `RankedHit` dataclass from Step 3-1 prerequisite.
2. `c.get('title') or c['url']` is the current pattern for building the
   chunk header; after `RankedHit` is a dataclass, this becomes
   `c.title if c.title else c.url`.
3. `_format_chunks` may be a module-level function or a method; change its
   type annotation accordingly.
4. No other `dict`-style access remains in this file after the change.

# Implementation

## Target file

`scripts/rag/stages/augment.py`

## Procedure

1. Change `_format_chunks(reranked: list)` → `_format_chunks(reranked: list[RankedHit])`.
2. Replace `c.get('title') or c['url']` → `c.title if c.title else c.url`.
3. Replace any other `c.get(...)` / `c["..."]` patterns with attribute access.
4. Run ruff + mypy.

## Method

Type annotation tightening + attribute access substitution.

# Validation plan

- `grep -n "\.get\|c\[" scripts/rag/stages/augment.py` → 0 hits
- `uv run ruff check scripts/rag/stages/augment.py`
- `uv run mypy scripts/rag/stages/augment.py`
