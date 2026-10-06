## Goal

Add regression test verifying that FATAL error messages include remediation steps.

## Scope

- Create `tests/agent/test_startup.py` with test for FATAL error message

## Assumptions

- The test framework uses pytest
- The StartupOrchestrator is importable from `scripts.agent.startup`
- The `StartupOutcome` object has a `message`, `is_fatal`, and `remediation` attribute

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Mock `pipeline.outcomes` to control which outcomes are returned
- Verify error message includes both message and remediation text
- Verify formatting matches existing display format

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real validation pipeline — too brittle, slow

## Implementation

### Target file

`tests/agent/test_startup.py`

### Procedure

Create a new test file with regression test for FATAL error message.

### Method

1. Create `tests/agent/test_startup.py`
2. Add test for FATAL error message with remediation (REQ-002)
3. Add test for formatting consistency with startup_reporter.py (REQ-003)

### Details

```python
import pytest
from unittest.mock import MagicMock
from scripts.agent.startup import StartupOrchestrator

class TestStartupOrchestratorFatalErrorScenarios:
    """Tests for REQ-002, REQ-003: Verify FATAL error message includes remediation."""

    def test_fatal_error_includes_remediation(self):
        """REQ-002: Error message includes remediation steps for each FATAL outcome."""
        orchestrator = StartupOrchestrator()
        
        # Create mock fatal outcomes with remediation
        mock_outcome1 = MagicMock()
        mock_outcome1.message = "Service A failed"
        mock_outcome1.is_fatal = True
        mock_outcome1.remediation = "Check Service A configuration"
        
        mock_outcome2 = MagicMock()
        mock_outcome2.message = "Service B failed"
        mock_outcome2.is_fatal = True
        mock_outcome2.remediation = "Restart Service B"
        
        # Create mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.outcomes = [mock_outcome1, mock_outcome2]
        
        # Call _check_services and verify error message includes remediation
        with pytest.raises(RuntimeError) as exc_info:
            orchestrator._check_services(mock_pipeline)
        
        error_msg = str(exc_info.value)
        
        # Verify both messages are present
        assert "Service A failed" in error_msg
        assert "Service B failed" in error_msg
        
        # Verify remediation text is included
        assert "Remediation:" in error_msg
        assert "Check Service A configuration" in error_msg
        assert "Restart Service B" in error_msg

    def test_fatal_error_format_matches_startup_reporter(self):
        """REQ-003: Formatting matches startup_reporter.py format."""
        orchestrator = StartupOrchestrator()
        
        # Create mock fatal outcome with remediation
        mock_outcome = MagicMock()
        mock_outcome.message = "Test failure"
        mock_outcome.is_fatal = True
        mock_outcome.remediation = "Fix test configuration"
        
        # Create mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.outcomes = [mock_outcome]
        
        # Call _check_services and verify format
        with pytest.raises(RuntimeError) as exc_info:
            orchestrator._check_services(mock_pipeline)
        
        error_msg = str(exc_info.value)
        
        # Verify format: "Message\nRemediation: ..."
        assert "Test failure" in error_msg
        assert "\nRemediation: Fix test configuration" in error_msg

    def test_fatal_error_without_remediation(self):
        """Edge case: Error message without remediation still works."""
        orchestrator = StartupOrchestrator()
        
        # Create mock fatal outcome without remediation
        mock_outcome = MagicMock()
        mock_outcome.message = "Simple failure"
        mock_outcome.is_fatal = True
        mock_outcome.remediation = None
        
        # Create mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.outcomes = [mock_outcome]
        
        # Call _check_services and verify error message
        with pytest.raises(RuntimeError) as exc_info:
            orchestrator._check_services(mock_pipeline)
        
        error_msg = str(exc_info.value)
        
        # Should only contain the message, no Remediation line
        assert "Simple failure" in error_msg
        assert "Remediation:" not in error_msg
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the startup change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_startup.py | Unit test — verify FATAL error message includes remediation | uv run pytest tests/agent/test_startup.py | New tests pass |

## Completion criteria

- [ ] Test verifies error message contains remediation text (REQ-002)
- [ ] Test verifies formatting matches existing display format (REQ-003)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `startup.py` (handled in separate document)
- Modifying `startup_reporter.py` (handled in separate document)

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20261004-143012_so013_missing_remediation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182820_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-200157
- **Related target files**: tests/agent/test_startup.py
