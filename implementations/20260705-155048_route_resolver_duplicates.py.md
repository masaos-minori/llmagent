# Implementation: shared/route_resolver.py — Return duplicate ownership info from build_discovery_map()

## Goal

Change `build_discovery_map()` to return `tuple[dict[str, str], dict[str, list[str]]]` so duplicate tool ownership is structured output, not just a log message.

## Scope

**In**: Change `build_discovery_map()` return type. Update all callers of `build_discovery_map()` in the codebase.

**Out**: Changes to `check_routing_drift_vs_live()` caller logic (handled in separate doc).

## Assumptions

1. Current `build_discovery_map()` returns `dict[str, str]` (route_map).
2. It already logs duplicate warnings but doesn't return duplicate info.
3. Callers to update: `check_routing_drift_vs_live()` in `repl_health.py` (and any test mocks).
4. `server_tool_lists` param: `dict[str, list[dict[str, object]]]` with tool dict having `name` key.

## Implementation

### Target file
`scripts/shared/route_resolver.py`

### Procedure
1. Update `build_discovery_map()` to build `all_claims` dict.
2. Change return to `(route_map, duplicates)`.
3. Update type annotation.

### Method

**Updated `build_discovery_map()`:**
```python
def build_discovery_map(
    server_tool_lists: dict[str, list[dict[str, object]]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates
```

### Details

- `all_claims` tracks all claims before filtering to `> 1` at the end.
- `route_map` still uses first-wins semantics for backward compatibility.
- Callers unpacking with `route_map = build_discovery_map(...)` will break — must change to `route_map, _ = build_discovery_map(...)` or `route_map, duplicates = build_discovery_map(...)`.

## Validation plan

- `uv run pytest tests/ -v -k "route_resolver or duplicate_ownership"` — all pass.
- Verify: single server, no duplicates → `duplicates == {}`.
- Verify: two servers claim same tool → `duplicates == {"tool": ["srv1", "srv2"]}`.
- `mypy scripts/shared/route_resolver.py` — no new errors.
- `ruff check scripts/shared/route_resolver.py` — 0 errors.
