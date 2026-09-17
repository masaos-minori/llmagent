## Goal

Add unit tests for the immutable `llm_visibility_base` field on `RuntimeTool` — verifying default resolution (mirrors `enabled_for_llm` when omitted), explicit override, and preservation under `dataclasses.replace()` (as used by `apply_policy()`). (REQ-001; "Add unit tests for the immutable base field in `tests/shared/test_runtime_tool.py`")

## Scope

- Add tests for default resolution: `llm_visibility_base` defaults to mirroring `enabled_for_llm` when omitted.
- Add tests for explicit override: `llm_visibility_base=True/False` overrides the default.
- Add tests for `dataclasses.replace()` preservation: the immutable base field carries forward unchanged.

## Assumptions

- The `llm_visibility_base` field exists on `RuntimeTool` (covered by a separate document — this row depends on its completion).
- The existing test infrastructure (fixtures, mocks) in `tests/shared/test_runtime_tool.py` is sufficient for these tests.

## Design decisions

- **Test structure**: Use a single test method per scenario for clarity.
- **Default resolution test**: Verify both `True` and `False` cases (when `enabled_for_llm=True`, default should be `True`; when `enabled_for_llm=False`, default should be `False`).
- **Explicit override test**: Verify that `llm_visibility_base=True` overrides even when `enabled_for_llm=False`.
- **Preservation test**: Verify that `dataclasses.replace()` preserves the field without explicitly passing it.

## Alternatives considered

- **Parameterized test**: Could use `@pytest.mark.parametrize` for multiple scenarios, but separate test methods are clearer for complex state transitions.
- **Integration test vs. unit test**: Unit test is preferred because we want to isolate the dataclass's behavior without involving the full agent lifecycle.

## Implementation

### Target file

`tests/shared/test_runtime_tool.py`

### Procedure

1. Create test methods in the existing test class for each scenario.
2. Write a test for default resolution:
   ```python
   async def test_llm_visibility_base_defaults_to_enabled_for_llm(self) -> None:
       """When llm_visibility_base is omitted, it should mirror enabled_for_llm."""
       # Arrange: create a RuntimeTool with enabled_for_llm=True
       tool = RuntimeTool(
           name="test_tool",
           description="Test tool",
           enabled_for_llm=True,
       )
       
       # Assert: llm_visibility_base should mirror enabled_for_llm
       assert tool.llm_visibility_base is True
   ```
3. Write a test for explicit override:
   ```python
   async def test_llm_visibility_base_explicit_override(self) -> None:
       """An explicit llm_visibility_base value should override the default."""
       # Arrange: create a RuntimeTool with enabled_for_llm=False but llm_visibility_base=True
       tool = RuntimeTool(
           name="test_tool",
           description="Test tool",
           enabled_for_llm=False,
           llm_visibility_base=True,
       )
       
       # Assert: llm_visibility_base should be True (explicitly set)
       assert tool.llm_visibility_base is True
   ```
4. Write a test for `dataclasses.replace()` preservation:
   ```python
   async def test_llm_visibility_base_preserved_under_replace(self) -> None:
       """The llm_visibility_base field should be preserved under dataclasses.replace()."""
       # Arrange: create a RuntimeTool with llm_visibility_base=True
       tool = RuntimeTool(
           name="test_tool",
           description="Test tool",
           enabled_for_llm=True,
           llm_visibility_base=True,
       )
       
       # Act: replace another field
       replaced = dataclasses.replace(tool, description="Updated description")
       
       # Assert: llm_visibility_base should still be True
       assert replaced.llm_visibility_base is True
   ```

### Method

Add test methods to the existing test class. No new imports or dependencies.

### Details

**Step 1: Identify the existing test class**

Find the existing test class in `tests/shared/test_runtime_tool.py` (likely named `TestRuntimeTool` or similar).

**Step 2: Add the default resolution test**

```python
    async def test_llm_visibility_base_defaults_to_enabled_for_llm(self) -> None:
        """When llm_visibility_base is omitted, it should mirror enabled_for_llm."""
        # Test case 1: enabled_for_llm=True → llm_visibility_base=True
        tool_true = RuntimeTool(
            name="test_tool",
            description="Test tool",
            enabled_for_llm=True,
        )
        assert tool_true.llm_visibility_base is True
        
        # Test case 2: enabled_for_llm=False → llm_visibility_base=False
        tool_false = RuntimeTool(
            name="test_tool",
            description="Test tool",
            enabled_for_llm=False,
        )
        assert tool_false.llm_visibility_base is False
```

**Step 3: Add the explicit override test**

```python
    async def test_llm_visibility_base_explicit_override(self) -> None:
        """An explicit llm_visibility_base value should override the default."""
        # Test case 1: enabled_for_llm=False, llm_visibility_base=True
        tool = RuntimeTool(
            name="test_tool",
            description="Test tool",
            enabled_for_llm=False,
            llm_visibility_base=True,
        )
        assert tool.llm_visibility_base is True
        
        # Test case 2: enabled_for_llm=True, llm_visibility_base=False
        tool2 = RuntimeTool(
            name="test_tool",
            description="Test tool",
            enabled_for_llm=True,
            llm_visibility_base=False,
        )
        assert tool2.llm_visibility_base is False
```

**Step 4: Add the preservation test**

```python
    async def test_llm_visibility_base_preserved_under_replace(self) -> None:
        """The llm_visibility_base field should be preserved under dataclasses.replace()."""
        # Arrange: create a RuntimeTool with llm_visibility_base=True
        tool = RuntimeTool(
            name="test_tool",
            description="Test tool",
            enabled_for_llm=True,
            llm_visibility_base=True,
        )
        
        # Act: replace another field
        replaced = dataclasses.replace(tool, description="Updated description")
        
        # Assert: llm_visibility_base should still be True
        assert replaced.llm_visibility_base is True
```

## Compatibility considerations

- **No signature change**: The test methods follow the existing pattern in the file.
- **Mock compatibility**: Uses `unittest.mock.Mock` which is already imported in the file.

## Security considerations

This test validates a security property: that the immutable base field cannot be accidentally mutated during policy application, ensuring tools can be re-enabled after being disabled.

## Rollback considerations

If the test fails due to incorrect assumptions about the dataclass's behavior, revert to the previous test expectations and adjust accordingly.

## Validation plan

- Run the new tests: `uv run pytest tests/shared/test_runtime_tool.py -v`
- Static analysis: `uv run mypy tests/shared/test_runtime_tool.py` — confirm no type regressions.

## Completion criteria

- Default resolution test passes.
- Explicit override test passes.
- Preservation test passes.
- All pre-existing tests in `tests/shared/test_runtime_tool.py` continue to pass.

## Out of scope

- Tests for the disable-then-re-enable sequence in `apply_policy()` (covered by a separate document).
- Tests for the `/diff` bypass (covered by a separate document).
- Tests for the MDQ bypass (covered by a separate document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add default resolution test | Pending | — | — | |
| 2 | Add explicit override test | Pending | — | — | |
| 3 | Add preservation test | Pending | — | — | |
| 4 | Validate all tests pass | Pending | — | — | |

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
- **Related target files**: tests/shared/test_runtime_tool.py
