# Implementation Procedure: per-server snapshot count tests (tests/test_tool_registry_counts.py)

## Goal

Complete per-server snapshot-test coverage for all 10 registered MCP server groups (today only
`rag_pipeline` and `github` are covered), plus a direct assertion on `get_servers()`'s full key list,
so that any future addition/removal of a tool without a corresponding test update fails CI with a
clear, server-specific message.

## Scope

**In-Scope:**
- `tests/test_tool_registry_counts.py`: add 8 missing per-server tool-count test methods for
  `file_read` (9), `file_write` (4), `file_delete` (2), `cicd` (4), `mdq` (9), `git` (10), `shell` (1),
  `web_search` (1)
- Add one `get_servers()` test asserting the full sorted list of 10 server keys

**Out-of-Scope:**
- `shared/tool_constants.py` — no changes; it is the already-verified source of truth these tests
  check against
- `tests/test_tool_constants.py` — already exists and covers a different concern (frozenset
  disjointness/non-emptiness); no changes needed
- The two existing `rag_pipeline`/`github` test classes — unchanged, used only as the style template
- Any change to `_populate_default_registry()`'s registration order or the 10 server_key names

## Assumptions

- Exact expected counts (computed directly from `shared/tool_constants.py`'s 10 frozensets at planning
  time via `PYTHONPATH=scripts uv run python -c "..."`): `file_read=9, file_write=4, file_delete=2,
  rag_pipeline=4, cicd=4, mdq=9, git=10, shell=1, github=21, web_search=1`, total `65`. These are
  stable and already confirmed correct by the two existing assertions (`rag_pipeline==4`,
  `github==21`, `total==65`) in this same file.
- `ToolRegistry.get_servers()` already returns `sorted(self._by_server.keys())` (no code change
  needed) — this doc adds only a test, not an implementation change.
- Every test in this file follows the existing pattern: import `_reset_registry_for_testing` and
  `get_registry` from `shared.tool_registry` inside the test method, call `_reset_registry_for_testing()`
  first, then `get_registry()`.

## Implementation

### Target file

`tests/test_tool_registry_counts.py`

### Procedure

1. Add a new test class (or classes) mirroring the existing `TestRegistryRagPipelineCounts` pattern —
   one test method per remaining server group listed above.
2. Each test method:
   - Imports `_reset_registry_for_testing, get_registry` from `shared.tool_registry` locally (matching
     existing style in this file).
   - Calls `_reset_registry_for_testing()` then `get_registry()`.
   - Calls `registry.get_tool_names(<server_key>)` and asserts `len(tools) == <expected count>`.
   - Uses a failure message in the existing style: `f"Expected {N} {server_key} tools, got {tools}"`.
3. Add one additional test method `test_get_servers_returns_all_ten_keys` (can live in the same new
   class or `TestRegistryTotalCounts`) that:
   - Resets and fetches the registry as above.
   - Asserts `registry.get_servers() == [<sorted list of the 10 server keys>]`, with keys sorted
     alphabetically: `["cicd", "file_delete", "file_read", "file_write", "git", "github", "mdq",
     "rag_pipeline", "shell", "web_search"]`.
   - Uses a failure message stating the expected list and the actual list observed.

### Method

Plain pytest test-class/test-method additions — no fixtures, no parametrization needed (matches the
existing file's un-parametrized, one-assertion-per-method style). No production code changes.

### Details

Illustrative structure (signatures/pseudocode only — do not write this code in this design step):

```python
class TestRegistryServerGroupCounts:
    def test_file_read_tool_count(self) -> None:
        from shared.tool_registry import _reset_registry_for_testing, get_registry
        _reset_registry_for_testing()
        registry = get_registry()
        tools = registry.get_tool_names("file_read")
        assert len(tools) == 9, f"Expected 9 file_read tools, got {tools}"

    # ... repeat for file_write=4, file_delete=2, cicd=4, mdq=9, git=10, shell=1, web_search=1

    def test_get_servers_returns_all_ten_keys(self) -> None:
        from shared.tool_registry import _reset_registry_for_testing, get_registry
        _reset_registry_for_testing()
        registry = get_registry()
        expected = [
            "cicd", "file_delete", "file_read", "file_write", "git",
            "github", "mdq", "rag_pipeline", "shell", "web_search",
        ]
        assert registry.get_servers() == expected, (
            f"Expected server keys {expected}, got {registry.get_servers()}"
        )
```

Notes for the implementer:
- Keep one assertion focus per test method (matches existing style — do not combine multiple server
  checks into one method).
- Each failure message must name the exact server key and the observed list/count, per the plan's
  Acceptance Criteria ("Test failure messages clearly indicate which count, server key, or ordering
  assumption drifted").
- This file's tests are unaffected by the Phase 1 `get_tool_names()` sorted-order change (Assumption:
  counts are order-independent — `len()` of a list is unchanged whether sorted or not).

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_tool_registry_counts.py` | 0 errors |
| Tests | `uv run pytest tests/test_tool_registry_counts.py tests/test_tool_constants.py -v` | All pass, including the 9 new tests (8 per-server + `get_servers()`) |
| Docs consistency | `uv run python tools/check_docs_consistency.py` (or `uv run check-mcp-docs`) | Passes — tool-count check verifies against the canonical frozensets |
| Manual count re-verify | `PYTHONPATH=scripts uv run python -c "from shared.tool_registry import get_registry; r = get_registry(); print(len(r.get_all_tool_names())); [print(k, len(r.get_tool_names(k))) for k in r.get_servers()]"` | Matches the 10 counts recorded in the plan's Assumption 1 exactly |
