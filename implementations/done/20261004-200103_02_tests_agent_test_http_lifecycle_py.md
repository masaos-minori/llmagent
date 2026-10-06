## Goal

Verify that the documented behavior (new client per session) is correct and no connection leaks occur on failure paths.

## Scope

- Create `tests/agent/test_http_lifecycle.py` with test for health check scenarios

## Assumptions

- The test framework uses pytest
- The HTTP lifecycle manager is importable from `scripts.agent.http_lifecycle`

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Verify no connection leaks when health check fails
- Verify connection reuse across multiple health-poll attempts (if applicable)

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real subprocesses — too brittle, slow

## Implementation

### Target file

`tests/agent/test_http_lifecycle.py`

### Procedure

Create a new test file with regression test for health check scenarios.

### Method

1. Create `tests/agent/test_http_lifecycle.py`
2. Add test for no connection leaks on failure path (REQ-002)
3. Add test for connection reuse verification (REQ-003)

### Details

```python
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from scripts.agent.http_lifecycle import HttpServerLifecycleManager

class TestHttpServerLifecycleHealthCheckScenarios:
    """Tests for REQ-002, REQ-003: Verify health check behavior."""

    @pytest.mark.asyncio
    async def test_no_connection_leak_on_health_check_failure(self):
        """REQ-002: No connection leak when health check fails."""
        manager = HttpServerLifecycleManager()
        
        # Mock the health poll method to simulate failure
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Simulate health check failure
            with patch.object(manager, '_poll_health_endpoint', side_effect=Exception("Connection refused")):
                result = await manager._health_poll_until_ready("test-server", timeout=1.0)
                
                # Should return False on failure
                assert result is False
                
                # Verify client was properly closed (context manager exited)
                mock_client.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_new_client_per_session(self):
        """REQ-003: New AsyncClient created per health-poll session."""
        manager = HttpServerLifecycleManager()
        
        # Track how many times AsyncClient is instantiated
        instantiation_count = 0
        
        original_async_client = None
        
        def counting_async_client(*args, **kwargs):
            nonlocal instantiation_count
            instantiation_count += 1
            return original_async_client(*args, **kwargs)
        
        # Patch AsyncClient to count instantiations
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance
            
            # Call health poll twice
            await manager._health_poll_until_ready("server-1", timeout=1.0)
            await manager._health_poll_until_ready("server-2", timeout=1.0)
            
            # Each call should create a new client
            assert mock_client_class.call_count == 2
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the http_lifecycle change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_http_lifecycle.py | Unit test — verify health check behavior | uv run pytest tests/agent/test_http_lifecycle.py | New tests pass |

## Completion criteria

- [ ] Test verifies no connection leaks when health check fails (REQ-002)
- [ ] Test verifies new client per session (REQ-003)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `http_lifecycle.py` beyond documentation (handled in separate document)

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261006-075819 | 20261006-075819 | Tests written to tests/agent/test_http_lifecycle_health_check.py against current _health_poll_until_ready(server_key,cfg,proc,deadline,shutdown_event) API; ruff/mypy/bandit/pytest green. |
| 2 | Add or update tests per Validation plan | Completed | 20261006-075819 | 20261006-075819 | Tests written to tests/agent/test_http_lifecycle_health_check.py against current _health_poll_until_ready(server_key,cfg,proc,deadline,shutdown_event) API; ruff/mypy/bandit/pytest green. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-075819 | 20261006-075819 | Tests written to tests/agent/test_http_lifecycle_health_check.py against current _health_poll_until_ready(server_key,cfg,proc,deadline,shutdown_event) API; ruff/mypy/bandit/pytest green. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-075819 | 20261006-075819 | Tests written to tests/agent/test_http_lifecycle_health_check.py against current _health_poll_until_ready(server_key,cfg,proc,deadline,shutdown_event) API; ruff/mypy/bandit/pytest green. |

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
- **Source issue**: issues/20261004-143011_hlm012_http_client_reuse.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182819_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-200103
- **Related target files**: tests/agent/test_http_lifecycle.py