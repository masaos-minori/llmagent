# Implementation: scripts/shared/transport_dto.py (update ToolCallResult field-comment docs)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 4)

Gap-filling note: fills the missing doc for plan Implementation step 4, which
had no `implementations/` doc despite being explicitly listed as its own
numbered step. Purely a comment/documentation edit — no dataclass shape
change, no import to remove, independent of every other step in this plan
(can land at any point in the sequence, before or after steps 1-3/5-9).

## Goal

`ToolCallResult`'s field comments no longer describe `"plugin"`/
`"plugin_contract"` as live semantics — they describe only `"mcp"`/`"cache"`/
`"transport"`/`"tool"` (the values still actually produced once the plugin
subsystem is gone).

## Scope

**In scope**: `scripts/shared/transport_dto.py` — reword the 4 field comments
on `ToolCallResult` (lines 13, 15, 16, 17, 19) that currently mention
`"plugin"`/`plugin-contract`/`plugin_contract` as an active value/source.

**Out of scope**: the dataclass's field names, types, or defaults — unchanged
per the plan's explicit "no dataclass shape change" note. `source`/`error_type`
remain plain `str` fields; this doc only edits the inline comments describing
what values they historically could hold.

## Assumptions

1. Confirmed by direct read (2026-07-17): the 4 comments are:
   - line 13: `bool  # True if the call failed (transport, tool, or plugin-contract error)`
   - line 15: `request_id: str  # x-request-id from HTTP transport; "" for plugin/cache`
   - line 16: `server_key: str  # server key that handled the call; "" for plugin tools`
   - line 17: `source: str = ""  # "mcp" for MCP tools, "plugin" for plugin tools, "cache" for cache hits, "" for error paths`
   - line 19: `""  # "transport" | "tool" | "plugin_contract" | "" (empty on success)`
2. No production code constructs a `ToolCallResult` with `source="plugin"` or `error_type="plugin_contract"` once `plugin_tool_invoker.py` is deleted (step 2, sibling doc) — those were the only two call sites producing those specific string values (confirmed via `grep -rn 'source="plugin"\|error_type="plugin_contract"' scripts/` returning only `plugin_tool_invoker.py`, which is deleted). This doc's comment update is purely descriptive cleanup, matching reality post-removal — it does not need to run in any particular order relative to the step-2 file deletions to be *correct*, though running it after is slightly more natural (comments describe the post-removal state).
3. `source`/`error_type` remain generic `str` fields (not `Literal[...]`) so no type-checking implication from this comment-only change — mypy is unaffected either way.

## Implementation

### Target file

`scripts/shared/transport_dto.py`

### Procedure

1. Reword line 13's comment from:
   ```python
   bool  # True if the call failed (transport, tool, or plugin-contract error)
   ```
   to:
   ```python
   bool  # True if the call failed (transport or tool error)
   ```
2. Reword line 15's comment from:
   ```python
   request_id: str  # x-request-id from HTTP transport; "" for plugin/cache
   ```
   to:
   ```python
   request_id: str  # x-request-id from HTTP transport; "" for cache hits
   ```
3. Reword line 16's comment from:
   ```python
   server_key: str  # server key that handled the call; "" for plugin tools
   ```
   to:
   ```python
   server_key: str  # server key that handled the call
   ```
   (drop the `"" for plugin tools` qualifier; if any other case still legitimately produces an empty `server_key`, e.g. cache hits, confirm and reword to reflect that instead — check `_execute_with_cache()`/`_raw_execute()` in `tool_executor.py` for what they actually set `server_key` to on a cache hit before finalizing this specific wording).
4. Reword line 17's comment from:
   ```python
   source: str = ""  # "mcp" for MCP tools, "plugin" for plugin tools, "cache" for cache hits, "" for error paths
   ```
   to:
   ```python
   source: str = ""  # "mcp" for MCP tools, "cache" for cache hits, "" for error paths
   ```
5. Reword line 19's comment from:
   ```python
   ""  # "transport" | "tool" | "plugin_contract" | "" (empty on success)
   ```
   to:
   ```python
   ""  # "transport" | "tool" | "" (empty on success)
   ```

### Method

Comment-only edits, one field at a time — no logic, type, or default-value change anywhere in this file.

### Details

- Do not add a `Literal[...]` type or any runtime validation to `source`/`error_type` — the plan explicitly scopes this as a documentation-only change; introducing a stricter type would be scope creep beyond what was planned.
- Double-check step 3's wording claim in Procedure step 3 (whether `""` is actually still produced by a real case like cache hits) against the current `tool_executor.py`/`http_transport.py` code before finalizing — do not leave a comment that's simply wrong in a different way than before.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No plugin references remain in this file | `grep -n "plugin" scripts/shared/transport_dto.py` | 0 matches |
| Syntax/lint | `uv run ruff check scripts/shared/transport_dto.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/transport_dto.py` | no new errors (comment-only change, should be a no-op for mypy) |
| No behavior change | `uv run pytest tests/ -k transport_dto -v` (or the relevant existing test file covering `ToolCallResult`, confirm its name at implementation time) | all pass, unchanged from before this edit |
