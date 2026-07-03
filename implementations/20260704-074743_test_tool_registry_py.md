# Implementation: Fix imports in `tests/test_tool_registry.py`

## Goal

Fix the broken imports in `tests/test_tool_registry.py:17-19` that currently import
`validate_all_routing`, `validate_routing_against_config`, and `validate_routing_against_live`
from `shared.tool_registry` (where they are not defined). Move these imports to a separate
`from shared.tool_routing_validation import ...` block.

## Scope

- In-Scope: Change the 3 validation function imports from `shared.tool_registry` to
  `shared.tool_routing_validation` in `tests/test_tool_registry.py`.
- Out-of-Scope: No changes to test logic, `ToolDefinition`, `ToolRegistry`, `get_registry`, or
  `reset_registry` imports.

## Assumptions

1. `scripts/shared/tool_routing_validation.py` exists (prerequisite: rename doc `20260704-074648`).
2. Lines 17-19 of `test_tool_registry.py` have the following pattern:
   ```python
   from shared.tool_registry import (
       ...
       validate_all_routing,
       validate_routing_against_config,
       validate_routing_against_live,
   )
   ```
3. The remaining imports from `shared.tool_registry` (e.g., `ToolDefinition`, `ToolRegistry`,
   `get_registry`, `reset_registry`) stay in the original import block.

## Implementation

### Target file

`tests/test_tool_registry.py` (existing — import change)

### Procedure

1. Read `test_tool_registry.py` lines 1-25 to confirm the exact import structure.
2. Remove `validate_all_routing`, `validate_routing_against_config`, and
   `validate_routing_against_live` from the `from shared.tool_registry import ...` block.
3. Add a new import block:
   ```python
   from shared.tool_routing_validation import (
       validate_all_routing,
       validate_routing_against_config,
       validate_routing_against_live,
   )
   ```
4. Run `uv run ruff check tests/test_tool_registry.py` — expect 0 errors.
5. Run `uv run pytest tests/test_tool_registry.py -q` — expect all pass.

### Method

```python
# Before (lines 17-19, approximate):
from shared.tool_registry import (
    ToolDefinition,
    ToolRegistry,
    get_registry,
    reset_registry,
    validate_all_routing,
    validate_routing_against_config,
    validate_routing_against_live,
)

# After:
from shared.tool_registry import (
    ToolDefinition,
    ToolRegistry,
    get_registry,
    reset_registry,
)
from shared.tool_routing_validation import (
    validate_all_routing,
    validate_routing_against_config,
    validate_routing_against_live,
)
```

### Details

- No other test file should be importing `validate_*` from `shared.tool_registry` — grep confirms
  only `test_tool_registry.py` (lines 17-19) and `repl_health.py` (line 272) use this pattern.
- All test logic remains unchanged — only the import source changes.

## Validation plan

```bash
# No stale imports
grep -n "from shared.tool_registry import.*validate" tests/test_tool_registry.py
# Expected: 0 results

# Lint
uv run ruff check tests/test_tool_registry.py
# Expected: 0 errors

# All tests pass
uv run pytest tests/test_tool_registry.py -q
# Expected: all pass
```
