# Implementation: Update and extend `tests/test_tool_policy.py`

## Goal

Update one existing test that becomes incorrect after the `classify_risk()` fix (require-35),
and add a new `TestClassifyRiskConstantsFallback` class with 6 tests covering the
constants-based classification path for delete, shell, and write tools.

## Scope

- In-Scope:
  - Update `test_non_recursive_delete_returns_medium_by_default` (line ~88): rename it to
    `test_non_recursive_delete_defaults_to_high_from_constants` and change assertion from
    `"medium"` to `"high"`.
  - Add `TestClassifyRiskConstantsFallback` class with 6 test methods.
- Out-of-Scope: No changes to any other test. No changes to production code (see `tool_policy_py.md`).

## Assumptions

1. `tests/test_tool_policy.py` contains a test at line ~88:
   ```python
   def test_non_recursive_delete_returns_medium_by_default(self):
       result = classify_risk(cfg, "delete_directory", {"recursive": False})
       assert result == "medium"
   ```
2. A `_cfg()` helper function exists in the test file (or similar) for building `AgentConfig`
   with empty `tool_safety_tiers`.
3. After require-35, `delete_directory` is in `DELETE_TOOLS` → `classify_risk()` returns `"high"`.
4. `uv run pytest` is the test runner.

## Implementation

### Target file

`tests/test_tool_policy.py` (existing)

### Procedure

1. Read `test_tool_policy.py` around line 88 to find the exact test to update.
2. Rename the test and update the assertion.
3. Add `TestClassifyRiskConstantsFallback` class at the end of the file.
4. Run `uv run ruff check tests/test_tool_policy.py` — expect 0 errors.
5. Run `uv run pytest tests/test_tool_policy.py -v` — all pass.

### Method

**Update existing test:**
```python
# Before:
def test_non_recursive_delete_returns_medium_by_default(self):
    result = classify_risk(cfg, "delete_directory", {"recursive": False})
    assert result == "medium"

# After:
def test_non_recursive_delete_defaults_to_high_from_constants(self):
    result = classify_risk(cfg, "delete_directory", {"recursive": False})
    assert result == "high"
```

**Add new class:**
```python
class TestClassifyRiskConstantsFallback:
    """Tests for priority 3: tool_constants.py classification when not in tool_safety_tiers."""

    def test_delete_tool_defaults_to_high(self) -> None:
        cfg = _cfg()  # empty tool_safety_tiers
        result = classify_risk(cfg, "delete_file", {})
        assert result == "high"

    def test_delete_directory_no_recursive_defaults_to_high(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "delete_directory", {"recursive": False})
        assert result == "high"

    def test_shell_tool_defaults_to_high(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "shell_run", {})
        assert result == "high"

    def test_write_tool_defaults_to_medium(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "write_file", {})
        assert result == "medium"

    def test_explicit_risk_rule_overrides_constants(self) -> None:
        cfg = _cfg(approval_risk_rules={"delete_file": "none"})
        result = classify_risk(cfg, "delete_file", {})
        assert result == "none"

    def test_safety_tier_overrides_constants(self) -> None:
        cfg = _cfg(tool_safety_tiers={"shell_run": "READ_ONLY"})
        result = classify_risk(cfg, "shell_run", {})
        assert result == "none"
```

### Details

- `_cfg()` is assumed to be a helper in the existing test file. If the signature does not accept
  `approval_risk_rules` or `tool_safety_tiers` keyword args, adapt the constructor call to match
  the existing pattern in the test file.
- After the update, `test_non_recursive_delete_returns_medium_by_default` no longer exists; if
  other test classes reference it, update those references.

## Validation plan

```bash
# Lint
uv run ruff check tests/test_tool_policy.py
# Expected: 0 errors

# Updated existing test
uv run pytest tests/test_tool_policy.py -k "test_non_recursive_delete_defaults_to_high_from_constants" -v
# Expected: 1 passed

# New constants tests
uv run pytest tests/test_tool_policy.py::TestClassifyRiskConstantsFallback -v
# Expected: 6 passed

# Full policy test suite
uv run pytest tests/test_tool_policy.py tests/test_tool_policy_comprehensive.py -q
# Expected: all pass
```
