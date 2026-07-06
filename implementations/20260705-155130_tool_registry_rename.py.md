# Implementation: shared/tool_registry.py — Rename reset_registry() → _reset_registry_for_testing()

## Goal

Rename `reset_registry()` to `_reset_registry_for_testing()` and update all test file imports to use the new name.

## Scope

**In**: Rename in `tool_registry.py`. Update all test file imports.

**Out**: Changes to routing logic, removing singleton, or adding backward-compat alias.

## Assumptions

1. `reset_registry()` at `tool_registry.py:148` — only definition.
2. No production callers exist (verified by grep: `grep -rn "reset_registry" scripts/ --include="*.py" | grep -v "tests/" | grep -v "def reset_registry"` → empty).
3. Test files import it as `from shared.tool_registry import reset_registry`.
4. No compatibility alias needed — all callers updated atomically.

## Implementation

### Target files
- `scripts/shared/tool_registry.py`
- All test files importing `reset_registry`

### Procedure
1. In `tool_registry.py`, rename `def reset_registry()` → `def _reset_registry_for_testing()`.
2. Add docstring to make intent clear.
3. Find all test files using `reset_registry` and update imports.
4. Check `conftest.py` files for fixture usage.

### Method

**Renamed function in `scripts/shared/tool_registry.py`:**
```python
def _reset_registry_for_testing() -> None:
    """Reset the global ToolRegistry singleton. FOR TESTING ONLY."""
    global _registry
    _registry = None
```

**Test import update pattern (apply to all test files found by grep):**
```python
# Before:
from shared.tool_registry import reset_registry
# After:
from shared.tool_registry import _reset_registry_for_testing
```

**Call site update pattern:**
```python
# Before:
reset_registry()
# After:
_reset_registry_for_testing()
```

**Grep command to find all callsites:**
```bash
grep -rn "reset_registry" scripts/ tests/ --include="*.py"
```

### Details

- If `tool_routing_validation.py` re-exports `reset_registry`, update that export to `_reset_registry_for_testing`.
- `conftest.py` fixtures may use `reset_registry` as a cleanup fixture — these must be updated.
- `_reset_registry_for_testing` is still importable — the underscore prefix is a convention, not a Python access restriction.

## Validation plan

- `grep -rn "reset_registry" scripts/ --include="*.py" | grep -v "_reset_registry_for_testing"` → 0 results.
- `uv run pytest tests/ -x -q` — all pass.
- `mypy scripts/shared/tool_registry.py` — no new errors.
- `ruff check scripts/shared/tool_registry.py` — 0 errors.
