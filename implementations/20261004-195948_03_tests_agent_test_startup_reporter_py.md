## Goal

Add regression test verifying consistent behavior under both scenarios (invariant enforced vs defensive checks present).

## Scope

- Create `tests/agent/test_startup_reporter.py` with test for readiness reporting with missing services

## Assumptions

- The test framework uses pytest
- The readiness reporter is importable from `scripts.agent.startup_reporter`

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Test both scenarios: invariant enforced (AssertionError) and defensive checks present (graceful handling)
- Verify readiness reporting works correctly when services_required is None vs when it has values

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real service injection — too brittle, slow

## Implementation

### Target file

`tests/agent/test_startup_reporter.py`

### Procedure

Create a new test file with regression test for readiness reporting scenarios.

### Method

1. Create `tests/agent/test_startup_reporter.py`
2. Add test for readiness reporting with invariant enforced (REQ-003)
3. Add test for graceful handling when services_required is None (REQ-003)

### Details

```python
import pytest
from unittest.mock import MagicMock, patch
from scripts.agent.startup_reporter import ReadinessReporter

class TestReadinessReporterInvariantScenarios:
    """Tests for REQ-003: Verify consistent behavior under both scenarios."""

    def test_readiness_with_invariant_enforced(self):
        """REQ-003: Invariant enforcement raises AssertionError when required service is missing."""
        # Mock context with services_required that violates invariant
        mock_ctx = MagicMock()
        
        # Create a mock AppServices with a missing required service
        mock_services = MagicMock()
        mock_services.http = "mock_http"
        mock_services.llm = "mock_llm"
        mock_services.tools = "mock_tools"
        mock_services.lifecycle = "mock_lifecycle"
        mock_services.hist_mgr = None  # Missing required service
        mock_services.audit_logger = "mock_audit_logger"
        mock_ctx.services_required = mock_services
        
        reporter = ReadinessReporter(mock_ctx)
        
        # With invariant enforced, accessing services_required should raise AssertionError
        with patch.object(type(mock_ctx), 'services_required', 
                        side_effect=AssertionError("Required service 'hist_mgr' is None")):
            with pytest.raises(AssertionError, match="Required service 'hist_mgr'"):
                reporter.report_readiness()

    def test_readiness_with_defensive_checks_present(self):
        """REQ-003: Defensive checks handle missing services gracefully."""
        mock_ctx = MagicMock()
        mock_ctx.services_required = None
        
        reporter = ReadinessReporter(mock_ctx)
        
        # With defensive checks, should return unavailable status without error
        result = reporter.report_readiness()
        assert result["status"] == "unavailable"
        assert "No services configured" in result.get("reason", "")
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the startup_reporter change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_startup_reporter.py | Unit test — verify readiness reporting consistency | uv run pytest tests/agent/test_startup_reporter.py | New tests pass |

## Completion criteria

- [ ] Test verifies consistent behavior under both scenarios (REQ-003)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `startup_reporter.py` (handled in separate document)
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261004-143010_rr011_services_invariant_uncertainty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182818_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195948
- **Related target files**: tests/agent/test_startup_reporter.py
