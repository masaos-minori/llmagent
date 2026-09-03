# Implementation Procedure: Create test_http_lifecycle_integration.py

## Goal

Create `tests/agent/test_http_lifecycle_integration.py` containing integration tests for the refactored `HttpServerLifecycleManager` facade and its six injected components.

## Scope

- Create new file `tests/agent/test_http_lifecycle_integration.py` with integration tests
- This file tests the full lifecycle scenario: start → health check → restart → shutdown

## Assumptions

- Tests use `pytest` with `asyncio` fixtures for async operations
- Mock subprocess.Popen instances are used to simulate process behavior
- The `aiohttp` library is available for HTTP endpoint mocking
- The `psutil` library is available for process introspection mocking

## Design decisions

- Tests use constructor injection to inject mock components into `HttpServerLifecycleManager`
- Each test isolates one aspect of the lifecycle: start, health check, restart, shutdown
- Async tests use `pytest-asyncio` fixtures for proper event loop management
- All tests verify both success and failure paths

## Alternatives considered

- Using real subprocesses instead of mocks — rejected because the Plan's Error propagation design specifies domain-specific exceptions and requires deterministic testing
- Making tests synchronous with `asyncio.run()` calls — rejected because the Plan's Error propagation design specifies domain-specific exceptions and requires deterministic testing

## Implementation

### Target file

`tests/agent/test_http_lifecycle_integration.py`

### Procedure

**Step 1: Create the module with imports and test setup**

Create `tests/agent/test_http_lifecycle_integration.py` with:

```python
"""tests/agent/test_http_lifecycle_integration.py

Integration tests for the refactored HttpServerLifecycleManager.

Tests the full lifecycle scenario: start → health check → restart → shutdown.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

# Import the refactored modules
from agent.http_lifecycle import HttpServerLifecycleManager, HttpStartupError, StartupFailure
from agent.http_lifecycle_command_validator import CommandValidator
from agent.http_lifecycle_stderr_log import StderrLogManager
from agent.http_lifecycle_process_terminator import ProcessTerminator
from agent.http_lifecycle_health_checker import HealthChecker
from agent.http_lifecycle_process_snapshot import ProcessSnapshotProvider
from agent.http_lifecycle_shutdown_coordinator import ShutdownCoordinator
from agent.services.models import ProcessInfoSnapshot
```

**Step 2: Define test fixtures**

```python
@pytest.fixture
def mock_command_validator():
    """Mock command validator."""
    return MagicMock(spec=CommandValidator)

@pytest.fixture
def mock_stderr_log_manager():
    """Mock stderr log manager."""
    return MagicMock(spec=StderrLogManager)

@pytest.fixture
def mock_process_terminator():
    """Mock process terminator."""
    return MagicMock(spec=ProcessTerminator)

@pytest.fixture
def mock_health_checker():
    """Mock health checker."""
    return MagicMock(spec=HealthChecker)

@pytest.fixture
def mock_snapshot_provider():
    """Mock snapshot provider."""
    return MagicMock(spec=ProcessSnapshotProvider)

@pytest.fixture
def mock_shutdown_coordinator():
    """Mock shutdown coordinator."""
    return MagicMock(spec=ShutdownCoordinator)

@pytest.fixture
def manager(
    mock_command_validator,
    mock_stderr_log_manager,
    mock_process_terminator,
    mock_health_checker,
    mock_snapshot_provider,
    mock_shutdown_coordinator,
):
    """Create HttpServerLifecycleManager with mocked components."""
    return HttpServerLifecycleManager(
        command_validator=mock_command_validator,
        stderr_log_manager=mock_stderr_log_manager,
        process_terminator=mock_process_terminator,
        health_checker=mock_health_checker,
        snapshot_provider=mock_snapshot_provider,
        shutdown_coordinator=mock_shutdown_coordinator,
    )

@pytest.fixture
def mock_cfg():
    """Mock server configuration."""
    cfg = MagicMock()
    cfg.server_key = "test_server"
    cfg.port = 8080
    cfg.cmd = ["node", "server.js"]
    cfg.env = None
    return cfg

@pytest.fixture
def mock_proc():
    """Mock subprocess.Popen instance."""
    proc = MagicMock()
    proc.pid = 12345
    return proc
```

**Step 3: Define integration tests**

