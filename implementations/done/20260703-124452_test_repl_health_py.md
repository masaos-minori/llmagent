# Step 3 — Add missing tests in `tests/test_repl_health.py`

## Goal

Add three new test cases to `TestCheckToolDefinitions` to fully cover the partial-unreachable and all-unreachable-non-strict branches of `_check_tool_definitions`, satisfying the plan's acceptance criteria.

## Scope

- **In-Scope:**
  - Add `test_partial_unreachable_non_strict_returns_warning_if_mismatch` inside `TestCheckToolDefinitions`.
  - Add `test_partial_unreachable_strict_raises` inside `TestCheckToolDefinitions`.
  - Add `test_all_unreachable_non_strict_skips_validation` inside `TestCheckToolDefinitions`.

- **Out-of-Scope:**
  - No modifications to any existing test in the file.
  - No changes to test helper functions (`_async_result`).
  - No changes to any other test class (`TestProbeMcpHealth`, `TestCheckServiceHealth`, etc.).
  - No changes to `scripts/agent/repl_health.py`.

## Assumptions

1. `_collect_server_tool_names` is patched via `patch("agent.repl_health._collect_server_tool_names", new_callable=AsyncMock)` — same pattern as all existing tests in `TestCheckToolDefinitions`.
2. The return type of the mock is `tuple[set[str], list[str]]` where the second element is the unreachable-server key list. A non-empty second element means some servers are unreachable.
3. For "partial unreachable" tests: `_collect_server_tool_names` returns `({"read_file"}, ["srv-b"])` — one tool name available (from reachable servers), one server key unreachable.
4. For `test_all_unreachable_non_strict_skips_validation`: `_collect_server_tool_names` returns `(set(), ["srv-a"])` — zero tool names (all servers unreachable). This exercises the `if not server_names: if unreachable: if not strict:` branch at lines 173-183 in `repl_health.py`.
5. `tool_definitions` in `ctx.cfg.tool.tool_definitions` uses the same fixture shape as existing tests: `[{"function": {"name": "read_file"}}, {"function": {"name": "write_file"}}]`.
6. `HealthCheckResult.warning_messages()` is the correct method to extract warning text — used in `test_returns_warning_on_missing_in_server` at line 133.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_repl_health.py`

### Procedure

1. Open `tests/test_repl_health.py`.
2. Locate the end of `TestCheckToolDefinitions` class — the last method is `test_raises_in_strict_mode_when_all_unreachable` ending at line 197.
3. Append the following three test methods inside the class, after line 197 (before the blank line that separates `TestCheckToolDefinitions` from `TestCheckServiceHealth`):

   **Test A — `test_partial_unreachable_non_strict_returns_warning_if_mismatch`:**
   ```python
   @pytest.mark.asyncio
   async def test_partial_unreachable_non_strict_returns_warning_if_mismatch(self) -> None:
       ctx = MagicMock()
       ctx.cfg.tool.tool_definitions = [
           {"function": {"name": "read_file"}},
           {"function": {"name": "write_file"}},
       ]

       with patch(
           "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
       ) as mock_collect:
           # One server reachable (returned read_file), one server unreachable (srv-b)
           mock_collect.return_value = ({"read_file"}, ["srv-b"])
           result = await _check_tool_definitions(ctx, strict=False)

       msgs = result.warning_messages()
       assert len(msgs) == 1
       assert "write_file" in msgs[0]
   ```

   **Test B — `test_partial_unreachable_strict_raises`:**
   ```python
   @pytest.mark.asyncio
   async def test_partial_unreachable_strict_raises(self) -> None:
       ctx = MagicMock()
       ctx.cfg.tool.tool_definitions = [
           {"function": {"name": "read_file"}},
           {"function": {"name": "write_file"}},
       ]

       with patch(
           "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
       ) as mock_collect:
           # One server reachable (returned read_file), one server unreachable (srv-b)
           mock_collect.return_value = ({"read_file"}, ["srv-b"])
           with pytest.raises(RuntimeError, match="Strict mode"):
               await _check_tool_definitions(ctx, strict=True)
   ```

   **Test C — `test_all_unreachable_non_strict_skips_validation`:**
   ```python
   @pytest.mark.asyncio
   async def test_all_unreachable_non_strict_skips_validation(self) -> None:
       ctx = MagicMock()
       ctx.cfg.tool.tool_definitions = [
           {"function": {"name": "read_file"}},
       ]

       with patch(
           "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
       ) as mock_collect:
           # All servers unreachable (non-empty unreachable list)
           mock_collect.return_value = (set(), ["srv-a"])
           result = await _check_tool_definitions(ctx, strict=False)

       assert not result.has_issues
   ```

4. Save the file.

### Method

- All three tests follow the exact same structure as the existing six tests in `TestCheckToolDefinitions`:
  - Build a `MagicMock()` ctx.
  - Set `ctx.cfg.tool.tool_definitions` to a list of tool definition dicts.
  - Patch `agent.repl_health._collect_server_tool_names` with `new_callable=AsyncMock`.
  - Set `mock_collect.return_value` to `(set[str], list[str])`.
  - Call `await _check_tool_definitions(ctx, strict=<bool>)`.
  - Assert on the result or expected exception.

- `_check_tool_definitions` is already imported at line 16 of the test file; no new imports needed.

- Use `pytest.raises(RuntimeError, match="Strict mode")` for Test B — the function raises with message starting "Strict mode: tool definition mismatch detected." when `missing_in_server` is non-empty and `strict=True` (line 198-212 in repl_health.py). The match `"Strict mode"` is sufficient (used in existing `test_raises_in_strict_mode`).

### Details

- **Insertion point:** After line 197 (closing line of `test_raises_in_strict_mode_when_all_unreachable`), before line 200 (the `# ── check_service_health()` comment line).
- **Code path exercised by Test A and Test B:** `server_names = {"read_file"}` (non-empty), so the function does NOT enter the `if not server_names:` branch. `missing_in_server = {"write_file"} - {"read_file"} = {"write_file"}`. Test A: `strict=False` → returns `HealthCheckResult(warnings=[...])`. Test B: `strict=True` → raises `RuntimeError`.
- **Code path exercised by Test C:** `server_names = set()` (empty), `unreachable = ["srv-a"]` (non-empty), `strict=False` → enters `if not server_names: if unreachable: (not strict)` → logs INFO and returns `HealthCheckResult()`.
- **Difference from existing `test_returns_empty_when_all_servers_unreachable`:** That test uses `(set(), [])` — empty unreachable list — which hits the `else:` branch at line 184. Test C uses `(set(), ["srv-a"])` — non-empty unreachable list — which hits the `if unreachable:` branch at line 174.

## Validation plan

```bash
# Run only the new tests by name
uv run pytest tests/test_repl_health.py -v \
  -k "partial_unreachable or all_unreachable_non_strict"
# Expected: 3 tests collected, 3 passed

# Run the full TestCheckToolDefinitions class to confirm no regressions
uv run pytest tests/test_repl_health.py::TestCheckToolDefinitions -v
# Expected: 9 tests collected (6 existing + 3 new), all pass

# Run the entire test file
uv run pytest tests/test_repl_health.py -v
# Expected: all tests pass, 0 failures

# Ruff check
uv run ruff check tests/test_repl_health.py
# Expected: exit code 0

# Mypy check
uv run mypy tests/test_repl_health.py
# Expected: 0 errors
```
