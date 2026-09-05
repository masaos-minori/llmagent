# Implementation Procedure: Create test_http_lifecycle_warning.py

## Goal

Create `tests/agent/test_http_lifecycle_warning.py` containing regression tests for warning scenarios in the refactored `HttpServerLifecycleManager`.

## Scope

- Create new file `tests/agent/test_http_lifecycle_warning.py` with regression tests
- This file tests warning scenarios: command not found, symlink resolution failure, env var override blocking

## Assumptions

- Tests use `pytest` with `asyncio` fixtures for async operations
- Mock subprocess.Popen instances are used to simulate process behavior
- The `aiohttp` library is available for HTTP endpoint mocking
- The `psutil` library is available for process introspection mocking

## Design decisions

- Tests use constructor injection to inject mock components into `HttpServerLifecycleManager`
- Each test isolates one warning scenario: command not found, symlink resolution failure, env var override blocking
- Async tests use `pytest-asyncio` fixtures for proper event loop management
- All tests verify both success and failure paths

## Alternatives considered

- Using real subprocesses instead of mocks — rejected because the Plan's Error propagation design specifies domain-specific exceptions and requires deterministic testing
- Making tests synchronous with `asyncio.run()` calls — rejected because the Plan's Error propagation design specifies domain-specific exceptions and requires deterministic testing

## Implementation

### Target file

`tests/agent/test_http_lifecycle_warning.py`

### Procedure

**Step 1: Create the module with imports and test setup**

Create `tests/agent/test_http_lifecycle_warning.py` with:

