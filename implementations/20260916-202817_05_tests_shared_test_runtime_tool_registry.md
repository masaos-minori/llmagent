## Goal

Add unit tests for the disable-then-re-enable sequence in `RuntimeToolRegistry.apply_policy()` — verifying that a tool disabled by one `apply_policy()` call becomes re-enabled by a subsequent call when included in `allowed_tools`. (REQ-003; "Add a disable-then-re-enable regression test in `tests/shared/test_runtime_tool_registry.py`")

## Scope

- Add a test class or test methods in `tests/shared/test_runtime_tool_registry.py` covering the disable-then-re-enable scenario.
- Test that `enabled_for_llm` transitions from `True` → `False` → `True` across three `apply_policy()` calls.
- Test that the atomic swap invariant holds (one dict identity change per call).

## Assumptions

- The `llm_visibility_base` field exists on `RuntimeTool` (covered by a separate document — this row depends on its completion).
- The `apply_policy()` formula has been rewritten to use the immutable base field (covered by a separate document — this row depends on its completion).
- The existing test infrastructure (fixtures, mocks) in `tests/shared/test_runtime_tool_registry.py` is sufficient for this test.

## Design decisions

- **Test structure**: Use a single test method per scenario (disable, re-enable, both together) for clarity.
- **Atomic swap assertion**: Verify the `_tools` mapping reference changes identity exactly once per call using `is not` comparison.

## Alternatives considered

- **Parameterized test**: Could use `@pytest.mark.parametrize` for multiple scenarios, but separate test methods are clearer for complex state transitions.
- **Integration test vs. unit test**: Unit test is preferred because we want to isolate the registry's behavior without involving the full agent lifecycle.

## Implementation

### Target file

`tests/shared/test_runtime_tool_registry.py`

### Procedure

1. Create a new test class or add test methods to an existing test class.
2. Write a test for disable-then-re-enable:
   ```python
   async def test_disable_then_re_enable(self) -> None:
       """A tool disabled by one apply_policy() call should become re-enabled by a subsequent call."""
       # Arrange: create a registry with a tool visible to LLM
       registry = RuntimeToolRegistry(
           cfg=self.cfg,
           tools={"test_tool": Mock(spec=RuntimeTool)},
       )
       
       # Act: first call disables the tool
       await registry.apply_policy(tier_map={}, allowed_tools=[])
       
       # Assert: tool is now disabled
       assert registry.get("test_tool").enabled_for_llm is False
       
       # Act: second call re-enables the tool
       await registry.apply_policy(tier_map={}, allowed_tools=["test_tool"])
       
       # Assert: tool is now re-enabled
       assert registry.get("test_tool").enabled_for_llm is True
   ```
3. Write a test for atomic swap:
   ```python
   async def test_atomic_swap_single_identity_change(self) -> None:
       """The _tools mapping should change identity exactly once per apply_policy() call."""
       registry = RuntimeToolRegistry(
           cfg=self.cfg,
           tools={"test_tool": Mock(spec=RuntimeTool)},
       )
       
       old_tools = registry._tools
       
       # Act: apply policy
       await registry.apply_policy(tier_map={}, allowed_tools=["test_tool"])
       
       # Assert: the mapping changed identity
       assert registry._tools is not old_tools
   ```

### Method

Add test methods to the existing test class. No new imports or dependencies.

### Details

**Step 1: Identify the existing test class**

Find the existing test class in `tests/shared/test_runtime_tool_registry.py` (likely named `TestRuntimeToolRegistry` or similar).

**Step 2: Add the disable-then-re-enable test**

```python
    async def test_disable_then_re_enable(self) -> None:
        """A tool disabled by one apply_policy() call should become re-enabled by a subsequent call."""
        # Arrange: create a registry with a tool visible to LLM
        tool = Mock(spec=RuntimeTool)
        tool.llm_visibility_base = True
        tool.enabled_for_llm = True
        
        registry = RuntimeToolRegistry(
            cfg=self.cfg,
            tools={"test_tool": tool},
        )
        
        # Act: first call disables the tool
        await registry.apply_policy(tier_map={}, allowed_tools=[])
        
        # Assert: tool is now disabled
        assert registry.get("test_tool").enabled_for_llm is False
        
        # Act: second call re-enables the tool
        await registry.apply_policy(tier_map={}, allowed_tools=["test_tool"])
        
        # Assert: tool is now re-enabled
        assert registry.get("test_tool").enabled_for_llm is True
```

**Step 3: Add the atomic swap test**

```python
    async def test_atomic_swap_single_identity_change(self) -> None:
        """The _tools mapping should change identity exactly once per apply_policy() call."""
        tool = Mock(spec=RuntimeTool)
        tool.llm_visibility_base = True
        tool.enabled_for_llm = True
        
        registry = RuntimeToolRegistry(
            cfg=self.cfg,
            tools={"test_tool": tool},
        )
        
        old_tools = registry._tools
        
        # Act: apply policy
        await registry.apply_policy(tier_map={}, allowed_tools=["test_tool"])
        
        # Assert: the mapping changed identity
        assert registry._tools is not old_tools
```

## Compatibility considerations

- **No signature change**: The test methods follow the existing pattern in the file.
- **Mock compatibility**: Uses `unittest.mock.Mock` which is already imported in the file.

## Security considerations

This test validates a security property: that tools can be re-enabled after being disabled, preventing permanent lockout due to cumulative mutation.

## Rollback considerations

If the test fails due to incorrect assumptions about the registry's behavior, revert to the previous test expectations and adjust accordingly.

## Validation plan

- Run the new tests: `uv run pytest tests/shared/test_runtime_tool_registry.py::TestRuntimeToolRegistry::test_disable_then_re_enable -v`
- Run all registry tests: `uv run pytest tests/shared/test_runtime_tool_registry.py -v`
- Static analysis: `uv run mypy tests/shared/test_runtime_tool_registry.py` — confirm no type regressions.

## Completion criteria

- Disable-then-re-enable test passes.
- Atomic swap test passes.
- All pre-existing tests in `tests/shared/test_runtime_tool_registry.py` continue to pass.

## Out of scope

- Tests for the immutable base field default/override/preservation (covered by a separate document).
- Tests for the `/diff` bypass (covered by a separate document).
- Tests for the MDQ bypass (covered by a separate document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add disable-then-re-enable test | Pending | — | — | |
| 2 | Add atomic swap test | Pending | — | — | |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260914-103138_mcpagent04_runtime-policy-reload-reversibility.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-122227_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-202817
- **Related target files**: tests/shared/test_runtime_tool_registry.py
