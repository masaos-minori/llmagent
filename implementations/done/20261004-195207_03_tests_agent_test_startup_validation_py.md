## Goal

Add regression tests verifying that RAG consistency check timeout is enforced and thread pool starvation is prevented under concurrent startup.

## Scope

- Create `tests/agent/test_startup_validation.py` with tests for RAG check timeout scenarios

## Assumptions

- The test framework uses pytest
- The startup validation pipeline is importable from `scripts.agent.startup_validation`

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Mock `RagMaintenanceService.consistency()` to simulate slow operation
- Verify timeout raises CancelledError or custom timeout exception
- Verify no thread pool starvation under concurrent startup

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real RAG indices — too brittle, slow

## Implementation
### Target file
`tests/agent/test_startup_validation.py`

### Procedure
Create a new test file with regression tests for RAG check timeout scenarios.

### Method
1. Create `tests/agent/test_startup_validation.py`
2. Add test for RAG check timeout behavior (REQ-004)
3. Add test for no thread pool starvation under concurrent startup (REQ-003)

### Details
```python
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from scripts.agent.startup_validation import StartupValidationPipeline

class TestStartupValidationRagTimeoutScenarios:
    """Tests for REQ-003, REQ-004: Verify RAG check timeout enforcement."""

    @pytest.mark.asyncio
    async def test_rag_check_timeout_enforced(self):
        """REQ-004: Timeout is enforced on the RAG check operation."""
        pipeline = StartupValidationPipeline()
        
        # Mock RagMaintenanceService.consistency to simulate slow operation
        mock_consistency = MagicMock(side_effect=lambda: None)
        
        with patch('scripts.agent.startup_validation.RagMaintenanceService') as mock_rag_svc:
            mock_rag_svc.return_value.consistency = mock_consistency
            
            # Patch asyncio.wait_for to simulate timeout
            with patch('asyncio.wait_for', side_effect=Exception("timeout")):
                with pytest.raises(Exception, match="timeout"):
                    await pipeline.check_services()

    @pytest.mark.asyncio
    async def test_no_thread_pool_starvation_under_concurrent_startup(self):
        """REQ-003: No thread pool starvation under concurrent startup."""
        pipeline = StartupValidationPipeline()
        
        # Mock RagMaintenanceService.consistency to simulate slow operation
        mock_consistency = MagicMock(side_effect=lambda: None)
        
        with patch('scripts.agent.startup_validation.RagMaintenanceService') as mock_rag_svc:
            mock_rag_svc.return_value.consistency = mock_consistency
            
            # Patch asyncio.wait_for to return normally
            with patch('asyncio.wait_for', return_value=None):
                await pipeline.check_services()
                
                # Verify wait_for was called with timeout parameter
                # (this confirms the timeout mechanism is active)
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the startup validation change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_startup_validation.py | Unit test — verify timeout enforcement | uv run pytest tests/agent/test_startup_validation.py | New tests pass |

## Completion criteria

- [ ] Test verifies no thread pool starvation under concurrent startup (REQ-003)
- [ ] Test verifies timeout behavior (REQ-004)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `startup_validation.py` (handled in separate document)
- Modifying `rag_maintenance_service.py` (handled in separate document)

## Implementation outcome

Deviation from procedure: the inline draft was NOT applied. It imports
`from scripts.agent.startup_validation import StartupValidationPipeline` (the real
module is imported as `agent.startup_validation`), constructs
`StartupValidationPipeline()` (no-arg; the real constructor is
`StartupValidationPipeline(ctx, ...)`), patches global `asyncio.wait_for`, and its
second test performs no assertion. Origin/master already ships a correct test file in
commit `10308ed7` (`tests/agent/test_startup_validation.py`,
`TestRagConsistencyTimeout`) that drives the real `check_services()` body, patches
`agent.startup_validation.asyncio.wait_for`, and asserts SKIPPED (REQ-002) and OK
(REQ-003); it passes (2 passed). No new file was created and no code was changed.
Accepting the upstream implementation and closing the workflow.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Deliverable (test file) present in origin `10308ed7`; no code authored by this workflow (see outcome). |
| 2 | Add or update tests per Validation plan | Done | — | — | `tests/agent/test_startup_validation.py` present in origin, 2 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | 2 passed; ruff/bandit clean (no code change). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | Out of scope per procedure. |

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20261004-143006_sv007_blocking_rag_check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182814_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195207
- **Related target files**: tests/agent/test_startup_validation.py
