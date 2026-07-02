# Implementation Procedure: tests/test_tool_registry.py

## Goal

Add tests for ToolRegistry duplicate-ownership rejection and live drift validation (`validate_routing_against_live`, `validate_all_routing`) without changing any production code.

## Scope

**In**:
- New file: `tests/test_tool_registry.py`
  - Duplicate ownership rejection test
  - `validate_routing_against_live()` tests
  - `validate_all_routing()` tests
- Existing file: `tests/test_tool_registry_counts.py` — keep unchanged (count tests remain)
- Source file: `scripts/shared/tool_registry.py` — read-only reference, no production changes

**Out**:
- No changes to `scripts/shared/tool_registry.py`
- No changes to `scripts/shared/tool_constants.py`
- No changes to `tests/test_tool_registry_counts.py`

## Assumptions

1. `reset_registry()` is the correct isolation mechanism between tests (confirmed in source).
2. `validate_routing_against_live()` accepts `dict[str, list[str]]` (confirmed from source line 219).
3. Mismatch message format is stable: `"[{server_key}] tool {t!r} in live response but not in registry"` and `"[{server_key}] tool {t!r} in registry but not in live response"` (confirmed from source lines 121-130).
4. `validate_all_routing()` merges config drift and live drift into one dict, extending lists for shared server keys (confirmed from source lines 240-258).
5. `ToolRegistry` and all functions under test are importable as `from shared.tool_registry import ...` (test discovery pattern confirmed from `test_tool_registry_counts.py`).

## Implementation

### Target file

`tests/test_tool_registry.py`

### Procedure

1. Create `tests/test_tool_registry.py` with the following test classes:

   **TestDuplicateOwnershipRejection**
   - Test: registering the same tool name twice raises `ValueError` with expected message.
   - Use a fresh `ToolRegistry()` instance (not the global singleton) to avoid ordering issues.

   **TestValidateRoutingAgainstLive**
   - Test `no_drift_when_live_matches_registry`: pass live list identical to registry; expect empty dict.
   - Test `owner_mismatch_detected`: register tool `"x"` to server `"s1"`, pass live `{"s2": ["x"]}` (wrong server key); expect mismatch message for `s2` containing `"x"`.
   - Test `tool_in_live_not_in_registry`: pass `{"rag_pipeline": ["nonexistent_tool"]}` against global registry; expect mismatch entry.
   - Test `tool_in_registry_not_in_live`: pass `{"rag_pipeline": []}` against global registry; expect all 4 rag_pipeline tools listed as missing from live.
   - Test `returns_empty_when_live_is_none`: call with `live_tool_lists=None`; expect `{}`.

   **TestValidateAllRouting**
   - Test `merges_config_and_live_results`: pass both `server_configs` with a drift and `live_tool_lists` with a drift for same server key; expect single key with both messages concatenated.
   - Test `empty_when_both_inputs_none`: call with no args; expect `{}`.

### Method

- Use pytest class-based test organization (matching existing `test_tool_registry_counts.py` pattern).
- For tests using global registry (`get_registry()`), only read from it — no teardown mutation needed.
- For tests modifying registry state, use local `ToolRegistry()` instances.
- Assert substring patterns (`in msg`) rather than exact string equality for message assertions.

### Details

```python
import pytest
from shared.tool_registry import (
    ToolDefinition,
    ToolRegistry,
    reset_registry,
    get_registry,
    validate_routing_against_live,
    validate_all_routing,
)

# --- Duplicate ownership rejection ---

class TestDuplicateOwnershipRejection:
    def test_duplicate_raises_value_error(self):
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="tool_a", server_key="s1"))
        with pytest.raises(ValueError, match=r"already registered"):
            registry.register(ToolDefinition(name="tool_a", server_key="s2"))

# --- validate_routing_against_live ---

class TestValidateRoutingAgainstLive:
    def test_no_drift_when_live_matches_registry(self):
        """Live list identical to registry → empty dict."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="tool_a", server_key="s1"))
        drift = validate_routing_against_live(registry, {"s1": ["tool_a"]})
        assert drift == {}

    def test_owner_mismatch_detected(self):
        """Tool registered to s1 but live response comes from s2 → mismatch."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(name="x", server_key="s1"))
        drift = validate_routing_against_live(registry, {"s2": ["x"]})
        assert "s2" in drift
        assert '"x" in live response but not in registry' in drift["s2"][0]

    def test_tool_in_live_not_in_registry(self):
        """Tool in live response but not in registry → mismatch."""
        # Use global registry which has rag_pipeline tools
        reset_registry()
        registry = get_registry()
        drift = validate_routing_against_live(registry, {"rag_pipeline": ["nonexistent_tool"]})
        assert "rag_pipeline" in drift
        assert '"nonexistent_tool" in live response but not in registry' in drift["rag_pipeline"][0]

    def test_tool_in_registry_not_in_live(self):
        """Tool in registry but not in live → mismatch for all rag_pipeline tools."""
        reset_registry()
        registry = get_registry()
        drift = validate_routing_against_live(registry, {"rag_pipeline": []})
        assert "rag_pipeline" in drift
        # All 4 rag_pipeline tools should be listed as missing from live
        assert len(drift["rag_pipeline"]) == 4

    def test_returns_empty_when_live_is_none(self):
        """None input → empty dict."""
        registry = ToolRegistry()
        drift = validate_routing_against_live(registry, None)
        assert drift == {}

# --- validate_all_routing ---

class TestValidateAllRouting:
    def test_merges_config_and_live_results(self):
        """Both config and live have drift for same server key → merged."""
        from shared.mcp_config import McpServerConfig

        reset_registry()
        registry = get_registry()
        cfg = McpServerConfig(
            name="rag_pipeline",
            command="rag",
            args=[],
            tool_names=["existing_tool"],  # drift: not in registry
        )
        server_configs = {"rag_pipeline": cfg}
        live_tool_lists = {"rag_pipeline": ["nonexistent_tool"]}  # drift: in live but not registry

        result = validate_all_routing(server_configs, live_tool_lists)
        assert "rag_pipeline" in result
        # Both config drift and live drift messages present
        assert len(result["rag_pipeline"]) >= 2

    def test_empty_when_both_inputs_none(self):
        """No inputs → empty dict."""
        result = validate_all_routing()
        assert result == {}
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `ruff check scripts/ tests/` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Architecture | `lint-imports` | 0 violations |
| Tests | `uv run pytest tests/test_tool_registry.py tests/test_tool_registry_counts.py -v` | all pass |
| Regression | `uv run pytest tests/ -q` | no regressions |
