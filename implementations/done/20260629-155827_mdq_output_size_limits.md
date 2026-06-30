# Implementation: Harden MDQ output-size limits and fix OutlineRequest field-name mismatch

## Goal

Harden all MDQ tools (`search_docs`, `get_chunk`, `outline`, `grep_docs`) with complete, consistent, configurable output-size limits that truncate predictably before MCP global truncation, and fix the existing field-name inconsistency between `OutlineRequest` and the tool schema.

## Scope

- **In-Scope**:
  - Fix `OutlineRequest` field-name bug: model uses `max_items` but tool schema uses `max_outline_items` — must align
  - Verify and harden `search_docs` truncation: ensure `[Truncated — ...]` message includes original total count and a narrowing suggestion
  - Verify and harden `get_chunk` truncation: ensure `[Truncated — X/Y chars]` format always includes original size; add narrowing suggestion
  - Verify and harden `outline` truncation: ensure `[Truncated — X/Y headings]` format always includes original total; add narrowing suggestion
  - Verify and harden `grep_docs` truncation: ensure `[Truncated — N matches shown (total: M)]` includes original count; add narrowing suggestion
  - Enforce that per-tool request overrides cannot exceed config-level caps (i.e., request overrides are bounded by server config)
  - Add tests for each truncation path in `tests/test_mdq_service.py`
  - Update `config/mdq_mcp_server.toml` inline comments to document each limit parameter's role and recommended production values

- **Out-of-Scope**:
  - Changing DB schema or SQLite table definitions
  - Adding new limit parameters beyond the 5 already specified (`max_results_limit`, `max_chars_per_chunk`, `max_total_result_chars`, `max_outline_items`, `max_grep_matches`)
  - Hybrid search / embedding pipeline changes
  - `index_paths` / `refresh_index` output (these return structured operation summaries, not large retrieval blobs)
  - MCP transport-level truncation mechanism (handled by MCP framework, outside this scope)

## Verification Results

### 1. Current state: OutlineRequest field-name mismatch confirmed

**File**: `scripts/mcp/mdq/tools.py:85` — tool schema uses `max_outline_items`
**File**: `scripts/mcp/mdq/models.py:113` — OutlineRequest uses `max_items`

```python
# tools.py (tool schema):
"max_outline_items": {"type": "integer", "description": "Max outline items..."}

# models.py (request model):
class OutlineRequest(BaseModel):
    path: str
    max_depth: int | None = 6
    max_items: int | None = 500  # <-- MISMATCH: should be max_outline_items
```

- When agent sends `max_outline_items: 100`, it is silently ignored
- OutlineRequest defaults to 500 instead of using the agent's intent
- This is a real bug — not just a naming inconsistency

### 2. Current state: truncation messages lack narrowing suggestions

**File**: `scripts/mcp/mdq/search.py` — search_docs truncation
- Current: `[Truncated — total chars exceeded {max_chars}]`
- Missing: original result count, narrowing suggestion

**File**: `scripts/mcp/mdq/service.py` — get_chunk truncation
- Current: `[Truncated — {len(row['content'])}/{max_chars} chars]`
- Missing: narrowing suggestion

**File**: `scripts/mcp/mdq/service.py` — outline truncation
- Current: `[Truncated — {len(headings)}/{max_items} headings]`
- Missing: original total count, narrowing suggestion

