## Goal

Add unit tests for `ShutdownCoordinator.shutdown_all()` confirming the ported cleanup and the fixed `terminator` parameter — none exists today.

## Scope

- Create `tests/agent/test_http_lifecycle_shutdown_coordinator.py` exercising the ported cleanup and the fixed `terminator` parameter directly against `ShutdownCoordinator`.
- Verify equivalence against `tests/agent/test_http_lifecycle_integration.py`'s existing assertions.

## Assumptions

- The existing `tests/agent/test_http_lifecycle_integration.py` suite asserts on `manager`'s internal state (`_http_pgids`, `_stderr_files`, `_stderr_log_paths`, `_last_health_check`) after `shutdown_all()` runs — this is the equivalence bar REQ-001/REQ-003 must clear.
- A mock `HttpServerLifecycleManager` can be constructed with the required attributes (`_http_procs`, `_http_pgids`, `_stderr_files`, `_stderr_log_paths`, `_last_health_check`, `_process_terminator`).

## Design decisions

- Use `unittest.mock.Mock` objects to simulate `subprocess.Popen` instances and `ProcessTerminator` — avoids needing live subprocesses.
- Test both the `terminator` parameter fix (caller-supplied terminator is used) and the new cleanup steps (pgid pop, stderr close, path clearing).

## Alternatives considered

- Using `pytest` fixtures instead of `unittest.TestCase` — either works; using `unittest.mock` for clarity.

## Implementation
### Target file

`tests/agent/test_http_lifecycle_shutdown_coordinator.py`

### Procedure

1. Create the test file with the following test classes:
   - `TestShutdownCoordinatorShutdownAll`: tests for `ShutdownCoordinator.shutdown_all()`.
2. Add test methods:
   - `test_shutdown_all_clears_internal_state`: verify `_http_pgids`, `_stderr_files`, `_stderr_log_paths`, `_last_health_check` are cleared after shutdown.
   - `test_shutdown_all_uses_caller_supplied_terminator`: verify the `terminator` parameter is actually used (not overwritten by the dead-code bug at L85).
   - `test_shutdown_all_closes_stderr_file_handles`: verify stderr file handles are closed after shutdown.
   - `test_shutdown_all_skips_already_exited_processes`: verify processes with `poll() != None` are skipped without calling terminator.
3. Import `ShutdownCoordinator` from `scripts.agent.http_lifecycle_shutdown_coordinator`.

### Method

Create a mock manager with:
```python
mock_manager = Mock()
mock_manager._http_procs = {"server1": mock_proc}
mock_manager._http_pgids = {"server1": 1234}
mock_manager._stderr_files = {"server1": mock_stderr_fh}
mock_manager._stderr_log_paths = {"server1": "/tmp/server1.stderr.log"}
mock_manager._last_health_check = {"server1": time.monotonic()}
mock_manager._process_terminator = mock_terminator
```

Where `mock_proc.poll.return_value = None` (still running) and `mock_stderr_fh.close` is a mock.

For the `terminator` parameter test:
```python
custom_terminator = Mock()
await coordinator.shutdown_all(mock_manager, terminator=custom_terminator)
custom_terminator.terminate_with_timeout.assert_called_once()
```

For the cleanup verification:
```python
assert mock_manager._http_pgids == {}
assert mock_manager._stderr_files == {}
assert mock_manager._stderr_log_paths == {}
assert mock_manager._last_health_check == {}
```

For the stderr close verification:
```python
mock_stderr_fh.close.assert_called_once()
```

### Details

