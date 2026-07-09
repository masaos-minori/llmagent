# Implementation: plugin audit — audit event source standardization

## Goal

Set `source="plugin"` for plugin tool audit events and `source="mcp"` for MCP tool audit events. Remove the early-return guard that suppresses plugin tool audit. Document that plugin events have empty `server_key` and `request_id`.

## Scope

- `scripts/agent/tool_audit.py` — modify `audit_tool_exec()` guard and set source field
- `scripts/shared/tool_executor.py` — pass source parameter for plugin tools
- `scripts/shared/plugin_tool_invoker.py` — add audit call (if not called from tool_executor)

## Assumptions

1. `ToolExecEvent.source` default is `"agent"` (models.py:56).
2. Plugin tools have empty `request_id` and `server_key`.
3. Analysis phase has determined the correct insertion point.

## Implementation

### Target files

1. `scripts/agent/tool_audit.py`
2. `scripts/shared/tool_executor.py`
3. `scripts/shared/plugin_tool_invoker.py`

### Procedure

1. In `tool_audit.py`: modify the guard so plugin tools (source="plugin") bypass the `mcp_request_id` early-return.
2. In `tool_executor.py` or `plugin_tool_invoker.py`: set `source="plugin"` when calling `audit_tool_exec()` for plugin tools.
3. In `tool_audit.py`: set `source="mcp"` for MCP tool paths (or keep backward-compatible default).
4. Document that plugin audit events have `server_key=""` and `request_id=""`.

### Method

```python
# In audit_tool_exec():
if source == "agent" and not mcp_request_id:
    return  # only suppress default-source tools without request_id
```

### Details

- Do not break existing log parsers: add `source` as a new field without removing old behavior.
- Plugin tool audit events will have `source="plugin"`, `server_key=""`, `request_id=""`.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Plugin audit emits | `uv run pytest tests/test_plugin_contract.py -v` | Pass |
| MCP audit unchanged | `uv run pytest tests/test_tool_audit.py -v` | Pass |