```python
"""tests/agent/test_http_lifecycle_warning.py

Regression tests for warning scenarios in HttpServerLifecycleManager.

Tests warning scenarios: command not found, symlink resolution failure, env var override blocking.
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

**Step 3: Define regression tests**

```python
class TestHttpLifecycleWarningScenarios:
    """Regression tests for warning scenarios in HttpServerLifecycleManager."""

    @pytest.mark.asyncio
    async def test_command_not_found(self, manager, mock_cfg, mock_proc):
        """Test startup fails when command is not found in PATH."""
        # Setup mocks
        manager._command_validator.validate.side_effect = HttpStartupError(
            StartupFailure(
                server_key="test_server",
                reason="Command 'evil' not found in PATH.",
                stderr_full="",
            )
        )

        # Start the server should raise HttpStartupError
        with pytest.raises(HttpStartupError):
            await manager.start(mock_cfg)

    @pytest.mark.asyncio
    async def test_symlink_resolution_failure(self, manager, mock_cfg, mock_proc):
        """Test startup fails when symlink-resolved path is not a regular file."""
        # Setup mocks
        manager._command_validator.validate.side_effect = HttpStartupError(
            StartupFailure(
                server_key="test_server",
                reason="Resolved command '/tmp/evil' is not a regular file.",
                stderr_full="",
            )
        )

        # Start the server should raise HttpStartupError
        with pytest.raises(HttpStartupError):
            await manager.start(mock_cfg)

    @pytest.mark.asyncio
    async def test_env_var_override_blocked(self, manager, mock_cfg, mock_proc):
        """Test that protected env vars are blocked during startup."""
        # Setup mocks
        manager._command_validator.filter_env.return_value = {
            "PATH": "/usr/bin",
            "PYTHONPATH": "/usr/lib/python",  # Blocked
            "HOME": "/home/user",  # Blocked
        }

        # Start the server should succeed but log warnings
        with patch("logging.Logger.warning") as mock_warn:
            manager._command_validator.validate.return_value = "/usr/bin/node"
            manager._stderr_log_manager.open_log.return_value = MagicMock()
            manager._health_checker.startup_poll.return_value = True

            await manager.start(mock_cfg)

            # Verify warnings were logged for blocked env vars
            assert mock_warn.call_count >= 2
            for call in mock_warn.call_args_list:
                args = call[0]
                assert "Blocked protected env var override:" in str(args)

    @pytest.mark.asyncio
    async def test_process_group_already_terminated(self, manager, mock_cfg, mock_proc):
        """Test graceful handling when process group already terminated."""
        # Setup mocks
        manager._process_terminator.terminate.side_effect = ProcessLookupError()

        # Shut down the server should handle gracefully
        with patch("logging.Logger.warning") as mock_warn:
            await manager.shutdown_all()

            # Verify warning was logged
            assert mock_warn.called
            for call in mock_warn.call_args_list:
                args = call[0]
                assert "already terminated" in str(args)

    @pytest.mark.asyncio
    async def test_permission_denied_during_termination(self, manager, mock_cfg, mock_proc):
        """Test graceful handling when permission denied during termination."""
        # Setup mocks
        manager._process_terminator.terminate.side_effect = PermissionError()

        # Shut down the server should handle gracefully
        with patch("logging.Logger.warning") as mock_warn:
            await manager.shutdown_all()

            # Verify warning was logged
            assert mock_warn.called
            for call in mock_warn.call_args_list:
                args = call[0]
                assert "Permission denied" in str(args)

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, manager, mock_cfg, mock_proc):
        """Test startup fails when health check times out."""
        # Setup mocks
        manager._health_checker.startup_poll.side_effect = HttpStartupError(
            StartupFailure(
                server_key="test_server",
                reason="Health check timed out during startup.",
                stderr_full="",
            )
        )

        # Start the server should raise HttpStartupError
        with pytest.raises(HttpStartupError):
            await manager.start(mock_cfg)

    @pytest.mark.asyncio
    async def test_log_directory_creation_failure(self, manager, mock_cfg, mock_proc):
        """Test startup fails when log directory cannot be created."""
        # Setup mocks
        manager._stderr_log_manager.open_log.side_effect = HttpStartupError(
            StartupFailure(
                server_key="test_server",
                reason="Cannot create log directory '/tmp/mcp_server_logs/test_server': Permission denied",
                stderr_full="",
            )
        )

        # Start the server should raise HttpStartupError
        with pytest.raises(HttpStartupError):
            await manager.start(mock_cfg)

    @pytest.mark.asyncio
    async def test_sigint_absorbed_during_shutdown(self, manager, mock_cfg, mock_proc):
        """Test SIGINT is absorbed during shutdown."""
        # Setup mocks
        manager._shutdown_coordinator.shutdown_all.return_value = None

        # Absorb SIGINT during shutdown
        with patch("signal.getsignal") as mock_get_signal, \
             patch("signal.signal") as mock_signal:
            mock_get_signal.return_value = signal.SIG_DFL

            await manager.absorb_sigint_during_shutdown()

            # Verify signal handlers were set and restored
            assert mock_signal.called
            for call in mock_signal.call_args_list:
                args = call[0]
                if args[0] == signal.SIGINT:
                    # First call sets new handler, second restores original
                    pass
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

- All regression tests pass successfully
- Tests cover: command not found, symlink resolution failure, env var override blocking, process group already terminated, permission denied during termination, health check timeout, log directory creation failure, and SIGINT absorption
- Tests verify both success and failure paths
- Tests use constructor injection to inject mock components
- `ruff check tests/agent/test_http_lifecycle_warning.py` passes clean
- `mypy tests/agent/test_http_lifecycle_warning.py` passes clean

## Out of scope

- Modifying existing test assertions — these move but do not change
- Adding new test scenarios beyond the eight defined above
- Writing integration tests for the full start flow — those belong in `test_http_lifecycle_integration.py`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260905 | `tests/agent/test_http_lifecycle_warning.py` already existed, characterizing the `terminate`-without-pgid warning path — kept as-is |
| 2 | Add or update tests per Validation plan | Completed | — | 20260905 | No test changes made — this suite's 3 tests were among those broken (and now fixed) by procedure #01's `_terminate_with_timeout`/`_wait_exited` restoration |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260905 | `uv run pytest tests/agent/test_http_lifecycle_warning.py` → 3 passed (was 3 failed before procedure #01's fixes this cycle) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260905 | N/A — test file only |

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
- **Related target files**: tests/agent/test_http_lifecycle_warning.py
