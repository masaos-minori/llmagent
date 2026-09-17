## Goal

Add unit tests for the MDQ bypass prevention — verifying that `_execute_mdq()` denies execution when any tool is absent from `cfg.tool.allowed_tools`. (REQ-005; "Add unit tests for the MDQ bypass prevention in `tests/agent/commands/test_cmd_mdq.py`")

## Scope

- Add tests for the MDQ bypass prevention: verify that `_execute_mdq()` denies execution when any tool is absent from `cfg.tool.allowed_tools`.
- Verify that the denial message is written to the output channel.

## Assumptions

- The `check_preflight()` call has been added to `_execute_mdq()` (covered by a separate document — this row depends on its completion).
- The existing test infrastructure (fixtures, mocks) in `tests/agent/commands/test_cmd_mdq.py` is sufficient for these tests.

## Design decisions

- **Test structure**: Use a single test method per scenario for clarity.
- **Denial test**: Verify that `_execute_mdq()` writes a denial message and returns without executing when the tool is absent from `cfg.tool.allowed_tools`.
- **Allowance test**: Verify that `_execute_mdq()` executes normally when the tool is present in `cfg.tool.allowed_tools`.

## Alternatives considered

- **Parameterized test**: Could use `@pytest.mark.parametrize` for multiple scenarios, but separate test methods are clearer for complex state transitions.
- **Integration test vs. unit test**: Unit test is preferred because we want to isolate the command's behavior without involving the full agent lifecycle.

## Implementation

### Target file

`tests/agent/commands/test_cmd_mdq.py`

### Procedure

1. Create test methods in the existing test class for each scenario.
2. Write a test for denial:
   ```python
   async def test_mdq_search_denied_when_tool_not_in_allowed_tools(self) -> None:
       """_execute_mdq() should deny execution when the tool is absent from allowed_tools."""
       # Arrange: create a mixin with search_docs excluded from allowed_tools
       mixin = _MdqMixin(cfg=self.cfg, services=None)
       
       # Act: call _execute_mdq()
       await mixin._execute_mdq(
           tools=Mock(),
           tool_name="search_docs",
           tool_args={"query": "test"},
           success_label="search",
       )
       
       # Assert: a denial message should be written
       self.assertIn("[DENIED]", mixin._out.getvalue())
   ```
3. Write a test for allowance:
   ```python
   async def test_mdq_search_executed_when_tool_in_allowed_tools(self) -> None:
       """_execute_mdq() should execute normally when the tool is present in allowed_tools."""
       # Arrange: create a mixin with search_docs included in allowed_tools
       mixin = _MdqMixin(cfg=self.cfg, services=None)
       
       # Act: call _execute_mdq()
       await mixin._execute_mdq(
           tools=Mock(),
           tool_name="search_docs",
           tool_args={"query": "test"},
           success_label="search",
       )
       
       # Assert: no denial message should be written
       self.assertNotIn("[DENIED]", mixin._out.getvalue())
   ```

### Method

Add test methods to the existing test class. No new imports or dependencies.

### Details

**Step 1: Identify the existing test class**

Find the existing test class in `tests/agent/commands/test_cmd_mdq.py` (likely named `TestCmdMdq` or similar).

**Step 2: Add the denial test**

```python
    async def test_mdq_search_denied_when_tool_not_in_allowed_tools(self) -> None:
        """_execute_mdq() should deny execution when the tool is absent from allowed_tools."""
        # Arrange: create a mixin with search_docs excluded from allowed_tools
        # Note: cfg.tool.allowed_tools does not include "search_docs"
        
        # Act: call _execute_mdq()
        await self.mixin._execute_mdq(
            tools=Mock(),
            tool_name="search_docs",
            tool_args={"query": "test"},
            success_label="search",
        )
        
        # Assert: a denial message should be written
        output = self.mixin._out.getvalue()
        self.assertIn("[DENIED]", output)
        self.assertIn("search_docs", output.lower())
```

**Step 3: Add the allowance test**

```python
    async def test_mdq_search_executed_when_tool_in_allowed_tools(self) -> None:
        """_execute_mdq() should execute normally when the tool is present in allowed_tools."""
        # Arrange: create a mixin with search_docs included in allowed_tools
        # Note: cfg.tool.allowed_tools includes "search_docs"
        
        # Act: call _execute_mdq()
        await self.mixin._execute_mdq(
            tools=Mock(),
            tool_name="search_docs",
            tool_args={"query": "test"},
            success_label="search",
        )
        
        # Assert: no denial message should be written
        output = self.mixin._out.getvalue()
        self.assertNotIn("[DENIED]", output)
```

## Compatibility considerations

- **No signature change**: The test methods follow the existing pattern in the file.
- **Mock compatibility**: Uses `unittest.mock.Mock` which is already imported in the file.

## Security considerations

This test validates a security property: that tools hidden from the LLM are correctly denied during direct execution via the MDQ slash commands, preventing unauthorized access to restricted tools.

## Rollback considerations

If the test fails due to incorrect assumptions about the command's behavior, revert to the previous test expectations and adjust accordingly.

## Validation plan

- Run the new tests: `uv run pytest tests/agent/commands/test_cmd_mdq.py -v`
- Static analysis: `uv run mypy tests/agent/commands/test_cmd_mdq.py` — confirm no type regressions.

## Completion criteria

- Denial test passes.
- Allowance test passes.
- All pre-existing tests in `tests/agent/commands/test_cmd_mdq.py` continue to pass.

## Out of scope

- Tests for the disable-then-re-enable sequence in `apply_policy()` (covered by a separate document).
- Tests for the `/diff` bypass (covered by a separate document).
- Tests for the immutable base field default/override/preservation (covered by a separate document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add denial test | Pending | — | — | |
| 2 | Add allowance test | Pending | — | — | |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260914-103138_mcpagent04_runtime-policy-reload-reversibility.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-122227_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-202817
- **Related target files**: tests/agent/commands/test_cmd_mdq.py
