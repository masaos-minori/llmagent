# Implementation: Fix circular import in `scripts/shared/tool_executor_helpers.py`

## Goal

Fix the circular import in `scripts/shared/tool_executor_helpers.py:32` where
`TransportErrorInfo` is lazily imported from `shared.tool_executor`. Change it to import
directly from `shared.transport_dto` (the canonical definition location). This eliminates the
cycle: `tool_executor` → `tool_executor_helpers` → `tool_executor`.

## Scope

- In-Scope: Change the `TransportErrorInfo` import at line 32 from `shared.tool_executor` to
  `shared.transport_dto`. Remove the `# noqa: F821` comment.
- Out-of-Scope: No changes to function bodies, `_SIDE_EFFECT_TOOLS`, or any other import in
  `tool_executor_helpers.py`. (Side-effect tools are extended in require-36.)

## Assumptions

1. `TransportErrorInfo` is defined in `scripts/shared/transport_dto.py` (confirmed by
   require-31 analysis).
2. The current import is a lazy import inside a function body (not at module level), using
   `# noqa: F821` to suppress a mypy false-positive.
3. After the fix, the import can move to the module-level import block (no lazy import needed).

## Implementation

### Target file

`scripts/shared/tool_executor_helpers.py` (existing — one-line change)

### Procedure

1. Read `tool_executor_helpers.py` around line 32 to confirm the exact import pattern.
2. Remove the lazy `from shared.tool_executor import TransportErrorInfo  # noqa: F821` import.
3. Add `TransportErrorInfo` to the module-level `from shared.transport_dto import ...` block
   (or add a new import line if `transport_dto` is not yet imported there).
4. Run `uv run ruff check scripts/shared/tool_executor_helpers.py` — expect 0 errors.
5. Run `uv run mypy scripts/shared/tool_executor_helpers.py` — expect no new errors.

### Method

```python
# Before (lazy import at line 32, inside function body):
from shared.tool_executor import TransportErrorInfo  # noqa: F821

# After (at module level with canonical import):
from shared.transport_dto import TransportErrorInfo
```

### Details

- The `# noqa: F821` comment was suppressing a mypy error caused by the circular import;
  removing it along with changing the import source is correct.
- `format_transport_error()` uses `TransportErrorInfo` as a return type annotation; the
  function signature and body are unchanged.

## Validation plan

```bash
# No circular import reference
grep -n "from shared.tool_executor import TransportErrorInfo" scripts/shared/tool_executor_helpers.py
# Expected: 0 results

# Lint
uv run ruff check scripts/shared/tool_executor_helpers.py
# Expected: 0 errors

# Type check
uv run mypy scripts/shared/tool_executor_helpers.py
# Expected: no new errors

# Tests
uv run pytest tests/test_tool_executor_helpers.py -q
# Expected: all pass
```
