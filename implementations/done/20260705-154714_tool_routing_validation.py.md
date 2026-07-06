# Implementation: shared/tool_routing_validation.py — Add check_tool_safety_tiers()

## Goal

Add `check_tool_safety_tiers()` to detect registered tools that lack a declared safety tier in `tool_safety_tiers` config.

## Scope

**In**: New function `check_tool_safety_tiers()`. Export in module.

**Out**: Changes to `validate_routing_against_config()`, `validate_routing_against_live()`, `validate_all_routing()`.

## Assumptions

1. `tool_routing_validation.py` currently has 3 functions: `validate_routing_against_config()`, `validate_routing_against_live()`, `validate_all_routing()`.
2. `tool_safety_tiers: dict[str, str]` is the config dict mapping tool_name → tier.
3. An empty `tool_safety_tiers` dict means no tiers are declared → return empty list (nothing to check).
4. The function uses `get_registry()` to get all registered tool names.

## Implementation

### Target file
`scripts/shared/tool_routing_validation.py`

### Procedure
1. Add `check_tool_safety_tiers()` function after `validate_all_routing()`.

### Method

```python
def check_tool_safety_tiers(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return warning messages for registered tools missing a safety tier declaration.

    Only checks when tool_safety_tiers is non-empty (i.e., tier declarations are in use).
    Returns empty list when tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    if registry is None:
        from shared.tool_registry import get_registry
        registry = get_registry()
    missing = [
        t for t in sorted(registry.get_all_tool_names())
        if t not in tool_safety_tiers
    ]
    return [
        f"Tool {t!r} registered in ToolRegistry but missing from tool_safety_tiers"
        for t in missing
    ]
```

### Details

- `sorted()` ensures deterministic output order.
- Only triggers when `tool_safety_tiers` is non-empty — avoids flooding warnings in environments that don't use tiers.
- Callers (`repl_health.check_routing_safety_tiers()`) decide severity.

## Validation plan

- `uv run pytest tests/ -v -k "safety_tier or routing_validation"` — all pass.
- Verify: all tools missing from non-empty `tool_safety_tiers` → messages returned.
- Verify: empty `tool_safety_tiers` → `[]` returned.
- Verify: all tools present in `tool_safety_tiers` → `[]` returned.
- `mypy scripts/shared/tool_routing_validation.py` — no new errors.
- `ruff check scripts/shared/tool_routing_validation.py` — 0 errors.