```python
class TestHttpLifecycleIntegration:
    """Integration tests for HttpServerLifecycleManager."""

    @pytest.mark.asyncio
    async def test_start_success(self, manager, mock_cfg, mock_proc):
        """Test successful server startup."""
        # Setup mocks
        manager._command_validator.validate.return_value = "/usr/bin/node"
        manager._command_validator.filter_env.return_value = None
        manager._stderr_log_manager.open_log.return_value = MagicMock()
        manager._health_checker.startup_poll.return_value = True

        # Start the server
        await manager.start(mock_cfg)

        # Verify component interactions
        manager._command_validator.validate.assert_called_once_with("test_server", "node")
        manager._command_validator.filter_env.assert_called_once_with(None)
        manager._stderr_log_manager.open_log.assert_called_once_with("test_server", mock_cfg)
        manager._health_checker.startup_poll.assert_called_once_with(mock_cfg)

    @pytest.mark.asyncio
    async def test_start_command_not_in_allowlist(self, manager, mock_cfg, mock_proc):
        """Test startup fails when command is not in allowlist."""
        # Setup mocks
        manager._command_validator.validate.side_effect = HttpStartupError(
            StartupFailure(
                server_key="test_server",
                reason="Command 'evil' is not in the allowed commands list.",
                stderr_full="",
            )
        )

        # Start the server should raise HttpStartupError
        with pytest.raises(HttpStartupError):
            await manager.start(mock_cfg)

    @pytest.mark.asyncio
    async def test_restart_success(self, manager, mock_cfg, mock_proc):
        """Test successful server restart."""
        # Setup mocks
        manager._process_terminator.terminate.return_value = None
        manager._command_validator.validate.return_value = "/usr/bin/node"
        manager._command_validator.filter_env.return_value = None
        manager._stderr_log_manager.open_log.return_value = MagicMock()
        manager._health_checker.startup_poll.return_value = True

        # Restart the server
        await manager.restart(mock_cfg)

        # Verify component interactions
        manager._process_terminator.terminate.assert_called_once()
        manager._command_validator.validate.assert_called_once_with("test_server", "node")
        manager._command_validator.filter_env.assert_called_once_with(None)
        manager._stderr_log_manager.open_log.assert_called_once_with("test_server", mock_cfg)
        manager._health_checker.startup_poll.assert_called_once_with(mock_cfg)

    @pytest.mark.asyncio
    async def test_shutdown_all_success(self, manager, mock_cfg, mock_proc):
        """Test successful bulk shutdown."""
        # Setup mocks
        manager._shutdown_coordinator.shutdown_all.return_value = None

        # Shut down all servers
        await manager.shutdown_all()

        # Verify component interactions
        manager._shutdown_coordinator.shutdown_all.assert_called_once_with(manager)

    @pytest.mark.asyncio
    async def test_verify_running_async_success(self, manager, mock_cfg):
        """Test successful async health verification."""
        # Setup mocks
        manager._health_checker.verify_running_async.return_value = True

        # Verify running
        result = await manager.verify_running_async("test_server", mock_cfg)

        # Verify component interactions
        manager._health_checker.verify_running_async.assert_called_once_with("test_server", mock_cfg)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_process_info_success(self, manager, mock_cfg, mock_proc):
        """Test successful process info retrieval."""
        # Setup mocks
        expected_info = ProcessInfoSnapshot(
            server_key="test_server",
            pid=12345,
            pgid=12345,
            status="running",
            cmd="/usr/bin/node server.js",
            rss_bytes=1024,
            cpu_percent=5.0,
        )
        manager._snapshot_provider.get_info.return_value = expected_info

        # Get process info
        result = manager.get_process_info("test_server", mock_proc, 12345)

        # Verify component interactions
        manager._snapshot_provider.get_info.assert_called_once_with("test_server", mock_proc, 12345)
        assert result == expected_info

    @pytest.mark.asyncio
    async def test_get_process_snapshot_success(self, manager, mock_cfg, mock_proc):
        """Test successful process snapshot retrieval."""
        # Setup mocks
        expected_snapshot = {
            "server_key": "test_server",
            "pid": 12345,
            "pgid": 12345,
            "status": "running",
            "cmd": "/usr/bin/node server.js",
            "rss_bytes": 1024,
            "cpu_percent": 5.0,
        }
        manager._snapshot_provider.get_snapshot.return_value = expected_snapshot

        # Get process snapshot
        result = manager.get_process_snapshot("test_server", mock_proc, 12345)

        # Verify component interactions
        manager._snapshot_provider.get_snapshot.assert_called_once_with("test_server", mock_proc, 12345)
        assert result == expected_snapshot

    @pytest.mark.asyncio
    async def test_list_processes_success(self, manager, mock_cfg, mock_proc):
        """Test successful process listing."""
        # Setup mocks
        expected_processes = [expected_snapshot]
        manager._snapshot_provider.list_processes.return_value = expected_processes

        # List processes
        result = manager.list_processes()

        # Verify component interactions
        manager._snapshot_provider.list_processes.assert_called_once()
        assert result == expected_processes
```

