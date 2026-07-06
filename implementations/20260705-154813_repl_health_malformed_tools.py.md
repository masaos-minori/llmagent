# Implementation: agent/repl_health.py — Validate /v1/tools response schema

## Goal

Add `_validate_tools_response()` helper to classify malformed `/v1/tools` responses explicitly, and apply it in `_collect_server_tool_names()` and `_collect_server_tool_names_per_server()`.

## Scope

**In**: New `_validate_tools_response()` function. Update both collector functions. Wrap `resp.json()` in `try/except ValueError`.

**Out**: Changes to `check_routing_drift_vs_live()`, strict mode behavior (already handled), other functions.

## Assumptions

1. `_collect_server_tool_names()` line 163: `server_names.update(t["name"] for t in resp.json().get("tools", []))` — no validation.
2. `_collect_server_tool_names_per_server()` line 198: same pattern.
3. `resp.json()` may raise `ValueError`/`json.JSONDecodeError` on invalid JSON — currently uncaught.
4. Malformed servers are added to `unreachable` list — existing strict mode logic handles them correctly.
5. 7 malformed cases: not JSON, not dict, missing `tools`, `tools` not list, entry not dict, no `name`, empty `name`.

## Implementation

### Target file
`scripts/agent/repl_health.py`

### Procedure
1. Add `_validate_tools_response()` helper before the collector functions.
2. Update `_collect_server_tool_names()` to use it.
3. Update `_collect_server_tool_names_per_server()` to use it.

### Method

**New helper:**
```python
def _validate_tools_response(
    server_key: str, body: object
) -> tuple[list[str], str | None]:
    """Validate /v1/tools response. Returns (tool_names, error_msg).

    error_msg is None on success; a descriptive string if malformed.
    """
    if not isinstance(body, dict):
        return [], f"{server_key}: /v1/tools response is not a JSON object (got {type(body).__name__})"
    tools = body.get("tools")
    if tools is None:
        return [], f"{server_key}: /v1/tools response missing 'tools' field"
    if not isinstance(tools, list):
        return [], f"{server_key}: /v1/tools 'tools' must be a list (got {type(tools).__name__})"
    names: list[str] = []
    for i, entry in enumerate(tools):
        if not isinstance(entry, dict):
            return [], f"{server_key}: /v1/tools tools[{i}] is not an object"
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            return [], f"{server_key}: /v1/tools tools[{i}] has invalid name {name!r}"
        names.append(name)
    return names, None
```

**Updated `_collect_server_tool_names()` inner block (replace lines 161-163):**
```python
try:
    body_data: object = resp.json()
except ValueError as e:
    msg = f"{key}: /v1/tools response is not valid JSON: {e}"
    logger.warning("Malformed /v1/tools: %s", msg)
    unreachable.append(key)
    continue
names, err_msg = _validate_tools_response(key, body_data)
if err_msg:
    logger.warning("Malformed /v1/tools: %s", err_msg)
    unreachable.append(key)
else:
    server_names.update(names)
```

**Same pattern applied in `_collect_server_tool_names_per_server()`.**

### Details

- Using `continue` to skip malformed server within the for loop.
- Both functions preserve existing `unreachable.append(key)` semantics — callers that check for all-unreachable conditions work unchanged.
- `name.strip()` handles whitespace-only names.

## Validation plan

- `uv run pytest tests/ -v -k "malformed or v1_tools"` — all pass.
- Verify: non-JSON response → `unreachable` list includes server key.
- Verify: missing `tools` → malformed warning, server in `unreachable`.
- Verify: valid response → names extracted correctly.
- `mypy scripts/agent/repl_health.py` — no new errors.
- `ruff check scripts/agent/repl_health.py` — 0 errors.
