# Implementation: Document ToolCallResult fields and add plugin_contract to error_type (scripts/shared/transport_dto.py)

## Goal

Expand the field-level comments on `ToolCallResult` in `scripts/shared/transport_dto.py` so that:
- the `error_type` comment lists `"plugin_contract"` as a valid value (currently missing, even though `plugin_tool_invoker.py` sets it in 3 return branches)
- every field on the dataclass has an explicit comment describing its meaning and per-source-type conventions

## Scope

**In-Scope:**
- `scripts/shared/transport_dto.py::ToolCallResult` — comment/documentation changes only, on fields: `output`, `is_error`, `request_id`, `server_key`, `source`, `error_type`

**Out-of-Scope:**
- Any change to field names, types, defaults, or the `from_transport()` classmethod's behavior
- Any change to `TransportErrorInfo` or any other class in this file
- Any change to `plugin_tool_invoker.py` (already correctly sets `error_type="plugin_contract"`; not touched here)

## Assumptions

1. Current state of `ToolCallResult` (confirmed by direct read of `scripts/shared/transport_dto.py`):
   ```python
   @dataclass(frozen=True)
   class ToolCallResult:
       """Typed result from a single tool call execution."""

       output: str
       is_error: bool
       request_id: str  # x-request-id from HTTP transport; "" for plugin/cache
       server_key: str  # server key that handled the call; "" for plugin tools
       source: str = (
           ""  # "mcp" for MCP tools, "plugin" for plugin tools, "" for cache/error paths
       )
       error_type: str = ""  # "transport" | "tool" | "" (empty on success)
   ```
   Only `output` and `is_error` currently have no inline comment at all; `error_type`'s comment omits `"plugin_contract"`.
2. This is a comment-only change (per the plan's Affected areas table: "Blast radius: None (comment-only)"). No behavior, type, or runtime change results from this edit.
3. `plugin_tool_invoker.py` (not modified here) already sets `error_type="plugin_contract"` in its 3 contract-violation return branches — this doc only brings the DTO's own comment in line with that already-correct runtime behavior.

## Implementation

### Target file

`scripts/shared/transport_dto.py`

### Procedure

1. Open `scripts/shared/transport_dto.py` and locate the `ToolCallResult` dataclass body.
2. Add an inline comment to `output: str` describing its dual role (tool result text on success, error message when `is_error=True`).
3. Add an inline comment to `is_error: bool` describing what it flags.
4. Leave `request_id` and `server_key` comments as-is (already documented).
5. Leave `source`'s comment as-is (already documented; do not add `"cache"` — out of scope per the plan).
6. Update `error_type`'s comment to add `"plugin_contract"` to the enumerated values, in the position matching where it is set in code (between `"tool"` and the empty-string case, since `plugin_contract` and `tool` are both error paths).
7. Save the file. No import changes, no logic changes.

### Method

Target end state for the dataclass body (comments only; no field/type/default changes):

```python
@dataclass(frozen=True)
class ToolCallResult:
    """Typed result from a single tool call execution."""

    output: str  # tool result text, or error message when is_error=True
    is_error: bool  # True if the call failed (transport, tool, or plugin-contract error)
    request_id: str  # x-request-id from HTTP transport; "" for plugin/cache
    server_key: str  # server key that handled the call; "" for plugin tools
    source: str = (
        ""  # "mcp" for MCP tools, "plugin" for plugin tools, "" for cache/error paths
    )
    error_type: str = (
        ""  # "transport" | "tool" | "plugin_contract" | "" (empty on success)
    )
```

### Details

- Do not reorder fields (dataclass field order affects positional construction elsewhere in the codebase; keep `output, is_error, request_id, server_key, source, error_type`).
- Do not change `ruff format` line-wrapping conventions already used for `source`'s comment — apply the same parenthesized-comment style to `error_type` if line length requires it (project max line length is 120 chars per `rules/coding.md`).
- Comments must be in English only (per `rules/coding.md`: "Comments and log output: English only").
- No test file needs updating for this phase — it is a pure comment change with no observable behavior difference.

## Validation plan

Relevant subset of the plan's Validation plan table, filtered to this target file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/transport_dto.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/transport_dto.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |

No test run is required specifically for this file (no behavior change), but the full targeted test command from the plan should still be run once all phases are complete:
`uv run pytest tests/shared/test_plugin_tool_invoker.py tests/test_plugin_registry.py -v`
