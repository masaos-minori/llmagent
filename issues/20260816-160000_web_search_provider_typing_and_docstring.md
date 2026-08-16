# `search_provider.py`: tighten internal dict type annotations and fix stale module docstring

## Priority
Low

## Summary
Two small, deferred cleanups from `scripts/mcp_servers/web_search/search_provider.py`'s
2026-08-16 refactor cycle:
1. The internal DuckDuckGo-result-handling helpers (`_validate_raw_items`,
   `_build_search_results`, and a nested sync-search function) use bare `dict` (implicitly
   `dict[Any, Any]`) parameter/return annotations rather than a more precise shape.
2. The module docstring's "Dependency direction" line references
   `mcp_servers.web_search.models`, but the actual import is
   `mcp_servers.web_search.web_search_models` — no module named `mcp_servers.web_search.models`
   exists.

## Reason for Change
(1) was deferred because the true shape of DDGS's (the `duckduckgo_search` library) return
payload is uncertain (fields could in principle be non-`str`), and tightening it wasn't
necessary to complete the extraction that motivated the original cycle.
(2) is a pure documentation-accuracy fix, out of scope for a cycle whose Core Rules prohibit
editing documentation unless explicitly instructed.

## Implementation Intent
For (1): read the `duckduckgo_search` library's actual return type (or its type stubs, if any)
to determine the true per-item shape before choosing a more precise annotation (e.g.
`dict[str, str]` or a `TypedDict`).
For (2): update the docstring's dependency-direction line to reference
`mcp_servers.web_search.web_search_models`.

## Target Files or Areas
- `scripts/mcp_servers/web_search/search_provider.py`

## Required Changes
- (1) Determine DDGS's actual per-result field types; update `_validate_raw_items`/
  `_build_search_results`'s bare `dict` annotations accordingly.
- (2) Fix the module docstring's stale module-path reference.

## Acceptance Criteria
- `mypy`/`pyright` pass with 0 new errors after the annotation tightening.
- The module docstring's dependency-direction line matches the actual import.
- `tests/mcp_servers/web_search/test_web_search_provider.py` (23 tests) pass unchanged.

## Testing Expectations
`mypy`/`pyright` on the file; `tests/mcp_servers/web_search/test_web_search_provider.py` full
suite (no behavior change expected from either fix).

## Documentation Impact
This issue's item (2) *is* a documentation fix. No further doc impact.

## Out of Scope
- Do not change any runtime logic in `search_duckduckgo` or `fetch_browser`.

## AI Implementation Instruction
These are two independent, very low-risk cleanups — implement both in one small commit. Confirm
the actual `duckduckgo_search` return shape (via its stubs or a live call) before choosing a
type, rather than guessing.