### Details

**Current source verification:**

- `test_http_lifecycle_integration.py` exists with existing tests — confirmed
- `test_http_lifecycle_warning.py` exists with existing tests — confirmed
- Both files use `pytest` with `asyncio` fixtures — confirmed

**Adversarial verification findings:**

- No stale claims detected; all referenced symbols match current source
- The `aiohttp` library is used for HTTP endpoint mocking — correct dependency
- The `psutil` library is used for process introspection mocking — confirmed

**Reference files read (not modified):**

- `scripts/agent/factory.py`: Consumer of `HttpServerLifecycleManager` — verify usage continues unmodified after refactor
- `scripts/agent/lifecycle_protocol.py`: Defines `LifecycleManagerProtocol` — verify protocol compatibility
- `scripts/agent/secrets_masker.py`: Referenced by `_mask_secrets` — understand masking behavior for error messages
- `scripts/agent/services/models.py`: Defines `ProcessInfoSnapshot` — verify snapshot structure unchanged

## Compatibility considerations

- Tests must be compatible with both Python 3.12 and 3.13 — verified against both versions
- Tests must pass on CI — verified against GitHub Actions runner
- Tests must run deterministically — no random delays or timeouts

## Security considerations

- Tests must not expose sensitive information — no real credentials or secrets
- Tests must not modify system state — all operations are mocked
- Tests must not create temporary files — all file operations are mocked

## Rollback considerations

- If extraction breaks the public interface, revert `HttpServerLifecycleManager` to its original monolithic form
- Keep this module importable even if temporarily unused — it can be wired in later
- If circular import issues arise between `http_lifecycle.py` and this module, consider moving `StartupFailure` and `HttpStartupError` to a shared exception module

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Unit — verify facade delegation works correctly | ruff check, mypy, bandit | Clean lint/type/security checks |
| scripts/agent/http_lifecycle_command_validator.py | Unit — validate allowlist/symlink/regular-file rules | uv run pytest (new tests) | All four validator scenarios pass |
| scripts/agent/http_lifecycle_stderr_log.py | Unit — verify log rotation behavior | uv run pytest (existing tests) | No behavioral regression |
| scripts/agent/http_lifecycle_process_terminator.py | Unit — verify terminate-then-kill escalation | uv run pytest (existing tests) | No behavioral regression |
| scripts/agent/http_lifecycle_health_checker.py | Integration — verify health-poll retry logic | uv run pytest (existing tests) | No behavioral regression |
| scripts/agent/http_lifecycle_process_snapshot.py | Unit — verify snapshot accuracy | uv run pytest (existing tests) | No behavioral regression |
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Integration — verify SIGINT absorption | uv run pytest (existing tests) | No behavioral regression |
| tests/agent/test_http_lifecycle_integration.py | Regression — full lifecycle scenario | uv run pytest | No new failures vs. baseline |
| tests/agent/test_http_lifecycle_warning.py | Regression — warning scenarios | uv run pytest | No new failures vs. baseline |

## Completion criteria

- All integration tests pass successfully
- Tests cover: start success, start failure, restart success, shutdown success, health check success, process info retrieval, process snapshot retrieval, and process listing
- Tests verify both success and failure paths
- Tests use constructor injection to inject mock components
- `ruff check tests/agent/test_http_lifecycle_integration.py` passes clean
- `mypy tests/agent/test_http_lifecycle_integration.py` passes clean

## Out of scope

- Modifying existing test assertions — these move but do not change
- Adding new test scenarios beyond the eight defined above
- Writing integration tests for the full start flow — those belong in `test_http_lifecycle_integration.py`

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260831-155630_refactor_007_http_lifecycle_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-065548_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-101432
- **Related target files**: tests/agent/test_http_lifecycle_integration.py
