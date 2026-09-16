## Goal

Add a test proving `ConfigLoader._allowed_files == frozenset({"agent.toml"})` unconditionally after `AgentContext()` construction, with no environment variable set.

## Scope

- Modify `tests/agent/test_context.py`: add one new test method.

## Assumptions

- The existing test classes bypass `__init__` via `AgentContext.__new__` (confirmed by direct read).
- The test must construct an `AgentContext` directly (not via `__new__`) to exercise the `restrict_to()` call.

## Design decisions

- Add a single new test method in a new test class `TestRestrictToUnconditional`.
- Use `pytest.importorskip` if any optional dependencies are needed.

## Alternatives considered

- Adding the test to an existing test class — rejected: would mix concerns; a dedicated class keeps the test focused.
- Creating a fixture instead of a test method — rejected: a simple test method is clearer for this assertion.

## Implementation

### Target file

`tests/agent/test_context.py`

### Procedure

1. Add a new test class `TestRestrictToUnconditional` with one test method.

### Method

- **Step 1**: Add the new test class:

```python
class TestRestrictToUnconditional:
    """REQ-001: AgentContext.__init__ calls restrict_to() unconditionally."""

    def test_restrict_to_called_unconditionally(self) -> None:
        """Proving ConfigLoader._allowed_files == frozenset({'agent.toml'}) after AgentContext() construction."""
        # Ensure AGENT_RESTRICT_CONFIG is NOT set
        import os
        original_value = os.environ.pop("AGENT_RESTRICT_CONFIG", None)
        
        try:
            from shared.config_loader import ConfigLoader
            from agent.context import AgentContext
            
            # Construct AgentContext directly (not via __new__)
            ctx = AgentContext()
            
            # Verify restrict_to() was called unconditionally
            assert ConfigLoader._allowed_files == frozenset({"agent.toml"})
        finally:
            # Restore original env var value
            if original_value is not None:
                os.environ["AGENT_RESTRICT_CONFIG"] = original_value
```

### Details

**Step 1 — Add the test class:**

After the existing test classes in `tests/agent/test_context.py`:

```python
class TestRestrictToUnconditional:
    """REQ-001: AgentContext.__init__ calls restrict_to() unconditionally."""

    def test_restrict_to_called_unconditionally(self) -> None:
        """Proving ConfigLoader._allowed_files == frozenset({'agent.toml'}) after AgentContext() construction."""
        # Ensure AGENT_RESTRICT_CONFIG is NOT set
        import os
        original_value = os.environ.pop("AGENT_RESTRICT_CONFIG", None)
        
        try:
            from shared.config_loader import ConfigLoader
            from agent.context import AgentContext
            
            # Construct AgentContext directly (not via __new__)
            ctx = AgentContext()
            
            # Verify restrict_to() was called unconditionally
            assert ConfigLoader._allowed_files == frozenset({"agent.toml"})
        finally:
            # Restore original env var value
            if original_value is not None:
                os.environ["AGENT_RESTRICT_CONFIG"] = original_value
```

The test ensures `AGENT_RESTRICT_CONFIG` is not set during execution (by popping it), constructs an `AgentContext` directly, and asserts that `ConfigLoader._allowed_files` equals `frozenset({"agent.toml"})`.

## Compatibility considerations

- No behavioral change. This is a test addition proving REQ-001's unconditional behavior.
- The test uses `os.environ.pop()` to ensure the env var is not set, which is safe because the test restores the original value afterward.

## Security considerations

- No security impact. This is a test addition proving REQ-001's unconditional behavior.

## Rollback considerations

- Reverting removes the test but does not affect source code.

## Validation plan

- Run unit tests: `uv run pytest tests/agent/test_context.py::TestRestrictToUnconditional -v`
- Verify the new test passes.
- Static analysis: `uv run ruff check tests/agent/test_context.py`, `uv run mypy tests/agent/test_context.py`.

## Completion criteria

- New test class added to `tests/agent/test_context.py`.
- Test proves `ConfigLoader._allowed_files == frozenset({"agent.toml"})` unconditionally.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `scripts/agent/context.py` source code — covered in previous row (REQ-001).
- Modifying `tests/conftest.py` — covered in previous row (REQ-001).
- Modifying `docs/adr/ADR-002-config-isolation.md` — covered in subsequent row (REQ-008).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add TestRestrictToUnconditional test class | Pending | — | — | |
| 2 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Source issue**: issues/20260914-103255_mcpagent07_config-isolation-schema-validation-loader-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-125251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: tests/agent/test_context.py
