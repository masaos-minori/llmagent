# Implementation: agent/startup.py — Wire routing_drift_strict into _check_services()

## Goal

Use `routing_drift_strict` from `ctx.cfg.tool` when calling `check_routing_drift()`, removing the hardcoded `[non-fatal]` prefix for strict mode, and add `check_routing_safety_tiers()` call.

## Scope

**In**: Update `_check_services()` lines 167-168. Add safety tier check call.

**Out**: Changes to `check_routing_drift()`, config dataclasses, or other checks.

## Assumptions

1. `startup.py:167` currently: `for msg in check_routing_drift(ctx): self._view.write_warning(f"[non-fatal] {msg}")`.
2. `routing_drift_strict` field is available at `ctx.cfg.tool.routing_drift_strict`.
3. When `routing_drift_strict=True`, `check_routing_drift()` raises — the exception propagates and startup fails.
4. `check_routing_safety_tiers()` returns `list[str]` — always non-fatal (add as warning).

## Implementation

### Target file
`scripts/agent/startup.py`

### Procedure
1. Import `check_routing_safety_tiers` from `agent.repl_health`.
2. Update `check_routing_drift()` call to pass `strict` flag.
3. Add `check_routing_safety_tiers()` call after routing drift check.

### Method

**Updated imports:**
```python
from agent.repl_health import (
    audit_security_defaults,
    check_readiness,
    check_routing_drift,
    check_routing_drift_vs_live,
    check_routing_safety_tiers,   # NEW
    check_tool_definitions_startup,
    check_workflow_definition,
)
```

**Updated `_check_services()` (lines ~167-172):**
```python
routing_strict = getattr(ctx.cfg.tool, "routing_drift_strict", False)
for msg in check_routing_drift(ctx, strict=routing_strict):
    prefix = "" if routing_strict else "[non-fatal] "
    self._view.write_warning(f"{prefix}{msg}")

# Safety tier check (always non-fatal)
for msg in check_routing_safety_tiers(ctx):
    self._view.write_warning(f"[non-fatal] {msg}")

strict = getattr(ctx.cfg.tool, "tool_definitions_strict", False)
drift_result = await check_routing_drift_vs_live(ctx, strict=strict)
```

### Details

- `getattr(..., False)` is a safe fallback if `routing_drift_strict` is not yet in config.
- When `routing_drift_strict=True` and drift exists, `check_routing_drift()` raises `RuntimeError` — the exception propagates from `_check_services()` to `StartupOrchestrator.run()`, aborting startup.

## Validation plan

- `uv run pytest tests/ -v -k "startup_routing or startup_check"` — all pass.
- Verify: `routing_drift_strict=True` + drift → startup raises.
- Verify: `routing_drift_strict=False` + drift → `[non-fatal]` warnings, no raise.
- `mypy scripts/agent/startup.py` — no new errors.
- `ruff check scripts/agent/startup.py` — 0 errors.
