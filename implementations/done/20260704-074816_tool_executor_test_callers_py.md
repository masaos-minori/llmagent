# Implementation: Update re-export callers in test files (8 files)

## Goal

Update 8 test files to import symbols from their canonical modules instead of the backward-compat
re-exports in `shared.tool_executor`. Required after the re-export removal in `tool_executor.py`
(require-31).

## Scope

**Files and changes:**

| File | Symbol | Old source | New source |
|---|---|---|---|
| `tests/test_llm_client.py:20` | `TransportErrorInfo` | `shared.tool_executor` | `shared.transport_dto` |
| `tests/test_llm_client.py:668` | `format_transport_error` | `shared.tool_executor` | `shared.tool_executor_helpers` |
| `tests/test_tool_approval_preflight.py:24` | `ToolCallResult` | `shared.tool_executor` | `shared.transport_dto` |
| `tests/test_tool_executor.py:15-19` | `ToolCallResult` | `shared.tool_executor` | `shared.transport_dto` |
| `tests/test_tool_executor_helpers.py:8` | `is_side_effect, tool_hash_key` | `shared.tool_executor` | `shared.tool_executor_helpers` |
| `tests/test_tool_executor_routing.py:21-26` | `ToolCallResult` | `shared.tool_executor` | `shared.transport_dto` |
| `tests/test_tool_loop_guard.py:181,208,317,345` | `tool_hash_key` | `shared.tool_executor` (lazy) | `shared.tool_executor_helpers` |
| `tests/test_tool_runner.py:20` | `ToolCallResult` | `shared.tool_executor` | `shared.transport_dto` |
| `tests/integration/test_rag_llm_integration.py:315` | `ToolCallResult` | `shared.tool_executor` | `shared.transport_dto` |

- Out-of-Scope: No changes to test logic. Script file updates are a separate doc.

## Assumptions

1. `test_tool_loop_guard.py` has 4 lazy inline imports of `tool_hash_key` from
   `shared.tool_executor` inside test methods (at lines 181, 208, 317, 345 approximately).
   Each must be changed individually.
2. `tests/test_tool_executor.py` already imports `ToolCallResult` as part of the existing import
   block — only the source module changes.
3. Line numbers are approximate; read each file to confirm exact locations before editing.

## Implementation

### Target files

- `tests/test_llm_client.py`
- `tests/test_tool_approval_preflight.py`
- `tests/test_tool_executor.py`
- `tests/test_tool_executor_helpers.py`
- `tests/test_tool_executor_routing.py`
- `tests/test_tool_loop_guard.py`
- `tests/test_tool_runner.py`
- `tests/integration/test_rag_llm_integration.py`

### Procedure

1. For each file, grep for `from shared.tool_executor import` to find all affected lines.
2. Apply the import source changes per the table above.
3. For `test_tool_loop_guard.py`, find all 4 lazy inline imports inside method bodies and
   change each from `shared.tool_executor` to `shared.tool_executor_helpers`.
4. Run `uv run ruff check tests/test_llm_client.py tests/test_tool_executor.py ...` after editing.
5. Run `uv run pytest tests/ -q --ignore=tests/integration` — all pass.

### Method

For each `from shared.tool_executor import ...<symbol>...` pattern where `<symbol>` is one of
`ToolCallResult`, `TransportErrorInfo`, `format_transport_error`, `is_side_effect`, `tool_hash_key`:

- `ToolCallResult` → `from shared.transport_dto import ToolCallResult`
- `TransportErrorInfo` → `from shared.transport_dto import TransportErrorInfo`
- `format_transport_error` → `from shared.tool_executor_helpers import format_transport_error`
- `is_side_effect` → `from shared.tool_executor_helpers import is_side_effect`
- `tool_hash_key` → `from shared.tool_executor_helpers import tool_hash_key`

Keep any remaining imports from `shared.tool_executor` (e.g., `HttpTransport`, `ToolExecutor`,
`TransportError`, `LifecycleProtocol`) in their original block.

### Details

- `test_tool_loop_guard.py` uses lazy imports (`from shared.tool_executor import tool_hash_key`)
  inside test method bodies with `# noqa: PLC0415`. Update the module path only; keep `# noqa`.
- After editing `test_tool_executor.py`, verify that `HttpTransport`, `ToolExecutor`, and
  `TransportError` still import correctly from their original locations.

## Validation plan

```bash
# Verify no stale re-export usage in tests
grep -rn "from shared.tool_executor import.*ToolCallResult\|TransportErrorInfo\|format_transport_error\|is_side_effect\|tool_hash_key" tests/
# Expected: 0 results

# Lint all changed test files
uv run ruff check tests/test_llm_client.py tests/test_tool_executor.py \
  tests/test_tool_executor_helpers.py tests/test_tool_executor_routing.py \
  tests/test_tool_loop_guard.py tests/test_tool_runner.py \
  tests/test_tool_approval_preflight.py
# Expected: 0 errors each

# Run all non-integration tests
uv run pytest tests/ -q --ignore=tests/integration
# Expected: all pass
```
