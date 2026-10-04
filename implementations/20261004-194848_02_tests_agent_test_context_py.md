## Goal

Add regression test verifying that the original exception chain is preserved when `AgentContext.__init__()` fails to load configuration.

## Scope

- Create `tests/agent/test_context.py` with test for traceback preservation

## Assumptions

- The test framework uses pytest
- The AgentContext is importable from `scripts.agent.context`

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Mock `build_agent_config()` to raise ValueError
- Verify exception chain includes both wrapper RuntimeError and original ValueError

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real config files — too brittle, slow

## Implementation
### Target file
`tests/agent/test_context.py`

### Procedure
Create a new test file with regression test for traceback preservation.

### Method
1. Create `tests/agent/test_context.py`
2. Add test for exception chain preservation (REQ-002)

### Details
```python
import pytest
from unittest.mock import patch, MagicMock
from scripts.agent.context import AgentContext

class TestAgentContextExceptionChain:
    """Tests for REQ-002: Verify exception chain preservation."""

    def test_exception_chain_preserved_on_config_load_failure(self):
        """REQ-002: Exception chain includes both wrapper RuntimeError and original ValueError."""
        mock_config = MagicMock()
        
        # Mock build_agent_config to raise ValueError
        with patch('scripts.agent.context.build_agent_config', side_effect=ValueError("Invalid config")):
            with pytest.raises(RuntimeError) as exc_info:
                AgentContext(config_dir="/nonexistent")
            
            # Verify wrapper exception message contains config directory info
            assert "Failed to load agent config" in str(exc_info.value)
            
            # Verify exception chain is preserved (not suppressed by 'from None')
            assert exc_info.value.__cause__ is not None
            assert isinstance(exc_info.value.__cause__, ValueError)
            assert str(exc_info.value.__cause__) == "Invalid config"
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the context change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_context.py | Unit test — verify exception chain preservation | uv run pytest tests/agent/test_context.py | New tests pass |

## Completion criteria

- [ ] Test verifies traceback includes both wrapper and original frames (REQ-002)
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261004-143004_ac005_traceback_suppression.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182812_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-194848
- **Related target files**: tests/agent/test_context.py
