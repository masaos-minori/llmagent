# Implementation Procedure: Fix enabled_for_llm wiring gap in MCP tool discovery

## Goal

Fix critical wiring gap where `enabled_for_llm` is never passed from MCP tool discovery into `build_runtime_tool()`, causing ALL discovered tools to have `enabled_for_llm=False` and be filtered out of the LLM-facing tool list.

## Scope

- `scripts/agent/services/mcp_tool_discovery.py` — add `enabled_for_llm=bool(entry.get("enabled", True))` to `build_runtime_tool()` call in `_dedupe_and_build()`
- `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` — update implementation status text
- Tests — add unit/integration tests for `enabled_for_llm` wiring

## Assumptions

1. `enabled` field defaults to `True` if absent from `/v1/tools` response (backward compatibility with servers that don't send it yet)
2. The `disabled_reason` field is preserved for diagnostics but does not affect `enabled_for_llm` computation
3. No existing tests directly verify `enabled_for_llm` values on discovered tools

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py`

### Procedure

1. Locate `_dedupe_and_build()` method in `mcp_tool_discovery.py` at approximately lines 311-322
2. Find the `build_runtime_tool()` call and add `enabled_for_llm=bool(entry.get("enabled", True))`:
   ```python
   built[name] = build_runtime_tool(
       name=name,
       server_key=server_key,
       server_url=server_url,
       description=str(entry.get("description", "")),
       input_schema=entry.get("inputSchema", entry.get("input_schema")),
       raw_definition=entry,
       status=str(entry.get("status", "active")),
       is_write=entry.get("is_write"),
       requires_serial=entry.get("requires_serial"),
       enabled_for_llm=bool(entry.get("enabled", True)),  # NEW
       capabilities=tuple(entry.get("capabilities", []) or []),
   )
   ```

3. Update `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` line 22: change "not yet implemented in MCP server responses" to "implemented in MCP server responses AND wired into RuntimeToolRegistry at discovery time"

4. Add tests covering:
   - `enabled=true` → `enabled_for_llm=True`
   - `enabled=false` → `enabled_for_llm=False`
   - Missing `enabled` field → defaults to `True` (backward compatibility)
   - Integration test: MCP server returns disabled tool → discovery reads `enabled=false` → LLM cannot invoke the disabled tool

### Method

Use targeted edit to add one parameter to the existing `build_runtime_tool()` call. The `enabled_for_llm` parameter already exists in `build_runtime_tool()` with default `None`. By passing `bool(entry.get("enabled", True))`, we set it to `True` by default for backward compatibility.

### Details

- Blast radius: High — this is a production-blocking issue; every discovered tool will change its `enabled_for_llm` value from `False` to `True` (or whatever the server reports)
- Zero churn on this specific code path (the bug has been present since the feature was implemented); no existing tests cover this behavior
- Deploy impact: None — no config changes needed; fix takes effect immediately upon deployment

## Validation plan

1. Run specific tests: `uv run pytest tests/test_mcp_tool_discovery.py`
2. Run type check: `uv run mypy scripts/agent/services/mcp_tool_discovery.py`
3. Run lint: `uv run ruff check scripts/agent/services/mcp_tool_discovery.py`
4. Run full test suite: `uv run pytest`
