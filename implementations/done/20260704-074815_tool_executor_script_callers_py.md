# Implementation: Update re-export callers in `scripts/agent/` (4 files)

## Goal

Update 4 script files in `scripts/agent/` to import symbols from their canonical modules
instead of the backward-compat re-exports in `shared.tool_executor`. This is required after
the re-export removal in `tool_executor.py` (require-31).

## Scope

**Files and changes:**

| File | Old import | New import |
|---|---|---|
| `scripts/agent/tool_loop_guard.py:18` | `from shared.tool_executor import tool_hash_key` | `from shared.tool_executor_helpers import tool_hash_key` |
| `scripts/agent/tool_runner.py:22` | `from shared.tool_executor import is_side_effect, tool_hash_key` | `from shared.tool_executor_helpers import is_side_effect, tool_hash_key` |
| `scripts/agent/error_injection_service.py:16` | `from shared.tool_executor import format_transport_error` | `from shared.tool_executor_helpers import format_transport_error` |
| `scripts/agent/repository_gateway.py:18` | `from shared.tool_executor import ToolCallResult` (+ `ToolExecutor`) | `from shared.transport_dto import ToolCallResult` (keep `ToolExecutor` from `shared.tool_executor`) |

- Out-of-Scope: No changes to function logic in any of these files. Test file updates are
  covered by a separate implementation doc.

## Assumptions

1. `tool_hash_key`, `is_side_effect`, `format_transport_error` are defined in
   `shared.tool_executor_helpers` (confirmed by caller map in require-31 plan).
2. `ToolCallResult` is defined in `shared.transport_dto` (confirmed by require-31 plan).
3. `ToolExecutor` continues to be imported from `shared.tool_executor`.
4. Line numbers in the plan are approximate; read each file before editing to confirm the
   exact import block.

## Implementation

### Target files

- `scripts/agent/tool_loop_guard.py`
- `scripts/agent/tool_runner.py`
- `scripts/agent/error_injection_service.py`
- `scripts/agent/repository_gateway.py`

### Procedure

1. Read each file to find the exact import block.
2. Apply the import change per the table above.
3. Run `uv run ruff check <file>` after each edit — expect 0 errors.
4. Run `uv run pytest tests/test_tool_loop_guard.py tests/test_tool_runner.py -q` — all pass.

### Method

**`tool_loop_guard.py`**
```python
# Before:
from shared.tool_executor import tool_hash_key
# After:
from shared.tool_executor_helpers import tool_hash_key
```

**`tool_runner.py`**
```python
# Before:
from shared.tool_executor import is_side_effect, tool_hash_key
# After:
from shared.tool_executor_helpers import is_side_effect, tool_hash_key
```

**`error_injection_service.py`**
```python
# Before:
from shared.tool_executor import format_transport_error
# After:
from shared.tool_executor_helpers import format_transport_error
```

**`repository_gateway.py`**
```python
# Before:
from shared.tool_executor import ToolCallResult, ToolExecutor  # (example)
# After:
from shared.transport_dto import ToolCallResult
from shared.tool_executor import ToolExecutor
```

### Details

- For `repository_gateway.py`, if `ToolCallResult` and `ToolExecutor` were in the same import
  block, split them into two separate import lines as shown.
- Preserve any existing `# noqa` comments relevant to the import lines.

## Validation plan

```bash
# No stale tool_executor re-export usage in scripts/agent
grep -rn "from shared.tool_executor import.*tool_hash_key\|is_side_effect\|format_transport_error" scripts/agent/
# Expected: 0 results

grep -rn "from shared.tool_executor import.*ToolCallResult" scripts/agent/
# Expected: 0 results (ToolExecutor imports still allowed)

# Lint all 4 files
uv run ruff check scripts/agent/tool_loop_guard.py scripts/agent/tool_runner.py \
  scripts/agent/error_injection_service.py scripts/agent/repository_gateway.py
# Expected: 0 errors

# Tests
uv run pytest tests/test_tool_loop_guard.py tests/test_tool_runner.py -q
# Expected: all pass
```
