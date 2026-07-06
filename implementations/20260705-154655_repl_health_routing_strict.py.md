# Implementation: agent/repl_health.py — Extend check_routing_drift() with strict mode and add safety tier check

## Goal

Add `strict: bool = False` parameter to `check_routing_drift()` so startup can raise on drift. Wire to `check_routing_drift_vs_live()` for safety tier check call.

## Scope

**In**: Add `strict` parameter to `check_routing_drift()`. Add call to `check_tool_safety_tiers()` in a new `check_routing_safety_tiers()` wrapper.

**Out**: Changes to `_collect_server_tool_names*()`, `build_discovery_map()`, watchdog.

## Assumptions

1. `check_routing_drift()` at `repl_health.py:411` currently returns `list[str]` and never raises.
2. Adding `strict=False` default is backward-compatible.
3. `check_tool_safety_tiers()` will be defined in `tool_routing_validation.py` (separate doc).
4. A new `check_routing_safety_tiers()` function wraps the call with `AgentContext`.

## Implementation

### Target file
`scripts/agent/repl_health.py`

### Procedure
1. Update `check_routing_drift()` signature to add `strict: bool = False`.
2. Add strict mode raise after collecting drift messages.
3. Add `check_routing_safety_tiers()` function calling the new validation helper.

### Method

**Updated `check_routing_drift()`:**
```python
def check_routing_drift(ctx: AgentContext, *, strict: bool = False) -> list[str]:
    from shared.tool_routing_validation import validate_routing_against_config
    try:
        server_configs = ctx.cfg.mcp.mcp_servers
        drift = validate_routing_against_config(server_configs=server_configs)
        warnings: list[str] = []
        for server_key, messages in drift.items():
            for msg in messages:
                full_msg = f"Routing drift [{server_key}]: {msg}"
                logger.warning(full_msg)
                warnings.append(full_msg)
        if drift and strict:
            drift_str = "; ".join(f"{sk}: {msgs}" for sk, msgs in drift.items())
            msg = f"Strict mode: routing drift detected. Drift: {drift_str}."
            logger.error(msg)
            raise RuntimeError(msg)
        return warnings
    except RuntimeError:
        raise
    except Exception as exc:
        logger.warning("Routing drift check failed: %s", exc)
        return []
```

**New `check_routing_safety_tiers()`:**
```python
def check_routing_safety_tiers(ctx: AgentContext) -> list[str]:
    """Check that all registered tools have a declared safety tier. Returns warning messages."""
    from shared.tool_routing_validation import check_tool_safety_tiers
    tool_safety_tiers = getattr(ctx.cfg.approval, "tool_safety_tiers", {})
    return check_tool_safety_tiers(tool_safety_tiers=tool_safety_tiers)
```

### Details

- The `except RuntimeError: raise` ensures strict mode `RuntimeError` propagates through the broad `except Exception`.
- `check_routing_safety_tiers()` is non-fatal by design; callers decide whether to treat missing tiers as warnings or errors.

## Validation plan

- `uv run pytest tests/ -v -k "routing_drift"` — all pass.
- Verify: `check_routing_drift(ctx, strict=True)` raises on drift.
- Verify: `check_routing_drift(ctx, strict=False)` returns warnings.
- `mypy scripts/agent/repl_health.py` — no new errors.
- `ruff check scripts/agent/repl_health.py` — 0 errors.