Test class structure:
```python
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from agent.http_lifecycle_shutdown_coordinator import ShutdownCoordinator


class TestShutdownCoordinatorShutdownAll:
    """Tests for ShutdownCoordinator.shutdown_all()."""

    @pytest.fixture
    def mock_manager(self):
        mgr = Mock()
        mgr._http_procs = {}
        mgr._http_pgids = {}
        mgr._stderr_files = {}
        mgr._stderr_log_paths = {}
        mgr._last_health_check = {}
        mgr._process_terminator = MagicMock(spec=AsyncMock)
        return mgr

    @pytest.fixture
    def mock_proc(self):
        proc = Mock()
        proc.poll.return_value = None  # still running
        proc.pid = 1234
        return proc

    @pytest.fixture
    def mock_stderr_fh(self):
        fh = MagicMock()
        fh.close = MagicMock()
        return fh

    async def test_shutdown_all_clears_internal_state(self, mock_manager, mock_proc, mock_stderr_fh):
        mock_manager._http_procs["server1"] = mock_proc
        mock_manager._http_pgids["server1"] = 1234
        mock_manager._stderr_files["server1"] = mock_stderr_fh
        mock_manager._stderr_log_paths["server1"] = "/tmp/server1.stderr.log"
        mock_manager._last_health_check["server1"] = time.monotonic()

        coord = ShutdownCoordinator()
        await coord.shutdown_all(mock_manager)

        assert mock_manager._http_pgids == {}
        assert mock_manager._stderr_files == {}
        assert mock_manager._stderr_log_paths == {}
        assert mock_manager._last_health_check == {}

    async def test_shutdown_all_uses_caller_supplied_terminator(self, mock_manager, mock_proc):
        mock_manager._http_procs["server1"] = mock_proc
        custom_terminator = MagicMock(spec=AsyncMock)

        coord = ShutdownCoordinator()
        await coord.shutdown_all(mock_manager, terminator=custom_terminator)

        custom_terminator.terminate_with_timeout.assert_called_once_with(
            mock_proc, "server1", 30.0
        )

    async def test_shutdown_all_closes_stderr_file_handles(self, mock_manager, mock_proc, mock_stderr_fh):
        mock_manager._http_procs["server1"] = mock_proc
        mock_manager._stderr_files["server1"] = mock_stderr_fh

        coord = ShutdownCoordinator()
        await coord.shutdown_all(mock_manager)

        mock_stderr_fh.close.assert_called_once()

    async def test_shutdown_all_skips_already_exited_processes(self, mock_manager):
        exited_proc = Mock()
        exited_proc.poll.return_value = 1  # already exited
        mock_manager._http_procs["server1"] = exited_proc

        coord = ShutdownCoordinator()
        await coord.shutdown_all(mock_manager)

        # Should not call terminate_with_timeout for an already-exited process
        mock_manager._process_terminator.terminate_with_timeout.assert_not_called()
```

## Compatibility considerations

- This is a new test file — no compatibility impact on existing code.
- The test uses `MagicMock` and `Mock` which are standard library — no new dependencies.

## Security considerations

- No secrets, credentials, or sensitive data exposure in test code.
- Tests use mocked subprocess objects — no real processes are spawned.

## Rollback considerations

- If tests fail due to behavioral drift from the REQ-001 port, revert the coordinator changes and re-test before proceeding.
- The test file itself can be safely deleted if it proves incorrect — no production impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `test_http_lifecycle_shutdown_coordinator.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -q` | All tests pass |
| `test_http_lifecycle_integration.py` | Integration (existing regression) | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | All existing assertions still pass |

## Completion criteria

- All four test methods in `TestShutdownCoordinatorShutdownAll` pass.
- `uv run ruff check scripts/agent/http_lifecycle*.py tests/agent/test_http_lifecycle_shutdown_coordinator.py` passes clean.
- `uv run mypy scripts/agent/http_lifecycle*.py` passes (no new regressions vs pre-existing errors).

## Out of scope

- Testing SIGINT signal handling — out of scope for unit tests (requires OS-level signal manipulation).
- Testing the delegation switch in `HttpServerLifecycleManager.shutdown_all()` — handled in a separate procedure document.
- Testing other `ShutdownCoordinator` methods — only `shutdown_all()` is in scope for this Plan.

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
- **Requirement ID**: REQ-001, REQ-009
- **Source issue**: issues/20260915-102515_refactor_http_lifecycle_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-140327_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-140327
- **Related target files**: tests/agent/test_http_lifecycle_shutdown_coordinator.py