**File**: `scripts/mcp/mdq/service.py` — grep_docs truncation
- Current: `[Truncated — {max_matches} matches shown]`
- Missing: total-count note (can't know true total), narrowing suggestion

### 3. UNK-01: grep_docs cannot report true total match count

- `grep_docs` stops scanning at `max_matches` by design for performance
- Cannot report exact total — must use "at least" or "cap reached" phrasing
- Resolution: `[Truncated — cap of {max_matches} matches reached. Narrow pattern or add path filter.]`

### 4. UNK-03: Request override capping decision

- Requirement says "configurable limits" but doesn't explicitly state whether request can override higher
- Decision: request overrides are bounded above by the config cap
- Pattern: `min(request_override, config_cap)` in each method

## Implementation

### Target file: `scripts/mcp/mdq/models.py`

#### Procedure

Fix OutlineRequest field name to match tool schema.

#### Details

**In OutlineRequest — rename max_items to max_outline_items:**
```python
# Before:
class OutlineRequest(BaseModel):
    path: str
    max_depth: int | None = 6
    max_items: int | None = 500

# After:
class OutlineRequest(BaseModel):
    path: str
    max_depth: int | None = 6
    max_outline_items: int | None = 500
```

**Update service.py to use new field name:**
```python
# Before (in outline method):
max_items = getattr(req, "max_outline_items", None) or self._cfg.max_outline_items

# After:
max_items = req.max_outline_items or self._cfg.max_outline_items
```

### Target file: `scripts/mcp/mdq/search.py`

#### Procedure

Improve search_docs truncation message.

#### Details

**In search_docs — improve truncation message:**
```python
# Before:
result += f"\n[Truncated — total chars exceeded {max_chars}]"

# After:
result += (
    f"\n[Truncated — {total_results} results found, "
    f"{len(results)} shown ({chars_used}/{max_chars} chars). "
    f"Use a narrower query or get_chunk for specific sections.]"
)
```

### Target file: `scripts/mcp/mdq/service.py`

#### Procedure

Improve truncation messages for get_chunk, outline, grep_docs and add request override capping.

#### Details

**In get_chunk — improve truncation message:**
```python
# Before:
result += f"\n[Truncated — {original_len}/{max_chars} chars]"

# After:
result += (
    f"\n[Truncated — {original_len}/{max_chars} chars. "
    f"Use a narrower chunk_id or reduce max_chars_per_chunk.]"
)
```

**In outline — improve truncation message:**
```python
# Before:
result += f"\n[Truncated — {len(headings)}/{max_items} headings]"

# After:
result += (
    f"\n[Truncated — {total_headings} headings found, "
    f"{max_items} shown. "
    f"Use a deeper path_prefix filter or reduce max_outline_items.]"
)
```

**In grep_docs — improve truncation message:**
```python
# Before:
result += f"\n[Truncated — {len(matches)} matches shown]"

# After:
result += (
    f"\n[Truncated — cap of {max_matches} matches reached. "
    f"Use a more specific pattern or path filter to narrow results.]"
)
```

**In each method — add request override capping:**
```python
# Before:
max_items = req.max_outline_items or self._cfg.max_outline_items

# After:
request_limit = req.max_outline_items
config_cap = self._cfg.max_outline_items
max_items = min(request_limit, config_cap) if request_limit is not None else config_cap
```

### Target file: `tests/test_mdq_service.py`

#### Procedure

Add truncation coverage tests for each tool.

#### Details

**Append new test class:**
```python
class TestTruncation:
    """Verify output-size limits and truncation messages."""

    def test_search_docs_truncates_by_results_limit(self) -> None:
        ...

    def test_search_docs_truncates_by_char_limit(self) -> None:
        ...

    def test_get_chunk_truncates_large_content(self) -> None:
        ...

    def test_outline_truncates_large_heading_list(self) -> None:
        ...

    def test_grep_docs_truncates_at_match_cap(self) -> None:
        ...

    def test_request_override_bounded_by_config_cap(self) -> None:
        """Per-request override cannot exceed config cap."""
        ...
```

### Target file: `config/mdq_mcp_server.toml`

#### Procedure

Add production-guidance comments for each limit key.

#### Details

**Expand existing comments:**
```toml
# Maximum number of search results returned (default: 10).
# Production recommendation: 20-50 depending on typical query specificity.
max_results_limit = 10

# Maximum characters per chunk returned by get_chunk (default: 4096).
# Production recommendation: 8192 for full section content, 2048 for snippets.
max_chars_per_chunk = 4096

# Maximum total characters across all search results (default: 32768).
# Production recommendation: 65536 for broad queries, 16384 for targeted queries.
max_total_result_chars = 32768

# Maximum outline items returned by outline tool (default: 500).
# Production recommendation: 200-300 for reasonable response sizes.
max_outline_items = 500

# Maximum grep match results returned by grep_docs (default: 200).
# Production recommendation: 100-200 to prevent large response payloads.
max_grep_matches = 200
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `models.py` OutlineRequest field alignment | Verify `OutlineRequest(**{"max_outline_items": 5})` does not raise | `uv run python -c "from mcp.mdq.models import OutlineRequest; r = OutlineRequest(path='/tmp/test.md', max_outline_items=5)"` | No ValidationError |
| `scripts/mcp/mdq/service.py` (get_chunk) | Unit test with content > max_chars_per_chunk | `uv run pytest tests/test_mdq_service.py::TestTruncation::test_get_chunk_truncates_large_content -v` | Returns truncated content with `[Truncated — X/Y chars]` message |
| `scripts/mcp/mdq/service.py` (outline) | Unit test with >max_outline_items headings | `uv run pytest tests/test_mdq_service.py::TestTruncation::test_outline_truncates_large_heading_list -v` | Returns capped heading list with truncation marker |
| `scripts/mcp/mdq/service.py` (grep_docs) | Unit test with pattern matching >max_grep_matches chunks | `uv run pytest tests/test_mdq_service.py::TestTruncation::test_grep_docs_truncates_at_match_cap -v` | Returns capped match list with truncation marker |
| `scripts/mcp/mdq/search.py` (search_docs) | Unit tests for both results-limit and char-limit paths | `uv run pytest tests/test_mdq_service.py -k "search_docs_truncat" -v` | Truncation messages include counts and narrowing suggestion |
| Full MDQ test suite | Regression check | `uv run pytest tests/test_mdq_service.py tests/test_mdq_hybrid_search.py tests/test_mdq_error_taxonomy.py -v` | All existing tests pass |

## Risks & Mitigations

- **Risk**: `OutlineRequest` field-name mismatch (`max_items` in model vs `max_outline_items` in tool schema) may silently ignore the per-request override today. Adding a new field could break existing callers using `max_items`. → **Mitigation**: Rename `max_items` → `max_outline_items` and verify no tests use the old name. Check `tests/test_mdq_service.py` for field name usage before renaming.
- **Risk**: Behavior-lock tests may not exist for current truncation paths, meaning any pre-existing bug in truncation logic is not caught. → **Mitigation**: Write behavior-lock tests in Phase 1 before making changes to capture current (possibly buggy) behavior, then update them to reflect the correct target behavior in Phase 2.
- **Risk**: `grep_docs` cannot report true total match count because scanning stops at `max_matches` (by design for performance). Reporting "N+ matches" may confuse users expecting an exact count. → **Mitigation**: Phrase the message as `[Truncated — cap of {max_matches} matches reached. Narrow pattern or add path filter.]` — avoids implying an exact total.
- **Risk**: Changing truncation message format may break tests that assert on exact output strings. → **Mitigation**: Search for `Truncated` in all test files before editing; update affected assertions in the same PR.
