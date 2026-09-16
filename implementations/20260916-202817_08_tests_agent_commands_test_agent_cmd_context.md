## Goal

Add unit tests for the `/diff` bypass prevention — verifying that `_cmd_diff()` denies execution when `git_diff` is absent from `cfg.tool.allowed_tools`. (REQ-004; "Add unit tests for the /diff bypass prevention in `tests/agent/commands/test_agent_cmd_context.py`")

## Scope

- Add tests for the `/diff` bypass prevention: verify that `_cmd_diff()` denies execution when `git_diff` is absent from `cfg.tool.allowed_tools`.
- Verify that the denial message is written to the output channel.

## Assumptions

- The `check_preflight()` call has been added to `_cmd_diff()` (covered by a separate document — this row depends on its completion).
- The existing test infrastructure (fixtures, mocks) in `tests/agent/commands/test_agent_cmd_context.py` is sufficient for these tests.

## Design decisions

- **Test structure**: Use a single test method per scenario for clarity.
- **Denial test**: Verify that `_cmd_diff()` writes a denial message and returns without executing when `git_diff` is absent from `cfg.tool.allowed_tools`.
- **Allowance test**: Verify that `_cmd_diff()` executes normally when `git_diff` is present in `cfg.tool.allowed_tools`.

## Alternatives considered

- **Parameterized test**: Could use `@pytest.mark.parametrize` for multiple scenarios, but separate test methods are clearer for complex state transitions.
- **Integration test vs. unit test**: Unit test is preferred because we want to isolate the command's behavior without involving the full agent lifecycle.

## Implementation

### Target file

`tests/agent/commands/test_agent_cmd_context.py`

### Procedure

1. Create test methods in the existing test class for each scenario.
2. Write a test for denial:
   ```python
   async def test_diff_denied_when_git_diff_not_in_allowed_tools(self) -> None:
       """_cmd_diff() should deny execution when git_diff is absent from allowed_tools."""
       # Arrange: create a command with git_diff excluded from allowed_tools
       cmd = CmdContext(cfg=self.cfg, services=None)
       
       # Act: call _cmd_diff()
       await cmd._cmd_diff("")
       
       # Assert: a denial message should be written
       self.assertIn("[DENIED]", cmd._out.getvalue())
   ```
3. Write a test for allowance:
   ```python
   async def test_diff_executed_when_git_diff_in_allowed_tools(self) -> None:
       """_cmd_diff() should execute normally when git_diff is present in allowed_tools."""
       # Arrange: create a command with git_diff included in allowed_tools
       cmd = CmdContext(cfg=self.cfg, services=None)
       
       # Act: call _cmd_diff()
       await cmd._cmd_diff("")
       
       # Assert: no denial message should be written
       self.assertNotIn("[DENIED]", cmd._out.getvalue())
   ```

### Method

Add test methods to the existing test class. No new imports or dependencies.

### Details

**Step 1: Identify the existing test class**

Find the existing test class in `tests/agent/commands/test_agent_cmd_context.py` (likely named `TestCmdContext` or similar).

**Step 2: Add the denial test**

```python
    async def test_diff_denied_when_git_diff_not_in_allowed_tools(self) -> None:
        """_cmd_diff() should deny execution when git_diff is absent from allowed_tools."""
        # Arrange: create a command with git_diff excluded from allowed_tools
        # Note: cfg.tool.allowed_tools does not include "git_diff"
        
        # Act: call _cmd_diff()
        await self.cmd._cmd_diff("")
        
        # Assert: a denial message should be written
        output = self.cmd._out.getvalue()
        self.assertIn("[DENIED]", output)
        self.assertIn("git_diff", output.lower())
```

**Step 3: Add the allowance test**

```python
    async def test_diff_executed_when_git_diff_in_allowed_tools(self) -> None:
        """_cmd_diff() should execute normally when git_diff is present in allowed_tools."""
        # Arrange: create a command with git_diff included in allowed_tools
        # Note: cfg.tool.allowed_tools includes "git_diff"
        
        # Act: call _cmd_diff()
        await self.cmd._cmd_diff("")
        
        # Assert: no denial message should be written
        output = self.cmd._out.getvalue()
        self.assertNotIn("[DENIED]", output)
```

## Compatibility considerations

- **No signature change**: The test methods follow the existing pattern in the file.
- **Mock compatibility**: Uses `unittest.mock.Mock` which is already imported in the file.

## Security considerations

This test validates a security property: that tools hidden from the LLM are correctly denied during direct execution via the `/diff` command, preventing unauthorized access to restricted tools.

## Rollback considerations

If the test fails due to incorrect assumptions about the command's behavior, revert to the previous test expectations and adjust accordingly.

## Validation plan

- Run the new tests: `uv run pytest tests/agent/commands/test_agent_cmd_context.py -v`
- Static analysis: `uv run mypy tests/agent/commands/test_agent_cmd_context.py` — confirm no type regressions.

## Completion criteria

- Denial test passes.
- Allowance test passes.
- All pre-existing tests in `tests/agent/commands/test_agent_cmd_context.py` continue to pass.

## Out of scope

- Tests for the disable-then-re-enable sequence in `apply_policy()` (covered by a separate document).
- Tests for the MDQ bypass (covered by a separate document).
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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260914-103138_mcpagent04_runtime-policy-reload-reversibility.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-122227_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-202817
- **Related target files**: tests/agent/commands/test_agent_cmd_context.py
