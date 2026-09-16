## Goal

Add unit tests for the LLM visibility filter (`AgentSafetyTier`) — verifying that tools hidden from the LLM are correctly filtered out during discovery, and that the filter respects the current policy state. (REQ-001; "Add unit tests for the LLM visibility filter in `tests/agent/test_tool_policy.py`")

## Scope

- Add tests for the LLM visibility filter: verify that tools hidden from the LLM are correctly filtered out during discovery.
- Add tests for the filter respecting the current policy state: verify that the filter uses the current `cfg.tool.allowed_tools` and `cfg.tool.disallowed_tools`.

## Assumptions

- The `llm_visibility_base` field exists on `RuntimeTool` (covered by a separate document — this row depends on its completion).
- The `apply_policy()` formula has been rewritten to use the immutable base field (covered by a separate document — this row depends on its completion).
- The existing test infrastructure (fixtures, mocks) in `tests/agent/test_tool_policy.py` is sufficient for these tests.

## Design decisions

- **Test structure**: Use a single test method per scenario for clarity.
- **Discovery-time filter test**: Verify that tools with `enabled_for_llm=False` are excluded from the discovered tool list.
- **Policy-state filter test**: Verify that the filter respects the current `cfg.tool.allowed_tools` and `cfg.tool.disallowed_tools`.

## Alternatives considered

- **Parameterized test**: Could use `@pytest.mark.parametrize` for multiple scenarios, but separate test methods are clearer for complex state transitions.
- **Integration test vs. unit test**: Unit test is preferred because we want to isolate the filter's behavior without involving the full agent lifecycle.

## Implementation

### Target file

`tests/agent/test_tool_policy.py`

### Procedure

1. Create test methods in the existing test class for each scenario.
2. Write a test for discovery-time filtering:
   ```python
   async def test_discovery_time_filter_excludes_hidden_tools(self) -> None:
       """Tools hidden from the LLM should be excluded from the discovered tool list."""
       # Arrange: create a registry with one visible and one hidden tool
       visible_tool = Mock(spec=RuntimeTool)
       visible_tool.enabled_for_llm = True
       
       hidden_tool = Mock(spec=RuntimeTool)
       hidden_tool.enabled_for_llm = False
       
       registry = Mock(spec=RuntimeToolRegistry)
       registry.get.side_effect = lambda name: visible_tool if name == "visible" else hidden_tool
       
       # Act: discover tools
       result = await discover_tools(registry, cfg=self.cfg)
       
       # Assert: only the visible tool should be returned
       assert len(result) == 1
       assert result[0].name == "visible"
   ```
3. Write a test for policy-state filtering:
   ```python
   async def test_filter_respects_allowed_tools(self) -> None:
       """The filter should respect the current allowed_tools configuration."""
       # Arrange: create a registry with two tools
       tool1 = Mock(spec=RuntimeTool)
       tool1.enabled_for_llm = True
       tool1.name = "tool1"
       
       tool2 = Mock(spec=RuntimeTool)
       tool2.enabled_for_llm = True
       tool2.name = "tool2"
       
       registry = Mock(spec=RuntimeToolRegistry)
       registry.get.side_effect = lambda name: tool1 if name == "tool1" else tool2
       
       # Act: discover tools with allowed_tools=["tool1"]
       result = await discover_tools(registry, cfg=self.cfg)
       
       # Assert: only tool1 should be returned
       assert len(result) == 1
       assert result[0].name == "tool1"
   ```

### Method

Add test methods to the existing test class. No new imports or dependencies.

### Details

**Step 1: Identify the existing test class**

Find the existing test class in `tests/agent/test_tool_policy.py` (likely named `TestToolPolicy` or similar).

**Step 2: Add the discovery-time filter test**

```python
    async def test_discovery_time_filter_excludes_hidden_tools(self) -> None:
        """Tools hidden from the LLM should be excluded from the discovered tool list."""
        # Test case 1: enabled_for_llm=True → included
        visible_tool = Mock(spec=RuntimeTool)
        visible_tool.enabled_for_llm = True
        
        # Test case 2: enabled_for_llm=False → excluded
        hidden_tool = Mock(spec=RuntimeTool)
        hidden_tool.enabled_for_llm = False
        
        registry = Mock(spec=RuntimeToolRegistry)
        
        def side_effect(name):
            if name == "visible":
                return visible_tool
            elif name == "hidden":
                return hidden_tool
            raise KeyError(name)
        
        registry.get.side_effect = side_effect
        
        # Act: discover tools
        result = await discover_tools(registry, cfg=self.cfg)
        
        # Assert: only the visible tool should be returned
        assert len(result) == 1
        assert result[0].name == "visible"
```

**Step 3: Add the policy-state filter test**

```python
    async def test_filter_respects_allowed_tools(self) -> None:
        """The filter should respect the current allowed_tools configuration."""
        # Test case 1: allowed_tools=["tool1"] → only tool1 included
        tool1 = Mock(spec=RuntimeTool)
        tool1.enabled_for_llm = True
        tool1.name = "tool1"
        
        tool2 = Mock(spec=RuntimeTool)
        tool2.enabled_for_llm = True
        tool2.name = "tool2"
        
        registry = Mock(spec=RuntimeToolRegistry)
        
        def side_effect(name):
            if name == "tool1":
                return tool1
            elif name == "tool2":
                return tool2
            raise KeyError(name)
        
        registry.get.side_effect = side_effect
        
        # Act: discover tools with allowed_tools=["tool1"]
        result = await discover_tools(registry, cfg=self.cfg)
        
        # Assert: only tool1 should be returned
        assert len(result) == 1
        assert result[0].name == "tool1"
```

## Compatibility considerations

- **No signature change**: The test methods follow the existing pattern in the file.
- **Mock compatibility**: Uses `unittest.mock.Mock` which is already imported in the file.

## Security considerations

This test validates a security property: that tools hidden from the LLM are correctly filtered out during discovery, preventing unauthorized access to restricted tools.

## Rollback considerations

If the test fails due to incorrect assumptions about the filter's behavior, revert to the previous test expectations and adjust accordingly.

## Validation plan

- Run the new tests: `uv run pytest tests/agent/test_tool_policy.py -v`
- Static analysis: `uv run mypy tests/agent/test_tool_policy.py` — confirm no type regressions.

## Completion criteria

- Discovery-time filter test passes.
- Policy-state filter test passes.
- All pre-existing tests in `tests/agent/test_tool_policy.py` continue to pass.

## Out of scope

- Tests for the disable-then-re-enable sequence in `apply_policy()` (covered by a separate document).
- Tests for the `/diff` bypass (covered by a separate document).
- Tests for the MDQ bypass (covered by a separate document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add discovery-time filter test | Pending | — | — | |
| 2 | Add policy-state filter test | Pending | — | — | |
| 3 | Validate all tests pass | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-103138_mcpagent04_runtime-policy-reload-reversibility.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-122227_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-202817
- **Related target files**: tests/agent/test_tool_policy.py
