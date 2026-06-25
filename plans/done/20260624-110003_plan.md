# Design Doc: Plugin Registry — Strict Mode Tool Conflict Rejection

**Plan:** `plans/20260623-141242_plan.md` (Phase 1)
**Status:** In Progress

---

## Goal

Add `strict_mode` parameter to `_validate_tool_conflicts()` so that MCP tool-conflict rejection raises `PluginLoadError` in strict mode, preserving the "load all, then raise once" contract.

---

## Scope

**In:**
- `scripts/shared/plugin_registry.py` — modify `_validate_tool_conflicts()` signature and return type; update `load_plugins()` to unpack new return value and include strict_rejected names in PluginLoadError

**Out:**
- Changing existing callers outside `load_plugins()` (only one call site)
- Modifying `PluginLoadResult` dataclass (count remains accurate)

---

## Assumptions

1. Only one call site of `_validate_tool_conflicts()`: `load_plugins()` at line 343.
2. The "load all, then raise once" contract must be preserved — tool conflicts should not raise directly inside `_validate_tool_conflicts()`, but return rejected names for aggregation in `load_plugins()`.
3. `override_policy="reject"` (default) already removes shadowing tools silently; the gap is that this removal doesn't raise in strict mode.

---

## Implementation

### Target file: `scripts/shared/plugin_registry.py`

### Procedure

1. Change `_validate_tool_conflicts()` signature to accept `strict_mode` parameter
2. Collect rejected tool names when `strict_mode=True` in the reject branch
3. Return 3-tuple `(shadowed_count, allowed_count, strict_rejected)` instead of 2-tuple
4. Update `load_plugins()` to unpack 3-tuple and include `strict_rejected` in PluginLoadError

### Method

#### Change 1: `_validate_tool_conflicts()` signature and return type

**Before:**
```python
def _validate_tool_conflicts(
    known_tools: frozenset[str],
    override_policy: str,
) -> tuple[int, int]:
```

**After:**
```python
def _validate_tool_conflicts(
    known_tools: frozenset[str],
    override_policy: str,
    strict_mode: bool = False,
) -> tuple[int, int, list[str]]:
    """Returns (shadowed_count, allowed_count, strict_rejected_names)."""
```

#### Change 2: Collect rejected names in reject branch

**Before:**
```python
else:
    del _tools[tool_name]
    shadowed_count += 1
    logger.info(
        "[plugin] conflict: tool '%s' in '%s' shadows MCP tool — rejected",
        tool_name,
        module_name,
    )
```

**After:**
```python
else:
    del _tools[tool_name]
    shadowed_count += 1
    if strict_mode:
        strict_rejected.append(tool_name)
    logger.info(
        "[plugin] conflict: tool '%s' in '%s' shadows MCP tool — rejected",
        tool_name,
        module_name,
    )
```

#### Change 3: Initialize and return `strict_rejected`

Add at the top of the function body (after `shadowed_count = 0`):
```python
strict_rejected: list[str] = []
```

Change return statement:
```python
return (shadowed_count, allowed_count, strict_rejected)
```

#### Change 4: Update `load_plugins()` call site

**Before:**
```python
shadowed, allowed = _validate_tool_conflicts(known_tools, override_policy)
```

**After:**
```python
shadowed, allowed, strict_rejected = _validate_tool_conflicts(
    known_tools, override_policy, strict_mode
)
```

#### Change 5: Include `strict_rejected` in PluginLoadError

**Before:**
```python
if strict_mode and failures:
    details = "; ".join(f.error for f in failures)
    raise PluginLoadError(
        f"Plugin load failed ({len(failures)} error(s)): {details}"
    )
```

**After:**
```python
if strict_mode and (failures or strict_rejected):
    parts: list[str] = []
    if failures:
        parts.append(f"Plugin load failed ({len(failures)} error(s)): {'; '.join(f.error for f in failures)}")
    if strict_rejected:
        parts.append(f"Tool MCP conflicts rejected: {', '.join(strict_rejected)}")
    raise PluginLoadError("; ".join(parts))
```

---

## Validation Plan

| Check | Tool | Target |
|---|---|---|
| Lint | `ruff check scripts/shared/plugin_registry.py` | 0 errors |
| Type check | `mypy scripts/shared/plugin_registry.py` | no new errors |
| Tests | `uv run pytest tests/test_plugin_registry.py -v` | all pass including new |
| Architecture | import contract | `shared` must not import from `agent` — no violation |
