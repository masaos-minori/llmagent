# Implementation: plugin audit — execution path analysis

## Goal

Trace plugin tool execution path in `tool_executor.py` and `plugin_tool_invoker.py` to determine where and how audit events should be emitted for plugin tools.

## Scope

- `scripts/shared/tool_executor.py`
- `scripts/shared/plugin_tool_invoker.py`
- `scripts/agent/tool_audit.py`

## Assumptions

1. Plugin tools are executed via `plugin_tool_invoker.py` and may or may not go through `tool_executor.py` audit path.
2. `audit_tool_exec()` in `tool_audit.py:169` returns early when `mcp_request_id` is empty (plugin tools have `request_id=""`).

## Implementation

### Target files

1. `scripts/shared/tool_executor.py`
2. `scripts/shared/plugin_tool_invoker.py`
3. `scripts/agent/tool_audit.py`

### Procedure

1. Read `tool_executor.py` to find the execution path for plugin tools (search for `plugin_tool_invoker` imports/calls).
2. Read `plugin_tool_invoker.py` to confirm whether it emits any audit events.
3. Read `tool_audit.py` to understand the `audit_tool_exec()` guard condition that skips plugin tools.
4. Determine insertion point: either add audit call in `plugin_tool_invoker.py` or modify `tool_executor.py` to pass `source="plugin"` for plugin tools.

### Details

- Document the exact line numbers of the guard condition and execution path.
- Recommend where to add the audit event emission.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Analysis complete | Manual review of 3 files | Identify exact insertion point |
