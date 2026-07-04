# Step 1 — Fix `_check_tool_definitions` docstring in `scripts/agent/repl_health.py`

## Goal

Replace the stale Option B docstring in `_check_tool_definitions` with accurate Option A language that distinguishes `strict=True` vs `strict=False` for the all-servers-unreachable case.

## Scope

- **In-Scope:**
  - Replace the "All servers unreachable" block in the docstring of `_check_tool_definitions` (lines 157-159 in `scripts/agent/repl_health.py`) with two separate bullets: one for `strict=True` and one for `strict=False`.

- **Out-of-Scope:**
  - No changes to the function's logic (lines 167-213 are correct as-is).
  - No changes to any other function, class, or import in the file.
  - No changes to `_collect_server_tool_definitions` docstring (which already correctly describes its behavior).

## Assumptions

1. The function logic at lines 173-183 already implements Option A correctly: `strict=True` + all unreachable → `RuntimeError`; `strict=False` + all unreachable → `INFO` log + return `HealthCheckResult()`.
2. The docstring change is purely cosmetic (string data); ruff and mypy will produce no new errors.
3. The exact string `"no error even in strict mode"` appears only at line 159 and nowhere else in the file.

## Implementation

### Target file

`/home/masaos/llmagent/scripts/agent/repl_health.py`

### Procedure

1. Open `scripts/agent/repl_health.py`.
2. Locate the docstring block for `_check_tool_definitions` (starts at line 144, "Compare tool_definitions against live server tool lists.").
3. Find the exact lines (157-159) inside that docstring:
   ```
         - All servers unreachable:
             INFO "All MCP servers unreachable during strict validation: [...]; skipping tool definition check"
             returns HealthCheckResult() — no warnings, no error even in strict mode
   ```
4. Replace those three lines with the following five lines, preserving the 6-space indentation (matching the surrounding bullet style):
   ```
         - All servers unreachable, strict=True:
             ERROR "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]."
             raises RuntimeError
         - All servers unreachable, strict=False:
             INFO "All MCP servers unreachable; skipping tool definition check. Unreachable: [...]"
             returns HealthCheckResult() — no warnings
   ```
5. Save the file.
6. Run `grep -n "no error even in strict mode" scripts/agent/repl_health.py` — must return no output.

### Method

- Pure docstring text replacement; no imports, no logic changes.
- Use the Edit tool for a precise `old_string`/`new_string` swap to avoid any indentation drift.
- The `old_string` must include all three original lines verbatim with their leading spaces.

### Details

- File: `/home/masaos/llmagent/scripts/agent/repl_health.py`
- Old block (exact text to match, indented with 6 spaces before `-`):
  ```
        - All servers unreachable:
            INFO "All MCP servers unreachable during strict validation: [...]; skipping tool definition check"
            returns HealthCheckResult() — no warnings, no error even in strict mode
  ```
- New block (exact replacement text):
  ```
        - All servers unreachable, strict=True:
            ERROR "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]."
            raises RuntimeError
        - All servers unreachable, strict=False:
            INFO "All MCP servers unreachable; skipping tool definition check. Unreachable: [...]"
            returns HealthCheckResult() — no warnings
  ```
- The surrounding docstring lines (lines 152-156 and 160-165) must remain untouched.
- The actual runtime log strings are at lines 177-183 in the function body; the docstring must now match those strings.

## Validation plan

```bash
# Confirm the stale text is gone
grep -n "no error even in strict mode" /home/masaos/llmagent/scripts/agent/repl_health.py
# Expected: no output

# Confirm the new strict=True bullet is present
grep -n "All servers unreachable, strict=True" /home/masaos/llmagent/scripts/agent/repl_health.py
# Expected: one match

# Confirm no ruff errors introduced
uv run ruff check scripts/agent/repl_health.py
# Expected: exit code 0

# Confirm no mypy errors introduced
uv run mypy scripts/agent/repl_health.py
# Expected: "Success: no issues found" or 0 errors

# Confirm existing tests still pass (no logic changed)
uv run pytest tests/test_repl_health.py -v
# Expected: all tests pass
```
