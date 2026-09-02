## Goal

Update the `test_startup.py` test suite to cover the REQ-001 strict-default behavior and the REQ-002 consequence.

## Scope

Modify `tests/agent/test_startup.py` only. Add tests for strict-default behavior and the REQ-002 consequence.

## Assumptions

- REQ-001's fix (making `load_all()` strict by default) is applied first.
- REQ-002's fix (explicit default for `security_profile`) is applied before testing its consequences.
- The existing test suite structure supports adding new test cases.

## Design decisions

- Add two new test methods: one for strict-default behavior, one for REQ-002 consequence.
- Use the existing `TestStartup` class pattern.

## Alternatives considered

- Modifying existing tests to change their expectations. Rejected because it risks breaking existing coverage.
- Creating a separate test class. Rejected because the existing class already covers related scenarios.

## Implementation

### Target file

`tests/agent/test_startup.py`

### Procedure

Add two new test methods to `TestStartup`:
1. Test that startup fails when `agent.toml` is missing (strict-default).
2. Test that `build_agent_config()` raises `ConfigMissingError` when `agent.toml` is missing (REQ-002 consequence).

### Method

1. After applying REQ-001 and REQ-002 fixes, read `tests/agent/test_startup.py` to find the appropriate location for new tests.
2. Add two new test methods following the existing naming convention.

### Details

1. Read `tests/agent/test_startup.py` around lines 50-100 to find the end of the `TestStartup` class.
2. Add the following test methods:

```python
def test_startup_fails_without_agent_toml(self):
    """REQ-001: Startup fails when agent.toml is missing (strict-default)."""
    # Arrange: patch ConfigLoader to raise ConfigMissingError
    with patch('scripts.shared.config_loader.ConfigLoader') as mock_loader:
        mock_loader.return_value.load_all.side_effect = ConfigMissingError("agent.toml")
        # Act & Assert
        with pytest.raises(ConfigMissingError):
            startup()

def test_build_agent_config_requires_agent_toml(self):
    """REQ-002: build_agent_config() raises ConfigMissingError when agent.toml is missing."""
    # Arrange: patch ConfigLoader to return empty config
    with patch('scripts.agent.config_builders.ConfigLoader') as mock_loader:
        mock_loader.return_value.load_all.side_effect = ConfigMissingError("agent.toml")
        # Act & Assert
        with pytest.raises(ConfigMissingError):
            build_agent_config()
```

## Compatibility considerations

- Existing tests remain unchanged. New tests add coverage without modifying existing assertions.

## Security considerations

- These tests verify the fail-closed behavior required by ADR-004 INV-01/INV-02.

## Rollback considerations

- Remove the two new test methods if REQ-001 or REQ-002 is rolled back. No other rollback needed.

## Validation plan

Run `uv run pytest tests/agent/test_startup.py -v` to confirm all tests pass including the new ones.

## Completion criteria

- Two new test methods added covering strict-default and REQ-002 consequence
- All tests in `tests/agent/test_startup.py` pass

## Out of scope

- Changes to other test files (handled by their respective documents)
- Unknown-key rejection tests (REQ-004, handled separately)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-191443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-220059
- **Related target files**: tests/agent/test_startup.py
