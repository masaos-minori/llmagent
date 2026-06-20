# Implementation: Add OQ-6 reference to test_fts_fallback.py module docstring

## Goal
Add a `Resolves:` line to the module docstring of `tests/test_fts_fallback.py`
so the file is traceable to the open question it validates.

## Scope
- File: `tests/test_fts_fallback.py`
- Module docstring only — one line added
- No behavior change

## Assumptions
- Current module docstring ends at line 10 (after "- Mixed-language documents...")
- The closing `"""` is the next line to be edited
- Consistent with project convention of referencing issue IDs in test docstrings

## Implementation

### Target file
`tests/test_fts_fallback.py`

### Procedure
Append a `Resolves:` line to the existing module docstring.

### Method
Single edit — add one line before the closing triple-quote.

### Details

**Current module docstring (lines 1-10):**
```python
"""
tests/test_fts_fallback.py
Integration tests for FTS5 fallback behavior when normalized_content is NULL.

Verifies:
- COALESCE trigger falls back to content when normalized_content is NULL
- English and code chunk tokens are indexed via the fallback path
- Empty string normalized_content differs from NULL (COALESCE semantics)
- Mixed-language documents index each chunk independently
"""
```

**Updated module docstring:**
```python
"""
tests/test_fts_fallback.py
Integration tests for FTS5 fallback behavior when normalized_content is NULL.

Verifies:
- COALESCE trigger falls back to content when normalized_content is NULL
- English and code chunk tokens are indexed via the fallback path
- Empty string normalized_content differs from NULL (COALESCE semantics)
- Mixed-language documents index each chunk independently

Resolves: OQ-6 (docs/03_rag_90_inconsistencies_and_known_issues.md)
"""
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| OQ-6 reference present | `grep "OQ-6" tests/test_fts_fallback.py` | 1 match |
| Tests still pass | `uv run pytest tests/test_fts_fallback.py -v` | 8 passed |
| Lint | `uv run ruff check tests/test_fts_fallback.py` | 0 errors |
