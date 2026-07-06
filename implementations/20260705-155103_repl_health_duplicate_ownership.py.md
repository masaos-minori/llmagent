# Implementation: agent/repl_health.py — Use duplicate info in check_routing_drift_vs_live()

## Goal

Update `check_routing_drift_vs_live()` to unpack the new `(route_map, duplicates)` tuple from `build_discovery_map()`, add duplicate ownership warnings to `HealthCheckResult`, and raise in strict mode.

## Scope

**In**: Update `check_routing_drift_vs_live()` at line ~339. Update `build_discovery_map()` call.

**Out**: Changes to `build_discovery_map()` itself, health_models, or other functions.

## Assumptions

1. `check_routing_drift_vs_live()` currently: `route_map = build_discovery_map(...)`.
2. After Plan 16 Phase 1, `build_discovery_map()` returns `(route_map, duplicates)`.
3. `HealthCheckResult` has `warnings: list[ServiceWarning]`.
4. `ServiceWarning` is importable from `agent.shared.health_models`.
5. `get_registry()` returns the `ToolRegistry`; `registry.get_server_for_tool(name)` returns `str | None`.
6. `strict` parameter already exists on `check_routing_drift_vs_live()` — carries through from config.

## Implementation

### Target file
`scripts/agent/repl_health.py`

### Procedure
1. Change `route_map = build_discovery_map(...)` to `route_map, duplicates = build_discovery_map(...)`.
2. After building route_map, iterate `duplicates` and append to `HealthCheckResult.warnings`.
3. After populating warnings, check `if duplicates and strict: raise RuntimeError(...)`.

### Method

**Updated call site (replaces line ~339):**
```python
route_map, duplicates = build_discovery_map(
    {k: [{"name": n} for n in names] for k, names in per_server.items()}
)
```

**New block after `route_map` is built (insert before existing drift comparison):**
```python
from agent.shared.health_models import ServiceWarning  # (likely already imported)
from shared.tool_registry import get_registry

for tool_name, server_keys in duplicates.items():
    registry_owner = get_registry().get_server_for_tool(tool_name)
    msg = (
        f"Duplicate live tool ownership: {tool_name!r} claimed by {sorted(server_keys)}; "
        f"registry owner={registry_owner!r}"
    )
    logger.warning(msg)
    result.warnings.append(ServiceWarning(label="duplicate_ownership", url="", message=msg))

if duplicates and strict:
    raise RuntimeError(
        f"Strict mode: duplicate live tool ownership detected: {sorted(duplicates)}"
    )
```

### Details

- `sorted(server_keys)` ensures deterministic output in messages and error text.
- The raise happens after all duplicates are collected — operator sees the full list, not just the first.
- `ServiceWarning(label=..., url="", message=...)` — `url=""` since this is a routing warning, not a URL.

## Validation plan

- `uv run pytest tests/ -v -k "duplicate_ownership"` — all pass.
- Verify: no duplicates → no new warnings in `HealthCheckResult`.
- Verify: one duplicate → warning with tool name and server keys in message.
- Verify: strict mode + duplicate → `RuntimeError`.
- `mypy scripts/agent/repl_health.py` — no new errors.
- `ruff check scripts/agent/repl_health.py` — 0 errors.
