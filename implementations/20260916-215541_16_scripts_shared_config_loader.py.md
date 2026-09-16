## Goal

Add a test-only reset classmethod to `ConfigLoader` and make `restrict_to()` reject a later call that changes `_allowed_files` unless made through that reset path.

## Scope

- Modify `scripts/shared/config_loader.py`: add `_reset_for_testing()` classmethod and update `restrict_to()` to reject broadening.

## Assumptions

- The new reset method should be a public classmethod named `_reset_for_testing()` per UNK-02 resolution.
- Rejection should raise `ConfigPermissionError` (consistent with other permission failures in this module).

## Design decisions

- Add `_reset_for_testing()` as a public classmethod that sets `_allowed_files = None`.
- In `restrict_to()`, check if `_allowed_files` is already set to a different set before allowing the change — raise `ConfigPermissionError` if it differs.
- The reset method clears `_allowed_files` first, then allows the next `restrict_to()` call to succeed.

## Alternatives considered

- Using a dedicated exception type for the rejection — rejected: adds unnecessary exception hierarchy; `ConfigPermissionError` already covers this case.
- Adding a boolean flag to track whether `restrict_to()` has been called — rejected: `_allowed_files is not None` already serves this purpose.

## Implementation

### Target file

`scripts/shared/config_loader.py`

### Procedure

1. Add `_reset_for_testing()` classmethod after `restrict_to()`.
2. Update `restrict_to()` to check for existing allowed-file set before allowing changes.

### Method

- **Step 1**: Add `_reset_for_testing()` after `restrict_to()`:

```python
@classmethod
def _reset_for_testing(cls) -> None:
    """Reset the allowed-file restriction for testing purposes only.

    This is a test-only mechanism. Production code MUST NOT call this method.
    After calling this, the next call to restrict_to() will establish a new
    allowed-file set.
    """
    cls._allowed_files = None
```

- **Step 2**: Update `restrict_to()`:

```python
# Before (lines 40-49):
@classmethod
def restrict_to(cls, *filenames: str) -> None:
    """Restrict this process to loading only the specified config files.

    Call once at process startup (before any config is loaded). Any
    subsequent call to load() or load_all() that touches a file not in
    this set raises ConfigPermissionError.
    """
    if not filenames:
        raise ValueError("restrict_to() requires at least one filename.")
    cls._allowed_files = frozenset(filenames)

# After:
@classmethod
def restrict_to(cls, *filenames: str) -> None:
    """Restrict this process to loading only the specified config files.

    Call once at process startup (before any config is loaded). Any
    subsequent call to load() or load_all() that touches a file not in
    this set raises ConfigPermissionError.

    Raises:
        ConfigPermissionError: If a second, different restrict_to() call is
            attempted without first calling _reset_for_testing().
    """
    if not filenames:
        raise ValueError("restrict_to() requires at least one filename.")
    new_set = frozenset(filenames)
    if cls._allowed_files is not None and cls._allowed_files != new_set:
        msg = (
            f"Cannot change allowed-file set from {cls._allowed_files} to {new_set}. "
            "Call _reset_for_testing() first if this is a test-only reset."
        )
        raise ConfigPermissionError(msg)
    cls._allowed_files = new_set
```

### Details

**Step 1 — Add reset method:**

After line 49 (`cls._allowed_files = frozenset(filenames)`), add:

```python
@classmethod
def _reset_for_testing(cls) -> None:
    """Reset the allowed-file restriction for testing purposes only.

    This is a test-only mechanism. Production code MUST NOT call this method.
    After calling this, the next call to restrict_to() will establish a new
    allowed-file set.
    """
    cls._allowed_files = None
```

**Step 2 — Update restrict_to():**

Replace lines 40-49 as shown above. Key changes:
- Check if `_allowed_files` is already set to a different set
- Raise `ConfigPermissionError` if the sets differ
- Add docstring documenting the new `ConfigPermissionError` raise

## Compatibility considerations

- Existing tests asserting "last call wins" behavior must be rewritten (REQ-002).
- Tests that need to change the allowed-file set between calls must use `_reset_for_testing()` first.
- Production code that currently relies on multiple `restrict_to()` calls must be reviewed.

## Security considerations

- REQ-002 improves security by preventing accidental broadening of the allowed-file set after initialization.

## Rollback considerations

- Reverting removes the rejection logic but does not break existing behavior.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_config_loader.py -v`
- Verify `restrict_to()` rejects a second, different call.
- Verify `_reset_for_testing()` allows a subsequent `restrict_to()` call.
- Static analysis: `uv run ruff check scripts/shared/config_loader.py`, `uv run mypy scripts/shared/config_loader.py`.

## Completion criteria

- `_reset_for_testing()` classmethod added.
- `restrict_to()` rejects a second, different call with `ConfigPermissionError`.
- All existing tests pass after updates.
- No new lint/type errors introduced.

## Out of scope

- Modifying `AgentContext.__init__` — covered in subsequent row (REQ-001).
- Modifying `tests/conftest.py` — covered in subsequent row (REQ-001).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add _reset_for_testing() and update restrict_to() | Pending | — | — | |
| 2 | Rewrite test_multiple_restrict_calls_last_wins | Pending | — | — | See next row |
| 3 | Migrate test_reload_without_restriction to use reset classmethod | Pending | — | — | See next row |
| 4 | Add test for reset classmethod | Pending | — | — | See next row |
| 5 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 6 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: scripts/shared/config_loader.py
