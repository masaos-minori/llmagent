# Implementation: Add contract validation tests to test_plugin_registry.py

Steps covered: Plan 20260626-091912 — Steps 2-1, 2-2

---

## Goal

Add tests verifying that `register_tool()` raises `ValueError` on contract violations (missing name, invalid schema, conflicts) and does NOT emit a warning silently.

---

## Scope

- **In scope**: `tests/test_plugin_registry.py` — add/update test functions
- **Out of scope**: production code changes (step 1-x must be completed first)

---

## Assumptions

- After step 1-x, `register_tool()` raises `ValueError` on violations.
- Existing tests may have used `pytest.warns()` to check for warnings — those need to change to `pytest.raises(ValueError)`.

---

## Implementation

### Target file
`tests/test_plugin_registry.py`

### Procedure
1. Read `tests/test_plugin_registry.py` to find existing contract-related tests.
2. Step 2-1: Update any test that expected `logger.warning()` to now expect `pytest.raises(ValueError)`:
   ```python
   def test_register_tool_raises_on_missing_name():
       registry = PluginRegistry()
       with pytest.raises(ValueError, match="contract violation"):
           registry.register_tool(ToolDef(name="", description="x", inputSchema={"type": "object"}))
   ```
3. Step 2-2: Add conflict detection test:
   ```python
   def test_register_tool_raises_on_duplicate_name():
       registry = PluginRegistry()
       tool = ToolDef(name="my_tool", description="x", inputSchema={"type": "object"})
       registry.register_tool(tool)
       with pytest.raises(ValueError, match="tool conflict"):
           registry.register_tool(tool)  # second registration of same name
   ```
4. Add: invalid inputSchema test:
   ```python
   def test_register_tool_raises_on_invalid_input_schema():
       registry = PluginRegistry()
       with pytest.raises(ValueError, match="inputSchema must be a JSON Schema object"):
           registry.register_tool(ToolDef(name="t", description="x", inputSchema=["not", "a", "dict"]))
   ```

### Method
`pytest` unit tests. No async needed.

---

## Validation plan

- Run: `uv run pytest tests/test_plugin_registry.py -x -v` — all new tests pass.
- Run: `uv run pytest tests/ -x` — no regressions.
