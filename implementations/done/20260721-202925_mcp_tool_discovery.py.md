# Implementation Procedure: Wire enabled_for_llm from /v1/tools response into build_runtime_tool()

## Goal

Fix the critical gap where `enabled_for_llm` defaults to `False` because the `/v1/tools` response's `enabled` field is never read during tool discovery, causing ALL tools to be hidden from the LLM.

## Scope

- `scripts/agent/services/mcp_tool_discovery.py` — add `enabled_for_llm` parameter to `build_runtime_tool()` call in `_dedupe_and_build()`
- `scripts/shared/runtime_tool.py` — no changes needed (`enabled_for_llm` parameter already exists)
- `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` — update outdated statement about `enabled`/`disabled_reason` not being implemented
- Tests: `tests/test_mcp_tool_discovery*.py` — add test for `enabled_for_llm` wiring

## Assumptions

- `enabled` field in `/v1/tools` response is a boolean (or absent)
- When `enabled` is absent, tools should default to `enabled_for_llm=True` (backward compatible)
- `disabled_reason` is preserved for diagnostics but not exposed to LLM

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py`

### Procedure

1. Locate `_dedupe_and_build()` method in `mcp_tool_discovery.py`
2. Find the `build_runtime_tool()` call (currently passes 10 parameters)
3. Add `enabled_for_llm=bool(entry.get("enabled", True))` to the call:
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

4. Update `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` line 22 to reflect that `enabled`/`disabled_reason` ARE now implemented in MCP server responses AND wired into RuntimeToolRegistry.

5. Add tests covering:
   - `enabled=true` → `enabled_for_llm=True`
   - `enabled=false` → `enabled_for_llm=False`
   - Missing `enabled` field → defaults to `True` (backward compatibility)

### Method

Use targeted edit to add one parameter to the existing `build_runtime_tool()` call. The `enabled_for_llm` parameter already exists in `build_runtime_tool()` with default `None` (line 75 of `runtime_tool.py`). The current default is `False` when `enabled_for_llm=None` (line 102) — this is the bug. By passing `bool(entry.get("enabled", True))`, we set it to `True` by default for backward compatibility.

### Details

- `entry.get("enabled", True)` — default `True` for backward compatibility with servers not sending `enabled` yet
- `bool(...)` — cast to bool for type safety even though `entry.get()` may already return bool
- Blast radius: High — this fix restores correct behavior for all tools; previously hidden tools will become visible again

## Validation plan

1. Run specific tests: `uv run pytest tests/test_mcp_tool_discovery*.py`
2. Run type check: `uv run mypy scripts/agent/services/mcp_tool_discovery.py`
3. Run lint: `uv run ruff check scripts/agent/services/mcp_tool_discovery.py`
4. Run full test suite: `uv run pytest`
