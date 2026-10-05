## Goal

Add regression test verifying that AppServices constructor rejects None for required services.

## Scope

- Create `tests/agent/test_context.py` with test for AppServices validation

## Assumptions

- The test framework uses pytest
- AppServices is importable from `scripts.agent.context`

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Test each required service individually to verify error message includes the service name
- Verify memory can still be None (optional service)

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real service injection — too brittle, slow

## Implementation

### Target file

`tests/agent/test_context.py`

### Procedure

Create a new test file with regression test for AppServices validation.

### Method

1. Create `tests/agent/test_context.py`
2. Add test for None rejection of each required service (REQ-002)
3. Add test for memory being optional (REQ-004)

### Details

```python
import pytest
from scripts.agent.context import AppServices

class TestAppServicesValidation:
    """Tests for REQ-002, REQ-004: Verify AppServices constructor validation."""

    def test_none_http_raises_runtime_error(self):
        """REQ-002: RuntimeError raised when http is None."""
        with pytest.raises(RuntimeError, match="Required service 'http' is None"):
            AppServices(http=None, llm="mock_llm", tools="mock_tools",
                       lifecycle="mock_lifecycle", hist_mgr="mock_hist_mgr",
                       audit_logger="mock_audit_logger")

    def test_none_llm_raises_runtime_error(self):
        """REQ-002: RuntimeError raised when llm is None."""
        with pytest.raises(RuntimeError, match="Required service 'llm' is None"):
            AppServices(http="mock_http", llm=None, tools="mock_tools",
                       lifecycle="mock_lifecycle", hist_mgr="mock_hist_mgr",
                       audit_logger="mock_audit_logger")

    def test_none_tools_raises_runtime_error(self):
        """REQ-002: RuntimeError raised when tools is None."""
        with pytest.raises(RuntimeError, match="Required service 'tools' is None"):
            AppServices(http="mock_http", llm="mock_llm", tools=None,
                       lifecycle="mock_lifecycle", hist_mgr="mock_hist_mgr",
                       audit_logger="mock_audit_logger")

    def test_none_lifecycle_raises_runtime_error(self):
        """REQ-002: RuntimeError raised when lifecycle is None."""
        with pytest.raises(RuntimeError, match="Required service 'lifecycle' is None"):
            AppServices(http="mock_http", llm="mock_llm", tools="mock_tools",
                       lifecycle=None, hist_mgr="mock_hist_mgr",
                       audit_logger="mock_audit_logger")

    def test_none_hist_mgr_raises_runtime_error(self):
        """REQ-002: RuntimeError raised when hist_mgr is None."""
        with pytest.raises(RuntimeError, match="Required service 'hist_mgr' is None"):
            AppServices(http="mock_http", llm="mock_llm", tools="mock_tools",
                       lifecycle="mock_lifecycle", hist_mgr=None,
                       audit_logger="mock_audit_logger")

    def test_none_audit_logger_raises_runtime_error(self):
        """REQ-002: RuntimeError raised when audit_logger is None."""
        with pytest.raises(RuntimeError, match="Required service 'audit_logger' is None"):
            AppServices(http="mock_http", llm="mock_llm", tools="mock_tools",
                       lifecycle="mock_lifecycle", hist_mgr="mock_hist_mgr",
                       audit_logger=None)

    def test_memory_can_be_none(self):
        """REQ-004: memory is optional and does not raise RuntimeError."""
        # Should not raise — memory is intentionally allowed to be None
        services = AppServices(http="mock_http", llm="mock_llm", tools="mock_tools",
                              lifecycle="mock_lifecycle", hist_mgr="mock_hist_mgr",
                              audit_logger="mock_audit_logger", memory=None)
        assert services.memory is None
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the AppServices change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_context.py | Unit test — verify None rejection for required services | uv run pytest tests/agent/test_context.py | New tests pass |

## Completion criteria

- [ ] Test verifies RuntimeError raised for each required service when None (REQ-002)
- [ ] Test verifies memory can be None without raising (REQ-004)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `context.py` (handled in separate document)

## execution Status

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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/20261004-143009_as010_no_required_validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195847
- **Related target files**: tests/agent/test_context.py
