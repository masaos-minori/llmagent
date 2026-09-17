## Goal

Rewrite `test_multiple_restrict_calls_last_wins` and `test_reload_without_restriction`; add a new test for the reset mechanism.

## Scope

- Modify `tests/shared/test_config_loader.py`: update two existing tests and add a new one.

## Assumptions

- REQ-002's `_reset_for_testing()` classmethod exists (covered in previous row).
- The existing `TestGlobalStateCleanup` class provides a good home for these tests.

## Design decisions

- Rename `test_multiple_restrict_calls_last_wins` to `test_second_restrict_call_is_rejected` to reflect the new assertion.
- Rewrite `test_reload_without_restriction` to use `_reset_for_testing()` instead of direct attribute write.
- Add a separate test for the reset mechanism.

## Alternatives considered

- Creating a new test class for each requirement — rejected: adds unnecessary class proliferation.
- Merging all three requirements into one test — rejected: clarity benefits from separation.

## Implementation

### Target file

`tests/shared/test_config_loader.py`

### Procedure

1. Rename and rewrite `test_multiple_restrict_calls_last_wins` for REQ-002.
2. Migrate `test_reload_without_restriction` to use `_reset_for_testing()`.
3. Add a new test for the reset mechanism.

### Method

- **Step 1**: In `TestGlobalStateCleanup`, rename and rewrite `test_multiple_restrict_calls_last_wins`:

```python
# Before:
def test_multiple_restrict_calls_last_wins(self) -> None:
    ConfigLoader.restrict_to("a.toml")
    ConfigLoader.restrict_to("b.toml")
    assert ConfigLoader._allowed_files == frozenset({"b.toml"})

# After:
def test_second_restrict_call_is_rejected(self) -> None:
    """REQ-002: a second restrict_to() call with different filenames is rejected."""
    ConfigLoader.restrict_to("a.toml")
    with pytest.raises(ConfigPermissionError):
        ConfigLoader.restrict_to("b.toml")
    # Original restriction should still be in effect
    assert ConfigLoader._allowed_files == frozenset({"a.toml"})
```

- **Step 2**: Rewrite `test_reload_without_restriction`:

```python
# Before:
def test_reload_without_restriction(self) -> None:
    ConfigLoader._allowed_files = None  # Direct write — bypasses restrict_to()
    loader = ConfigLoader()
    result = loader.load_all(strict=False)
    assert isinstance(result, dict)

# After:
def test_reload_without_restriction_via_reset(self) -> None:
    """REQ-002: _reset_for_testing() allows reloading without restriction."""
    ConfigLoader.restrict_to("agent.toml")
    ConfigLoader._reset_for_testing()  # Use the new reset method
    loader = ConfigLoader()
    result = loader.load_all(strict=False)
    assert isinstance(result, dict)
```

- **Step 3**: Add a new test for the reset mechanism:

```python
class TestResetForTesting:
    """REQ-002: test-only reset mechanism."""

    def test_reset_clears_allowed_files(self) -> None:
        """_reset_for_testing() sets _allowed_files back to None."""
        ConfigLoader.restrict_to("agent.toml")
        ConfigLoader._reset_for_testing()
        assert ConfigLoader._allowed_files is None

    def test_reset_allows_subsequent_restrict_to(self) -> None:
        """After _reset_for_testing(), a subsequent restrict_to() succeeds."""
        ConfigLoader.restrict_to("agent.toml")
        ConfigLoader._reset_for_testing()
        ConfigLoader.restrict_to("other.toml")  # Should succeed
        assert ConfigLoader._allowed_files == frozenset({"other.toml"})
```

### Details

**Step 1 — Rewrite test_multiple_restrict_calls_last_wins:**

Replace lines ~50-55 in `TestGlobalStateCleanup`:

```python
def test_second_restrict_call_is_rejected(self) -> None:
    """REQ-002: a second restrict_to() call with different filenames is rejected."""
    ConfigLoader.restrict_to("a.toml")
    with pytest.raises(ConfigPermissionError):
        ConfigLoader.restrict_to("b.toml")
    # Original restriction should still be in effect
    assert ConfigLoader._allowed_files == frozenset({"a.toml"})
```

**Step 2 — Rewrite test_reload_without_restriction:**

Replace lines ~60-65 in `TestGlobalStateCleanup`:

```python
def test_reload_without_restriction_via_reset(self) -> None:
    """REQ-002: _reset_for_testing() allows reloading without restriction."""
    ConfigLoader.restrict_to("agent.toml")
    ConfigLoader._reset_for_testing()  # Use the new reset method
    loader = ConfigLoader()
    result = loader.load_all(strict=False)
    assert isinstance(result, dict)
```

**Step 3 — Add reset mechanism tests:**

Add after `TestGlobalStateCleanup`:

```python
class TestResetForTesting:
    """REQ-002: test-only reset mechanism."""

    def test_reset_clears_allowed_files(self) -> None:
        """_reset_for_testing() sets _allowed_files back to None."""
        ConfigLoader.restrict_to("agent.toml")
        ConfigLoader._reset_for_testing()
        assert ConfigLoader._allowed_files is None

    def test_reset_allows_subsequent_restrict_to(self) -> None:
        """After _reset_for_testing(), a subsequent restrict_to() succeeds."""
        ConfigLoader.restrict_to("agent.toml")
        ConfigLoader._reset_for_testing()
        ConfigLoader.restrict_to("other.toml")  # Should succeed
        assert ConfigLoader._allowed_files == frozenset({"other.toml"})
```

## Compatibility considerations

- Renamed test replaces the old assertion; all other tests in `TestGlobalStateCleanup` are unchanged.
- New tests use the existing `_make_executor()` helper pattern.

## Security considerations

- No security impact. This is a behavioral change test for REQ-002.

## Rollback considerations

- Reverting the test changes restores the pre-fix test suite but does not affect source code.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_config_loader.py -v`
- Verify the renamed test passes with the new rejection assertion.
- Verify the reset mechanism tests pass.
- Static analysis: `uv run ruff check tests/shared/test_config_loader.py`, `uv run mypy tests/shared/test_config_loader.py`.

## Completion criteria

- `test_second_restrict_call_is_rejected` asserts rejection of a second, different call.
- `test_reload_without_restriction_via_reset` uses `_reset_for_testing()`.
- Reset mechanism tests verify `_reset_for_testing()` behavior.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `scripts/shared/config_loader.py` source code — covered in previous row (REQ-002).
- Modifying `AgentContext.__init__` — covered in subsequent row (REQ-001).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite test_multiple_restrict_calls_last_wins for REQ-002 | Completed | 20260917-195747 | 20260917-195747 |  |
| 2 | Migrate test_reload_without_restriction to use reset classmethod | Completed | 20260917-195747 | 20260917-195747 |  |
| 3 | Add reset mechanism tests | Completed | 20260917-195748 | 20260917-195748 |  |
| 4 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-195748 | 20260917-195748 |  |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-195748 | 20260917-195748 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260914-103255_mcpagent07_config-isolation-schema-validation-loader-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-125251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: tests/shared/test_config_loader.py