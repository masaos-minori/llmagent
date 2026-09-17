## Goal

Cross-reference each exception class in `scripts/shared/config_errors.py` with the loader method(s) that raise it, supporting REQ-003's "document all loader exception types" requirement.

## Scope

- Modify `scripts/shared/config_errors.py`: add cross-references to each exception class's docstring indicating which `ConfigLoader` methods raise it.

## Assumptions

- The module currently documents each class's own meaning but not which `ConfigLoader` method raises it.
- Each exception should list all methods that can raise it.

## Design decisions

- Add a "Raised by:" section to each exception class's docstring listing the relevant `ConfigLoader` methods.

## Alternatives considered

- Adding a separate mapping constant — rejected: adds unnecessary indirection; docstrings are the canonical place for this information.
- Creating a new exception hierarchy — rejected: out of scope for REQ-003.

## Implementation

### Target file

`scripts/shared/config_errors.py`

### Procedure

1. Update each exception class's docstring to include a "Raised by:" section.

### Method

- **Step 1**: Update each exception class's docstring:

```python
# Before (example):
class ConfigMissingError(RuntimeError):
    """A required configuration file was not found."""

# After:
class ConfigMissingError(RuntimeError):
    """A required configuration file was not found.

    Raised by:
        ConfigLoader.load()
        ConfigLoader.load_all()
    """

# Similar updates for ConfigParseError, ConfigReadError, ConfigPermissionError.
```

### Details

**Step 1 — Update exception docstrings:**

For each exception class in `scripts/shared/config_errors.py`:

```python
class ConfigMissingError(RuntimeError):
    """A required configuration file was not found.

    Raised by:
        ConfigLoader.load()
        ConfigLoader.load_all()
    """

class ConfigParseError(RuntimeError):
    """A configuration file failed to parse (TOML or JSON).

    Raised by:
        ConfigLoader.load()
        ConfigLoader.load_all()
    """

class ConfigReadError(RuntimeError):
    """A configuration file could not be read from disk.

    Raised by:
        ConfigLoader.load()
        ConfigLoader.load_all()
    """

class ConfigPermissionError(RuntimeError):
    """The process is not permitted to load the requested configuration file.

    Raised by:
        ConfigLoader.load()
        ConfigLoader.load_all()
        ConfigLoader.restrict_to()
    """
```

## Compatibility considerations

- No behavioral change. This is a documentation-only update.
- Existing assertions checking exception types remain valid.

## Security considerations

- No security impact. This is a documentation improvement.

## Rollback considerations

- Reverting removes the cross-references but does not affect other functionality.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_config_loader.py::TestCustomExceptionTypes -v`
- Verify existing exception-type assertions still pass.
- Static analysis: `uv run ruff check scripts/shared/config_errors.py`, `uv run mypy scripts/shared/config_errors.py`.

## Completion criteria

- Each exception class's docstring includes a "Raised by:" section.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `config_loader.py` source code — covered in previous row (REQ-002).
- Modifying `AgentContext.__init__` — covered in subsequent row (REQ-001).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update exception docstrings with "Raised by:" sections | Completed | 20260917-192647 | 20260917-192647 |  |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-192648 | 20260917-192648 |  |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-192648 | 20260917-192648 |  |

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
- **Source issue**: issues/20260914-103255_mcpagent07_config-isolation-schema-validation-loader-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-125251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/shared/config_errors.py