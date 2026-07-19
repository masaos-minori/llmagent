# Implementation: tests/test_mdq_tool_layer_consistency.py (new — guardrail tests for MDQ tool-layer alignment)

Source plan: `plans/20260716-123746_plan.md`

## Goal

Add a new test module that fails immediately if any future change adds or
removes an MDQ tool in `TOOL_LIST`, `_DISPATCH_TABLE`, `MDQ_TOOLS`, or
`ToolRegistry` without keeping all four in sync — the same class of drift
that `plans/done/20260716-123031_plan.md` fixed for the
`fts_consistency_check`/`fts_rebuild` case.

## Scope

**In:**
- Create `tests/test_mdq_tool_layer_consistency.py` with 6 test functions
  (per Design in the source plan):
  1. `test_tool_list_subset_of_dispatch_table`
  2. `test_dispatch_table_subset_of_tool_list`
  3. `test_mdq_tools_matches_tool_list`
  4. `test_mdq_tools_registered_in_registry`
  5. `test_write_tools_flagged_is_write`
  6. `test_serial_tools_flagged_requires_serial`

**Out:**
- Live `/v1/tools` drift validation against `ToolRegistry` — already
  generically covered by `shared/tool_routing_validation.py`'s
  `validate_routing_against_live`; do not duplicate it here.
- Generalizing this guardrail pattern to other MCP servers (github, shell,
  git, cicd, rag_pipeline, sqlite, file) — explicitly out of scope per the
  source plan; flagged there as a candidate follow-up requirement only.
- Any change to production code (`tools.py`, `server.py`,
  `tool_constants.py`, `tool_registry.py`) — this is a test-only addition.

## Assumptions

1. This test module must be written against the **post-removal** MDQ state
   (7 tools, no `fts_consistency_check`/`fts_rebuild` anywhere) — confirmed
   via direct read: `scripts/mcp_servers/mdq/server.py:167-175`'s
   `_DISPATCH_TABLE` already has exactly 7 entries
   (`search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`,
   `stats`, `grep_docs`), and `scripts/mcp_servers/mdq/tools.py:95-126`
   confirms `index_paths`/`refresh_index` are the only two entries with
   `"is_write": True, "requires_serial": True`. This confirms
   `plans/done/20260716-123031_plan.md`'s removal has already landed in the
   source tree (companion implementation docs for that plan cover the
   removal itself) — this guardrail can be safely written against the
   current 7-tool state without rework.
2. `ToolRegistry.get_tool_names(server_key: str) -> list[str]` exists at
   `scripts/shared/tool_registry.py:80` and `get_registry() -> ToolRegistry`
   exists at line 166 — both verified by direct read, matching the Design
   section's import (`from shared.tool_registry import get_registry`).
3. `MDQ_WRITE_TOOLS` (from `scripts/shared/tool_constants.py`, after the
   companion `tool_constants.py` doc for plan 02 lands) is
   `{"index_paths", "refresh_index"}` — exactly the two tools with
   `is_write`/`requires_serial` both `True` in `TOOL_LIST`.
4. No existing test in `tests/` checks `_DISPATCH_TABLE` consistency for
   any MCP server — confirmed via `rg -n "_DISPATCH_TABLE" tests/`. This is
   a net-new coverage area, not a duplicate.

## Implementation

### Target file

`tests/test_mdq_tool_layer_consistency.py` (new file)

### Procedure

1. Create `tests/test_mdq_tool_layer_consistency.py` with a module
   docstring describing its purpose (guardrail against MDQ tool-layer
   drift across schema/dispatch/registry/config).
2. Add imports:
   ```python
   from __future__ import annotations

   from mcp_servers.mdq.mdq_server import _DISPATCH_TABLE
   from mcp_servers.mdq.mdq_tools import TOOL_LIST
   from shared.tool_constants import MDQ_TOOLS, MDQ_WRITE_TOOLS
   from shared.tool_registry import get_registry
   ```
3. Add the 6 test functions exactly as specified in the source plan's
   Design section:
   ```python
   def test_tool_list_subset_of_dispatch_table() -> None:
       schema_names = {t["name"] for t in TOOL_LIST}
       assert schema_names <= set(_DISPATCH_TABLE)


   def test_dispatch_table_subset_of_tool_list() -> None:
       schema_names = {t["name"] for t in TOOL_LIST}
       assert set(_DISPATCH_TABLE) <= schema_names


   def test_mdq_tools_matches_tool_list() -> None:
       assert MDQ_TOOLS == {t["name"] for t in TOOL_LIST}


   def test_mdq_tools_registered_in_registry() -> None:
       registry = get_registry()
       assert set(registry.get_tool_names("mdq")) == MDQ_TOOLS


   def test_write_tools_flagged_is_write() -> None:
       for t in TOOL_LIST:
           if t["name"] in MDQ_WRITE_TOOLS:
               assert t.get("is_write") is True


   def test_serial_tools_flagged_requires_serial() -> None:
       for t in TOOL_LIST:
           if t["name"] in MDQ_WRITE_TOOLS:
               assert t.get("requires_serial") is True
   ```
4. Add return-type annotations (`-> None`) to every test function per
   `rules/coding.md` mypy conventions (already included above).
5. Verify `get_registry()`'s `"mdq"` server key matches the key used
   elsewhere for this server (cross-check against
   `scripts/shared/route_resolver.py` or wherever `ToolRouteResolver`
   resolves MDQ tools to confirm the string literal `"mdq"` is the correct
   registry key, not e.g. `"mdq-mcp"` or `"mdq_mcp_server"`).

### Method

New pytest module, plain `assert`-based tests with no fixtures — each test
imports the real production modules directly (no mocking), matching the
Design section's explicit intent ("no mocking") so a future edit to any one
layer trips the corresponding test.

### Details

- Do not add parametrization or a shared fixture across the 6 tests — each
  is independent and imports its own dependencies at module level (the
  Design section's plain function style, not class-based).
- Do not add tests beyond the 6 specified — the source plan explicitly
  scopes "generalizing this guardrail to every other MCP server" as out of
  scope; stick to MDQ only.
- Follow this file's module docstring convention to match other
  `tests/test_mdq_*.py` files (e.g. `test_mdq_metadata_consistency.py`'s
  triple-quoted module docstring listing what is verified).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New tests pass | `uv run pytest tests/test_mdq_tool_layer_consistency.py -v` | 6 passed |
| Regression proof (manual) | temporarily delete one `_DISPATCH_TABLE` entry in `server.py`, re-run the new test file, confirm `test_dispatch_table_subset_of_tool_list` or `test_tool_list_subset_of_dispatch_table` fails, then revert | test fails as expected, then passes after revert |
| Lint | `uv run ruff check tests/test_mdq_tool_layer_consistency.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_tool_layer_consistency.py` | no new errors |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | all pass |
| Registry/constants suite | `uv run pytest tests/test_tool_registry.py tests/test_tool_constants.py -v` | all pass |
